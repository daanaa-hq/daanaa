# Execution Handoff — Strategy Locked, Mechanical Work Queued

**Authority:** DR-2026-07-12-008 (baked-data hardening; supersedes Postgres plan)
**Written:** 2026-07-12, deliberately on the stronger model. Every task below is specified
so a smaller model (or a future session with no memory of this conversation) can execute
it without making new judgment calls. If a task requires a decision not written here,
STOP and ask the founder — do not improvise strategy.

---

## Strategic State (do not re-litigate)

1. **Dataset is bounded** (~1.7M US 501c3). No growth-driven scaling will ever be needed.
2. **Baked-data architecture is final**: home server bakes precompute + search.db nightly →
   droplet serves them → Cloudflare edge caches the public read paths. No Postgres, no
   Redis, no Elasticsearch. Reconsider only if server-side user accounts or high-volume
   writes become real (review trigger in DR-008).
3. **Cost ceiling**: ~$18–19/mo total (droplet $16 + snapshots ~$2–3). Everything else
   free tier. The approved extra budget stays in reserve for credibility work.
4. **Privacy invariant for edge caching**: only content identical-for-all-users may be
   cached. Wallet, claims, guild, nonprofit-portal, admin paths are bypass-listed and must
   stay bypass-listed in any future rule edit. Violating this = P2 breach.

---

## T0 — APPLY CLOUDFLARE CACHE RULES (blocked on founder approval)

**Status:** ✅ APPLIED & VERIFIED 2026-07-12 (ruleset 40e4b952c8154602ac8773d65cf6729e).
Live checks: org API second request = HIT; wallet/search/health = DYNAMIC (bypassed);
homepage renders. Founder ran the PUT via `!` command. Payload note: the entrypoint
endpoint accepts `{"rules": [...]}` only — no name/kind/phase fields.

**Design rationale (the judgment, already made):**
- CACHE rule: `/api/organizations*` (detail/similar/financials/score-history/browse),
  `/api/stats`, `/api/sector-health`, `/api/ntee-categories`, `/api/how-it-works`,
  `/api/methodology`, `/api/guides`, `/api/zip/*`. All precompute-backed, identical for
  every user, refreshed nightly. Edge TTL 4h (max staleness after nightly deploy),
  browser TTL 1h.
- BYPASS rule (listed second so it wins any overlap): `/api/wallet*`, `/api/claim/*`,
  `/api/partner/*`, `/api/nonprofit/*`, `/api/guild/*`, `/api/org/*` (note: this is the
  volunteer-events/service-area prefix, distinct from `/api/organizations`),
  `/api/volunteer-events*`, `/api/impact*`, `/api/search*`, `/api/fused-search*`,
  `/api/admin*`, `/health` (watchdog must always reach origin).
- Search is bypassed for now: unbounded query cardinality = low hit rate; revisit only
  with evidence.
- HTML/SPA shell NOT cached in v1 (server-side meta injection varies per path; measure
  API caching first). Phase-2 candidate, see T10.

**Apply step (single command, run with founder approval outside auto mode):**
`PUT https://api.cloudflare.com/client/v4/zones/d55f274096de6bda42012ac8f220eedb/rulesets/phases/http_request_cache_settings/entrypoint`
with the two-rule JSON (CACHE rule first, BYPASS rule second).

**Verification (mandatory before declaring done):**
1. `curl -sI https://daanaa.org/api/organizations?limit=1` twice → second response header
   `cf-cache-status: HIT`.
2. `curl -sI https://daanaa.org/api/wallet` → `cf-cache-status: BYPASS` (or DYNAMIC).
3. `curl -sI https://daanaa.org/health` → never HIT.
4. Real org page in browser still renders.

**Rollback:** DELETE the ruleset (or PUT an empty rules array). One call, instant.

**⚠️ Token timing:** The founder plans to re-roll the Cloudflare token (it was pasted in
chat). Re-roll AFTER T0 is applied and verified — re-rolling first kills the stored token.
After re-roll, the `.env` value is dead; future Cloudflare work needs a fresh token.

---

## T1 — Fix test_nonprofit_endpoints_phase2.py DB isolation (free, ~30 min)

**Diagnosis (confirmed):** Line ~24 opens the LIVE database at import/setup time instead
of the conftest temp DB, so it fails with `database is locked` whenever the pipeline or
gunicorn is running. This is the only real remaining "DB lock" bug — production WAL mode
is already on (verified: journal_mode=wal, busy_timeout=5000).

