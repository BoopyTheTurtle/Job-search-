# Job Search Bot

A personal, zero-cost bot that runs every Wednesday on GitHub Actions, pulls IT job
postings from legitimate APIs and feeds across Europe and selected other countries, keeps
the ones that are remote, in English and open to an EU-based candidate, and emails a
ranked digest of what is new.

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

## Status
Phase 0 (foundation). The reference connector (Remotive) works in dry-run mode. Weekly
digest lands in Phase 1.
