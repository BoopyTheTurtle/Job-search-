# Job Search Bot — Specification

Status: Draft v0.1 (Phase 0) · Last updated: 2026-10-03 · Owner: @BoopyTheTurtle

## 1. Purpose

A personal, zero-cost bot that runs once a week, pulls IT job postings from legitimate
APIs and feeds across Europe and selected other countries, keeps only the postings that
are **remote**, **in English**, and **eligible for an EU-based candidate**, and emails a
ranked digest of what is new since the last run.

It is a personal tool. One user, no web UI, no multi-tenancy. The crawler core is kept
separate from the user profile so this can change later without a rewrite (see ADR-0001).

Since 2026-10-05 the bot runs parallel **searches** over one shared crawl (ADR-0004), each
with its own profile and email. The IT search is the one described above. The
impact-finance search covers international development, project and development finance,
private equity, ESG and sustainable finance, and project administration; it accepts
remote, hybrid and on-site work in the EU and Switzerland (not the UK), favours Benelux,
France, Spain, Portugal and Switzerland, and reads English and French. Its sources are
listed in `docs/inventory/impact-finance-sources.md`.

## 2. Interview summary (what was decided)

| Question | Decision |
|---|---|
| Audience | Personal tool, single user |
| Sourcing | API and feed first. No scraping of sites whose terms forbid it (LinkedIn, Indeed, StepStone, Glassdoor, etc.). Polite HTML fetching only where terms and robots.txt permit |
| Eligibility | EU-based with EU/EEA work rights only. Postings count if they are remote and allow EU/EEA, a named EU country, or worldwide. US/CA/AU/NZ postings count **only** when they allow working from anywhere |
| Home country | Latvia (`LV`). Postings restricted to Latvia count as eligible alongside EU/EEA/worldwide ones |
| Roles | Software/web development, DevOps/cloud/SRE, data/ML/AI engineering, broader IT (support, sysadmin, QA, technical product/project) |
| Seniority | Intern, junior and mid-level included (confirmed). Senior/lead/staff/principal postings are kept but shown in a collapsed "senior-only" section rather than dropped. Configurable |
| Contract type | Permanent, part-time, freelance, contract and B2B all included, tagged separately |
| Language | Posting text in English, French, Latvian or Spanish. English is the primary target; the other three are accepted and tagged with their language in the digest |
| Runtime | GitHub Actions scheduled workflow, every Wednesday |
| Delivery | Email digest (HTML + plain text) sent through the Resend API (free tier). Markdown copy committed to the repo |
| Licence | MIT |
| Stack | Python 3.11+, `uv`, `ruff`, `mypy`, `pytest` |
| Collaboration | Small PRs per feature, CI required, owner reviews and merges. Issues track the backlog |

## 3. Goals and non-goals

### Goals
1. Weekly digest of new remote IT postings, written in English (or French, Latvian or Spanish), eligible for an EU-based candidate living in Latvia.
2. Coverage of Europe (EU-27, UK, Switzerland, Norway, Iceland) plus worldwide-remote postings from AU, NZ, US, CA sources.
3. Zero running cost: GitHub Actions free tier, free API tiers, SQLite in a git branch.
4. Every source is legal to use: public API, documented partner API with a key, or RSS/XML feed.
5. Reproducible and testable: every connector has an offline fixture test.
6. Easy to extend: adding a source is one module plus one YAML entry plus one fixture.

### Non-goals (for now)
- Scraping sites whose terms of service forbid automated access.
- Auto-applying, CV tailoring, or contacting recruiters.
- Multi-user accounts, authentication, hosted web UI.
- Real-time alerts. Weekly cadence only (manual runs allowed).
- Postings in languages other than English, French, Latvian and Spanish (language is a profile filter, not an architectural limit).

## 4. Users and scenarios

**Primary scenario.** Wednesday 08:17 CEST: an email arrives with ~20–80 new postings
grouped by match strength. Each row shows title, company, remote scope ("Worldwide",
"EU only", "Germany only"), contract type, seniority guess, salary if present, source,
and a link. A footer shows per-source health (fetched / new / errors).

**Secondary scenarios.**
- Run manually from the Actions tab after adding a source or changing filters.
- Run locally with `jobbot crawl --dry-run` to debug a connector without sending email.
- Mark companies or title patterns as "never show again" via `config/profile.yaml`.
- Query history: `data/jobbot.sqlite` can be opened with any SQLite client.

