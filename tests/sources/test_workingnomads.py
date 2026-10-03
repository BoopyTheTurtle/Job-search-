import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import respx

from jobbot.sources import build
from jobbot.sources.workingnomads import API_URL

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "workingnomads" / "sample.json"
SINCE = datetime(2026, 9, 15, tzinfo=UTC)


def _payload() -> list[object]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))  # type: ignore[no-any-return]


@respx.mock
def test_workingnomads_maps_fields() -> None:
    route = respx.get(API_URL).mock(return_value=httpx.Response(200, json=_payload()))
    with httpx.Client() as client:
        jobs = list(build("workingnomads", client, {}).fetch(since=None))

    assert route.call_count == 1
    assert len(jobs) == 3
    first = jobs[0]
    assert first.source == "workingnomads"
    assert first.url == "https://www.workingnomads.com/jobs/junior-python-developer-acme-robotics"
    assert first.source_id == first.url, "no id in the payload: the URL is the stable key"
    assert first.title == "Junior Python Developer"
    assert first.company == "Acme Robotics"
    assert first.location_raw == "Europe"
    assert (
        first.description_html is not None and "<strong>Europe</strong>" in first.description_html
    )
    assert first.remote_hint is True
    assert first.posted_at == datetime(2026, 9, 29, 10, 15, tzinfo=UTC)
    assert first.posted_at.tzinfo is not None
    assert first.tags == ["python", "django", "postgresql", "Development"]
    assert first.extra["category"] == "Development"
    assert first.salary_raw is None

    sparse = jobs[1]
    assert sparse.company is None
    assert sparse.tags == []
    assert sparse.extra["category"] is None
    assert sparse.posted_at == datetime(2026, 9, 30, 12, 0, tzinfo=UTC)


@respx.mock
def test_workingnomads_respects_since_and_limit() -> None:
    respx.get(API_URL).mock(return_value=httpx.Response(200, json=_payload()))
    with httpx.Client() as client:
        src = build("workingnomads", client, {})
        recent = list(src.fetch(since=SINCE))
        assert [j.title for j in recent] == ["Junior Python Developer", "Cloud Engineer"]

        limited = list(src.fetch(since=None, limit=1))
        assert [j.title for j in limited] == ["Junior Python Developer"]
