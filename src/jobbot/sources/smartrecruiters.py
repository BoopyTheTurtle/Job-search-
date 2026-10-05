"""SmartRecruiters Posting API. Docs: https://developers.smartrecruiters.com/docs/posting-api

List: GET https://api.smartrecruiters.com/v1/companies/{id}/postings?limit=100&offset=N
Detail: GET https://api.smartrecruiters.com/v1/companies/{id}/postings/{postingId}
Keyless and public. The list carries title, location (with `remote` / `hybrid` flags),
employment type and release date; the description lives only in the detail, so we fetch
the detail for postings released since `since` and no others. Companies come from
config/companies.yaml (`ats: smartrecruiters`; the slug is the company identifier).

params: `companies` (list of company identifiers; default: the watchlist), `page_size`
(max 100), `max_pages` (per company, default 5).
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from datetime import datetime
from typing import Any

import httpx

from jobbot.http import get_json
from jobbot.models import RawJob
from jobbot.sources import register
from jobbot.sources._common import MAX_PAGES, from_iso, is_older, strings, text
from jobbot.sources._watchlist import arrangement, crawl_boards, slugs

LIST_URL = "https://api.smartrecruiters.com/v1/companies/{company}/postings"
DETAIL_URL = LIST_URL + "/{posting}"
PUBLIC_URL = "https://jobs.smartrecruiters.com/{company}/{posting}"
MAX_PAGE_SIZE = 100
_SECTIONS = ("jobDescription", "qualifications", "additionalInformation", "companyDescription")
_EMPLOYMENT = {
    "permanent": "full_time",
    "full_time": "full_time",
    "part_time": "part_time",
    "contract": "contract",
    "temporary": "contract",
    "intern": "internship",
    "internship": "internship",
    "freelance": "freelance",
}


def _obj(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def location_text(location: dict[str, Any]) -> str | None:
    full = text(location.get("fullLocation"))
    if full:
        return full
    parts = [text(location.get(k)) for k in ("city", "region", "country")]
    return ", ".join(p for p in parts if p) or None


class SmartRecruiters:
    name = "smartrecruiters"

    def __init__(self, client: httpx.Client, params: dict[str, Any]) -> None:
        self._client = client
        self._boards = slugs(params, "smartrecruiters")
        size = int(params.get("page_size", MAX_PAGE_SIZE))
        self._page_size = max(1, min(size, MAX_PAGE_SIZE))
        self._max_pages = max(1, min(int(params.get("max_pages", 5)), MAX_PAGES))

    def fetch(self, since: datetime | None, limit: int | None = None) -> Iterable[RawJob]:
        def board(company: str) -> Iterator[RawJob]:
            for page in range(self._max_pages):
                payload = get_json(
                    self._client,
                    LIST_URL.format(company=company),
                    params={"limit": self._page_size, "offset": page * self._page_size},
                )
                items = payload.get("content") or [] if isinstance(payload, dict) else []
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    if is_older(from_iso(item.get("releasedDate")), since):
                        continue
                    url = DETAIL_URL.format(company=company, posting=item["id"])
                    yield self._to_raw(item, _obj(get_json(self._client, url)), company)
                if len(items) < self._page_size:
                    return

        return crawl_boards(self.name, self._boards, board, limit)

    @staticmethod
    def _to_raw(item: dict[str, Any], detail: dict[str, Any], company: str) -> RawJob:
        location = _obj(item.get("location"))
        remote_hint, location_raw = arrangement(
            location.get("remote"), location.get("hybrid"), location_text(location)
        )
        sections = _obj(_obj(detail.get("jobAd")).get("sections"))
        texts = (text(_obj(sections.get(k)).get("text")) for k in _SECTIONS)
        body = "\n".join(t for t in texts if t)
        employment = _obj(item.get("typeOfEmployment"))
        posting = str(item["id"])
        return RawJob(
            source="smartrecruiters",
            source_id=f"{company}:{posting}",
            url=text(detail.get("postingUrl"))
            or PUBLIC_URL.format(company=company, posting=posting),
            title=str(item["name"]).strip(),
            company=text(_obj(item.get("company")).get("name")) or company,
            location_raw=location_raw,
            description_html=body or None,
            posted_at=from_iso(item.get("releasedDate")),
            employment_type_raw=_EMPLOYMENT.get(
                str(employment.get("id")), text(employment.get("label"))
            ),
            remote_hint=remote_hint,
            tags=strings(
                [_obj(item.get(k)).get("label") for k in ("department", "function", "industry")]
            ),
            extra={
                "board": company,
                "experience_level": _obj(item.get("experienceLevel")).get("id"),
                "ref_number": item.get("refNumber"),
            },
        )


@register("smartrecruiters")
def _factory(client: httpx.Client, params: dict[str, Any]) -> SmartRecruiters:
    return SmartRecruiters(client, params)
