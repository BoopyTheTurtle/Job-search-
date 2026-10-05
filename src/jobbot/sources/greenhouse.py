"""Greenhouse job board API. Docs: https://developers.greenhouse.io/job-board.html

Endpoint: GET https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true
Keyless and public: every company on Greenhouse publishes its board here, EU-hosted boards
included. One request per board returns every open job with its full description
(`content`, HTML-escaped HTML). Greenhouse has no remote flag; the remote classifier reads
the title and location. Boards come from config/companies.yaml (`ats: greenhouse`).

params: `companies` (list of board slugs; default: the watchlist).
"""

from __future__ import annotations

import html
from collections.abc import Iterable, Iterator
from datetime import datetime
from typing import Any

import httpx

from jobbot.http import get_json
from jobbot.models import RawJob
from jobbot.sources import register
from jobbot.sources._common import from_iso, is_older, strings, text
from jobbot.sources._watchlist import crawl_boards, slugs

API_URL = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"


def _obj(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


class Greenhouse:
    name = "greenhouse"

    def __init__(self, client: httpx.Client, params: dict[str, Any]) -> None:
        self._client = client
        self._boards = slugs(params, "greenhouse")

    def fetch(self, since: datetime | None, limit: int | None = None) -> Iterable[RawJob]:
        def board(slug: str) -> Iterator[RawJob]:
            payload = get_json(self._client, API_URL.format(slug=slug), params={"content": "true"})
            items = payload.get("jobs") or [] if isinstance(payload, dict) else []
            for item in items:
                if isinstance(item, dict):
                    job = self._to_raw(item, slug)
                    if not is_older(job.posted_at, since):
                        yield job

        return crawl_boards(self.name, self._boards, board, limit)

    @staticmethod
    def _to_raw(item: dict[str, Any], slug: str) -> RawJob:
        content = text(item.get("content"))
        departments = [_obj(d).get("name") for d in item.get("departments") or []]
        return RawJob(
            source="greenhouse",
            source_id=f"{slug}:{item['id']}",
            url=str(item["absolute_url"]),
            title=str(item["title"]).strip(),
            company=text(item.get("company_name")) or slug,
            location_raw=text(_obj(item.get("location")).get("name")),
            description_html=html.unescape(content) if content else None,
            posted_at=from_iso(item.get("first_published")) or from_iso(item.get("updated_at")),
            remote_hint=None,
            tags=strings(departments),
            extra={"board": slug, "requisition_id": item.get("requisition_id")},
        )


@register("greenhouse")
def _factory(client: httpx.Client, params: dict[str, Any]) -> Greenhouse:
    return Greenhouse(client, params)
