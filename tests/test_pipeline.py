import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import respx

from jobbot.config import SourceConfig
from jobbot.models import EmploymentType, RawJob, RemoteType, RoleFamily, Seniority
from jobbot.pipeline import process, resolve_since, run_crawl
from jobbot.sources.remotive import API_URL
from jobbot.store import Store

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "remotive" / "sample.json"
NOW = datetime(2026, 10, 1, 6, tzinfo=UTC)


def test_process_end_to_end() -> None:
    raw = RawJob(
        source="remotive",
        source_id="1",
        url="https://remotive.com/remote-jobs/software-dev/junior-python-developer-1",
        title="Junior Python Developer",
        company="Acme Robotics",
        location_raw="Europe",
        description_html=(
            "<p>We are hiring a junior Python developer to join our fully remote team in Europe. "
            "You will build Django APIs, write tests and review pull requests with the team.</p>"
        ),
        posted_at=datetime(2026, 9, 29, 10, 15),
        salary_raw="€45,000 - €55,000",
        employment_type_raw="full_time",
        remote_hint=True,
        tags=["python", "django"],
    )
    job = process(raw, NOW)
    assert job.language == "en"
    assert job.remote_type is RemoteType.REMOTE
    assert job.regions_allowed == ["EUROPE"]
    assert job.role_family is RoleFamily.SOFTWARE_DEV
    assert job.seniority is Seniority.JUNIOR
    assert job.employment_type is EmploymentType.FULL_TIME
    assert job.posted_at == datetime(2026, 9, 29, 10, 15, tzinfo=UTC)


def test_resolve_since(tmp_path: Path) -> None:
    with Store(tmp_path / "t.sqlite") as store:
        assert resolve_since(store, None, NOW) == NOW - timedelta(days=14)
        assert resolve_since(store, 3, NOW) == NOW - timedelta(days=3)
        run = store.start_run(None, NOW - timedelta(days=7))
        store.finish_run(run, "ok", 0)
        assert resolve_since(store, None, NOW) == NOW - timedelta(days=8)


@respx.mock
def test_run_crawl_stores_and_reports(tmp_path: Path) -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    respx.get(API_URL).mock(return_value=httpx.Response(200, json=payload))
    configs = {"remotive": SourceConfig(terms="https://example.com/terms")}
    with Store(tmp_path / "t.sqlite") as store:
        summary = run_crawl(store, ["remotive", "nope"], configs, since_days=60, now=NOW)
        assert summary.status == "ok"
        assert summary.new_jobs == 2
        by_name = {s.source: s for s in summary.sources}
        assert by_name["remotive"].fetched == 2 and by_name["remotive"].new == 2
        assert by_name["nope"].errors == 1 and "unknown source" in (
            by_name["nope"].error_message or ""
        )
        assert store.count_jobs() == 2
        jobs = store.jobs_first_seen_in(summary.run_id)
        assert {j.title for j in jobs} == {"Junior Python Developer", "Senior Frontend Engineer"}
        us_only = next(j for j in jobs if j.title.startswith("Senior"))
        assert us_only.regions_allowed == ["US"]

        # Second run: nothing new, everything updated.
        summary2 = run_crawl(
            store, ["remotive"], configs, since_days=60, now=NOW + timedelta(days=7)
        )
        assert summary2.new_jobs == 0 and summary2.status == "ok"
        assert store.count_jobs() == 2


@respx.mock
def test_run_crawl_fails_when_majority_of_sources_fail(tmp_path: Path) -> None:
    respx.get(API_URL).mock(return_value=httpx.Response(500))
    with Store(tmp_path / "t.sqlite") as store:
        summary = run_crawl(store, ["remotive"], {}, since_days=7, now=NOW)
        assert summary.status == "failed"
        assert summary.sources[0].errors == 1
        assert store.last_successful_run() is None
