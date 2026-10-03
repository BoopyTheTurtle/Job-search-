import json
from datetime import datetime
from pathlib import Path

import httpx
import respx

from jobbot.sources import build
from jobbot.sources.remotive import API_URL

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "remotive" / "sample.json"


def _payload() -> dict[str, object]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))  # type: ignore[no-any-return]


@respx.mock
def test_remotive_maps_fields() -> None:
    route = respx.get(API_URL).mock(return_value=httpx.Response(200, json=_payload()))
    with httpx.Client() as client:
        src = build("remotive", client, {})
        jobs = list(src.fetch(since=None))

    assert route.call_count == 1, "Remotive allows only a few calls per day: one per run"
    assert [j.source_id for j in jobs] == ["1910001", "1910002"]
    first = jobs[0]
    assert first.source == "remotive"
    assert first.title == "Junior Python Developer"
    assert first.company == "Acme Robotics"
    assert first.location_raw == "Europe"
    assert first.salary_raw == "€45,000 - €55,000"
    assert first.employment_type_raw == "full_time"
    assert first.remote_hint is True
    assert first.posted_at == datetime(2026, 9, 29, 10, 15)
    assert "python" in first.tags
    assert jobs[1].salary_raw is None


@respx.mock
def test_remotive_respects_since_and_limit() -> None:
    respx.get(API_URL).mock(return_value=httpx.Response(200, json=_payload()))
    with httpx.Client() as client:
        src = build("remotive", client, {})
        recent = list(src.fetch(since=datetime(2026, 9, 15)))
        assert [j.source_id for j in recent] == ["1910001"]

        limited = list(src.fetch(since=None, limit=1))
        assert len(limited) == 1
