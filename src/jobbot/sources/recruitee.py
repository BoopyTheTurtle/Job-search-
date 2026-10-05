"""Recruitee Careers Site API.
Docs: https://docs.recruitee.com/reference/intro-to-careers-site-api

Endpoint: GET https://{slug}.recruitee.com/api/offers/
Keyless and public: one request per company returns every published offer with its full
description and structured `remote` / `hybrid` / `on_site` flags. Companies come from
config/companies.yaml (`ats: recruitee`).

params: `companies` (list of company slugs; default: the watchlist).
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from datetime import datetime
from typing import Any

import httpx

from jobbot.http import get_json
from jobbot.models import RawJob
from jobbot.sources import register
from jobbot.sources._common import from_iso, is_older, salary_range, strings, text
from jobbot.sources._watchlist import arrangement, crawl_boards, slugs

API_URL = "https://{slug}.recruitee.com/api/offers/"
_EMPLOYMENT = {
    "fulltime": "full_time",
    "parttime": "part_time",
    "contract": "contract",
    "freelance": "freelance",
    "internship": "internship",
    "traineeship": "internship",
}


def _obj(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def published(value: Any) -> datetime | None:
    """Recruitee writes "2026-10-02 15:52:39 UTC"."""
    raw = text(value)
    return from_iso(raw.replace(" UTC", "+00:00")) if raw else None


def employment(code: Any) -> str | None:
    """`fulltime_permanent`, `parttime_fixed_term`, `internship`, ... → our raw hint."""
    raw = text(code)
    if not raw:
        return None
    return _EMPLOYMENT.get(raw.split("_")[0], raw)


class Recruitee:
    name = "recruitee"

    def __init__(self, client: httpx.Client, params: dict[str, Any]) -> None:
        self._client = client
        self._boards = slugs(params, "recruitee")

    def fetch(self, since: datetime | None, limit: int | None = None) -> Iterable[RawJob]:
        def board(slug: str) -> Iterator[RawJob]:
            payload = get_json(self._client, API_URL.format(slug=slug))
            items = payload.get("offers") or [] if isinstance(payload, dict) else []
            for item in items:
                if isinstance(item, dict):
                    job = self._to_raw(item, slug)
                    if not is_older(job.posted_at, since):
                        yield job

        return crawl_boards(self.name, self._boards, board, limit)

    @staticmethod
    def _to_raw(item: dict[str, Any], slug: str) -> RawJob:
        remote_hint, location = arrangement(
            item.get("remote"), item.get("hybrid"), text(item.get("location"))
        )
        parts = (text(item.get("description")), text(item.get("requirements")))
        body = "\n".join(p for p in parts if p)
        salary = _obj(item.get("salary"))
        return RawJob(
            source="recruitee",
            source_id=f"{slug}:{item['id']}",
            url=str(item["careers_url"]),
            title=str(item["title"]).strip(),
            company=text(item.get("company_name")) or slug,
            location_raw=location,
            description_html=body or None,
            posted_at=published(item.get("published_at")) or published(item.get("created_at")),
            salary_raw=salary_range(salary.get("min"), salary.get("max"), salary.get("currency")),
            employment_type_raw=employment(item.get("employment_type_code")),
            remote_hint=remote_hint,
            tags=strings([item.get("department"), *(item.get("tags") or [])]),
            extra={
                "board": slug,
                "country_code": item.get("country_code"),
                "experience_code": item.get("experience_code"),
            },
        )


@register("recruitee")
def _factory(client: httpx.Client, params: dict[str, Any]) -> Recruitee:
    return Recruitee(client, params)
