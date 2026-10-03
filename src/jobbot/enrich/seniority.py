"""Seniority and employment type classification. SPEC §8.5, §8.6."""

from __future__ import annotations

import re

from jobbot.models import EmploymentType, Seniority

_F = re.IGNORECASE

INTERN = re.compile(
    r"\bintern(?:ship)?\b|\bwerkstudent\w*|\bpraktik(?:um|ant\w*)|\bstagiaire\b|\balternance\b"
    r"|\bbecario\b|\bprácticas\b|\bpraktikant\w*|\bpraktise\b|\bworking student\b",
    _F,
)
JUNIOR = re.compile(
    r"\bjunior\b|\bjr\.?\b|\bgraduates?\b|\bentry[- ]level\b|\btrainee\b|\bearly[- ]career\b"
    r"|\bapprentice\w*|\bdébutant\w*|\bjunior\w*|\bnew grads?\b"
    r"|\bassociate (?:software|developer|engineer)",
    _F,
)
LEAD = re.compile(
    r"\blead\b|\bhead of\b|\bprincipal\b|\bstaff\b|\bdirector\b|\bvp\b|\bvice president\b"
    r"|\bchief\b|\bcto\b|\barchitect\b|\bengineering manager\b|\bteam lead\w*|\btech lead\b",
    _F,
)
SENIOR = re.compile(r"\bsenior\b|\bsr\.?\b|\bsenior\w*\b|\bexperienced\b|\bexpert\b", _F)
YEARS = re.compile(r"\b(\d{1,2})\s*\+?\s*(?:years?|yrs?|jahre|ans|años|gad\w*)\b", _F)


def classify_seniority(title: str, description_text: str) -> Seniority:
    if INTERN.search(title):
        return Seniority.INTERN
    if JUNIOR.search(title):
        return Seniority.JUNIOR
    if LEAD.search(title):
        return Seniority.LEAD
    if SENIOR.search(title):
        return Seniority.SENIOR
    body = description_text[:4000]
    years = [int(m.group(1)) for m in YEARS.finditer(body)]
    if years:
        required = max(y for y in years if y <= 20) if any(y <= 20 for y in years) else 0
        if required >= 5:
            return Seniority.SENIOR
        if required >= 2:
            return Seniority.MID
        if required >= 0 and (JUNIOR.search(body) or INTERN.search(body)):
            return Seniority.JUNIOR
        return Seniority.MID
    if INTERN.search(body[:600]):
        return Seniority.INTERN
    if JUNIOR.search(body[:600]):
        return Seniority.JUNIOR
    return Seniority.MID


_RAW_MAP: list[tuple[re.Pattern[str], EmploymentType]] = [
    (re.compile(r"intern", _F), EmploymentType.INTERNSHIP),
    (
        re.compile(r"freelanc|self[- ]employed|independent contractor", _F),
        EmploymentType.FREELANCE,
    ),
    (
        re.compile(r"contract|contractor|b2b|temporary|fixed[- ]term|consultant|cdd|befristet", _F),
        EmploymentType.CONTRACT,
    ),
    (
        re.compile(r"part[- _]?time|teilzeit|deeltijd|temps partiel|media jornada", _F),
        EmploymentType.PART_TIME,
    ),
    (
        re.compile(
            r"full[- _]?time|vollzeit|voltijd|temps plein|jornada completa|permanent|cdi"
            r"|unbefristet",
            _F,
        ),
        EmploymentType.FULL_TIME,
    ),
]

FREELANCE_TEXT = re.compile(r"\bfreelance\w*\b|\bself[- ]employed\b|\bindependent contractor\b", _F)
CONTRACT_TEXT = re.compile(
    r"\bcontract(?:or|ing)?\b(?! of employment)|\bb2b\b|\bfixed[- ]term\b|\btemporary\b"
    r"|\b\d+[- ]month contract\b",
    _F,
)
PART_TIME_TEXT = re.compile(
    r"\bpart[- ]time\b|\bteilzeit\b|\bdeeltijd\b|\btemps partiel\b|\bmedia jornada\b"
    r"|\bnepilna slodze\b",
    _F,
)
FULL_TIME_TEXT = re.compile(
    r"\bfull[- ]time\b|\bvollzeit\b|\bvoltijd\b|\btemps plein\b|\bjornada completa\b"
    r"|\bpilna slodze\b|\bpermanent\b",
    _F,
)


def classify_employment(
    employment_type_raw: str | None, title: str, description_text: str
) -> EmploymentType:
    if employment_type_raw:
        for pattern, value in _RAW_MAP:
            if pattern.search(employment_type_raw):
                return value
    if INTERN.search(title):
        return EmploymentType.INTERNSHIP
    if FREELANCE_TEXT.search(title):
        return EmploymentType.FREELANCE
    if CONTRACT_TEXT.search(title):
        return EmploymentType.CONTRACT
    if PART_TIME_TEXT.search(title):
        return EmploymentType.PART_TIME
    body = description_text[:3000]
    if FREELANCE_TEXT.search(body):
        return EmploymentType.FREELANCE
    if PART_TIME_TEXT.search(body) and not FULL_TIME_TEXT.search(body):
        return EmploymentType.PART_TIME
    if CONTRACT_TEXT.search(body) and not FULL_TIME_TEXT.search(body):
        return EmploymentType.CONTRACT
    if FULL_TIME_TEXT.search(body):
        return EmploymentType.FULL_TIME
    return EmploymentType.UNKNOWN
