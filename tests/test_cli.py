import httpx
import pytest
import respx
from typer.testing import CliRunner

from jobbot.cli import app
from jobbot.sources import available

runner = CliRunner()


def test_sources_lists_every_registered_connector() -> None:
    result = runner.invoke(app, ["sources"])
    assert result.exit_code == 0
    for name in available():
        assert name in result.output


@respx.mock
def test_crawl_all_hits_every_registered_source_even_if_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ADZUNA_APP_ID", "id")
    monkeypatch.setenv("ADZUNA_APP_KEY", "key")
    respx.route().mock(return_value=httpx.Response(200, json={"jobs": [], "data": []}))
    result = runner.invoke(app, ["crawl", "--dry-run", "--all", "--limit", "1"])
    assert result.exit_code == 0, result.output
    for name in available():
        assert f"{name}: " in result.output
    assert respx.calls.call_count >= len(available())


@respx.mock
def test_crawl_dry_run_skips_keyed_sources_without_secrets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ADZUNA_APP_ID", raising=False)
    monkeypatch.delenv("ADZUNA_APP_KEY", raising=False)
    result = runner.invoke(app, ["crawl", "--dry-run", "--source", "adzuna"])
    assert result.exit_code == 0, result.output
    assert "adzuna: skipped: missing ADZUNA_APP_ID, ADZUNA_APP_KEY" in result.output
    assert respx.calls.call_count == 0
