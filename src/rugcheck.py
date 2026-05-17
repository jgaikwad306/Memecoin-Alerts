from __future__ import annotations

from typing import Any

from .config import Settings
from .http_client import get_json
from .models import RugCheckReport
from .utils import as_float


def _extract_score(payload: dict[str, Any]) -> float | None:
    for key in ("score", "score_normalised", "scoreNormalized", "normalizedScore"):
        score = as_float(payload.get(key))
        if score is not None:
            return score

    nested = payload.get("summary")
    if isinstance(nested, dict):
        for key in ("score", "score_normalised", "scoreNormalized", "normalizedScore"):
            score = as_float(nested.get(key))
            if score is not None:
                return score

    return None


def get_rugcheck_report(settings: Settings, token_address: str) -> RugCheckReport:
    payload = get_json(
        f"{settings.rugcheck_base_url}/v1/tokens/{token_address}/report",
        timeout=settings.request_timeout_seconds,
        user_agent=settings.http_user_agent,
    )
    if not isinstance(payload, dict):
        payload = {"response": payload}

    return RugCheckReport(
        token_address=token_address,
        score=_extract_score(payload),
        url=f"https://rugcheck.xyz/tokens/{token_address}",
        raw=payload,
    )
