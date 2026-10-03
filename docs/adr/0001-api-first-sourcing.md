# ADR-0001: API and feed first; no scraping of sites that forbid it

Date: 2026-10-03 · Status: Accepted

## Context
The highest-traffic job boards (LinkedIn, Indeed, Glassdoor, StepStone, Xing, Monster)
forbid automated access in their terms and deploy bot detection. Scraping them means
headless browsers, proxies, constant breakage and legal exposure. Meanwhile remote-first
boards, national employment services, aggregators and applicant tracking systems (ATS)
expose public or keyed APIs and feeds that cover most remote, English-language IT roles.

## Decision
Sources are added in this order of preference: public API → keyed partner API → RSS/XML
feed → HTML only where terms and robots.txt permit. Sites whose terms forbid automated
access are out of scope until an official API is available to us. Every source records
its terms link in `config/sources.yaml`.

## Consequences
- Lower coverage of purely local, on-site postings. Acceptable: the target is remote work.
- Connectors are small, stable and testable with recorded fixtures.
- Adding a Tier E (HTML) source requires an explicit terms note and owner approval in the PR.
- The crawler core (`sources`, `normalize`, `enrich`, `store`) is independent of the user
  profile (`filter`, `digest`), so a future multi-user product would not require a rewrite.
