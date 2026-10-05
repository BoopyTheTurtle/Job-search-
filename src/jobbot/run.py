"""`jobbot run`: crawl once → score per search → one digest and email per search.
SPEC §5.2 steps 5-7; ADR-0004."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from jobbot.config import Search, SourceConfig
from jobbot.digest import build_digest, render_html, render_markdown, render_text, send_digest
from jobbot.digest.build import Digest
from jobbot.digest.send import EmailSettings, ResendError
from jobbot.filter import Verdict
from jobbot.models import Job
from jobbot.pipeline import RunSummary, run_crawl
from jobbot.store import Store


@dataclass
class DigestResult:
    search: str
    shown: int
    strong: int
    possible: int
    senior: int
    dropped: int
    digest_path: str
    email: str  # "sent:<id>" | "skipped:<why>" | "failed:<why>"


@dataclass
class RunResult:
    run_id: str
    status: str
    new_jobs: int
    digests: list[DigestResult] = field(default_factory=list)

    @property
    def email_failed(self) -> bool:
        return any(d.email.startswith("failed") for d in self.digests)


def _send(digest: Digest, search: Search) -> str:
    settings = EmailSettings.from_env(search.digest.to)
    if settings is None:
        return "skipped:no RESEND_API_KEY/DIGEST_FROM/DIGEST_TO"
    if digest.total_shown == 0:
        return "skipped:nothing to show"
    try:
        message_id = send_digest(
            settings, subject=digest.subject, html=render_html(digest), text=render_text(digest)
        )
    except ResendError as exc:
        return f"failed:{exc}"
    return f"sent:{message_id}"


def best_scores(verdicts_by_search: dict[str, list[Verdict]]) -> list[Job]:
    """One score per job for the store: the highest any search gave it, reasons tagged
    with that search's name."""
    best: dict[str, tuple[str, Job]] = {}
    for name, verdicts in verdicts_by_search.items():
        for v in verdicts:
            held = best.get(v.job.id)
            if held is None or v.job.score > held[1].score:
                best[v.job.id] = (name, v.job)
    return [
        job.model_copy(update={"score_reasons": [f"[{name}]", *job.score_reasons]})
        for name, job in best.values()
    ]


def run_all(
    store: Store,
    searches: Sequence[Search],
    names: list[str],
    configs: dict[str, SourceConfig],
    *,
    out_dir: Path,
    send: bool = True,
    since_days: int | None = None,
    limit: int | None = None,
    now: datetime | None = None,
) -> RunResult:
    now = now or datetime.now(tz=UTC)
    stamp = now.strftime("%Y-%m-%d")
    crawl: RunSummary = run_crawl(
        store, names, configs, searches=searches, since_days=since_days, limit=limit, now=now
    )
    new_jobs = store.jobs_first_seen_in(crawl.run_id)
    result = RunResult(run_id=crawl.run_id, status=crawl.status, new_jobs=crawl.new_jobs)
    verdicts_by_search: dict[str, list[Verdict]] = {}

    for search in searches:
        digest, verdicts = build_digest(
            new_jobs,
            search,
            run_id=crawl.run_id,
            since=crawl.since,
            sources=crawl.sources,
            status=crawl.status,
            title=search.title,
            now=now,
        )
        verdicts_by_search[search.name] = verdicts
        digest_dir = out_dir / "digests" / search.name
        digest_dir.mkdir(parents=True, exist_ok=True)
        digest_path = digest_dir / f"{stamp}.md"
        digest_path.write_text(render_markdown(digest), encoding="utf-8")
        result.digests.append(
            DigestResult(
                search=search.name,
                shown=digest.total_shown,
                strong=len(digest.strong),
                possible=len(digest.possible),
                senior=len(digest.senior),
                dropped=digest.dropped,
                digest_path=str(digest_path),
                email=_send(digest, search) if send else "skipped:disabled",
            )
        )

    store.update_scores(best_scores(verdicts_by_search))
    runs = out_dir / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    payload = {
        **asdict(result),
        "date": now.isoformat(),
        "sources": [asdict(s) for s in crawl.sources],
    }
    (runs / f"{stamp}.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    store.finish_run(
        crawl.run_id,
        crawl.status,
        crawl.new_jobs,
        digest_path=";".join(d.digest_path for d in result.digests),
        now=now,
    )
    return result
