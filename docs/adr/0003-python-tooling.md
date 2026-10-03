# ADR-0003: Python 3.11+, uv, ruff, mypy, pytest, pydantic, httpx

Date: 2026-10-03 · Status: Accepted

## Context
The owner chose Python. The project is I/O-bound API fetching, text classification and
templating; it needs strong typing at the connector boundary and fast CI.

## Decision
- Python ≥ 3.11, `src/` layout, package `jobbot`.
- `uv` for dependency management and lockfile; `pyproject.toml` is the single config file.
- `ruff` (lint + format), `mypy --strict` on `src/`, `pytest` with `respx` for HTTP fixtures.
- `pydantic` v2 models for `RawJob`, `Job` and config; `httpx` client; `typer` CLI;
  `PyYAML` for config; `Jinja2` for digest templates (Phase 1); `lingua-language-detector`
  for language detection (Phase 1).
- Conventional Commits for commit messages; pre-commit runs ruff and mypy locally.

## Consequences
- Contributors need `uv` installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`).
- Strict typing adds friction at connector boundaries but catches field-mapping bugs,
  which are the most common failure in this kind of project.
