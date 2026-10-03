from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
import respx

from jobbot.http import SourceError
from jobbot.sources import build
from jobbot.sources.weworkremotely import DEFAULT_FEEDS

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "weworkremotely"
PROGRAMMING = "https://weworkremotely.com/categories/remote-programming-jobs.rss"
DEVOPS = "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss"
PARAMS = {"feeds": [PROGRAMMING, DEVOPS]}
SINCE = datetime(2026, 9, 15, tzinfo=UTC)


def _rss(name: str) -> httpx.Response:
    body = (FIXTURES / name).read_text(encoding="utf-8")
    return httpx.Response(200, text=body, headers={"content-type": "application/rss+xml"})


@respx.mock
def test_weworkremotely_maps_fields_and_dedupes_across_feeds() -> None:
    programming = respx.get(PROGRAMMING).mock(return_value=_rss("sample.rss"))
    devops = respx.get(DEVOPS).mock(return_value=_rss("devops.rss"))
    with httpx.Client() as client:
        jobs = list(build("weworkremotely", client, PARAMS).fetch(since=None))

    assert programming.call_count == 1 and devops.call_count == 1
    assert [j.source_id for j in jobs] == [
        "https://weworkremotely.com/remote-jobs/acme-robotics-junior-python-developer",
        "https://weworkremotely.com/remote-jobs/backend-engineer-no-company-prefix",
        "https://weworkremotely.com/remote-jobs/initech-senior-frontend-engineer",
        "https://weworkremotely.com/remote-jobs/globex-cloud-site-reliability-engineer",
    ], "the cross-posted guid appears once"

    first = jobs[0]
    assert first.source == "weworkremotely"
    assert first.company == "Acme Robotics"
    assert first.title == "Junior Python Developer"
    assert first.url == first.source_id
    assert first.location_raw == "Europe Only"
    assert first.employment_type_raw == "Full-Time"
    assert (
        first.description_html is not None
        and "<strong>fully remote</strong>" in first.description_html
    )
    assert first.remote_hint is True
    assert first.posted_at == datetime(2026, 9, 29, 10, 15, tzinfo=UTC)
    assert first.posted_at.tzinfo is not None
    assert first.tags == ["Programming", "Full-Time"]
    assert first.extra["feed"] == PROGRAMMING

    sparse = jobs[1]
    assert sparse.company is None, "title without 'Company: ' prefix stays whole"
    assert sparse.title == "Backend Engineer (no company prefix)"
    assert sparse.location_raw is None
    assert sparse.employment_type_raw is None
    assert sparse.tags == []

    namespaced = jobs[3]
    assert namespaced.company == "Globex Cloud"
    assert namespaced.location_raw == "Anywhere in the World", "namespaced <wwr:region> is read"
    assert namespaced.posted_at == datetime(2026, 9, 30, 9, 30, tzinfo=UTC), "-0000 is UTC"


@respx.mock
def test_weworkremotely_respects_since_and_limit() -> None:
    respx.get(PROGRAMMING).mock(return_value=_rss("sample.rss"))
    respx.get(DEVOPS).mock(return_value=_rss("devops.rss"))
    with httpx.Client() as client:
        src = build("weworkremotely", client, PARAMS)
        recent = list(src.fetch(since=SINCE))
        assert [j.title for j in recent] == [
            "Junior Python Developer",
            "Backend Engineer (no company prefix)",
            "Site Reliability Engineer",
        ]

        limited = list(src.fetch(since=None, limit=1))
        assert len(limited) == 1


@respx.mock
def test_weworkremotely_skips_a_broken_feed_but_fails_when_all_fail() -> None:
    respx.get(PROGRAMMING).mock(return_value=httpx.Response(200, text="<rss><channel>"))
    respx.get(DEVOPS).mock(return_value=_rss("devops.rss"))
    with httpx.Client() as client:
        jobs = list(build("weworkremotely", client, PARAMS).fetch(since=None))
    assert len(jobs) == 2

    respx.get(DEVOPS).mock(return_value=httpx.Response(200, text="<rss><channel>"))
    with httpx.Client() as client, pytest.raises(SourceError):
        list(build("weworkremotely", client, PARAMS).fetch(since=None))


def test_weworkremotely_defaults_to_programming_feeds() -> None:
    with httpx.Client() as client:
        src = build("weworkremotely", client, {})
    assert getattr(src, "_feeds") == DEFAULT_FEEDS  # noqa: B009
    assert PROGRAMMING in DEFAULT_FEEDS and DEVOPS in DEFAULT_FEEDS
