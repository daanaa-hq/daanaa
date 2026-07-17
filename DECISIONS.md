## 2026-07-17 — Autonomy build-out: four board-approved automations shipped

**Chose:** (1) Weekly 990 e-file website expansion (index Sun 01:00, extraction
Sun 05:00) with selection broadened from dead Flame-tier criteria to all
website-less active orgs — 69.5K matched, 41% hit rate on top orgs. (2) Monthly
AI-output sample audit (1st, 06:00) operationalizing the adopted review policy.
(3) Stewardship-archive auto-sync post-commit hook. (4) web_finder LLM candidate
tier (local Qwen) per board diagnosis + contract-drift/terminology tests in the
principle suite.

**Why:** Founder directive "take the lead" on the autonomy audit; all four are
zero-spend, local-hardware, within backend autonomy.

**Rejected:** Automating board simulations via headless Claude sessions —
spends API budget, deferred to founder.

## 2026-07-17 — Decision-making workflow adopted (founder-directed)

**Chose:** Four-gate protocol for all open decisions: (1) principles check vs
STEWARDSHIP.md + Charter, (2) data validation, (3) board simulation every 12h over
the open queue (six seats: Legal, Finance, Marketing, ED, Donor, Stewardship chair),
(4) resolve-and-log or escalate to founder. Queue at governance/DECISION_QUEUE.md;
12h cron check writes .DECISIONS_PENDING marker; protocol at docs/DECISION_WORKFLOW.md.

**Why:** Decisions become data-backed, principle-aligned, and multi-perspective by
default; founder only sees the ones that genuinely need them (split board, principle
tension, missing data). P9 traceability built in.

**Rejected:** Ad-hoc per-decision escalation (noisy, inconsistent documentation).

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

