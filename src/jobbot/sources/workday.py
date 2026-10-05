"""Workday career sites (the public JSON API behind `*.myworkdayjobs.com`).

List: POST https://{tenant}.{wdN}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs
      with {"appliedFacets": {}, "limit": 20, "offset": N, "searchText": ""}
Detail: GET https://{tenant}.{wdN}.myworkdayjobs.com/wday/cxs/{tenant}/{site}{externalPath}
Keyless; it is the API the career site itself calls, and robots.txt allows it. The list
gives only a relative age ("Posted 3 Days Ago"), so we fetch the detail (description,
country, posting date) for postings young enough to be new since `since`, and no others.
Sites come from config/companies.yaml (`ats: workday`, slug `tenant.wdN/site`, e.g.
`ardian.wd103/ArdianCareers`).

params: `companies` (list of slugs; default: the watchlist), `max_pages` (20 postings per
page, default 10), `page_delay` (seconds between requests, default 0.5).
"""

from __future__ import annotations

import re
import time
from collections.abc import Iterable, Iterator
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from jobbot.http import SourceError, get_json
from jobbot.models import RawJob
from jobbot.sources import register
from jobbot.sources._common import MAX_PAGES, as_utc, from_iso, text
from jobbot.sources._watchlist import arrangement, crawl_boards, names, slugs

PAGE_SIZE = 20  # the API's maximum
_AGE = re.compile(r"(\d+)\+?\s+days?\s+ago", re.IGNORECASE)
_REMOTE = {"remote": True, "fully remote": True}
_HYBRID = {"hybrid", "flexible"}


def _obj(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def parse_slug(slug: str) -> tuple[str, str]:
    """`ardian.wd103/ArdianCareers` → (base URL, cxs prefix)."""
    host, _, site = slug.partition("/")
    tenant = host.split(".")[0]
    if not tenant or not site or "." not in host:
        raise ValueError(f"workday slug must look like tenant.wdN/site, got {slug!r}")
    base = f"https://{host}.myworkdayjobs.com"
    return base, f"{base}/wday/cxs/{tenant}/{site}"


def age_days(posted_on: Any) -> int | None:
    """ "Posted Today" → 0, "Posted Yesterday" → 1, "Posted 30+ Days Ago" → 30."""
    raw = (text(posted_on) or "").lower()
    if "today" in raw:
        return 0
    if "yesterday" in raw:
        return 1
    match = _AGE.search(raw)
    return int(match.group(1)) if match else None


def is_recent(posted_on: Any, since: datetime | None, now: datetime) -> bool:
    """Keep a posting unless its relative age puts it clearly before `since`. A day of
    slack covers the rounding in Workday's wording; unknown ages are kept."""
    days = age_days(posted_on)
    if since is None or days is None:
        return True
    return now - timedelta(days=days) >= as_utc(since) - timedelta(days=1)


class Workday:
    name = "workday"

    def __init__(self, client: httpx.Client, params: dict[str, Any]) -> None:
        self._client = client
        self._boards = slugs(params, "workday")
        self._names = {} if "companies" in params else names("workday")
        self._max_pages = max(1, min(int(params.get("max_pages", 10)), MAX_PAGES))
        self._page_delay = float(params.get("page_delay", 0.5))

    def _pause(self) -> None:
        if self._page_delay > 0:
            time.sleep(self._page_delay)

    def fetch(self, since: datetime | None, limit: int | None = None) -> Iterable[RawJob]:
        now = datetime.now(tz=UTC)

        def board(slug: str) -> Iterator[RawJob]:
            try:
                base, api = parse_slug(slug)
            except ValueError as exc:
                raise SourceError(str(exc)) from exc
            for page in range(self._max_pages):
                if page:
                    self._pause()
                payload = self._post(
                    f"{api}/jobs",
                    {"appliedFacets": {}, "limit": PAGE_SIZE, "offset": page * PAGE_SIZE},
                )
                items = payload.get("jobPostings") or []
                for item in items:
                    if not isinstance(item, dict) or not item.get("externalPath"):
                        continue
                    if not is_recent(item.get("postedOn"), since, now):
                        continue
                    self._pause()
                    detail = _obj(get_json(self._client, f"{api}{item['externalPath']}"))
                    job = self._to_raw(item, detail, slug, base)
                    if slug in self._names:
                        job = job.model_copy(update={"company": self._names[slug]})
                    yield job
                if len(items) < PAGE_SIZE:
                    return

        return crawl_boards(self.name, self._boards, board, limit)

    def _post(self, url: str, body: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self._client.post(url, json=body)
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise SourceError(f"POST {url} failed: {exc}") from exc
        return _obj(data)

    @staticmethod
    def _to_raw(item: dict[str, Any], detail: dict[str, Any], slug: str, base: str) -> RawJob:
        info = _obj(detail.get("jobPostingInfo"))
        city = text(info.get("location")) or text(item.get("locationsText"))
        country = text(_obj(info.get("country")).get("descriptor"))
        location = city
        if country and country not in (city or ""):
            location = f"{city}, {country}" if city else country
        remote_type = (text(info.get("remoteType")) or "").lower()
        remote_hint, location = arrangement(
            True if remote_type in _REMOTE else (False if remote_type else None),
            remote_type in _HYBRID,
            location,
        )
        posting_id = text(info.get("jobReqId")) or str(item["externalPath"]).rsplit("_", 1)[-1]
        return RawJob(
            source="workday",
            source_id=f"{slug}:{posting_id}",
            url=text(info.get("externalUrl"))
            or f"{base}/{slug.partition('/')[2]}{item['externalPath']}",
            title=str(info.get("title") or item["title"]).strip(),
            company=text(_obj(detail.get("hiringOrganization")).get("name")) or slug,
            location_raw=location,
            description_html=text(info.get("jobDescription")),
            posted_at=from_iso(info.get("startDate")),
            employment_type_raw=text(info.get("timeType")),
            remote_hint=remote_hint,
            extra={"board": slug, "posted_on": item.get("postedOn")},
        )


@register("workday")
def _factory(client: httpx.Client, params: dict[str, Any]) -> Workday:
    return Workday(client, params)
