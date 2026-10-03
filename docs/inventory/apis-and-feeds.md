# Job APIs and Feeds: Technical Inventory

Date stamp: 2026-10-03. Scope: sources usable by a Python bot that runs weekly on GitHub Actions, API-first, no scraping of sites whose terms forbid it.

Verification legend: **verified** = confirmed against official docs or a primary artifact (official GitHub repo, official help page) or multiple independent secondary sources during research on 2026-10-03; **unverified** = reported by a single secondary source, or inferred from client code, or from memory. Several vendor doc sites (developer.adzuna.com, developers.greenhouse.io, developers.ashbyhq.com, themuse.com, reed.co.uk, jobtechdev.se, himalayas.app, jobicy.com, remoteok.com, arbeitnow.com, careerjet.com, usajobs.gov) could not be fetched directly from the research environment; claims for those rest on their official GitHub repos where they exist, plus secondary sources.

---

## 1. Remote-job and aggregator APIs

### Remotive
- Endpoint: `GET https://remotive.com/api/remote-jobs` (verified, official repo github.com/remotive-com/remote-jobs-api).
- Params: `category` (e.g. `software-dev`), `company_name`, `search`, `limit`.
- Auth: none. Cost: free.
- Pagination: none; `limit` caps results. Full feed in one call.
- Remote/location fields: `candidate_required_location` (free text, e.g. `Worldwide`, `Europe`, `USA`, `UK`), `job_type` (`full_time`, `contract`, `part_time`, `freelance`, `internship`), `publication_date` (ISO 8601), `salary`, `description` (HTML), `url`.
- Rate limit: official guidance "max ~4 calls/day"; more than ~2 req/min gets blocked. Data has a 24 h delay.
- Terms: must link back and credit Remotive; forbidden to re-submit jobs to other aggregators (Jooble, Google Jobs) or collect signups off their listings.
- Coverage: global, English, remote only. Good EU share.

### Arbeitnow
- Endpoint: `GET https://www.arbeitnow.com/api/job-board-api` (verified via multiple secondary sources; site not fetchable here).
- Params: `page` (unverified name; follow `links.next` instead).
- Auth: none. Cost: free.
- Pagination: Laravel-style `links.next` / `links.prev` and `meta`.
- Fields: `slug`, `company_name`, `title`, `description`, `remote` (boolean), `url`, `tags[]`, `job_types[]`, `location` (string), `created_at` (unix ts). No salary.
- Rate limit: unpublished; keep to a few requests per run.
- Terms: free "job board API", no stated attribution, but attribute anyway. Coverage: Germany/EU heavy, many German-language postings; `remote` flag is reliable.

### RemoteOK
- Endpoint: `GET https://remoteok.com/api` (verified, secondary). Also `https://remoteok.com/remote-jobs.rss` reported as HTTP 410 (retired) by one source (unverified).
- Auth: none. Cost: free.
- Pagination: none; returns ~100 most recent jobs. Element `[0]` is a legal notice, not a job: skip it.
- Fields: `id`, `slug`, `epoch`, `date` (ISO), `position`, `company`, `location` (free text, e.g. `Worldwide`, `Europe`, `US only`), `tags[]`, `description`, `salary_min`, `salary_max`, `url`, `apply_url`, `company_logo`, `logo`.
- Rate limit: unpublished. Weekly fetch is fine.
- Terms (in element 0): you may use the data only if you link back to the RemoteOK posting URL with a normal followed link (no `nofollow`) and name RemoteOK as source. Coverage: global, English.

### Himalayas
- Endpoints: browse `GET https://himalayas.app/jobs/api?limit=20&offset=0`; a search variant exists with keyword, country, company slug, seniority, employment type, timezone (parameter names unverified). Documented at himalayas.app/api (not fetchable here; claims from secondary sources, verified across several).
- Auth: none. Cost: free.
- Pagination: `limit` (max 20 since 2025-03-24) and `offset`. Full-feed sync needs many requests; fetch only the first few pages weekly (feed is newest-first; unverified).
- Fields: `locationRestrictions[]` (countries the role is open to; the single most useful EU filter in this group), `timezoneRestrictions`, `employmentType`, `seniority`, `pubDate`, `companyName`, `title`, `applicationLink`, `description`.
- Rate limit: unpublished. Terms: attribution expected; not fetched (unverified). Coverage: global, English, remote only.

### Jobicy
- Endpoint: `GET https://jobicy.com/api/v2/remote-jobs` (verified, official repo github.com/Jobicy/remote-jobs-api).
- Params: `count` (1-200, default 200 per the repo; older docs say max 100), `cursor` (pagination token valid 24 h), `geo` (e.g. `usa`, `europe`, `apac`, `anywhere`, `canada`; current list via `?get=locations`), `industry` (slug; list via `?get=industries`, unverified), `tag` (3-50 chars keyword).
- Auth: none. Cost: free.
- Pagination: cursor-based (`nextCursor`, `hasMore`).
- Fields: `id`, `url`, `jobTitle`, `companyName`, `jobIndustry`, `jobType`, `jobGeo` (eligibility region), `jobLevel`, `jobExcerpt`, `jobDescription` (HTML), `pubDate`, optional `annualSalaryMin/Max`, `salaryCurrency`.
- Rate limit: no hard number; official rule "do not poll more than once per hour"; cache responses.
- Terms: keep Jobicy as source and preserve canonical Jobicy URL; no spam networks or misrepresentation. Coverage: global, English, remote; `geo=europe` works directly.

