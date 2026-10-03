from typing import Any

import pytest

from jobbot.enrich.seniority import classify_employment, classify_seniority
from jobbot.models import EmploymentType, Seniority
from tests.enrich.conftest import case_ids, load_cases

CASES = load_cases("seniority")
SENIORITY_CASES = [c for c in CASES if "seniority" in c]
EMPLOYMENT_CASES = [c for c in CASES if "employment" in c]


@pytest.mark.parametrize("case", SENIORITY_CASES, ids=case_ids(SENIORITY_CASES))
def test_seniority_golden(case: dict[str, Any]) -> None:
    assert classify_seniority(case["title"], case.get("description") or "") == Seniority(
        case["seniority"]
    )


@pytest.mark.parametrize("case", EMPLOYMENT_CASES, ids=case_ids(EMPLOYMENT_CASES))
def test_employment_golden(case: dict[str, Any]) -> None:
    result = classify_employment(
        case.get("employment_type_raw"), case["title"], case.get("description") or ""
    )
    assert result == EmploymentType(case["employment"])
