"""Shared HTTP client with project User-Agent, timeouts and simple retry."""

from __future__ import annotations

import time
from typing import Any

import httpx

from jobbot import USER_AGENT

DEFAULT_TIMEOUT = 30.0
RETRY_STATUSES = {429, 500, 502, 503, 504}


class SourceError(RuntimeError):
    """A connector could not complete its fetch. Recorded per source, never fatal to a run."""


def make_client() -> httpx.Client:
    return httpx.Client(
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json, application/xml;q=0.9, */*;q=0.8",
        },
        timeout=DEFAULT_TIMEOUT,
        follow_redirects=True,
    )


def get_json(
    client: httpx.Client, url: str, *, params: dict[str, Any] | None = None, attempts: int = 3
) -> Any:
    """GET with exponential backoff on transient errors. Returns parsed JSON."""
    delay = 1.0
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            response = client.get(url, params=params)
            if response.status_code in RETRY_STATUSES and attempt < attempts:
                time.sleep(delay)
                delay *= 2
                continue
            response.raise_for_status()
            return response.json()
        except (httpx.TransportError, httpx.HTTPStatusError, ValueError) as exc:
            last_error = exc
            if attempt < attempts:
                time.sleep(delay)
                delay *= 2
    raise SourceError(f"GET {url} failed after {attempts} attempts: {last_error}") from last_error
