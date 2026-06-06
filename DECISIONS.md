# DECISIONS.md

Append-only decision log. Each entry: **what we chose and why, plus the option
rejected.** Two lines is enough. Keeps non-obvious choices traceable
(Stewardship principle: significant decisions must be explainable).

---

## 2026-06-01 — Public web serving on a cloud droplet, not the home server
Chose a $8/mo DigitalOcean droplet to serve daanaa.org. Why: the home server sits behind
home NAT (no port forwarding) and shouldn't carry public uptime/heat. Rejected: exposing
the home Ryzen directly (NAT pain, downtime when home internet drops, security surface).

## 2026-06-01 — Lean 1.7GB web DB synced to the droplet, not the full 19GB
Chose to drop ML/pipeline tables (embeddings, raw financials, work queues) before syncing.
Why: 19GB is too slow to ship nightly and the web API never needs embeddings/raw filings.
Rejected: syncing the full DB. The home server keeps the full 19GB for the pipeline.

## 2026-06-01 — Separate daanaa_live.db via ATTACH for user-write data
Chose SQLite ATTACH + bare-name resolution so write tables live in a sync-safe DB. Why:
zero query rewrites (names resolve to the attached DB when absent from the catalog).
Rejected: prefixing 32+ queries with `live.` (error-prone, churny).

## 2026-06-01 — First-party aggregate analytics, not Plausible/Hotjar
Chose tiny first-party event counting (no cookie, no IP, no session record). Why: privacy
invariants + the 1GB droplet can't run Plausible's ClickHouse; Hotjar-style session replay
is surveillance and off-brand. Rejected: any third-party analytics or session recording.

## 2026-06-01 — Cloudflare Flexible SSL + gunicorn on :80 for beta
Chose Flexible SSL (HTTPS to visitor, HTTP Cloudflare→origin on :80). Why: simplest path
to HTTPS with no origin cert management during beta. Rejected (for now): Full(strict) with
an origin cert — REVISIT before any heavy/public launch push for true end-to-end TLS.

## 2026-06-01 — Donate paths: official sources only, or fail closed
Chose to only present a donate path as authoritative when it traces to an OFFICIAL source —
(1) the org confirmed it on claim, (2) an IRS-EIN-keyed authoritative router (Every.org,
PayPal Giving Fund), or (3) a high-confidence donate URL on the org's own verified domain.
Scraped/AI-found links stay "beta"-labeled (never authoritative); revoked/not-in-good-
standing orgs are withheld entirely. Why: protects Daanaa and donors from routing money to
wrong/fraudulent/outdated destinations; aligns with the fail-closed trust posture and
Stewardship "trust signals reflect real data." Key consequence: the EIN router is
official-by-construction (keyed on the authoritative IRS EIN, not a guessed URL), so it's
the SAFEST give path — no need to discover an invisible org's page to give them a protected
one. Rejected: presenting any high-confidence scraped link as a committed donate path.

## 2026-06-04 — Search: fused-mode result count confusion — REVIEW NEEDED
**Issue:** Fused search (semantic + keyword, no filters) caps at RESULT_N=20 with totalPages=1.
When any filter is added, isFusedMode flips false → standard FTS fires → result count jumps from
20 to potentially thousands. Users see "20 results," add a filter, see 1,000+. Confusing.
**Also:** Cold fused search latency is ~1 second (query embedding + 546K vector cosine scan + FTS + RRF).
**Options to review:**
- A) Show "Top 20 smart matches" label + "Show all text results" button in fused mode
- B) Increase RESULT_N to 50 and add pagination to fused results
- C) Make fused mode trigger the standard search simultaneously and show a max count
- D) Cache query embeddings more aggressively to reduce cold latency
**Not fixed yet:** this is a product decision. Logged for review.

## 2026-06-04 — Autonomous event-driven search boosting via agents (fully logged, human-overrideable)
Chose to implement two autonomous agents: (1) Surge Monitor detects search spikes (3x baseline) and classifies
events (hurricane → disaster, unemployment → employment), (2) Outcome Analyzer measures boost effectiveness
(clicks, donations). Boosts are fully auditable, expire after 48h, and can be paused by humans via admin endpoint.
Why: Search by event name (e.g., "hurricane") won't match org names ("Red Cross"); semantic boosting + human oversight
honors principles #3 (evidence-based), #6 (correct mistakes), #9 (explainable), #10 (AI as tool, not replacement).
All agent actions logged to `agent_actions` table; every boost is overrideable via `/api/admin/surge-boosts/<id>/override`.
Event classification rules documented in `EVENT_RULES` and extensible. Crons run hourly (surge) + nightly (outcome analysis).
See `docs/AGENT-SYSTEM.md` for full architecture. Rejected: static search, opaque agent decisions, permanent boosts.

## 2026-06-05 — Dual-column NTEE filtering (NTEE1 single-letter + NTEECC full-code)
Chose to detect category parameter format and filter on NTEE1 (single letter like 'O') or NTEECC (full code like 'O23').
In `organizations_fast()`: if category contains a digit, filter NTEECC; otherwise filter NTEE1. Why: frontend sends
both formats (directory URL `?sub=O23` → NTEECC, search page category toggles → NTEE1). Single endpoint detects intent.
Rejected: separate endpoints for each format, or forcing frontend to always send one format (would require UI changes).

## 2026-06-05 — Pre-computed static results architecture (replaces live database queries)
Chose weekly pre-compute pipeline on home server (Sunday 22:00) that generates: (1) browse results for all 26 NTEE × 50 states combos (~100MB), (2) 1.8M org detail pages with similar orgs (~3.2GB), (3) static content pages homepage/methodology/sector-health/guides/faqs/about/legal (~50MB), (4) FAISS approximate NN index from 1.8M embeddings (~300MB). Total ~3.8GB gzipped delivered to droplet Sunday 23:00, atomically swapped (v1→v0, v2→v1) with zero-downtime rollback. Droplet API serves all files as static JSON (50-200ms vs current 2-10s database queries). Why: (1) Eliminates 19GB database sync bottleneck + embeddings reload on every worker restart, (2) 10-20x faster response times, (3) Static files are cache-friendly and require no query optimization, (4) Weekly update cycle matches nonprofit data change frequency (IRS filings ~annual, org updates ~weekly), (5) Simple rollback: v0 kept for 7 days, (6) Daily claims merge on-the-fly for org detail endpoint. Rejected: keeping live database queries (too slow on droplet), daily full pre-compute (excessive compute, nonprofit data doesn't change that fast), FAISS on every server (300MB resident memory × N workers vs one index file).
