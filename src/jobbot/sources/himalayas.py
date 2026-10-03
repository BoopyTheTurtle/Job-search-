"""Himalayas jobs API. Docs: https://himalayas.app/api

Endpoint: GET https://himalayas.app/jobs/api?limit=<n>&offset=<n>
Keyless; `limit` is capped at 20 by the API. The feed is newest-first, so we page with
`offset` and stop as soon as an item is older than `since`, a page comes back short, or
20 pages were fetched. `locationRestrictions[]` (country names the role is open to) is
the most useful eligibility signal and is joined into `location_raw`. Remote by
definition (`remote_hint=True`).

params: `page_size` (default 20, max 20).
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any

import httpx

from jobbot.http import get_json
from jobbot.models import RawJob
from jobbot.sources import register
from jobbot.sources._common import (
    MAX_PAGES,
    from_unix,
    is_older,
    salary_range,
    strings,
    text,
)

API_URL = "https://himalayas.app/jobs/api"
MAX_PAGE_SIZE = 20


class Himalayas:
    name = "himalayas"

    def __init__(self, client: httpx.Client, params: dict[str, Any]) -> None:
        self._client = client
        self._params = params
        self._page_size = max(1, min(int(params.get("page_size", MAX_PAGE_SIZE)), MAX_PAGE_SIZE))

    def fetch(self, since: datetime | None, limit: int | None = None) -> Iterable[RawJob]:
        size = min(self._page_size, limit) if limit else self._page_size
        emitted = 0
        for page in range(MAX_PAGES):
            query = {"limit": size, "offset": page * size}
            payload = get_json(self._client, API_URL, params=query)
            items = payload.get("jobs") or [] if isinstance(payload, dict) else []
            stale = False
            for item in items:
                if not isinstance(item, dict):
                    continue
                job = self._to_raw(item)
                if is_older(job.posted_at, since):
                    stale = True
                    continue
                yield job
                emitted += 1
                if limit and emitted >= limit:
                    return
            if stale or len(items) < size:
                return

    @staticmethod
    def _to_raw(item: dict[str, Any]) -> RawJob:
        url = str(item.get("applicationLink") or item["url"])
        restrictions = strings(item.get("locationRestrictions"))
        return RawJob(
            source="himalayas",
            source_id=str(item.get("guid") or item.get("id") or url),
            url=url,
            title=str(item["title"]),
            company=text(item.get("companyName")),
            location_raw=", ".join(restrictions) or None,
            description_html=text(item.get("description")),
            posted_at=from_unix(item.get("pubDate")),
            salary_raw=salary_range(
                item.get("minSalary"), item.get("maxSalary"), item.get("currency")
            ),
            employment_type_raw=text(item.get("employmentType")),
            remote_hint=True,
            tags=strings(item.get("categories")),
            extra={
                "seniority": item.get("seniority"),
                "locationRestrictions": restrictions,
                "timezoneRestrictions": strings(item.get("timezoneRestrictions")),
            },
        )


@register("himalayas")
def _factory(client: httpx.Client, params: dict[str, Any]) -> Himalayas:
    return Himalayas(client, params)
