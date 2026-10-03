# Contributing

This is a two-person project (owner plus Claude). The rules below keep history clean and
make every change reviewable.

## Workflow
1. **Issues first.** Every piece of work has an issue in the backlog (see `docs/ROADMAP.md`).
   Labels: `phase-0` … `phase-4`, `source`, `enrich`, `infra`, `docs`, `bug`, `good first issue`.
2. **Branch per issue** from `main`: `feat/<short-name>`, `fix/<short-name>`,
   `docs/<short-name>`, `chore/<short-name>`. Short-lived; delete after merge.
3. **Small PRs.** One issue, ideally under 400 lines of diff. Fill in the PR template and
   link the issue with `Closes #N`.
4. **CI must be green** (the `Checks` job: `ruff`, `mypy`, `pytest`). No merging with red checks.
5. **Review.** The owner reviews and merges (squash merge). Claude never merges its own
   PRs unless told to.
6. **Conventional Commits:** `feat(sources): add arbeitnow connector`, `fix(enrich): …`,
   `docs: …`, `chore(ci): …`, `test: …`.

## Branch protection (owner action, once)
Settings → Branches → Add rule for `main`: require a pull request before merging,
require status checks (`Checks`), require branches to be up to date, block force pushes.

## Local setup
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # once
uv sync --all-extras
uv run pre-commit install
cp .env.example .env            # add API keys as you get them
cp config/profile.example.yaml config/profile.yaml
uv run jobbot sources
uv run jobbot crawl --source remotive --limit 5 --dry-run
```

## Checks
```bash
uv run ruff check . && uv run ruff format --check .
uv run mypy src
uv run pytest
```

## Adding a source
1. Read `docs/inventory/apis-and-feeds.md` and confirm the terms allow it. Record the
   terms URL in `config/sources.yaml`.
2. Create `src/jobbot/sources/<name>.py` implementing `Source`; register it.
3. Save a trimmed real response as `tests/fixtures/<name>/sample.json` (remove personal data).
4. Add `tests/sources/test_<name>.py` asserting the `RawJob` mapping.
5. Add the entry to `config/sources.yaml` with `enabled: false` until a live smoke run passes.

## The `data` branch
`weekly-crawl` clones the orphan `data` branch into `./data`, runs `jobbot run` against it
and pushes the result back as `github-actions[bot]`. Never commit to it by hand. To inspect
history locally: `git fetch origin data && git worktree add ../jobbot-data data`. If the
branch ever needs resetting, delete it on GitHub and the next run recreates it.

## Secrets
Never commit keys. Locally use `.env`; in Actions use repository secrets. `.env` and
`config/profile.yaml` are gitignored except for the `.example` copies. The digest is sent
through Resend: `RESEND_API_KEY`, `DIGEST_FROM`, `DIGEST_TO`.
