# Roadmap and backlog

Each item becomes a GitHub issue; phases become milestones. Keep PRs small: one item,
one PR. Items are ordered by dependency within a phase.

## Phase 0 — Foundation
- [x] Spec, ADRs, inventory research
- [x] Repo scaffold: `uv`, `ruff`, `mypy`, `pytest`, pre-commit, CI workflow
- [x] Canonical `Job`/`RawJob` models and `Source` protocol
- [x] Reference connector: Remotive, with fixture test
- [x] GitHub collaboration: CODEOWNERS, PR template, issue templates, Dependabot, CONTRIBUTING
- [ ] Owner: enable branch protection on `main` (require PR, require CI, no force push)
- [ ] Owner: fill in `config/profile.yaml` (home country, keyword boosts, email)

## Phase 1 — MVP weekly digest
- [ ] Normalizer: HTML→text, date parsing, URL canonicalisation
- [ ] Enrich: language detection (`lingua`)
- [ ] Enrich: remote type classifier with golden tests
- [ ] Enrich: regions-allowed parser and eligibility check with golden tests
- [ ] Enrich: role family taxonomy (`config/taxonomy.yaml`) and classifier
- [ ] Enrich: seniority and employment type classifiers
- [ ] Dedupe: canonical URL + fuzzy (company, title, location) key
- [ ] Store: SQLite schema, upsert, runs and source_runs tables
- [ ] Filter and score per `profile.yaml`
- [ ] Digest: Markdown, HTML and plain-text renderers (Jinja2)
- [ ] Digest: SMTP sender with secrets, dry-run mode
- [ ] Connectors: Arbeitnow, RemoteOK, Himalayas, Jobicy, WeWorkRemotely RSS, Working Nomads
- [ ] Workflow: `weekly-crawl.yml` on cron with `data` branch checkout and commit
- [ ] Workflow: `manual-smoke.yml` live run with `--limit 5`, artifact upload
- [ ] First real digest received and reviewed

## Phase 2 — European breadth
- [ ] Connector: Adzuna (all supported EU countries + GB/US/CA/AU/NZ, keyword `remote`)
- [ ] Connector: EURES
- [ ] Connector: Arbetsförmedlingen JobTech (SE)
- [ ] Connector: France Travail
- [ ] Connector: Arbeitsagentur Jobsuche (DE), if API status allows
- [ ] Connector: Reed (UK)
- [ ] Connector: Jooble, The Muse, Careerjet (keys permitting)
- [ ] Per-country remote/region vocab (DE, FR, ES, IT, NL, PL, Nordics)
- [ ] Crawl failure → GitHub issue automation
- [ ] Source health dashboard section in digest

## Phase 3 — Employer-direct (ATS)
- [ ] Generic ATS connectors: Greenhouse, Lever, Ashby, Workable, Recruitee, Personio, SmartRecruiters, Teamtailor
- [ ] `config/companies.yaml` watchlist schema and loader
- [ ] Seed watchlist from public "remote-friendly European companies" lists
- [ ] ATS auto-detection helper: given a careers URL, guess the ATS and slug

## Phase 4 — Quality loop
- [ ] `feedback.yaml`: hide job, hide company, applied — reflected in digest and scoring
- [ ] Scoring tuning from feedback
- [ ] Description retention pruning (180 days)
- [ ] Optional second channel (Telegram/Slack) behind a flag
- [ ] Optional: static HTML report published via GitHub Pages from the `data` branch
