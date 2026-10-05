# ADR-0004: Parallel searches over one shared crawl

Date: 2026-10-05 · Status: Accepted

## Context
The bot began with one profile: remote IT jobs. The owner now wants a second, separate
search for international development, project and development finance, private equity,
ESG and project administration. It accepts on-site and hybrid work in the EU and
Switzerland, reads English and French only, and arrives as its own email. Both searches
draw on the same sources.

## Decision
A search is one YAML file in `config/searches/`: a profile (the fields `config/profile.yaml`
used to hold), a digest title, and optional per-source `queries`.

- **One crawl per run.** Every enabled source runs once into the shared store. A
  keyword-driven source that a search lists under `queries` runs once per such search,
  with that query merged over its `params` in `sources.yaml`; source health labels these
  runs `source:search`.
- **Every search scores the whole pool.** Each search evaluates all jobs first seen in the
  run, so a job either search finds can reach the other. A job that fits both profiles
  appears in both emails.
- **One digest and one email per search**, written to `digests/<search>/YYYY-MM-DD.md`.
  Both go to `DIGEST_TO`. The run summary `runs/YYYY-MM-DD.json` lists every digest.
- **The store keeps the best score.** `jobs.score` holds the highest score any search gave
  the job; `score_reasons` starts with that search's name.
- **Role families stay a single label.** Classification is profile-free; the new families
  (`intl_development`, `finance_investment`, `private_equity`, `project_admin`) join the
  taxonomy, and each search picks the families it wants. Exclusions that only one search
  needs move from the taxonomy into that search's `exclude_title_patterns`.
- **Work arrangement is a profile setting.** `hybrid_regions` and `onsite_regions` say
  where office jobs count; a hybrid or on-site job must name a country inside them. A
  profile that accepts on-site work reads an unknown arrangement as on-site.
  `preferred_countries` gives office jobs in those countries the same points as remote.

## Consequences
- Adding a third search is one YAML file and, if it needs its own queries, nothing more.
- Keyword sources cost one call set per querying search; rate budgets in `sources.yaml`
  must cover all of them.
- A search cannot see a job first seen in an earlier week. Acceptable: the digest reports
  what is new.
- A title that matches two families equally becomes `other` and is dropped by both
  searches. Keep each title phrase in one family.
