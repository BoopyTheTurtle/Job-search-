"""Remotive public API. Docs: https://remotive.com/api-documentation

Endpoint: GET https://remotive.com/api/remote-jobs?category=<slug>&limit=<n>
Keyless. Remotive asks for at most a few requests per day and to link back to the job
page, which the digest does. Every posting is remote by definition.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any

import httpx

from jobbot.http import get_json
from jobbot.models import RawJob
from jobbot.sources import register

API_URL = "https://remotive.com/api/remote-jobs"
DEFAULT_CATEGORIES = ["software-dev", "devops", "data", "qa", "product"]


class Remotive:
    name = "remotive"

    def __init__(self, client: httpx.Client, params: dict[str, Any]) -> None:
        self._client = client
        cats = params.get("categories") or DEFAULT_CATEGORIES
        self._categories: list[str] = [str(c) for c in cats]

    def fetch(self, since: datetime | None, limit: int | None = None) -> Iterable[RawJob]:
        seen: set[str] = set()
        emitted = 0
        for category in self._categories:
            query: dict[str, Any] = {"category": category}
            if limit:
                query["limit"] = limit
            payload = get_json(self._client, API_URL, params=query)
            for item in payload.get("jobs", []):
                job = self._to_raw(item)
                if job.source_id in seen:
                    continue
                if since and job.posted_at and job.posted_at < since:
                    continue
                seen.add(job.source_id)
                yield job
                emitted += 1
                if limit and emitted >= limit:
                    return

    @staticmethod
    def _to_raw(item: dict[str, Any]) -> RawJob:
        posted = item.get("publication_date")
        return RawJob(
            source="remotive",
            source_id=str(item["id"]),
            url=item["url"],
            title=item["title"],
            company=item.get("company_name"),
            location_raw=item.get("candidate_required_location"),
            description_html=item.get("description"),
            posted_at=datetime.fromisoformat(posted) if posted else None,
            salary_raw=item.get("salary") or None,
            employment_type_raw=item.get("job_type") or None,
            remote_hint=True,
            tags=[str(t) for t in item.get("tags", [])] + [str(item.get("category", ""))],
            extra={"category": item.get("category")},
        )


@register("remotive")
def _factory(client: httpx.Client, params: dict[str, Any]) -> Remotive:
    return Remotive(client, params)
