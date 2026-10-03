from typing import Any

import pytest

from jobbot.enrich.roles import classify_role, load_taxonomy
from jobbot.models import RoleFamily
from tests.enrich.conftest import case_ids, load_cases

CASES = load_cases("roles")


def test_taxonomy_covers_every_family_except_other() -> None:
    taxonomy = load_taxonomy()
    for family in RoleFamily:
        if family is RoleFamily.OTHER:
            continue
        assert taxonomy.title_patterns[family], f"{family} has no title patterns"


@pytest.mark.parametrize("case", CASES, ids=case_ids(CASES))
def test_roles_golden(case: dict[str, Any]) -> None:
    assert classify_role(case["title"], case.get("description") or "") == RoleFamily(
        case["expected"]
    )
