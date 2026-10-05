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
- [x] Owner: create a Resend API key and add the three secrets

## Phase 1 — MVP weekly digest
- [x] Normalizer: HTML→text, date parsing, URL canonicalisation
- [x] Enrich: language detection (`lingua`, accept en/fr/lv/es)
- [x] Enrich: remote type classifier with golden tests
- [x] Enrich: regions-allowed parser and eligibility check with golden tests
- [x] Enrich: role family taxonomy (`config/taxonomy.yaml`) and classifier
- [x] Enrich: seniority and employment type classifiers
- [x] Dedupe: canonical URL + fuzzy (company, title, location) key
- [x] Store: SQLite schema, upsert, runs and source_runs tables
- [x] Filter and score per profile (now `config/searches/*.yaml`)
- [x] Digest: Markdown, HTML and plain-text renderers (Jinja2)
- [x] Digest: Resend API sender with secrets, dry-run mode
- [x] Connectors: Arbeitnow, RemoteOK, Himalayas, Jobicy, WeWorkRemotely RSS, Working Nomads (disabled until smoke-tested)
- [x] Workflow: `weekly-crawl.yml` on cron with `data` branch checkout and commit
- [x] Workflow: `manual-smoke.yml` live run with `--limit 5`, artifact upload
- [x] Owner: add Resend secrets, trigger `weekly-crawl` once by hand (first digest sent 2026-10-03)
- [x] Run `manual-smoke`; all six Tier A sources verified live and enabled (fixtures still synthetic)
- [ ] First real digest received and reviewed; tune `taxonomy.yaml` and scoring from it

## Phase 2 — European breadth
- [x] Connector: Adzuna (AT BE DE ES FR IT NL PL + GB/US/CA/AU/NZ, `what=remote`, IT category); enabled after a live smoke run
- [x] Owner: register at developer.adzuna.com, add `ADZUNA_APP_ID` / `ADZUNA_APP_KEY` secrets, run `manual-smoke` for `adzuna`
- [ ] Connector: EURES (approved 2026-10-05 for both searches)
- [x] Connector: Arbetsförmedlingen JobTech (SE): `remote=true` in Data/IT, CC0, keyless
- [x] Connector: France Travail (IT domain, `télétravail`); enabled after a live smoke run
- [ ] Connector: Arbeitsagentur Jobsuche (DE), if API status allows
- [x] Connector: Reed (UK); enabled after a live smoke run
- [x] Owner: Reed key (reed.co.uk/developers/jobseeker) and France Travail OAuth client (francetravail.io) as secrets, then `manual-smoke` each
- [ ] Connector: Jooble, The Muse, Careerjet (keys permitting)
- [x] Per-country remote vocabulary (DE, FR, ES, IT, NL, PL, SV, NO, FI, LV)
- [x] Crawl failure → GitHub issue automation (`crawl-failure` label)
- [ ] Source health dashboard section in digest

## Phase 2b — Impact-finance search (ADR-0004)
- [x] Parallel searches in `config/searches/`, one digest and email each; new role families
- [x] Source research: `docs/inventory/impact-finance-sources.md`
- [x] Impact-finance queries for Adzuna (FR BE NL ES CH DE) and France Travail
- [ ] Owner: run `weekly-crawl` by hand with `searches: impact-finance` and review the first digest
- [ ] Connectors: SuccessFactors career-site RSS, Workday job API
- [ ] Connector: UN Careers (approved 2026-10-05, unofficial endpoint)
- [ ] Watchlist seed: development banks, international organisations, PE and infrastructure funds
- [ ] Later, maybe: ReliefWeb API (needs an approved appname), Jooble (needs a key)

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
