import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import respx

from jobbot.models import RemoteType
from jobbot.pipeline import process
from jobbot.sources import build
from jobbot.sources._watchlist import arrangement
from jobbot.sources.recruitee import employment, published

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "recruitee" / "meridiam.json"
URL = "https://meridiam.recruitee.com/api/offers/"


def _fetch(since: datetime | None = None) -> list:  # type: ignore[type-arg]
    respx.get(URL).mock(
        return_value=httpx.Response(200, json=json.loads(FIXTURE.read_text(encoding="utf-8")))
    )
    with httpx.Client() as client:
        return list(build("recruitee", client, {"companies": ["meridiam"]}).fetch(since))


@respx.mock
def test_recruitee_maps_fields() -> None:
    jobs = _fetch()
    assert len(jobs) == 3
    first = jobs[0]
    assert first.source == "recruitee"
    assert first.source_id == "meridiam:2769762"
    assert first.url == "https://careers.meridiam.com/o/accounting-associate-france-2027"
    assert first.title == "Accounting Associate - France - 2027"
    assert first.company == "Meridiam"
    assert first.location_raw == "Paris, Île-de-France, France (hybrid)"
    assert first.posted_at == datetime(2026, 10, 2, 15, 52, 39, tzinfo=UTC)
    assert first.salary_raw == "43000 EUR"
    assert first.employment_type_raw == "full_time"
    assert first.remote_hint is False
    assert "Finance" in first.tags
    assert process(first).remote_type is RemoteType.HYBRID
    # Flagged neither remote nor hybrid: on-site.
    assert jobs[1].remote_hint is False
    assert process(jobs[1]).remote_type is RemoteType.ONSITE


@respx.mock
def test_recruitee_drops_offers_older_than_since() -> None:
    jobs = _fetch(datetime(2026, 9, 20, tzinfo=UTC))
    assert [j.title for j in jobs] == [
        "Accounting Associate - France - 2027",
        "Corporate Compliance Associate",
    ]


def test_recruitee_helpers() -> None:
    assert published("2026-10-02 15:52:39 UTC") == datetime(2026, 10, 2, 15, 52, 39, tzinfo=UTC)
    assert published(None) is None
    assert employment("parttime_fixed_term") == "part_time"
    assert employment("internship") == "internship"
    assert employment(None) is None
    assert arrangement(True, False, "Paris") == (True, "Paris")
    assert arrangement(False, True, None) == (False, "hybrid")
    assert arrangement(None, None, "Paris") == (None, "Paris")
