import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
import respx

from jobbot.http import SourceError
from jobbot.pipeline import process
from jobbot.sources import build
from jobbot.sources._watchlist import slugs

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "greenhouse" / "eqtpartners.json"
URL = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"


def _payload() -> dict[str, object]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))  # type: ignore[no-any-return]


@respx.mock
def test_greenhouse_maps_fields() -> None:
    route = respx.get(URL.format(slug="eqtpartners")).mock(
        return_value=httpx.Response(200, json=_payload())
    )
    with httpx.Client() as client:
        jobs = list(build("greenhouse", client, {"companies": ["eqtpartners"]}).fetch(None))

    assert route.calls[0].request.url.params["content"] == "true"
    assert len(jobs) == 3
    first = jobs[0]
    assert first.source == "greenhouse"
    assert first.source_id == "eqtpartners:4936187101"
    assert first.url == "https://job-boards.eu.greenhouse.io/eqtpartners/jobs/4936187101"
    assert first.title == "AI Architect"
    assert first.company == "EQT Group"
    assert first.location_raw == "Stockholm, Stockholm, Sweden"
    assert first.posted_at == datetime(2026, 9, 28, 15, 15, 23, tzinfo=UTC)
    assert first.description_html and first.description_html.startswith("<div")
    assert first.remote_hint is None
    assert first.tags and "Real Estate" in first.tags[0]
    # The escaped HTML reaches the pipeline as readable text.
    assert "&lt;" not in process(first).description_text


@respx.mock
def test_greenhouse_drops_jobs_older_than_since() -> None:
    respx.get(URL.format(slug="eqtpartners")).mock(
        return_value=httpx.Response(200, json=_payload())
    )
    since = datetime(2026, 8, 1, tzinfo=UTC)
    with httpx.Client() as client:
        jobs = list(build("greenhouse", client, {"companies": ["eqtpartners"]}).fetch(since))
    assert [j.title for j in jobs] == ["AI Architect", "Applied AI Lead"]


@respx.mock
def test_greenhouse_skips_a_missing_board_and_fails_when_all_fail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("time.sleep", lambda _: None)
    respx.get(URL.format(slug="eqtpartners")).mock(
        return_value=httpx.Response(200, json=_payload())
    )
    respx.get(URL.format(slug="gone")).mock(return_value=httpx.Response(404))
    with httpx.Client() as client:
        jobs = list(build("greenhouse", client, {"companies": ["gone", "eqtpartners"]}).fetch(None))
        assert len(jobs) == 3
        with pytest.raises(SourceError, match="every greenhouse board failed"):
            list(build("greenhouse", client, {"companies": ["gone"]}).fetch(None))


def test_watchlist_slugs_default_to_companies_yaml(monkeypatch: pytest.MonkeyPatch) -> None:
    from jobbot.config import Company

    companies = [
        Company(name="A", ats="greenhouse", slug="a"),
        Company(name="B", ats="greenhouse", slug="b", enabled=False),
        Company(name="C", ats="recruitee", slug="c"),
    ]
    monkeypatch.setattr("jobbot.sources._watchlist.load_companies", lambda: companies)
    assert slugs({}, "greenhouse") == ["a"]
    assert slugs({"companies": ["x"]}, "greenhouse") == ["x"]
    assert slugs({"companies": []}, "greenhouse") == []
