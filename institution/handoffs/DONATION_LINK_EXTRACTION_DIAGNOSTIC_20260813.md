# Donation Link Extraction Diagnostic

**Prepared by:** Codex  
**Date:** 2026-08-13  
**Status:** Initial code and operational diagnostic; manual 100-site audit remains pending.

## Executive Finding

The current 16% donation-link coverage cannot be interpreted as a site-availability rate. The legacy daemon is both throughput-constrained and limited to server-rendered homepage HTML. A separate continuous scraper contains a persistence defect: it detects donation-link candidates but only writes `website_status`, discarding those candidates. It should not be restarted as-is because the legacy daemon queues links for deployment, which is outside a diagnostic-only scope.

## Database Snapshot

Counts queried on 2026-08-13 from active registry rows:

| Measure | Count |
|---|---:|
| Active organizations | 1,820,046 |
| Organizations with a website value | 419,404 |
| `website_status = 'ok'` | 81,060 |
| Website value with `website_status IS NULL` | 286,700 |
| Organizations with a `donate_url` value | 70,029 |
| `donate_url_status = 'beta'` | 63,462 |
| `website_status = 'ok'` and no `donate_url` | 62,579 |

There are no rows with the literal status `donate_url_status = 'verified'`; the pipeline uses `beta` for machine-discovered, publish-eligible links. Therefore the correct current claim is **70,029 active organizations have a donation URL value (3.8% of active organizations)**, not a verified-coverage percentage.

## Audit Findings

- Total sites manually audited: `0/100`.
- Reason: no browser-backed manual audit was run in this environment; an automated HTML sample must be labeled separately and cannot substitute for the requested human audit.
- Required next evidence: a stratified 100-site audit recording donate-button presence, stored `donate_url`, and observed URL match.

## Performance Analysis

### Observed daemon design

- Default batch size: `50` organizations.
- Default worker pool: `8`.
- Submission pacing: `0.5s` per organization before load-based adjustment.
- Homepage fetch timeout: `15s`.
- Donation-link verification: `HEAD` then `GET`, each with a `10s` timeout.
- Batch completion timeout: `600s`; unfinished work is abandoned.
- Per-domain spacing: `2s`; appropriate for same-domain politeness but does not improve cross-domain throughput.
- HTML only: `requests` + BeautifulSoup. No JavaScript rendering.
- Charity Navigator fallback: disabled in the daemon because automated extraction is not permitted by its terms.

### Bottleneck assessment

**Mixed: throughput + algorithm coverage.**

1. A slow or nonresponsive homepage occupies one of only eight workers for up to 15 seconds.
2. Each promising donation link adds a second `HEAD` and often a third `GET`; the daemon therefore processes network latency serially within each worker.
3. The extractor only scans homepage anchor text/hrefs and embedded PayPal/Stripe scripts. It misses client-rendered buttons, forms/iframes, donation widgets loaded after interaction, and donation pages reachable from navigation or a second click.
4. The daemon queues results into `link_deployment_queue`, making unattended reactivation unsuitable for a diagnostic or staging-only experiment.
5. `continuous_website_scraper.py` computes `donation_link_candidates` and `has_donation_links` but its write loop persists only `website_status` and `updated_at`. Detected donation candidates are lost after logging.

## Algorithm Review

### Current patterns

Homepage anchors are matched case-insensitively against:

`donate`, `give`, `support`, `sponsor`, `contribution`, `fund`, `help us`, `support us`, `make a gift`.

The verifier accepts a page only after HTTP 200 plus donation-keyword evidence, except selected payment processors which pass on host evidence.

### Coverage gaps

- No JavaScript rendering.
- No iframe/form/action extraction.
- No structured-data or embedded-widget extraction.
- No navigation-page traversal.
- No platform-specific patterns beyond PayPal/Stripe script text.
- No source-separated staging ledger for the daemon's donation results.

## Recommended Acceleration Strategy

### Do not restart the existing daemon unchanged

It should remain stopped until its output is redirected from the deployment queue to an auditable donation-candidate staging table and a sample-based quality gate exists.

### Build a staged, two-pass extractor

1. **Pass A, 8 request starts/sec, 24 in flight:** fetch homepage with robots compliance and record all candidate anchors, forms, iframes, JSON-LD, and known donation-platform embeds.
2. **Pass B, 8 request starts/sec, 24 in flight:** validate only deduplicated donation candidates; do not fetch full pages unless HEAD/status evidence is insufficient.
3. **Escalation sample:** use a small representative sample for browser rendering. Add JavaScript rendering only if the sample shows a material client-rendered gap.
4. **Staging only:** retain source URL, extraction method, evidence text, final URL, HTTP result, and confidence. Promote only under a separately reviewed policy.

### Expected throughput

- Homepage discovery: 5-10 sites/sec is realistic with global request-start capping and bounded concurrency, or approximately 432K-864K attempts/day before domains, robots rules, and errors.
- Candidate validation must be treated separately because it adds requests only for detected donation candidates.
- Accuracy cannot be estimated until the manual/representative audit is complete.

## Risks And Mitigations

| Risk | Mitigation |
|---|---|
| Incorrect donation URL | Stage evidence; do not auto-publish. |
| Burden on nonprofit sites | Respect robots, identify the user agent, use global and per-domain caps. |
| Client-rendered false negatives | Measure with a sample before adopting browser rendering. |
| Existing queue deploys links | Keep legacy daemon stopped; use a separate candidate table. |
| Stale sites | Store live-validation timestamp and retain unavailable results separately. |

## Immediate Handoff To Claude

1. Treat the current `16%` as an incomplete extraction measurement, not proof that 84% of sites lack giving paths.
2. Do not reactivate `scripts/discovery_daemon.py` without redirecting writes away from `link_deployment_queue`.
3. Prioritize a staging-first donation extractor and a 100-site representative audit before committing to browser infrastructure or public claims.
4. Codex can implement the staged extractor once Claude confirms ownership boundaries for the donation-candidate schema and review workflow.

## File Evidence

- `scripts/continuous_website_scraper.py:124-135` constructs donation candidates.
- `scripts/continuous_website_scraper.py:193-205` writes only website status, not donation candidates.
- `scripts/donation_link_pipeline.py:8-11` documents a 200-org Phase 1 limit.
- `scripts/donation_link_pipeline.py:548-760` is the stewardship-aware discovery path; it operates only from already verified websites and performs several network requests per organization.