### We Work Remotely (RSS)
- Feeds (verified, weworkremotely.com/remote-job-rss-feed): all jobs `https://weworkremotely.com/remote-jobs.rss`; per category e.g. `https://weworkremotely.com/categories/remote-programming-jobs.rss`, `remote-full-stack-programming-jobs.rss`, `remote-back-end-programming-jobs.rss`, `remote-front-end-programming-jobs.rss`, `remote-devops-sysadmin-jobs.rss`, `remote-design-jobs.rss`, `remote-product-jobs.rss`, `remote-sales-and-marketing-jobs.rss`, `remote-management-and-finance-jobs.rss`, `remote-customer-support-jobs.rss`, `all-other-remote-jobs.rss`.
- Auth: none. Cost: free. Pagination: none (recent items only).
- Fields: standard RSS `title` (often "Company: Title"), `link`, `pubDate`, `description` (HTML), plus `region` and `category` elements and `media:content` logo (element names partly unverified). Region text such as "Anywhere in the World", "Europe Only", "USA Only" is the remote-restriction signal; parse it.
- Rate limit: none stated. Terms: anyone may use the feeds; attribute links back to WWR. Coverage: global, English.

### Working Nomads
- Endpoint: `GET https://www.workingnomads.com/api/exposed_jobs/` (verified via several secondary sources; official docs page not found). RSS feed URL: unverified.
- Auth: none. Cost: free. Pagination: none (current open jobs in one array).
- Fields: `url`, `title`, `company_name`, `category_name`, `tags`, `location` (free text, e.g. `Anywhere`, `Europe`, `USA`), `pub_date`, `description` (HTML). Exact key names unverified.
- Rate limit / terms: unpublished; Working Nomads is itself an aggregator, so expect duplicates with Remotive/WWR. Attribute. Coverage: global, English.

### The Muse
- Endpoint: `GET https://www.themuse.com/api/public/jobs` and `/jobs/{id}` (verified, secondary; docs page not fetchable).
- Params: `page` (required, 0- or 1-based unverified), `category`, `level` (`Entry Level`, `Mid Level`, `Senior Level`, ...), `location` (repeatable; includes value `Flexible / Remote`), `company`, `descending`, `api_key`.
- Auth: optional key (`api_key` query). Without key 500 req/h, with key 3,600 req/h.
- Pagination: `page`, with `page_count` in response. 20 results per page (unverified).
- Fields: `name`, `company.name`, `locations[].name`, `levels[]`, `categories[]`, `publication_date`, `refs.landing_page`, `contents` (HTML).
- Terms: attribution ("Powered by The Muse") expected; free for non-commercial. Coverage: US-centric; EU coverage weak.

### Adzuna
- Endpoint: `GET https://api.adzuna.com/v1/api/jobs/{country}/search/{page}?app_id=...&app_key=...&what=...&where=...&results_per_page=50&max_days_old=7&content-type=application/json` (verified).
- Country codes: the 19-country set `at au be br ca ch de es fr gb in it mx nl nz pl sg us za` is the list used by many clients and documented in several repos (verified across 3+ independent sources; developer.adzuna.com/docs/regional was not fetchable). One secondary source lists only 16 (adds `ru`, omits `be ch es nz`); treat `be`, `ch`, `es`, `nz`, `ru` availability as **unverified** and probe each with one request. EU/EEA coverage therefore: AT, BE, DE, ES, FR, IT, NL, PL (+ CH); no Nordics, no IE, PT, CZ etc. Plus GB, US, CA, AU, NZ.
- Other params: `what_and`, `what_or`, `what_exclude`, `title_only`, `distance`, `salary_min`, `full_time`, `permanent`, `contract`, `sort_by` (`date`), `category`.
- Auth: free `app_id` + `app_key` from developer.adzuna.com. Cost: free tier (rate limits unpublished; commonly cited ~250 calls/day, unverified).
- Pagination: path `{page}` (1-based), max `results_per_page=50`.
- Fields: `title`, `company.display_name`, `location.display_name`, `location.area[]` (hierarchical: country, region, city), `description` (snippet only), `redirect_url`, `created`, `salary_min/max`, `contract_type`, `contract_time`, `category.tag`. No remote flag: put "remote" in `what` and regex the title/description.
- Terms: attribution ("Jobs by Adzuna" link/logo) required; no redistribution of listings; results link out to Adzuna, not the employer. Postings are in the local language of each country index.

### Jooble
- Endpoint: `POST https://jooble.org/api/{api_key}` with JSON body `{"keywords": "...", "location": "...", "radius": "...", "salary": "...", "page": 1, "ResultOnPage": 20, "datecreatedfrom": "..."}` (keywords/location/page verified; other body keys unverified).
- Auth: free key on request at jooble.org/api/about (partner API). Cost: free, per-key limits unpublished.
- Response: `totalCount`, `jobs[]` with `title`, `location`, `snippet`, `salary` (text), `source`, `link`, `company`, `updated`, `id`, `type`.
- Remote: no flag; use `location: "remote"` plus keyword. Coverage: 60+ countries including all EU; local-language postings. Terms: links must go to Jooble; attribution expected (unverified).

