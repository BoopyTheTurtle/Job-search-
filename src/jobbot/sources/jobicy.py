"""Jobicy remote jobs API. Docs: https://github.com/Jobicy/remote-jobs-api

Endpoint: GET https://jobicy.com/api/v2/remote-jobs?count=<n>&geo=<region>[&industry=..][&tag=..]
Keyless. Jobicy asks not to poll more than once per hour and to keep its canonical URL,
so this connector makes exactly one request per run with `count` capped at 50. The
`geo` filter (default `europe`) is applied server-side; `jobGeo` becomes `location_raw`.
Remote by definition (`remote_hint=True`).

params: `geo` (default "europe"), `industry`, `tag`.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any

import httpx

from jobbot.http import get_json
from jobbot.models import RawJob
from jobbot.sources import register
from jobbot.sources._common import first, from_iso, is_older, salary_range, strings, text

API_URL = "https://jobicy.com/api/v2/remote-jobs"
MAX_COUNT = 50


class Jobicy:
    name = "jobicy"

    def __init__(self, client: httpx.Client, params: dict[str, Any]) -> None:
        self._client = client
        self._params = params

    def fetch(self, since: datetime | None, limit: int | None = None) -> Iterable[RawJob]:
        query: dict[str, Any] = {
            "count": min(limit, MAX_COUNT) if limit else MAX_COUNT,
            "geo": self._params.get("geo", "europe"),
        }
        for key in ("industry", "tag"):
            if self._params.get(key):
                query[key] = self._params[key]
        payload = get_json(self._client, API_URL, params=query)
        items = payload.get("jobs") or [] if isinstance(payload, dict) else []
        emitted = 0
        for item in items:
            if not isinstance(item, dict):
                continue
            job = self._to_raw(item)
            if is_older(job.posted_at, since):
                continue
            yield job
            emitted += 1
            if limit and emitted >= limit:
                return

    @staticmethod
    def _to_raw(item: dict[str, Any]) -> RawJob:
        industries = strings(item.get("jobIndustry"))
        job_types = strings(item.get("jobType"))
        return RawJob(
            source="jobicy",
            source_id=str(item["id"]),
            url=str(item["url"]),
            title=str(item["jobTitle"]),
            company=text(item.get("companyName")),
            location_raw=text(item.get("jobGeo")),
            description_html=text(item.get("jobDescription")),
            posted_at=from_iso(item.get("pubDate")),
            salary_raw=salary_range(
                item.get("annualSalaryMin"),
                item.get("annualSalaryMax"),
                item.get("salaryCurrency"),
            ),
            employment_type_raw=first(job_types),
            remote_hint=True,
            tags=industries + job_types,
            extra={
                "jobLevel": item.get("jobLevel"),
                "jobIndustry": industries,
                "jobType": job_types,
                "jobExcerpt": item.get("jobExcerpt"),
            },
        )


@register("jobicy")
def _factory(client: httpx.Client, params: dict[str, Any]) -> Jobicy:
    return Jobicy(client, params)