## 5. System overview

```
GitHub Actions (cron Wed)                       Secrets: API keys, SMTP
        │
        ▼
  jobbot run ──► sources/* ──► normalize ──► enrich ──► dedupe ──► store (SQLite)
                 (API/RSS)     (RawJob→Job)  (lang,     (URL +     │
                                            remote,     fuzzy)     ▼
                                            region,             filter + score (profile.yaml)
                                            role,                 │
                                            seniority)            ▼
                                                             digest (HTML/text/MD)
                                                                  │
                                                      ┌───────────┴───────────┐
                                                      ▼                       ▼
                                                SMTP email              commit to `data` branch
```

### 5.1 Components

| Component | Responsibility | Key files |
|---|---|---|
| `jobbot.sources` | One connector per source. Fetches raw postings via API/feed, honours rate limits, returns `RawJob` | `src/jobbot/sources/<name>.py` |
| `jobbot.normalize` | Maps `RawJob` to the canonical `Job` schema; cleans HTML to text; parses dates and salaries | `src/jobbot/normalize.py` |
| `jobbot.enrich` | Language detection, remote classification, region/eligibility inference, role family, seniority, employment type | `src/jobbot/enrich/` |
| `jobbot.dedupe` | Canonical-URL and fuzzy (company, title, location) dedup across sources | `src/jobbot/dedupe.py` |
| `jobbot.store` | SQLite persistence: jobs, sightings, runs, source health | `src/jobbot/store.py` |
| `jobbot.filter` | Applies `profile.yaml`; computes a 0–100 score | `src/jobbot/filter.py` |
| `jobbot.digest` | Renders HTML, text and Markdown digests; sends email via the Resend API | `src/jobbot/digest/` |
| `jobbot.cli` | `jobbot sources`, `jobbot crawl`, `jobbot digest`, `jobbot run` | `src/jobbot/cli.py` |
| Config | `profile.yaml` (user filters), `sources.yaml` (enabled sources, env var names), `companies.yaml` (ATS watchlist), `taxonomy.yaml` (role keywords) | `config/` |
| Workflows | `ci.yml` (PR checks), `weekly-crawl.yml` (cron + manual) | `.github/workflows/` |

### 5.2 Data flow per run
1. Load config and every search in `config/searches/`. Decide `since` = last successful run minus 1 day of overlap (first run: 14 days).
2. For each enabled source: fetch once, or once per search that lists the source under `queries` (ADR-0004), with per-source timeout and retry (3 attempts, exponential backoff). A failing source is recorded, never fatal to the run.
3. Normalize each `RawJob` to `Job`. Enrich. Compute dedup key.
4. Upsert into SQLite: new job → insert with `first_seen`; existing → update `last_seen`, append sighting.
5. For each search: filter and score jobs with `first_seen == this run`.
6. For each search: render its digest and send it through Resend if `RESEND_API_KEY` exists, else write only.
7. Commit `data/jobbot.sqlite`, `data/digests/<search>/YYYY-MM-DD.md`, `data/runs/YYYY-MM-DD.json` to the `data` branch.
8. Fail the workflow (red) only if the store could not be written or more than 50% of sources failed.

## 6. Canonical data model

```python
class Job:
    id: str                    # sha1 of dedup key
    title: str
    company: str | None
    url: str                   # canonical, tracking params stripped
    source: str                # first source that saw it
    source_ids: dict[str, str] # every (source → native id) that saw it
    location_raw: str | None
    remote_type: RemoteType    # remote | hybrid | onsite | unknown
    regions_allowed: list[str] # ISO-3166 alpha-2, or WORLDWIDE | EU | EEA | EUROPE | AMERICAS | APAC | UNKNOWN
    employment_type: EmploymentType  # full_time | part_time | contract | freelance | internship | unknown
    seniority: Seniority       # intern | junior | mid | senior | lead | unknown
    role_family: RoleFamily    # software_dev | devops_cloud | data_ml_ai | it_ops_qa_product | other
    language: str | None       # ISO-639-1 of the posting text
    salary_raw: str | None
    salary_min: int | None; salary_max: int | None; salary_currency: str | None; salary_period: str | None
    posted_at: datetime | None
    first_seen: datetime
    last_seen: datetime
    description_text: str
    tags: list[str]
    score: int                 # 0–100, recomputed per run from the profile
    score_reasons: list[str]   # human-readable, shown in digest
```

