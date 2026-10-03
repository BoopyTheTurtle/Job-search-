"""`jobbot run`: crawl → score → digest → files → email. SPEC §5.2 steps 5-7."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from jobbot.config import Profile, SourceConfig
from jobbot.digest import build_digest, render_html, render_markdown, render_text, send_digest
from jobbot.digest.send import EmailSettings, ResendError
from jobbot.pipeline import RunSummary, run_crawl
from jobbot.store import Store


@dataclass
class RunResult:
    run_id: str
    status: str
    new_jobs: int
    shown: int
    strong: int
    possible: int
    senior: int
    dropped: int
    digest_path: str
    email: str  # "sent:<id>" | "skipped:<why>" | "failed:<why>"


def write_outputs(
    out_dir: Path,
    date: datetime,
    markdown: str,
    summary: RunResult,
    sources: list[dict[str, object]],
) -> Path:
    digests = out_dir / "digests"
    runs = out_dir / "runs"
    digests.mkdir(parents=True, exist_ok=True)
    runs.mkdir(parents=True, exist_ok=True)
    stamp = date.strftime("%Y-%m-%d")
    digest_path = digests / f"{stamp}.md"
    digest_path.write_text(markdown, encoding="utf-8")
    summary.digest_path = str(digest_path)
    payload = {**asdict(summary), "date": date.isoformat(), "sources": sources}
    (runs / f"{stamp}.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return digest_path


def run_all(
    store: Store,
    profile: Profile,
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
    crawl: RunSummary = run_crawl(
        store, names, configs, since_days=since_days, limit=limit, now=now
    )
    new_jobs = store.jobs_first_seen_in(crawl.run_id)
    digest, verdicts = build_digest(
        new_jobs,
        profile,
        run_id=crawl.run_id,
        since=crawl.since,
        sources=crawl.sources,
        status=crawl.status,
        now=now,
    )
    store.update_scores(v.job for v in verdicts)

    markdown = render_markdown(digest)
    email_status = "skipped:disabled"
    if send:
        settings = EmailSettings.from_env(profile.digest.to)
        if settings is None:
            email_status = "skipped:no RESEND_API_KEY/DIGEST_FROM/DIGEST_TO"
        elif digest.total_shown == 0:
            email_status = "skipped:nothing to show"
        else:
            try:
                message_id = send_digest(
                    settings,
                    subject=digest.subject,
                    html=render_html(digest),
                    text=render_text(digest),
                )
                email_status = f"sent:{message_id}"
            except ResendError as exc:
                email_status = f"failed:{exc}"

    result = RunResult(
        run_id=crawl.run_id,
        status=crawl.status,
        new_jobs=crawl.new_jobs,
        shown=digest.total_shown,
        strong=len(digest.strong),
        possible=len(digest.possible),
        senior=len(digest.senior),
        dropped=digest.dropped,
        digest_path="",
        email=email_status,
    )
    sources = [asdict(s) for s in crawl.sources]
    digest_path = write_outputs(out_dir, now, markdown, result, sources)
    result.digest_path = str(digest_path)
    store.finish_run(
        crawl.run_id, crawl.status, crawl.new_jobs, digest_path=str(digest_path), now=now
    )
    return result
