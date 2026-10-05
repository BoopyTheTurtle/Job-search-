import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import respx

from jobbot.models import RemoteType
from jobbot.pipeline import process
from jobbot.sources import build

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "smartrecruiters"
LIST = "https://api.smartrecruiters.com/v1/companies/OECD/postings"


def _json(name: str) -> object:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _mock() -> tuple[respx.Route, respx.Route]:
    listing = respx.get(LIST).mock(return_value=httpx.Response(200, json=_json("oecd_list.json")))

    def detail(request: httpx.Request, posting: str) -> httpx.Response:
        return httpx.Response(200, json=_json(f"oecd_{posting}.json"))

    details = respx.get(url__regex=LIST + r"/(?P<posting>\d+)").mock(side_effect=detail)
    return listing, details


@respx.mock
def test_smartrecruiters_maps_list_and_detail() -> None:
    listing, details = _mock()
    with httpx.Client() as client:
        jobs = list(build("smartrecruiters", client, {"companies": ["OECD"]}).fetch(None))

    assert listing.calls[0].request.url.params["limit"] == "100"
    assert details.call_count == 3
    assert len(jobs) == 3
    first = jobs[0]
    assert first.source == "smartrecruiters"
    assert first.source_id == "OECD:744000153200039"
    assert first.url.startswith("https://jobs.smartrecruiters.com/OECD/744000153200039")
    assert first.title == "Head of PARIS21 Secretariat"
    assert first.company == "OECD"
    assert first.location_raw and first.location_raw.startswith("Paris")
    assert first.posted_at == datetime(2026, 10, 2, 14, 19, 16, 19000, tzinfo=UTC)
    assert first.employment_type_raw == "full_time"
    assert first.remote_hint is False
    assert first.description_html
    assert "International Affairs" in first.tags
    assert process(first).remote_type is RemoteType.ONSITE


@respx.mock
def test_smartrecruiters_fetches_details_only_for_new_postings() -> None:
    _listing, details = _mock()
    since = datetime(2026, 10, 1, tzinfo=UTC)
    with httpx.Client() as client:
        jobs = list(build("smartrecruiters", client, {"companies": ["OECD"]}).fetch(since))
    assert len(jobs) == 2
    assert details.call_count == 2


@respx.mock
def test_smartrecruiters_respects_limit() -> None:
    _listing, details = _mock()
    with httpx.Client() as client:
        jobs = list(build("smartrecruiters", client, {"companies": ["OECD"]}).fetch(None, 1))
    assert len(jobs) == 1
    assert details.call_count == 1
