"""Send the digest through the Resend HTTP API. ADR-0002.

Secrets: RESEND_API_KEY, DIGEST_FROM ("Name <addr@verified-domain>"), DIGEST_TO
(comma-separated). DIGEST_TO falls back to profile.digest.to.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import httpx

from jobbot import USER_AGENT

RESEND_URL = "https://api.resend.com/emails"


class ResendError(RuntimeError):
    """Resend rejected the request or was unreachable."""


@dataclass(frozen=True)
class EmailSettings:
    api_key: str
    sender: str
    recipients: list[str]

    @classmethod
    def from_env(cls, fallback_to: list[str] | None = None) -> EmailSettings | None:
        api_key = os.environ.get("RESEND_API_KEY", "").strip()
        sender = os.environ.get("DIGEST_FROM", "").strip()
        to_raw = os.environ.get("DIGEST_TO", "").strip()
        recipients = [t.strip() for t in to_raw.split(",") if t.strip()] or list(fallback_to or [])
        if not (api_key and sender and recipients):
            return None
        return cls(api_key=api_key, sender=sender, recipients=recipients)


def send_digest(
    settings: EmailSettings,
    *,
    subject: str,
    html: str,
    text: str,
    client: httpx.Client | None = None,
) -> str:
    """POST to Resend; returns the message id."""
    payload = {
        "from": settings.sender,
        "to": settings.recipients,
        "subject": subject,
        "html": html,
        "text": text,
    }
    headers = {"Authorization": f"Bearer {settings.api_key}", "User-Agent": USER_AGENT}
    own_client = client is None
    client = client or httpx.Client(timeout=30.0)
    try:
        response = client.post(RESEND_URL, json=payload, headers=headers)
    except httpx.TransportError as exc:
        raise ResendError(f"Resend unreachable: {exc}") from exc
    finally:
        if own_client:
            client.close()
    if response.status_code >= 400:
        raise ResendError(f"Resend returned {response.status_code}: {response.text[:300]}")
    data = response.json()
    message_id = data.get("id") if isinstance(data, dict) else None
    if not isinstance(message_id, str):
        raise ResendError(f"Resend response had no id: {response.text[:300]}")
    return message_id
