import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
import respx

from jobbot.config import Profile, SourceConfig
from jobbot.digest.send import RESEND_URL
from jobbot.run import run_all
from jobbot.sources.remotive import API_URL
from jobbot.store import Store

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "remotive" / "sample.json"
NOW = datetime(2026, 10, 7, 6, 17, tzinfo=UTC)
CONFIGS = {"remotive": SourceConfig(terms="https://example.com")}


@respx.mock
def test_run_all_writes_digest_and_sends(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    respx.get(API_URL).mock(return_value=httpx.Response(200, json=json.loads(FIXTURE.read_text())))
    resend = respx.post(RESEND_URL).mock(return_value=httpx.Response(200, json={"id": "msg_42"}))
    monkeypatch.setenv("RESEND_API_KEY", "re_x")
    monkeypatch.setenv("DIGEST_FROM", "Bot <bot@example.com>")
    monkeypatch.setenv("DIGEST_TO", "me@example.com")
    profile = Profile(home_country="LV", languages=["en", "fr", "lv", "es"])

    with Store(tmp_path / "db.sqlite") as store:
        result = run_all(
            store, profile, ["remotive"], CONFIGS, out_dir=tmp_path / "out", since_days=60, now=NOW
        )
        assert result.status == "ok"
        assert result.new_jobs == 2
        assert result.strong == 1  # the junior Europe job
        assert result.dropped == 1  # the US-only senior job
        assert result.email == "sent:msg_42"
        assert resend.called
        scored = store.get_job(store.jobs_first_seen_in(result.run_id)[0].id)
        assert scored is not None and scored.score_reasons
        last = store.last_successful_run()
        assert last is not None and last.digest_path == result.digest_path

    digest_md = Path(result.digest_path)
    assert digest_md.name == "2026-10-07.md"
    assert "Junior Python Developer" in digest_md.read_text(encoding="utf-8")
    run_json = json.loads((tmp_path / "out" / "runs" / "2026-10-07.json").read_text())
    assert run_json["email"] == "sent:msg_42"
    assert run_json["digest_path"] == result.digest_path
    assert run_json["sources"][0]["source"] == "remotive"


@respx.mock
def test_run_all_without_email_config_skips(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    respx.get(API_URL).mock(return_value=httpx.Response(200, json=json.loads(FIXTURE.read_text())))
    for var in ("RESEND_API_KEY", "DIGEST_FROM", "DIGEST_TO"):
        monkeypatch.delenv(var, raising=False)
    with Store(tmp_path / "db.sqlite") as store:
        result = run_all(
            store,
            Profile(),
            ["remotive"],
            CONFIGS,
            out_dir=tmp_path / "out",
            since_days=60,
            now=NOW,
        )
    assert result.email.startswith("skipped:no RESEND")

    with Store(tmp_path / "db2.sqlite") as store:
        result = run_all(
            store,
            Profile(),
            ["remotive"],
            CONFIGS,
            out_dir=tmp_path / "out2",
            send=False,
            since_days=60,
            now=NOW,
        )
    assert result.email == "skipped:disabled"
