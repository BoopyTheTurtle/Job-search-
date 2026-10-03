import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
import respx

from jobbot.http import SourceError
from jobbot.sources import build
from jobbot.sources.adzuna import max_days_old

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "adzuna"
SINCE = datetime(2026, 9, 15, tzinfo=UTC)
PARAMS = {"countries": ["de", "gb"], "results_per_page": 3, "max_pages": 2, "page_delay": 0}
ROUTE = r"https://api\.adzuna\.com/v1/api/jobs/(?P<country>[a-z]{2})/search/(?P<page>\d+)"


@pytest.fixture(autouse=True)
def _keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADZUNA_APP_ID", "test-id")
    monkeypatch.setenv("ADZUNA_APP_KEY", "test-key")


def _serve(request: httpx.Request, country: str, page: str) -> httpx.Response:
    if page != "1":
        return httpx.Response(200, json={"count": 0, "results": []})
    path = FIXTURES / f"{country}.json"
    if not path.exists():
        return httpx.Response(400, json={"exception": "UNSUPPORTED_COUNTRY"})
    return httpx.Response(200, json=json.loads(path.read_text(encoding="utf-8")))


@respx.mock
def test_adzuna_maps_fields_and_sends_credentials() -> None:
    route = respx.get(url__regex=ROUTE).mock(side_effect=_serve)
    with httpx.Client() as client:
        jobs = list(build("adzuna", client, PARAMS).fetch(since=None))

    # de: full page of 3 -> page 2 (empty); gb: short page -> stop.
    assert [c.request.url.path for c in route.calls] == [
        "/v1/api/jobs/de/search/1",
        "/v1/api/jobs/de/search/2",
        "/v1/api/jobs/gb/search/1",
    ]
    query = route.calls[0].request.url.params
    assert query["app_id"] == "test-id" and query["app_key"] == "test-key"
    assert query["what"] == "remote"
    assert query["category"] == "it-jobs"
    assert query["sort_by"] == "date"
    assert query["max_days_old"] == "7"
    assert query["results_per_page"] == "3"

    assert len(jobs) == 4
    first = jobs[0]
    assert first.source == "adzuna"
    assert first.source_id == "de:4870012345"
    assert first.url.startswith("https://www.adzuna.de/details/4870012345")
    assert first.title == "Junior Python Entwickler (m/w/d) - 100% Remote"
    assert first.company == "Beispiel Software GmbH"
    assert first.location_raw == "Berlin, Deutschland"
    assert first.description_text is not None and "vollständig remote" in first.description_text
    assert first.description_html is None
    assert first.posted_at == datetime(2026, 9, 29, 8, 12, 44, tzinfo=UTC)
    assert first.salary_raw == "48000 - 58000 EUR"
    assert first.employment_type_raw == "full_time"
    assert first.remote_hint is None, "Adzuna has no remote flag; the classifier decides"
    assert first.tags == ["IT-Stellen"]
    assert first.extra == {
        "country": "de",
        "area": ["Deutschland", "Berlin", "Berlin"],
        "category": "it-jobs",
    }

    sparse = jobs[1]
    assert sparse.company is None
    assert sparse.location_raw == "Hamburg, Deutschland", "falls back to the area hierarchy"
    assert sparse.salary_raw is None, "predicted salaries are dropped"
    assert sparse.employment_type_raw == "contract"

    uk = jobs[3]
    assert uk.source_id == "gb:5100000042"
    assert uk.salary_raw == "32000 GBP"


@respx.mock
def test_adzuna_drops_items_older_than_since_and_derives_max_days_old() -> None:
    route = respx.get(url__regex=ROUTE).mock(side_effect=_serve)
    with httpx.Client() as client:
        jobs = list(build("adzuna", client, PARAMS).fetch(since=SINCE))

    assert "Data Analyst Remote" not in [j.title for j in jobs]
    assert len(jobs) == 3
    sent = int(route.calls[0].request.url.params["max_days_old"])
    assert 1 <= sent <= 30


@respx.mock
def test_adzuna_respects_limit() -> None:
    route = respx.get(url__regex=ROUTE).mock(side_effect=_serve)
    with httpx.Client() as client:
        jobs = list(build("adzuna", client, PARAMS).fetch(since=None, limit=2))

    assert len(jobs) == 2
    assert route.call_count == 1
    assert route.calls[0].request.url.params["results_per_page"] == "2"


@respx.mock
def test_adzuna_skips_a_failing_country(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("jobbot.http.time.sleep", lambda _: None)
    respx.get(url__regex=ROUTE).mock(side_effect=_serve)
    params = {**PARAMS, "countries": ["xx", "gb"]}
    with httpx.Client() as client:
        jobs = list(build("adzuna", client, params).fetch(since=None))

    assert [j.source_id for j in jobs] == ["gb:5100000042"]


@respx.mock
def test_adzuna_fails_when_every_country_fails_without_leaking_the_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("jobbot.http.time.sleep", lambda _: None)
    respx.get(url__regex=ROUTE).mock(side_effect=_serve)
    params = {**PARAMS, "countries": ["xx", "yy"]}
    with httpx.Client() as client, pytest.raises(SourceError) as err:
        list(build("adzuna", client, params).fetch(since=None))
    assert "test-key" not in str(err.value)


def test_adzuna_requires_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ADZUNA_APP_KEY")
    with httpx.Client() as client, pytest.raises(SourceError):
        list(build("adzuna", client, PARAMS).fetch(since=None))


def test_max_days_old_rounds_up_and_clamps() -> None:
    now = datetime(2026, 10, 7, 6, 0, tzinfo=UTC)
    assert max_days_old(None, now) == 7
    assert max_days_old(datetime(2026, 9, 30, 6, 0, tzinfo=UTC), now) == 7
    assert max_days_old(datetime(2026, 9, 30, 5, 0, tzinfo=UTC), now) == 8
    assert max_days_old(now, now) == 1
    assert max_days_old(datetime(2026, 1, 1, tzinfo=UTC), now) == 30


def test_adzuna_caps_page_size_at_api_maximum() -> None:
    with httpx.Client() as client:
        src = build("adzuna", client, {"results_per_page": 500})
    assert getattr(src, "_page_size") == 50  # noqa: B009
