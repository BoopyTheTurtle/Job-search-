"""Enrichment: language, remote type, regions, role family, seniority, employment type.

Profile-free by design (CLAUDE.md): everything here describes the posting, never the user.
"""

from __future__ import annotations

from jobbot.enrich.language import detect_language
from jobbot.enrich.regions import parse_regions
from jobbot.enrich.remote import classify_remote
from jobbot.enrich.roles import classify_role
from jobbot.enrich.seniority import classify_employment, classify_seniority
from jobbot.models import Job, RawJob


def enrich(job: Job, raw: RawJob) -> Job:
    text = job.description_text
    language, _confidence = detect_language(f"{job.title}\n{text}")
    remote_type = classify_remote(
        title=job.title,
        location_raw=job.location_raw,
        description_text=text,
        remote_hint=raw.remote_hint,
    )
    regions, region_tags = parse_regions(
        location_raw=job.location_raw, title=job.title, description_text=text
    )
    role_family = classify_role(job.title, text)
    seniority = classify_seniority(job.title, text)
    employment_type = classify_employment(raw.employment_type_raw, job.title, text)
    return job.model_copy(
        update={
            "language": language,
            "remote_type": remote_type,
            "regions_allowed": regions,
            "role_family": role_family,
            "seniority": seniority,
            "employment_type": employment_type,
            "tags": sorted(set(job.tags) | set(region_tags)),
        }
    )


__all__ = ["enrich"]