### SQLite tables
- `jobs` — one row per `Job.id`, columns as above (JSON for lists/dicts).
- `sightings` — `(job_id, source, source_id, url, seen_at)`; many per job.
- `runs` — `(run_id, started_at, finished_at, since, status, new_jobs, digest_path)`.
- `source_runs` — `(run_id, source, fetched, new, errors, duration_ms, error_message)`.
- `feedback` — `(job_id, verdict, note, at)` for future "hide/applied" tracking.

## 7. Source strategy

Full inventory lives in `docs/inventory/` (per-country sites and API/feed reference).
Sources are grouped into tiers; each tier maps to a roadmap phase.

| Tier | Type | Examples | Why |
|---|---|---|---|
| A | Remote-first job APIs, keyless | Remotive, Arbeitnow, RemoteOK, Himalayas, Jobicy, WeWorkRemotely RSS, Working Nomads | Highest remote density, free, English-language, trivially legal |
| B | Aggregators with keys and country coverage | Adzuna (many EU countries + GB/US/CA/AU/NZ), Jooble, Reed (UK), The Muse, Careerjet | Country breadth for Europe; remote filter via keyword |
| C | Public employment services | EURES, Arbetsförmedlingen JobTech (SE), France Travail, Arbeitsagentur (DE), others per inventory | Official, open, cover countries with weak private APIs |
| D | ATS public boards | Greenhouse, Lever, Ashby, Workable, Recruitee, Personio, SmartRecruiters, Teamtailor | Direct from employers, no intermediary, excellent data quality. Needs a company watchlist |
| E | Permissive HTML | National IT boards whose robots.txt and terms allow it | Gap-fill only, last resort, each one needs an explicit ToS note in the PR |

Excluded: LinkedIn, Indeed, Glassdoor, StepStone, Xing, Monster, Totaljobs and any
site whose terms forbid automated access. These may be added later only via an
official partner API.

### Connector contract
```python
class Source(Protocol):
    name: str                       # snake_case, matches sources.yaml key
    def fetch(self, since: datetime | None, limit: int | None = None) -> Iterable[RawJob]: ...
```
Rules: use the shared `httpx.Client` with the project User-Agent; respect documented rate
limits (default 1 request/second); never follow more than 20 pages per run; raise
`SourceError` on hard failures; log counts. Every connector ships with a recorded JSON
fixture under `tests/fixtures/<source>/` and a test asserting field mapping.

## 8. Classification rules

### 8.1 Language
Detect on `title + first 2000 chars of description_text`. Keep if the detected language
is in `profile.languages` (`en`, `fr`, `lv`, `es`) with confidence ≥ 0.8. Postings under
200 chars fall back to title-only detection with a lower bar. The detector is restricted
to a candidate set (the profile languages plus the common neighbours `de`, `nl`, `pl`,
`it`, `pt`, `ru`, `lt`, `et`) so short Latvian and Spanish texts are not misread.
Library: `lingua-language-detector` (accurate on short text; supports all four). Phase 1.
Non-English accepted languages are shown with a language tag in the digest.

### 8.2 Remote type
Order of precedence:
1. Structured field from the source (e.g. Remotive is remote by definition; Adzuna has no flag; Greenhouse `location.name`, Lever `workplaceType`, Ashby `isRemote`).
2. Title or location contains `remote`, `fully remote`, `work from anywhere`, `home office`, `homeoffice`, `télétravail`, `teletrabajo`, `100% remote` → `remote`.
3. `hybrid` or `2 days in office` patterns → `hybrid`.
4. Negative patterns override: `no remote`, `not remote`, `remote not possible`, `on-site only`, `onsite only`.
5. Otherwise `unknown`. Unknown is **excluded** from the digest unless the source is remote-first.

### 8.3 Regions allowed
Parse `location_raw`, `candidate_required_location`, title suffixes, and the first 1000
chars of the description for: `worldwide|anywhere|global` → `WORLDWIDE`; `EU|European
Union|EU only|EMEA (treated as EUROPE)|Europe|EEA|CET ±N` → `EU`/`EUROPE`; country names and
ISO codes → alpha-2 list; `US only|US-based|must be located in the United States`,
`US timezones` → `US`. Timezone-only restrictions (`UTC-1 to UTC+3`) are mapped to
`EUROPE` with a `timezone_inferred` tag.