### Careerjet
- Endpoint: `GET https://public.api.careerjet.net/search` (classic affiliate API; verified via official client repos github.com/careerjet/careerjet-api-client-python) with required `affid`, `user_ip`, `user_agent`, plus `locale_code` (e.g. `en_GB`, `de_DE`, `fr_FR`, `nl_NL`, `es_ES`, `it_IT`, `pl_PL`, `sv_SE`), `keywords`, `location`, `sort`, `start_num`, `pagesize` (max 99), `page`, `contracttype`, `contractperiod`. A newer per-locale `https://public-api.careerjet.{tld}/jobs` with Basic auth (API key as username) is also reported (unverified).
- Auth: affiliate ID (free signup). Cost: free.
- Fields: `jobs[].title`, `company`, `locations`, `date`, `description`, `salary`, `url` (Careerjet redirect), `site`.
- Terms: designed for display on a website to end users (hence `user_ip`/`user_agent`); using it for a private bot is a grey area: read the partner agreement before use. Remote: no flag. Coverage: ~90 countries, local language.

### Reed.co.uk
- Endpoint: `GET https://www.reed.co.uk/api/1.0/search?keywords=...&locationName=...&distanceFromLocation=10&resultsToTake=100&resultsToSkip=0` and `GET /api/1.0/jobs/{jobId}` (verified, secondary).
- Auth: HTTP Basic, API key as username, empty password. Free key via reed.co.uk/developers/jobseeker.
- Pagination: `resultsToTake` max 100, `resultsToSkip`; `totalResults` in response.
- Fields: `jobId`, `employerName`, `jobTitle`, `locationName`, `minimumSalary`, `maximumSalary`, `currency`, `date` (dd/MM/yyyy), `expirationDate`, `jobDescription` (snippet in search; full in detail), `jobUrl`, `applications`, `fullTime`, `partTime`, `contractType` fields.
- Remote: no flag; `locationName` often reads `Remote` or `Work from home`; also keyword "remote". Coverage: UK only, English. Terms: attribution to Reed required; no bulk redistribution.

### EURES (EU job mobility portal)
- Status: no officially documented public API. The portal's own front-end calls `POST https://europa.eu/eures/eures-apps/searchengine/page/jv-search/search` (verified from several open-source clients) with JSON `{"resultsPerPage":50,"page":1,"sortSearch":"BEST_MATCH","keywords":[{"keyword":"python","specificSearchCode":"EVERYWHERE"}],"publicationPeriod":null,"occupationUris":[],"positionScheduleCodes":[],"sectorCodes":[],"positionOfferingCodes":[],"locationCodes":["de","nl"],"requiredLanguages":[]}`.
- Auth: none, but it requires a session cookie `EURES_JVSE_SESSIONID` and `XSRF-TOKEN` cookie mirrored in header `X-XSRF-TOKEN`, obtained by a first GET to `https://europa.eu/eures/portal/jv-se/search` (some clients needed a browser; plain `requests.Session` reportedly works, unverified).
- Response: `numberRecords`, `jvs[]` with `id`, `title`, `description`, `employer`, `locationMap` (country -> cities), `creationDate`, `lastModificationDate`, `positionScheduleCodes`, `positionOfferingCode`, `jobCategoriesCodes`, `availableLanguages`, `score`. Detail: `https://europa.eu/eures/portal/jv-se/jv-details/{id}`.
- Remote: no field; filter by keyword. Coverage: all EU/EEA + CH, 2M+ postings aggregated from national PES, mostly local language. Terms: Europa.eu legal notice permits reuse of Commission documents with attribution, but this is an internal UI endpoint, not a published API; treat as "best effort, may break, keep volume minimal". Recommended: phase 3, or prefer the national PES APIs below.

### JobTech / Arbetsförmedlingen Platsbanken (Sweden)
- Endpoints: `GET https://jobsearch.api.jobtechdev.se/search?q=python&remote=true&limit=100&offset=0&published-after=2026-09-26T00:00:00` and `GET /ad/{id}` (verified, jobtechdev.se news + forum). Incremental alternative: JobStream API (`https://jobstream.api.jobtechdev.se/stream?date=...`) for changes since a timestamp.
- Auth: since 2022-03-04 no personal key; send header `api-key: developer` (shared public key) (verified, jobtechdev.se news). Cost: free.
- Pagination: `limit` (max 100), `offset` (max 2000). Filters: `occupation-field`, `municipality`, `region`, `country`, `employment-type`, `published-after/before`, `sort`.
- Fields: `headline`, `employer.name`, `workplace_address` (`municipality`, `region`, `country`), `description.text`, `publication_date`, `application_details.url`, `webpage_url`, `must_have`, `nice_to_have`, `working_hours_type`, `remote` (search param; heuristic phrase match, not structured, per JobTech forum).
- Terms: open data, free of charge; license statement for the ad texts not fetched (unverified; believed to be open with attribution). Coverage: Sweden, mostly Swedish; English tech ads exist.

### France Travail: Offres d'emploi v2
- Endpoint: `GET https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search?motsCles=python&departement=75&range=0-149&minCreationDate=...` (verified). Token: `POST https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=/partenaire` with `grant_type=client_credentials`, `scope=api_offresdemploiv2 o2dsoffre`.
- Auth: free developer account at francetravail.io, OAuth2 client credentials. Cost: free.
- Rate limit: 3 req/s (verified). Pagination: `range=a-b` with 150 per page; `a` max 1000, `b` max 1149 (1,150 results per query).
- Fields: `resultats[].intitule`, `entreprise.nom`, `lieuTravail.libelle/codePostal/commune`, `typeContrat`, `dateCreation`, `dateActualisation`, `description`, `origineOffre.urlOrigine`, `salaire`, `competences`; `filtresPossibles` facets.
- Remote: no structured flag in v2 (unverified); filter on "télétravail" in `description`/`intitule`. Coverage: France, French. Terms: francetravail.io CGU; attribution required; no reselling.

