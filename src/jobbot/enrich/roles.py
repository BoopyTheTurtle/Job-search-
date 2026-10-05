"""Role-family classification from config/taxonomy.yaml. SPEC §8.4."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from jobbot.config import CONFIG_DIR
from jobbot.models import RoleFamily

TITLE_WEIGHT = 3
DESCRIPTION_CAP = 5
MIN_BODY_ONLY_HITS = 3
_BODY_CHARS = 4000


def _compile(patterns: list[str]) -> list[re.Pattern[str]]:
    # Token boundaries that also work for "c++", ".net", "c#".
    return [re.compile(rf"(?<![a-z0-9]){p}(?![a-z0-9])", re.IGNORECASE) for p in patterns]


@dataclass(frozen=True)
class Taxonomy:
    title_patterns: dict[RoleFamily, list[re.Pattern[str]]]
    description_patterns: dict[RoleFamily, list[re.Pattern[str]]]
    exclude_title: list[re.Pattern[str]]
    tie_break: tuple[RoleFamily, ...] = ()
    """Families that may settle a full tie among themselves: the earliest listed wins."""


def _as_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    raise ValueError(f"expected a list of patterns, got {type(value).__name__}")


@lru_cache(maxsize=2)
def load_taxonomy(path: Path | None = None) -> Taxonomy:
    path = path or CONFIG_DIR / "taxonomy.yaml"
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must be a mapping")
    families = data.get("families") or {}
    if not isinstance(families, dict):
        raise ValueError("taxonomy.families must be a mapping")
    title: dict[RoleFamily, list[re.Pattern[str]]] = {}
    description: dict[RoleFamily, list[re.Pattern[str]]] = {}
    for name, spec in families.items():
        family = RoleFamily(str(name))
        spec = spec or {}
        if not isinstance(spec, dict):
            raise ValueError(f"taxonomy.families.{name} must be a mapping")
        title[family] = _compile(_as_list(spec.get("title")))
        description[family] = _compile(_as_list(spec.get("description")))
    exclude = data.get("exclude") or {}
    if not isinstance(exclude, dict):
        raise ValueError("taxonomy.exclude must be a mapping")
    tie_break = tuple(RoleFamily(name) for name in _as_list(data.get("tie_break")))
    return Taxonomy(title, description, _compile(_as_list(exclude.get("title"))), tie_break)


def _count(patterns: list[re.Pattern[str]], text: str) -> int:
    return sum(1 for p in patterns if p.search(text))


def classify_role(
    title: str, description_text: str, taxonomy: Taxonomy | None = None
) -> RoleFamily:
    taxonomy = taxonomy or load_taxonomy()
    if any(p.search(title) for p in taxonomy.exclude_title):
        return RoleFamily.OTHER
    body = description_text[:_BODY_CHARS]
    scores: dict[RoleFamily, tuple[int, int]] = {}
    for family in taxonomy.title_patterns:
        title_hits = _count(taxonomy.title_patterns[family], title)
        body_hits = min(
            _count(taxonomy.description_patterns.get(family, []), body), DESCRIPTION_CAP
        )
        scores[family] = (title_hits * TITLE_WEIGHT + body_hits, title_hits)
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    if not ranked or ranked[0][1][0] == 0:
        return RoleFamily.OTHER
    best, (best_score, best_title_hits) = ranked[0]
    # A title that says nothing IT-related needs solid evidence in the body: a web agency's
    # "Office Assistant" posting mentions WordPress and HTML without being a dev role.
    if best_title_hits == 0 and best_score < MIN_BODY_ONLY_HITS:
        return RoleFamily.OTHER
    # Tie on score: the family with more title hits wins. A full tie is ambiguous → other,
    # unless every tied family is in `tie_break`, which then names the winner.
    tied = [family for family, s in ranked if s == (best_score, best_title_hits)]
    if len(tied) > 1:
        order = taxonomy.tie_break
        if all(family in order for family in tied):
            return min(tied, key=order.index)
        return RoleFamily.OTHER
    return best
