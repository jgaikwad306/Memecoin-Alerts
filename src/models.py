from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TokenPair:
    chain_id: str
    token_address: str
    pair_address: str | None
    name: str
    symbol: str
    dex_url: str | None
    liquidity_usd: float | None
    volume_5m_usd: float | None
    market_cap_usd: float | None
    pair_age_minutes: float | None
    raw: dict[str, Any]


@dataclass(frozen=True)
class RugCheckReport:
    token_address: str
    score: float | None
    url: str
    raw: dict[str, Any]
