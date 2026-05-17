from __future__ import annotations

from .config import Settings
from .models import RugCheckReport, TokenPair


def passes_basic_filters(pair: TokenPair, settings: Settings) -> bool:
    if pair.chain_id != "solana":
        return False
    if pair.pair_age_minutes is None or pair.pair_age_minutes > settings.max_pair_age_minutes:
        return False
    if pair.liquidity_usd is None or pair.liquidity_usd < settings.min_liquidity_usd:
        return False
    if pair.volume_5m_usd is None or pair.volume_5m_usd < settings.min_volume_5m_usd:
        return False
    if pair.market_cap_usd is None:
        return False
    return settings.min_market_cap_usd <= pair.market_cap_usd <= settings.max_market_cap_usd


def passes_rugcheck_filter(report: RugCheckReport, settings: Settings) -> bool:
    return report.score is not None and report.score >= settings.min_rugcheck_score
