from __future__ import annotations

import argparse
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
from .telegram_bot import send_telegram_alert, send_telegram_message


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
LOGGER = logging.getLogger("memecoin_alerts")


def run_once(max_alerts: int | None = None) -> int:
    settings = load_settings()
    validate_runtime_settings(settings)
    alert_limit = settings.max_alerts_per_cycle if max_alerts is None else max_alerts

    alerted_count = 0
    skipped_seen = 0
    skipped_basic = 0
    skipped_rugcheck = 0
    rugcheck_count = 0
    with connect(settings.database_url, settings.sqlite_path) as conn:
        init_db(conn)
        pairs = get_candidate_solana_pairs(settings)
        LOGGER.info("Fetched %s candidate Solana pairs", len(pairs))

        for pair in pairs:
            if alert_limit > 0 and alerted_count >= alert_limit:
                LOGGER.info("Alert limit reached for this cycle: %s", alert_limit)
                break

            if has_seen_token(conn, pair.token_address):
                skipped_seen += 1
                continue

            save_seen_token(conn, pair)

            if not passes_basic_filters(pair, settings):
                skipped_basic += 1
                continue

            report = get_rugcheck_report(settings, pair.token_address)
            rugcheck_count += 1
            update_token_with_rugcheck(conn, pair.token_address, report)

            if passes_rugcheck_filter(report, settings):
                send_telegram_alert(settings, pair, report)
                mark_alerted(conn, pair.token_address)
                alerted_count += 1
                LOGGER.info("Alerted token %s", pair.token_address)
            else:
                skipped_rugcheck += 1

        LOGGER.info(
            "Cycle stats: seen=%s skipped_seen=%s skipped_basic=%s rugcheck=%s "
            "skipped_rugcheck=%s alerted=%s",
            len(pairs),
            skipped_seen,
            skipped_basic,
            rugcheck_count,
            skipped_rugcheck,
            alerted_count,
        )

    return alerted_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Solana memecoin Telegram alert bot")
    parser.add_argument(
        "--once",
        action="store_true",
        help="run one polling cycle and exit",
    )
    parser.add_argument(
        "--test-telegram",
        action="store_true",
        help="send a test Telegram message and exit",
    )
    parser.add_argument(
        "--max-alerts",
        type=int,
        default=None,
        help="maximum alerts to send before stopping this cycle; 0 means unlimited",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = load_settings()
    validate_runtime_settings(settings)

    try:
        if args.test_telegram:
            send_telegram_message(settings, "Memecoin Alerts test message.")
            LOGGER.info("Sent Telegram test message")
            return

        with connect(settings.database_url, settings.sqlite_path) as conn:
            init_db(conn)

        if args.once:
            alerted = run_once(max_alerts=args.max_alerts)
            LOGGER.info("Cycle complete, alerts sent: %s", alerted)
            return

        while True:
            try:
                alerted = run_once(max_alerts=args.max_alerts)
                LOGGER.info("Cycle complete, alerts sent: %s", alerted)
            except Exception:
                LOGGER.exception("Polling cycle failed")

            time.sleep(settings.poll_interval_seconds)
    except KeyboardInterrupt:
        LOGGER.info("Stopped by user")
        return


if __name__ == "__main__":
    main()
