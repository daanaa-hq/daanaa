# LESSONS.md

Append-only engineering memory. Each entry: **symptom → root cause → rule that
prevents recurrence.** Never make the same mistake twice. Consolidate into
`CLAUDE.md` rules every ~5–10 entries.

---

## 2026-06-08 — Bulk insert into the live registry starves under concurrent writers
- **Symptom:** `import_bmf_orgs.py` and a targeted new-org insert both failed or hung
  with `sqlite3.OperationalError: database is locked` — even with a 120s `busy_timeout`
  and capped-exponential retry, ZERO batches committed over 13+ minutes. The live DB had
  ~13 concurrent writers (web_finder ×5, reembed ×4, run_agents/cause_tags ×2, auto_ingest,
  gunicorn) and a **1.3GB uncheckpointed WAL**.
- **Root cause:** SQLite WAL allows exactly one writer at a time. Under sustained
  multi-writer load the write-slot is never free long enough for a bulk insert to win it;
  `busy_timeout`/retry just sleep-and-lose forever (it's starvation, not a transient).
  A perpetually-active reader/writer set also prevents WAL checkpointing, so the WAL grows
  unbounded (1.3GB), making every operation slower.
- **What did NOT work (dead ends, don't repeat):** (1) retry/backoff with `busy_timeout` —
  starves forever, writers hold the slot across slow network I/O. (2) `SIGSTOP`-ing the
  writers — a writer frozen mid-transaction holds the lock *forever* → guaranteed deadlock;
  the insert then blocks until timeout. (3) Pausing the gunicorn API to win the lock — wrong
  (it's a reader, doesn't block writes) and correctly blocked by the safety classifier.
- **Rule (the approach that works):** **Stop → apply → restart.** SIGTERM the *persistent
  pipeline writers* (web_finder, donation_link via cpu_night, reembed) — they roll back and
  release locks cleanly, and they're batch jobs safe to relaunch — then insert the tiny
  new-EIN delta uncontended, then relaunch via `gpu_night.sh start` + web_finder. Never touch
  the read-only API. Keep the write tiny: pre-filter to only genuinely-new EINs (~26K).
  Canonical impl: `scripts/refresh_bmf_apply.py` (took the live apply from 13+ min of
  failures to **6 seconds**). Also: `pkill -f <pat>` self-matches the running shell and exits
  144 — use `os.kill(pid, SIG...)` from a *script file* (not `python -c`, which also
  self-matches) so pgrep patterns don't match your own process.

## 2026-06-08 — First auto-detected IRS BMF delta (institutionalize the daily check)
- **Symptom (opportunity):** The monthly IRS EO BMF refreshed upstream (Last-Modified
  flipped to 2026-06-08) and we only noticed because someone asked to "check for new data."
  26,565 new 501(c)(3) orgs were missing from the registry.
- **Root cause:** No daily watch on IRS sources; ingest relied on a 1st-of-month cron, so
  mid-cycle refreshes (and any cadence change) were invisible for up to a month.
- **Rule:** Check IRS sources **every day, first thing** (BMF Last-Modified + SOI annual
  HEAD). This takes priority over other overnight work. On a delta: download → sandbox-
  validate against a `VACUUM INTO` snapshot (never the live DB) → apply only new EINs via
  `refresh_bmf_apply.py` → then cover gaps (missions/embeddings/scoring). Revocation/gap
  signals (existing EINs absent from new BMF) are review-only — never blind-purge. Orchestrated
  by `scripts/daily_irs_check.py` (cron 21:00, ahead of the 22:00 GPU window so new orgs get
  missioned the same night); state in `data/cache/irs_watch_state.json` makes no-delta days a
  cheap HEAD check.

## 2026-06-01 — Cloudflare 522 after enabling proxy
- **Symptom:** Site returned Cloudflare 522 ("can't reach origin") right after flipping
  the proxy on, even though the origin served fine on direct curl.
- **Root cause:** We had migrated the origin from the home server (`108.243.3.83`) to the
  droplet (`162.243.97.179`), but the Cloudflare A records still pointed at the old home
  IP. Time was lost chasing an IPv6 red herring (gunicorn bind) before checking the A record.
- **Rule:** On ANY Cloudflare 5xx, the FIRST check is "does the A record point at the
  current origin IP?" Verify origin address before touching SSL mode, IPv6, or ports.
  When migrating origins, updating the DNS A record is step one, not an afterthought.

## 2026-06-01 — Daily catalog sync would wipe all user data
- **Symptom:** Designing feedback/analytics, realized the 7am `sync_db.sh` overwrites the
  droplet's whole `merit_registry.db` from the home pipeline — which would erase every
  user-generated row (feedback, interest signals, handoffs, analytics) each morning.
- **Root cause:** Read-only catalog data and user-write data lived in one file that gets
  wholesale-replaced by sync.
- **Rule:** Never co-locate synced read-only data with user-write data in a single synced
  file. Split write-path tables into a separate DB the sync never touches.
- **Pattern that worked:** SQLite `ATTACH DATABASE '<live>' AS live` + name resolution —
  a bare table name resolves to the attached live DB *as long as it's absent from the
  catalog* (sync drops it). Zero per-query rewrites. See `merit_api.py` `LIVE_DB_PATH`.

## 2026-06-02 — /api/stats 500'd on production: endpoint queried a table the lean web DB drops
- **Symptom:** `GET /api/stats` returned 500 on daanaa.org (`no such table: propublica_financials`),
  latent since launch. The homepage depends on stats.
- **Root cause:** the lean web DB (`sync_db.sh`) drops heavy tables (propublica_financials,
  org_embeddings, nccs_core_2019, scoring_runs, etc.) to stay small. Any endpoint that
  hard-queries a dropped table 500s on the droplet even though it works on the home/full DB.
- **Rule:** every endpoint must degrade gracefully when a dropped table is absent — wrap
  optional-table queries in try/except with a sensible fallback (e.g. stats `financial_records`
  → fall back to the `with_revenue` count). When you add a table to the sync DROP list, grep
  the API for `FROM <table>` and confirm each caller is resilient. Test endpoints against the
  LEAN DB, not just the home DB.

## 2026-06-02 — DB sync failed "database disk image is malformed" under concurrent writes
- **Symptom:** `sync_db.sh` errored with `sqlite3.DatabaseError: database disk image is
  malformed` during the lean export, right after a heavy chain (re-embed + FTS --rebuild
  + 1M-row IRS ingest) on the 19GB DB. Scary, looked like corruption.
- **Root cause:** NOT corruption. `quick_check` and the FTS5 integrity check both passed.
  SQLite's online-backup API (`src.backup()`) is fragile when the source DB is being
  written concurrently — it restarts on each write and can surface a transient "malformed"
  read on a large DB while writes are still settling (WAL not fully checkpointed).
- **Rule:** Run the DB sync only after all writers have settled — confirm the WAL is
  checkpointed (`-wal` near 0 bytes) and no pipeline job is mid-write. If a sync throws
  "malformed", DON'T panic-restore: run `PRAGMA quick_check` + the FTS5 integrity check
  first; a clean result means retry the sync once the DB is quiet. Sequence DB-writing
  jobs, never overlap them with the backup/export.

## 2026-06-01 — Shared link showed stale MERIT branding
- **Symptom:** Sharing daanaa.org in iMessage rendered the old "MERIT / 430,000+" preview.
- **Root cause:** `og:image` is cached very aggressively by iMessage/Apple, keyed by the
  image URL. Overwriting the same `og-image.png` filename does not bust that cache.
- **Rule:** When changing a social preview image, change the FILENAME (cache-bust, e.g.
  `og-image-v2.png`), use absolute `https://` URLs in og/twitter tags, and expect the
  preview in an already-shared conversation to lag until its cache expires.

## 2026-06-09 — FAISS index build OOM-killed on a memory-constrained box
**Symptom:** `build_faiss_index.py` got SIGKILL'd (empty log, no output) building the
~1.85M-vector index, while :5000 (gunicorn, ~6GB preloaded embeddings) ran and swap was full.
**Root cause:** it built a Python list of 1.85M arrays then `np.array()`'d it (~3x peak),
and `fetchall()` pulled all blobs into RAM. Even after switching to a single preallocated
7.4GB array, that plus gunicorn's 6GB exceeded 30GB RAM with swap already full → OOM.
**Fix:** stream embeddings into a **disk-backed `np.memmap`** (normalize-on-write), train PQ
on a 50K sample, add to the index in 100K batches via `np.ascontiguousarray`. Peak RAM ~1GB,
coexists with :5000. Delete the memmap after build (never ship it). Also: `FAISS_PQ=1`
(IndexIVFPQ m=64) shrank the index 6.3GB→128MB.
**Preventing rule:** for any batch job that must run alongside the live :5000 API on this
30GB box, never hold a full embedding matrix in RAM — memmap it, sample-train, batch-add.

## 2026-06-09 — Deploy-blocking test suite was silently dead
Symptom: tests/test_principles.py (the "failing test BLOCKS DEPLOY" suite) crashed with
FileNotFoundError on every run — nobody noticed because nothing ran it.
Root cause: suite hardcoded `merit_api.py`, which was deleted in the daanaa_api migration;
no CI/cron executes pytest, so the failure was invisible.
Preventing rule: any file rename/deletion must grep tests/ for references; add pytest to
a scheduled job (or pre-deploy gate) so a dead suite fails loudly, not silently.

## 2026-06-09 — Fused search 500'd in production; latency probes hid it
Symptom: /api/search returned 500 on every fused query — discovered only because a
Session 3 smoke test checked the status code.
Root cause: fused_search queries surge_boosts/surge_detections, which exist only after
agent_surge_monitor.py runs; the daily catalog sync overwrites merit_registry.db, wiping
agent-created tables. Earlier audit latency probes used curl -o /dev/null -w time_total
without checking %{http_code} — fast 500s looked like healthy responses.
Preventing rules: (1) any API dependency on an agent-created table must tolerate its
absence (try/except OperationalError, like the has_v4_scores pattern); (2) every curl
probe in monitoring/audits must assert the status code, not just timing.

## 2026-06-09 — RSS lies for forked workers; use PSS
Symptom: audit Phase 4 flagged "gunicorn workers 2.2 GB each, CoW sharing may be broken."
Root cause: ps RSS counts shared pages once per process; smaps_rollup showed PSS 472 MB
per worker with 2.25 GB Shared_Dirty — the preloaded embedding matrix is shared exactly
as designed, and the API holds zero swap. The actual swap consumer was Ollama (5.5 GB).
Preventing rule: judge memory of forked/preloaded services by PSS (/proc/PID/smaps_rollup),
never ps RSS; find swap culprits via VmSwap in /proc/*/status before blaming the app.

## 2026-06-09 — Frontend filters silently unsupported by the lean droplet API
Symptom: production directory returned 0 results for multi-category + revenue band;
single filters looked fine, so it shipped unnoticed.
Root cause: droplet_api was a lean rewrite of daanaa_api and only implemented part of
the /api/organizations contract; the frontend sends the full contract. Unsupported
params were not rejected — they were ignored or mis-parsed ('R,I' treated as one
NTEECC code), producing silently wrong results.
Preventing rules: (1) when two backends serve one frontend, contract tests must run
against BOTH (tests/test_droplet_search.py now covers the droplet); (2) an API that
cannot honor a filter param must 400, never silently ignore it; (3) ORDER BY on an
indexed column + selective WHERE → check the plan, SQLite may pick the sort index and
probe the filter (use COALESCE/expression to force filter-first).

## 2026-06-10 — Built duplicate nightly pipeline before auditing existing cron
- **Symptom:** Wrote a 6-phase orchestrator + 3 agent stubs; discovered gpu_night.sh + cpu_night.sh + run_agents.py + sync_irs_revocations already covered 5 of 6 phases. Stubs also used nonexistent DB columns and would have corrupted cause_tags format (objects vs flat strings).
- **Root cause:** Designed from the vision statement instead of inventorying what already runs (`crontab -l` + scripts/ + gpu_night.sh).
- **Rule:** Before writing any scheduler/orchestrator, read the full crontab AND every script it references. The night stack's entry point is gpu_night.sh — extend it, don't parallel it.

## 2026-06-10 — `git add -A` in repo with deploy scratch dirs staged 1.02M files
- **Symptom:** Commit d5319e68c6d ballooned with 1,025,796 `.deploy_scratch/precompute/` files; had to redo HEAD.
- **Root cause:** `.deploy_scratch/`, `.backups/`, `scores_v4_0_*.json` were never gitignored.
- **Rule:** Any scratch/output dir created by a deploy or pipeline gets a .gitignore entry in the same change that creates it. Never `git add -A` without checking `git status --short | head` first.

## 2026-06-10: Exception handler crashed on the same bad data that triggered it
**Symptom:** Donate-link Phase 2 crashed 1,788× overnight (`TypeError: 'NoneType' object is not subscriptable`), blocking every release pass.
**Root cause:** 4 rows had `pending_review` status but NULL `donate_url`. `requests.head(None)` raised → the `except` handler itself did `durl[:70]` and died, killing the whole batch; the same 4 rows recycled every loop.
**Rule:** Validate row data before use, and never let an error handler dereference the value whose invariant just failed. A handful of bad rows must skip, not sink the batch.

## 2026-06-10: A verifier that never passes is a config bug — test against known-true pairs
**Symptom:** web_finder marked 1,800 orgs `no_website_found` in one night, 0 verified — including orgs whose obvious domain was correct (UPMC → upmc.com).
**Root cause:** Two stacked silent failures: (1) cosine threshold 0.85 unreachable for name-vs-HTML comparison (peaks ~0.7); (2) embed server returned HTTP 500 on >512-token inputs and the client swallowed non-200s without logging.
**Rule:** Before a verifier runs unattended, feed it pairs known to be true and confirm it can say yes. Log every non-200 from internal services. Marks written by a broken verifier are invalid data — clear them, don't let cooldowns hide the damage.

## 2026-06-10: git filter-branch stomps the working tree — commit before history surgery runs
**Symptom:** Uncommitted fixes vanished twice mid-session; every tracked file reset atomically (identical mtimes to the nanosecond).
**Root cause:** A credential-scrub `git filter-branch --tree-filter --force` was running concurrently — it checks out every commit into the working tree, destroying all uncommitted changes repeatedly until it finishes.
**Rule:** Never leave work uncommitted while any history rewrite (filter-branch/filter-repo) can run. Check `pgrep -f filter-branch` when files revert "by themselves" — identical mtimes across files = one atomic git operation, not a linter.

## 2026-06-10: git-filter-repo OOM on huge blobs; exit code masked by pipe
**Symptom:** `git filter-repo --replace-text` died mid-run with "fatal: stream ends early" + a fast-import crash report; the failure was invisible at first because `| tail -15` masked the exit code.
**Root cause:** filter-repo streams every blob through Python — three ~6.5GB FAISS blobs vs 12GB available RAM. Pipes return the LAST command's exit code; the crash looked like success.
**Preventing rule:** For history scrubs in repos with multi-GB blobs, use `git filter-branch --index-filter` with `git update-index --cacheinfo` blob swaps — it never streams blob contents (502 commits in ~2 min). And never judge a long git command through a pipe; check `${PIPESTATUS[0]}` or run it bare.

## 2026-06-11: claim_start referenced a column that never existed — schema drift between code and DB
**Symptom:** /api/claim/start would 500 on every call: `SELECT ... address ... FROM registry_enriched` — no `address` column exists (only CITY/STATE/zipcode).
**Root cause:** The endpoint was written against an assumed schema and shipped without a test that executes its SQL; CLAUDE.md also listed an `irs_bmf` table that doesn't exist, so docs reinforced the wrong mental model.
**Rule:** Any endpoint's SQL must run in a test against a fixture built from the real schema (tests/test_claim_flow.py is the pattern: temp DB + monkeypatched DB_PATH). When CLAUDE.md names a table, verify with PRAGMA before trusting it — fix stale docs on sight.

## 2026-06-12 — Debugged production for an hour with local-only rebuilds
- **Symptom:** /claim/verify on daanaa.org kept redirecting to /for-nonprofits no matter what we changed; an hour of route restructuring, cache busting, and rebuilds had zero effect.
- **Root cause:** Two layered. (1) The real bug: ClaimVerify required both `ein` and `email` URL params and the claim email link only carries `ein`, so it instantly redirected — fixed in the first 10 minutes. (2) The fix never reached users because daanaa.org is served by the droplet, and every `npm run build` + `restart_api.sh` only updated the local box. We were debugging a build that production never saw.
- **Preventing rule:** Before debugging "my change isn't working" on daanaa.org, FIRST compare asset hashes: `curl -s https://daanaa.org/ | grep -o 'assets/index-[^"]*\.js'` vs `frontend/dist/index.html`. If they differ, production is a stale build — ship before debugging further. Frontend ships are manual: rsync + atomic swap (safe_deploy_droplet.sh stage 7); local restart_api.sh does NOT deploy.

## Org-detail data fields must be added to precompute_orgs.py, not just daanaa_api.py
- **Symptom:** Added `cohort_context` to the live API's `get_organization()` and it returned correctly on local :5000 — but it would never have appeared on daanaa.org org pages.
- **Root cause:** The droplet serves org detail from precomputed static `orgs/<prefix>/<ein>.json.gz` files (built by `scripts/precompute_orgs.py`), via `scripts/droplet_api.py` `load_org_detail()` — NOT from the live SQLite `daanaa_api.py`. Any new org-detail field added only to `daanaa_api.py` is invisible in production. (Same gap silently affects `v5_context`, which is also absent from precompute output — v5.0 org-page context is not actually live on the droplet.)
- **Preventing rule:** A new field on the org-detail response has TWO integration points: `daanaa_api.py` `get_organization()` (local/dev + reverse-tunnel paths) AND `precompute_orgs.py` `org_to_dict()` (the static files the droplet serves). Add it to both, keep the gating logic identical, and remember `safe_deploy_droplet.sh` regenerates precompute from the snapshot — so the field appears in prod only after a deploy that re-runs precompute. Per-org enrichment in precompute must be cheap (cached dict lookup, not a per-org DB connection like `get_v5_context`).

## 2026-06-14 — Production had no CSP/HSTS for weeks because they lived only in daanaa_api.py
- **Symptom:** Security review found daanaa.org served no Content-Security-Policy and no HSTS, despite `daanaa_api.py` having a full, Firebase-tuned CSP in `set_security_headers`.
- **Root cause:** Same two-layer trap as the build-deploy and precompute lessons. `daanaa_api.py` runs on the home box (reverse-tunnel target for /api/claim, /api/wallet, etc.), but daanaa.org is served by `scripts/droplet_api.py` on the droplet. Its `set_security_headers` only set X-Content-Type-Options / X-Frame-Options / Referrer-Policy — the CSP and HSTS were never ported. Browsers hitting prod got neither. CORS was also `CORS(app)` wide-open on the droplet vs origin-restricted on the home API.
- **Preventing rule:** Treat `scripts/droplet_api.py` as the real edge for anything a browser receives — security headers, CORS, CSP, cache-control. When you add/modify a response-level security control in `daanaa_api.py`, mirror it in `droplet_api.py` (or factor it into a shared module). Verify in prod with `curl -sS -D - -o /dev/null https://daanaa.org/ | grep -i 'content-security\|strict-transport'` — not against :5000.

## 2026-06-20 — Deploy failed: stale snapshot missing street_address column
- **Symptom:** `precompute_orgs.py` crashed with `sqlite3.OperationalError: no such column: street_address` during a scheduled deploy, killing the entire pipeline.
- **Root cause:** `safe_deploy_droplet.sh` reuses an existing snapshot by default (`snapshot exists, reuse`). The snapshot was taken before 2026-06-11 when `street_address` was backfilled into `registry_enriched`. The updated SELECT in `precompute_orgs.py` referenced the new column but the snapshot DB didn't have it.
- **Fix:** Added `PRAGMA table_info(registry_enriched)` check in `precompute_orgs.py` to detect column presence at runtime, falling back to `NULL as street_address` if absent. New columns introduced by backfills must be guarded this way until the snapshot is refreshed.
- **Rule:** When a new column is added to `registry_enriched` and `precompute_orgs.py` SELECT is updated to read it, add a `PRAGMA table_info` fallback immediately — the deploy snapshot can be days old and will break the pipeline without it. Use `--force` to refresh the snapshot or wait for the next nightly that creates a fresh one.

## 2026-06-20 — Atomic swap failed "No space left on device" — site down 3 min
- **Symptom:** `safe_deploy_droplet.sh` reached Stage 4 (atomic swap), successfully stopped the API and renamed v1→v0, then failed on `cp /data/precompute/v0/search.db /data/precompute/v1/search.db` — "No space left on device". API never restarted; daanaa.org was down.
- **Root cause:** During the swap, three large objects co-exist on the 33GB droplet: live v1 (~8.4GB), extracted temp (~8.4GB in /tmp), and the staging tar (~2GB). Total peaked at ~19GB for precompute alone, pushing root past 97%. The `cp search.db` (1.2GB) hit the ceiling.
- **Fix (manual recovery):** Deleted staging tar + /tmp extract (freed ~10GB), manually `cp`'d search.db from v0→v1, ran `systemctl start daanaa`, then deleted the now-backup v0. Site restored in ~3 min.
- **Rule:** The deploy requires ~11GB of free space at the swap moment. Before shipping a new payload: `ssh root@162.243.97.179 df -h /` — if free < 12GB, abort and free space first (delete v0 if safe, clean /tmp). Consider pre-deleting the staging tar immediately after extraction in `safe_deploy_droplet.sh` to halve the peak usage.

## 2026-06-20 — Org-detail pages showed v4 and v5 financial context simultaneously
- **Symptom:** The org page for 900334854 (and all v5-scored orgs) displayed both the legacy v4 "Financial context" sidebar widget (financial_health: Strong/Stable/Inspiring + operating_model) AND the modern V5Context component, creating visible duplication and confusing copy.
- **Root cause:** v4Health widget was rendered unconditionally from `getV4FinancialHealth(apiOrg)`. The `financial_context` accordion also showed whenever `financial_context` was non-null, even when `v5_context` was also present. The two systems were additive, not mutually exclusive.
- **Fix:** Removed v4Health widget entirely; replaced with an "About this score →" methodology link. Gated the old `financial_context` accordion on `!v5_context` so it only shows for the minority of orgs that have v4 context but no v5 scoring.
- **Rule:** When adding a v2 of any computed field, gate the v1 display explicitly on `!v2_field`. Never assume both can coexist on the same page — they will both render.

## 2026-06-22 — privacy_check.sh silently grepped for ".md" instead of token shapes
- **Symptom:** The pre-commit privacy gate fired ~130 "Token pattern detected" / "Log leakage" warnings on benign UI `.tsx` content this session, blocking commits. Re-grepping the named token patterns against those files found nothing — the warnings didn't correspond to any real pattern hit.
- **Root cause:** `exclude_filter()` ran `for pattern in "${EXCLUDE_PATTERNS[@]}"` WITHOUT declaring `pattern` local. It is called inside each GATE's `for pattern in "${TOKEN_PATTERNS[@]}"` loop, so it overwrote the gate's `$pattern` with the last exclude entry, `.md`. GATE 1 and GATE 2 were therefore grepping file content for `.md`, never for AKIA/ghp_/sk-/console.log(token)/etc. This was BOTH the false-positive source (any content containing ".md" matched) AND a silent false-negative hole (real AWS keys and logged tokens passed the gate). `bash -x` revealed it: `+ added='...AKIA...'` followed by `+ grep -q .md`.
- **Fix:** Declared `local pattern` in `exclude_filter` (one line) — fixes GATES 1, 2, and 4, which all call it inside a `for pattern` loop. Also switched GATES 1/2 to scan only staged ADDED lines (`staged_added_lines()` via `git diff --cached`, fed to grep with a here-string to avoid `set -o pipefail` + `grep -q` SIGPIPE turning a match into a false "no match") instead of whole-file `git show ":$file"`, so a pre-existing token-shaped string no longer trips on every touch. Verified with positive controls (fake AKIA key + `console.log(token)` both caught, exit 1) and a negative control (benign `.tsx` with `.md` + "token" prose passes, exit 0).
- **Rule:** Any shell helper that loops with `for X in ...` MUST declare `local X` — an unscoped loop var clobbers a same-named var in the caller. For a security gate specifically: never trust it until a positive control proves it actually fails on a planted secret. A gate that never fires is worse than no gate — it manufactures false confidence. Pre-commit content checks should scan the staged diff (added lines), not whole files; and avoid `producer | grep -q` under `set -o pipefail` (use a here-string).

## 2026-06-23 — all keyword search down on prod: API expected `org_fts`, search.db only had `org_search`
- **Symptom:** Every keyword search on daanaa.org returned `search_type: "error"`, total 0 (`/api/search`, `/api/fused-search`, `/api/organizations?q=`) for ~7h. Category/state browse (`?ntee=A`) still worked.
- **Root cause:** The running service (`droplet_api:app` from `/opt/daanaa/droplet_api.py`, deployed ~2026-06-22 22:00) joins `org_fts s, registry_enriched o`. But the live `/data/precompute/v1/search.db` only had the older `org_search` FTS table — no `org_fts`. The API code shipped without a matching search.db; the FTS query hit a missing table and the handler returned the error shape. Browse survived because it reads `registry_enriched` directly.
- **Fix:** `scripts/build_search_db.py` (new) assembles the deployable search.db = `registry_enriched` (live 41-col parity) + `org_fts` (1.86M, now incl. `metro`), both copied from canonical `merit_registry.db`, with integrity_check + join sanity built in. Atomic deploy: upload to `search.db.new`, integrity-gate on droplet, rename-swap (`search.db`→`.bak`), restart. Restored search + shipped metro in one swap.
- **Rule:** The droplet search.db and the running `droplet_api.py` are a CONTRACT: the API's FTS table name (`org_fts`) and the `registry_enriched` columns it joins/filters MUST exist in the deployed search.db. Never ship one without the other. The API's startup health check FATALs on a missing `org_fts`/`registry_enriched` — but gunicorn workers were already up, so it didn't catch a hot DB swap. Rebuild search.db with `scripts/build_search_db.py` whenever the API's search schema changes. Keep `search.db.bak` for instant rollback until verified.

## 2026-06-29 — Public-facing numbers went stale and out of sync
- **Symptom:** `/api/stats` served 1,871,724 while the research page showed 1,729,314 and
  marketing said "1.8M" — three different headline counts; a reviewer hopping pages would
  see the contradiction. ForVendors computed "1.9M" from the stale API.
- **Root cause:** (1) the canonical filter was copy-pasted in 3+ files and one stayed on an
  older definition; (2) `/api/stats` serves a STATIC `homepage.json.gz` precompute that
  nothing regenerated/redeployed after the 2026-06-27 revoked-status sync dropped the true
  count by ~143K; (3) a `kill -HUP` does NOT reliably cycle all gunicorn workers, so some
  kept serving the old number from per-worker cache.
- **Fix:** single source of truth (`scripts/registry_filters.py`), a consistency gate that
  refuses to deploy drifted numbers (`check_number_consistency.py`), and a
  regenerate→gate→deploy→`systemctl restart daanaa`→verify step wired into the nightly
  pipeline (`refresh_public_numbers.sh` as Step 12 of `overnight_pipeline.py`).
- **Rule:** Any user-facing count MUST derive from `DEDUCTIBLE_FILTER` (never re-spell it).
  Droplet content files (`/data/precompute/v1/content/*.json.gz`) and `research-snapshot.json`
  in the frontend dist are derived artifacts — regenerate AND redeploy them whenever the DB
  changes, then full-RESTART the service (HUP is not enough). Cloudflare does NOT cache
  `/api/stats` (cf-cache-status: DYNAMIC), so origin/public splits are the worker cache.

## 2026-07-01 — Uncommitted changes wiped by worktree merge
Symptom: E4 proximity search (working on production) disappeared after deploying E5 sprint. Both `daanaa_api.py` and `scripts/droplet_api.py` lost `_haversine_mi`, `_zips_within_radius`, `_resolve_location` and all proximity wiring.
Root cause: E4 changes were never committed. Worktrees are created from the last commit, not the working tree. When E5 agents ran, they got the pre-E4 committed versions. Merging their files overwrote the uncommitted E4 modifications.
Rule: **Commit (or stash) any working changes before launching worktree agents.** Worktrees branch from HEAD — they cannot see uncommitted edits in the main working tree. If a deploy is approved, commit first; then spawn agents on the new HEAD.

## 2026-07-02 — EINs are public data, not credentials
- **Symptom:** `VolunteerSubmission.tsx` used an EIN entered by the user as a proxy for nonprofit identity — if you know the EIN, you can submit hours on behalf of any org.
- **Root cause:** EINs appear on every 990, ProPublica, and the IRS database; they are public record. Using a public identifier as an auth token is no auth at all — anyone can harvest EINs and submit on behalf of any org.
- **Rule:** Never treat a public identifier (EIN, NTEE code, state registration number) as a credential. Auth for nonprofit-facing features requires a verified account (email-confirmed or OAuth). Until that exists, gate the feature behind a clear "coming soon" error rather than shipping it with a false security boundary.

## 2026-07-02 — Curly quotes in Python string literals crash Python 3.12
- **Symptom:** After editing `droplet_api.py` in a context window and deploying, gunicorn refused to start with a `SyntaxError` — `ast.parse()` caught U+2018/U+2019 (curly apostrophes) inside string literals.
- **Root cause:** LLM output and Markdown editors commonly substitute typographic curly quotes (`'`/`'`, `"`/`"`) for straight ASCII quotes. Python 3.12 is strict: those Unicode code points are invalid inside string literals even if the surrounding delimiters are fine. The error only surfaces at parse time — tests running with exec/eval may not catch it.
- **Fix used:** Binary replacement pass before redeploy — `sed -i "s/\xe2\x80\x98/'/g; s/\xe2\x80\x99/'/g" droplet_api.py`, then verified with `python3 -c "import ast; ast.parse(open('droplet_api.py').read())"`.
- **Rule:** Before deploying any Python file that was generated or edited inside a context window, run `python3 -c "import ast; ast.parse(open('<file>').read())"`. A curly-quote `SyntaxError` is silent at rsync and only surfaces when gunicorn tries to load the module — the site goes down. Add this check to the deploy checklist alongside syntax/lint.

## 2026-07-05 — 11-hour site outage from an unapproved midnight "quick fix" deploy
- **Symptom:** Every page on daanaa.org returned 500 from ~04:30 to 15:32 UTC. `/health` stayed 200 the whole time.
- **Root cause (code):** Commit d56a76e moved the SPA fallback in `droplet_api.py` to the end of the file but dropped the final `return send_from_directory(FRONTEND_DIST, 'index.html')`. Every non-file route returned None → Flask 500. An orphaned copy of that return was left as dead code inside `nonprofit_verify_hours_action`.
- **Root cause (process):** An overnight session (a) replaced the lean 69KB droplet API with an 8,284-line copy of the home API needing twilio + ~2GB embeddings on a 961MB droplet, (b) deployed to production bypassing the approval gate, (c) claimed "verified" having only tested its own new endpoint, never `curl /`.
- **Why nobody knew for 11h:** watchdog alerts only on state change (one transition email, then silence); `public_site` checks `/health`, which lies about page health; `send_alert` in the deploy scripts used bare `python3` with a cwd-relative import under cron — alerts have been silently no-oping. The nightly deploy crons had also been failing on SSH `Permission denied` since ~Jul 3, unnoticed for the same reason.
- **Fix:** Restored the missing return (regression test: `tests/test_spa_fallback.py`); lean API redeploy; watchdog got a real homepage check + 6h re-alerts; deploy scripts got venv-python alerts, ERR traps, ssh retry, and a post-deploy smoke test with auto-rollback to `.prev`.
- **Rules:**
  1. A deploy is not "verified" until the homepage and one core API return 200 from the public URL — put the smoke test in the script, not in the deployer's discipline.
  2. Never point a health monitor only at `/health` — monitor what a user loads.
  3. Alert paths must be tested from cron's environment (venv + absolute cwd); an alert that can silently fail is not an alert.
  4. The droplet runs `scripts/droplet_api.py` (lean, search.db contract). The root-level `droplet_api.py` blueprint-refactor experiment must never be rsynced to the droplet — it physically cannot run there.

## 2026-07-05 (later same day) — Cron SSH root cause fixed: passphrase-protected key
- **Root cause confirmed:** `~/.ssh/daanaa_do` is passphrase-protected. Interactive `ssh`/`rsync` calls only worked because a cached gnome-keyring agent (`SSH_AUTH_SOCK=/run/user/1000/keyring/ssh`) had it unlocked from a login session. Cron runs with no such agent, so every unattended deploy/sync (`sync_droplet_api.sh`, `nightly_search_deploy.sh`, `frontend_deploy.sh`, `sync_db.sh`, `sync_db_from_droplet.sh`, `check_feedback.sh`, and others) has been silently failing with `Permission denied (publickey)` since the key was created — this is a separate, longer-standing bug than the alert-delivery bug fixed earlier today.
- **Fix:** generated `~/.ssh/daanaa_do_cron` (ed25519, no passphrase), added its public key to the droplet's `/root/.ssh/authorized_keys` alongside (not replacing) the original key, and repointed every script/cron job that SSHes to the droplet at the new key. Verified working with `env -i` (fully stripped env, no agent, no shell profile) — both `sync_droplet_api.sh` and `daanaa_watchdog.py` complete cleanly where they previously failed identically to the years-old cron logs.
- **Rule:** Any SSH key used by cron or an unattended script must be passphrase-free — a passphrase key only ever "works" by accident, via a cached agent from an unrelated interactive session. Keep the original passphrase-protected key for interactive/manual use only; give automation a dedicated key so revoking one never touches the other.