Eligibility: a job is eligible if `regions_allowed ∩ profile.eligible_regions ≠ ∅`,
where EU membership expands (`EU` matches any EU country code and vice versa).
`profile.eligible_regions` defaults to `[WORLDWIDE, EU, EEA, CH]` plus
`profile.home_country` (`LV`). It omits `EUROPE`, which expands to the UK and other
non-EU countries and would admit UK-only jobs; a job tagged `EUROPE` still matches
through its EU countries. Baltic and Nordic phrasing (`Baltics`, `Baltic states`,
`Nordics & Baltics`) maps to `[EE, LV, LT]` (plus Nordic codes). Jobs with `UNKNOWN`
region from a remote-first source are shown in the "verify eligibility" section.

### 8.4 Role family
Keyword taxonomy in `config/taxonomy.yaml`: include patterns per family, global exclude
patterns (`sales engineer`, `recruiter`, `account executive`, `IT sales`, `nurse`).
Families: `software_dev`, `devops_cloud`, `data_ml_ai`, `it_ops_qa_product` (IT search);
`intl_development`, `finance_investment`, `private_equity`, `project_admin`
(impact-finance search). Exclusions only one search needs live in that search's
`exclude_title_patterns`.
Title match weighs 3x description match. Ties → `other`. Jobs whose family is `other`
are excluded.

### 8.5 Seniority
Title patterns: `intern|werkstudent|praktikum` → intern; `junior|graduate|entry|trainee|
associate` → junior; `senior|sr\.|lead|staff|principal|head of|director|architect` →
senior/lead; else mid. Description phrases (`5+ years`) refine when the title is silent.

### 8.6 Employment type
From structured fields where available; else title/description patterns for
`part-time|teilzeit|deeltijd`, `freelance|contract|B2B|contractor|UoP/B2B`, `internship`.

### 8.7 Score (0–100)
| Signal | Points |
|---|---|
| Role family in profile | +30 (+10 if title match, not just description) |
| Language `en` | +15 (`fr`, `lv`, `es`: +10) |
| Remote type `remote`, or hybrid/on-site in a `preferred_countries` country | +15 (other office jobs 0) |
| Eligibility confirmed (not inferred) | +15 (+5 if inferred) |
| Seniority matches profile | +10 (senior-only: −10 and moved to collapsed section) |
| Posted within 7 days | +5 |
| Salary present | +5 |
| Profile keyword boosts (e.g. `python`, `typescript`) | +1 each, max +5 |
| Blocklisted company or title pattern | hard exclude |

Digest sections: **Strong (≥70)**, **Possible (50–69, verify eligibility)**,
**Senior-only (collapsed)**. Below 50 is stored but not emailed.

## 9. Configuration

`config/searches/<name>.yaml`, one file per search (user-owned, committed; preferences
only, the recipient address comes from the `DIGEST_TO` secret). The IT search:
```yaml
title: IT                     # digest heading and email subject
eligible_regions: [WORLDWIDE, EU, EEA, CH]   # where a remote job must allow work from
home_country: LV
languages: [en, fr, lv, es]
role_families: [software_dev, devops_cloud, data_ml_ai, it_ops_qa_product]
seniority: [intern, junior, mid]          # senior/lead kept but collapsed
employment_types: [full_time, part_time, contract, freelance, internship]
keyword_boosts: [python, typescript, javascript, html, css, c]
exclude_companies: []
exclude_title_patterns: ["sales", "recruiter"]
digest:
  min_score: 50
  max_items: 150
  to: []                      # local fallback only; CI uses the DIGEST_TO secret
queries:                      # per-source params merged over sources.yaml `params`
  adzuna: {what: remote, category: it-jobs}
```

Work arrangement fields (see `config/searches/impact-finance.yaml`): `hybrid_regions`
(default: the home country), `onsite_regions` (default: none; when set, an unknown
arrangement reads as on-site), and `preferred_countries` (office jobs there score like
remote ones). A hybrid or on-site job must name a country inside its regions.

