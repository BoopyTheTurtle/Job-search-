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
| Workday | JSON: `POST https://<tenant>.<wdN>.myworkdayjobs.com/wday/cxs/<tenant>/<site>/jobs` with `{"limit":20,"offset":0,"searchText":""}` | tested live | Ardian (`ardian.wd103`, site `ArdianCareers`), Triton (`tritonpartners.wd3`, `External`), Global Fund (`theglobalfund.wd1`, `External`) |
| Greenhouse | `GET https://boards-api.greenhouse.io/v1/boards/<slug>/jobs` | tested live | EQT (`eqtpartners`) |
| SmartRecruiters | `GET https://api.smartrecruiters.com/v1/companies/<id>/postings` | tested live | OECD (`OECD`) |
| Recruitee | `GET https://<slug>.recruitee.com/api/offers/` | tested live | Meridiam (`meridiam`) |

Greenhouse, SmartRecruiters and Recruitee connectors exist since 2026-10-05; the employers
they crawl are listed in `config/companies.yaml`.

## SAP SuccessFactors career sites: blocked by robots.txt

The RSS feed (`/services/rss/job/`) works on every site tested, but every site's
robots.txt disallows `/services/` for all user agents, so ADR-0001 rules it out. Each site
also publishes `/sitemap.xml`, which robots.txt allows. On EBRD it is a full Google Jobs
feed with descriptions (one request per employer). Elsewhere it lists job URLs only, and
reading a job means fetching its HTML page under `/job/` (allowed by robots.txt). That page
carries schema.org `itemprop` markup for title, date, location and description. Fetching
HTML pages is a Tier E source and needs the owner's approval in the PR.

Sites found (checked 2026-10-05): EBRD (`jobs.ebrd.com`), UNESCO (`careers.unesco.org`),
ILO (`jobs.ilo.org`), ICRC (`careers.icrc.org`), CEB (`jobs.coebank.org`), Partners Group
(`jobs.partnersgroup.com`), Enabel (`jobs.enabel.be`), FMO (`fmo.jobs.hr.cloud.sap`),
Triodos (`careers.triodos.com`).

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

The impact-finance search queries Adzuna and France Travail through its own `queries`
(`config/searches/impact-finance.yaml`); both connectors take a list of queries and run
each one separately.

- **Adzuna:** 14 English queries in the FR, BE, NL, ES, CH and DE indexes, plus six French
  queries in FR and BE, one page each, every category: 96 calls a week at 2.5 s apart.
  Adzuna has no Portugal or Luxembourg index.
- **France Travail:** 13 French queries across all domains, one page (150 offers) each.

Reed is UK-only and the search excludes UK office jobs, so it stays out. JobTech is mostly
Swedish and stays out too.

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

## Employer watchlist

`config/companies.yaml` holds every employer a connector can read: Ardian, Triton and the
Global Fund (Workday), EQT (Greenhouse), OECD (SmartRecruiters), Meridiam and PAI Partners
(Recruitee). A live crawl on 2026-10-05 found 19 postings from the past week, six of them
strong matches for the impact-finance search.

Checked on 2026-10-05 and not reachable yet:

| Employer | Where its jobs are | Why not |
|---|---|---|
| EBRD, UNESCO, ILO, ICRC, CEB, Partners Group, Enabel, FMO, Triodos | SuccessFactors | See the SuccessFactors section above |
| Tikehau, Eurazeo | Welcome to the Jungle, JobTeaser | Terms forbid scraping |
| Antin | Teamtailor | No connector yet |
| BlueOrchard | BambooHR | No connector yet |
| Apax | Lever (one New York posting) | No connector yet |
| EIB, EIF, AFD, Proparco, IFAD | Own portals | Pages blocked (HTTP 403) or no public feed found |
| LuxDev | Own site, Moovijob | No feed; Moovijob blocks bots |
| SOFID | Own site with an RSS link | Not yet checked |

Not yet researched or unresolved:

- **Development finance:** BIO (Belgium), Cofides (Spain).
- **International organisations:** Gavi, WHO, UNHCR, UNICEF.
- **Private equity, infrastructure and impact funds:** CVC, Cinven, Permira, Mirova,
  Bridgepoint, Astorg, Wendel, InfraVia, Incofin, responsAbility, Symbiotics, I&P,
  Oikocredit, Triple Jump. Their careers pages either load job lists through JavaScript or
  moved; none matched a public API under the slugs tried.
