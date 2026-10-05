# CLAUDE.md

Project: personal weekly job-search bot. Read `docs/SPEC.md` first, then `docs/ROADMAP.md`.

## Conventions
- Python ≥ 3.11, `src/jobbot` package, managed with `uv`. Run tools via `uv run …`.
- Checks before every push: `uv run ruff check . && uv run ruff format --check . && uv run mypy src && uv run pytest`.
- Conventional Commits. One issue per PR, branch names `feat/…`, `fix/…`, `docs/…`, `chore/…`.
- Never add a source whose terms forbid automated access (see ADR-0001). Record the terms
  URL in `config/sources.yaml` for every source.
- Every connector needs a recorded fixture under `tests/fixtures/<source>/` and a test.
- No network calls in tests; use `respx`.
- Secrets only via environment variables; never commit `.env`. `config/searches/*.yaml` hold
  preferences only (no addresses or keys) and are committed; the recipient comes from `DIGEST_TO`.
- Do not commit to `main` directly. Do not commit to the `data` branch by hand; the workflow owns it.
- Keep the crawler core (`sources`, `normalize`, `enrich`, `dedupe`, `store`) free of
  user-profile logic; profile logic lives in `filter` and `digest`.
- Each search (`config/searches/<name>.yaml`) gets its own digest and email over one shared
  crawl (ADR-0004). Source query terms go in a search's `queries`, not in `sources.yaml`.
