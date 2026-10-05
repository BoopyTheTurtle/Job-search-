"""Employer watchlist shared by the ATS connectors (Greenhouse, SmartRecruiters, Recruitee).

No @register here; the registry's module discovery imports this file harmlessly.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable, Iterator
from typing import Any

from jobbot.config import load_companies
from jobbot.http import SourceError
from jobbot.models import RawJob

log = logging.getLogger(__name__)


def slugs(params: dict[str, Any], ats: str) -> list[str]:
    """Board slugs to crawl: `params["companies"]` when given (tests, one-off runs), else
    every enabled company in config/companies.yaml whose `ats` matches."""
    given = params.get("companies")
    if given is not None:
        items = given if isinstance(given, list) else [given]
        return [str(s) for s in items if str(s).strip()]
    return [c.slug for c in load_companies() if c.enabled and c.ats == ats]


def crawl_boards(
    name: str,
    boards: list[str],
    fetch_board: Callable[[str], Iterable[RawJob]],
    limit: int | None,
) -> Iterator[RawJob]:
    """Yield each board's postings. One failing board is logged and skipped; the source
    fails only when every board fails."""
    emitted = 0
    failures: list[str] = []
    for board in boards:
        try:
            for job in fetch_board(board):
                yield job
                emitted += 1
                if limit and emitted >= limit:
                    return
        except SourceError as exc:
            log.warning("%s %s failed: %s", name, board, exc)
            failures.append(board)
    if failures and len(failures) == len(boards):
        raise SourceError(f"every {name} board failed: {', '.join(failures)}")


def arrangement(remote: Any, hybrid: Any, location: str | None) -> tuple[bool | None, str | None]:
    """Turn an ATS's structured remote/hybrid flags into (remote_hint, location_raw).
    The remote classifier reads hybrid from the location header, so a hybrid job gets
    "(hybrid)" appended; a job flagged neither remote nor hybrid is on-site."""
    if remote is True:
        return True, location
    if hybrid is True:
        return False, f"{location} (hybrid)" if location else "hybrid"
    if remote is False:
        return False, location
    return None, location


def names(ats: str) -> dict[str, str]:
    """slug → display name from the watchlist, for ATSs whose own company field holds a
    legal entity ("Corporate and Acquisition Services AB") rather than the brand."""
    return {c.slug: c.name for c in load_companies() if c.ats == ats}
