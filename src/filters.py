from __future__ import annotations

from .config import Settings
from .models import RugCheckReport, TokenPair


def basic_filter_rejection_reason(pair: TokenPair, settings: Settings) -> str | None:
    if pair.chain_id != "solana":
        return "chain"
    if pair.pair_age_minutes is None:
        return "missing_age"
    if pair.pair_age_minutes > settings.max_pair_age_minutes:
        return "age"
    if pair.liquidity_usd is None:
        return "missing_liquidity"
    if pair.liquidity_usd < settings.min_liquidity_usd:
        return "liquidity"
    if pair.volume_5m_usd is None:
        return "missing_volume_5m"
    if pair.volume_5m_usd < settings.min_volume_5m_usd:
        return "volume_5m"
    if pair.market_cap_usd is None:
        return "missing_market_cap"
    if pair.market_cap_usd < settings.min_market_cap_usd:
        return "market_cap_low"
    if pair.market_cap_usd > settings.max_market_cap_usd:
        return "market_cap_high"
    return None


def passes_basic_filters(pair: TokenPair, settings: Settings) -> bool:
    return basic_filter_rejection_reason(pair, settings) is None


def passes_rugcheck_filter(report: RugCheckReport, settings: Settings) -> bool:
    return report.score is not None and report.score >= settings.min_rugcheck_score