### Arbeitsagentur Jobsuche (Germany)
- Status: **unofficial / undocumented**. Reverse-engineered by github.com/bundesAPI/jobsuche-api (verified). The Bundesagentur offers no official public API; endpoint may change without notice.
- Endpoint: `GET https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs?was=python&wo=Berlin&umkreis=25&arbeitszeit=ho&veroeffentlichtseit=7&page=1&size=100` (v4 app endpoint; `pc/v6/jobs` also reported). Details `GET /pc/v4/jobdetails/{base64(refnr)}`.
- Auth: header `X-API-Key: jobboerse-jobsuche` (static client id). Cost: free.
- Params: `was`, `wo`, `umkreis` (km), `arbeitszeit` (`vz` full, `tz` part, `snw` shift, `ho` = Heim-/Telearbeit = home office, `mj` mini-job), `angebotsart` (1 job, 4 training, 34 internship), `veroeffentlichtseit` (days, 0-100), `page`, `size`.
- Fields: `stellenangebote[].titel`, `beruf`, `arbeitgeber`, `arbeitsort` (`ort`, `plz`, `region`, `land`), `aktuelleVeroeffentlichungsdatum`, `refnr`, `externeUrl`. Remote: `arbeitszeit=ho` filter.
- Terms: no license granted; data © BA. Use sparingly, low volume, and be ready for breakage. Coverage: Germany, German.

### USAJobs
- Endpoint: `GET https://data.usajobs.gov/api/search?Keyword=python&RemoteIndicator=True&ResultsPerPage=500&Page=1` (endpoint/headers verified; `RemoteIndicator` as a *query* filter is reported by secondary sources, unverified against official docs).
- Auth: free key; headers `Host: data.usajobs.gov`, `User-Agent: <registered email>`, `Authorization-Key: <key>`.
- Pagination: `ResultsPerPage` max 500, `Page`. Fields: `SearchResult.SearchResultItems[].MatchedObjectDescriptor` with `PositionTitle`, `OrganizationName`, `PositionLocation[]`, `PositionRemuneration`, `PublicationStartDate`, `ApplyURI`, `UserArea.Details.RemoteIndicator`, `TeleworkEligible`.
- Coverage: US federal only, English; most roles require US citizenship. Terms: public domain data; rate limits unpublished. Low value for an EU-based search; include only if the user wants US.

### Others (notable)
- **Jobspresso**: WordPress job board; RSS presumed at `https://jobspresso.co/feed/?post_type=job_listing` (**unverified**; no documented API).
- **Remote.co**: no API; RSS not found (**unverified**). Skip.
- **Landing.jobs**: `GET https://landing.jobs/api/v1/jobs` returns a public JSON array of EU tech postings (verified in two open-source clients; the official LandingJobs-api repo documents token auth for `/companies.json`, so auth for `/jobs` is **unverified**). Fields include `title`, `company_name`, `remote`, `city`, `country_code`, `published_at`, `url` (unverified).
- **EU-Startups job board**: WordPress + Jobbio partnership; an RSS feed exists per their blog, URL **unverified**. Low priority.
- **Welcome to the Jungle (incl. Otta)**: Otta merged into WTTJ in 2024. No public developer API for reading jobs; integrations are ATS-side (push). Third-party scrapers use the site's internal Algolia search; scraping is against WTTJ terms. **Not viable** via API.
- **Wellfound (AngelList Talent)**: old `api.angel.co` returns 404; no public jobs API. **Not viable**.
- **JustJoin.it** (Poland/EU): `GET https://justjoin.it/api/candidate-api/offers` public JSON reported (unverified). Candidate for phase 3.

---

## 2. ATS public job boards

All of these serve the JSON that the employer's own careers page calls. They are per-company: you need a company slug/token list (see "Discovering the ATS" below). None require auth unless noted. Rate limits are generally unpublished; treat as "a few requests per company per run".

### Greenhouse
- Endpoint: `GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true` (verified). Optional `&pay_transparency=true`. Single job: `/jobs/{id}?questions=true`. Also `/departments`, `/offices`.
- Token: the slug in `boards.greenhouse.io/{token}` or `job-boards.greenhouse.io/{token}`. Some EU tenants use `boards.eu.greenhouse.io` with `boards-api.eu.greenhouse.io` (unverified).
- Pagination: none; whole board in one response (`jobs[]`, `meta.total`).
- Fields: `id`, `title`, `updated_at`, `first_published`, `location.name` (single string; "Remote", "Remote - EMEA", "Berlin, Germany" etc.), `offices[].name/location`, `departments[].name`, `absolute_url`, `content` (HTML-escaped), `metadata[]` (custom fields; some employers put "Remote: Yes" here), `pay_input_ranges` (with pay_transparency). No native remote boolean.
- Rate limit: unpublished; reasonable polling accepted. Terms: data is public; no auth for GET; attribution not required. Low risk.

