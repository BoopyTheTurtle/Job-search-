import httpx
import pytest
import respx

from jobbot import http
from jobbot.http import SourceError, get_json, get_text

URL = "https://example.test/feed"


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(http.time, "sleep", lambda _s: None)


@respx.mock
def test_get_text_returns_body_and_retries_transient_errors() -> None:
    route = respx.get(URL).mock(
        side_effect=[httpx.Response(503), httpx.Response(200, text="<rss/>")]
    )
    with httpx.Client() as client:
        assert get_text(client, URL) == "<rss/>"
    assert route.call_count == 2


@respx.mock
def test_get_text_raises_source_error_after_exhausting_attempts() -> None:
    route = respx.get(URL).mock(return_value=httpx.Response(500))
    with httpx.Client() as client, pytest.raises(SourceError):
        get_text(client, URL, attempts=2)
    assert route.call_count == 2


@respx.mock
def test_get_json_still_parses_json() -> None:
    respx.get(URL).mock(return_value=httpx.Response(200, json={"ok": True}))
    with httpx.Client() as client:
        assert get_json(client, URL) == {"ok": True}
