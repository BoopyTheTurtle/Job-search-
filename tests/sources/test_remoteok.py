import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import respx

from jobbot.sources import build
from jobbot.sources.remoteok import API_URL

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "remoteok" / "sample.json"
SINCE = datetime(2026, 9, 15, tzinfo=UTC)


def _payload() -> list[object]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))  # type: ignore[no-any-return]


@respx.mock
def test_remoteok_maps_fields_and_skips_legal_notice() -> None:
    route = respx.get(API_URL).mock(return_value=httpx.Response(200, json=_payload()))
    with httpx.Client() as client:
        jobs = list(build("remoteok", client, {}).fetch(since=None))

    assert route.call_count == 1
    assert [j.source_id for j in jobs] == ["2001", "2002", "1999"], "legal notice is not a job"
    first = jobs[0]
    assert first.source == "remoteok"
    assert first.title == "Junior Python Developer"
    assert first.company == "Acme Robotics"
    assert first.location_raw == "Europe"
    assert (
        first.url
        == "https://remoteok.com/remote-jobs/remote-junior-python-developer-acme-robotics-2001"
    )
    assert (
        first.description_html is not None and "<strong>Europe</strong>" in first.description_html
    )
    assert first.salary_raw == "40000 - 60000 USD"
    assert first.remote_hint is True
    assert first.posted_at == datetime(2026, 9, 29, 10, 15, tzinfo=UTC)
    assert first.posted_at.tzinfo is not None
    assert first.tags == ["python", "django", "junior"]
    assert first.extra["slug"] == "remote-junior-python-developer-acme-robotics-2001"

    sparse = jobs[1]
    assert sparse.location_raw is None
    assert sparse.salary_raw is None, "zero salary bounds mean unknown"


@respx.mock
def test_remoteok_respects_since_and_limit() -> None:
    respx.get(API_URL).mock(return_value=httpx.Response(200, json=_payload()))
    with httpx.Client() as client:
        src = build("remoteok", client, {})
        recent = list(src.fetch(since=SINCE))
        assert [j.source_id for j in recent] == ["2001", "2002"]

        limited = list(src.fetch(since=None, limit=1))
        assert [j.source_id for j in limited] == ["2001"]
