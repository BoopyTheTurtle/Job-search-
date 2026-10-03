# Connector fixtures

One directory per source, named after the connector's registered name.

**Status: synthetic.** Every fixture except where noted below was hand-built from the API
documentation summarised in `docs/inventory/apis-and-feeds.md`, not recorded from a live
response (the build environment could not reach the job-board hosts). Field names and
value shapes follow the docs; the content is invented. Each fixture deliberately contains
one item older than the others (for the `since` tests) and one item with optional fields
missing or empty.

**Replace them with trimmed real responses after the first `manual-smoke` workflow run**
(`.github/workflows/manual-smoke.yml`): download the `out/crawl.jsonl` artifact, fetch the
raw payload of each source once, keep 2–3 items, strip anything personal (recruiter names,
emails), and update the assertions in `tests/sources/test_<source>.py` to match. Only after
that should the source be flipped to `enabled: true` in `config/sources.yaml`.

| Source | File(s) | Origin |
|---|---|---|
| remotive | `remotive/sample.json` | synthetic |
| arbeitnow | `arbeitnow/sample.json`, `arbeitnow/page2.json` | synthetic |
| remoteok | `remoteok/sample.json` | synthetic |
| himalayas | `himalayas/sample.json`, `himalayas/page2.json` | synthetic |
| jobicy | `jobicy/sample.json` | synthetic |
| weworkremotely | `weworkremotely/sample.rss`, `weworkremotely/devops.rss` | synthetic |
| workingnomads | `workingnomads/sample.json` | synthetic |