`config/sources.yaml`: each source has `enabled`, optional `env` (names of secrets),
`params` (e.g. Adzuna country list; query terms belong in each search's `queries`),
`rate_limit_rps`.

Secrets (GitHub repo settings → Secrets): `RESEND_API_KEY`, `DIGEST_FROM` (a sender on a
domain verified in Resend, or Resend's onboarding sender for testing), `DIGEST_TO`;
later `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`, `REED_API_KEY`, `JOOBLE_API_KEY`,
`MUSE_API_KEY`. Locally via `.env` (gitignored, see `.env.example`).

## 10. Runtime and operations

- **Schedule:** `17 6 * * 3` UTC (Wednesday 06:17 UTC, jittered off the hour), plus
  `workflow_dispatch` with inputs `dry_run`, `sources`, `since_days`.
- **Code branch:** `main` (protected). **Data branch:** `data` (orphan branch holding
  `jobbot.sqlite`, `digests/`, `runs/`). The workflow checks out `main` for code and
  `data` into `./data`, then commits back to `data` as `github-actions[bot]`. This keeps
  `main` protected and the PR history clean.
- **Budget:** one run ≈ 5–10 minutes. Well inside the 2,000 free minutes/month.
- **Failure policy:** per-source failures are reported in the digest footer; the
  workflow is red only on store write failure or >50% source failure. Red runs open or
  update a GitHub issue labelled `crawl-failure` (Phase 2).
- **Retention:** SQLite grows ~1–3 MB/month. Prune `description_text` for jobs older
  than 180 days (Phase 4).

## 11. Quality, testing, CI

- `ruff check`, `ruff format --check`, `mypy --strict` on `src/`, `pytest` on every PR.
- Offline tests only in CI: connectors tested against recorded fixtures via `respx`.
- `manual-smoke` workflow (dispatch only): live crawl with `--limit 5` per source,
  uploads the normalized JSON as an artifact for eyeballing.
- Golden tests for classification rules: `tests/fixtures/classification/*.yaml` with
  expected `remote_type`, `regions_allowed`, `role_family`, `seniority`.
- Coverage target 80% on `enrich/`, `normalize.py`, `dedupe.py`.

## 12. Legal and ethical constraints

- Only use sources via their public API, a partner API with a key we hold, or a feed the
  site publishes for consumption. Record the terms link in `sources.yaml`.
- Honour `robots.txt` and published rate limits. Identify with a descriptive User-Agent
  containing the repo URL.
- Store only what the digest needs. Postings are public, but we do not redistribute the
  data; the `data` branch stays in this private repo.
- Attribute the source in every digest row and link to the original posting.
- Remove a source immediately if its terms change or the owner asks.

## 13. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Free API quotas or key revocation | Missing sources | Per-source isolation; health footer; quotas documented in `sources.yaml` |
| "Remote" false positives (hybrid, "no remote") | Noise | Negative patterns, structured fields first, golden tests, feedback list |
| Eligibility false positives (US-only remote) | Wasted applications | Region parser with `verify` section, never silently promote `UNKNOWN` |
| Language detection on short posts | Misses | Title fallback, lower threshold for short texts |
| Cross-source duplicates | Noise | URL canonicalisation + fuzzy key, sightings table |
| Actions cron drift or skipped runs | Late digest | Overlap window, manual dispatch, run log |
| Email deliverability | Digest lost | Resend API with delivery status in the run log; Markdown copy committed to `data`; optional second channel later |
| Resend free tier limits (100 emails/day, 3,000/month) | None at weekly cadence | One email per run; alert if the digest exceeds the size limit and split |
| Scope creep into scraping | Legal exposure | Tier E requires explicit ToS note and owner approval in the PR |

## 14. Roadmap

See `docs/ROADMAP.md` for the issue-level backlog. Phases:

0. **Foundation** (this PR): spec, inventory, repo scaffold, CI, connector contract, one reference connector.
1. **MVP digest:** Tier A sources, normalize/enrich/dedupe, SQLite, email, weekly workflow on `data` branch.
2. **European breadth:** Tier B and C sources, per-country remote/region rules, failure issues.
3. **Employer-direct:** Tier D ATS watchlist and company discovery.
4. **Quality loop:** feedback file, scoring tuning, retention, optional second delivery channel.

## 15. Open questions

Resolved 2026-10-03: home country Latvia; mid-level included; posting languages en/fr/lv/es;
email via Resend; MIT licence; keyword boosts HTML, CSS, JavaScript, TypeScript, Python, C.

Still open:
1. Senior-only postings: keep collapsed (current default) or drop entirely?
2. Sending domain for Resend: verify a domain you own, or use Resend's onboarding sender
   (which can only deliver to the account's own address, fine for a personal tool).
