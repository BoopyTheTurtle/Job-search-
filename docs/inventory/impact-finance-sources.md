# Sources for the impact-finance search

Research date: 2026-10-05. Scope: international development, development and project
finance, private equity, ESG and project administration, in the EU and Switzerland
(Benelux, France, Spain, Portugal and Switzerland first). Robots.txt was checked with
Python's `urllib.robotparser` for a generic user agent; terms pages were read where they
loaded. "Tested live" means a request from the research machine returned job data.

Most of these jobs sit on employers' own applicant tracking systems (ATS) and a few sector
boards, not on general job sites. One connector per ATS reaches many employers.

## Usable now: official feed, no key

| Source | Access | Status | Reaches |
|---|---|---|---|
| SAP SuccessFactors career sites | RSS: `https://<site>/services/rss/job/?locale=en_GB&keywords=` | tested live | EBRD (`jobs.ebrd.com`), UNESCO (`careers.unesco.org`), ILO, FMO |
| Workday | JSON: `POST https://<tenant>.<wdN>.myworkdayjobs.com/wday/cxs/<tenant>/<site>/jobs` with `{"limit":20,"offset":0,"searchText":""}` | tested live | Ardian (`ardian.wd103`, site `ArdianCareers`), Triton (`tritonpartners.wd3`, `External`), Global Fund (`theglobalfund.wd1`, `External`) |
| Greenhouse | `GET https://boards-api.greenhouse.io/v1/boards/<slug>/jobs` | tested live | EQT (`eqtpartners`) |
| SmartRecruiters | `GET https://api.smartrecruiters.com/v1/companies/<id>/postings` | tested live | OECD (`OECD`) |
| Recruitee | `GET https://<slug>.recruitee.com/api/offers/` | tested live | Meridiam (`meridiam`) |

Greenhouse, SmartRecruiters and Recruitee are already planned in Phase 3.

## Approved by the owner: unofficial endpoints

| Source | Access | Notes |
|---|---|---|
| UN Careers (careers.un.org) | JSON: `POST https://careers.un.org/api/public/opening/jo/list/filteredV2/en` with `{"filterConfig":{"keyword":""},"pagination":{"page":0,"itemPerPage":50,"sortBy":"startDate","sortDirection":-1}}` | Tested live. The site's own front end calls it; robots.txt allows it. The UN terms permit personal, non-commercial downloading and say nothing on automated access. Keep to a few requests a week, no redistribution, kill switch. Covers the UN Secretariat. |
| EURES | Undocumented `jv-search` endpoint; see `apis-and-feeds.md` | EU-wide plus Switzerland, many English postings. Same handling as UN Careers. |

## Later, maybe

| Source | Why not now |
|---|---|
| ReliefWeb API (UN OCHA) | Needs a pre-approved `appname` since 1 November 2025 (an unapproved name returns HTTP 403). Free, 1,000 calls a day, content CC BY 4.0. Strongest single source for NGO and development jobs. Docs: https://apidoc.reliefweb.int/ |
| Jooble | Needs a free key (jooble.org/api/about). Adds Portugal and Luxembourg, which Adzuna lacks. |

## Keyword queries on existing sources

Adzuna (`be`, `nl`, `fr`, `es`, `ch` and others) and France Travail take a second set of
queries through the impact-finance search's `queries` (next PR). Reed is UK-only and the
search excludes UK office jobs, so it stays out.

## Rejected

| Source | Reason |
|---|---|
| UNjobs.org | robots.txt disallows all paths for every user agent |
| UNjobnet | Terms forbid robots, spiders, scrapers and crawlers |
| Devex | HTTP 403 to automated requests; paywalled |
| DevelopmentAid, NGOjobsite, Moovijob, APEC | HTTP 403 (bot protection) to automated requests |
| eFinancialCareers | Terms page did not load; commercial board, assumed to forbid scraping like its peers |
| Welcome to the Jungle | Terms forbid scraping (see `apis-and-feeds.md`) |
| EuroBrussels | No terms page, no feed |
| Impactpool | robots.txt allows crawling, but no terms page found; ask before use |
| World Bank Group (Cornerstone, `worldbankgroup.csod.com`) | Job list renders only through JavaScript; revisit later |

## Employer watchlist candidates

Check each one's ATS before adding it to `config/companies.yaml`.

- **Development banks and finance institutions:** EIB, EIF, CEB, AFD and Proparco, BIO
  (Belgium), FMO (Netherlands, SuccessFactors), Cofides (Spain), SOFID (Portugal),
  LuxDev, Enabel, EBRD (SuccessFactors).
- **International organisations:** OECD (SmartRecruiters), UNESCO (SuccessFactors), ILO
  (SuccessFactors), Global Fund (Workday), Gavi, WHO, UNHCR.
- **Private equity and infrastructure funds:** Ardian (Workday), EQT (Greenhouse),
  Triton (Workday), Meridiam (Recruitee), Eurazeo, PAI Partners, Tikehau, Partners Group,
  CVC, Cinven, Permira, Mirova.
