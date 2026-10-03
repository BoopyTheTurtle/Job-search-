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

```bash
```

## Licence
MIT, see [`LICENSE`](LICENSE).

## Status
Phase 0 (foundation). The reference connector (Remotive) works in dry-run mode. Weekly
digest lands in Phase 1.