### Lever
- Endpoint: `GET https://api.lever.co/v0/postings/{site}?mode=json&skip=0&limit=100` (verified). EU tenants: `https://api.eu.lever.co/v0/postings/{site}`. Single posting `/postings/{site}/{id}`.
- Site slug: from `jobs.lever.co/{site}` or `jobs.eu.lever.co/{site}`.
- Params: `skip`, `limit` (default 100; use skip loop until short page), `team`, `department`, `location`, `commitment` (repeatable), `group`.
- Fields: `id`, `text` (title), `createdAt` (ms epoch), `hostedUrl`, `applyUrl`, `categories.{team,department,location,commitment,allLocations[]}`, `workplaceType` (`remote` | `hybrid` | `onsite`; verified), `country` (ISO code), `descriptionPlain`, `lists[]`, `additionalPlain`, `salaryRange`.
- Remote detection: `workplaceType == "remote"` plus `categories.location` text ("Remote - Europe"). Terms: open, no auth; no published limits.

### Ashby
- Endpoint: `GET https://api.ashbyhq.com/posting-api/job-board/{org}?includeCompensation=true` (verified). `org` from `jobs.ashbyhq.com/{org}`.
- Pagination: none; `jobs[]` complete.
- Fields: `id`, `title`, `department`, `team`, `employmentType`, `location` (string), `secondaryLocations[]`, `address.postalAddress.{addressLocality,addressRegion,addressCountry}`, `isRemote` (boolean, verified), `isListed`, `publishedAt`, `jobUrl`, `applyUrl`, `descriptionHtml`, `descriptionPlain`, `compensation.compensationTiers[]`.
- Remote detection: `isRemote` plus `location`/`secondaryLocations` for region ("Remote - EMEA"). Terms: official public API; no auth; limits unpublished.

### Workable
- Public widget: `GET https://apply.workable.com/api/v1/widget/accounts/{account}?details=true` (verified). Account slug from `apply.workable.com/{account}/`. Also `GET https://apply.workable.com/api/v3/accounts/{account}/jobs` (POST with `{"query":"","location":[],"remote":true}` reported, unverified) used by the newer careers UI.
- Pagination: widget returns all in `jobs[]`; v3 paginates with `token` (unverified).
- Fields: `title`, `shortcode`, `url`/`shortlink`, `application_url`, `department`, `employment_type`, `experience`, `location.{country, country_code, city, region, telecommuting}` (`telecommuting` boolean = remote, verified via secondary; `remote` boolean also reported), `workplace` (`remote`/`hybrid`/`on_site`, unverified), `published_on`, `created_at`, `description` (with `details=true`).
- SPI (`https://{subdomain}.workable.com/spi/v3/jobs?state=published`): requires a bearer token issued to the *customer*; not for third parties. Ignore.
- Terms: widget API is intended for embedding on the employer's own site; third-party reads are tolerated and widely used but not formally licensed. Keep volume low.

### Recruitee (Tellent)
- Endpoint: `GET https://{company}.recruitee.com/api/offers/` (verified, Recruitee docs: "does not require authorization and is available under your Careers Site address"). Optional `?department=...`. Single: `/api/offers/{slug}`.
- Pagination: none; `offers[]` complete, ~56 fields each.
- Fields: `id`, `slug`, `title`, `status`, `department`, `location` (combined string), `city`, `state_name`, `country`, `country_code`, `postal_code`, `remote` (bool), `hybrid` (bool), `on_site` (bool) (verified), `employment_type_code`, `min_hours`/`max_hours`, `created_at`, `published_at`, `careers_url`, `careers_apply_url`, `description` (HTML), `requirements`, `salary{}` (often empty), `tags[]`.
- Terms: official careers-site API; strong EU footprint (NL/DE/PL). Low risk.

### Personio
- Endpoint: `GET https://{company}.jobs.personio.de/xml` (also `.jobs.personio.com/xml`); `?language=en` or `de` selects locale (verified). Slug from `{company}.jobs.personio.de`.
- Format: XML `<workzag-jobs><position>...`. Fields: `id`, `name`, `subcompany`, `office`, `additionalOffices`, `department`, `recruitingCategory`, `employmentType`, `seniority`, `schedule`, `yearsOfExperience`, `occupation`, `occupationCategory`, `createdAt`, `keywords`, `jobDescriptions/jobDescription{name,value}` (verified). Job URL: `https://{company}.jobs.personio.de/job/{id}`.
- Remote: no flag; `office` often literally "Remote"; otherwise regex description for "remote"/"Homeoffice". No pagination. Terms: public feed built for aggregators (Indeed etc.); no auth. Coverage: DACH SMEs, mostly German.

### SmartRecruiters
- Endpoint: `GET https://api.smartrecruiters.com/v1/companies/{companyIdentifier}/postings?limit=100&offset=0` (verified). Single: `/postings/{id}` (full `jobAd.sections`). Filters: `q`, `country`, `region`, `city`, `department`, `updatedAfter`, `language`, `custom_field.*`.
- Pagination: `limit` (max 100), `offset`, `totalFound`.
- Fields: `id`, `uuid`, `name`, `refNumber`, `releasedDate`, `location.{city, region, country, remote (bool), fullLocation}` (verified), `department.label`, `typeOfEmployment.label`, `experienceLevel.label`, `ref` (API url), `company.identifier`; apply URL `https://jobs.smartrecruiters.com/{company}/{id}`.
- Terms: official, keyless when the customer enabled public postings (lower-tier customers may be off). Limits unpublished.

