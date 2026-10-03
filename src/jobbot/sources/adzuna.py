"""Adzuna search API. Docs: https://developer.adzuna.com/docs/search

Endpoint: GET https://api.adzuna.com/v1/api/jobs/{country}/search/{page}
Keyed: `app_id` and `app_key` come from ADZUNA_APP_ID / ADZUNA_APP_KEY (the pipeline skips
the source when either is unset). Adzuna has no remote flag, so we search each country
index for `what=remote` within the IT category, newest first, and let the remote
classifier read the title and snippet. Postings are in each index's local language.

`max_days_old` is derived from `since` (whole days, 1..30), so the API filters by age and
we page until a short page or `max_pages` per country. One failing country is skipped;
the source fails only when every country fails. `description` is a plain-text snippet,
not the full posting. Predicted salaries (`salary_is_predicted == "1"`) are dropped.

Terms require "Jobs by Adzuna" attribution next to the listings; the digest adds it when
any Adzuna job is shown.

params: `countries` (index codes), `what` (default "remote"), `category` (default
"it-jobs"), `results_per_page` (max 50), `max_pages` (per country, default 2),
`page_delay` (seconds, default 1.0).
"""

from __future__ import annotations

import logging
import math
import os
import time
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

import httpx

from jobbot.http import SourceError, get_json
from jobbot.models import RawJob
from jobbot.sources import register
from jobbot.sources._common import MAX_PAGES, from_iso, is_older, salary_range, text

log = logging.getLogger(__name__)

API_URL = "https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"
MAX_PAGE_SIZE = 50
DEFAULT_COUNTRIES = ["at", "be", "de", "es", "fr", "it", "nl", "pl", "gb", "us", "ca", "au", "nz"]
CURRENCIES = {
    "at": "EUR",
    "be": "EUR",
    "de": "EUR",
    "es": "EUR",
    "fr": "EUR",
    "it": "EUR",
    "nl": "EUR",
    "pl": "PLN",
    "ch": "CHF",
    "gb": "GBP",
    "us": "USD",
    "ca": "CAD",
    "au": "AUD",
    "nz": "NZD",
}


def max_days_old(since: datetime | None, now: datetime | None = None) -> int:
    """Whole days back to `since`, rounded up and clamped to 1..30; 7 when unknown."""
    if since is None:
        return 7
    now = now or datetime.now(tz=UTC)
    days = math.ceil((now - since).total_seconds() / 86400)
    return max(1, min(days, 30))


def _obj(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


class Adzuna:
    name = "adzuna"

    def __init__(self, client: httpx.Client, params: dict[str, Any]) -> None:
        self._client = client
        self._countries = [str(c).lower() for c in params.get("countries", DEFAULT_COUNTRIES)]
        self._what = str(params.get("what", "remote"))
        self._category = params.get("category", "it-jobs")
        size = int(params.get("results_per_page", MAX_PAGE_SIZE))
        self._page_size = max(1, min(size, MAX_PAGE_SIZE))
        self._max_pages = max(1, min(int(params.get("max_pages", 2)), MAX_PAGES))
        self._page_delay = float(params.get("page_delay", 1.0))

    def fetch(self, since: datetime | None, limit: int | None = None) -> Iterable[RawJob]:
        app_id = os.environ.get("ADZUNA_APP_ID", "").strip()
        app_key = os.environ.get("ADZUNA_APP_KEY", "").strip()
        if not app_id or not app_key:
            raise SourceError("ADZUNA_APP_ID and ADZUNA_APP_KEY must be set")
        size = min(self._page_size, limit) if limit else self._page_size
        base = {
            "app_id": app_id,
            "app_key": app_key,
            "what": self._what,
            "results_per_page": size,
            "max_days_old": max_days_old(since),
            "sort_by": "date",
            "content-type": "application/json",
        }
        if self._category:
            base["category"] = self._category

        emitted = 0
        failures: list[str] = []
        requests = 0
        for country in self._countries:
            try:
                for page in range(1, self._max_pages + 1):
                    if requests and self._page_delay > 0:
                        time.sleep(self._page_delay)
                    requests += 1
                    url = API_URL.format(country=country, page=page)
                    payload = get_json(self._client, url, params=base)
                    items = payload.get("results") or [] if isinstance(payload, dict) else []
                    for item in items:
                        if not isinstance(item, dict):
                            continue
                        job = self._to_raw(item, country)
                        if is_older(job.posted_at, since):
                            continue
                        yield job
                        emitted += 1
                        if limit and emitted >= limit:
                            return
                    if len(items) < size:
                        break
            except SourceError as exc:
                # httpx errors quote the full request URL, credentials included.
                message = str(exc).replace(app_key, "***").replace(app_id, "***")
                log.warning("adzuna %s failed: %s", country, message)
                failures.append(country)
        if failures and len(failures) == len(self._countries):
            raise SourceError(f"every Adzuna country failed: {', '.join(failures)}")

    @staticmethod
    def _to_raw(item: dict[str, Any], country: str) -> RawJob:
        company = _obj(item.get("company"))
        location = _obj(item.get("location"))
        category = _obj(item.get("category"))
        area = [a for a in (text(v) for v in location.get("area") or []) if a]
        predicted = str(item.get("salary_is_predicted", "0")) == "1"
        contract_type = text(item.get("contract_type"))
        url = str(item["redirect_url"])
        return RawJob(
            source="adzuna",
            source_id=f"{country}:{item.get('id') or url}",
            url=url,
            title=str(item["title"]).strip(),
            company=text(company.get("display_name")),
            location_raw=text(location.get("display_name")) or ", ".join(reversed(area)) or None,
            description_text=text(item.get("description")),
            posted_at=from_iso(item.get("created")),
            salary_raw=None
            if predicted
            else salary_range(
                item.get("salary_min"), item.get("salary_max"), CURRENCIES.get(country)
            ),
            employment_type_raw="contract"
            if contract_type == "contract"
            else text(item.get("contract_time")) or contract_type,
            remote_hint=None,
            tags=[t for t in (text(category.get("label")),) if t],
            extra={"country": country, "area": area, "category": category.get("tag")},
        )


@register("adzuna")
def _factory(client: httpx.Client, params: dict[str, Any]) -> Adzuna:
    return Adzuna(client, params)
