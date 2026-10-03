from datetime import UTC, datetime

from jobbot.dedupe import dedupe, norm_company, norm_text
from jobbot.models import Job

NOW = datetime(2026, 10, 1, tzinfo=UTC)


def _job(
    source: str, source_id: str, url: str, title: str, company: str | None, **kw: object
) -> Job:
    base: dict[str, object] = {
        "id": kw.pop("id", f"{source}-{source_id}"),
        "title": title,
        "company": company,
        "url": url,
        "source": source,
        "source_ids": {source: source_id},
        "first_seen": NOW,
        "last_seen": NOW,
    }
    base.update(kw)
    return Job.model_validate(base)


def test_norm_helpers() -> None:
    assert norm_text("Senior Backend Engineer (m/f/d) - Remote") == "senior backend engineer"
    assert norm_company("Acme GmbH") == norm_company("ACME") == "acme"
    assert norm_company("Example SIA") == "example"


def test_same_id_merges_sources() -> None:
    a = _job("remotive", "1", "https://acme.com/j/1", "Dev", "Acme", id="x")
    b = _job("arbeitnow", "9", "https://acme.com/j/1", "Dev", "Acme", id="x", tags=["python"])
    out = dedupe([a, b])
    assert len(out) == 1
    assert out[0].source == "remotive"
    assert out[0].source_ids == {"remotive": "1", "arbeitnow": "9"}
    assert out[0].tags == ["python"]


def test_fuzzy_title_same_company_merges() -> None:
    a = _job(
        "remotive", "1", "https://remotive.com/1", "Senior Backend Engineer (m/f/d)", "Acme GmbH"
    )
    b = _job(
        "himalayas", "2", "https://himalayas.app/2", "Senior Backend Engineer - Remote", "Acme"
    )
    out = dedupe([a, b])
    assert len(out) == 1
    assert set(out[0].source_ids) == {"remotive", "himalayas"}


def test_different_titles_same_company_kept() -> None:
    a = _job("remotive", "1", "https://remotive.com/1", "Backend Engineer", "Acme")
    b = _job("remotive", "2", "https://remotive.com/2", "Frontend Engineer", "Acme")
    assert len(dedupe([a, b])) == 2


def test_same_title_different_company_kept() -> None:
    a = _job("remotive", "1", "https://remotive.com/1", "Backend Engineer", "Acme")
    b = _job("remotive", "2", "https://remotive.com/2", "Backend Engineer", "Globex")
    assert len(dedupe([a, b])) == 2


def test_no_company_never_fuzzy_merges() -> None:
    a = _job("remotive", "1", "https://remotive.com/1", "Backend Engineer", None)
    b = _job("remotive", "2", "https://remotive.com/2", "Backend Engineer", None)
    assert len(dedupe([a, b])) == 2


def test_merge_keeps_earliest_dates() -> None:
    early = datetime(2026, 9, 1, tzinfo=UTC)
    a = _job("remotive", "1", "https://remotive.com/1", "Dev", "Acme", posted_at=NOW)
    b = _job("x", "2", "https://x.com/2", "Dev", "Acme", posted_at=early, first_seen=early)
    out = dedupe([a, b])[0]
    assert out.posted_at == early
    assert out.first_seen == early
