"""Render a Digest as Markdown (committed copy), HTML and plain text (email)."""

from __future__ import annotations

from datetime import datetime
from functools import lru_cache

from jinja2 import Environment, PackageLoader

from jobbot.digest.build import Digest
from jobbot.models import Job

_REGION_LABELS = {
    "WORLDWIDE": "Worldwide",
    "EU": "EU",
    "EEA": "EEA",
    "EUROPE": "Europe",
    "AMERICAS": "Americas",
    "APAC": "APAC",
    "UNKNOWN": "region not stated",
}


def region_label(job: Job) -> str:
    return ", ".join(_REGION_LABELS.get(r, r) for r in job.regions_allowed)


def type_label(job: Job) -> str:
    parts = [job.employment_type.value.replace("_", " ")]
    if job.remote_type.value != "remote":
        parts.append(job.remote_type.value)
    return " · ".join(p for p in parts if p and p != "unknown")


def seniority_label(job: Job) -> str:
    return job.seniority.value if job.seniority.value != "unknown" else ""


def language_tag(job: Job) -> str:
    return "" if job.language in (None, "en") else f"[{job.language}]"


def age_label(job: Job, now: datetime) -> str:
    if not job.posted_at:
        return ""
    days = (now - job.posted_at).days
    if days <= 0:
        return "today"
    if days == 1:
        return "1 day ago"
    return f"{days} days ago"


@lru_cache(maxsize=1)
def _env() -> Environment:
    env = Environment(
        loader=PackageLoader("jobbot.digest", "templates"),
        autoescape=lambda name: bool(name) and ".html" in str(name),  # html.j2 only
        trim_blocks=True,
        lstrip_blocks=True,
        # Included per-job partials must keep their final newline, or list items run together.
        keep_trailing_newline=True,
    )
    env.filters["region"] = region_label
    env.filters["jobtype"] = type_label
    env.filters["seniority"] = seniority_label
    env.filters["lang"] = language_tag
    env.globals["age"] = age_label
    return env


def _render(template: str, digest: Digest) -> str:
    return _env().get_template(template).render(d=digest, now=digest.date).rstrip() + "\n"


def render_markdown(digest: Digest) -> str:
    return _render("digest.md.j2", digest)


def render_html(digest: Digest) -> str:
    return _render("digest.html.j2", digest)


def render_text(digest: Digest) -> str:
    return _render("digest.txt.j2", digest)
