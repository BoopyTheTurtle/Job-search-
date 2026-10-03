# ADR-0002: GitHub Actions runtime, SQLite state on a `data` branch, email digest

Date: 2026-10-03 · Status: Accepted

## Context
The bot runs weekly for one user. Options considered: a cloud VM or serverless function
with Postgres and a web UI; GitHub Actions with state in the repo; a desktop cron job.

## Decision
- Run on a scheduled GitHub Actions workflow (`17 6 * * 3` UTC) with manual dispatch.
- Persist state in a single SQLite file plus Markdown digests, committed to an orphan
  `data` branch by the workflow. `main` stays protected and contains only code.
- Deliver via SMTP email (HTML + text). A Markdown copy is always committed, so a lost
  email is recoverable.

## Alternatives rejected
- **Cloud host + Postgres + web UI:** more capability but monthly cost, auth, and
  maintenance for a single user. Can be revisited in Phase 4 or later.
- **Actions cache / artifacts for state:** evicted after days; not durable.
- **Committing state to `main`:** conflicts with branch protection and pollutes PR history.
- **Google Sheet / Notion:** convenient but adds OAuth setup; may be added as a second
  channel later.

## Consequences
- Zero hosting cost. Runs take a few minutes within the free tier.
- Cron on GitHub can be delayed by minutes to an hour at busy times; the overlap window
  handles missed items.
- Clone of `data` grows slowly (a few MB per month); prune descriptions after 180 days.
