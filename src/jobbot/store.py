"""SQLite persistence. SPEC §6 tables: jobs, sightings, runs, source_runs, feedback."""

from __future__ import annotations

import json
import sqlite3
import uuid
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import TracebackType
from typing import Any

from jobbot.dedupe import merge, norm_company, norm_text
from jobbot.models import Job

SCHEMA_VERSION = 2

# Incremental migrations keyed by the version they upgrade *to*. Each statement list is
# applied inside one transaction; `CREATE TABLE IF NOT EXISTS` in _SCHEMA already covers
# fresh databases, so migrations only touch existing tables.
_MIGRATIONS: dict[int, list[str]] = {
    2: ["ALTER TABLE source_runs ADD COLUMN skipped INTEGER NOT NULL DEFAULT 0"],
}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT,
    url TEXT NOT NULL,
    source TEXT NOT NULL,
    source_ids TEXT NOT NULL,
    location_raw TEXT,
    remote_type TEXT NOT NULL,
    regions_allowed TEXT NOT NULL,
    employment_type TEXT NOT NULL,
    seniority TEXT NOT NULL,
    role_family TEXT NOT NULL,
    language TEXT,
    salary_raw TEXT,
    salary_min INTEGER,
    salary_max INTEGER,
    salary_currency TEXT,
    salary_period TEXT,
    posted_at TEXT,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    description_text TEXT NOT NULL,
    tags TEXT NOT NULL,
    score INTEGER NOT NULL DEFAULT 0,
    score_reasons TEXT NOT NULL DEFAULT '[]',
    company_norm TEXT NOT NULL DEFAULT '',
    title_norm TEXT NOT NULL DEFAULT '',
    first_run_id TEXT
);
CREATE INDEX IF NOT EXISTS jobs_company_title ON jobs (company_norm, title_norm);
CREATE INDEX IF NOT EXISTS jobs_first_run ON jobs (first_run_id);
CREATE TABLE IF NOT EXISTS sightings (
    job_id TEXT NOT NULL REFERENCES jobs(id),
    source TEXT NOT NULL,
    source_id TEXT NOT NULL,
    url TEXT NOT NULL,
    seen_at TEXT NOT NULL,
    run_id TEXT
);
CREATE INDEX IF NOT EXISTS sightings_job ON sightings (job_id);
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    since TEXT,
    status TEXT NOT NULL,
    new_jobs INTEGER NOT NULL DEFAULT 0,
    digest_path TEXT
);
CREATE TABLE IF NOT EXISTS source_runs (
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    source TEXT NOT NULL,
    fetched INTEGER NOT NULL DEFAULT 0,
    new INTEGER NOT NULL DEFAULT 0,
    errors INTEGER NOT NULL DEFAULT 0,
    duration_ms INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    skipped INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS feedback (
    job_id TEXT NOT NULL,
    verdict TEXT NOT NULL,
    note TEXT,
    at TEXT NOT NULL
);
"""

_JOB_COLUMNS = (
    "id",
    "title",
    "company",
    "url",
    "source",
    "source_ids",
    "location_raw",
    "remote_type",
    "regions_allowed",
    "employment_type",
    "seniority",
    "role_family",
    "language",
    "salary_raw",
    "salary_min",
    "salary_max",
    "salary_currency",
    "salary_period",
    "posted_at",
    "first_seen",
    "last_seen",
    "description_text",
    "tags",
    "score",
    "score_reasons",
)


@dataclass
class SourceRunRecord:
    source: str
    fetched: int = 0
    new: int = 0
    errors: int = 0
    duration_ms: int = 0
    error_message: str | None = None
    skipped: bool = False
    """True when the source was not attempted (e.g. its API key is not configured)."""


@dataclass
class RunRecord:
    run_id: str
    started_at: datetime
    finished_at: datetime | None
    since: datetime | None
    status: str
    new_jobs: int
    digest_path: str | None


def _iso(value: datetime | None) -> str | None:
    return value.astimezone(UTC).isoformat() if value else None


def _dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _row_to_job(row: sqlite3.Row) -> Job:
    data: dict[str, Any] = {col: row[col] for col in _JOB_COLUMNS}
    data["source_ids"] = json.loads(row["source_ids"])
    data["regions_allowed"] = json.loads(row["regions_allowed"])
    data["tags"] = json.loads(row["tags"])
    data["score_reasons"] = json.loads(row["score_reasons"])
    return Job.model_validate(data)


def _job_to_params(job: Job, run_id: str | None) -> dict[str, Any]:
    return {
        "id": job.id,
        "title": job.title,
        "company": job.company,
        "url": job.url,
        "source": job.source,
        "source_ids": json.dumps(job.source_ids, sort_keys=True),
        "location_raw": job.location_raw,
        "remote_type": job.remote_type.value,
        "regions_allowed": json.dumps(job.regions_allowed),
        "employment_type": job.employment_type.value,
        "seniority": job.seniority.value,
        "role_family": job.role_family.value,
        "language": job.language,
        "salary_raw": job.salary_raw,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "salary_currency": job.salary_currency,
        "salary_period": job.salary_period,
        "posted_at": _iso(job.posted_at),
        "first_seen": _iso(job.first_seen),
        "last_seen": _iso(job.last_seen),
        "description_text": job.description_text,
        "tags": json.dumps(job.tags),
        "score": job.score,
        "score_reasons": json.dumps(job.score_reasons),
        "company_norm": norm_company(job.company),
        "title_norm": norm_text(job.title),
        "first_run_id": run_id,
    }


class Store:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._init_schema()

    def _init_schema(self) -> None:
        with self._conn:
            self._conn.executescript(_SCHEMA)
            row = self._conn.execute("SELECT version FROM schema_version").fetchone()
            if row is None:
                self._conn.execute("INSERT INTO schema_version VALUES (?)", (SCHEMA_VERSION,))
                return
            current = int(row["version"])
            for version in range(current + 1, SCHEMA_VERSION + 1):
                for statement in _MIGRATIONS.get(version, []):
                    try:
                        self._conn.execute(statement)
                    except sqlite3.OperationalError as exc:
                        # The column already exists when a fresh _SCHEMA created the
                        # table on a database whose version row lagged behind.
                        if "duplicate column" not in str(exc).lower():
                            raise
                self._conn.execute("UPDATE schema_version SET version = ?", (version,))

    def schema_version(self) -> int:
        row = self._conn.execute("SELECT version FROM schema_version").fetchone()
        return int(row["version"]) if row else 0

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> Store:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    # Runs -------------------------------------------------------------------------------

    def start_run(self, since: datetime | None, now: datetime | None = None) -> str:
        run_id = uuid.uuid4().hex[:12]
        now = now or datetime.now(tz=UTC)
        with self._conn:
            self._conn.execute(
                "INSERT INTO runs (run_id, started_at, since, status) VALUES (?, ?, ?, 'running')",
                (run_id, _iso(now), _iso(since)),
            )
        return run_id

    def finish_run(
        self,
        run_id: str,
        status: str,
        new_jobs: int,
        digest_path: str | None = None,
        now: datetime | None = None,
    ) -> None:
        now = now or datetime.now(tz=UTC)
        with self._conn:
            self._conn.execute(
                "UPDATE runs SET finished_at = ?, status = ?, new_jobs = ?, digest_path = ? "
                "WHERE run_id = ?",
                (_iso(now), status, new_jobs, digest_path, run_id),
            )

    def last_successful_run(self) -> RunRecord | None:
        row = self._conn.execute(
            "SELECT * FROM runs WHERE status = 'ok' ORDER BY started_at DESC LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        return RunRecord(
            run_id=row["run_id"],
            started_at=datetime.fromisoformat(row["started_at"]),
            finished_at=_dt(row["finished_at"]),
            since=_dt(row["since"]),
            status=row["status"],
            new_jobs=row["new_jobs"],
            digest_path=row["digest_path"],
        )

    def record_source_run(self, run_id: str, record: SourceRunRecord) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT INTO source_runs (run_id, source, fetched, new, errors, duration_ms, "
                "error_message, skipped) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    run_id,
                    record.source,
                    record.fetched,
                    record.new,
                    record.errors,
                    record.duration_ms,
                    record.error_message,
                    int(record.skipped),
                ),
            )

    def source_runs(self, run_id: str) -> list[SourceRunRecord]:
        rows = self._conn.execute(
            "SELECT * FROM source_runs WHERE run_id = ? ORDER BY source", (run_id,)
        ).fetchall()
        return [
            SourceRunRecord(
                source=r["source"],
                fetched=r["fetched"],
                new=r["new"],
                errors=r["errors"],
                duration_ms=r["duration_ms"],
                error_message=r["error_message"],
                skipped=bool(r["skipped"]),
            )
            for r in rows
        ]

    # Jobs -------------------------------------------------------------------------------

    def get_job(self, job_id: str) -> Job | None:
        row = self._conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return _row_to_job(row) if row else None

    def _find_existing(self, job: Job) -> Job | None:
        row = self._conn.execute("SELECT * FROM jobs WHERE id = ?", (job.id,)).fetchone()
        if row is None:
            company_norm = norm_company(job.company)
            if company_norm:
                row = self._conn.execute(
                    "SELECT * FROM jobs WHERE company_norm = ? AND title_norm = ? LIMIT 1",
                    (company_norm, norm_text(job.title)),
                ).fetchone()
        return _row_to_job(row) if row else None

    def upsert_jobs(self, jobs: Iterable[Job], run_id: str | None = None) -> tuple[list[str], int]:
        """Insert new jobs, fold repeats into existing rows. Returns (new ids, updated count)."""
        new_ids: list[str] = []
        updated = 0
        with self._conn:
            for job in jobs:
                existing = self._find_existing(job)
                if existing is None:
                    params = _job_to_params(job, run_id)
                    cols = ", ".join(params)
                    placeholders = ", ".join(f":{c}" for c in params)
                    self._conn.execute(f"INSERT INTO jobs ({cols}) VALUES ({placeholders})", params)
                    new_ids.append(job.id)
                    target_id = job.id
                else:
                    merged = merge(existing, job)
                    params = _job_to_params(merged, None)
                    params.pop("first_run_id")
                    params.pop("id")
                    assignments = ", ".join(f"{c} = :{c}" for c in params)
                    params["id"] = existing.id
                    self._conn.execute(f"UPDATE jobs SET {assignments} WHERE id = :id", params)
                    updated += 1
                    target_id = existing.id
                for source, source_id in job.source_ids.items():
                    self._conn.execute(
                        "INSERT INTO sightings (job_id, source, source_id, url, seen_at, run_id) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (target_id, source, source_id, job.url, _iso(job.last_seen), run_id),
                    )
        return new_ids, updated

    def update_scores(self, jobs: Iterable[Job]) -> None:
        with self._conn:
            self._conn.executemany(
                "UPDATE jobs SET score = ?, score_reasons = ? WHERE id = ?",
                [(j.score, json.dumps(j.score_reasons), j.id) for j in jobs],
            )

    def jobs_first_seen_in(self, run_id: str) -> list[Job]:
        rows = self._conn.execute(
            "SELECT * FROM jobs WHERE first_run_id = ? ORDER BY posted_at DESC, title", (run_id,)
        ).fetchall()
        return [_row_to_job(r) for r in rows]

    def iter_jobs(self) -> Iterator[Job]:
        for row in self._conn.execute("SELECT * FROM jobs ORDER BY first_seen DESC"):
            yield _row_to_job(row)

    def count_jobs(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) AS n FROM jobs").fetchone()
        return int(row["n"])

    # Feedback ---------------------------------------------------------------------------

    def add_feedback(self, job_id: str, verdict: str, note: str | None = None) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT INTO feedback (job_id, verdict, note, at) VALUES (?, ?, ?, ?)",
                (job_id, verdict, note, _iso(datetime.now(tz=UTC))),
            )
