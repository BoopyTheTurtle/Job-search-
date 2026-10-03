from datetime import UTC, datetime, timedelta

from jobbot.config import Profile
from jobbot.filter import Section, evaluate, exclusion_reason, score
from jobbot.models import EmploymentType, Job, RemoteType, RoleFamily, Seniority

NOW = datetime(2026, 10, 1, 6, tzinfo=UTC)
PROFILE = Profile(
    home_country="LV", languages=["en", "fr", "lv", "es"], keyword_boosts=["python", "django"]
)


def _job(**kw: object) -> Job:
    base: dict[str, object] = {
        "id": "a",
        "title": "Junior Python Developer",
        "company": "Acme",
        "url": "https://acme.com/1",
        "source": "remotive",
        "source_ids": {"remotive": "1"},
        "first_seen": NOW,
        "last_seen": NOW,
        "remote_type": RemoteType.REMOTE,
        "regions_allowed": ["EUROPE"],
        "role_family": RoleFamily.SOFTWARE_DEV,
        "seniority": Seniority.JUNIOR,
        "employment_type": EmploymentType.FULL_TIME,
        "language": "en",
        "posted_at": NOW - timedelta(days=2),
        "salary_raw": "€45k",
        "description_text": "Build Django apps in Python.",
    }
    base.update(kw)
    return Job.model_validate(base)


def test_full_marks_strong() -> None:
    verdict = evaluate(_job(), PROFILE, NOW)
    assert verdict.section is Section.STRONG
    # role 30, title 10, en 15, remote 15, eligible 15, seniority 10, fresh 5, salary 5, kw 2
    # = 107, capped at 100
    assert verdict.job.score == 100
    assert "keywords python, django +2" in verdict.job.score_reasons


def test_exclusions() -> None:
    assert exclusion_reason(_job(role_family=RoleFamily.OTHER), PROFILE) == "role family other"
    assert exclusion_reason(_job(remote_type=RemoteType.ONSITE), PROFILE) == "remote type onsite"
    assert exclusion_reason(_job(remote_type=RemoteType.UNKNOWN), PROFILE) == "remote type unknown"
    assert (
        exclusion_reason(_job(remote_type=RemoteType.HYBRID), PROFILE)
        == "hybrid outside home country"
    )
    assert (
        exclusion_reason(_job(remote_type=RemoteType.HYBRID, regions_allowed=["LV"]), PROFILE)
        is None
    )
    assert exclusion_reason(_job(language="de"), PROFILE) == "language de"
    assert exclusion_reason(_job(language=None), PROFILE) is None
    assert exclusion_reason(_job(regions_allowed=["US"]), PROFILE) == "not eligible: US"
    assert exclusion_reason(_job(regions_allowed=["UNKNOWN"]), PROFILE) is None
    assert (
        exclusion_reason(_job(company="Evil Corp"), Profile(exclude_companies=["evil corp"]))
        == "company excluded"
    )
    assert exclusion_reason(
        _job(title="Sales Engineer"), Profile(exclude_title_patterns=[r"\bsales\b"])
    ).startswith("title matches")
    only_perm = Profile(employment_types=[EmploymentType.FULL_TIME])
    assert (
        exclusion_reason(_job(employment_type=EmploymentType.FREELANCE), only_perm)
        == "employment type freelance"
    )
    assert exclusion_reason(_job(employment_type=EmploymentType.UNKNOWN), only_perm) is None


def test_unknown_region_goes_to_possible() -> None:
    verdict = evaluate(_job(regions_allowed=["UNKNOWN"]), PROFILE, NOW)
    assert verdict.section is Section.POSSIBLE
    assert "eligibility unknown +0" in verdict.job.score_reasons


def test_inferred_region_scores_less() -> None:
    base = {"salary_raw": None, "posted_at": None}  # keep both below the 100 cap
    confirmed, _ = score(_job(**base), PROFILE, NOW)
    inferred, reasons = score(_job(tags=["timezone_inferred"], **base), PROFILE, NOW)
    assert confirmed == 97 and confirmed - inferred == 10
    assert "eligibility inferred +5" in reasons


def test_other_language_scores_less_than_english() -> None:
    base = {"salary_raw": None, "posted_at": None}  # keep both below the 100 cap
    en, _ = score(_job(**base), PROFILE, NOW)
    lv, _ = score(_job(language="lv", **base), PROFILE, NOW)
    assert en - lv == 5


def test_senior_goes_to_collapsed_section() -> None:
    verdict = evaluate(
        _job(title="Senior Python Developer", seniority=Seniority.SENIOR), PROFILE, NOW
    )
    assert verdict.section is Section.SENIOR
    assert "seniority senior -10" in verdict.job.score_reasons


def test_low_score_dropped() -> None:
    weak = _job(
        title="Engineer",
        language=None,
        regions_allowed=["UNKNOWN"],
        seniority=Seniority.UNKNOWN,
        posted_at=None,
        salary_raw=None,
        description_text="",
    )
    verdict = evaluate(weak, PROFILE, NOW)
    assert verdict.job.score == 45  # role 30 + remote 15
    assert verdict.section is Section.DROPPED
