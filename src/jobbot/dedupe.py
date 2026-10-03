"""Cross-source duplicate detection. SPEC §5.1.

Two passes: exact id (canonical URL), then fuzzy (same normalised company, near-identical
normalised title). The earliest-seen job survives and absorbs the other's source ids.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from difflib import SequenceMatcher

from jobbot.models import Job

TITLE_SIMILARITY = 0.9

_NOISE = re.compile(
    r"\b(?:m/f/d|m/w/d|f/m/x|w/m/d|h/f|all genders|remote|fully remote|100% remote|hybrid)\b"
    r"|\((?:[^()]*)\)",
    re.IGNORECASE,
)


def norm_text(value: str | None) -> str:
    if not value:
        return ""
    value = _NOISE.sub(" ", value.lower())
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def norm_company(value: str | None) -> str:
    text = norm_text(value)
    return re.sub(
        r"\b(?:gmbh|ltd|limited|inc|llc|sia|sas|sa|bv|ag|plc|co|corp|oy|ab|as)\b", "", text
    ).strip()


def merge(primary: Job, other: Job) -> Job:
    """Fold `other` into `primary`. Earliest first_seen / posted_at win; sources accumulate."""
    source_ids = {**other.source_ids, **primary.source_ids}
    posted = [d for d in (primary.posted_at, other.posted_at) if d is not None]
    return primary.model_copy(
        update={
            "source_ids": source_ids,
            "tags": sorted(set(primary.tags) | set(other.tags)),
            "posted_at": min(posted) if posted else None,
            "first_seen": min(primary.first_seen, other.first_seen),
            "last_seen": max(primary.last_seen, other.last_seen),
            "description_text": primary.description_text or other.description_text,
            "salary_raw": primary.salary_raw or other.salary_raw,
            "location_raw": primary.location_raw or other.location_raw,
            "company": primary.company or other.company,
        }
    )


def _similar(a: str, b: str) -> bool:
    if a == b:
        return True
    if not a or not b:
        return False
    return SequenceMatcher(None, a, b).ratio() >= TITLE_SIMILARITY


def dedupe(jobs: Iterable[Job]) -> list[Job]:
    by_id: dict[str, Job] = {}
    order: list[str] = []
    for job in jobs:
        if job.id in by_id:
            by_id[job.id] = merge(by_id[job.id], job)
        else:
            by_id[job.id] = job
            order.append(job.id)

    kept: list[Job] = []
    by_company: dict[str, list[int]] = {}
    for job_id in order:
        job = by_id[job_id]
        company = norm_company(job.company)
        title = norm_text(job.title)
        if company:
            for idx in by_company.get(company, []):
                if _similar(norm_text(kept[idx].title), title):
                    kept[idx] = merge(kept[idx], job)
                    break
            else:
                by_company.setdefault(company, []).append(len(kept))
                kept.append(job)
        else:
            kept.append(job)
    return kept
