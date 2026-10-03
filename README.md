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
cp config/profile.example.yaml config/profile.yaml   # edit: home_country, email, keyword boosts
uv run jobbot sources
uv run jobbot crawl --source remotive --limit 5 --dry-run
```

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
- **Secrets:** `RESEND_API_KEY`, `DIGEST_FROM`, `DIGEST_TO` in repository settings.

## Status
Phase 1 (MVP digest): pipeline, filtering, digest and weekly workflow are in place.
Remotive is the only enabled source until the Tier A connectors pass a live smoke run.