**Fix pattern:** Make the test read `os.environ["DB_PATH"]` (already set by conftest.py
to the temp DB) instead of any hardcoded path. Copy the connection pattern used by
tests/test_concierge_confirm.py (which passes cleanly).

**Verification:** `pytest tests/test_nonprofit_endpoints_phase2.py -q` passes twice: once
normally, once while `overnight_pipeline.py` is running (proves isolation).

## T2 — Fix test_nonprofit_data_updates.py schema drift (free, ~20 min)

**Diagnosis (confirmed):** conftest.py seeds `org_claims` with only
(ein, claim_status, verified_at, firebase_uid); the tests expect an `email` column
(error: "table org_claims has no column named email").

**Fix:** Diff the production `org_claims` schema (`sqlite3 data/merit_registry.db
'.schema org_claims'`) against the conftest seed; add ALL missing columns to the seed so
it stops drifting one column at a time.

**Verification:** `pytest tests/test_nonprofit_data_updates.py -q` → 4/4 pass; full suite
has zero locked/schema errors.

## T3 — Passphrase-free automation SSH key (free, ~30 min, fixes nightly sync)

Per C-OP-004. The nightly droplet homepage.json.gz sync fails on key auth.

1. `ssh-keygen -t ed25519 -f ~/.ssh/daanaa_do_cron -N "" -C "daanaa-cron"`
2. Append pubkey to droplet `/root/.ssh/authorized_keys` (use existing interactive key:
   `ssh root@162.243.97.179` — NEVER the daanaa.org hostname, per C-OP-002).
3. Repoint every cron/ops script that SSHes to the droplet to `-i ~/.ssh/daanaa_do_cron`.
   Find them: `grep -rl "162.243.97.179" scripts/ *.sh`.
4. Verification: `ssh -o BatchMode=yes -i ~/.ssh/daanaa_do_cron root@162.243.97.179 true`
   exits 0; next nightly sync log shows success.

## T4 — External uptime monitoring (free, ~20 min)

