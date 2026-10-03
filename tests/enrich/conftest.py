from pathlib import Path
from typing import Any

import pytest
import yaml

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "classification"


def load_cases(name: str) -> list[dict[str, Any]]:
    with (FIXTURES / f"{name}.yaml").open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    assert isinstance(data, list)
    return data


def case_ids(cases: list[dict[str, Any]]) -> list[str]:
    return [str(c.get("name") or c.get("title") or i) for i, c in enumerate(cases)]


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES
