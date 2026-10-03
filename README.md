# Job Search Bot

A personal, zero-cost bot that runs every Wednesday on GitHub Actions, pulls IT job
postings from legitimate APIs and feeds across Europe and selected other countries, keeps
the ones that are remote, written in English (or French, Latvian or Spanish) and open to
an EU-based candidate in Latvia, and emails a ranked digest of what is new via Resend.

- **Spec:** [`docs/SPEC.md`](docs/SPEC.md)
- **Backlog:** [`docs/ROADMAP.md`](docs/ROADMAP.md) and the GitHub issues
- **Decisions:** [`docs/adr/`](docs/adr/)
- **Source inventory:** [`docs/inventory/`](docs/inventory/)
- **Contributing:** [`CONTRIBUTING.md`](CONTRIBUTING.md)

## Quick start
```bash
uv sync --all-extras
uv run jobbot sources
uv run jobbot crawl --source remotive --limit 5 --dry-run   # raw postings, nothing stored
uv run jobbot run --no-send --db /tmp/jobbot.sqlite --out-dir /tmp/out   # full run, digest on disk
```

Edit `config/profile.yaml` to tune filters and scoring. Set `RESEND_API_KEY`, `DIGEST_FROM`
and `DIGEST_TO` (see `.env.example`) to receive the digest by email.

## Licence
MIT, see [`LICENSE`](LICENSE).

## Operations
- **Weekly run:** the `weekly-crawl` workflow runs Wednesdays 06:17 UTC. Trigger it by hand
  from the Actions tab; tick *dry_run* to get the digest as an artifact without emailing or
  writing state.
- **State:** the `data` branch holds `jobbot.sqlite`, `digests/YYYY-MM-DD.md` and
  `runs/YYYY-MM-DD.json`. Only the workflow writes to it.
- **New sources:** run `manual-smoke` for the source, check the artifact, replace the
  synthetic fixture, then flip `enabled: true` in `config/sources.yaml`.
- **Secrets:** `RESEND_API_KEY`, `DIGEST_FROM`, `DIGEST_TO` in repository settings. Keyed
  sources add their own (`ADZUNA_APP_ID`, `ADZUNA_APP_KEY`, `REED_API_KEY`,
  `FRANCE_TRAVAIL_CLIENT_ID`, `FRANCE_TRAVAIL_CLIENT_SECRET`); without them the source is skipped.

## Status
Phase 1 (MVP digest): pipeline, filtering, digest and weekly workflow are in place.
Remotive is the only enabled source until the Tier A connectors pass a live smoke run.
