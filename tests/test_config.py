from pathlib import Path

from jobbot.config import CONFIG_DIR, load_profile, load_sources
from jobbot.models import RoleFamily


def test_example_profile_loads() -> None:
    profile = load_profile(CONFIG_DIR / "profile.example.yaml")
    assert "EU" in profile.eligible_regions
    assert RoleFamily.SOFTWARE_DEV in profile.role_families
    assert profile.digest.min_score == 50


def test_home_country_added_to_eligible_regions(tmp_path: Path) -> None:
    p = tmp_path / "profile.yaml"
    p.write_text("home_country: de\n", encoding="utf-8")
    profile = load_profile(p)
    assert "DE" in profile.all_eligible_regions


def test_sources_config_requires_terms() -> None:
    cfg = load_sources()
    assert cfg.sources
    for name, entry in cfg.sources.items():
        assert entry.terms.startswith("http"), f"{name} is missing a terms URL (ADR-0001)"
