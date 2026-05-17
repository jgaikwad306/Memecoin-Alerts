from __future__ import annotations

import html

from .config import Settings
from .http_client import post_json
from .models import RugCheckReport, TokenPair
from .utils import format_minutes, format_usd


def build_alert_message(pair: TokenPair, report: RugCheckReport) -> str:
    score = "unknown" if report.score is None else f"{report.score:g}/100"
    dex_url = pair.dex_url or "unknown"

    lines = [
        "<b>New Solana Meme Alert</b>",
        "",
        f"Name: {html.escape(pair.name)} ({html.escape(pair.symbol)})",
        f"RugCheck Score: {score}",
        f"Liquidity: {format_usd(pair.liquidity_usd)}",
        f"5m Volume: {format_usd(pair.volume_5m_usd)}",
        f"Market Cap/FDV: {format_usd(pair.market_cap_usd)}",
        f"Age: {format_minutes(pair.pair_age_minutes)} min",
        "",
        "Token:",
        html.escape(pair.token_address),
        "",
        "DexScreener:",
        html.escape(dex_url),
        "",
        "RugCheck:",
        html.escape(report.url),
        "",
        "Not financial advice. Manually verify before trading.",
    ]
    return "\n".join(lines)


def send_telegram_alert(settings: Settings, pair: TokenPair, report: RugCheckReport) -> None:
    send_telegram_message(settings, build_alert_message(pair, report), parse_mode="HTML")


def send_telegram_message(
    settings: Settings,
    text: str,
    parse_mode: str | None = None,
) -> None:
    payload = {
        "chat_id": settings.telegram_chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode

    post_json(
        f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
        timeout=settings.request_timeout_seconds,
        user_agent=settings.http_user_agent,
        payload=payload,
    )
