"""Load config/searches/*.yaml and config/sources.yaml."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from jobbot.models import EmploymentType, RoleFamily, Seniority

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"
SEARCHES_DIR = CONFIG_DIR / "searches"
_ALL_FAMILIES: list[RoleFamily] = [f for f in RoleFamily if f is not RoleFamily.OTHER]


class DigestConfig(BaseModel):
    min_score: int = 50
    max_items: int = 150
    to: list[str] = Field(default_factory=list)


class Profile(BaseModel):
    eligible_regions: list[str] = Field(
        default_factory=lambda: ["WORLDWIDE", "EU", "EEA", "EUROPE"]
    )
    """Where a remote job must allow working from."""
    home_country: str | None = None
    hybrid_regions: list[str] | None = None
    """Where hybrid jobs count. None means the home country only."""
    onsite_regions: list[str] = Field(default_factory=list)
    """Where on-site jobs count. Empty means on-site jobs are dropped. When set, postings
    whose work arrangement is unknown are treated as on-site."""
    preferred_countries: list[str] = Field(default_factory=list)
    """Hybrid or on-site jobs in these countries score as high as remote ones."""
    languages: list[str] = Field(default_factory=lambda: ["en"])
    role_families: list[RoleFamily] = Field(default_factory=lambda: _ALL_FAMILIES.copy())
    seniority: list[Seniority] = Field(
        default_factory=lambda: [Seniority.INTERN, Seniority.JUNIOR, Seniority.MID]
    )
    employment_types: list[EmploymentType] = Field(
        default_factory=lambda: [
            EmploymentType.FULL_TIME,
            EmploymentType.PART_TIME,
            EmploymentType.CONTRACT,
            EmploymentType.FREELANCE,
            EmploymentType.INTERNSHIP,
        ]
    )
    keyword_boosts: list[str] = Field(default_factory=list)
    exclude_companies: list[str] = Field(default_factory=list)
    exclude_title_patterns: list[str] = Field(default_factory=list)
    digest: DigestConfig = Field(default_factory=DigestConfig)

    @property
    def all_eligible_regions(self) -> list[str]:
        regions = list(self.eligible_regions)
        if self.home_country and self.home_country.upper() not in regions:
            regions.append(self.home_country.upper())
        return regions

    @property
    def effective_hybrid_regions(self) -> list[str]:
        if self.hybrid_regions is not None:
            return [r.upper() for r in self.hybrid_regions]
        return [self.home_country.upper()] if self.home_country else []


class Search(Profile):
    """One parallel search: a profile, a digest of its own, and per-source query overrides.
    Every search scores the same crawled pool; `queries` only adds connector runs."""

    name: str
    title: str = ""
    queries: dict[str, dict[str, Any]] = Field(default_factory=dict)
    """source name -> params merged over that source's `params` in sources.yaml."""

    @property
    def label(self) -> str:
        return self.title or self.name


class SourceConfig(BaseModel):
    enabled: bool = True
    tier: str = "A"
    terms: str
    rate_limit_rps: float = 1.0
    env: list[str] = Field(default_factory=list)
    params: dict[str, Any] = Field(default_factory=dict)


class SourcesConfig(BaseModel):
    sources: dict[str, SourceConfig] = Field(default_factory=dict)


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a mapping at the top level")
    return data


def load_search(path: Path) -> Search:
    data = _read_yaml(path)
    data.setdefault("name", path.stem)
    return Search.model_validate(data)


def load_searches(directory: Path | None = None, names: list[str] | None = None) -> list[Search]:
    """All searches in `directory` (default config/searches), sorted by name. `names`
    selects a subset and fails on an unknown name."""
    directory = directory or SEARCHES_DIR
    searches = sorted((load_search(p) for p in directory.glob("*.yaml")), key=lambda s: s.name)
    if names:
        known = {s.name: s for s in searches}
        unknown = [n for n in names if n not in known]
        if unknown:
            raise ValueError(f"unknown search(es): {', '.join(unknown)}; have {sorted(known)}")
        searches = [known[n] for n in names]
    return searches


def load_sources(path: Path | None = None) -> SourcesConfig:
    return SourcesConfig.model_validate(_read_yaml(path or CONFIG_DIR / "sources.yaml"))
