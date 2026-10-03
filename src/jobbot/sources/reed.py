"""Reed.co.uk Jobseeker API (UK). Docs: https://www.reed.co.uk/developers/jobseeker

Endpoint: GET https://www.reed.co.uk/api/1.0/search
Keyed: REED_API_KEY goes in HTTP Basic auth as the username with an empty password (the
pipeline skips the source when it is unset). The API has no remote flag, no date filter
and no documented sort, so we run each keyword query for up to `max_pages` pages and
drop postings older than `since` ourselves. `date` is dd/mm/yyyy; `jobDescription` is a
plain-text snippet. Reed is UK-only and English.

The digest credits Reed next to its listings (see digest.build.ATTRIBUTIONS).

params: `keywords` (list of queries, default remote developer/engineer/data),
`page_size` (max 100), `max_pages` (per query, default 2).
"""

from __future__ import annotations

import base64
import os
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

import httpx

from jobbot.http import SourceError, get_json
from jobbot.models import RawJob
from jobbot.sources import register
from jobbot.sources._common import MAX_PAGES, is_older, salary_range, text

API_URL = "https://www.reed.co.uk/api/1.0/search"
MAX_PAGE_SIZE = 100
DEFAULT_KEYWORDS = ["remote developer", "remote engineer", "remote data"]


def from_dmy(value: Any) -> datetime | None:
    """Reed's dd/mm/yyyy date to midnight UTC."""
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value.strip(), "%d/%m/%Y").replace(tzinfo=UTC)
    except ValueError:
        return None


def employment_raw(item: dict[str, Any]) -> str | None:
    if item.get("contractType"):
        return str(item["contractType"]).lower()
    if item.get("partTime"):
        return "part_time"
    if item.get("fullTime"):
        return "full_time"
    return None


class Reed:
    name = "reed"

    def __init__(self, client: httpx.Client, params: dict[str, Any]) -> None:
        self._client = client
        self._keywords = [str(k) for k in params.get("keywords", DEFAULT_KEYWORDS)]
        size = int(params.get("page_size", MAX_PAGE_SIZE))
        self._page_size = max(1, min(size, MAX_PAGE_SIZE))
        self._max_pages = max(1, min(int(params.get("max_pages", 2)), MAX_PAGES))

    def fetch(self, since: datetime | None, limit: int | None = None) -> Iterable[RawJob]:
        key = os.environ.get("REED_API_KEY", "").strip()
        if not key:
            raise SourceError("REED_API_KEY must be set")
        token = base64.b64encode(f"{key}:".encode()).decode()
        headers = {"Authorization": f"Basic {token}"}
        size = min(self._page_size, limit) if limit else self._page_size
        seen: set[str] = set()
        emitted = 0
        for keywords in self._keywords:
            for page in range(self._max_pages):
                query = {"keywords": keywords, "resultsToTake": size, "resultsToSkip": page * size}
                payload = get_json(self._client, API_URL, params=query, headers=headers)
                items = payload.get("results") or [] if isinstance(payload, dict) else []
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    job = self._to_raw(item)
                    # Overlapping queries return the same job; dedupe would merge them, but
                    # skipping here keeps the fetched count honest.
                    if job.source_id in seen or is_older(job.posted_at, since):
                        continue
                    seen.add(job.source_id)
                    yield job
                    emitted += 1
                    if limit and emitted >= limit:
                        return
                if len(items) < size:
                    break

    @staticmethod
    def _to_raw(item: dict[str, Any]) -> RawJob:
        job_id = str(item["jobId"])
        return RawJob(
            source="reed",
            source_id=job_id,
            url=text(item.get("jobUrl")) or f"https://www.reed.co.uk/jobs/{job_id}",
            title=str(item["jobTitle"]).strip(),
            company=text(item.get("employerName")),
            location_raw=text(item.get("locationName")),
            description_text=text(item.get("jobDescription")),
            posted_at=from_dmy(item.get("date")),
            salary_raw=salary_range(
                item.get("minimumSalary"), item.get("maximumSalary"), item.get("currency")
            ),
            employment_type_raw=employment_raw(item),
            remote_hint=None,
            extra={
                "expirationDate": item.get("expirationDate"),
                "applications": item.get("applications"),
            },
        )


@register("reed")
def _factory(client: httpx.Client, params: dict[str, Any]) -> Reed:
    return Reed(client, params)
