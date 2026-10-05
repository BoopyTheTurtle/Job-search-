import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
import respx

from jobbot.config import Search, SourceConfig
from jobbot.digest.send import RESEND_URL
from jobbot.models import RoleFamily
from jobbot.run import run_all
from jobbot.sources.remotive import API_URL
from jobbot.store import Store

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "remotive" / "sample.json"
NOW = datetime(2026, 10, 7, 6, 17, tzinfo=UTC)
CONFIGS = {"remotive": SourceConfig(terms="https://example.com")}
IT = Search(name="it", title="IT", home_country="LV", languages=["en", "fr", "lv", "es"])
IMPACT = Search(
    name="impact",
    title="Impact",
    home_country="LV",
    role_families=[RoleFamily.FINANCE_INVESTMENT, RoleFamily.INTL_DEVELOPMENT],
)


@respx.mock
def test_run_all_writes_one_digest_per_search_and_sends(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    respx.get(API_URL).mock(return_value=httpx.Response(200, json=json.loads(FIXTURE.read_text())))
    resend = respx.post(RESEND_URL).mock(return_value=httpx.Response(200, json={"id": "msg_42"}))
    monkeypatch.setenv("RESEND_API_KEY", "re_x")
    monkeypatch.setenv("DIGEST_FROM", "Bot <bot@example.com>")
    monkeypatch.setenv("DIGEST_TO", "me@example.com")

    with Store(tmp_path / "db.sqlite") as store:
        result = run_all(
            store,
            [IT, IMPACT],
            ["remotive"],
            CONFIGS,
            out_dir=tmp_path / "out",
            since_days=60,
            now=NOW,
        )
        assert result.status == "ok"
        assert result.new_jobs == 2
        it, impact = result.digests
        assert (it.search, it.strong, it.dropped) == ("it", 1, 1)  # junior Europe job kept
        assert it.email == "sent:msg_42"
        assert (impact.search, impact.shown, impact.dropped) == ("impact", 0, 2)
        assert impact.email == "skipped:nothing to show"
        assert resend.call_count == 1
        assert "IT job digest" in json.loads(resend.calls[0].request.content)["subject"]
        scored = store.get_job(store.jobs_first_seen_in(result.run_id)[0].id)
        assert scored is not None and scored.score_reasons[0] in {"[it]", "[impact]"}
        last = store.last_successful_run()
        assert last is not None and last.digest_path == f"{it.digest_path};{impact.digest_path}"

    it_md = Path(it.digest_path)
    assert it_md == tmp_path / "out" / "digests" / "it" / "2026-10-07.md"
    assert "Junior Python Developer" in it_md.read_text(encoding="utf-8")
    assert (
        Path(impact.digest_path)
        .read_text(encoding="utf-8")
        .startswith("# Impact job digest 2026-10-07")
    )
    run_json = json.loads((tmp_path / "out" / "runs" / "2026-10-07.json").read_text())
    assert [d["search"] for d in run_json["digests"]] == ["it", "impact"]
    assert run_json["digests"][0]["email"] == "sent:msg_42"
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
            store, [IT], ["remotive"], CONFIGS, out_dir=tmp_path / "out", since_days=60, now=NOW
        )
    assert result.digests[0].email.startswith("skipped:no RESEND")
    assert not result.email_failed

    with Store(tmp_path / "db2.sqlite") as store:
        result = run_all(
            store,
            [IT],
            ["remotive"],
            CONFIGS,
            out_dir=tmp_path / "out2",
            send=False,
            since_days=60,
            now=NOW,
        )
    assert result.digests[0].email == "skipped:disabled"


@respx.mock
def test_failed_email_marks_the_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    respx.get(API_URL).mock(return_value=httpx.Response(200, json=json.loads(FIXTURE.read_text())))
    respx.post(RESEND_URL).mock(return_value=httpx.Response(500, text="boom"))
    monkeypatch.setenv("RESEND_API_KEY", "re_x")
    monkeypatch.setenv("DIGEST_FROM", "Bot <bot@example.com>")
    monkeypatch.setenv("DIGEST_TO", "me@example.com")
    with Store(tmp_path / "db.sqlite") as store:
        result = run_all(
            store, [IT], ["remotive"], CONFIGS, out_dir=tmp_path / "out", since_days=60, now=NOW
        )
    assert result.email_failed
