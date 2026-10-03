"""Load config/profile.yaml and config/sources.yaml."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from jobbot.models import EmploymentType, RoleFamily, Seniority

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"


class DigestConfig(BaseModel):
    min_score: int = 50
    max_items: int = 150
    to: list[str] = Field(default_factory=list)


class Profile(BaseModel):
    eligible_regions: list[str] = Field(
        default_factory=lambda: ["WORLDWIDE", "EU", "EEA", "EUROPE"]
    )
    home_country: str | None = None
    languages: list[str] = Field(default_factory=lambda: ["en"])
    role_families: list[RoleFamily] = Field(default_factory=lambda: list(RoleFamily)[:-1])
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


def load_profile(path: Path | None = None) -> Profile:
    return Profile.model_validate(_read_yaml(path or CONFIG_DIR / "profile.yaml"))


def load_sources(path: Path | None = None) -> SourcesConfig:
    return SourcesConfig.model_validate(_read_yaml(path or CONFIG_DIR / "sources.yaml"))
