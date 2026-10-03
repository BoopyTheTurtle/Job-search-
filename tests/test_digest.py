from datetime import UTC, datetime, timedelta

import httpx
import pytest
import respx

from jobbot.config import Profile
from jobbot.digest import build_digest, render_html, render_markdown, render_text, send_digest
from jobbot.digest.send import RESEND_URL, EmailSettings, ResendError
from jobbot.models import EmploymentType, Job, RemoteType, RoleFamily, Seniority
from jobbot.store import SourceRunRecord

NOW = datetime(2026, 10, 7, 6, 17, tzinfo=UTC)
PROFILE = Profile(home_country="LV", languages=["en", "fr", "lv", "es"])


def _job(job_id: str, **kw: object) -> Job:
    base: dict[str, object] = {
        "id": job_id,
        "title": f"Python Developer {job_id}",
        "company": "Acme",
        "url": f"https://acme.com/{job_id}",
        "source": "remotive",
        "source_ids": {"remotive": job_id},
        "first_seen": NOW,
        "last_seen": NOW,
        "remote_type": RemoteType.REMOTE,
        "regions_allowed": ["EU"],
        "role_family": RoleFamily.SOFTWARE_DEV,
        "seniority": Seniority.JUNIOR,
        "employment_type": EmploymentType.FULL_TIME,
        "language": "en",
        "posted_at": NOW - timedelta(days=1),
        "description_text": "Build things.",
    }
    base.update(kw)
    return Job.model_validate(base)


def _digest() -> tuple[object, object]:
    jobs = [
        _job("strong"),
        _job("possible", regions_allowed=["UNKNOWN"], language="lv", salary_raw="€3000/mo"),
        _job("senior", title="Senior Dev", seniority=Seniority.SENIOR),
        _job("dropped", regions_allowed=["US"]),
        _job("dropped2", role_family=RoleFamily.OTHER),
    ]
    sources = [
        SourceRunRecord("remotive", fetched=5, new=5, duration_ms=300),
        SourceRunRecord("arbeitnow", errors=1, error_message="403 Forbidden"),
    ]
    return build_digest(
        jobs, PROFILE, run_id="run1", since=NOW - timedelta(days=8), sources=sources, now=NOW
    )


def test_build_sections_and_subject() -> None:
    digest, verdicts = _digest()
    assert [j.id for j in digest.strong] == ["strong"]
    assert [j.id for j in digest.possible] == ["possible"]
    assert [j.id for j in digest.senior] == ["senior"]
    assert digest.dropped == 2
    assert digest.drop_reasons == {"not eligible": 1, "role family other": 1}
    assert digest.subject == "Job digest: 2 new matches (2026-10-07)"
    assert len(verdicts) == 5
    assert all(v.job.score_reasons for v in verdicts)


def test_max_items_cap() -> None:
    jobs = [_job(f"j{i}") for i in range(10)]
    profile = PROFILE.model_copy(
        update={"digest": PROFILE.digest.model_copy(update={"max_items": 3})}
    )
    digest, _ = build_digest(jobs, profile, run_id="r", since=None, now=NOW)
    assert digest.total_shown == 3


def test_render_markdown() -> None:
    digest, _ = _digest()
    md = render_markdown(digest)
    assert md.startswith("# Job digest 2026-10-07")
    assert "## Strong matches (1)" in md
    assert "[Python Developer strong](https://acme.com/strong)" in md
    assert "EU · full time · junior · remotive · 1 day ago · score" in md
    assert "[lv]" in md
    assert "region not stated" in md
    assert "<summary>Senior-only roles (1)</summary>" in md
    assert "| arbeitnow | 0 | 0 | error: 403 Forbidden |" in md
    assert "Filtered out: not eligible (1), role family other (1)." in md


def test_render_markdown_separates_list_items() -> None:
    jobs = [_job(f"s{i}", title=f"Senior Dev {i}", seniority=Seniority.SENIOR) for i in range(3)]
    jobs += [_job(f"p{i}") for i in range(2)]
    digest, _ = build_digest(jobs, PROFILE, run_id="r", since=None, now=NOW)
    md = render_markdown(digest)
    lines = md.splitlines()
    item_lines = [ln for ln in lines if ln.startswith("- **[")]
    assert len(item_lines) == 5, md
    assert not any("score 9" in ln and "- **[" in ln[5:] for ln in lines), "items ran together"


def test_render_html_and_text() -> None:
    digest, _ = _digest()
    html = render_html(digest)
    assert "<title>Job digest: 2 new matches (2026-10-07)</title>" in html
    assert 'href="https://acme.com/strong"' in html
    assert "403 Forbidden" in html
    text = render_text(digest)
    assert "STRONG MATCHES (1)" in text
    assert "https://acme.com/possible" in text
    assert "arbeitnow: fetched 0, new 0, ERROR 403 Forbidden" in text


def test_attribution_only_when_the_source_is_shown() -> None:
    digest, _ = _digest()
    assert digest.attributions == []  # type: ignore[attr-defined]
    assert "Adzuna" not in render_markdown(digest)  # type: ignore[arg-type]

    shown, _ = build_digest(
        [_job("az", source="adzuna", source_ids={"adzuna": "de:1"})],
        PROFILE,
        run_id="r",
        since=None,
        now=NOW,
    )
    assert "[Jobs by Adzuna](https://www.adzuna.co.uk)" in render_markdown(shown)
    assert 'href="https://www.adzuna.co.uk"' in render_html(shown)
    assert "Jobs by Adzuna: https://www.adzuna.co.uk" in render_text(shown)


def test_html_escapes_untrusted_fields() -> None:
    digest, _ = build_digest(
        [_job("x", title="<script>alert(1)</script>", company="A&B")],
        PROFILE,
        run_id="r",
        since=None,
        now=NOW,
    )
    html = render_html(digest)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html and "A&amp;B" in html


def test_email_settings_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in ("RESEND_API_KEY", "DIGEST_FROM", "DIGEST_TO"):
        monkeypatch.delenv(var, raising=False)
    assert EmailSettings.from_env(["x@y.z"]) is None
    monkeypatch.setenv("RESEND_API_KEY", "re_123")
    monkeypatch.setenv("DIGEST_FROM", "Bot <bot@example.com>")
    settings = EmailSettings.from_env(["fallback@example.com"])
    assert settings is not None and settings.recipients == ["fallback@example.com"]
    monkeypatch.setenv("DIGEST_TO", "a@example.com, b@example.com")
    settings = EmailSettings.from_env([])
    assert settings is not None and settings.recipients == ["a@example.com", "b@example.com"]


@respx.mock
def test_send_digest_posts_to_resend() -> None:
    route = respx.post(RESEND_URL).mock(return_value=httpx.Response(200, json={"id": "msg_1"}))
    settings = EmailSettings("re_123", "Bot <bot@example.com>", ["me@example.com"])
    with httpx.Client() as client:
        message_id = send_digest(settings, subject="S", html="<p>h</p>", text="t", client=client)
    assert message_id == "msg_1"
    request = route.calls.last.request
    assert request.headers["Authorization"] == "Bearer re_123"
    body = request.read().decode()
    assert '"to": ["me@example.com"]' in body or '"to":["me@example.com"]' in body


@respx.mock
def test_send_digest_raises_on_error() -> None:
    respx.post(RESEND_URL).mock(return_value=httpx.Response(422, json={"message": "bad from"}))
    settings = EmailSettings("re_123", "nope", ["me@example.com"])
    with httpx.Client() as client, pytest.raises(ResendError, match="422"):
        send_digest(settings, subject="S", html="h", text="t", client=client)
