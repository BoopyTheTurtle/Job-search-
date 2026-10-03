import base64
import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
import respx

from jobbot.http import SourceError
from jobbot.sources import build
from jobbot.sources.reed import API_URL, from_dmy

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "reed"
PARAMS = {"keywords": ["remote developer", "remote data"], "page_size": 3, "max_pages": 2}


@pytest.fixture(autouse=True)
def _key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REED_API_KEY", "test-key")


def _serve(request: httpx.Request) -> httpx.Response:
    if request.url.params["resultsToSkip"] != "0":
        return httpx.Response(200, json={"results": [], "totalResults": 3})
    return httpx.Response(200, json=json.loads((FIXTURES / "sample.json").read_text("utf-8")))


@respx.mock
def test_reed_maps_fields_and_authenticates() -> None:
    route = respx.get(API_URL).mock(side_effect=_serve)
    with httpx.Client() as client:
        jobs = list(build("reed", client, PARAMS).fetch(since=None))

    expected = "Basic " + base64.b64encode(b"test-key:").decode()
    assert route.calls[0].request.headers["Authorization"] == expected
    assert route.calls[0].request.url.params["keywords"] == "remote developer"
    assert route.calls[0].request.url.params["resultsToTake"] == "3"
    # Each query: a full page, then an empty one. The second query repeats the same jobs.
    assert route.call_count == 4
    assert len(jobs) == 3, "duplicates across keyword queries are skipped"

    first = jobs[0]
    assert first.source == "reed"
    assert first.source_id == "55012345"
    assert first.url == "https://www.reed.co.uk/jobs/junior-python-developer-fully-remote/55012345"
    assert first.title == "Junior Python Developer - Fully Remote"
    assert first.company == "Example Digital Ltd"
    assert first.location_raw == "Remote"
    assert first.description_text is not None and "fully remote" in first.description_text
    assert first.posted_at == datetime(2026, 9, 29, tzinfo=UTC)
    assert first.salary_raw == "30000 - 38000 GBP"
    assert first.employment_type_raw is None
    assert first.remote_hint is None

    contract = jobs[1]
    assert contract.salary_raw is None
    assert contract.employment_type_raw == "contract"
    assert jobs[2].salary_raw is None, "zero bounds mean no salary"


@respx.mock
def test_reed_drops_postings_older_than_since() -> None:
    respx.get(API_URL).mock(side_effect=_serve)
    with httpx.Client() as client:
        jobs = list(build("reed", client, PARAMS).fetch(since=datetime(2026, 9, 15, tzinfo=UTC)))
    assert [j.source_id for j in jobs] == ["55012345", "55012399"]


@respx.mock
def test_reed_respects_limit() -> None:
    route = respx.get(API_URL).mock(side_effect=_serve)
    with httpx.Client() as client:
        jobs = list(build("reed", client, PARAMS).fetch(since=None, limit=1))
    assert len(jobs) == 1
    assert route.call_count == 1
    assert route.calls[0].request.url.params["resultsToTake"] == "1"


def test_reed_requires_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("REED_API_KEY")
    with httpx.Client() as client, pytest.raises(SourceError):
        list(build("reed", client, PARAMS).fetch(since=None))


def test_from_dmy() -> None:
    assert from_dmy("03/10/2026") == datetime(2026, 10, 3, tzinfo=UTC)
    assert from_dmy("2026-10-03") is None
    assert from_dmy(None) is None
