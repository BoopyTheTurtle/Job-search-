"""Arbetsförmedlingen JobTech JobSearch API (Sweden). Docs: https://jobsearch.api.jobtechdev.se

Endpoint: GET https://jobsearch.api.jobtechdev.se/search
Keyless in practice: since 2022 the API takes the shared public header `api-key: developer`.
We ask for `remote=true` (JobTech's own phrase match on the ad text, not a structured
field) within the Data/IT occupation field, newest first, `published-after` set from
`since`. The structured `workplace_model` field is empty in live data (2026-10-03), so the
remote classifier still reads the ad. Most ads are Swedish; the language filter keeps the
English ones.

`publication_date` is naive Swedish local time; we read it as UTC (an hour or two early,
harmless at weekly granularity). Swedish employment labels are mapped to English here so
the shared classifier needs no Swedish vocabulary.

params: `occupation_field` (taxonomy concept id, default Data/IT), `page_size` (max 100),
`max_pages` (default 5).
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any

import httpx

from jobbot.http import get_json
from jobbot.models import RawJob
from jobbot.sources import register
from jobbot.sources._common import MAX_PAGES, as_utc, from_iso, is_older, text

API_URL = "https://jobsearch.api.jobtechdev.se/search"
HEADERS = {"api-key": "developer"}
DATA_IT = "apaJ_2ja_LuF"
MAX_PAGE_SIZE = 100

_HOURS = {"heltid": "full_time", "deltid": "part_time"}
_FIXED_TERM = ("tidsbegränsad", "behovsanställning", "vikariat")


def _obj(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def employment_raw(item: dict[str, Any]) -> str | None:
    """Fixed-term and on-call contracts read as `contract`; otherwise the working hours."""
    kind = (text(_obj(item.get("employment_type")).get("label")) or "").lower()
    if any(term in kind for term in _FIXED_TERM):
        return "contract"
    hours = (text(_obj(item.get("working_hours_type")).get("label")) or "").lower()
    return _HOURS.get(hours)


class JobTech:
    name = "jobtech"

    def __init__(self, client: httpx.Client, params: dict[str, Any]) -> None:
        self._client = client
        self._field = params.get("occupation_field", DATA_IT)
        size = int(params.get("page_size", MAX_PAGE_SIZE))
        self._page_size = max(1, min(size, MAX_PAGE_SIZE))
        self._max_pages = max(1, min(int(params.get("max_pages", 5)), MAX_PAGES))

    def fetch(self, since: datetime | None, limit: int | None = None) -> Iterable[RawJob]:
        size = min(self._page_size, limit) if limit else self._page_size
        query: dict[str, Any] = {"remote": "true", "sort": "pubdate-desc", "limit": size}
        if self._field:
            query["occupation-field"] = self._field
        if since is not None:
            query["published-after"] = as_utc(since).strftime("%Y-%m-%dT%H:%M:%S")
        emitted = 0
        for page in range(self._max_pages):
            payload = get_json(
                self._client, API_URL, params={**query, "offset": page * size}, headers=HEADERS
            )
            hits = payload.get("hits") or [] if isinstance(payload, dict) else []
            for item in hits:
                if not isinstance(item, dict) or item.get("removed"):
                    continue
                job = self._to_raw(item)
                if is_older(job.posted_at, since):
                    continue
                yield job
                emitted += 1
                if limit and emitted >= limit:
                    return
            if len(hits) < size:
                return

    @staticmethod
    def _to_raw(item: dict[str, Any]) -> RawJob:
        ad_id = str(item["id"])
        address = _obj(item.get("workplace_address"))
        description = _obj(item.get("description"))
        place = [text(address.get(k)) for k in ("municipality", "region", "country")]
        return RawJob(
            source="jobtech",
            source_id=ad_id,
            url=text(item.get("webpage_url"))
            or f"https://arbetsformedlingen.se/platsbanken/annonser/{ad_id}",
            title=str(item["headline"]).strip(),
            company=text(_obj(item.get("employer")).get("name")),
            location_raw=", ".join(p for p in place if p) or None,
            description_html=text(description.get("text_formatted")),
            description_text=text(description.get("text")),
            posted_at=from_iso(item.get("publication_date")),
            salary_raw=text(item.get("salary_description")),
            employment_type_raw=employment_raw(item),
            remote_hint=None,
            tags=[t for t in (text(_obj(item.get("occupation")).get("label")),) if t],
            extra={
                "apply_url": text(_obj(item.get("application_details")).get("url")),
                "deadline": item.get("application_deadline"),
                "employment_type": _obj(item.get("employment_type")).get("label"),
            },
        )


@register("jobtech")
def _factory(client: httpx.Client, params: dict[str, Any]) -> JobTech:
    return JobTech(client, params)
