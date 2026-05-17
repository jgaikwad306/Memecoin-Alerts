from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable, TypeVar


T = TypeVar("T")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def chunked(items: list[T], size: int) -> Iterable[list[T]]:
    for index in range(0, len(items), size):
        yield items[index : index + size]


def as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def format_usd(value: float | None) -> str:
    if value is None:
        return "unknown"
    return f"${value:,.0f}"


def format_minutes(value: float | None) -> str:
    if value is None:
        return "unknown"
    return f"{value:.1f}"
