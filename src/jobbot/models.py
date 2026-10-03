"""Canonical data model. See docs/SPEC.md §6."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from enum import StrEnum
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import BaseModel, Field


class RemoteType(StrEnum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"
    UNKNOWN = "unknown"


class EmploymentType(StrEnum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    FREELANCE = "freelance"
    INTERNSHIP = "internship"
    UNKNOWN = "unknown"


class Seniority(StrEnum):
    INTERN = "intern"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    UNKNOWN = "unknown"


class RoleFamily(StrEnum):
    SOFTWARE_DEV = "software_dev"
    DEVOPS_CLOUD = "devops_cloud"
    DATA_ML_AI = "data_ml_ai"
    IT_OPS_QA_PRODUCT = "it_ops_qa_product"
    OTHER = "other"


class RawJob(BaseModel):
    """What a connector returns: the source's own fields, lightly typed, nothing inferred."""

    source: str
    source_id: str
    url: str
    title: str
    company: str | None = None
    location_raw: str | None = None
    description_html: str | None = None
    description_text: str | None = None
    posted_at: datetime | None = None
    salary_raw: str | None = None
    employment_type_raw: str | None = None
    remote_hint: bool | None = None
    """True when the source itself asserts the job is remote (e.g. a remote-only board)."""
    tags: list[str] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)


class Job(BaseModel):
    """Normalized, enriched posting. One row per dedup key."""

    id: str
    title: str
    company: str | None
    url: str
    source: str
    source_ids: dict[str, str] = Field(default_factory=dict)
    location_raw: str | None = None
    remote_type: RemoteType = RemoteType.UNKNOWN
    regions_allowed: list[str] = Field(default_factory=lambda: ["UNKNOWN"])
    employment_type: EmploymentType = EmploymentType.UNKNOWN
    seniority: Seniority = Seniority.UNKNOWN
    role_family: RoleFamily = RoleFamily.OTHER
    language: str | None = None
    salary_raw: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    salary_currency: str | None = None
    salary_period: str | None = None
    posted_at: datetime | None = None
    first_seen: datetime
    last_seen: datetime
    description_text: str = ""
    tags: list[str] = Field(default_factory=list)
    score: int = 0
    score_reasons: list[str] = Field(default_factory=list)


_TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "ref",
    "source",
    "gh_src",
    "lever-source",
}


def canonical_url(url: str) -> str:
    """Lower-case scheme/host, drop tracking params and fragments, strip trailing slash."""
    parts = urlsplit(url.strip())
    query = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if k not in _TRACKING_PARAMS
    ]
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, urlencode(query), ""))


def _norm(text: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def dedup_key(title: str, company: str | None, url: str) -> str:
    """Stable id. Primary signal is the canonical URL; company+title lets cross-source
    duplicates with different URLs collapse in a later fuzzy pass (see dedupe module)."""
    basis = canonical_url(url) if url else f"{_norm(company)}|{_norm(title)}"
    return hashlib.sha1(basis.encode("utf-8")).hexdigest()