### Teamtailor
- RSS: `https://{company}.teamtailor.com/jobs.rss` or on a custom domain `https://career.{company}.com/jobs.rss` (verified, Teamtailor help: append `.rss` to the jobs page). Items: title, description, link, `remote status`, global id, location(s), department (element names unverified; inspect first feed).
- JSON API `GET https://api.teamtailor.com/v1/jobs` needs a customer token + `X-Api-Version: 20240904`; not public. Ignore.
- Pagination: none; feed lists all published jobs. Coverage: Nordics strong, English common. Terms: RSS is a public feature; attribute.

### BambooHR
- Endpoints: `GET https://{company}.bamboohr.com/careers/list` (summaries) and `GET https://{company}.bamboohr.com/careers/{id}/detail` (verified). Response `result[]` with `id`, `jobOpeningName`, `departmentLabel`, `employmentStatusLabel`, `location.{city,state,country}`, `isRemote` (reported, unverified), `atsLocation`, `datePosted`; detail adds `description`, `compensation`.
- Pagination: none. Auth: none. Terms: internal careers-page endpoint, not a documented public API; use lightly. Coverage: mostly US SMEs; some EU.

### Join.com
- No documented public API. Careers pages `https://join.com/companies/{slug}` are Next.js and embed `__NEXT_DATA__` JSON; an internal `https://join.com/api/public/companies/{id}/jobs?page=1&pageSize=100` is reported by one client (**unverified**; needs numeric company id). `api.join.com/v2/jobs` returns 422 without params (unverified).
- Fields (from page data, unverified): `title`, `workplaceType`/`remote`, `location.{city,country}`, `employmentType`, `publishedAt`, `url`.
- Status: not viable in phase 1; phase 3 if Swiss/German startups matter. Scraping page HTML may breach join.com terms.

### Workday
- Status: hard but keyless. Each tenant: `POST https://{tenant}.wd{N}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs` with JSON `{"appliedFacets":{},"limit":20,"offset":0,"searchText":"python"}` and `Content-Type: application/json` (verified). GET returns nothing useful. Detail: `GET /wday/cxs/{tenant}/{site}/{externalPath}`.
- Pagination: `limit` (max 20) / `offset`; `total` in response. Fields: `jobPostings[].title`, `locationsText`, `postedOn` ("Posted 3 Days Ago"), `bulletFields[]` (req id), `externalPath`; detail `jobPostingInfo.{remoteType, location, additionalLocations, startDate, jobDescription}`.
- Remote: `appliedFacets.workerSubType`/`locations` facet ids vary per tenant; `jobPostingInfo.remoteType` text in detail. Terms: undocumented internal API; large enterprises; brittle. Phase 3 only, for a handful of named companies.

### iCIMS
- Status: no public jobs API. Career portals `https://careers-{company}.icims.com/jobs/search?ss=1&in_iframe=1` render from an internal JSON endpoint (`/jobs/search?...&pr={page}` HTML, or on newer Jibe-based sites `/api/jobs?page=1`) (unverified). The Customer/Partner REST API is OAuth and customer-only. **Not viable** without HTML parsing; skip.

### Jobvite
- Status: no universal public API. Customers may enable a "Job Feed" (`https://jobs.jobvite.com/{company}/jobs` HTML; a legacy XML/JSON feed requires the customer to enable it and often an api/sc key) (unverified). Widget data comes from an internal endpoint whose schema differs by tenant. **Not viable**; skip.

### Discovering which ATS a company uses
Check the careers link's final redirect host; patterns (verified by common usage):
- `boards.greenhouse.io/{t}`, `job-boards.greenhouse.io/{t}`, `boards.eu.greenhouse.io/{t}`, or embedded iframe `boards-api.greenhouse.io/v1/boards/{t}/embed` -> Greenhouse token `{t}`.
- `jobs.lever.co/{s}`, `jobs.eu.lever.co/{s}` -> Lever.
- `jobs.ashbyhq.com/{o}` or `{o}.ashbyhq.com` -> Ashby.
- `apply.workable.com/{a}/` or `{a}.workable.com` -> Workable.
- `{c}.recruitee.com` or `careers.{company}.com` whose HTML links `*.recruitee.com/api` -> Recruitee.
- `{c}.jobs.personio.de`, `{c}.jobs.personio.com` -> Personio.
- `jobs.smartrecruiters.com/{Company}/...` or `careers.smartrecruiters.com/{Company}` -> SmartRecruiters.
- `{c}.teamtailor.com` or page footer "Powered by Teamtailor" (also `<link rel=alternate type=application/rss+xml>`) -> Teamtailor.
- `{c}.bamboohr.com/careers` -> BambooHR. `join.com/companies/{c}` -> Join. `{t}.wd1..wd12.myworkdayjobs.com` -> Workday. `careers-{c}.icims.com` -> iCIMS. `jobs.jobvite.com/{c}` -> Jobvite.
- Fallbacks: fetch `/careers` or `/jobs` HTML once and grep for the host names above; check `robots.txt`/`sitemap.xml`; many companies also expose `https://{domain}/.well-known/` nothing relevant, so the HTML grep is the practical route. Cache the result per company for months.

