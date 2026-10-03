# Roadmap and backlog

Each item becomes a GitHub issue; phases become milestones. Keep PRs small: one item,
one PR. Items are ordered by dependency within a phase.

## Phase 0 — Foundation
- [x] Spec, ADRs, inventory research
- [x] Repo scaffold: `uv`, `ruff`, `mypy`, `pytest`, pre-commit, CI workflow
- [x] Canonical `Job`/`RawJob` models and `Source` protocol
- [x] Reference connector: Remotive, with fixture test
- [x] GitHub collaboration: CODEOWNERS, PR template, issue templates, Dependabot, CONTRIBUTING
- [x] Owner: enable branch protection on `main` (require PR, require CI, no force push)
- [x] Owner: home country (LV), languages (en/fr/lv/es), email provider (Resend), licence (MIT)
- [x] Owner: keyword boosts (html, css, javascript, typescript, python, c)
- [ ] Owner: create a Resend API key and add the three secrets

## Phase 1 — MVP weekly digest
- [x] Normalizer: HTML→text, date parsing, URL canonicalisation
- [x] Enrich: language detection (`lingua`, accept en/fr/lv/es)
- [x] Enrich: remote type classifier with golden tests
- [x] Enrich: regions-allowed parser and eligibility check with golden tests
- [x] Enrich: role family taxonomy (`config/taxonomy.yaml`) and classifier
- [x] Enrich: seniority and employment type classifiers
- [x] Dedupe: canonical URL + fuzzy (company, title, location) key
- [x] Store: SQLite schema, upsert, runs and source_runs tables
- [x] Filter and score per `profile.yaml`
- [x] Digest: Markdown, HTML and plain-text renderers (Jinja2)
- [x] Digest: Resend API sender with secrets, dry-run mode
- [x] Connectors: Arbeitnow, RemoteOK, Himalayas, Jobicy, WeWorkRemotely RSS, Working Nomads (disabled until smoke-tested)
- [x] Workflow: `weekly-crawl.yml` on cron with `data` branch checkout and commit
- [x] Workflow: `manual-smoke.yml` live run with `--limit 5`, artifact upload
- [ ] Owner: add Resend secrets, trigger `weekly-crawl` once by hand
- [x] Run `manual-smoke`; all six Tier A sources verified live and enabled (fixtures still synthetic)
- [ ] First real digest received and reviewed; tune `taxonomy.yaml` and scoring from it

## Phase 2 — European breadth
- [ ] Connector: Adzuna (all supported EU countries + GB/US/CA/AU/NZ, keyword `remote`)
- [ ] Connector: EURES
- [ ] Connector: Arbetsförmedlingen JobTech (SE)
- [ ] Connector: France Travail
- [ ] Connector: Arbeitsagentur Jobsuche (DE), if API status allows
- [ ] Connector: Reed (UK)
- [ ] Connector: Jooble, The Muse, Careerjet (keys permitting)
- [x] Per-country remote vocabulary (DE, FR, ES, IT, NL, PL, SV, NO, FI, LV)
- [x] Crawl failure → GitHub issue automation (`crawl-failure` label)
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
