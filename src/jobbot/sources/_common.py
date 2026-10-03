"""Helpers shared by connectors: timestamp coercion, `since` checks, loose JSON typing.

No @register here; the registry's module discovery imports this file harmlessly.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

MAX_PAGES = 20
"""Hard cap on pages per run for any paginated source (SPEC §7)."""


def as_utc(value: datetime) -> datetime:
    """Return a timezone-aware UTC datetime; naive input is assumed to be UTC."""
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def from_unix(value: Any) -> datetime | None:
    """Unix seconds (int, float or numeric string) to aware UTC datetime."""
    if value is None or isinstance(value, bool):
        return None
    try:
        return datetime.fromtimestamp(float(value), tz=UTC)
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def from_iso(value: Any) -> datetime | None:
    """ISO 8601 string (with or without offset, `Z` allowed) to aware UTC datetime."""
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return as_utc(datetime.fromisoformat(value.strip()))
    except ValueError:
        return None


def is_older(posted_at: datetime | None, since: datetime | None) -> bool:
    """True only when both are known and the posting predates `since`."""
    if posted_at is None or since is None:
        return False
    return as_utc(posted_at) < as_utc(since)


def text(value: Any) -> str | None:
    """Stringify a scalar; empty/whitespace-only becomes None."""
    if value is None:
        return None
    result = str(value).strip()
    return result or None


def strings(value: Any) -> list[str]:
    """A list of non-empty strings from a JSON list (or a single scalar)."""
    if value is None:
        return []
    items = value if isinstance(value, list) else [value]
    return [s for s in (text(v) for v in items) if s]


def first(value: Any) -> str | None:
    """First non-empty string of a JSON list (or the scalar itself)."""
    items = strings(value)
    return items[0] if items else None


def salary_range(low: Any, high: Any, currency: Any = None) -> str | None:
    """Render "low - high CUR" from numeric bounds; None when neither bound is set."""
    lo = text(low) if low not in (None, 0, "0", "") else None
    hi = text(high) if high not in (None, 0, "0", "") else None
    if not lo and not hi:
        return None
    amount = f"{lo} - {hi}" if lo and hi else (lo or hi)
    cur = text(currency)
    return f"{amount} {cur}" if cur else amount