### Seed lists for an EU remote company watchlist
- github.com/EuropeanRemote/european-remote-software-companies (verified): remote software companies hiring in Europe, with domain, stack, salary transparency columns.
- github.com/remoteintech/remote-jobs (well-known "semi-to-fully remote companies" list with a Region column; existence from memory, **unverified** this session).
- euremotejobs.com, remoteworkeurope.eu company pages (sites exist; usable only as manual seeds, not feeds).
- Companies with public ATS boards and EU remote hiring commonly cited: GitLab (Greenhouse), Grafana Labs (Greenhouse), Elastic (Greenhouse), Canonical (Greenhouse), Automattic, Doist, Toggl, Hotjar, Buffer, Zapier, Wikimedia (Greenhouse), Sketch, Help Scout. Verify each ATS at build time.

---

## 3. Cross-cutting notes

### Comparison table

| Source | Auth | Cost | Coverage region | Remote filter | English postings | Update freq | ToS summary | Phase |
|---|---|---|---|---|---|---|---|---|
| Remotive | none | free | global remote | field `candidate_required_location` | yes | daily (24 h delay) | link back + credit; no re-syndication | 1 |
| Arbeitnow | none | free | DE/EU | `remote` bool | mixed (DE/EN) | continuous | free API, attribute | 1 |
| RemoteOK | none | free | global remote | `location` text | yes | continuous | followed link back + name source | 1 |
| Himalayas | none | free | global remote | `locationRestrictions[]` | yes | continuous | attribution (unverified) | 1 |
| Jobicy | none | free | global remote | `geo=europe`, `jobGeo` | yes | continuous | keep canonical URL; poll <= 1/h | 1 |
| WWR RSS | none | free | global remote | `region` text | yes | continuous | attribute links | 1 |
| Working Nomads | none | free | global remote | `location` text | yes | continuous | unpublished; attribute | 2 |
| The Muse | optional key | free | US-centric | `location=Flexible / Remote` | yes | daily | attribution | 3 |
| Adzuna | app_id+key | free tier | 19 countries (EU: AT BE DE ES FR IT NL PL; CH; + GB US CA AU NZ) | keyword only | local language | continuous | attribution; no redistribution | 2 |
| Jooble | key (request) | free | 60+ countries | keyword/location only | local language | continuous | link to Jooble; partner terms | 3 |
| Careerjet | affid | free | ~90 countries | keyword only | local language | continuous | built for end-user display; check agreement | 3 |
| Reed | key | free | UK | `locationName`/keyword | yes | continuous | attribution; no bulk redistribution | 2 |
| EURES | session cookie | free | EU/EEA+CH | keyword only | mixed | daily | undocumented UI endpoint; reuse w/ attribution | 3 |
| JobTech (SE) | `api-key: developer` | free | Sweden | `remote=true` (heuristic) | some | continuous | open data | 2 |
| France Travail | OAuth2 client creds | free | France | keyword ("télétravail") | no (FR) | continuous | CGU; attribution; 3 req/s | 2 |
| Arbeitsagentur | static `X-API-Key` | free | Germany | `arbeitszeit=ho` | no (DE) | continuous | unofficial, no license | 3 |
| USAJobs | key + email UA | free | US federal | `RemoteIndicator` | yes | continuous | public domain | 3/skip |
| Landing.jobs | none? (unverified) | free | EU tech | `remote` (unverified) | yes | continuous | unverified | 3 |
| Greenhouse boards | none | free | per company | `location.name` text, `metadata` | yes | real-time | public data, no auth | 1 |
| Lever postings | none | free | per company | `workplaceType`, `country` | yes | real-time | open | 1 |
| Ashby | none | free | per company | `isRemote`, `location` | yes | real-time | official public API | 1 |
| Workable widget | none | free | per company | `location.telecommuting`/`remote` | yes | real-time | embed API; tolerated | 2 |
| Recruitee | none | free | per company (EU strong) | `remote`/`hybrid`/`on_site` | mixed | real-time | official careers API | 1 |
| Personio XML | none | free | per company (DACH) | `office`=="Remote" + regex | mixed | real-time | public feed | 2 |
| SmartRecruiters | none | free | per company | `location.remote` | yes | real-time | official when enabled | 1 |
| Teamtailor RSS | none | free | per company (Nordics) | remote-status element | mixed | real-time | public feature | 2 |
| BambooHR | none | free | per company | `isRemote` (unverified), `location` | yes | real-time | internal endpoint | 3 |
| Join.com | none | free | per company (CH/DE) | page data only | mixed | real-time | undocumented; HTML | 3 |
| Workday | none | free | per company (enterprise) | `remoteType` in detail | yes | real-time | undocumented; brittle | 3 |
| iCIMS / Jobvite | n/a | n/a | per company | n/a | yes | n/a | no public API | skip |
| WTTJ/Otta, Wellfound | n/a | n/a | EU / global | n/a | yes | n/a | no public API; scraping disallowed | skip |

