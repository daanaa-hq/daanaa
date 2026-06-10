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

## 2026-06-08 — Do NOT overwrite SOI-derived NTEE with BMF NTEE (or rescore on it)
The June BMF disagreed with our existing NTEE1 on 66,569 orgs (45,467 scored). Investigation:
86% of our existing codes came from irs_soi (the 990 filing extract), only 4% of the BMF "new"
codes are Z/unknown, and the letter transitions are scattered with no pattern. Conclusion: this
is IRS-vs-IRS source disagreement (BMF master classification vs 990-filing classification) — the
normal ~3-4% NTEE ambiguity, not real reclassifications or a pipeline bug. Chose to KEEP the
298K NTEE *fills* (empty -> BMF code = pure gain) but HOLD the flips and NOT rescore on them
(would churn ~45K scores by swapping one IRS opinion for another). Rebalancing should be driven
by real data changes (new financials from enrichment), not NTEE source noise. Rejected: blindly
adopting BMF NTEE as "more current" (no evidence it's more correct than the filing code).
If we ever reconcile NTEE, do it with an explicit source-priority rule, not a blind overwrite.

## 2026-06-09 — Sandboxed, snapshot-based droplet deploy (never ship the live DB)
Chose `scripts/safe_deploy_droplet.sh`: snapshot the live DB via SQLite's online `.backup`
API, run `PRAGMA integrity_check` as a hard gate, precompute from the snapshot into a scratch
sandbox (env vars MERIT_DB_PATH / PRECOMPUTE_OUT), disk-guard the droplet BEFORE transfer, then
atomic v0/v1 swap with auto-rollback. Why: the 2026-06-06 corruption came from `gzip`-ing the
live WAL-mode DB file directly (torn snapshot), and the 2026-06-09 lockup came from shipping that
7GB DB to a droplet that doesn't even use SQLite, filling it to 100%. The droplet serves precompute
static files only. Rejected: retiring `sync_db_to_droplet.sh` keeps the live-file gzip path around
(it should be deleted). The new pipeline never disturbs :5000 and never lets corrupt/oversized data reach prod.

## 2026-06-09 — Quantize the semantic index (IVFPQ) to fit the droplet's disk budget
Chose FAISS_PQ=1 (IndexIVFPQ, ~64 bytes/vector) over the current IndexIVFFlat (4KB/vector fp32):
shrinks faiss_index.bin ~60x (6.3G -> ~150-300M), dropping the precompute payload from ~12G to ~5G
so it fits the 33G droplet with room for the atomic v0/v1 backup. Why: an IVFFlat full-precision
index is overkill for "similar orgs" surfacing; PQ recall loss is negligible at this task. Rejected:
resizing the droplet (recurring cost) and dropping semantic search (loses a feature). Revisit M if recall feels off.

## 2026-06-09 — Public display = active + tax-deductible only (exclude IRS-revoked)
Chose to surface only `deductibility=1 AND org_status='active'` (~1.97M of 2.06M) in
precompute browse/orgs. Why: donating to a revoked org is NOT tax-deductible — showing the
96,247 IRS-auto-revoked orgs as donatable would mislead donors (fail-closed per stewardship +
REVOCATION_PROTOCOL). All rows are deductibility=1 & subsection='3', so org_status is the
operative filter. Similar-org links are auto-safe (validated against the filtered set).
Rejected: showing revoked orgs flagged-but-visible (donor-confusion risk; revisit later as a
"status revoked" info page for direct EIN lookups, never in browse).

## 2026-06-09 — API browse filter now also excludes revoked (audit Session 1)
Chose to extend `_DEDUCTIBILITY_FILTER` in daanaa_api.py with `COALESCE(irs_revoked,0)!=1
AND COALESCE(org_status,'')!='revoked'` — the :5000 API was still listing 192,501 revoked
orgs (browse/search/stats/sector-health/fused-search) even after the precompute exclusion
above covered the droplet. Rows stay in registry_enriched untouched (reversible by removing
two clauses); direct /api/organizations/<ein> remains accessible and the donate gate fails
closed independently. Guarded by tests/test_principles.py::test_browse_excludes_revoked_orgs.
Also fixed: test_principles.py pointed at deleted merit_api.py — the deploy-blocking
principle suite had been silently dead since the daanaa_api migration.
Rejected: deleting revoked rows (irreversible; "keep them handy" for a future status page).

## 2026-06-09 — Research dashboard auth removed entirely (audit Session 2)
Chose to delete the passcode/session machinery (RESEARCH_PASSCODE, /api/research/auth,
_check_research_auth, X-Research-Session gates on 8 routes, frontend ResearchAccess.tsx)
rather than harden it. Why: the dashboard serves only aggregate public IRS data, the
frontend reads a static snapshot (/research-snapshot.json) and never even sent the session
header, and the passcode was hardcoded in BOTH backend and frontend bundle — a fake lock.
Also added: _CLAIM_SECRET now refuses to start under DAANAA_PROD without a real secret.
Guarded by test_no_research_passcode_machinery + test_claim_secret_fails_closed_in_prod.
Rejected: env-only passcode + rate limit (built first, then discarded — protecting public
data with a secret adds operational friction for zero privacy gain; re-gate only if any
non-public field ever lands in these endpoints).

## 2026-06-09 — Fused-search failures degrade, don't alarm (audit Session 3)
Chose: when the fused (semantic) query fails but the keyword query already returned
results, show those results silently; show the error state only when there is nothing
to display. Why: partial degradation beats a scary banner over usable results. Also added
a 10s AbortSignal.timeout to fetchJson (frontend) so a hung backend becomes a readable
error instead of minutes of blank loading. Rejected: always surfacing fused errors
(noise) and per-call timeout overrides (no caller needs one yet — YAGNI).

## 2026-06-09 — Revocation flag derives from the list, sync keeps it current (Session 7)
Chose: backfilled 218,775 NULL irs_revoked rows from revoked_eins (30,713 → 1, rest → 0;
verified no browse leakage existed — org_status caught them all), and sync_irs_revocations
now (a) refuses an IRS file that shrank >20% vs the last load (truncation guard, the list
is append-only) and (b) updates registry_enriched.irs_revoked after every load so the
column the browse filter reads can never drift from the list again. Conservative writes
only: never auto-flips 1→0. Rejected: deriving revocation at query time via JOIN (hot-path
cost on every browse query) and fixing legacy ingest_bmf_master.py (writes an obsolete
table; only referenced by a retired setup script — left for the archive sweep).

## 2026-06-09 — Droplet search: full filter parity + indexed (prod 0-results bug)
Chose: droplet_api now parses comma lists (ntee=R,I / sub=I21,R20) and min/max_revenue,
routing multi-select or revenue queries to the DB path; added (NTEE1,total_revenue),
(total_revenue), (NTEECC) indexes + ANALYZE to droplet_search.db and the rebuild script;
NTEECC uses GLOB not LIKE (case-sensitive → index-driven); ORDER BY uses
COALESCE(merit_score,-1) DESC instead of NULLS LAST (stops SQLite walking the score
index probing the filter row-by-row: 6s → 0.2s). Guarded by tests/test_droplet_search.py.
Why: production directory showed "0 results" for any category combo and silently ignored
revenue bands — silent wrong results are a trust violation, and speed is part of accuracy.
Rejected: proxying filters to the home API (droplet must stand alone) and two-step rowid
pagination (measured slower than the straight query).

## 2026-06-09 — Withheld donate links on 73 revoked orgs (stewardship audit catch)
The new weekly stewardship audit agent (scripts/agents/stewardship_audit.py) found 73
IRS-revoked orgs still carrying donate_url_status values like beta/dead/human_review.
None were 'verified', but fail-closed means withheld outright. Set status='withheld' on
all 73 (reversible — pipeline re-discovers links if an org is reinstated). Also deduped
crontab (6 agent jobs were scheduled twice, running 2x daily) and added T5 traction-brief
+ T7 stewardship-audit weekly agents per TEAMS_AND_MILESTONES.md. Rejected: leaving the
links visible-but-flagged (donor-confusion risk, violates 2026-06-09 fail-closed decision).

## 2026-06-10 — Nightly enrichment: align to gpu_night.sh, not a new orchestrator
- **Chose:** `gpu_night.sh` stays the single nightly orchestrator; added `web_night.sh` (website discovery loop) as its third worker; deleted the 4 new `nightly_*` scripts written earlier the same day.
- **Why:** gpu_night.sh already launches missions + donate-link loop + reembed watchdog; the new orchestrator duplicated all of it, and its stubs used nonexistent columns (`ntee1`, `data_is_stale`) and a wrong `--batch` flag — it would have crashed on first cron fire.
- **Rejected:** keeping both (double work, two sources of truth), Python rewrite of gpu_night.sh (working bash, no need).

## 2026-06-10 — web_finder marks failures; finds published as 'beta'
- **Chose:** failed attempts set `website_status='no_website_found'` + `website_checked_at` (90-day retry window); verified finds set `website_status='beta'` not `'ok'`.
- **Why:** without a tried-marker every nightly pass re-processed the same top-revenue failures forever; 'beta' per the web-discovery disclosure policy (heuristic + embedding match, no human review).

## 2026-06-10 — Mission model upgrade candidate: Qwen3-30B-A3B-Instruct-2507 (MoE)
- **Chose:** download standalone Q4_K_M GGUF (not an ollama-blob symlink — ollama GC broke the 14B that way); benchmark vs Qwen2.5-32B before swapping gpu_night.sh MODEL.
- **Why:** ~5x throughput (MoE A3B ≈146 tok/s vs dense 32B) on 1–2 sentence missions; quality gate first per stewardship (no silent degradation).

## 2026-06-10: Generic platform donate URLs fail closed at release
**Chose:** Regex guard in Phase 2 release rejecting platform landing pages with no org identifier (`paypal.com/donate`, `donorbox.org/widget(s)`, `givebutter.com/embed|latest`, bare `venmo.com`, `crm.bloomerang.co/HostedDonation`) → `human_review`; pulled 46 already-published ones back from `beta`.
**Why:** Phase 1 scored these at confidence 90 and the HEAD check passes (the generic page is alive), so they published — a false trust signal pointing donors at PayPal's homepage, not the org. Fail-closed beats fixing only upstream scoring.
**Rejected:** Deleting the URLs (they're evidence for human review); fixing only Phase 1 confidence (release is the last gate — it must be safe regardless).

## 2026-06-10: web_finder verification = name-token gate + embedding floor
**Chose:** Primary gate ≥70% of meaningful org-name tokens present on the page; embedding similarity ≥0.5 as a secondary floor (was: similarity ≥0.85 alone).
**Why:** Name-string vs homepage-HTML cosine peaks ~0.7 — the 0.85 bar was mathematically unreachable (0 verified in 1,800 attempts). Token containment is deterministic and explainable from public data.
**Rejected:** Just lowering the threshold to 0.6 (would admit squatter/wrong-org pages scoring 0.6+ on topic alone).

## 2026-06-10: Qwen3-30B-A3B MoE is the nightly mission model
**Chose:** Switched gpu_night.sh :11437 model to Qwen3-30B-A3B-Instruct-2507 Q4_K_M (MoE, 3B active params) and chained generate_missions_irs_bmf.py after generate_missions.py.
**Why:** Supervised run wrote 11,252 EIN-validated missions at ~7 orgs/sec with 0 write errors; dense 32B does ~1.5/sec. Quality spot-checks passed (active voice, correct org, correct sector).
**Rejected:** Staying on dense 32B (245K backlog would take ~2 weeks of nights vs ~2 nights).

## 2026-06-10: Generic platform URLs deducted at scoring time, not just blocked at release
**Chose:** `generic_platform_url` factor (−40) in `score_confidence`, applied at all three scoring sites (Phase 0 audit, subdomain probe, Phase 1 main). Regex moved next to the scorer; the Phase 2 release guard stays as the last gate.
**Why:** Root cause of the 46-link incident — no factor asked "does this URL identify the org?", so `paypal.com/donate` scored 90. With −40 a generic URL caps at 65 even with every positive factor: below publish (90) and review (75) bands.
**Rejected:** Regex-rejecting candidates before scoring (loses the evidence trail in donation_link_evidence; scoring + deduction keeps the decision explainable).

## 2026-06-10: web_finder identifies itself + respects robots.txt (own copy of can_fetch)
**Chose:** DaanaaWebFinder/1.0 UA on all fetches, RobotFileParser cache (fails open), honest docstring (domain-pattern guessing — there is no search engine), dead `find_donation_links()` deleted.
**Why:** Stewardship rule 1 (no robots bypass) was claimed in the docstring but not implemented; default python-requests UA hides who we are.
**Rejected:** Importing `can_fetch` from donation_link_pipeline (pulls that module's heavier deps and module-level state into a script that needs 15 lines).

## 2026-06-10: GPU-queue track retired (3 cron jobs removed, scripts archived)
**Chose:** Removed crontab entries for gpu_queue_manager.py (*/4), phase4_completion_monitor.py (hourly), gpu_workload_pusher.py (*/15); archived all three to archive/gpu_queue_track_20260610/.
**Why:** All three were broken (two crashed on missing psutil — 1,446 tracebacks; the pusher used `source` under cron's /bin/sh and never ran once). Had they worked, they'd have spawned the legacy mission_generation_pipeline.py against gpu_night's GPU with no already-running check. gpu_night.sh is the single nightly orchestrator (T1 doc); cause tags stay covered by the 02:35 agent.
**Rejected:** Installing psutil to "fix" them (would activate an unaudited duplicate orchestrator mid-consolidation).

## 2026-06-10: Credential scrub v2 — surgical index-filter, not filter-repo
**Chose:** git filter-branch --index-filter swapping only the 2 dirty blobs (batch_import.py, daily_sync.sh) for redacted ones, across all 502 commits incl. backup branches.
**Why:** git-filter-repo --replace-text OOM-crashed ("stream ends early") loading the 6.5GB FAISS blobs on a 30GB-RAM box; index-filter never streams blob contents. Full pre-scrub bundle at ~/daanaa_prescrub_20260610.bundle.
**Rejected:** filter-repo with more swap (slow, still risky); tree-filter (stomps the working tree — 2026-06-10 lesson).
