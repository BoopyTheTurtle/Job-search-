from pathlib import Path

import pytest

from jobbot.config import load_search, load_searches, load_sources
from jobbot.models import RoleFamily


def test_committed_searches_load() -> None:
    searches = {s.name: s for s in load_searches()}
    assert set(searches) == {"it", "impact-finance"}
    for search in searches.values():
        assert search.digest.to == [], "no addresses in committed searches; use DIGEST_TO"
        assert search.home_country == "LV"


def test_it_search_keeps_the_original_profile() -> None:
    it = load_searches(names=["it"])[0]
    assert it.title == "IT"
    assert "EU" in it.eligible_regions
    assert "EUROPE" not in it.eligible_regions, "EUROPE would let UK-only jobs through"
    assert it.languages == ["en", "fr", "lv", "es"]
    assert RoleFamily.SOFTWARE_DEV in it.role_families
    assert it.effective_hybrid_regions == ["LV"]
    assert it.onsite_regions == []
    assert it.digest.min_score == 50
    assert it.queries["adzuna"] == {"what": "remote", "category": "it-jobs"}


def test_impact_finance_search() -> None:
    impact = load_searches(names=["impact-finance"])[0]
    assert impact.languages == ["en", "fr"]
    assert set(impact.role_families) == {
        RoleFamily.INTL_DEVELOPMENT,
        RoleFamily.FINANCE_INVESTMENT,
        RoleFamily.PRIVATE_EQUITY,
        RoleFamily.PROJECT_ADMIN,
    }
    assert impact.onsite_regions == ["EU", "CH"]
    assert "GB" not in impact.preferred_countries
    assert "EUROPE" not in impact.eligible_regions, "EUROPE would let UK-only jobs through"
    assert set(impact.queries) == {"adzuna", "francetravail"}
    assert "gb" not in impact.queries["adzuna"]["countries"]
    assert impact.queries["adzuna"]["category"] is None
    assert (
        impact.queries["adzuna"]["what_by_country"]["be"]
        == (impact.queries["adzuna"]["what_by_country"]["fr"])
    )
    assert impact.queries["francetravail"]["domain"] is None


def test_search_name_defaults_to_file_stem(tmp_path: Path) -> None:
    p = tmp_path / "mine.yaml"
    p.write_text("home_country: de\n", encoding="utf-8")
    search = load_search(p)
    assert search.name == "mine"
    assert search.label == "mine"
    assert "DE" in search.all_eligible_regions


def test_unknown_search_name_fails(tmp_path: Path) -> None:
    (tmp_path / "a.yaml").write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unknown search"):
        load_searches(tmp_path, names=["b"])


def test_sources_config_requires_terms() -> None:
    cfg = load_sources()
    assert cfg.sources
    for name, entry in cfg.sources.items():
        assert entry.terms.startswith("http"), f"{name} is missing a terms URL (ADR-0001)"


def test_search_queries_name_configured_sources() -> None:
    sources = load_sources().sources
    for search in load_searches():
        for name in search.queries:
            assert name in sources, f"{search.name} queries unknown source {name}"
