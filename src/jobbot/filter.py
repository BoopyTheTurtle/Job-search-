"""Profile filtering and 0-100 scoring. SPEC §8.7. This is the only place (besides digest)
that knows about the user's preferences."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum

from jobbot.config import Profile
from jobbot.dedupe import norm_company
from jobbot.enrich.regions import expand, is_eligible
from jobbot.enrich.roles import load_taxonomy
from jobbot.models import Job, RemoteType, RoleFamily, Seniority

STRONG_SCORE = 70
INFERRED_TAGS = {"timezone_inferred", "region_from_description"}
SENIOR_LEVELS = {Seniority.SENIOR, Seniority.LEAD}


class Section(StrEnum):
    STRONG = "strong"
    POSSIBLE = "possible"
    SENIOR = "senior"
    DROPPED = "dropped"


@dataclass
class Verdict:
    job: Job
    section: Section
    excluded_reason: str | None = None
    reasons: list[str] = field(default_factory=list)


def work_arrangement(job: Job, profile: Profile) -> RemoteType:
    """The job's remote type as this profile reads it: a search that accepts on-site work
    treats an unstated arrangement as on-site, since that is what most such postings are."""
    if job.remote_type is RemoteType.UNKNOWN and profile.onsite_regions:
        return RemoteType.ONSITE
    return job.remote_type


def _in_regions(job: Job, regions: list[str]) -> bool:
    """A hybrid or on-site job counts only when it names a country inside `regions`.
    A vague location ("Europe", "EU") says nothing about where the office is."""
    countries = {r for r in job.regions_allowed if len(r) == 2}
    return bool(countries & expand(regions))


def _preferred_country(job: Job, profile: Profile) -> str | None:
    preferred = {c.upper() for c in profile.preferred_countries}
    return next((r for r in job.regions_allowed if r in preferred), None)


def exclusion_reason(job: Job, profile: Profile) -> str | None:
    """Hard excludes. Returns a short reason or None if the job may be scored."""
    if job.role_family is RoleFamily.OTHER or job.role_family not in profile.role_families:
        return f"role family {job.role_family.value}"
    company = norm_company(job.company)
    if company and any(norm_company(c) == company for c in profile.exclude_companies):
        return "company excluded"
    for pattern in profile.exclude_title_patterns:
        if re.search(pattern, job.title, re.IGNORECASE):
            return f"title matches {pattern!r}"
    arrangement = work_arrangement(job, profile)
    if arrangement is RemoteType.HYBRID:
        if not _in_regions(job, profile.effective_hybrid_regions):
            return "hybrid outside accepted regions"
    elif arrangement is RemoteType.ONSITE:
        if not profile.onsite_regions:
            return "remote type onsite"
        if not _in_regions(job, profile.onsite_regions):
            return "on-site outside accepted regions"
    elif arrangement is not RemoteType.REMOTE:
        return f"remote type {arrangement.value}"
    if job.language and job.language not in profile.languages:
        return f"language {job.language}"
    if (
        arrangement is RemoteType.REMOTE
        and "UNKNOWN" not in job.regions_allowed
        and not is_eligible(job.regions_allowed, profile.all_eligible_regions)
    ):
        return f"not eligible: {', '.join(job.regions_allowed)}"
    if (
        job.employment_type.value != "unknown"
        and job.employment_type not in profile.employment_types
    ):
        return f"employment type {job.employment_type.value}"
    return None


def keyword_present(keyword: str, text: str) -> bool:
    """Whole-token match so a short keyword like "c" does not hit every posting.
    Tokens may contain letters, digits, '+', '#' and '.', so "c" does not match "css"
    but does match "C/C++"; "c++" and ".net" match literally."""
    pattern = rf"(?<![a-z0-9+#.]){re.escape(keyword.lower())}(?![a-z0-9+#])"
    return re.search(pattern, text.lower()) is not None


def _title_matches_family(job: Job) -> bool:
    patterns = load_taxonomy().title_patterns.get(job.role_family, [])
    return any(p.search(job.title) for p in patterns)


def score(job: Job, profile: Profile, now: datetime | None = None) -> tuple[int, list[str]]:
    now = now or datetime.now(tz=UTC)
    points = 0
    reasons: list[str] = []

    def add(n: int, why: str) -> None:
        nonlocal points
        points += n
        reasons.append(f"{why} {n:+d}")

    add(30, f"role {job.role_family.value}")
    if _title_matches_family(job):
        add(10, "title match")
    if job.language == "en":
        add(15, "english")
    elif job.language in profile.languages:
        add(10, f"language {job.language}")
    if job.remote_type is RemoteType.REMOTE:
        add(15, "remote")
    elif country := _preferred_country(job, profile):
        add(15, f"preferred country {country}")
    if "UNKNOWN" in job.regions_allowed:
        reasons.append("eligibility unknown +0")
    elif INFERRED_TAGS & set(job.tags):
        add(5, "eligibility inferred")
    else:
        add(15, "eligibility confirmed")
    if job.seniority in profile.seniority:
        add(10, f"seniority {job.seniority.value}")
    elif job.seniority in SENIOR_LEVELS:
        add(-10, f"seniority {job.seniority.value}")
    if job.posted_at and now - job.posted_at <= timedelta(days=7):
        add(5, "posted this week")
    if job.salary_raw:
        add(5, "salary listed")
    haystack = f"{job.title}\n{job.description_text}"
    boosts = [k for k in profile.keyword_boosts if keyword_present(k, haystack)]
    if boosts:
        add(min(len(boosts), 5), "keywords " + ", ".join(boosts[:5]))
    return max(0, min(100, points)), reasons


def evaluate(job: Job, profile: Profile, now: datetime | None = None) -> Verdict:
    reason = exclusion_reason(job, profile)
    if reason:
        return Verdict(
            job=job.model_copy(update={"score": 0, "score_reasons": [reason]}),
            section=Section.DROPPED,
            excluded_reason=reason,
        )
    points, reasons = score(job, profile, now)
    scored = job.model_copy(update={"score": points, "score_reasons": reasons})
    if points < profile.digest.min_score:
        section = Section.DROPPED
    elif job.seniority in SENIOR_LEVELS and job.seniority not in profile.seniority:
        section = Section.SENIOR
    elif points >= STRONG_SCORE and "UNKNOWN" not in job.regions_allowed:
        section = Section.STRONG
    else:
        section = Section.POSSIBLE
    return Verdict(job=scored, section=section, reasons=reasons)
