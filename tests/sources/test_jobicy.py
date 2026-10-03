import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import respx

from jobbot.sources import build
from jobbot.sources.jobicy import API_URL

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "jobicy" / "sample.json"
SINCE = datetime(2026, 9, 15, tzinfo=UTC)


def _payload() -> dict[str, object]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))  # type: ignore[no-any-return]


@respx.mock
def test_jobicy_maps_fields() -> None:
    route = respx.get(API_URL).mock(return_value=httpx.Response(200, json=_payload()))
    with httpx.Client() as client:
        jobs = list(build("jobicy", client, {}).fetch(since=None))

    assert route.call_count == 1, "Jobicy asks for at most one poll per hour: one per run"
    sent = route.calls[0].request.url.params
    assert sent["geo"] == "europe", "default geo is europe"
    assert sent["count"] == "50"
    assert "industry" not in sent

    assert [j.source_id for j in jobs] == ["4001", "4002", "3999"]
    first = jobs[0]
    assert first.source == "jobicy"
    assert first.url == "https://jobicy.com/jobs/4001-junior-full-stack-developer"
    assert first.title == "Junior Full Stack Developer"
    assert first.company == "Acme Robotics"
    assert first.location_raw == "Europe"
    assert first.description_html is not None and "<strong>React</strong>" in first.description_html
    assert first.employment_type_raw == "full-time"
    assert first.salary_raw == "40000 - 55000 EUR"
    assert first.remote_hint is True
    assert first.posted_at == datetime(2026, 9, 29, 10, 15, tzinfo=UTC)
    assert first.posted_at.tzinfo is not None
    assert first.tags == ["Software Engineering", "full-time"]
    assert first.extra["jobLevel"] == "Junior"

    sparse = jobs[1]
    assert sparse.employment_type_raw is None
    assert sparse.salary_raw is None
    assert sparse.extra["jobExcerpt"] == ""


@respx.mock
def test_jobicy_passes_configured_filters() -> None:
    route = respx.get(API_URL).mock(return_value=httpx.Response(200, json=_payload()))
    params = {"geo": "anywhere", "industry": "dev", "tag": "python"}
    with httpx.Client() as client:
        list(build("jobicy", client, params).fetch(since=None, limit=10))

    sent = route.calls[0].request.url.params
    assert sent["geo"] == "anywhere"
    assert sent["industry"] == "dev"
    assert sent["tag"] == "python"
    assert sent["count"] == "10", "count follows limit when it is below the API maximum"


@respx.mock
def test_jobicy_respects_since_and_limit() -> None:
    respx.get(API_URL).mock(return_value=httpx.Response(200, json=_payload()))
    with httpx.Client() as client:
        src = build("jobicy", client, {})
        recent = list(src.fetch(since=SINCE))
        assert [j.source_id for j in recent] == ["4001", "4002"]

        limited = list(src.fetch(since=None, limit=1))
        assert [j.source_id for j in limited] == ["4001"]
