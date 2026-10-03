# Job-search websites by country: access inventory

Date: 2026-10-03. Purpose: which boards a personal job-search bot can read, and how.

Conventions
- Type: GB = general board, IT = IT-specialist board, PES = public employment service, AGG = aggregator.
- Access: Public API (self-serve, free or no key) / Partner API (key or contract) / RSS-XML / HTML only (incl. undocumented internal JSON used by the site's own front end).
- Scraping stance: ToS forbids / robots disallows / unclear / permissive. "unverified" = not confirmed by a source during this research. Direct robots.txt fetches of indeed.com, linkedin.com, stepstone.de, seek.com.au and pracuj.pl were blocked from this environment, so robots entries for those are unverified.
- "Internal JSON" means a browser-facing endpoint that third-party scrapers use; it is not a licence to use it. Treat as HTML-only legally.

Cross-border sources (apply to several countries below)

| Site | Type | Access | Scraping stance | Notes |
|---|---|---|---|---|
| EURES (eures.europa.eu) | PES (EU-wide) | HTML only + undocumented `jv-search` REST endpoint | unclear | Aggregates PES vacancies from 31 EU/EEA+CH countries; many postings in English; no formal public API docs found (unverified). Members/partners exchange data via the EURES single coordinated channel (contract). |
| Adzuna (adzuna.com) | AGG | Public API (free key, ~1,000 calls/mo) | permissive via API | ~16-19 countries incl. UK, US, DE, FR, AT, NL, BE, IT, ES, PL, CH, AU, NZ, CA. Docs: https://developer.adzuna.com. Remote filter via keyword only. |
| Jooble (jooble.org) | AGG | Public API (free key on request) | permissive via API | 60+ countries incl. all countries in this file. POST https://jooble.org/api/{key}. Snippets + outbound link only. |
| Careerjet (careerjet.com) | AGG | Public API (free affiliate key, v4 basic-auth) | permissive via API | ~70 markets. Requires end-user IP/UA/referrer on each call, i.e. designed for live sites, not batch crawling. |
| LinkedIn Jobs | GB | none | ToS forbids; robots.txt bars bots without permission | User Agreement bans scrapers/bots; no job-read API for individuals. Off-limits. |
| Indeed (all country sites) | GB/AGG | none (Publisher API shut 2023) | ToS forbids | Largest traffic in most countries below; automated access prohibited. Off-limits except via licensed resellers. |
| Glassdoor | GB | none (public API retired 2021-22) | ToS forbids (unverified text) | Off-limits. |
| Arbeitnow (arbeitnow.com) | AGG (Europe/remote) | Public API, no key | permissive | GET https://www.arbeitnow.com/api/job-board-api ; English, remote + visa-sponsorship flags; ATS-sourced (Greenhouse, SmartRecruiters, etc.). |
| Remotive (remotive.com) | AGG (remote) | Public API, no key | permissive with limits | https://remotive.com/api/remote-jobs ; max ~4 fetches/day, attribution required. |
| RemoteOK (remoteok.com) | AGG (remote) | Public API/feed, no key | permissive with attribution | https://remoteok.com/api ; link back required. |
| Himalayas (himalayas.app) | AGG (remote) | Public API, no key | permissive | Documented JSON API; filters for country/timezone. |
| Welcome to the Jungle (incl. Otta) | GB | Partner API (contact support) | unclear | FR/UK/ES/CZ/SK; many English tech postings; no self-serve read API. |

---

## EU/EEA region summary

Public employment services are the best legal entry points: Sweden (JobTech JobSearch/JobStream, open), France (France Travail Offres d'emploi v2, free OAuth2), Norway (NAV pam-stilling-feed, free token), Germany (Bundesagentur Jobsuche, undocumented but stable key `jobboerse-jobsuche`), and Finland/Belgium (partner REST APIs on application). Denmark, Estonia, Latvia, Czechia, Austria and Switzerland expose internal JSON search endpoints without published terms. Most other PES portals (PL, ES, IT, PT, GR, HU, RO, BG, HR, SI, SK, LT, LU, MT, CY, IE) are HTML only. Among commercial boards, almost all leaders (Indeed, LinkedIn, StepStone, pracuj.pl, InfoJobs without key, Finn, Jobindex) forbid or do not sanction scraping; usable exceptions are Arbeitnow, Adzuna, Jooble, Careerjet, InfoJobs (free developer key) and the remote boards. EURES is the one EU-wide PES mirror with English-language coverage but lacks published API terms.

## Austria

| Site | Type | Access | Scraping stance | Notes |
|---|---|---|---|---|
| karriere.at | GB | HTML only | unclear (unverified) | Market leader; German; Homeoffice filter on site. |
| StepStone.at | GB | HTML only | ToS forbids (Nutzungsbedingungen; unverified wording) | German; remote filter on site. |
| willhaben Jobs | GB | HTML only | unclear (unverified) | Classifieds-based; German. |
| devjobs.at | IT | HTML only | unclear (unverified) | Austrian dev board; some English. |
| AMS "alle jobs" / eJob-Room (jobs.ams.at) | PES | HTML only (internal search/detail API with HMAC-SHA512 signing; undocumented) | unclear | No published public API found. Data also flows to EURES. |
| Adzuna AT, Jooble AT | AGG | Public API | permissive via API | See cross-border table. |

## Belgium

| Site | Type | Access | Scraping stance | Notes |
|---|---|---|---|---|
| Indeed.be | GB | none | ToS forbids | Off-limits. |
| StepStone.be | GB | HTML only | ToS forbids (unverified wording) | NL/FR/EN UI. |
| Jobat.be | GB | HTML only | unclear (unverified) | NL/FR. |
| ICTjob.be | IT | HTML only | unclear (unverified) | IT-only board; many English postings. |
| VDAB (vdab.be, Flanders) | PES | Partner API (developer.vdab.be/openservices; access agreement) | unclear for HTML | Vacancies API: `GET vacatures/bulk`, `GET vacatures/{id}`. Largest Flemish source; English postings uncommon. |
| Le Forem (leforem.be, Wallonia) | PES | HTML only (unverified) | unclear | French. |
| Actiris (actiris.brussels) | PES | HTML only (unverified) | unclear | FR/NL; Brussels. |

## Bulgaria

| Site | Type | Access | Scraping stance | Notes |
|---|---|---|---|---|
| jobs.bg | GB | HTML only | unclear (unverified) | Market leader; Bulgarian with English IT postings. |
| zaplata.bg | GB | HTML only | unclear (unverified) | Bulgarian. |
| dev.bg | IT | HTML only | unclear (unverified) | Dev community board; remote filter; many English postings. |
| Agency for Employment (az.government.bg) | PES | HTML only | unclear | Bulgarian; no API found (unverified). |

## Croatia

| Site | Type | Access | Scraping stance | Notes |
|---|---|---|---|---|
| MojPosao.net | GB | HTML only | unclear (unverified) | Market leader; Croatian. |
| Posao.hr | GB | HTML only | unclear (unverified) | Croatian. |
| HZZ Burza rada (burzarada.hzz.hr) | PES | HTML only | unclear | ~16k open positions; no API or open data for live vacancies found. |

## Cyprus

| Site | Type | Access | Scraping stance | Notes |
|---|---|---|---|---|
| ergodotisi.com | GB | HTML only | unclear (unverified) | Greek/English. |
| Carierista.com | GB | HTML only | unclear (unverified) | English common. |
| PES Portal (pescps.dl.mlsi.gov.cy) | PES | HTML only (unverified) | unclear | Greek/English; EURES mirror is the easier route. |

## Czechia

| Site | Type | Access | Scraping stance | Notes |
|---|---|---|---|---|
| Jobs.cz (LMC/Alma Career) | GB | HTML only | ToS forbids (unverified wording) | Market leader; Czech, some English. |
| Prace.cz (LMC) | GB | HTML only | ToS forbids (unverified wording) | Czech. |
| StartupJobs.cz | IT | HTML only | unclear (unverified) | Startup/tech; remote filter; some English. |
| Úřad práce ČR (uradprace.cz / MPSV portal) | PES | HTML only (internal JSON search API); MPSV documents XML/HTML increments of vacancies for public access | unclear | Open data (monthly stats) since Jan 2025; employers legally report vacancies, so coverage is broad. Czech only. |

## Denmark

| Site | Type | Access | Scraping stance | Notes |
|---|---|---|---|---|
| Jobindex.dk | GB/AGG | HTML only | unclear (robots/ToS unverified) | Market leader; Danish; receives Jobnet jobs via webservice. |
| Ofir.dk | GB | HTML only | unclear (unverified) | Danish. |
| it-jobbank.dk (Jobindex) | IT | HTML only | unclear (unverified) | Danish IT board. |
| The Hub (thehub.io) | IT/startup | HTML only (no public API found; unverified) | unclear | Nordic startup jobs; English dominant; remote filter. |
| Jobnet.dk (STAR) | PES | HTML only (internal public JSON search API, no login); STAR distributes all ads to job banks via webservice (partner) | unclear | No published API terms found; Danish. |

## Estonia

| Site | Type | Access | Scraping stance | Notes |
|---|---|---|---|---|
| CV.ee (Alma Career) | GB | HTML only | unclear (unverified) | Market leader; ET/EN/RU. |
| CV Keskus (cvkeskus.ee) | GB | HTML only | unclear (unverified) | ET/EN/RU. |
| MeetFrank | IT | HTML only (app-first) | unclear (unverified) | Baltic tech; English. |
| Töötukassa (tootukassa.ee) | PES | HTML only (internal public search JSON API; remote flag present) | unclear | English UI available; no official API docs found. |

## Finland

| Site | Type | Access | Scraping stance | Notes |
|---|---|---|---|---|
| Duunitori.fi | GB/AGG | HTML only | unclear (unverified) | Market leader; Finnish, English filter available. |
| Oikotie Työpaikat | GB | HTML only | unclear (unverified) | Finnish. |
| The Hub (thehub.io) | IT/startup | HTML only | unclear | English; Helsinki startups. |
| Työmarkkinatori (tyomarkkinatori.fi, KEHA) | PES | Partner API (REST retrieval interface; credentials via activation form tied to a business ID) | unclear for HTML | Terms: https://tyomarkkinatori.fi/en/info/kehittajille/tyopaikkailmoitusten-rajapinnat ; ESCO-coded; feeds EURES. English UI; postings mostly Finnish. |

## France

| Site | Type | Access | Scraping stance | Notes |
|---|---|---|---|---|
| Indeed.fr | GB | none | ToS forbids | Off-limits. |
| HelloWork | GB | HTML only | ToS forbids (unverified wording) | French. |
| Welcome to the Jungle | GB/IT | Partner API | unclear | Tech-heavy; some English. |
| APEC (apec.fr) | GB (executives) | HTML only (unverified) | unclear | French; cadre roles incl. IT. |
| France Travail (francetravail.fr) | PES | Public API (free account at https://francetravail.io, OAuth2 client credentials; "Offres d'emploi v2") | n/a for API; HTML scraping unnecessary | 1,150-result cap per query; ROME taxonomy; reuse licence requires displaying full offer incl. logo. French; remote filter unverified. |

## Germany

| Site | Type | Access | Scraping stance | Notes |
|---|---|---|---|---|
| StepStone.de | GB | HTML only | ToS forbids (Nutzungsbedingungen; wording unverified); robots unverified | Largest paid board; German; Homeoffice filter. |
| Indeed.de | GB | none | ToS forbids | Off-limits. |
| XING Jobs (onlyfy) | GB | HTML only | ToS forbids (unverified) | German. |
| LinkedIn.de | GB | none | ToS forbids | Off-limits. |
| honeypot.io | IT | none (reverse marketplace; companies apply to you) | n/a | No listings to crawl. |
| germantechjobs.de | IT | HTML only | unclear (unverified) | English-language tech board; remote filter. |
| Arbeitnow | IT/AGG | Public API | permissive | Berlin-based; see cross-border table. |
| Bundesagentur für Arbeit Jobsuche (arbeitsagentur.de/jobsuche) | PES | HTML only officially; de-facto open JSON API `https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v6/jobs` with header `X-API-Key: jobboerse-jobsuche` (unofficial docs: https://github.com/bundesAPI/jobsuche-api) | unclear (no official licence; widely used) | Largest German database; German; filter `arbeitszeit=ho` for home office. |

## Greece

| Site | Type | Access | Scraping stance | Notes |
|---|---|---|---|---|
| kariera.gr | GB | HTML only | unclear (unverified) | Greek/English. |
| Skywalker.gr | GB | HTML only | unclear (unverified) | Greek. |
| jobfind.gr | GB | HTML only | unclear (unverified) | Greek. |
| DYPA (dypa.gov.gr; HotJobs platform) | PES | HTML only | unclear | Greek; no API found. |

## Hungary

| Site | Type | Access | Scraping stance | Notes |
|---|---|---|---|---|
| Profession.hu | GB | HTML only | ToS forbids (unverified wording) | Market leader; Hungarian; English filter. |
| CVOnline.hu (Alma Career) | GB | HTML only | unclear (unverified) | Hungarian. |
| Jobline.hu | GB | HTML only | unclear (unverified) | Hungarian. |
| NFSZ Virtuális Munkaerőpiac Portál (vmp.munka.hu) | PES | HTML only (server-rendered, no JSON API) | unclear | Hungarian. |

## Ireland

| Site | Type | Access | Scraping stance | Notes |
|---|---|---|---|---|
| IrishJobs.ie (StepStone Group) | GB | HTML only | ToS forbids (unverified wording) | English; remote filter. |
| Indeed.ie | GB | none | ToS forbids | Off-limits. |
| Jobs.ie | GB | HTML only | unclear (unverified) | English. |
| JobsIreland.ie (Intreo/DSP) | PES | HTML only | unclear | English; no API or feed found. |
| Adzuna IE (unverified coverage), Jooble IE | AGG | Public API | permissive via API | |

## Italy

| Site | Type | Access | Scraping stance | Notes |
|---|---|---|---|---|
| Indeed.it | GB | none | ToS forbids | Off-limits. |
| InfoJobs.it (Adevinta) | GB | HTML only (Italian site has no developer API found; unverified) | ToS forbids (unverified) | Italian. |
| Subito Lavoro | GB | HTML only | unclear (unverified) | Italian classifieds. |
| LinkedIn.it | GB | none | ToS forbids | Dominant for IT roles; off-limits. |
| Cliclavoro / MyANPAL (cliclavoro.gov.it; ANPAL folded into Ministry of Labour 2024) | PES | HTML only; open-data catalog in csv/xml/json for statistics, not live ads | unclear | Fragmented into regional "Cliclavoro" portals; Italian. |

## Latvia

| Site | Type | Access | Scraping stance | Notes |
|---|---|---|---|---|
| CV.lv (Alma Career) | GB | HTML only | unclear (unverified) | LV/EN/RU. |
| visidarbi.lv | AGG | HTML only | unclear (unverified) | Latvian aggregator. |
| MeetFrank | IT | HTML only | unclear | English. |
| NVA CVVP (cvvp.nva.gov.lv) | PES | HTML only (internal JSON REST API, no login) | unclear | Latvian; no official docs found. |

## Lithuania

| Site | Type | Access | Scraping stance | Notes |
|---|---|---|---|---|
| CVbankas.lt | GB | HTML only | unclear (unverified) | Market leader; Lithuanian. |
| CV.lt / cvonline.lt | GB | HTML only | unclear (unverified) | Lithuanian. |
| MeetFrank | IT | HTML only | unclear | English. |
| Užimtumo tarnyba (uzt.lt) | PES | HTML only (server-rendered, no JSON API) | unclear | Lithuanian; full national inventory. |

## Luxembourg

| Site | Type | Access | Scraping stance | Notes |
|---|---|---|---|---|
| Jobs.lu (StepStone Group) | GB | HTML only | ToS forbids (unverified wording) | FR/EN/DE; English common. |
| Moovijob.com | GB | HTML only | unclear (unverified) | FR/EN. |
| ADEM JobBoard (adem.public.lu) | PES | HTML only; full access requires jobseeker registration (unverified) | unclear | Employers legally must declare vacancies to ADEM; data.public.lu publishes a skills-in-vacancies dataset (not live ads). |

## Malta

| Site | Type | Access | Scraping stance | Notes |
|---|---|---|---|---|
| Keepmeposted.com.mt | GB | HTML only | unclear (unverified) | English. |
| jobsinmalta.com | GB | HTML only | unclear (unverified) | English; iGaming/IT heavy. |
| Jobsplus (jobsplus.gov.mt) | PES | HTML only | unclear | English; no API found. |

## Netherlands

| Site | Type | Access | Scraping stance | Notes |
|---|---|---|---|---|
| Indeed.nl | GB | none | ToS forbids | Off-limits. |
| Nationale Vacaturebank (DPG) | GB | HTML only | ToS forbids (unverified wording) | Dutch. |
| LinkedIn.nl | GB | none | ToS forbids | Dominant for IT; off-limits. |
| Honeypot (NL) | IT | none (reverse marketplace) | n/a | |
| Tweakers Carrière / itbanen.nl | IT | HTML only | unclear (unverified) | Dutch IT boards. |
| UWV werk.nl | PES | HTML only (internal vacancy search API); UWV confirmed no official API and none planned; UWV stated scraping of werk.nl open data is "in principle possible" (data.overheid.nl datarequest) | unclear, leaning permissive | Dutch; large volume incl. aggregated private ads. |

## Poland

| Site | Type | Access | Scraping stance | Notes |
|---|---|---|---|---|
| Pracuj.pl | GB | HTML only | ToS forbids (regulamin; unverified wording); robots unverified | Market leader; Polish; remote filter. |
| OLX Praca | GB | HTML only | ToS forbids (unverified) | Polish. |
| Indeed.pl | GB | none | ToS forbids | Off-limits. |
| justjoin.it | IT | HTML only (no public API; Next.js, hashed classes) | unclear (unverified) | English-friendly; remote filter; salary ranges. |
| nofluffjobs.com | IT | HTML only (internal REST `/api/search/posting`, `/api/posting/{id}`; undocumented) | unclear | PL/HU/CZ/SK/UA/NL; English UI; remote filter. |
| bulldogjob.pl / theprotocol.it (Grupa Pracuj) | IT | HTML only | unclear / ToS forbids (unverified) | Polish IT boards. |
| Centralna Baza Ofert Pracy (oferty.praca.gov.pl) | PES | HTML only | unclear | No API docs found; Polish. |

## Portugal

| Site | Type | Access | Scraping stance | Notes |
|---|---|---|---|---|
| Net-Empregos.com | GB | HTML only | unclear (unverified) | Portuguese. |
| Sapo Emprego | GB | HTML only | unclear (unverified) | Portuguese. |
| Indeed.pt | GB | none | ToS forbids | Off-limits. |
| Landing.jobs | IT | HTML only | unclear (unverified) | Tech; English; remote filter. |
| IEFP iefponline (iefponline.iefp.pt) | PES | HTML only | unclear | Portuguese; no API/open data for live ads found. |

## Romania

| Site | Type | Access | Scraping stance | Notes |
|---|---|---|---|---|
| eJobs.ro | GB | HTML only | ToS forbids (unverified wording) | Market leader; Romanian. |
| BestJobs.eu | GB | HTML only | unclear (unverified) | Romanian/English. |
| Hipo.ro | GB | HTML only | unclear (unverified) | Romanian. |
| ANOFM (anofm.ro) | PES | HTML only (county lists, often PDF) | unclear | Romanian; no API. |

## Slovakia

| Site | Type | Access | Scraping stance | Notes |
|---|---|---|---|---|
| Profesia.sk (Alma Career) | GB | HTML only | ToS forbids (unverified wording) | Market leader; Slovak, English filter. |
| Kariera.sk | GB | HTML only | unclear (unverified) | Slovak. |
| nofluffjobs.com (SK) | IT | HTML only | unclear | English UI. |
| Služby zamestnanosti (sluzbyzamestnanosti.gov.sk; replaced ISTP 2022) | PES | HTML only | unclear | Monthly open-data stats only; Slovak. |

## Slovenia

| Site | Type | Access | Scraping stance | Notes |
|---|---|---|---|---|
| MojeDelo.com | GB | HTML only | unclear (unverified) | Market leader; Slovene. |
| Zaposlitev.net | GB | HTML only | unclear (unverified) | Slovene. |
| ZRSZ (ess.gov.si) | PES | HTML only | unclear | OPSI open-data portal has an API but no live-vacancy dataset found; Slovene. |

## Spain

| Site | Type | Access | Scraping stance | Notes |
|---|---|---|---|---|
| InfoJobs.net (Adevinta) | GB | Partner API, free developer key (https://developer.infojobs.net; REST, 20 results/page, pagination) | ToS forbids scraping (unverified wording) | Market leader; Spanish; remote (teletrabajo) filter. |
| Indeed.es | GB | none | ToS forbids | Off-limits. |
| LinkedIn.es | GB | none | ToS forbids | Off-limits. |
| Tecnoempleo.com | IT | HTML only (RSS feeds historically; unverified) | unclear | Spanish IT board; remote filter. |
| SEPE Empléate (empleate.gob.es) | PES | HTML only | unclear | Open-data portal has statistics, no live-ad API found; aggregates partner portals; Spanish. |

## Sweden

| Site | Type | Access | Scraping stance | Notes |
|---|---|---|---|---|
| Arbetsförmedlingen Platsbanken (arbetsformedlingen.se/platsbanken) | PES | Public API, no key: JobSearch https://jobsearch.api.jobtechdev.se ; JobStream (full change feed) with free key; docs https://jobtechdev.se/en/components/jobsearch | n/a (API is the sanctioned route) | Largest Swedish source; `remote` filter and English-language ads searchable; historical ads dataset also open. |
| LinkedIn.se | GB | none | ToS forbids | Off-limits. |
| Indeed.se | GB | none | ToS forbids | Off-limits. |
| Blocket Jobb | GB | HTML only | unclear (unverified) | Swedish. |
| The Hub (thehub.io) | IT/startup | HTML only | unclear | English; Stockholm startups. |
| Demando / Jobbland (unverified) | IT | HTML only | unclear | Swedish tech boards. |

## United Kingdom + Switzerland (+ Norway, Iceland) summary

The UK is the friendliest commercial market: Reed's Jobseeker API issues free keys self-serve, and Adzuna (UK-founded) gives a free aggregator API; DWP Find a job has no read API. Switzerland's job-room.ch exposes an unauthenticated JSON search endpoint (blocks datacenter IPs) and SECO offers partner APIs; jobs.ch and JobScout24 are HTML with restrictive terms. Norway's NAV pam-stilling-feed is a proper open-data change feed with free registration; Finn.no is the traffic leader but forbids scraping. Iceland has no API source; Alfred.is and Störf.is are HTML only.

## United Kingdom

| Site | Type | Access | Scraping stance | Notes |
|---|---|---|---|---|
| Indeed.co.uk | GB | none | ToS forbids | Off-limits. |
| Reed.co.uk | GB | Public API (free Jobseeker API key, https://www.reed.co.uk/developers; basic auth, key as username; 100 results/page) | n/a (API) | English; remote filter via keyword/location; details endpoint gives full description. |
| Totaljobs / CV-Library | GB | HTML only | ToS forbids (unverified wording) | English. |
| LinkedIn.uk | GB | none | ToS forbids | Off-limits. |
| CWJobs (StepStone) / Technojobs | IT | HTML only | ToS forbids / unclear (unverified) | English IT boards. |
| Otta (Welcome to the Jungle) | IT | Partner API | unclear | Tech/startup; English. |
| Find a job (findajob.dwp.gov.uk, DWP) | PES | HTML only; inbound SFTP feed for publishers only | unclear | English; UK-only roles; RSS availability unverified. |
| Adzuna UK | AGG | Public API | permissive via API | Best UK aggregator route. |

## Switzerland

| Site | Type | Access | Scraping stance | Notes |
|---|---|---|---|---|
| jobs.ch | GB | HTML only | ToS forbids (unverified wording) | Market leader; DE/FR/EN UI; English postings common in IT. |
| JobScout24.ch | GB | HTML only | unclear (unverified) | DE/FR. |
| Indeed.ch | GB | none | ToS forbids | Off-limits. |
| SwissDevJobs.ch | IT | HTML only | unclear (unverified) | English dev board; remote filter. |
| job-room.ch / arbeit.swiss (SECO + RAV) | PES | HTML only officially; public JSON REST search used by the Angular front end (no login); SECO partner API for job boards (contract; details unverified) | unclear | Datacenter/cloud IPs reported blocked; DE/FR/IT/EN. |
| Adzuna CH, Jooble CH | AGG | Public API | permissive via API | |

## Norway

| Site | Type | Access | Scraping stance | Notes |
|---|---|---|---|---|
| Finn.no Jobb | GB | HTML only (partner API for advertisers only) | ToS forbids scraping (unverified wording) | Market leader; Norwegian. |
| Indeed.no | GB | none | ToS forbids | Off-limits. |
| LinkedIn.no | GB | none | ToS forbids | Off-limits. |
| kode24 jobb / The Hub | IT | HTML only | unclear | Norwegian / English. |
| arbeidsplassen.nav.no (NAV) | PES | Public API: pam-stilling-feed, free token after accepting terms at https://arbeidsplassen.nav.no/vilkar-api ; docs https://navikt.github.io/pam-stilling-feed/ ; listed on data.norge.no | n/a (API) | Paginated change feed (not keyword search); ~30k live ads; Norwegian with some English. |

## Iceland

| Site | Type | Access | Scraping stance | Notes |
|---|---|---|---|---|
| Alfred.is | GB | HTML only | unclear (unverified) | Largest board (~1,300 ads); Icelandic + English. |
| Störf.is | AGG | HTML only | unclear (unverified) | "All ads in one place". |
| Starfatorg.is | GB (public sector) | HTML only | unclear | Government jobs. |
| Vinnumálastofnun (vinnumalastofnun.is) | PES | HTML only | unclear | Mainly links to other boards; EURES mirror covers Iceland. |

## Australia + New Zealand summary

SEEK dominates both markets and explicitly offers no read API and treats automated access as against its terms; Indeed and LinkedIn are likewise off-limits. Legal routes are Adzuna AU/NZ, Jooble, Careerjet, and in New Zealand the official Trade Me API (OAuth, rate-limited) which includes a Jobs search method. Workforce Australia (government) has no public API; APS Jobs and jobs.govt.nz are HTML only.

## Australia

| Site | Type | Access | Scraping stance | Notes |
|---|---|---|---|---|
| SEEK (seek.com.au) | GB | none for reading (developer.seek.com is posting/apply only; SEEK states no market-data API will be offered) | ToS forbids automated access | Market leader; English; remote filter on site. |
| Indeed.com.au | GB | none | ToS forbids | Off-limits. |
| Jora (SEEK-owned) | AGG | HTML only | ToS forbids (unverified) | |
| LinkedIn.au | GB | none | ToS forbids | Off-limits. |
| Workforce Australia (workforceaustralia.gov.au, DEWR) | PES | HTML only (internal JSON used by scrapers) | unclear | English; no public API found; data.gov.au has historical vacancy datasets only. |
| APS Jobs (apsjobs.gov.au) | GB (public sector) | HTML only | unclear | Federal public service. |
| Adzuna AU, Jooble AU, Careerjet AU | AGG | Public API | permissive via API | Adzuna AU is the practical remote-IT route. |

## New Zealand

| Site | Type | Access | Scraping stance | Notes |
|---|---|---|---|---|
| SEEK NZ (seek.co.nz) | GB | none for reading | ToS forbids | Market leader. |
| Trade Me Jobs | GB | Public API with OAuth registration: `GET https://api.trademe.co.nz/v1/Search/Jobs.json` (docs https://developer.trademe.co.nz/api-reference/search-methods/jobs-search); rate-limited | n/a (API) | English; category/district/pay filters. |
| Indeed.co.nz | GB | none | ToS forbids | Off-limits. |
| jobs.govt.nz | GB (public sector) | HTML only | unclear | Government roles. |
| Work and Income / MSD "Find a job" (unverified) | PES | HTML only | unclear | Thin IT coverage. |
| Adzuna NZ, Jooble NZ | AGG | Public API | permissive via API | |

## North America summary

The United States has the richest set of sanctioned feeds: USAJOBS (free key), The Muse v2 (no key), CareerOneStop Jobs API (free but approval now routed through the NLx governance board), plus Adzuna/Jooble/Careerjet and the remote boards (Remotive, RemoteOK, Himalayas, Arbeitnow). Indeed, LinkedIn, Glassdoor and ZipRecruiter (ZipSearch API ended March 2025) are all closed to bots. Canada's Job Bank offers only monthly open-data CSVs and an inbound XML feed for publishers; Adzuna CA and Jooble CA are the API routes.

## United States

| Site | Type | Access | Scraping stance | Notes |
|---|---|---|---|---|
| Indeed.com | GB | none | ToS forbids | Off-limits. |
| LinkedIn.com | GB | none | ToS forbids; robots.txt bars bots | Off-limits. |
| ZipRecruiter | GB | none (ZipSearch API deprecated 2025-03-31) | ToS forbids (unverified wording) | Off-limits. |
| Glassdoor | GB | none | ToS forbids | Off-limits. |
| Dice.com | IT | HTML only (RSS historically; unverified) | ToS forbids (unverified wording) | US tech; remote filter. |
| Wellfound (AngelList Talent) | IT | HTML only | ToS forbids (unverified) | Startups; remote filter. |
| Built In | IT | HTML only | unclear (unverified) | City tech hubs + remote. |
| Hacker News "Who is hiring" | IT | Public API (Firebase HN API, no key) | permissive | Monthly thread; English; remote tags in free text. |
| The Muse | GB | Public API v2, optional key (500 req/h without, 3,600 with) | n/a (API) | https://www.themuse.com/developers/api/v2 ; curated US/remote postings. |
| USAJOBS (usajobs.gov, OPM) | PES (federal) | Public API, free key: https://developer.usajobs.gov ; `GET https://data.usajobs.gov/api/search` with Host/User-Agent/Authorization-Key headers | n/a (API) | Federal jobs only; remote/telework filter available. |
| CareerOneStop (DOL) / NLx | PES/AGG | Public API, free key, now approved via NLx Research Hub governance (https://www.careeronestop.org/Developers/WebAPI) | n/a (API) | Pulls National Labor Exchange postings from state job banks; broad coverage. |
| Remotive, RemoteOK, Himalayas, Arbeitnow | AGG (remote) | Public API | permissive | See cross-border table. |
| Adzuna US, Jooble US, Careerjet US | AGG | Public API | permissive via API | |

## Canada

| Site | Type | Access | Scraping stance | Notes |
|---|---|---|---|---|
| Indeed.ca | GB | none | ToS forbids | Off-limits. |
| LinkedIn.ca | GB | none | ToS forbids | Off-limits. |
| Workopolis (now Indeed) / Eluta.ca | GB/AGG | HTML only | ToS forbids / unclear (unverified) | |
| Job Bank (jobbank.gc.ca, ESDC) | PES | HTML only for live search; monthly open-data CSV (EN/FR) at https://open.canada.ca/data/en/dataset/ea639e28-c0fc-48bf-b5dd-b8899bd43072 ; inbound XML feed for job boards (partner); RSS unverified | unclear | EN/FR; remote filter on site. |
| Dice / Built In (CA cities) | IT | HTML only | ToS forbids / unclear | |
| Adzuna CA, Jooble CA, Careerjet CA | AGG | Public API | permissive via API | Practical API routes. |

---

## Recommended first targets

Ranked by legal access x remote/IT coverage x English-language postings.

1. Arbetsförmedlingen JobTech JobSearch + JobStream (SE) - open API, no key for search, remote flag, English ads searchable.
2. France Travail Offres d'emploi v2 (FR) - official free OAuth2 API; honour display licence.
3. NAV pam-stilling-feed (NO) - free token, full change feed.
4. Bundesagentur für Arbeit Jobsuche (DE) - unofficial but stable public endpoint, largest German corpus; keep polite rate.
5. Reed Jobseeker API (UK) - free self-serve key, full descriptions.
6. Adzuna API - one key covers UK, US, DE, FR, AT, NL, BE, IT, ES, PL, CH, AU, NZ, CA (1,000 calls/mo).
7. Jooble API - free key, 60+ countries incl. every country in this file; snippet-level data.
8. Arbeitnow API - no key, English, remote + visa flags, Europe-focused ATS feeds.
9. Remotive + RemoteOK + Himalayas APIs - no key, remote-only English tech roles; respect fetch limits.
10. USAJOBS API (US federal) and The Muse API v2 (US/remote).
11. CareerOneStop/NLx Jobs API (US state job banks) - apply for key.
12. Trade Me Jobs search API (NZ) - OAuth registration.
13. Työmarkkinatori retrieval API (FI) and VDAB vacancies API (BE) - partner credentials on application; worth requesting.
14. EURES portal - EU-wide English coverage; use only after confirming terms (no public API docs found).
15. InfoJobs developer API (ES) - free key; Spanish IT market.

Explicitly avoid: Indeed (all countries), LinkedIn, Glassdoor, ZipRecruiter, SEEK/Jora, StepStone group sites, pracuj.pl, Finn.no, Jobindex - no read API and ToS prohibit bots.
