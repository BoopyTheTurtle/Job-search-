import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest
import respx

from jobbot.http import SourceError
from jobbot.sources import build
from jobbot.sources.workday import age_days, is_recent, parse_slug

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "workday"
SLUG = "ardian.wd103/ArdianCareers"
API = "https://ardian.wd103.myworkdayjobs.com/wday/cxs/ardian/ArdianCareers"
PARAMS = {"companies": [SLUG], "page_delay": 0}


def _json(name: str) -> object:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _mock() -> tuple[respx.Route, respx.Route]:
    listing = respx.post(f"{API}/jobs").mock(
        return_value=httpx.Response(200, json=_json("ardian_list.json"))
    )
    paths = {p["externalPath"]: i for i, p in enumerate(_json("ardian_list.json")["jobPostings"])}  # type: ignore[index]

    def detail(request: httpx.Request) -> httpx.Response:
        index = paths[request.url.path.removeprefix("/wday/cxs/ardian/ArdianCareers")]
        return httpx.Response(200, json=_json(f"ardian_detail_{index}.json"))

    details = respx.get(url__startswith=f"{API}/job/").mock(side_effect=detail)
    return listing, details


@respx.mock
def test_workday_maps_list_and_detail() -> None:
    listing, details = _mock()
    since = datetime.now(tz=UTC) - timedelta(days=7)
    with httpx.Client() as client:
        jobs = list(build("workday", client, PARAMS).fetch(since))

    body = json.loads(listing.calls[0].request.content)
    assert body == {"appliedFacets": {}, "limit": 20, "offset": 0}
    # The third posting is 14 days old: no detail call, not yielded.
    assert details.call_count == 2
    assert len(jobs) == 2
    first = jobs[0]
    assert first.source == "workday"
    assert first.source_id == f"{SLUG}:JR1002259"
    assert first.url.startswith("https://ardian.wd103.myworkdayjobs.com/ArdianCareers/job/Paris/")
    assert first.title == "Group Finance Treasury Stage - Mars 2027 I Paris (H/F)"
    assert first.company == "ARDIAN France"
    assert first.location_raw == "Paris, France"
    assert first.posted_at == datetime(2026, 10, 2, tzinfo=UTC)
    assert first.employment_type_raw == "Full time"
    assert first.description_html


@respx.mock
def test_workday_without_since_fetches_every_detail_and_respects_limit() -> None:
    _listing, details = _mock()
    with httpx.Client() as client:
        assert len(list(build("workday", client, PARAMS).fetch(None, limit=1))) == 1
        assert details.call_count == 1


@respx.mock
def test_workday_list_failure_is_a_source_error() -> None:
    respx.post(f"{API}/jobs").mock(return_value=httpx.Response(500))
    with httpx.Client() as client, pytest.raises(SourceError, match="every workday board"):
        list(build("workday", client, PARAMS).fetch(None))


def test_workday_uses_watchlist_name(monkeypatch: pytest.MonkeyPatch) -> None:
    from jobbot.config import Company

    monkeypatch.setattr(
        "jobbot.sources._watchlist.load_companies",
        lambda: [Company(name="Ardian", ats="workday", slug=SLUG)],
    )
    with respx.mock:
        _mock()
        with httpx.Client() as client:
            jobs = list(build("workday", client, {"page_delay": 0}).fetch(None, limit=1))
    assert jobs[0].company == "Ardian"


def test_workday_helpers() -> None:
    assert parse_slug(SLUG) == ("https://ardian.wd103.myworkdayjobs.com", API)
    with pytest.raises(ValueError):
        parse_slug("ardian")
    assert age_days("Posted Today") == 0
    assert age_days("Posted Yesterday") == 1
    assert age_days("Posted 3 Days Ago") == 3
    assert age_days("Posted 30+ Days Ago") == 30
    assert age_days(None) is None
    now = datetime(2026, 10, 5, tzinfo=UTC)
    since = now - timedelta(days=7)
    assert is_recent("Posted 7 Days Ago", since, now)
    assert is_recent("Posted 8 Days Ago", since, now)  # a day of slack
    assert not is_recent("Posted 9 Days Ago", since, now)
    assert is_recent("Posted 30+ Days Ago", None, now)
    assert is_recent("Reposted", since, now)
