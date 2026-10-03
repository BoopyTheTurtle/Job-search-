import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import respx

from jobbot.sources import build
from jobbot.sources.himalayas import API_URL

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "himalayas"
SINCE = datetime(2026, 9, 15, tzinfo=UTC)
PARAMS = {"page_size": 2}


def _page(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def _serve(request: httpx.Request) -> httpx.Response:
    offset = request.url.params.get("offset")
    if offset == "0":
        return httpx.Response(200, json=_page("sample.json"))
    if offset == "2":
        return httpx.Response(200, json=_page("page2.json"))
    return httpx.Response(200, json={"jobs": [], "offset": offset, "limit": 2, "totalCount": 4})


@respx.mock
def test_himalayas_maps_fields() -> None:
    route = respx.get(API_URL).mock(side_effect=_serve)
    with httpx.Client() as client:
        jobs = list(build("himalayas", client, PARAMS).fetch(since=None))

    assert route.call_count == 3, "two full pages then an empty one"
    assert route.calls[0].request.url.params["limit"] == "2"
    assert route.calls[1].request.url.params["offset"] == "2"
    assert len(jobs) == 4
    first = jobs[0]
    assert first.source == "himalayas"
    assert first.source_id == first.url
    assert (
        first.url == "https://himalayas.app/companies/acme-analytics/jobs/junior-data-engineer-3001"
    )
    assert first.title == "Junior Data Engineer"
    assert first.company == "Acme Analytics"
    assert first.location_raw == "Germany, Netherlands, Latvia"
    assert first.description_html is not None and "<strong>dbt</strong>" in first.description_html
    assert first.employment_type_raw == "Full Time"
    assert first.salary_raw == "45000 - 60000 EUR"
    assert first.remote_hint is True
    assert first.posted_at == datetime(2026, 9, 29, 10, 15, tzinfo=UTC)
    assert first.posted_at.tzinfo is not None
    assert first.tags == ["Data", "Engineering"]
    assert first.extra["seniority"] == ["Entry Level"]
    assert first.extra["locationRestrictions"] == ["Germany", "Netherlands", "Latvia"]

    sparse = jobs[1]
    assert sparse.location_raw is None
    assert sparse.employment_type_raw is None
    assert sparse.salary_raw is None
    assert sparse.tags == []

    assert jobs[2].salary_raw == "70000 GBP", "open-ended range keeps the known bound"


@respx.mock
def test_himalayas_stops_paginating_once_items_are_older_than_since() -> None:
    route = respx.get(API_URL).mock(side_effect=_serve)
    with httpx.Client() as client:
        jobs = list(build("himalayas", client, PARAMS).fetch(since=SINCE))

    assert route.call_count == 2, "page 2 holds an old item: offset 4 is never requested"
    assert [j.title for j in jobs] == [
        "Junior Data Engineer",
        "Platform Engineer",
        "Backend Developer (Go)",
    ]


@respx.mock
def test_himalayas_respects_limit() -> None:
    route = respx.get(API_URL).mock(side_effect=_serve)
    with httpx.Client() as client:
        jobs = list(build("himalayas", client, PARAMS).fetch(since=None, limit=1))

    assert len(jobs) == 1
    assert route.call_count == 1
    assert route.calls[0].request.url.params["limit"] == "1", "page size shrinks to the limit"


def test_himalayas_caps_page_size_at_api_maximum() -> None:
    with httpx.Client() as client:
        src = build("himalayas", client, {"page_size": 500})
    assert getattr(src, "_page_size") == 20  # noqa: B009
