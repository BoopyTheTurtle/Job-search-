import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import respx

from jobbot.sources import build
from jobbot.sources.arbeitnow import API_URL

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "arbeitnow"
SINCE = datetime(2026, 9, 15, tzinfo=UTC)


def _page(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def _serve(request: httpx.Request) -> httpx.Response:
    page = request.url.params.get("page", "1")
    if page == "1":
        return httpx.Response(200, json=_page("sample.json"))
    if page == "2":
        return httpx.Response(200, json=_page("page2.json"))
    return httpx.Response(200, json={"data": [], "links": {"next": None}})


@respx.mock
def test_arbeitnow_maps_fields() -> None:
    route = respx.get(API_URL).mock(side_effect=_serve)
    with httpx.Client() as client:
        jobs = list(build("arbeitnow", client, {}).fetch(since=None))

    assert route.call_count == 3, "follows links.next until it is null"
    assert [j.source_id for j in jobs] == [
        "junior-backend-developer-python-berlin-remote-1001",
        "werkstudent-it-support-muenchen-1002",
        "devops-engineer-kubernetes-remote-eu-1003",
        "senior-java-architect-hamburg-0999",
    ]
    first = jobs[0]
    assert first.source == "arbeitnow"
    assert first.title == "Junior Backend Developer (Python)"
    assert first.company == "Acme Robotics GmbH"
    assert first.location_raw == "Berlin"
    assert first.url.endswith("junior-backend-developer-python-berlin-remote-1001")
    assert (
        first.description_html is not None and "<strong>junior</strong>" in first.description_html
    )
    assert first.employment_type_raw == "full-time"
    assert first.remote_hint is True
    assert first.posted_at == datetime(2026, 9, 29, 10, 15, tzinfo=UTC)
    assert first.posted_at.tzinfo is not None
    assert "Python" in first.tags
    assert first.salary_raw is None

    sparse = jobs[1]
    assert sparse.company is None
    assert sparse.location_raw is None
    assert sparse.employment_type_raw is None
    assert sparse.remote_hint is False
    assert sparse.tags == []


@respx.mock
def test_arbeitnow_stops_paginating_once_items_are_older_than_since() -> None:
    route = respx.get(API_URL).mock(side_effect=_serve)
    with httpx.Client() as client:
        jobs = list(build("arbeitnow", client, {}).fetch(since=SINCE))

    assert route.call_count == 2, "page 2 holds an item older than since: page 3 is never fetched"
    assert [j.source_id for j in jobs] == [
        "junior-backend-developer-python-berlin-remote-1001",
        "werkstudent-it-support-muenchen-1002",
        "devops-engineer-kubernetes-remote-eu-1003",
    ]


@respx.mock
def test_arbeitnow_respects_limit() -> None:
    route = respx.get(API_URL).mock(side_effect=_serve)
    with httpx.Client() as client:
        jobs = list(build("arbeitnow", client, {}).fetch(since=None, limit=1))

    assert len(jobs) == 1
    assert route.call_count == 1
