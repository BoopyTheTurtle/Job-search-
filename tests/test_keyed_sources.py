"""Keyed sources are skipped, not failed, when their credentials are absent."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from jobbot.config import SourceConfig
from jobbot.digest import build_digest, render_markdown
from jobbot.pipeline import missing_env, run_crawl
from jobbot.store import SourceRunRecord, Store

NOW = datetime(2026, 10, 7, 6, tzinfo=UTC)


def test_missing_env_lists_unset_and_blank_names(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JOBBOT_TEST_A", raising=False)
    monkeypatch.setenv("JOBBOT_TEST_B", "   ")
    monkeypatch.setenv("JOBBOT_TEST_C", "set")
    cfg = SourceConfig(terms="https://x", env=["JOBBOT_TEST_A", "JOBBOT_TEST_B", "JOBBOT_TEST_C"])
    assert missing_env(cfg) == ["JOBBOT_TEST_A", "JOBBOT_TEST_B"]
    assert missing_env(None) == []


def test_run_crawl_skips_keyed_source_without_secret(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("JOBBOT_TEST_KEY", raising=False)
    configs = {"needs_key": SourceConfig(terms="https://x", env=["JOBBOT_TEST_KEY"])}
    with Store(tmp_path / "t.sqlite") as store:
        summary = run_crawl(store, ["needs_key"], configs, since_days=7, now=NOW)
        rec = summary.sources[0]
        assert rec.skipped is True and rec.errors == 0
        assert rec.error_message == "skipped: missing JOBBOT_TEST_KEY"
        # A skipped source neither counts as attempted nor as failed.
        assert summary.status == "ok"
        stored = store.source_runs(summary.run_id)
        assert stored[0].skipped is True


def test_digest_shows_skipped_sources_distinctly() -> None:
    sources = [
        SourceRunRecord("adzuna", skipped=True, error_message="skipped: missing ADZUNA_APP_ID"),
        SourceRunRecord("remotive", fetched=3, new=1, duration_ms=100),
    ]
    from jobbot.config import Profile

    digest, _ = build_digest([], Profile(), run_id="r", since=None, sources=sources, now=NOW)
    md = render_markdown(digest)
    assert "| adzuna | 0 | 0 | skipped: missing ADZUNA_APP_ID |" in md
    assert "| remotive | 3 | 1 | ok (100 ms) |" in md


def test_schema_migrates_v1_database(tmp_path: Path) -> None:
    import sqlite3

    path = tmp_path / "old.sqlite"
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE schema_version (version INTEGER NOT NULL);
        INSERT INTO schema_version VALUES (1);
        CREATE TABLE source_runs (
            run_id TEXT NOT NULL, source TEXT NOT NULL,
            fetched INTEGER NOT NULL DEFAULT 0, new INTEGER NOT NULL DEFAULT 0,
            errors INTEGER NOT NULL DEFAULT 0, duration_ms INTEGER NOT NULL DEFAULT 0,
            error_message TEXT
        );
        INSERT INTO source_runs (run_id, source) VALUES ('r1', 'remotive');
        """
    )
    conn.commit()
    conn.close()

    with Store(path) as store:
        assert store.schema_version() == 2
        recs = store.source_runs("r1")
        assert recs[0].skipped is False
        store.record_source_run("r1", SourceRunRecord("adzuna", skipped=True))
        assert any(r.skipped for r in store.source_runs("r1"))
