from __future__ import annotations

import logging
import time

from .config import load_settings, validate_runtime_settings
from .db import (
    connect,
    has_seen_token,
    init_db,
    mark_alerted,
    save_seen_token,
    update_token_with_rugcheck,
)
from .dexscreener import get_candidate_solana_pairs
from .filters import passes_basic_filters, passes_rugcheck_filter
from .rugcheck import get_rugcheck_report
from .telegram_bot import send_telegram_alert


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
LOGGER = logging.getLogger("memecoin_alerts")


def run_once() -> int:
    settings = load_settings()
    validate_runtime_settings(settings)

    alerted_count = 0
    with connect(settings.sqlite_path) as conn:
        init_db(conn)
        pairs = get_candidate_solana_pairs(settings)
        LOGGER.info("Fetched %s candidate Solana pairs", len(pairs))

        for pair in pairs:
            if has_seen_token(conn, pair.token_address):
                continue

            save_seen_token(conn, pair)

            if not passes_basic_filters(pair, settings):
                continue

            report = get_rugcheck_report(settings, pair.token_address)
            update_token_with_rugcheck(conn, pair.token_address, report)

            if passes_rugcheck_filter(report, settings):
                send_telegram_alert(settings, pair, report)
                mark_alerted(conn, pair.token_address)
                alerted_count += 1
                LOGGER.info("Alerted token %s", pair.token_address)

    return alerted_count


def main() -> None:
    settings = load_settings()
    validate_runtime_settings(settings)

    with connect(settings.sqlite_path) as conn:
        init_db(conn)

    while True:
        try:
            alerted = run_once()
            LOGGER.info("Cycle complete, alerts sent: %s", alerted)
        except Exception:
            LOGGER.exception("Polling cycle failed")

        time.sleep(settings.poll_interval_seconds)


if __name__ == "__main__":
    main()
