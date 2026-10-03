"""Regions-allowed parsing and eligibility. SPEC §8.3.

Output vocabulary: ISO-3166 alpha-2 codes plus the group tokens WORLDWIDE, EU, EEA,
EUROPE, AMERICAS, APAC and UNKNOWN. Groups expand to country codes in `expand`.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

EU: frozenset[str] = frozenset(
    [
        "AT",
        "BE",
        "BG",
        "HR",
        "CY",
        "CZ",
        "DK",
        "EE",
        "FI",
        "FR",
        "DE",
        "GR",
        "HU",
        "IE",
        "IT",
        "LV",
        "LT",
        "LU",
        "MT",
        "NL",
        "PL",
        "PT",
        "RO",
        "SK",
        "SI",
        "ES",
        "SE",
    ]
)
EEA: frozenset[str] = EU | {"IS", "LI", "NO"}
EUROPE: frozenset[str] = EEA | {"CH", "GB", "UA", "RS", "BA", "ME", "MK", "AL", "MD", "GE", "AM"}
AMERICAS: frozenset[str] = frozenset(["US", "CA", "MX", "BR", "AR", "CL", "CO", "PE", "UY"])
APAC: frozenset[str] = frozenset(["AU", "NZ", "JP", "SG", "IN", "KR", "PH", "ID", "MY", "VN", "TH"])

GROUPS: dict[str, frozenset[str]] = {
    "EU": EU,
    "EEA": EEA,
    "EUROPE": EUROPE,
    "AMERICAS": AMERICAS,
    "APAC": APAC,
}

# Country names and common variants → alpha-2. Lower-case keys; longest match wins.
COUNTRY_NAMES: dict[str, str] = {
    "austria": "AT",
    "österreich": "AT",
    "belgium": "BE",
    "belgië": "BE",
    "belgique": "BE",
    "bulgaria": "BG",
    "croatia": "HR",
    "cyprus": "CY",
    "czechia": "CZ",
    "czech republic": "CZ",
    "denmark": "DK",
    "estonia": "EE",
    "eesti": "EE",
    "finland": "FI",
    "suomi": "FI",
    "france": "FR",
    "germany": "DE",
    "deutschland": "DE",
    "greece": "GR",
    "hungary": "HU",
    "ireland": "IE",
    "italy": "IT",
    "italia": "IT",
    "latvia": "LV",
    "latvija": "LV",
    "lithuania": "LT",
    "lietuva": "LT",
    "luxembourg": "LU",
    "malta": "MT",
    "netherlands": "NL",
    "the netherlands": "NL",
    "holland": "NL",
    "nederland": "NL",
    "poland": "PL",
    "polska": "PL",
    "portugal": "PT",
    "romania": "RO",
    "slovakia": "SK",
    "slovenia": "SI",
    "spain": "ES",
    "españa": "ES",
    "sweden": "SE",
    "sverige": "SE",
    "iceland": "IS",
    "liechtenstein": "LI",
    "norway": "NO",
    "norge": "NO",
    "switzerland": "CH",
    "schweiz": "CH",
    "suisse": "CH",
    "united kingdom": "GB",
    "great britain": "GB",
    "britain": "GB",
    "england": "GB",
    "scotland": "GB",
    "wales": "GB",
    "uk": "GB",
    "ukraine": "UA",
    "serbia": "RS",
    "united states": "US",
    "united states of america": "US",
    "usa": "US",
    "u.s.": "US",
    "u.s.a.": "US",
    "us": "US",
    "america": "US",
    "canada": "CA",
    "mexico": "MX",
    "brazil": "BR",
    "argentina": "AR",
    "australia": "AU",
    "new zealand": "NZ",
    "india": "IN",
    "singapore": "SG",
    "japan": "JP",
    "philippines": "PH",
}

REGION_ALIASES: dict[str, frozenset[str]] = {
    "baltics": frozenset({"EE", "LV", "LT"}),
    "baltic states": frozenset({"EE", "LV", "LT"}),
    "baltic": frozenset({"EE", "LV", "LT"}),
    "nordics": frozenset({"DK", "SE", "NO", "FI", "IS"}),
    "nordic": frozenset({"DK", "SE", "NO", "FI", "IS"}),
    "scandinavia": frozenset({"DK", "SE", "NO"}),
    "dach": frozenset({"DE", "AT", "CH"}),
    "benelux": frozenset({"BE", "NL", "LU"}),
    "iberia": frozenset({"ES", "PT"}),
    "uk & ireland": frozenset({"GB", "IE"}),
    "uk and ireland": frozenset({"GB", "IE"}),
    "north america": frozenset({"US", "CA"}),
    "latam": AMERICAS - {"US", "CA"},
    "latin america": AMERICAS - {"US", "CA"},
}

WORLDWIDE = re.compile(
    r"\bworldwide\b|\banywhere\b|\bglobal(?:ly)?\b|\bany (?:location|country|time ?zone)\b"
    r"|\ball countries\b|\binternational\b|\bremote[- ]anywhere\b|\bno location restriction",
    re.IGNORECASE,
)
EU_GROUP = re.compile(
    r"\bEU\b|\bEuropean Union\b|\bEU[- ](?:only|based|wide|residents?|citizens?)\b", re.IGNORECASE
)
EEA_GROUP = re.compile(r"\bEEA\b|\bEuropean Economic Area\b|\bSchengen\b", re.IGNORECASE)
EUROPE_GROUP = re.compile(
    r"\bEurope(?:an)?\b|\bEMEA\b|\bCE[S]?T\b|\bEuropean time ?zones?\b|\bEU time ?zones?\b",
    re.IGNORECASE,
)
APAC_GROUP = re.compile(r"\bAPAC\b|\bAsia[- ]Pacific\b", re.IGNORECASE)
AMERICAS_GROUP = re.compile(r"\bAmericas\b|\bUS time ?zones?\b|\bEST\b|\bPST\b", re.IGNORECASE)
US_ONLY = re.compile(
    r"\bUS[- ](?:only|based|residents?|citizens?)\b"
    r"|\b(?:located|based|reside|residing|living) in the (?:US|USA|United States)\b"
    r"|\bauthori[sz]ed to work in the (?:US|USA|United States)\b"
    r"|\bUS work authori[sz]ation\b",
    re.IGNORECASE,
)
_MINUS_SIGNS = "-−–"  # noqa: RUF001  hyphen, true minus sign, en dash (all seen in offsets)
TZ_OFFSET = re.compile(rf"\b(?:UTC|GMT)\s*([+{_MINUS_SIGNS}])\s*(\d{{1,2}})\b", re.IGNORECASE)

# Phrases in the description body that mark a real restriction (not a company HQ mention).
RESTRICTION_CONTEXT = re.compile(
    r"(?:must (?:be )?(?:located|based|reside|live)|located|based|residents?|citizens?|"
    r"authori[sz]ed to work|eligible to work|work permit|only(?: open to)?|within|"
    r"candidates (?:in|from)|applicants (?:in|from)|time ?zones?|hiring in|open to candidates in)"
    r"[^.\n]{0,80}",
    re.IGNORECASE,
)

_NAME_PATTERN = re.compile(
    r"(?<![a-z])(?:"
    + "|".join(
        re.escape(name) for name in sorted({*COUNTRY_NAMES, *REGION_ALIASES}, key=len, reverse=True)
    )
    + r")(?![a-z])",
    re.IGNORECASE,
)
_ISO_PATTERN = re.compile(
    r"(?<![A-Za-z])(" + "|".join(sorted(EUROPE | AMERICAS | APAC)) + r")(?![A-Za-z])"
)


def _scan(text: str, *, allow_iso: bool) -> tuple[set[str], set[str]]:
    """Return (regions, tags) found in a piece of text."""
    regions: set[str] = set()
    tags: set[str] = set()
    if not text:
        return regions, tags
    if WORLDWIDE.search(text):
        regions.add("WORLDWIDE")
    if US_ONLY.search(text):
        regions.add("US")
    if EEA_GROUP.search(text):
        regions.add("EEA")
    if EU_GROUP.search(text):
        regions.add("EU")
    if EUROPE_GROUP.search(text):
        regions.add("EUROPE")
    if APAC_GROUP.search(text):
        regions.add("APAC")
    if AMERICAS_GROUP.search(text):
        regions.add("AMERICAS")
    for match in _NAME_PATTERN.finditer(text):
        key = match.group(0).lower()
        if key in REGION_ALIASES:
            regions.update(REGION_ALIASES[key])
        elif key in COUNTRY_NAMES:
            regions.add(COUNTRY_NAMES[key])
    if allow_iso:
        for match in _ISO_PATTERN.finditer(text):
            regions.add(match.group(1))
    offsets = [
        int(m.group(2)) * (-1 if m.group(1) in _MINUS_SIGNS else 1)
        for m in TZ_OFFSET.finditer(text)
    ]
    if offsets and not regions:
        if all(-2 <= o <= 4 for o in offsets):
            regions.add("EUROPE")
            tags.add("timezone_inferred")
        elif all(-10 <= o <= -3 for o in offsets):
            regions.add("AMERICAS")
            tags.add("timezone_inferred")
    return regions, tags


def parse_regions(
    *, location_raw: str | None, title: str, description_text: str
) -> tuple[list[str], list[str]]:
    """Infer where a remote job may be worked from. Location field first, then title,
    then restriction phrases in the first 1500 characters of the description."""
    regions, tags = _scan(location_raw or "", allow_iso=True)
    if not regions:
        regions, tags = _scan(title, allow_iso=False)
    if not regions:
        snippets = " ".join(
            m.group(0) for m in RESTRICTION_CONTEXT.finditer(description_text[:1500])
        )
        regions, tags = _scan(snippets, allow_iso=False)
        if regions:
            tags.add("region_from_description")
    if not regions:
        return ["UNKNOWN"], sorted(tags)
    return sorted(regions), sorted(tags)


def expand(regions: Iterable[str]) -> set[str]:
    """Expand group tokens to country codes; WORLDWIDE and UNKNOWN pass through."""
    out: set[str] = set()
    for region in regions:
        token = region.upper()
        if token in GROUPS:
            out.update(GROUPS[token])
            out.add(token)
        else:
            out.add(token)
    return out


def is_eligible(regions_allowed: Iterable[str], eligible_regions: Iterable[str]) -> bool:
    """True if the job allows at least one place the candidate may work from.
    UNKNOWN never matches. A job open WORLDWIDE matches any profile; WORLDWIDE in the
    profile only means such jobs are wanted, not that the candidate can work anywhere."""
    allowed = expand(regions_allowed)
    eligible = expand(eligible_regions)
    allowed.discard("UNKNOWN")
    if not allowed:
        return False
    if "WORLDWIDE" in allowed:
        return True
    eligible.discard("WORLDWIDE")
    return bool(allowed & eligible)
