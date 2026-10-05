"""Turn a run's new jobs into a sectioned Digest. SPEC §4."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime

from jobbot.config import Profile
from jobbot.filter import Section, Verdict, evaluate
from jobbot.models import Job
from jobbot.store import SourceRunRecord

ATTRIBUTIONS = {
    "adzuna": ("Jobs by Adzuna", "https://www.adzuna.co.uk"),
    "reed": ("Jobs by Reed", "https://www.reed.co.uk"),
}
"""Credit lines some sources' terms require next to their listings: source -> (text, link)."""


@dataclass
class Digest:
    date: datetime
    run_id: str
    since: datetime | None
    strong: list[Job] = field(default_factory=list)
    possible: list[Job] = field(default_factory=list)
    senior: list[Job] = field(default_factory=list)
    dropped: int = 0
    drop_reasons: dict[str, int] = field(default_factory=dict)
    sources: list[SourceRunRecord] = field(default_factory=list)
    status: str = "ok"
    title: str = ""

    @property
    def heading(self) -> str:
        return f"{self.title} job digest" if self.title else "Job digest"

    @property
    def total_shown(self) -> int:
        return len(self.strong) + len(self.possible) + len(self.senior)

    @property
    def subject(self) -> str:
        count = len(self.strong) + len(self.possible)
        noun = "match" if count == 1 else "matches"
        return f"{self.heading}: {count} new {noun} ({self.date:%Y-%m-%d})"

    def all_jobs(self) -> list[Job]:
        return [*self.strong, *self.possible, *self.senior]

    @property
    def attributions(self) -> list[tuple[str, str]]:
        shown = {job.source for job in self.all_jobs()}
        return [credit for source, credit in sorted(ATTRIBUTIONS.items()) if source in shown]


def build_digest(
    jobs: Iterable[Job],
    profile: Profile,
    *,
    run_id: str,
    since: datetime | None,
    sources: Iterable[SourceRunRecord] = (),
    status: str = "ok",
    title: str = "",
    now: datetime | None = None,
) -> tuple[Digest, list[Verdict]]:
    """Evaluate every job; return the digest and all verdicts (for persisting scores)."""
    now = now or datetime.now(tz=UTC)
    digest = Digest(
        date=now, run_id=run_id, since=since, sources=list(sources), status=status, title=title
    )
    verdicts: list[Verdict] = []
    for job in jobs:
        verdict = evaluate(job, profile, now)
        verdicts.append(verdict)
        if verdict.section is Section.STRONG:
            digest.strong.append(verdict.job)
        elif verdict.section is Section.POSSIBLE:
            digest.possible.append(verdict.job)
        elif verdict.section is Section.SENIOR:
            digest.senior.append(verdict.job)
        else:
            digest.dropped += 1
            key = (verdict.excluded_reason or "score below threshold").split(":")[0]
            digest.drop_reasons[key] = digest.drop_reasons.get(key, 0) + 1

    def order(items: list[Job]) -> list[Job]:
        return sorted(items, key=lambda j: (-j.score, j.posted_at or now, j.title))

    digest.strong = order(digest.strong)
    digest.possible = order(digest.possible)
    digest.senior = order(digest.senior)

    cap = profile.digest.max_items
    if digest.total_shown > cap:
        remaining = cap
        for name in ("strong", "possible", "senior"):
            items: list[Job] = getattr(digest, name)
            setattr(digest, name, items[:remaining])
            remaining = max(0, remaining - len(items))
    return digest, verdicts
