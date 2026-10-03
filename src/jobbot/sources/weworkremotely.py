"""We Work Remotely RSS feeds. Docs: https://weworkremotely.com/remote-job-rss-feed

Per-category feeds, e.g. https://weworkremotely.com/categories/remote-programming-jobs.rss
Keyless, no pagination (recent items only). Item titles usually read "Company: Title";
custom <region>, <category> and <type> elements carry the eligibility region, category and
employment type (WWR emits them without a namespace, but a namespaced variant is handled
too). Items are deduplicated across feeds by guid. WWR asks only that links point back to
the posting, which the digest does. Remote by definition (`remote_hint=True`).

params: `feeds` (list of feed URLs; defaults to the programming/devops categories).
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import Iterable
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any

import httpx

from jobbot.http import SourceError, get_text
from jobbot.models import RawJob
from jobbot.sources import register
from jobbot.sources._common import as_utc, is_older, strings, text

DEFAULT_FEEDS = [
    "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
    "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-front-end-programming-jobs.rss",
]


def _local(tag: str) -> str:
    """Strip an `{namespace}` prefix from an element tag."""
    return tag.rsplit("}", 1)[-1]


def _child_text(element: ET.Element, name: str) -> str | None:
    for child in element:
        if _local(child.tag) == name:
            return text(child.text)
    return None


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return as_utc(parsedate_to_datetime(value))
    except (TypeError, ValueError):
        return None


def _split_title(raw: str) -> tuple[str | None, str]:
    """Split "Company: Title" into (company, title); no separator -> (None, raw)."""
    company, sep, title = raw.partition(": ")
    if sep and company.strip() and title.strip():
        return company.strip(), title.strip()
    return None, raw.strip()


class WeWorkRemotely:
    name = "weworkremotely"

    def __init__(self, client: httpx.Client, params: dict[str, Any]) -> None:
        self._client = client
        self._params = params
        self._feeds = strings(params.get("feeds")) or list(DEFAULT_FEEDS)

    def fetch(self, since: datetime | None, limit: int | None = None) -> Iterable[RawJob]:
        seen: set[str] = set()
        emitted = 0
        failures: list[SourceError] = []
        for feed_url in self._feeds:
            try:
                body = get_text(self._client, feed_url)
                root = ET.fromstring(body)
            except SourceError as exc:
                failures.append(exc)
                continue
            except ET.ParseError as exc:
                failures.append(SourceError(f"{feed_url}: malformed RSS: {exc}"))
                continue
            for item in root.iter():
                if _local(item.tag) != "item":
                    continue
                job = self._to_raw(item, feed_url)
                if job is None or job.source_id in seen:
                    continue
                seen.add(job.source_id)
                if is_older(job.posted_at, since):
                    continue
                yield job
                emitted += 1
                if limit and emitted >= limit:
                    return
        if failures and len(failures) == len(self._feeds):
            raise SourceError(f"all {len(self._feeds)} WWR feeds failed: {failures[0]}")

    @staticmethod
    def _to_raw(item: ET.Element, feed_url: str) -> RawJob | None:
        link = _child_text(item, "link")
        raw_title = _child_text(item, "title")
        if not link or not raw_title:
            return None
        company, title = _split_title(raw_title)
        region = _child_text(item, "region")
        category = _child_text(item, "category")
        job_type = _child_text(item, "type")
        return RawJob(
            source="weworkremotely",
            source_id=_child_text(item, "guid") or link,
            url=link,
            title=title,
            company=company,
            location_raw=region,
            description_html=_child_text(item, "description"),
            posted_at=_parse_date(_child_text(item, "pubDate")),
            employment_type_raw=job_type,
            remote_hint=True,
            tags=[t for t in (category, job_type) if t],
            extra={"feed": feed_url, "region": region, "category": category},
        )


@register("weworkremotely")
def _factory(client: httpx.Client, params: dict[str, Any]) -> WeWorkRemotely:
    return WeWorkRemotely(client, params)
