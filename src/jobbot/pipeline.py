"""Crawl orchestration: sources → normalize → enrich → dedupe → store. SPEC §5.2."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from jobbot.config import SourceConfig
from jobbot.dedupe import dedupe
from jobbot.enrich import enrich
from jobbot.http import SourceError, make_client
from jobbot.models import Job, RawJob
from jobbot.normalize import normalize
from jobbot.sources import build
from jobbot.store import SourceRunRecord, Store

OVERLAP = timedelta(days=1)
FIRST_RUN_LOOKBACK = timedelta(days=14)


def process(raw: RawJob, now: datetime | None = None) -> Job:
    """RawJob → normalized, enriched Job."""
    return enrich(normalize(raw, now), raw)


@dataclass
class RunSummary:
    run_id: str
    since: datetime
    status: str
    new_jobs: int = 0
    sources: list[SourceRunRecord] = field(default_factory=list)

    @property
    def failed_sources(self) -> int:
        return sum(1 for s in self.sources if s.errors)

    @property
    def attempted_sources(self) -> int:
        return sum(1 for s in self.sources if not s.skipped)


def missing_env(cfg: SourceConfig | None) -> list[str]:
    """Names of the credentials a source declares in `env` that are not set (or empty)."""
    if cfg is None:
        return []
    return [name for name in cfg.env if not os.environ.get(name, "").strip()]


def resolve_since(store: Store, since_days: int | None, now: datetime) -> datetime:
    if since_days is not None:
        return now - timedelta(days=since_days)
    last = store.last_successful_run()
    if last is None:
        return now - FIRST_RUN_LOOKBACK
    return last.started_at - OVERLAP


def run_crawl(
    store: Store,
    names: list[str],
    configs: dict[str, SourceConfig],
    *,
    since_days: int | None = None,
    limit: int | None = None,
    now: datetime | None = None,
) -> RunSummary:
    now = now or datetime.now(tz=UTC)
    since = resolve_since(store, since_days, now)
    run_id = store.start_run(since, now)
    summary = RunSummary(run_id=run_id, since=since, status="running")

    with make_client() as client:
        for name in names:
            record = SourceRunRecord(source=name)
            started = time.monotonic()
            raws: list[RawJob] = []
            cfg = configs.get(name)
            absent = missing_env(cfg)
            if absent:
                # A keyed source without its secret is not a failure: it simply does not
                # take part in this run. The digest shows it as skipped.
                record.skipped = True
                record.error_message = "skipped: missing " + ", ".join(absent)
                store.record_source_run(run_id, record)
                summary.sources.append(record)
                continue
            try:
                connector = build(name, client, cfg.params if cfg else {})
                # Collect incrementally: a paginated source that fails on page N (rate
                # limit, outage) still contributes pages 1..N-1 to this run.
                for raw in connector.fetch(since, limit):
                    raws.append(raw)
            except (SourceError, KeyError, ValueError) as exc:
                record.errors = 1
                record.error_message = str(exc)[:500]
            record.fetched = len(raws)
            if raws:
                jobs = dedupe(process(raw, now) for raw in raws)
                new_ids, _updated = store.upsert_jobs(jobs, run_id)
                record.new = len(new_ids)
                summary.new_jobs += len(new_ids)
            record.duration_ms = int((time.monotonic() - started) * 1000)
            store.record_source_run(run_id, record)
            summary.sources.append(record)

    failed, attempted = summary.failed_sources, summary.attempted_sources
    summary.status = "ok" if not attempted or failed * 2 <= attempted else "failed"
    store.finish_run(run_id, summary.status, summary.new_jobs, now=datetime.now(tz=UTC))
    return summary
