"""Remote type classification. SPEC §8.2.

Precedence: structured hint from the source → negative phrases → hybrid → remote → on-site.
Title and location are trusted more than the description body.
"""

from __future__ import annotations

import re

from jobbot.models import RemoteType

_FLAGS = re.IGNORECASE

NEGATIVE = re.compile(
    r"\b(?:no|not|non)[- ]remote\b"
    r"|\bremote(?: work| working)?(?: is)? not (?:possible|available|an option|offered)\b"
    r"|\bnot (?:a )?remote(?: position| role| job)?\b"
    r"|\bon[- ]?site only\b"
    r"|\bin[- ]office only\b"
    r"|\bkein(?:e)? home[- ]?office\b"
    r"|\bno (?:home[- ]?office|wfh|teletrabajo|télétravail)\b"
    r"|\bsans télétravail\b|\bpas de télétravail\b"  # fr
    r"|\bsin teletrabajo\b|\bno remoto\b"  # es
    r"|\binte(?:t)? distans\b|\bej distans\b"  # sv
    r"|\bbez attālinātā\b|\btikai klātienē\b",  # lv
    _FLAGS,
)
HYBRID = re.compile(
    r"\bhybrid(?:e|o)?\b"
    r"|\b\d\s*(?:to|-|–)?\s*\d?\s*(?:days?|tage|jours|días)\b[^.\n]{0,20}"  # noqa: RUF001
    r"\b(?:office|büro|bureau|oficina|on[- ]?site)\b"
    r"|\bpartial(?:ly)? remote\b"
    r"|\bremote[- ]friendly\b"
    r"|\bflexible remote\b",
    _FLAGS,
)
REMOTE = re.compile(
    r"\bremote\b"
    r"|\bfully[- ]remote\b"
    r"|\b100\s?% remote\b"
    r"|\bwork from anywhere\b"
    r"|\bwork from home\b"
    r"|\bwfh\b"
    r"|\bhome[- ]?office\b"
    r"|\bmobiles arbeiten\b"  # de
    r"|\bremote[- ]arbeit\b"  # de
    r"|\btélétravail\b|\btele?travail\b|\bfull remote\b|\ben remote\b"  # fr
    r"|\bteletrabajo\b|\b(?:trabajo|empleo|100\s?%) (?:en )?remoto\b|\bremoto\b"  # es
    r"|\battālināt[sai]\b|\battālināti\b|\battālinātais darbs\b"  # lv
    r"|\bdistansarbete\b|\bpå distans\b|\bhemifrån\b|\bdistansjobb\b"  # sv
    r"|\bfjernarbeid\b|\bhjemmekontor\b"  # no
    r"|\betätyö\b|\betänä\b"  # fi
    r"|\bthuiswerken\b|\bvanuit huis\b"  # nl
    r"|\bpraca zdalna\b|\bzdalnie\b"  # pl
    r"|\blavoro da remoto\b|\bda remoto\b|\bsmart working\b"  # it
    r"|\bdistributed(?: team| company)\b"
    r"|\bremote[- ](?:first|only)\b",
    _FLAGS,
)
ONSITE = re.compile(
    r"\bon[- ]?site\b|\bin[- ]office\b|\bvor ort\b|\bpräsenz\b|\bpresencial\b|\bsur site\b"
    r"|\bklātienē\b|\bpå plats\b|\bpå kontoret\b|\bop kantoor\b|\bin sede\b",
    _FLAGS,
)


def classify_remote(
    *,
    title: str,
    location_raw: str | None,
    description_text: str,
    remote_hint: bool | None,
) -> RemoteType:
    head = " | ".join(part for part in (title, location_raw) if part)
    body = description_text[:3000]

    if remote_hint is True:
        # A remote-only board can still list hybrid roles; trust an explicit hybrid in the header.
        return RemoteType.HYBRID if HYBRID.search(head) else RemoteType.REMOTE
    if remote_hint is False:
        return RemoteType.HYBRID if HYBRID.search(head) else RemoteType.ONSITE

    if NEGATIVE.search(head) or NEGATIVE.search(body):
        return RemoteType.HYBRID if HYBRID.search(head) else RemoteType.ONSITE
    if HYBRID.search(head):
        return RemoteType.HYBRID
    if REMOTE.search(head):
        return RemoteType.REMOTE
    if ONSITE.search(head):
        return RemoteType.ONSITE
    if HYBRID.search(body):
        return RemoteType.HYBRID
    if REMOTE.search(body):
        return RemoteType.REMOTE
    return RemoteType.UNKNOWN
