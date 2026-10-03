"""Arbeitnow job board API. Docs: https://www.arbeitnow.com/api

Endpoint: GET https://www.arbeitnow.com/api/job-board-api
Keyless, Laravel-style pagination via `links.next`. Items are newest-first, so we stop
following pages as soon as an item is older than `since`. `remote` is a reliable boolean
and becomes `remote_hint`. Coverage is Germany/EU heavy with many German-language posts;
language filtering happens later in the pipeline.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any

import httpx

from jobbot.http import get_json
from jobbot.models import RawJob
from jobbot.sources import register
from jobbot.sources._common import MAX_PAGES, first, from_unix, is_older, strings, text

API_URL = "https://www.arbeitnow.com/api/job-board-api"


class Arbeitnow:
    name = "arbeitnow"

    def __init__(self, client: httpx.Client, params: dict[str, Any]) -> None:
        self._client = client
        self._params = params

    def fetch(self, since: datetime | None, limit: int | None = None) -> Iterable[RawJob]:
        url: str | None = API_URL
        emitted = 0
        for _ in range(MAX_PAGES):
            if not url:
                return
            payload = get_json(self._client, url)
            items = payload.get("data") or [] if isinstance(payload, dict) else []
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
            if stale or not items:
                return
            links = payload.get("links") if isinstance(payload, dict) else None
            url = text(links.get("next")) if isinstance(links, dict) else None

    @staticmethod
    def _to_raw(item: dict[str, Any]) -> RawJob:
        remote = item.get("remote")
        job_types = strings(item.get("job_types"))
        return RawJob(
            source="arbeitnow",
            source_id=str(item.get("slug") or item["url"]),
            url=str(item["url"]),
            title=str(item["title"]),
            company=text(item.get("company_name")),
            location_raw=text(item.get("location")),
            description_html=text(item.get("description")),
            posted_at=from_unix(item.get("created_at")),
            employment_type_raw=first(job_types),
            remote_hint=remote if isinstance(remote, bool) else None,
            tags=strings(item.get("tags")) + job_types,
            extra={"job_types": job_types},
        )


@register("arbeitnow")
def _factory(client: httpx.Client, params: dict[str, Any]) -> Arbeitnow:
    return Arbeitnow(client, params)