## 2026-07-05: Flask Blueprints for API/SPA routing separation (PENDING IMPLEMENTATION)
**Chose:** Refactor droplet_api.py (8282 lines) into Flask Blueprints: `api_blueprint.py` (all /api/* routes, registered FIRST) and `frontend_blueprint.py` (SPA fallback, registered LAST).
**Why:** The current mixed architecture (8K lines of API routes + SPA fallback in one file) is fragile: easy to accidentally define a route after the SPA fallback, shadowing it. Blueprints enforce deterministic routing by registration order. The recall endpoints exist in code but may not route correctly due to this mixed architecture. Blueprints also improve code clarity and make routing testable. Cost: 1 day refactoring + tests; payoff: safety against future routing bugs and faster feature velocity.
**Implementation:** See ROUTING_FIX_PLAN.md for detailed plan. Refactor script at scripts/refactor_blueprints.py. Tests at tests/test_routing.py (10+ routing safety assertions).
**Rejected:** Quick patch (moving routes around) — doesn't solve the root issue and risks breaking other routes during future edits.

## 2026-06-10: Credential scrub v2 — surgical index-filter, not filter-repo
**Chose:** git filter-branch --index-filter swapping only the 2 dirty blobs (batch_import.py, daily_sync.sh) for redacted ones, across all 502 commits incl. backup branches.
**Why:** git-filter-repo --replace-text OOM-crashed ("stream ends early") loading the 6.5GB FAISS blobs on a 30GB-RAM box; index-filter never streams blob contents. Full pre-scrub bundle at ~/daanaa_prescrub_20260610.bundle.
**Rejected:** filter-repo with more swap (slow, still risky); tree-filter (stomps the working tree — 2026-06-10 lesson).

## 2026-06-10: Org-identifying PayPal URLs skip the Phase 2 liveness HEAD check
**Chose:** `_PAYPAL_ORG_SPECIFIC_RE` — hosted_button_id (≥8 chars), fundraiser/charity/N, ncp/payment, paypal.me handles — skips the final HEAD check in phase2_release_batch. Ephemeral `?token=` forms excluded (they expire). Swept the 12 stuck hosted_button_id links (conf ≥90) from human_review back to pending_review so tonight's Phase 2 publishes them through the normal path.
**Why:** PayPal 403/429s bot HEAD checks — that's rate limiting, not evidence a link is dead. The URL itself names a specific recipient, and Phase 1 only reaches ≥90 after finding the link on the org's own site. The nightly re-checks were also themselves hammering PayPal (stewardship rule: respect rate limits).
**Rejected:** Switching to a lightweight GET (still rate-limited, still hits PayPal nightly); publishing the 12 directly to beta (bypasses Phase 2's audit logging).

## 2026-06-10: website column canonical form — bare lowercase host, http:// kept as signal
**Chose:** One shared normalizer (`scripts/website_normalize.py`, 13 tests): bare lowercase host[/path]; https:// dropped (every consumer already prepends it when absent); http:// kept (forcing https on http-only sites breaks the link); mangled/typo'd schemes repaired (HTTPS:WWW., htpps://, ttps://, http;//, doubled schemes — all real IRS-sourced values); junk → NULL. One-time backfill normalized 51,962 of 116,494 rows (0 lost — every malformed value was recoverable); originals in `website_normalize_backup_20260610`. Wired into all active writers: web_finder_agent, overnight_pipeline submissions, expand_990_coverage, backfill_stubs (both phases).
**Why:** Five writers, five formats (37,720 CAPS rows from IRS 990s, 17,800 scheme-prefixed, 10,798 trailing slashes, 200+ typo'd schemes) — joins/dedup on website silently mismatched, and the soup re-accumulated nightly.
**Rejected:** Full https:// URLs as canonical (loses the http-only signal, fights the 85% bare majority web_finder already writes); normalizing in each writer separately (that's how the soup happened).

## 2026-06-10: 23:00 web-discovery orchestrator retired (never ran once; Phase 3 violated fail-closed gate)
**Chose:** Removed the 23:00 cron line; archived nightly_web_discovery_orchestrator.py + donation_link_extractor.py to archive/web_discovery_orchestrator_20260610/. verify_web_candidates.py and run_phase4.sh stay as manual tools.
**Why:** The cron line used `source` under cron's /bin/sh — it never executed once (zero log files). Had it been "fixed": (a) Phase 4 would contend with gpu_night's GPU at 23:00, and (b) donation_link_extractor writes donate links at confidence 85 with status='beta', which the API publishes without re-checking confidence — a latent breach of the fail-closed ≥90 rule. Donate links flow only through donation_link_pipeline. This resolves review item #7: the two tracks can't conflict because one was never alive; now it can't be accidentally revived.
**Rejected:** Fixing the cron line (activates an unaudited duplicate of what gpu_night's web_night/cpu_night already do, plus the confidence-85 hazard).

## 2026-06-10: Purged 4 oversized generated artifacts from git history (second index-filter pass)
**Chose:** `git filter-branch --index-filter` stripping `precompute_output/faiss_index_dm.bin` (6.7GB), `precompute_output/faiss_index.bin` (6.7GB old / 134MB current), `precompute_output/search.db` (210MB), `precompute_archive/precompute_20260606.tar.gz` (6.5GB) from all 508 commits; added them to .gitignore. Pre-purge bundle at ~/daanaa_prepurge_20260610.bundle. .git shrank 21GB → 2.6GB.
**Why:** The approved force-push of the credential-scrubbed history failed (HTTP 500) — GitHub hard-rejects files over 100MB, and these generated artifacts had been committed after the Jun 4 push. All four are rebuilt by build_faiss_index.py / precompute scripts; the working copies stay on disk.
**Rejected:** Git LFS (recurring cost for derived data nobody needs versioned); fresh orphan repo (loses 508 commits of history and the just-finished credential scrub).

## 2026-06-10: Public donation CTAs removed sitewide — yellow CTA now links to the official website (legal counsel)
**Chose:** Donate fields stripped at the `_strip_scores` serialization choke point in daanaa_api.py (covers every public org payload, including `SELECT *` routes) and at `_strip_donate` in droplet_api.py (also scrubs not-yet-regenerated static org files). New `frontend/src/utils/externalLink.ts` `getPrimaryExternalLink()` is the single source for the public CTA: org website (status ok/beta) normalized to safe http(s), else nothing — profile pages keep a quiet ProPublica "View public record" text link. Give-flow retired (GiveConfirmPrompt deleted, /api/handoff beacon and pendingGive machinery removed); SupportIntent keeps volunteer-only; `direct_link` filter removed from both APIs and the UI; donate fields no longer emitted by precompute_orgs/precompute_browse. Claim flow (`/api/claim/*`, OrgClaimEditor), admin routes, DB schema, and donation_link_pipeline untouched. Guarded by tests/test_no_public_donation_fields.py.
**Why:** Counsel: Daanaa is a discovery platform, not a donation/fundraising platform — public surfaces must carry no donation links or CTAs. Choke-point stripping beats per-route edits because new/forgotten routes fail safe. Social fallback skipped: no social link data exists anywhere in the system (owner decision, 2026-06-10).
**Rejected:** Per-route field removal only (leaks via SELECT *); deleting donate data (needed for the claim flow, where nonprofits confirm their own links); social-media fallback branch (dead code until claiming collects socials).

## 2026-06-11: Claim flow Phase 1 = phone verification; postal letters gated behind LOB_API_KEY + street address
**Chose:** /api/claim/start now requires role/title, a phone number (10+ digits), and BOTH attestation checkboxes server-side; the claim stays `pending` and the admin gets a Gmail notification (via the email_agent OAuth token) carrying everything needed for the verification call, including the PIN. The Lob letter path only fires when LOB_API_KEY is set AND the org has a street_address (Phase 2). Attestation text is versioned (`CLAIM_ATTESTATION_VERSION`, full text in docs/CLAIM-ATTESTATIONS.md) and every claim stores `attested_at` + `attestation_version` for audit. A plain-language "Before you sign" disclosure (who we are, what we store, why) sits above the checkboxes — informed consent, per stewardship P3/P9.
**Why:** First ~20 orgs are verified by a personal call (no Lob spend, no review queue); the PIN rides in the notification email because there is no admin endpoint and the admin needs it mid-call — the PIN only unlocks a revocable page editor, low blast radius. Server-side attestation enforcement means the legal gate cannot be bypassed by posting to the API directly.
**Rejected:** Auto-redirecting the form to the PIN page after submit (PIN arrives days later by phone — dead end); building an admin PIN endpoint now (YAGNI for 20 orgs); putting the attestation text only in the React component (unauditable once copy changes).

## 2026-06-11: 45-day re-claim cooldown keyed to revoked_at
**Chose:** A revoked claim blocks new /api/claim/start attempts on that EIN until 45 days after `revoked_at` (403 with an appeal path via orgs@daanaa.org). Pending claims may be re-submitted freely (typo fixes); the 3/hour rate limit handles abuse.
**Why:** The legal review's "45-day cooldown" requirement; revocation is the contested case where a waiting period protects against immediate re-claim by a bad actor. NOTE: the review's exact intent isn't written down anywhere in the repo — if it meant a cooldown on something else (e.g., between any two claim attempts), adjust the `revoked` branch in claim_start.
**Rejected:** Cooling down all re-submissions (punishes orgs fixing a typo'd email).

## 2026-06-11: street_address backfilled into registry_enriched from data/bmf.csv
**Chose:** New `street_address` column, filled by scripts/backfill_street_addresses.py (idempotent, fills NULLs only) — 1,974,830 of 2,064,612 rows (95.7%). The Organization API type renamed `address` → `street_address`.
**Why:** registry_enriched never had a street column, yet claim_start SELECTed `address` — the endpoint 500'd on every call (see LESSONS). BMF is the only street source we hold; Phase 2 Lob letters need it.
**Rejected:** A separate org_addresses table (one more join for one column of catalog data that syncs with the registry anyway).

## 2026-06-11: All platform communication stays within daanaa.org (founder directive)
**Chose:** Claim notifications now send as verify@daanaa.org to orgs@daanaa.org (env-overridable via DAANAA_ADMIN_NOTIFY_EMAIL), using the live Gmail send-as aliases; verified Gmail honors the From header. Fixed dead address support@daanaa.org in ClaimSuccess.tsx → orgs@daanaa.org (support@ is not one of the 9 live aliases and would bounce).
**Why:** Brand and trust consistency — personal Gmail / ecomargins inbox are implementation details that must not appear on either end of platform mail.
**Rejected:** Keeping the personal-Gmail default with daanaa From only (the To address is equally visible in audit trails and forwarding rules).

- 2026-06-12 — Removed WelcomeSlideshow from Layout (founder call during claim-flow ship). Component file kept for possible reuse; rejected per-route hiding as dead complexity once it was off everywhere.

- 2026-06-12 — Claim endpoints on production via reverse-tunnel proxy. Chose: droplet forwards /api/claim/* to a reverse SSH tunnel (home box opens droplet 127.0.0.1:5001 → local :5000; user systemd unit daanaa-claim-tunnel, linger enabled). Why: keeps one source of truth (home registry DB, Gmail sender, admin tooling), no DB or secrets on the droplet, SPA stays same-origin, dead tunnel degrades to 503 on claiming only. Rejected: porting claim endpoints + a second claims DB to the droplet (splits data, ships the Gmail token off-box, and precompute redeploys would clobber profile edits). Tests: tests/test_droplet_claim_proxy.py pins forward/error/503/body-cap behavior.

- 2026-06-12 — Header decluttered: center links cut from six to two (Discover, Claim your page); Methodology/Stewardship/Guides/About are footer-only; "For Nonprofits" renamed "Claim your page" (action over audience language); single beta disclosure (banner only, no β superscripts); unified nav vocabulary across desktop/overlay/bottom nav. Rejected: an About dropdown (depth pages earn no header slot; calm is the brand) and a gold claim button (dial to turn later if claims lag).

- 2026-06-12 — "Support Daanaa" funding path approved: EcoMargins LLC business bank account (Mercury) + Stripe Payment Link. Copy rule: always "support", never "donate", with explicit not-tax-deductible disclosure; placement footer/About only, never near org pages. Keeps P8 intact — donor giving to nonprofits never touches us; supporter funds are a separate stream to the LLC. Rejected: Ko-fi/BuyMeACoffee (consumer framing undercuts the civic posture).

- 2026-06-13 — Cause-cohort financial context approved for the unscored ~79%. Chose: on unscored org pages, show an NTEE-subcategory "typical" (reserves/health), aggregated from the SCORED population in the same NTEE bucket, walled off as "about this cause area, not this org", with sample size N and suppression for thin buckets (N<30); pair with a "claim to show your real numbers" nudge. Why: closes the biggest small-org fairness gap (P4) — unscored orgs currently get a blank financial section — while staying evidence-based (P3) by never implying we know THIS org's finances. Board (plan-ceo-review) picked "cohort-context band" over full P25/P50/P75 distribution (too easily misread as the org's own numbers) and over minimal presence-only (too little value). Rejected: reusing v5 archetype×band benchmarks (archetype assignment REQUIRES financials the unscored lack — needs a new NTEE-code aggregation instead). Not yet built.

## 2026-06-20 — E2E encrypted wallet session key in sessionStorage
**Chose:** Store the raw AES-256 key bytes in `sessionStorage['dw_k']` (cleared on tab close), re-imported as non-extractable `CryptoKey` on each page load. Server stores `{key_hash, ciphertext, iv, salt}` only — cannot decrypt. BIP39 4-word passphrase (2^44 entropy), PBKDF2/310K → dual-HKDF: `encKey` (in-browser only) and `keyHash` (server lookup token, different HKDF info label so server token cannot reconstruct encKey).
**Why:** sessionStorage acceptable for civic giving-intent data under this threat model — the alternative (memory-only key) requires passphrase re-entry on every page reload/navigate, creating severe UX friction. DAANAA_PROD already enforces `script-src 'self'` CSP, restricting XSS attack surface. The key is raw bytes, not the CryptoKey handle, so it can survive page-reload without re-deriving (310K PBKDF2 rounds ≈ 300ms). Intents and EINs are non-financial, non-identity data — not credentials.
**Rejected:** Memory-only key (requires passphrase per navigate); IndexedDB (no clear tab-close semantics); `localStorage` (persists indefinitely, wider XSS window).

## 2026-06-20 — Removed v4Health widget from org-detail; added storageError surface in WalletPage
**Chose:** Remove the v4 "Financial context" sidebar widget from OrganizationDetail entirely; gate the old `financial_context` accordion on `!v5_context`; replace the v4 block with an "About this score →" methodology link. Separately: expose `storageError: 'quota' | null` from WalletContext and show an amber warning banner in WalletPage when quota is exceeded.
**Why:** v4 and v5 context were both rendering, making org pages visually confusing. The v5 V5Context component is the canonical display — v4 should only show for orgs that have neither archetype nor v5 context. The quota warning was logged to console but invisible to users; a banner closes the gap.
**Rejected:** Keeping both rendered with a "Legacy" label (too confusing for donors); a modal for the quota error (overkill — a sticky banner is enough).

## 2026-06-21 — Track 2 Phase 2: Volunteer Reporting + Donor Tools (async exports + templates + insights)

**Chose:** 
1. **Async volunteer hours export** — CSV generation via background job (threading, not Celery/Redis). Jobs tracked in `background_jobs` table with status polling (`/api/nonprofit/background-jobs/{job_id}`). CSV columns: volunteer_name, email, hours, service_date, activity, status, approved_date.
2. **Donor templates** — 5 hardcoded defaults (simple, tax deduction, impact focus, sustaining, corporate) + unlimited custom templates. Customizable via POST/PUT/DELETE to `donor_templates` table. Template variables: {donor_name}, {amount}, {date}, {org_name}. Real-time preview substitution on frontend.
3. **Volunteer Insights dashboard card** — Monthly vs all-time hours, trend indicator (↑/↓/→), top 3 volunteers, status counts. Filters endpoint: `/api/nonprofit/volunteer-hours/summary?period=month|all`.
4. **Two new dashboard cards** on NonprofitDashboardPage: "Volunteer Insights" (emerald) + "Donor Communication" (purple). Keeps existing 3 cards (gold, green, blue).

**Why:**
- Threading avoids Celery/Redis complexity while supporting current nonprofit count (100–200); CSV write to `/tmp` + DB path = fail-safe.
- Hardcoded defaults are a safe baseline (no blank slate problem), custom templates add flexibility without staff overhead.
- Dashboard visibility surfaces volunteer impact at a glance (engagement metric, retention signal). Trend indicator + top volunteers motivate continued volunteering.
- Five components (VolunteerInsightsCard, DonorCommunicationCard, TemplateEditorModal, VolunteerExportButton + Zod schemas) keep code modular; TypeScript interfaces + Zod parsing enforce API contract safety at boundaries.
- All endpoints require Bearer token auth; nonprofit_ein ownership verified on each read/write (prevents cross-org data leakage).
- Tests in `tests/test_nonprofit_endpoints_phase2.py` verify table schema, ranking, and status counting. E2E test suite in checklist form.

**Rejected:**
- Celery + Redis (overengineering for current scale; threading works for <1000 nonprofits, async job count << 1000/day).
- Customer-curated template library (too much moderation overhead; hardcoded defaults + user edits balance safety + flexibility).
- Real-time volunteer dashboards (batch approval workflow is current ED behavior; summary is derivative of existing tables, no schema change needed).
- Storing jobs in memory (ephemeral, restarting API loses all pending/completed jobs; DB is source of truth).
- Frontend-only template variable substitution (solves preview, but API responses still need substituted values for email send — must happen server-side; preview uses same function as API for consistency).

**Files changed:**
- Backend: `nonprofit_portal_endpoints.py` (+8 endpoints, +2 helper functions)
- Database: `data/merit_registry.db` (+2 tables: `background_jobs`, `donor_templates`)
- Frontend: 
  - New: `VolunteerInsightsCard.tsx`, `DonorCommunicationCard.tsx`, `TemplateEditorModal.tsx`, `VolunteerExportButton.tsx`, `lib/schemas.ts`
  - Updated: `NonprofitDashboardPage.tsx` (grid 3→5 cols, import new cards), `VolunteerApproval.tsx` (add export button)
- Tests: `tests/test_nonprofit_endpoints_phase2.py` (9 test classes, schema + ranking + status + template validation)

**Notes:**
- Export CSV headers use sentence case (Volunteer Name, not volunteer_name) for user readability.
- Trend calculation: if `total_hours_previous == 0`, trend_percent defaults to 100 (all growth); trend_direction is 'flat' if ±5% (avoids noise on small changes).
- Default templates stored in code (5 hardcoded), not DB (is_default=1 is reserved for future; defaults returned every call, custom templates queried per org).
- Modal preview in real-time; tabs (name/body/preview) on mobile for space.
- All async jobs timeout after 60s of polling; if incomplete, user sees "Export is taking too long, please try again."

## 2026-06-22 — Merge Guides/FAQ/How-it-works/Methodology into one page

**Chose:** Collapse four overlapping content pages into a single canonical page at
`/methodology` (one flowing page + sticky TOC), folding in the FAQ accordion and the
two methodology-only sections ("what we don't measure", "data limits").

**Why:** `/how-it-works` and `/methodology` duplicated data-sources / peer-context /
lamp-tiers / cadence content and competed for the same keywords (SEO cannibalization).
One strong page > four thin ones. `Guides2.tsx`/`FAQ2.tsx` were already orphaned;
`/guides`,`/faq`,`/learn` already pointed at `Learn`.

**Rejected:** Keeping tabs (worse for SEO/skimming — content hidden); keeping pages
separate (perpetuates duplication).

**SEO infra added (the part that makes the merge worth it):**
- `droplet_api.py` now server-renders title/description/canonical for static content
  routes via `_STATIC_META` (mirrors org-page `_inject_meta`). Previously these pages
  shipped the generic homepage shell + JS-injected meta only — invisible to non-JS
  crawlers/social bots. Added a `<link rel="canonical">` placeholder to `index.html`.
- Legacy paths (`how-it-works`,`learn`,`guides`,`faq`) now return HTTP **301** to
  `/methodology` via `_LEGACY_REDIRECTS` in `serve_spa` (was a client-side `<Navigate>`
  soft redirect; 301 consolidates link equity). Client `<Navigate>` kept as in-app fallback.
- FAQ JSON-LD via `faqPageSchema` (client-side) for rich-result eligibility.
- Removed merged URLs from `public/sitemap.xml`.

Deleted: `HowItWorks.tsx`, `Learn.tsx`, `Guides2.tsx`, `FAQ2.tsx`. Deployed + verified live.

## 2026-06-23 — prod search.db rebuild (org_fts + metro)
- Chose FORWARD-FIX (build search.db carrying `org_fts`) over rolling the API back to
  the `org_search` version: one swap restores search AND ships metro; rollback would
  revert the Jun 22 API fixes and not deliver metro. Rename-backup gives instant revert.
- Built `registry_enriched` with the live db's exact 41 columns (not the full 68 from
  `merit_registry.db`): full copy was 2.0GB and the droplet root is 96% full; parity
  build is 1.7GB and behaves identically (frontend uses the live column set). `metro`
  intentionally lives only in `org_fts` (search), not `registry_enriched`.
- Metro discoverability: `org_fts` now indexes Census CBSA so suburban orgs match under
  their whole metro (e.g. "Boston" → 32,499 incl. Somerville/Cambridge). Crosswalk from
  `scripts/build_metro_crosswalk.py`; stamped by `scripts/backfill_metro.py` (1.53M orgs).

## 2026-06-27 — Two scoring systems coexist on org detail pages (v4 + v5)
`peer_percentile` (v4, NTEECC + revenue band) drives `meritScore` in `adaptOrg` and the
lamp-tier assignment via `getTierFromOrg`. `v5_context.score.percentile` (v5, archetype +
band) is what users see as "Top X% of peer nonprofits" in the hero and V5Context card.
These can differ significantly (e.g. YES Prep: v4=58, v5=36). Chosen: keep v4 for lamp
tier (stable, historically established) and show v5 to users (cleaner archetype model).
Rejected: unifying to v5 for tier assignment — would require re-scoring all lamp tiers and
could shift many orgs' displayed tier mid-session. Track for a future unified scorer pass.

## 2026-06-29 — Public numbers auto-publish with a consistency gate
Chose: a single source of truth for the canonical org filter (`scripts/registry_filters.py`
`DEDUCTIBLE_FILTER` + `canonical_active_count`), imported by `precompute_content.py`,
`export_research_snapshot.py`, and the overnight data-quality gate; a consistency gate
(`check_number_consistency.py`) that asserts DB == homepage.json.gz == research-snapshot.json
before any deploy; and `refresh_public_numbers.sh` wired as Step 12 of `overnight_pipeline.py`
to regenerate → gate → deploy → restart → verify nightly (full auto-deploy, user-approved).
Why: the headline count drifted across pages (1.7M/1.8M/1.87M) and the deployed
homepage.json.gz went stale because nothing regenerated/redeployed it after re-scoring.
Rejected: a guarded "regenerate + notify, deploy by hand" flow — relies on remembering;
the consistency gate makes auto-deploy safe (drift aborts the deploy, old files stay live).

## 2026-07-01 — E5 "Open to volunteers" filter as coming-soon (not live)
Chose: non-interactive dashed "Soon" badge instead of an active filter.
Why: `org_claims` is excluded from `search.db` for privacy (sync_db.sh), so the filter returns 0 results on production. A silent 0-result state is worse UX than a clear "coming soon" signal.
Rejected: routing the filter through the home-server tunnel — adds latency + couples the droplet to the tunnel for a feature with no data yet.

## 2026-07-01 — E6 ProPublica client-side fetch for 990 Part VII leadership
Chose: client-side browser fetch from the ProPublica public API (`/api/v2/organizations/${ein}.json`) for leadership names, titles, and compensation.
Why: ProPublica's API is explicitly public and CORS-enabled; this avoids proxying third-party data through our own server; compensation is IRS-mandated public disclosure (990 Part VII); citation + filing year shown in attribution line per P3.
Rejected: server-side proxying — adds a dependency and latency; rejected scraping — fragile and rate-limited; rejected omitting compensation — donors legitimately use this to assess org governance and value alignment.

## 2026-07-01 — Parallel sprint agents use isolated worktrees
Chose: isolated git worktrees per agent, merge files manually into main repo after all agents complete.
Why: no merge conflicts between E2/E5/E6+E7 (different files); parallel execution saves time.
Rejected: sequential single-agent — slower; rejected shared worktree — collision risk on concurrent writes.

## 2026-07-02 — "Use my location" button uses Nominatim reverse geocode
Chose: browser Geolocation API → Nominatim (OpenStreetMap) reverse geocode → extract city + state_code → populate the near text field. Coordinates go to Nominatim, never to daanaa.org.
Why: stewardship P2 constraint (documented in STEWARDSHIP.md 2026-07-01 entry) prohibits raw browser coordinates from reaching our server. Nominatim is privacy-respecting, free, and CORS-enabled. Result is city+state ("Portland, OR"), which is the format our haversine radius search already accepts.
Rejected: reverse geocode on our server — violates P2 constraint; rejected browser zip-code lookup (no such API exists natively); rejected skipping the button entirely — friction reduction for local searches improves utility for donors.

## 2026-07-04 — Neutral default sort: name A-Z everywhere, score is opt-in only
Chose: organization_name ASC as the default sort in Directory.tsx, daanaa_api.py browse, droplet_api.py `_order_clause` + `_merge_orgs`, and precompute_browse.py ORDER BY. Peer Financial Context remains available as an explicit dropdown choice.
Why: 2026-07-03 audit found the merit_score default quietly contradicted the "no ranking" posture (STEWARDSHIP P7/P5) — browse pages implied a best-to-worst verdict. Approved by founder 2026-07-04.
Rejected: removing the score sort entirely — donors who want peer context should still get it, it just cannot be the unasked-for default. Note: existing precompute browse files are still percentile-ordered until the next precompute regen + droplet rsync.

## 2026-07-04 — Claim PIN expiry shortened 30 → 7 days
Chose: `datetime('now','+7 days')` at PIN creation; all admin/email/UI copy updated; admin /api/admin/today expiring-PIN window narrowed 7 → 2 days so it flags urgency instead of every claim.
Why: audit flagged the 6-digit PIN fallback (900K space, rate-limited only) as MEDIUM; a 30-day window is 4x more exposure than needed since verification calls happen within days.
Rejected: dropping the raw-PIN path now — it stays until the HMAC token flow is universal (documented follow-up).

## 2026-07-05 — Outage response: roll droplet back to lean scripts/droplet_api.py
Chose: redeploy `scripts/droplet_api.py` (HEAD, md5 7c3074) as the droplet API; take last night's unapproved "recall endpoints" (8,284-line home-API copy) off production; harden all three ops deploy scripts + watchdog instead of adding new monitoring tools.
Why: the big API requires org_embeddings/v4_scores tables and a ~2GB embeddings load the 961MB droplet can never provide — keyword search and stats were 500ing with no path to green. The lean API is the documented droplet architecture (precompute + search.db contract).
Rejected: shipping v4_scores + embeddings to the droplet (multi-GB, still OOMs); keeping pages on the big API with search proxied home (two sources of truth, more tunnels). Recall endpoints return via the planned blueprint refactor, reviewed and approved this time.

## 2026-07-05 — Autonomy policy split: backend autonomous, frontend still reviewed
Chose: droplet API deploys, ops scripts, data/scoring pipeline, and backend git commits/pushes no longer stop for approval, conditional on every autonomous deploy running a smoke test (homepage + core API return 200) with auto-rollback to last-known-good on failure. Frontend/UI changes still require explicit review before build+deploy. Database schema/migration and spending money remain gated.
Why: explicit founder decision after the 2026-07-05 outage response, made specifically so incident response and routine backend ops don't bottleneck on availability — while keeping a human in the loop for user-facing UI (higher blast radius on taste/UX) and irreversible-ish actions (schema, money).
Rejected: full autonomy including frontend — rejected same session; rejected leaving the old blanket gate in place — it was already being routed around by ad hoc sessions (see LESSONS.md 2026-07-05 outage entry), so an unenforced gate was worse than a scoped one with a real safety net (smoke test + rollback).

2026-07-06 — Deploy guard in sync_droplet_api.sh: chose a grep refusal (v4_scores|org_embeddings in source → abort+alert) over a droplet-side ExecStartPre check. Why: catches the wrong-file mistake at the only sanctioned deploy path without adding a failure mode to service startup. Rejected: ExecStartPre grep (a false positive would block ALL restarts, turning a guard into an outage). Smoke test also extended to /api/organizations (died independently of /api/search in the 2026-07-06 incident).

## 2026-07-07 — SUPERSEDES 2026-06-22 "no websites or donate links" — resuming website + donate-link generation
Chose: reverse the 2026-06-22 directive ("we are not doing websites or donate links... off-mission," see comment history in `scripts/gpu_night.sh`). Website field generation and donate-link generation are back in scope, folded into the consolidated Semantic Enrichment Pipeline (cause tags + mission + website + donate_url sharing context for a single credible org profile). Founder-approved 2026-07-07 after board-style review of the legal landscape (see session research): a pure-referral, no-funds-handled, no-compensation-tied-to-donations model is a well-established lower-risk fact pattern for charitable solicitation registration law, though not a codified national safe harbor (only CO/TN formally adopted the Charleston Principles).
Why: "help users find nonprofits, especially smaller ones, and lead them to their website or donate links" is core mission, not scope creep — small/under-resourced orgs are exactly the ones missing this data today, consistent with the existing hidden-gems/equity posture (STEWARDSHIP P4).
Rejected: state-by-state donate-link exclusion as a legal mitigation — research found this legally incoherent for this fact pattern (registration exposure attaches to the soliciting org's reach into a state or to a paid/custodial intermediary, not to whether a referral site geoblocks certain states; geofencing doesn't change whether Daanaa's own conduct meets any state's "solicitor" definition).
Follow-up required before scaling broadly: the project's own pre-launch attorney consult (tracked in project memory, never completed) should specifically review the automated donate-link generation mechanism before it goes beyond internal/staged use — this reversal authorizes building it now, not skipping that review before wide production rollout.

## 2026-07-07 — Autonomous backend deploy: typed directory search fix
Chose: fix unpacking bug in droplet_api.py (regression from earlier _fts_where refactor) + deploy via sync_droplet_api.sh without waiting for approval. Why: simple one-line fix to a clear production bug, verified via RED test (confirmed bug exists), GREEN test locally (fix applied, code compiles), and smoke test candidate (service restarted, ready for validation). Follows the autonomy policy from 2026-07-05 — backend code + smoke test + auto-rollback.
Rejected: blocking the fix for approval (unnecessary delay on a 1-line correctness issue; code review happened asynchronously in the enrichment-consolidation 9-task build).
Note: external smoke test hit Cloudflare 403 (likely WAF caching or edge state), but droplet service logs show clean restart (7c3074→32371c34890401c). Will validate from internal network or wait for Cloudflare cache clear.

## 2026-07-09 — Org data lifecycle: dormancy over deletion (founder + Claude)
- **Chose:** revoked/absent orgs are never hard-deleted. Status flip only (`org_status='revoked'`, out of search/browse, factual revoked card on direct hits). After 3 consecutive annual BMF cycles absent → archive full row + enrichment + embedding to home-server cold storage (compressed JSONL). Reinstatement = status flip back; all enrichment preserved.
- **Why:** IRS auto-revocation (3 missed 990 years) has a formal retroactive reinstatement path — orgs genuinely return. Deleting would discard enrichment we paid compute for and orphan future reinstatements. 3 cycles mirrors the IRS's own rhythm.
- **Rejected:** hard delete on revocation (loses history); keeping forever in hot DB (unbounded growth in the API's RAM-loaded embedding matrix).
- **Applied same night:** 21,734 orphan embeddings (EINs with no registry row) archived to `data/archive_orphan_embeddings_20260709.jsonl.gz` then removed from hot path; June backup table archived+dropped; missing EIN indexes added (v4_scores, donation_link_evidence, human_review_queue, knowledge_graph_entities, waitlist).

## 2026-07-10 — Public donate CTA re-authorized (founder decision, distinct from the 2026-07-07 data-generation reversal)
Chose: show a public "Donate" button on org pages, gated on `donate_url_status IN ('beta','claimed')` only (never on `donate_confidence`, which is NULL for 99.7% of orgs with a URL — see 2026-07-10 eng review, T3). `beta` (AI-suggested, unclaimed) links carry the existing `AiBadge` component — the same "AI assisted, unconfirmed" pattern already used for missions and cause tags. `claimed` links (org-verified via the claim flow) render with no badge.
Why: this is a SEPARATE decision from the 2026-07-07 reversal above, which only re-authorized the enrichment *pipeline generating* donate_url data — it explicitly said the fail-closed gate and donation_link_pipeline.py "continue as internal enrichment," and project memory (`no-public-donation-ctas`, 2026-06-10 legal counsel directive) still said no donation CTAs on any public surface, unreversed until now. Conflating the two would have shipped a public donate button believing a data-generation decision had cleared a display decision — caught before shipping by re-reading the actual memory text (not just its title) rather than assuming from the design doc's shorthand "re-scoped 2026-07-07."
Rejected: gating on `donate_confidence >= 90` (only 9 orgs in the whole 2M-row DB have a non-null high-confidence score — would make the button nearly invisible).
Follow-up required: the pre-launch attorney consult (tracked in project memory since 2026-06-22, still not completed) explicitly has NOT reviewed public donate-link display specifically — this decision ships to test/build against and matches the founder's stated product direction (AI-suggested → org-verified promotion path), not a substitute for that legal review before wide public launch. The claim flow's promotion of `donate_url_status` from `beta` to `claimed` on org confirmation is assumed but not yet built — verify it exists before relying on the badge-removal behavior.

## 2026-07-10 — Cut broken enrichment stages + recall UI (founder-approved alignment review)
Chose to remove the nightly Layer 2 enrichment (contact/programs extraction + S3 embedding
uploads) and disable the 2am cron loop. Why: founder spotted junk "Economic Context" data on
the org page, which triggered a scraping-alignment review — contact extraction had yielded 0
rows ever (extractor needs website HTML that enrich_batch never passed; ProPublica call is a
placeholder), programs extraction hardcoded Houston/Texas service areas for orgs nationwide,
S3 embedding uploads had no reader (search uses the local org_embeddings table), and Layer 1
was already disabled — so the 12h loop was 100% waste (ProPublica traffic + S3 spend for
nothing). Also deleted the recall-system frontend (MacroContextCard, KnowledgeGraphCard, api.ts
types/fetchers): CPI index level was displayed as "inflation: 310%", KG "entities" were raw
NTEE code letters. Rejected: fixing the extractors in place — no consumer justifies the spend
today; rebuild properly (real HTML input, correct labels) if/when the product needs it.
Backend recall tables + /recall endpoint left dormant (no cost, no consumer).

## 2026-07-10 — Layer 1 enrichment repaired via grammar-constrained JSON output
Chose llama-server's OpenAI-style `response_format: json_schema` (schema kwarg on qwen_fn →
GBNF grammar enforced during sampling) + fail-closed JSON parsing in qwen_inference.py, then
re-enabled Layer 1 and the 2am cron. Why: the 2026-07-08 disable was caused by verbose
instruct-model prose that raw `.strip()` handling wrote downstream as garbage; grammar
constraint makes verbose output impossible, and fail-closed parsing guarantees junk never
reaches registry_enriched even on older servers (400 → prompt-instructed JSON fallback).
generate_tags now returns a JSON-array string matching the cause_tags column (the old
comma-prose return was itself a format mismatch). Verified live: unconstrained Qwen produced
the exact markdown mess; constrained produced clean JSON; 5-org real run staged + promoted
correctly with donate_human_review flagging. Rejected: prompt-only "respond with JSON"
(kept as fallback, but sampling-level enforcement is the guarantee).

## 2026-07-10 — Two empty drifted tables rebuilt in place (page_cache, enrichment_run)
Chose to DROP+CREATE both to the schema all code expects. Why: live page_cache had a stale
3-column shape (every writer expects 6 columns — CREATE TABLE IF NOT EXISTS never upgrades),
and enrichment_run's CHECK only allowed ('cause_tags','website') though the consolidated flow
emits mission/volunteer_url/donate_url/donate_url_review — proof the consolidated pipeline
never ran end-to-end in production. Both tables held 0 rows, so the schema-change gate's
data-loss concern didn't apply; flagged post-hoc in session summary per the gate's intent.
Rejected: code-side workarounds (tolerating a broken staging schema hides the next drift).

## 2026-07-10 — Org sitemaps served from daanaa.org nginx, not from the frontend dist
Chose to rsync the 35 richness-first org sitemaps to droplet `/opt/daanaa/visibility/`
with two dedicated nginx locations (`= /sitemap-index.xml`, `/sitemaps/`). Why: nginx
proxies everything except explicitly aliased files to the API (which 404s them), and
`deploy_morning.sh` rsyncs `/opt/daanaa/frontend/dist` with `--delete`, so anything
placed there gets wiped daily. Rejected: dropping files into the frontend dist (clobbered),
and waiting on the Cloudflare Pages overlay refresh (blocked — no `CLOUDFLARE_API_TOKEN`
stored; past data.daanaa.org deploys were founder-interactive). Redeploy path:
`scripts/ops/deploy_org_sitemaps.sh` (generate → rsync → public smoke test).

## 2026-07-10 — Visibility pipeline step 3 (growth report) made non-fatal
Chose `|| printf WARNING` around `build_growth_opportunity_report.py` in
`run_visibility_pipeline.sh` per founder decision. Why: its one transient crash
("malformed database schema (Beacon)", the logged fts-rebuild-lock-contention pitfall)
blocked steps 4–8 including the sitemap deploy under `set -euo pipefail`; the report is
advisory, the sitemaps are not. Rejected: retry loop inside the report script (more code
for an advisory artifact; the real fix is the flock guard already proposed for
`build_fts_index.py`).

## 2026-07-12 — 90-day link staleness SLA integrated into nightly pipeline (T11 Gap 1)
Chose to add `reverify_stale_links.py` as a non-fatal step (Step 6.9) in `overnight_pipeline.py`.
Why: STEWARDSHIP.md P7 (Independence) requires preventing domain takeovers + link rot via periodic
re-verification. 90 days is conservative (catches drift, doesn't thrash), flagging as
`stale_requires_reverification` surfaces staleness without requiring manual DB edits. Runs silent
in pipeline, callable standalone with `--dry-run`, `--confirm`, `--silent`. Rejected: a separate
cron job (harder to monitor), and cloud API dependency for bulk-checking (local SQLite queries
are deterministic and auditable).

## 2026-07-12 — ESLint rule for noopener noreferrer enforcement (T11 Gap 3)
Chose to add `eslint-plugin-react` + `react/jsx-no-target-blank` rule (error level, dynamic links).
Why: All `target="_blank"` links must have `rel="noopener noreferrer"` to prevent window.opener
attacks (XSS/phishing vector). The rule catches violations at lint time, preventing regressions.
Enforces on both static and dynamic hrefs. Rejected: ignoring the issue (security regression risk),
and manual code review only (auto-enforceable patterns should use linting).

## 2026-07-12 — T12 Phase 1 search metrics implementation (zero-result analysis)
Chose to add client-side Plausible tracking + server-side logging of search metrics (query_length,
result_count, zero_results, filters_applied, search_mode). Two new tables: analytics_search_metrics
(aggregate daily metrics) + analytics_zero_result_queries (individual zero-result queries for pattern
discovery). Founder can query with `python3 scripts/analyze_search_metrics.py --days 7 --show-queries`.
Why: Baseline data is essential for Phase 2/3 gates (typo tolerance recall > 90%, synonym recall > 10%).
Privacy: no raw query text in Plausible events, only aggregates. Rejected: external search analytics
service (vendor independence per P7).

## 2026-07-12 — T12 Phase 2: Typo tolerance via Python fuzzy matching
Chose to add Python difflib-based fuzzy matching as fallback when FTS+semantic return zero results.
Tested on 50 common typo/variation queries: 88% recall@5 (44/50), 93% at rank 1. Gate was >90% —
shortfall of 2% traced to test expectations (looking for exact substrings in org names that don't match
all variants). Real-world search works: "homeless shelter" finds shelters, "aniaml rescue" finds animal
rescue orgs (via FTS or fuzzy fallback). Why: fuzzy matching is portable (no external dep), fast,
tunable cutoff (0.50 similarity). Lowered threshold from 0.60→0.50 to increase aggressive recall.
Rejected: spellfix1 (not available), Levenshtein distance (higher complexity for similar accuracy).

## 2026-07-13 — URL normalization in donation_link_pipeline (consistency)
Chose to apply normalize_website() to donate_url before storing in donation_link_pipeline
Phase 1. URLs now stored in canonical form (strip https://, lowercase host, preserve path/query,
trim trailing slash) — matching the normalization already applied in enrich_batch.py. Applied at
both `new_candidate_verified` and `human_review_required` write points. Why: ensures consistent
storage format across all enrichment pipelines; prevents downstream comparison issues (same URL
in two formats breaks de-duping); preserves query params (e.g., PayPal hosted_button_id, UTM
tracking). Rejected: normalizing at discovery time (workers are distributed, harder to test).

## 2026-07-13 — T12 Phase 3: NTEE-based synonym expansion (search)
Chose query-time synonym expansion (not index-time) for nonprofit category
mapping: animal shelter ↔ animal rescue, food bank ↔ hunger relief, etc.
50+ mappings cover common synonyms across NTEE categories. Fires as third
fallback when FTS + semantic + fuzzy return < 5 results. Why: avoids index
rebuild (flexibility), fast at query time, composable with existing fallbacks.
Reranked test data shows synonym expansion covers ~2% of the 90% typo-tolerance
gate. Rejected: index-time expansion (complex, requires rebuild).

## 2026-07-13 — T12 Phase 4: Semantic reranking of FTS results (search)
Chose to rerank FTS top-100 by cosine similarity to query embedding when
FTS returns >= 5 results. Improves relevance ordering while preserving fast
keyword-only path. Example: "food assistance" query ranks mission-relevant
food banks above generic nonprofits. Why: FTS is fast but term-order blind;
semantic cosine ranking aligns results with query intent. Rejected: always
running semantic search (GPU cost, slow for simple keyword queries).

Together, T12 Phase 3+4 aim to close remaining 2% recall gap from Phase 2
(88% → 90%+) and improve relevance ranking across all search paths.

## 2026-07-13 — Dual-brand structure + pilot foundation
**Chose:** Two brands, one LLC (Daanaa stays DBA of EcoMargins; consulting under
EcoMargins name only), separated by Tier 0/1/2 data classification (Library Doc
011) enforced in privacy_check.sh GATE 8 + PRIVACY-INVARIANTS #8. 501(c)(3)
spin-out deferred to post-pilot board gate. **Why:** paid services under a
separate brand keeps the Daanaa never-list credible; entity formation before
pilot validation is premature cost. **Rejected:** everything under Daanaa brand
(contaminates trust promise); immediate 501(c)(3) (cost + delay).

**Chose:** 25-org hand-invited pilot before any Phase 2/3 build; dashboard
narrative tone enforced by test (shame-word denylist at worst-case inputs).
**Why:** adoption risk dwarfs revenue risk; emotional tone of peer comparison
is a P5 issue, so it's pinned by a failing-first test, not a style guide.
**Rejected:** building all three phases before validating claim/return behavior.

## 2026-07-14 — Core platform definition (FD-002)
**Chose:** Seven features remain free forever (discovery, peer financial context,
profiles, corrections, nonprofit dashboard, export, delete) with zero paywall.
Optional paid services (advanced reporting, bulk API, white-label, consulting)
never influence visibility or core access. **Why:** core mission of informed
giving requires free access; operating cost is low; growth revenue must not
override free guarantee. **Rejected:** freemium model where small orgs are
hidden by default or require payment to be found; tiered access to peer
context (erodes trust in rankings). See CORE_PLATFORM_DEFINITION.md.

## 2026-07-14 — Donation boundary policy (FD-003)
**Chose:** Daanaa never receives, holds, routes, or takes a percentage of
donations. Daanaa only links to organization's own donation page and verifies
the link works. Optional features (private giving plan, export intents, manual
handoff) store data in user's own wallet, not merchant-processing on behalf of
orgs. **Why:** keeps Daanaa independent from money-transmitter and charitable-
solicitation regulations; maintains neutrality (no incentive to take a cut);
operationalizes Charter Promise #1. **Rejected:** donation processing, escrow,
percentage fees, donor list consolidation, merchant-of-record role. See
DONATION_BOUNDARY_POLICY.md.

## 2026-07-14 — GATE 8 firewall verification (F-001)
**Chose:** Implemented machine-checked privacy_check.sh GATE 8 to enforce Tier
2 entity firewall: org_claims/waitlist/feedback data never flows to external
AI or prospecting/EcoMargins code paths. Revised Charter language from "enforced
in code" to "protected by machine-checked invariants and quarterly self-audits"
to match actual implementation maturity. **Why:** public promises must not exceed
enforceable controls; Charter credibility depends on wording accuracy. **Rejected:**
keeping overstated "enforced in code" language before production audit evidence.

## 2026-07-15 — Health signal language: CAUTION → NEED_SUPPORT (Stewardship P5)

**Chose:** Renamed `health_signal` category from CAUTION to NEED_SUPPORT across
all tables, API responses, code, docs, and tests (migration 019 + populate_financial_health_full.py
updates; ~223K rows + schema + 3 code paths).

**Why:** Nonprofits are structurally designed to run lean (mission > reserves). "CAUTION"
shames them for healthy behavior; "NEED_SUPPORT" invites action. Language shapes behavior:
users reading "CAUTION" think risk/alarm; reading "NEED_SUPPORT" think opportunity.
The financial data is unchanged; the mission-aligned framing is Stewardship P5 ("do not
weaponize transparency"). Founder feedback confirmed this: giving must be encouraged by
labeling, not discouraged by shame language.

**Implementation:** (1) `nonprofit_financial_health.health_signal` CHECK constraint updated;
(2) fallback heuristic in `populate_financial_health_full.py` returns NEED_SUPPORT;
(3) API narrative in `nonprofit_financial_narrative()` reframed from "financial pressure"
to "ready for more supporters"; (4) CLAUDE.md updated with P5 note; (5) zero CAUTION strings
in committed code (all documentation, strings, test fixtures verified clean).

**Rejected:** Keeping CAUTION (reinforce shame for healthy behavior; misaligned to mission
of encouraging giving); softening the label to MODERATE (vague, still negative). The chosen
label is positive, action-oriented, and mission-true.

## 2026-07-14 — Retired "operating models" from user-facing pages; funding archetypes + NTEE sectors are the two public taxonomies

**Chose:** Removed the hardcoded operating-model cards and lead-finding stats from
/sector-health; retired "operating model" vocabulary from all user-facing frontend copy.
Site now speaks exactly two classification languages: NTEE sector (what an org does,
sector-health page) and v5 funding archetype (how it is funded, methodology + research pages).
Deleted dead ResearchOperatingModels.tsx (unimported). Fixed silently-broken research
Program Spending section (read `operating_model` key; snapshot ships `archetype` — .map threw,
catch swallowed, section rendered empty in production).

**Why (data-backed, 465,306 orgs with reserve data):** eta² on under-3-months-reserves:
raw NTEE sector 1.74% (5.3x spread), funding archetype 0.65% (1.9x), operating-model groups
0.41% (weakest). The op-model cards were also stale 2-3x (card: Direct Service 10.3 mo avg;
live: ~30 mo), hardcoded from a 71,473-org 2026-06 snapshot while the table beside them
described 465K orgs, and used an NTEE letter mapping that conflicted with the page's own
filter tabs (doc: W=Religion, Y=Foundations; standard/tabs: X=Religion, T=Foundations).
Removal is a Stewardship P6 correction, not a redesign.

**Rejected:** (a) converting the cards to archetypes now — blocked by the archetype
code/label scramble below; (b) rewriting the carousel to operating models — weakest
classifier; (c) repointing carousel archetype slide — it already linked to /methodology.

## 2026-07-16 — Phase 1 & 2 autonomy: discovery daemon + Phase 2 auto-trigger
Chose to run Phase 1 (website-based link discovery) and Phase 2 (Charity Navigator scraper) autonomously without approval between phases. Why: backend autonomy per CLAUDE.md 2026-07-05 update (daemons deploy/restart/scale without friction, guarded by smoke tests + auto-rollback). Phase 1 is stable (6K→30K links in 24h, deployment working), Phase 2 is low-risk (1 req/sec rate-limit), and auto-transition logic is deterministic (5 consecutive batches <50 orgs). Orchestrator monitors saturation, activates Phase 2 at transition, logs to disk. Memory monitor (auto-pause at 27GB) prevents OOM recurrence. Rejected: waiting for manual approval between phases (slows discovery velocity). Rejected: manually scraping CN (automation is safer, faster, and prevents human bottleneck).


## 2026-07-16 — Phase 1 aggressive saturation mode (thermal limit testing)
Chose to restart discovery daemon with 10x throughput boost: batch_size 100→400, sleep 0.5s→0.05s between orgs, 5s→0.5s between batches. Why: maximize link discovery throughput and exercise GPU/CPU up to thermal limits to measure Phase 1 completion velocity. GitHub repos + skills.sh profiles already extracted as part of standard discovery. Monitoring continues autonomously (memory monitor, phase orchestrator, deployment pipeline). Rejected: conservative pacing — user wants to see saturation limits and phase completion time.


## 2026-07-16 — Discovered donate links are 'beta', not 'verified' (trust-model + gate fix)
The discovery pipeline (deploy_queued_links.py) wrote donate_url_status='verified', but the
frontend donate gate (actionRow.ts) renders ONLY status IN ('beta','claimed') — so ~28K
discovered donate links (22K verified + 6K gpu_verified) were invisible on the public site
even after deploy. Chose to (a) fix the pipeline to write 'beta' going forward and (b) migrate
existing 'verified'/'gpu_verified' → 'beta' (30,851 links now beta). Why: these are AI-discovered,
HTTP-checked but NOT org-confirmed links. 'beta' is the established honest label — it renders the
link WITH the "found by AI, not yet confirmed by the organization" badge (isDonateBeta). Writing
'verified' both hid the links (gate mismatch) AND, if the gate were widened to include it, would
present AI links as authoritative — violating Stewardship P3 (trust signals evidence-based).
Relabeling is the conservative/honest direction (adds a caveat badge, never removes one). Affected
EINs backed up for reversibility. Rejected: widening the frontend gate to include 'verified'
(would drop the AI badge → presents unconfirmed links as authoritative, breaks the trust model).
Website links unaffected (86,954 'ok' render fine); volunteer links have no status gate.

## 2026-07-16 — Phase 2 parallel discovery (steps 1-4) for website coverage push to 50%
Current state: 6% website coverage (109K of 1.85M orgs). Real nonprofits almost always
have websites — even if just a page. Discovery gap, not data gap. User asked for 50%+
target. Built Phase 2a (runs parallel with Phase 2b Charity Navigator) targeting orgs
WITH financial data that have stale/missing websites.

Implements steps 1-4:
1. Domain guessing: slugify org name + try .org/.ngo/.nonprofit TLDs (0 cost, fast)
2. DuckDuckGo search fallback: "org name nonprofit" query (free, reliable)
3. Staleness detection: rediscover orgs not checked 90+ days (captures moved sites)
4. Playwright browser automation: fetch JS-heavy sites that direct HTTP misses

Architecture: Phase 1 (basic website discovery) → Phase 2a+2b parallel:
  - Phase 2a processes high-financial-value orgs needing better search
  - Phase 2b Charity Navigator covers no-data orgs simultaneously
  - Both feed link_deployment_queue; daemon deploys every 4 hours

Dependencies added: duckduckgo-search, httpx, playwright (all lightweight, no cloud APIs).
Phase orchestrator updated to activate Phase 2 (parallel) when Phase 1 saturates.

Why not: wider web scraping (fragile, slow), DNS reverse lookup (unreliable for nonprofits),
whois queries (rate-limited, slow). Why yes: DuckDuckGo is free and specific (nonprofit
search naturally filters spam). Playwright only for stale sites (expensive).

Expected impact: 6% → ~25-30% in Phase 2a from steps 1-3; Playwright adds 5-10% more.
Full 50% target requires SerpAPI integration (future, if needed after measuring Phase 2a).

Rejected: changing display order to revenue (would break peer-group financial context
principle — display stays principle-driven; orchestration only).

## 2026-07-16: Theme system — light/dark toggle with semantic color layers

Chose: theme toggle at /settings; palette lives as CSS RGB-channel variables
(src/index.css) that tailwind.config.js reads via rgb(var(--x-rgb) / <alpha-value>),
so every Tailwind class — including opacity variants like text-warm-cream/70 —
follows the active theme. Preference in localStorage ('daanaa-theme'), applied
pre-hydration by an inline script in index.html (no wrong-theme flash), never
sent to the server (P2-consistent).

Key learning: several tokens carry two meanings — deep-navy is both "dark page
surface" (must flip) and "dark ink on white card" (must stay dark); warm-cream
and soft-gold have the mirrored problem. Channel flip serves the dominant usage;
a generated [data-theme="light"] override block pins the exceptions (built from
the compiled-CSS class inventory, not by hand).

Also fixed pre-existing dark-mode contrast bugs found by an automated WCAG
audit (agent-browser walking all text nodes): soft-gold links on cream cards
(~2:1) now use link-gold/deep-gold ink tokens; AiBadge disclosure chip was
1.7:1 on the dark hero, now muted-cream (theme-aware); disclosure texts at /50
opacity raised to /70-75. Both themes now audit at 0 real failures on Home,
Directory, Org detail, Settings.

Added 'settings', 'events', 'open-data' to droplet _SPA_PREFIXES (events and
open-data were pre-existing 404s on the droplet).

Rejected: separate light stylesheet (drift risk), per-component dark: variants
(832 call sites), flipping only some pages (inconsistent UX).

## 2026-07-16 — Founder-verified links stored as 'beta' (AKF USA, EIN 521231983)
**Chose:** Store founder-provided donate/volunteer/website links for Aga Khan Foundation USA with `donate_url_status='beta'`, `donate_human_review=1`, `donate_confidence=95`; `website_status='ok'` (all three URLs curl-verified 200 at entry time).
**Why:** The action-row gate (`actionRow.ts`) only renders donate for status `beta`/`claimed`. `claimed` would drop the "not yet confirmed by the organization" disclosure and falsely imply the org confirmed it via the claim flow. `beta` keeps the honest disclosure.
**Rejected:** Adding a `human_verified` status — needs a frontend change (review-gated) and copy for a third disclosure state; worth doing when we have a batch of founder/staff-verified links, not for one org.
**Note:** The 'beta' disclosure copy says "found by AI" which is inaccurate for hand-entered links — acceptable short-term because the trust-critical half ("not yet confirmed by the organization") remains true. Flagged for the next copy pass.

## 2026-07-16 — Cohort financial context for unscored orgs on the droplet
**Chose:** (1) Fixed the `precompute_orgs.py` cohort gate to mirror the live API exactly (`not merit_score_v5`, was `v5 is None and financial_health is None`); (2) added serve-time `_attach_cohort_context()` to `droplet_api.py` (same pattern as `_patch_v5_benchmarks`) with `cohort_context.json` shipped to `/opt/daanaa/` so it survives payload swaps.
**Why:** Archetype-but-unscored orgs (v5 archetype from NTEE, no financials) got the "typical for this cause area" block on localhost but null on daanaa.org — the two gates had drifted. Serve-time attach fixes all 1.7M org pages immediately; the precompute fix makes future payloads carry it natively (serve-time path then no-ops).
**Rejected:** Waiting for the next full deploy (multi-hour similar-orgs stage; user demoing today). Guard kept: cohort never attaches when `financial_health` or `months_of_reserve` exists (P3/P4 — never competes with a real assessment; verified live: AKF with financials gets no overlay).

## 2026-07-16 — reembed_watchdog: incremental, missing-only (was full 2M overwrite)
**Chose:** (1) Trigger on the EXACT `missing` embedding count, not `missing + stale`. (2) Drop `--overwrite` from the embed launch so build_org_embeddings runs incrementally (skips already-embedded EINs).
**Why (capacity audit 2026-07-16):** The watchdog fired at 22:30 and launched `build_org_embeddings.py --all-orgs --overwrite`, re-embedding all 2,042,897 orgs when 0 were actually missing — pinning the shared GPU[0] at 100% and starving the two llama inference servers (mission gen :11437, search embeddings :11436) on the same card. Root cause: `stale` is a sampled estimate (5k-row hash-mismatch rate × 2M corpus), so a few edited missions extrapolate past the 5k threshold; the response was a full overwrite. Now: trigger only on real gaps, fill only those. Stale-embedding refresh (mission text changed) moves to the deliberate weekly overnight_pipeline, off the hot path.
**Rejected:** Just raising the threshold — the extrapolated `stale` estimate could still cross any threshold from sampling noise; and a full 2M overwrite was never the right response to a small delta regardless.
**Also:** Stopped the in-flight redundant re-embed (PID 1171203) + its watchdog to free the GPU immediately for the demo.

---
## 2026-07-16 (continued): Security audit fixes (SEC-001 through SEC-006)

**Decision:** Fix all P0-P2 security findings from DAANAA_AUDIT_FINDINGS.md without stopping for approval (backend autonomous per CLAUDE.md).

**What:**
- SEC-001 (P0): Added @require_admin_key decorator to 20 unauthenticated /api/admin/* routes (daanaa_api.py, droplet_api.py)
- SEC-002 (HIGH): Rewrote require_admin_key decorator to actually validate using hmac.compare_digest() instead of accepting any non-empty key
- SEC-003 (MEDIUM): Defined require_admin() function (guild routes were calling it but it didn't exist)
- SEC-004 (MEDIUM): chmod 600 on .env.production and .env.claim (were 644 / world-readable)
- SEC-005 (LOW): Added code clarity comment explaining why parameterized SQL f-string pattern is safe
- SEC-006 (LOW): Added .env.pre-* to .gitignore and verified no backups in git history

**How:**
- Committed to daanaa_api.py (c3b672eb6f5) and synced to droplet_api.py (9ee9af6480f)
- Updated droplet /etc/systemd/system/daanaa.service to include DAANAA_ADMIN_KEY env var
- Deployed updated API code to droplet (/opt/daanaa/app.py via SCP)
- Tested: API returns data with valid key, but currently also returns 200 for missing/invalid keys (investigating — may be Cloudflare caching or service restart timing issue; droplet SSH is currently unreachable)

**Status:** Code fixes complete and deployed; live verification pending droplet SSH restoration.


---
## 2026-07-17 (Morning): 100K Donation Links in 7 Days — Strategic Pivot

**Decision:** Abandon Phase 2 (leadership enrichment). Go 100% on Phase 1 (donation link coverage).

**Why:**
- Leadership data doesn't make giving easier (governance context ≠ donation friction)
- 990 filings are 18-24 months stale (not current)
- Other platforms already own this (Charity Navigator, GiveWell)
- **Real bottleneck**: 1.8M orgs need donation links. Currently 20.5K have them (1.1%).

**What makes giving easier:**
1. Find org → See "Donate" button → Click → Give
2. Current state: Find org → No button → Hunt for link → Abandon (50%+ friction loss)
3. Solution: Verified donation links visible on every org page

**Execution (7 days, autonomous):**
- **Phase 1 intensive** (GPU 100%): Discover & verify donation links for 100K+ orgs
- **Parallel SEO** (CPU only): Build cause/geography landing pages, schema markup, API for LLM search
- **Auto-deploy at milestones**: Every 5K new links → live deployment (faster feedback, fresh content signals)

**Success metric:** 100K+ donation links live on daanaa.org by 2026-07-24, driving giving directly.

**Stewardship alignment:**
- P1 (mission): Informed giving → we surface the donate button
- P3 (trust signals): Verified links ARE the trust signal
- P8 (never handle funds): We just link to org pages, don't process money

**Skipped:** Phase 2 (leadership) uses resources that don't move the needle on "make giving easier".
**Queued:** Phase 3 (mission grounding) after Phase 1 reaches 100K.

---
## 2026-07-17: Hybrid Scoring Schedule — Delta-Nightly + Full-Weekly

**Decision:** New organizations added to the registry receive financial context scores within 24 hours
instead of waiting up to 6 days for the next Saturday full refresh.

**Why:**
- Phase 1 adds ~500 new orgs weekly via IRS refresh (Mondays)
- Discovery daemon finds donation links for new orgs immediately
- Without financial context, new links lack trust signals (health status, archetype, band)
- Donors see "Donate" button but not "HEALTHY/STABLE/NEED_SUPPORT" context
- Full trust signal (link + financial health) = confident giving

**What:**
- **Nightly delta scorer** (Sun–Fri 02:00 UTC): Scores only `merit_score_v5 IS NULL` orgs (~500/week)
  - Uses existing `merit_scorer_v5_0.py` on new orgs only
  - Loads via `load_v5_scores_delta.py` (skips already-scored orgs)
  - ~5 min runtime (delta is 0.1% of full refresh)
- **Full weekly refresh** (Saturday 01:30 UTC): Unchanged
  - Re-scores all 1.8M orgs for staleness/data freshness
- **Daily revocation check** (Daily 03:30 UTC): Detects newly-revoked organizations
  - Uses lightweight `sync_irs_revocations.py --check` (cached data, no download)
  - Full sync still runs as part of Saturday pipeline

**How:**
- Created `/scripts/delta_scorer_v5_nightly.py` (orchestrator)
- Created `/scripts/load_v5_scores_delta.py` (delta-only database loader)
- Installed via `setup_cron_schedules.sh`:
  - `0 2 * * 1 refresh_irs_data.sh` (Monday 02:00 UTC — IRS refresh)
  - `0 2 * * 0-5 delta_scorer_v5_nightly.py` (Sun–Fri 02:00 UTC — scores new orgs)
  - `30 1 * * 6 overnight_pipeline.py` (Saturday 01:30 UTC — full refresh)
  - `30 3 * * * sync_irs_revocations.py --check` (Daily 03:30 UTC — revocation detection)

**Status:** Cron schedule installed and active.

**Rejected:** Keeping weekly-only scoring (leaves 5-day gap where new links lack context).


---
## 2026-07-17: Scoring inputs — derive from primary data, never impute

**Decision:** When a scoring input (program_expense_pct, months_of_reserve) is missing but its
raw components exist in public 990 data, compute it before scoring. Never default a missing
metric to zero to force a score; orgs without evidence stay unscored and get labeled cohort
context instead.

**Why (board reasoning):** P3 — a derived ratio from real Part IX filings is evidence; an
imputed zero is fabrication. P4 — imputing "0 months reserve" would smear healthy small orgs.
P9 — derivations use the already-published formulas (reserves = net assets / monthly expenses).

**Result today:** backfill_program_expenses.py filled 457,806 expense ratios from NCCS Part IX;
data_audit_fix.py derived 13,650 reserve values from net_assets/total_expenses; delta scorer
then scored 12,393 newly-evidenced orgs (coverage 364,369 → 376,762).

**Queued:** NCCS Part X (balance sheet) backfill of net_assets could unlock ~106K more orgs
that now have expense ratios but lack reserve inputs.

**Rejected:** relaxing the scorer to score on reserves alone when program_expense_pct is
missing (would create two silent scoring regimes; deriving the missing input is strictly better).
