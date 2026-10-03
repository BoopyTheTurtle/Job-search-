"""RemoteOK public API. Terms: https://remoteok.com/api (legal notice in element 0)

Endpoint: GET https://remoteok.com/api
Keyless, no pagination; returns the ~100 most recent postings as a JSON array whose first
element is a legal notice rather than a job. RemoteOK requires a followed link back to the
posting URL and naming RemoteOK as source, which the digest does. Every posting is remote
by definition (`remote_hint=True`); `location` carries the region restriction.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any

import httpx

from jobbot.http import get_json
from jobbot.models import RawJob
from jobbot.sources import register
from jobbot.sources._common import from_iso, from_unix, is_older, salary_range, strings, text

API_URL = "https://remoteok.com/api"


class RemoteOK:
    name = "remoteok"

    def __init__(self, client: httpx.Client, params: dict[str, Any]) -> None:
        self._client = client
        self._params = params

    def fetch(self, since: datetime | None, limit: int | None = None) -> Iterable[RawJob]:
        payload = get_json(self._client, API_URL)
        emitted = 0
        for item in payload if isinstance(payload, list) else []:
            if not isinstance(item, dict) or "id" not in item or "position" not in item:
                continue  # element 0 is the legal notice
            job = self._to_raw(item)
            if is_older(job.posted_at, since):
                continue
            yield job
            emitted += 1
            if limit and emitted >= limit:
                return

    @staticmethod
    def _to_raw(item: dict[str, Any]) -> RawJob:
        return RawJob(
            source="remoteok",
            source_id=str(item["id"]),
            url=str(item["url"]),
            title=str(item["position"]),
            company=text(item.get("company")),
            location_raw=text(item.get("location")),
            description_html=text(item.get("description")),
            posted_at=from_iso(item.get("date")) or from_unix(item.get("epoch")),
            salary_raw=salary_range(item.get("salary_min"), item.get("salary_max"), "USD"),
            remote_hint=True,
            tags=strings(item.get("tags")),
            extra={"slug": item.get("slug"), "apply_url": item.get("apply_url")},
        )


@register("remoteok")
def _factory(client: httpx.Client, params: dict[str, Any]) -> RemoteOK:
    return RemoteOK(client, params)
