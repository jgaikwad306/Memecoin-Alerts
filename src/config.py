from __future__ import annotations

import os
from dataclasses import dataclass


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return float(value)


def _load_dotenv(path: str = ".env") -> None:
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    telegram_chat_id: str
    poll_interval_seconds: int
    min_rugcheck_score: float
    min_liquidity_usd: float
    min_volume_5m_usd: float
    max_pair_age_minutes: float
    min_market_cap_usd: float
    max_market_cap_usd: float
    dexscreener_base_url: str
    rugcheck_base_url: str
    sqlite_path: str
    request_timeout_seconds: int


def load_settings() -> Settings:
    _load_dotenv()

    return Settings(
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
        poll_interval_seconds=_get_int("POLL_INTERVAL_SECONDS", 15),
        min_rugcheck_score=_get_float("MIN_RUGCHECK_SCORE", 80),
        min_liquidity_usd=_get_float("MIN_LIQUIDITY_USD", 5000),
        min_volume_5m_usd=_get_float("MIN_VOLUME_5M_USD", 10000),
        max_pair_age_minutes=_get_float("MAX_PAIR_AGE_MINUTES", 10),
        min_market_cap_usd=_get_float("MIN_MARKET_CAP_USD", 25000),
        max_market_cap_usd=_get_float("MAX_MARKET_CAP_USD", 500000),
        dexscreener_base_url=os.getenv(
            "DEXSCREENER_BASE_URL", "https://api.dexscreener.com"
        ).rstrip("/"),
        rugcheck_base_url=os.getenv("RUGCHECK_BASE_URL", "https://api.rugcheck.xyz").rstrip(
            "/"
        ),
        sqlite_path=os.getenv("SQLITE_PATH", "data/bot.sqlite3"),
        request_timeout_seconds=_get_int("REQUEST_TIMEOUT_SECONDS", 15),
    )


def validate_runtime_settings(settings: Settings) -> None:
    missing = []
    if not settings.telegram_bot_token:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not settings.telegram_chat_id:
        missing.append("TELEGRAM_CHAT_ID")
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(f"Missing required environment variable(s): {joined}")
