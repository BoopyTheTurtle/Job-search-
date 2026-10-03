"""RawJob → Job normalisation: HTML to text, lenient dates, canonical URL. SPEC §5.1."""

from __future__ import annotations

import html
import re
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser

from jobbot.models import Job, RawJob, canonical_url, dedup_key

_BLOCK_TAGS = {
    "p",
    "div",
    "br",
    "ul",
    "ol",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "tr",
    "table",
    "section",
    "article",
    "blockquote",
    "pre",
    "hr",
}
_SKIP_TAGS = {"script", "style", "noscript"}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _SKIP_TAGS:
            self._skip += 1
        elif tag == "li":
            self._parts.append("\n- ")
        elif tag in _BLOCK_TAGS:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIP_TAGS:
            self._skip = max(0, self._skip - 1)
        elif tag in _BLOCK_TAGS or tag == "li":
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self._parts.append(data)

    def text(self) -> str:
        return "".join(self._parts)


def html_to_text(value: str | None) -> str:
    """Strip tags, keep list bullets and paragraph breaks, collapse whitespace."""
    if not value:
        return ""
    # Some APIs (Arbeitnow, for one) ship HTML with the tags themselves entity-escaped
    # ("&lt;p&gt;"). Unescape once so the parser sees real tags instead of literal text.
    if "<" not in value and "&lt;" in value:
        value = html.unescape(value)
    parser = _TextExtractor()
    parser.feed(value)
    parser.close()
    text = parser.text().replace("\xa0", " ")
    lines = (re.sub(r"[ \t\r\f\v]+", " ", line).strip() for line in text.splitlines())
    return "\n".join(line for line in lines if line)


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(value.split())
    return cleaned or None


def parse_datetime(value: object) -> datetime | None:
    """Accept datetime, unix seconds/millis, ISO 8601 (with Z), RFC 2822, 'YYYY-MM-DD HH:MM:SS'.

    Always returns a timezone-aware UTC datetime, or None if unparseable."""
    if value is None or value == "":
        return None
    dt: datetime
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, bool):
        return None
    elif isinstance(value, int | float):
        ts = float(value)
        if ts > 1e12:  # milliseconds
            ts /= 1000
        return datetime.fromtimestamp(ts, tz=UTC)
    elif isinstance(value, str):
        text = value.strip()
        if re.fullmatch(r"\d{9,13}", text):
            return parse_datetime(int(text))
        try:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            try:
                dt = parsedate_to_datetime(text)
            except (TypeError, ValueError, IndexError):
                return None
    else:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def normalize(raw: RawJob, now: datetime | None = None) -> Job:
    """Map a connector's RawJob to the canonical Job. No classification happens here."""
    now = now or datetime.now(tz=UTC)
    title = " ".join(raw.title.split())
    company = clean_text(raw.company)
    text = raw.description_text or html_to_text(raw.description_html)
    tags = sorted({t.strip() for t in raw.tags if t and t.strip()})
    return Job(
        id=dedup_key(title, company, raw.url),
        title=title,
        company=company,
        url=canonical_url(raw.url) if raw.url else raw.url,
        source=raw.source,
        source_ids={raw.source: raw.source_id},
        location_raw=clean_text(raw.location_raw),
        salary_raw=clean_text(raw.salary_raw),
        posted_at=parse_datetime(raw.posted_at),
        first_seen=now,
        last_seen=now,
        description_text=text,
        tags=tags,
    )
