import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import respx

from jobbot.sources import build
from jobbot.sources.jobtech import API_URL, DATA_IT

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "jobtech"


def _sample() -> dict[str, object]:
    return json.loads((FIXTURES / "sample.json").read_text(encoding="utf-8"))  # type: ignore[no-any-return]


@respx.mock
def test_jobtech_maps_fields_and_sends_public_key() -> None:
    route = respx.get(API_URL).mock(return_value=httpx.Response(200, json=_sample()))
    with httpx.Client() as client:
        jobs = list(build("jobtech", client, {}).fetch(since=None))

    assert route.call_count == 1, "a short page ends pagination"
    request = route.calls[0].request
    assert request.headers["api-key"] == "developer"
    assert request.url.params["remote"] == "true"
    assert request.url.params["occupation-field"] == DATA_IT
    assert request.url.params["sort"] == "pubdate-desc"
    assert "published-after" not in request.url.params

    assert len(jobs) == 3
    first = jobs[0]
    assert first.source == "jobtech"
    assert first.source_id == "31548844"
    assert first.url == "https://arbetsformedlingen.se/platsbanken/annonser/31548844"
    assert first.title == "Var med och forma hur AI används på Finansinspektionen"
    assert first.company == "Finansinspektionen"
    assert first.location_raw == "Stockholm, Stockholms län, Sverige"
    assert first.description_html is not None and first.description_html.startswith("<p>")
    assert first.description_text
    assert first.posted_at == datetime(2026, 10, 2, 15, 44, 31, tzinfo=UTC)
    assert first.employment_type_raw == "full_time", "Heltid"
    assert first.remote_hint is None
    assert first.tags == ["IT-arkitekt/Lösningsarkitekt"]
    assert first.extra["apply_url"].startswith("https://www.fi.se/")

    assert jobs[2].employment_type_raw == "contract", "Tidsbegränsad anställning"


@respx.mock
def test_jobtech_sends_published_after_and_drops_older_items() -> None:
    route = respx.get(API_URL).mock(return_value=httpx.Response(200, json=_sample()))
    since = datetime(2026, 10, 1, 0, 0, tzinfo=UTC)
    with httpx.Client() as client:
        jobs = list(build("jobtech", client, {}).fetch(since=since))

    assert route.calls[0].request.url.params["published-after"] == "2026-10-01T00:00:00"
    assert [j.source_id for j in jobs] == ["31548844", "31540686"]


@respx.mock
def test_jobtech_pages_with_offset_and_respects_limit() -> None:
    sample = _sample()
    route = respx.get(API_URL).mock(return_value=httpx.Response(200, json=sample))
    with httpx.Client() as client:
        jobs = list(build("jobtech", client, {"page_size": 3}).fetch(since=None, limit=4))

    assert len(jobs) == 4
    assert [c.request.url.params["offset"] for c in route.calls] == ["0", "3"]


@respx.mock
def test_jobtech_skips_removed_ads() -> None:
    sample = _sample()
    sample["hits"][0]["removed"] = True  # type: ignore[index]
    respx.get(API_URL).mock(return_value=httpx.Response(200, json=sample))
    with httpx.Client() as client:
        jobs = list(build("jobtech", client, {}).fetch(since=None))
    assert "31548844" not in [j.source_id for j in jobs]
