from typing import Any

import pytest

from jobbot.enrich.remote import classify_remote
from jobbot.models import RemoteType
from tests.enrich.conftest import case_ids, load_cases

CASES = load_cases("remote")


@pytest.mark.parametrize("case", CASES, ids=case_ids(CASES))
def test_remote_golden(case: dict[str, Any]) -> None:
    result = classify_remote(
        title=case["title"],
        location_raw=case.get("location"),
        description_text=case.get("description") or "",
        remote_hint=case.get("remote_hint"),
    )
    assert result == RemoteType(case["expected"])
