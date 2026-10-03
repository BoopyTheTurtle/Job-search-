from typing import Any

import pytest

from jobbot.enrich.regions import EU, expand, is_eligible, parse_regions
from tests.enrich.conftest import case_ids, load_cases

CASES = load_cases("regions")
PROFILE_REGIONS = ["WORLDWIDE", "EU", "EEA", "EUROPE", "LV"]


@pytest.mark.parametrize("case", CASES, ids=case_ids(CASES))
def test_regions_golden(case: dict[str, Any]) -> None:
    regions, tags = parse_regions(
        location_raw=case.get("location"),
        title=case["title"],
        description_text=case.get("description") or "",
    )
    assert regions == case["expected"]
    for tag in case.get("tags", []):
        assert tag in tags
    assert is_eligible(regions, PROFILE_REGIONS) is case["eligible"]


def test_expand_groups() -> None:
    assert "LV" in expand(["EU"])
    assert "NO" in expand(["EEA"])
    assert "NO" not in expand(["EU"])
    assert "CH" in expand(["EUROPE"])
    assert expand(["EUROPE"]) >= EU


def test_eligibility_edge_cases() -> None:
    assert is_eligible(["UNKNOWN"], PROFILE_REGIONS) is False
    assert is_eligible([], PROFILE_REGIONS) is False
    assert is_eligible(["US"], ["WORLDWIDE"]) is False
    assert is_eligible(["WORLDWIDE"], ["LV"]) is True
    assert is_eligible(["LV"], ["EU"]) is True
    assert is_eligible(["EU"], ["LV"]) is True
    assert is_eligible(["US", "CA"], ["EU"]) is False
