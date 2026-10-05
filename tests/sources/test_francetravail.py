import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
import respx

from jobbot.http import SourceError
from jobbot.sources import build
from jobbot.sources.francetravail import API_URL, SCOPE, TOKEN_URL, published_window

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "francetravail"
PARAMS = {"page_size": 3, "max_pages": 3, "page_delay": 0}


@pytest.fixture(autouse=True)
def _keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FRANCE_TRAVAIL_CLIENT_ID", "cid")
    monkeypatch.setenv("FRANCE_TRAVAIL_CLIENT_SECRET", "csecret")


def _sample() -> dict[str, object]:
    return json.loads((FIXTURES / "sample.json").read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def _search(request: httpx.Request) -> httpx.Response:
    if request.url.params["range"].startswith("0-"):
        return httpx.Response(206, json=_sample())
    return httpx.Response(204)


def _mock_token() -> respx.Route:
    return respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(200, json={"access_token": "tok", "expires_in": 1499})
    )


@respx.mock
def test_francetravail_authenticates_and_maps_fields() -> None:
    token = _mock_token()
    search = respx.get(API_URL).mock(side_effect=_search)
    with httpx.Client() as client:
        jobs = list(build("francetravail", client, PARAMS).fetch(since=None))

    form = token.calls[0].request.content.decode()
    assert "grant_type=client_credentials" in form and "client_secret=csecret" in form
    assert "scope=" + SCOPE.replace(" ", "+") in form
    assert token.calls[0].request.url.params["realm"] == "/partenaire"

    request = search.calls[0].request
    assert request.headers["Authorization"] == "Bearer tok"
    assert request.url.params["motsCles"] == "télétravail"
    assert request.url.params["grandDomaine"] == "M18"
    assert request.url.params["sort"] == "1"
    assert request.url.params["publieeDepuis"] == "7"
    assert [c.request.url.params["range"] for c in search.calls] == ["0-2", "3-5"]

    assert len(jobs) == 3
    first = jobs[0]
    assert first.source == "francetravail"
    assert first.source_id == "198ABCD"
    assert first.url == "https://candidat.francetravail.fr/offres/recherche/detail/198ABCD"
    assert first.title == "Développeur Python junior (H/F) - Télétravail"
    assert first.company == "Exemple Logiciel SAS"
    assert first.location_raw == "75 - Paris 11e"
    assert first.description_text is not None and "Télétravail total" in first.description_text
    assert first.posted_at == datetime(2026, 9, 29, 10, 15, tzinfo=UTC)
    assert first.salary_raw == "Annuel de 38000,00 Euros à 45000,00 Euros sur 12 mois"
    assert first.employment_type_raw == "full_time", "CDI falls back to working hours"
    assert first.tags == ["Études et développement informatique"]

    sparse = jobs[1]
    assert sparse.company is None
    assert sparse.url.endswith("/198ABCE"), "falls back to the candidate site"
    assert sparse.employment_type_raw == "contract"
    assert jobs[2].employment_type_raw == "freelance"


@respx.mock
def test_francetravail_no_content_yields_nothing() -> None:
    _mock_token()
    respx.get(API_URL).mock(return_value=httpx.Response(204))
    with httpx.Client() as client:
        assert list(build("francetravail", client, PARAMS).fetch(since=None)) == []


@respx.mock
def test_francetravail_drops_older_items_and_respects_limit() -> None:
    _mock_token()
    search = respx.get(API_URL).mock(side_effect=_search)
    since = datetime(2026, 9, 15, tzinfo=UTC)
    with httpx.Client() as client:
        recent = list(build("francetravail", client, PARAMS).fetch(since=since))
        one = list(build("francetravail", client, PARAMS).fetch(since=None, limit=1))
    assert [j.source_id for j in recent] == ["198ABCD", "198ABCE"]
    assert len(one) == 1
    assert search.calls[-1].request.url.params["range"] == "0-0"


@respx.mock
def test_francetravail_token_failure_is_a_source_error() -> None:
    respx.post(TOKEN_URL).mock(return_value=httpx.Response(401, json={"error": "invalid_client"}))
    with httpx.Client() as client, pytest.raises(SourceError) as err:
        list(build("francetravail", client, PARAMS).fetch(since=None))
    assert "csecret" not in str(err.value)


def test_francetravail_requires_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FRANCE_TRAVAIL_CLIENT_SECRET")
    with httpx.Client() as client, pytest.raises(SourceError):
        list(build("francetravail", client, PARAMS).fetch(since=None))


def test_published_window_picks_smallest_allowed_value() -> None:
    now = datetime(2026, 10, 7, 6, 0, tzinfo=UTC)
    assert published_window(None, now) == 7
    assert published_window(datetime(2026, 10, 6, 12, tzinfo=UTC), now) == 1
    assert published_window(datetime(2026, 9, 30, 6, tzinfo=UTC), now) == 7
    assert published_window(datetime(2026, 9, 29, 6, tzinfo=UTC), now) == 14
    assert published_window(datetime(2026, 1, 1, tzinfo=UTC), now) == 31


@respx.mock
def test_francetravail_runs_each_keyword_without_duplicates() -> None:
    _mock_token()
    search = respx.get(API_URL).mock(side_effect=_search)
    params = {**PARAMS, "keywords": ["private equity", "finance durable"], "domain": None}
    with httpx.Client() as client:
        jobs = list(build("francetravail", client, params).fetch(since=None))

    sent = [(c.request.url.params["motsCles"], c.request.url.params["range"]) for c in search.calls]
    assert sent == [
        ("private equity", "0-2"),
        ("private equity", "3-5"),
        ("finance durable", "0-2"),
        ("finance durable", "3-5"),
    ]
    assert "grandDomaine" not in search.calls[0].request.url.params
    assert len(jobs) == 3, "the second keyword returns the same offers"
