from datetime import UTC, datetime, timedelta
from pathlib import Path

from jobbot.models import Job, RemoteType, RoleFamily
from jobbot.store import SourceRunRecord, Store

NOW = datetime(2026, 10, 1, 6, tzinfo=UTC)


def _job(job_id: str, title: str = "Dev", company: str | None = "Acme", **kw: object) -> Job:
    base: dict[str, object] = {
        "id": job_id,
        "title": title,
        "company": company,
        "url": f"https://acme.com/{job_id}",
        "source": "remotive",
        "source_ids": {"remotive": job_id},
        "first_seen": NOW,
        "last_seen": NOW,
        "regions_allowed": ["EU", "LV"],
        "remote_type": RemoteType.REMOTE,
        "role_family": RoleFamily.SOFTWARE_DEV,
        "tags": ["python"],
        "description_text": "Hello",
    }
    base.update(kw)
    return Job.model_validate(base)


def test_roundtrip_and_new_vs_updated(tmp_path: Path) -> None:
    with Store(tmp_path / "t.sqlite") as store:
        run = store.start_run(NOW - timedelta(days=14), NOW)
        new_ids, updated = store.upsert_jobs([_job("a"), _job("b", title="Ops")], run)
        assert new_ids == ["a", "b"] and updated == 0

        loaded = store.get_job("a")
        assert loaded is not None
        assert loaded.regions_allowed == ["EU", "LV"]
        assert loaded.remote_type is RemoteType.REMOTE
        assert loaded.role_family is RoleFamily.SOFTWARE_DEV
        assert loaded.tags == ["python"]
        assert loaded.first_seen == NOW

        later = NOW + timedelta(days=7)
        run2 = store.start_run(NOW, later)
        new_ids, updated = store.upsert_jobs([_job("a", last_seen=later)], run2)
        assert new_ids == [] and updated == 1
        again = store.get_job("a")
        assert again is not None
        assert again.first_seen == NOW and again.last_seen == later
        assert [j.id for j in store.jobs_first_seen_in(run)] == ["a", "b"]
        assert store.jobs_first_seen_in(run2) == []
        assert store.count_jobs() == 2


def test_cross_source_duplicate_folds_into_existing(tmp_path: Path) -> None:
    with Store(tmp_path / "t.sqlite") as store:
        run = store.start_run(None, NOW)
        store.upsert_jobs(
            [_job("a", title="Senior Backend Engineer (m/f/d)", company="Acme GmbH")], run
        )
        dup = _job(
            "zzz",
            title="Senior Backend Engineer",
            company="ACME",
            source="himalayas",
            source_ids={"himalayas": "77"},
            url="https://himalayas.app/77",
        )
        new_ids, updated = store.upsert_jobs([dup], run)
        assert new_ids == [] and updated == 1
        merged = store.get_job("a")
        assert merged is not None
        assert merged.source_ids == {"remotive": "a", "himalayas": "77"}
        assert store.get_job("zzz") is None


def test_runs_and_source_runs(tmp_path: Path) -> None:
    with Store(tmp_path / "t.sqlite") as store:
        assert store.last_successful_run() is None
        run = store.start_run(NOW - timedelta(days=14), NOW)
        store.record_source_run(
            run, SourceRunRecord("remotive", fetched=10, new=3, duration_ms=120)
        )
        store.record_source_run(
            run, SourceRunRecord("arbeitnow", errors=1, error_message="403 Forbidden")
        )
        store.finish_run(run, "ok", 3, now=NOW + timedelta(minutes=2))
        last = store.last_successful_run()
        assert last is not None
        assert last.run_id == run and last.started_at == NOW and last.new_jobs == 3
        recs = store.source_runs(run)
        assert [r.source for r in recs] == ["arbeitnow", "remotive"]
        assert recs[0].error_message == "403 Forbidden"

        failed = store.start_run(NOW, NOW + timedelta(days=7))
        store.finish_run(failed, "failed", 0)
        still = store.last_successful_run()
        assert still is not None and still.run_id == run


def test_update_scores(tmp_path: Path) -> None:
    with Store(tmp_path / "t.sqlite") as store:
        store.upsert_jobs([_job("a")])
        store.update_scores([_job("a", score=77, score_reasons=["role +30"])])
        job = store.get_job("a")
        assert job is not None and job.score == 77 and job.score_reasons == ["role +30"]
