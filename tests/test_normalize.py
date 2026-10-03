from datetime import UTC, datetime, timedelta, timezone

from jobbot.models import RawJob
from jobbot.normalize import html_to_text, normalize, parse_datetime


def test_html_to_text_keeps_bullets_and_breaks() -> None:
    html = (
        "<h2>About</h2><p>We build <strong>things</strong>.&nbsp;Fast.</p>"
        "<ul><li>Python</li><li>Postgres &amp; Redis</li></ul>"
        "<script>alert(1)</script><p>Apply   now<br>today</p>"
    )
    assert html_to_text(html) == (
        "About\nWe build things. Fast.\n- Python\n- Postgres & Redis\nApply now\ntoday"
    )


def test_html_to_text_handles_plain_and_empty() -> None:
    assert html_to_text(None) == ""
    assert html_to_text("  just   text  ") == "just text"


def test_parse_datetime_variants() -> None:
    expected = datetime(2026, 9, 29, 10, 15, tzinfo=UTC)
    assert parse_datetime("2026-09-29T10:15:00") == expected
    assert parse_datetime("2026-09-29T10:15:00Z") == expected
    assert parse_datetime("2026-09-29 10:15:00") == expected
    assert parse_datetime("2026-09-29T12:15:00+02:00") == expected
    assert parse_datetime("Tue, 29 Sep 2026 10:15:00 +0000") == expected
    assert parse_datetime(int(expected.timestamp())) == expected
    assert parse_datetime(int(expected.timestamp()) * 1000) == expected
    assert parse_datetime(str(int(expected.timestamp()))) == expected
    assert parse_datetime(datetime(2026, 9, 29, 10, 15)) == expected
    assert (
        parse_datetime(datetime(2026, 9, 29, 12, 15, tzinfo=timezone(timedelta(hours=2))))
        == expected
    )


def test_parse_datetime_rejects_garbage() -> None:
    assert parse_datetime(None) is None
    assert parse_datetime("") is None
    assert parse_datetime("yesterday") is None
    assert parse_datetime(True) is None
    assert parse_datetime(["x"]) is None


def test_normalize_maps_fields() -> None:
    raw = RawJob(
        source="remotive",
        source_id="1",
        url="https://Example.com/jobs/1/?utm_source=x",
        title="  Junior   Python Developer ",
        company=" Acme  Robotics ",
        location_raw=" Europe ",
        description_html="<p>Hello <b>world</b></p>",
        posted_at=datetime(2026, 9, 29, 10, 15),
        salary_raw="",
        tags=["python", " python ", "", "django"],
    )
    now = datetime(2026, 10, 1, tzinfo=UTC)
    job = normalize(raw, now)
    assert job.title == "Junior Python Developer"
    assert job.company == "Acme Robotics"
    assert job.url == "https://example.com/jobs/1"
    assert job.description_text == "Hello world"
    assert job.location_raw == "Europe"
    assert job.salary_raw is None
    assert job.tags == ["django", "python"]
    assert job.source_ids == {"remotive": "1"}
    assert job.posted_at == datetime(2026, 9, 29, 10, 15, tzinfo=UTC)
    assert job.first_seen == job.last_seen == now
    assert len(job.id) == 40
