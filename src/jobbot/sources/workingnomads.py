"""Working Nomads exposed jobs API. Terms: https://www.workingnomads.com/api/exposed_jobs/

Endpoint: GET https://www.workingnomads.com/api/exposed_jobs/
Keyless, no pagination; one JSON array with the currently open jobs. Working Nomads is
itself an aggregator, so expect duplicates with Remotive/WWR (handled by dedupe). No
official docs page was found; field names follow the live payload as recorded in
docs/inventory/apis-and-feeds.md. Remote by definition (`remote_hint=True`).
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any

import httpx

from jobbot.http import get_json
from jobbot.models import RawJob
from jobbot.sources import register
from jobbot.sources._common import from_iso, is_older, text

API_URL = "https://www.workingnomads.com/api/exposed_jobs/"


def _split_tags(value: Any) -> list[str]:
    if isinstance(value, list):
        return [s for s in (text(v) for v in value) if s]
    raw = text(value)
    return [t.strip() for t in raw.split(",") if t.strip()] if raw else []


class WorkingNomads:
    name = "workingnomads"

    def __init__(self, client: httpx.Client, params: dict[str, Any]) -> None:
        self._client = client
        self._params = params

    def fetch(self, since: datetime | None, limit: int | None = None) -> Iterable[RawJob]:
        payload = get_json(self._client, API_URL)
        emitted = 0
        for item in payload if isinstance(payload, list) else []:
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
        url = str(item["url"])
        category = text(item.get("category_name"))
        return RawJob(
            source="workingnomads",
            source_id=str(item.get("id") or url),
            url=url,
            title=str(item["title"]),
            company=text(item.get("company_name")),
            location_raw=text(item.get("location")),
            description_html=text(item.get("description")),
            posted_at=from_iso(item.get("pub_date")),
            remote_hint=True,
            tags=_split_tags(item.get("tags")) + ([category] if category else []),
            extra={"category": category},
        )


@register("workingnomads")
def _factory(client: httpx.Client, params: dict[str, Any]) -> WorkingNomads:
    return WorkingNomads(client, params)