UptimeRobot free tier, three monitors, alerts to founder email:
1. `https://daanaa.org/` — keyword check for a string that only renders when the SPA
   shell is intact (closes the INC-001 gap: /health lied while every page 500'd).
2. `https://daanaa.org/api/organizations?limit=1` — expect HTTP 200.
3. `https://daanaa.org/api/search?q=food` — expect 200 + keyword `"mode"`.
Verification: use UptimeRobot's test-notification button; confirm founder receives email.

## T5 — DigitalOcean snapshots (+$2–3/mo, blocked on DO token)

When founder provides a DigitalOcean API token (scoped: droplet read/write):
enable weekly snapshots on the daanaa droplet. This is the ONLY billing change in the
whole plan — appears automatically on the existing DO invoice. Verification: snapshot
listed in DO dashboard; note created date in DECISION_LOG.

## T6 — Cache purge after nightly deploy (deferred)

4h edge TTL means org pages can be ≤4h stale after the nightly precompute deploy.
Acceptable for now. If founder wants instant freshness later: mint a token with
Zone → Cache Purge permission and add a purge call to the end of the nightly sync.
Do NOT add purge with the current token (lacks permission).

## T7 — Research experiment: sqlite-vec on droplet (free, home GPU/CPU)

**Hypothesis (log in institution/research/REGISTRY.md):** 546K × 1024-dim org embeddings
via sqlite-vec can serve semantic search on the 2GB droplet, eliminating the 2.2GB
in-RAM matrix that caused INC-003.

**Protocol:** Build a sqlite-vec DB from `org_embeddings` on the home server. Measure:
(a) file size on disk, (b) query latency p50/p95 over 100 representative queries,
(c) recall@10 vs. the exact numpy cosine results as ground truth.
**Decision rule (pre-committed):** p95 < 150ms AND recall@10 > 0.95 → propose shipping
droplet semantic search; otherwise log negative result (valued per Learning Directive)
and keep semantic search home-server-only.

## T8 — Research experiment: Litestream → Cloudflare R2 (free tier)

**Hypothesis:** Litestream can continuously replicate the critical tables to Cloudflare
R2 (free 10GB, zero egress), upgrading backups from nightly to continuous.
**Constraint:** full merit_registry.db is 9.6GB (fits R2 free tier only barely; nightly
scoring churn may blow replication volume). Start with a critical-tables-only replica DB.
**Protocol:** replicate for 48h across two pipeline runs; measure replica lag, R2 usage,
restore correctness (`litestream restore` → row-count diff). Decision rule: restore
correct AND R2 usage < 5GB → adopt alongside (not replacing) the Google Drive chain.

## T9 — Datasette for the open-data/researcher offering (founder decision)

Publishing a browsable/queryable public dataset is a credibility play for the academic
audience. It is outward-facing → founder approves scope before anything ships. Prepare
a 1-page proposal only.

## T10 — Phase 2: HTML edge caching (evidence-gated)

Only after T0 has ≥1 week of cache analytics: consider caching the SPA shell/org HTML
(per-URL cache key, short TTL, respect the per-path meta injection). Requires evidence
that HTML origin load matters. Do not do speculatively.

## T11 — Outbound-link security hardening (founder-raised 2026-07-12)

**Verified already in place (do not rebuild):** scheme validation via `new URL()` in
`frontend/src/utils/externalLink.ts` (http/https only, javascript:/data: rejected, test
exists), `rel="noopener noreferrer"` on external links, no open-redirect endpoint,
pipeline identity matching (donate domain must match verified org website domain,
confidence ≥90, HTTPS forced), public surfaces link to official website not donate pages.

**Gap 1 — re-verification cadence (domain-takeover defense):** add a staleness SLA to the
enrichment pipeline: any `donate_url`/`website` not re-verified in 90 days gets re-checked;
if `website_final_domain` changes vs. the stored value, NULL the donate link and flag for
`donate_human_review`. Implement inside the existing nightly enrichment loop (no new
infra). Verification: pipeline log shows re-check counts; a test simulates a domain change
and asserts the link is dropped.

**Gap 2 — server-side URL validation at write:** the org-claim editor endpoints must
reject any submitted website/donate URL that fails the same rules as
`normalizeExternalUrl` (scheme http/https, dotted hostname). Port that logic to a Python
helper used by every endpoint that writes URL fields. Verification: failing-first test
posting `javascript:alert(1)` as a claimed org's website → 400.

**Gap 3 — make noopener structural:** enable `react/jsx-no-target-blank` as an ESLint
error in `frontend/eslint.config.js` so a missing `rel` fails lint instead of relying on
reviewer discipline. (Frontend lint config change only — not a droplet deploy — but show
the founder the diff per the frontend rule if it touches shipped code.)

---

## Standing rules for the executing model

**Prefer established OSS over hand-rolling (founder directive 2026-07-12, cost
optimization).** Pinned choices — use these, don't build equivalents:
- T7 vector search: `asg017/sqlite-vec` (pip `sqlite-vec`)
- T8 continuous backup: `benbjohnson/litestream` (single static binary)
- Phase B voice STT: `ggml-org/whisper.cpp` (Vulkan build, same stack as llama.cpp)
- Phase B voice TTS: `rhasspy/piper` (fast local TTS, CPU is enough)
- T4 monitoring: UptimeRobot free tier (external vantage) — optionally add self-hosted
  `louislam/uptime-kuma` on the home server later for the droplet's second opinion;
  never self-host as the ONLY monitor (a home-server outage would blind it)
- T11 gap 3: `react/jsx-no-target-blank` from eslint-plugin-react (already a dep)
- Open-data publishing (T9 proposal): `simonw/datasette`
One-line justification in DECISIONS.md per new dependency, per CLAUDE.md. Verify licenses
are permissive (all above are MIT/Apache) and pin versions.

**GPU compute is free (founder ruling 2026-07-12).** Home-server GPU running costs are
minimal — treat local inference/compute as zero-cost in every decision. Implications:
run the largest local model that meets latency targets (don't downsize to "save" GPU);
expand batch enrichment coverage rather than sampling; run T7/T8 experiments thoroughly;
prefer a GPU-heavy local solution over ANY paid cloud service, always.

**Use the project's skills** per CLAUDE.md routing (/investigate for bugs, /review before
commits, /qa for site behavior, /ship for deploys, /context-save at milestones) — they
encode the working agreements and save tokens vs. re-deriving process.

- Backend/scripts/tests: autonomous. Frontend to droplet: founder approval. Spend: only
  T5's ~$2–3/mo is pre-approved; anything else → ask.
- Every droplet-touching change follows C-OP-001/002/005 (sync script only, direct IP,
  smoke test + rollback).
- Log completions in DECISION_LOG.md / LESSONS.md as usual. Update this file's task
  statuses in place.
- Priority order: T0 (awaiting founder) → T1 → T2 → T3 → T4 → T5 (awaiting token) →
  T7 → T8 → T9 proposal → T10.

## T12 — Search excellence, SQLite-native (founder-raised 2026-07-12)

Stay in the SQLite family (bounded dataset, DR-008). Three upgrades, in order:
1. **Measure first (C-DEV-002):** instrument zero-result rate + result-click position as
   Plausible custom events (no PII, no query logging of anything user-identifying).
   One week of data before tuning anything.
2. **Typo tolerance:** SQLite trigram/spellfix1 layer for did-you-mean; verify against
   the top-100 real misspellings observed in (1).
3. **Baked synonyms (GPU is free):** nightly pipeline uses Qwen to generate synonym/
   related-term expansions per NTEE category + org keywords, written INTO the FTS index
   at bake time. Query path stays fast; intelligence moves to indexing.
4. **Hybrid semantic, corrected design (2026-07-12 re-test):** full-corpus semantic
   search on the droplet is confirmed infeasible — not on RAM (retracted, see
   DISCOVERIES.md correction) but on latency: sqlite-vec's vec0 has no ANN index,
   brute-force scan extrapolates to ~1.4s p50 at 2.04M vectors. Viable path: mirror
   the home server's existing `/api/search` RRF pattern — FTS narrows to ~100
   candidates first, THEN sqlite-vec reranks only those 100 (not all 2M) by semantic
   distance. A 100-row vec0 scan is sub-millisecond; this fits the droplet easily.
   Requires: (a) load only the candidate EINs' vectors into a per-request scratch
   vec0 table or query pattern, (b) benchmark p95 on this narrowed design specifically
   before shipping (do not assume — measure, per C-DEV-002).

## T13 — Wallet: zero-knowledge sync architecture (founder-raised 2026-07-12)

**Locked principle:** all synced donor data is encrypted client-side (WebCrypto) before
leaving the device; servers store ciphertext only. "We cannot see your giving" — 
structural, not policy. Current DynamoDB backup migrates to encrypted blobs.
**Retained:** device-first default (no account), bookmarks+intent only (never
transactions, P8), one-click full deletion, add one-click export (portability).
**Key handling:** derive/wrap the encryption key client-side; the key or its passphrase
never transits to Daanaa. Design doc + founder review REQUIRED before implementation
(key-recovery UX is the hard tradeoff: lost key = lost wallet vs. escrow weakening the
guarantee — founder decides that posture; prepare a one-pager with both options).
**Future-data gates:** any feature storing more donor data must pass: (a) never
transactions, (b) E2EE mandatory, (c) founder ruling + PRIVACY-INVARIANTS.md update.

## T14 — Nonprofit Manager Capacity Tools (founder decisions required)

**Authority:** Stewardship Board Resolution 2026-07-11, Decision #6 (Capacity Stewardship).  
**Test:** "What capability does this org have after this interaction that it didn't before?"  
**Scope:** Build tools mapping to the 11 canonical capacity dimensions (Clarity, Financial,
Leadership, Technology, Community, Governance, Sustainability, Data, Communication, Growth, Impact).

**Full spec:** institution/NONPROFIT_MANAGER_TOOLS.md (read before deciding).

**Phase 1 (3–4 weeks, if approved):** Self-assessment survey (11 questions, 5 min) +
peer-benchmark dashboard (revenue-banded comparisons, no org names). Closes the "I don't
know where to focus" problem for nonprofit managers, especially small orgs.

**Phase 2/3:** Communication templates, peer-learning directory, sustainability modeling
(gated on Phase 1 success metrics).

**Founder decisions needed (before design starts):**
1. Timeline: Phase 1 only (ship + measure) vs. commit to full roadmap?
2. Advisory board: Should Daanaa convene nonprofit data experts to co-author guidance?
3. Peer-learning directory scope: Just nonprofits, or include vendor recommendations (risks P7)?
4. Email sequence: Optional 8-week onboarding emails if we build the tutorial?

**Why this matters:** Board Resolution §6 explicitly binds the platform to this test. Every
feature must build capacity. Right now Daanaa helps with Financial + Clarity (peer context,
Mistake Registry); this fills the other 9 dimensions and gives small orgs words, models, and
peer examples. Cost: ~2–3 weeks dev + advisory time. Benefit: structured to Daanaa's core mission.