### Legal and ethical notes
- Keyless public endpoints are still governed by each site's terms. Common requirements: attribute the source, link to the canonical posting (RemoteOK: followed link), do not re-publish the data as your own board or push it to other aggregators (Remotive explicit), do not collect candidate data. A personal, private bot that stores postings for the owner's own review and links out to originals satisfies all of these.
- Rate-limit text is often the only "license" (Remotive <= 4/day, Jobicy <= 1/h). Respect it as a contract term.
- ATS board APIs (Greenhouse, Lever, Ashby, Recruitee, SmartRecruiters, Personio, Teamtailor RSS) are built for public consumption. Workable widget, BambooHR, Workday CXS, Join, iCIMS, Jobvite are internal page APIs: no license is granted, they can change silently, and heavy use could be seen as scraping. Use only for a short named list, low volume, with a descriptive `User-Agent` containing a contact address.
- Keyed APIs (Adzuna, Reed, Jooble, Careerjet, France Travail, USAJobs, The Muse) have written developer terms; store keys as GitHub Actions secrets; most forbid redistribution and require attribution in any UI. Careerjet's `user_ip`/`user_agent` requirement signals an end-user-display model; confirm with their partner terms before using in a batch job.
- Arbeitsagentur and EURES endpoints are unofficial; neither grants a license. Keep to a handful of requests weekly, do not redistribute, and have a kill switch.
- Do not scrape Welcome to the Jungle, Wellfound, LinkedIn, Indeed, Glassdoor, StepStone, Xing: their terms prohibit automated access and there is no public API for job seekers.
- Personal data: postings may contain recruiter names/emails; store only what is needed and purge old records (e.g. 90 days).

### Caching and rate limiting for a weekly batch job
- One run per week means every source's limits are trivially satisfied if the run is serialized: aim for <= 1 request/second per host, and `time.sleep` 0.5-1 s between company-board calls. France Travail's 3 req/s and Remotive's 2 req/min are the tightest documented.
- Use conditional requests where supported: send `If-Modified-Since`/`If-None-Match` and persist `ETag`/`Last-Modified` per URL (RSS feeds and Greenhouse often honor these; unverified per source). Persist the cache file as a workflow artifact or commit it to a `data/` branch.
- Incremental fetch: use `published-after` (JobTech), `minCreationDate` (France Travail), `max_days_old=7` (Adzuna), `veroeffentlichtseit=7` (Arbeitsagentur), `updatedAfter` (SmartRecruiters), `sort_by=date` (Adzuna), `datecreatedfrom` (Jooble, unverified). For full-dump sources (Remotive, RemoteOK, Himalayas, ATS boards) diff against stored IDs; stop paginating when a page contains only known IDs (Himalayas, Lever, Jobicy).
- Dedupe across sources on normalized (company, title, apply-URL host) and on canonical URL after stripping UTM params; aggregators (Working Nomads, Jooble, Adzuna, Careerjet) re-list postings already seen on ATS boards.
- Retry policy: exponential backoff on 429/5xx (max 3 tries), skip source on repeated failure and continue; log a per-source status line. Set `timeout=30`. Send `User-Agent: job-search-bot/1.0 (+mailto:<you>)`.
- Cache ATS detection per company for 90 days; cache full job descriptions by job ID indefinitely (they rarely change) and refetch only the list endpoint.
- GitHub Actions: a single `cron: "0 6 * * 1"` job; total runtime target < 10 min; store state in the repo (JSON/SQLite) or in an artifact with `actions/cache`.

### Detecting "remote" and region restrictions per source
- Structured boolean/enum (trust first): Arbeitnow `remote`; Ashby `isRemote`; Lever `workplaceType=="remote"`; Recruitee `remote`/`hybrid`/`on_site`; SmartRecruiters `location.remote`; Workable `location.telecommuting`; BambooHR `isRemote` (unverified); Workday `jobPostingInfo.remoteType`; USAJobs `RemoteIndicator`; Teamtailor RSS remote-status element.
- Structured region list (best for "can I, in the EU, apply?"): Himalayas `locationRestrictions[]` (country names) and `timezoneRestrictions`; Jobicy `jobGeo` / `geo=europe`; Remotive `candidate_required_location`; WWR `region`; RemoteOK `location`; Lever `country` + `categories.allLocations[]`; Ashby `address.postalAddress.addressCountry` + `secondaryLocations[]`; Greenhouse `offices[].location` and `location.name`.
- Free-text normalization (apply to all `location`/`title`/`description` fields): lower-case; match `\bremote\b`, `work from home`, `wfh`, `home[- ]?office`, `telearbeit`, `télétravail`, `distans` (SE), `fully distributed`, `anywhere`. Then extract restriction: `(emea|europe|eu|eea|cet|cest|gmt\s*[+-]\s*\d|uk only|us only|usa only|united states|north america|americas|latam|apac|worldwide|anywhere|global)`; map `us only|united states|north america` -> exclude for an EU candidate; `emea|europe|eu|eea|cet|worldwide|anywhere|global` -> include; `uk only` -> include only if UK work rights; timezone offsets `UTC-1..UTC+3` -> include. Treat "Remote (US)" / "Remote - USA" as US-restricted even though it contains "remote".
- National PES sources (JobTech, France Travail, Arbeitsagentur) are by definition country-scoped; `remote` there means "home office allowed within the country", so tag them `remote_scope=national`.
- Hybrid: Recruitee `hybrid`, Lever `workplaceType=="hybrid"`, Workable `workplace=="hybrid"` (unverified), or text `hybrid` -> tag `hybrid`, exclude from "fully remote" lists unless the office city is acceptable.
- Store three derived columns per posting: `is_remote` (bool), `remote_scope` (`worldwide|europe|emea|country:<ISO>|us|other|unknown`), `work_model` (`remote|hybrid|onsite|unknown`), plus `evidence` (the matched string) so rules can be audited.
