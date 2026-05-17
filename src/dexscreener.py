from __future__ import annotations

import time
from typing import Any

from .config import Settings
from .http_client import get_json
from .models import TokenPair
from .utils import as_float, chunked


SOLANA_CHAIN_ID = "solana"


def _get_json(settings: Settings, path: str) -> Any:
    return get_json(
        f"{settings.dexscreener_base_url}{path}",
        timeout=settings.request_timeout_seconds,
        user_agent=settings.http_user_agent,
    )


def _items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        return [payload]
    return []


def _latest_solana_token_addresses(settings: Settings) -> list[str]:
    addresses: list[str] = []
    seen: set[str] = set()

    for path in ("/token-profiles/latest/v1", "/token-boosts/latest/v1"):
        payload = _get_json(settings, path)
        for item in _items(payload):
            if item.get("chainId") != SOLANA_CHAIN_ID:
                continue
            address = item.get("tokenAddress")
            if isinstance(address, str) and address and address not in seen:
                seen.add(address)
                addresses.append(address)

    return addresses


def _normalize_pair(raw: dict[str, Any]) -> TokenPair | None:
    base_token = raw.get("baseToken") or {}
    token_address = base_token.get("address")
    if raw.get("chainId") != SOLANA_CHAIN_ID or not isinstance(token_address, str):
        return None

    liquidity = raw.get("liquidity") or {}
    volume = raw.get("volume") or {}
    created_at_ms = as_float(raw.get("pairCreatedAt"))
    age_minutes = None
    if created_at_ms:
        age_minutes = max((time.time() - (created_at_ms / 1000)) / 60, 0)

    market_cap = as_float(raw.get("marketCap"))
    if market_cap is None:
        market_cap = as_float(raw.get("fdv"))

    return TokenPair(
        chain_id=SOLANA_CHAIN_ID,
        token_address=token_address,
        pair_address=raw.get("pairAddress"),
        name=str(base_token.get("name") or "Unknown"),
        symbol=str(base_token.get("symbol") or "UNKNOWN"),
        dex_url=raw.get("url"),
        liquidity_usd=as_float(liquidity.get("usd")),
        volume_5m_usd=as_float(volume.get("m5")),
        market_cap_usd=market_cap,
        pair_age_minutes=age_minutes,
        raw=raw,
    )


def get_candidate_solana_pairs(settings: Settings) -> list[TokenPair]:
    token_addresses = _latest_solana_token_addresses(settings)
    pairs_by_token: dict[str, TokenPair] = {}

    for batch in chunked(token_addresses, 30):
        payload = _get_json(settings, f"/tokens/v1/{SOLANA_CHAIN_ID}/{','.join(batch)}")
        for item in _items(payload):
            pair = _normalize_pair(item)
            if pair is None:
                continue
            current = pairs_by_token.get(pair.token_address)
            current_liquidity = current.liquidity_usd if current else None
            if current is None or (pair.liquidity_usd or 0) > (current_liquidity or 0):
                pairs_by_token[pair.token_address] = pair

    return list(pairs_by_token.values())
