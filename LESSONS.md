## 2026-07-19 — URL "sanity" without domain knowledge scores junk at 95% confidence

**Symptom:** 742 donation links sat in pending_review at confidence 90-95, all
scheme-less, top entries being donation platforms' own widget-installer pages
(donorbox.org/install-popup-button, checkout.square.site/pay/merchant,
givebutter.com/elements). Promoting them would have pointed donate buttons at
setup documentation.

**Root cause:** The GPU discovery path's QualityGate.url_sanity scored URLs on
FORM only (length, scheme, injection chars) — a perfectly-formed URL to a
platform's installer docs passes every formal check. The main pipeline's
_GENERIC_DONATE_RE knowledge existed but wasn't shared with the GPU path
(same duplicated-function drift class as the FTS sanitizer, same week).

**Preventing rules:** (a) URL validation for donate links MUST include the
platform-infrastructure blocklist — form checks alone cannot distinguish "a
donation page" from "a page about donation pages." (b) When the same concept
(generic-URL detection, query sanitizing) lives in two pipelines, add the
KEEP-IN-SYNC comment pair and a cross-file test. (c) A review queue that only
grows is a signal, not a backlog — audit its top URL patterns before bulk
promotion, ever.

## 2026-07-18 — FTS5 gives punctuation syntax meaning; a swallowed error is a silent 0-result page

**Symptom:** Donors searching real org names with punctuation ("4-H", "St. Jude's",
"TRIPLE-CORD") got empty results on daanaa.org. 4.3% of small-org self-searches
errored. Nobody noticed because the droplet wrapped search in `except Exception:
return 0 results`.

**Root cause:** Two stacked failures. (1) The sanitizer's strip list enumerated
some FTS5 metacharacters but not `-` (column-NOT: "no such column: CORD"), `:`
(column filter), or `/` (syntax error) — an allowlist of known-bad characters
always loses to a parser with more syntax than you remembered. (2) The generic
exception handler converted the crash into a silent empty page — indistinguishable
from "no such org exists," which donors believe.

**Preventing rules:** (a) Sanitize user text into FTS MATCH by stripping
everything that isn't `\w` or whitespace (deny-by-default), never by enumerating
bad characters. (b) A caught search exception must be visible somewhere
(zero-result analytics, logs) — "silent wrong results violate the trust
principles harder than errors do" (test_droplet_search.py header, proven again).
(c) Any duplicated function across the two backends needs a cross-file test
(`tests/test_search_quality.py` pattern).

## 2026-07-18 — Deploy smoke probes can fail while the deploy succeeded

**Symptom:** `sync_droplet_api.sh` reported "SMOKE TEST FAILED … Rollback FAILED
— MANUAL ACTION NEEDED" — alarming. The site was healthy the whole time and the
new code was live and verified.

**Root cause:** Three rapid consecutive SSH connections (deploy, restart, probe)
hit connection-refused — SSH-level throttling, not service failure. The script
interpreted an unreachable probe channel as a failed deploy, then the rollback
attempt failed on the same refused SSH.

**Preventing rule:** When a deploy script reports failure, verify BEHAVIORALLY
via the public URL before acting on the report (curl the pages + the specific
changed behavior). Distinguish "probe channel down" from "service down" —
the script should back off and retry SSH probes, and prefer HTTPS probes of
the public URL which don't share the SSH failure domain.

## 2026-07-17 — Crontab near-wipe #2: manual `crontab` edits are landmines

**Symptom:** Two cron jobs added manually via `crontab -l > tmp; echo >> tmp; crontab tmp`
earlier in the day were silently wiped hours later when `setup_cron_schedules.sh`
(the canonical full-replace installer) was re-run for an unrelated addition.

**Root cause:** Two write paths to one resource. The installer is documented as the
single source of truth and REPLACES the whole crontab; any job added outside it has
a lifespan of "until the next installer run."

**Preventing rule:** NEVER edit the crontab directly. Every new job goes into
`scripts/setup_cron_schedules.sh` first, then the script is run. The installer's
pre-replace backup (logs/crontab_backup_*.txt) is the safety net, and the same-day
detection here worked only because the jobs were minutes old.

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

## 2026-07-05 (later) — Zip/location search silently inherited the hidden-gems default
- **Symptom:** Founder testing zip code search found the first response felt wrong; verified against prod that a real zip (97201, 25mi) returned **0 results**.
- **Root cause:** `Directory.tsx`'s `effectiveHiddenGem` only dropped the hidden-gems default when there was a typed text query (`!debouncedQuery.trim()`). The separate "Zip or city, state" location field (`near`) was never checked, so any location-only search silently kept `hidden_gem=1`, narrowing to the ~34K gems subset — often empty for a given radius.
- **Fix:** `effectiveHiddenGem = hiddenGem && !debouncedQuery.trim() && !near` (Directory.tsx:227). Verified via live API diff (0 → 5,466 results for the same zip) before and after deploy.
- **Rule:** Any deliberate narrowing action (typed query, location filter, and any future one like this) should drop implicit default filters — the same pattern already existed for text search but wasn't generalized. Grep for other `!debouncedQuery.trim()`-only checks if new search entry points are added.

## 2026-07-05 (later still) — Browse regen deployed but invisible for ~1h: restart.sh doesn't restart
- **Symptom:** Regenerated all browse precompute files with the July 4 name-ASC fix (137K files, verified correct locally and on-disk on the droplet after rsync), ran `deploy_browse.sh`, health check passed — but live `/api/organizations?ntee=T` still returned the old merit_score-DESC order and a stale total count, both on daanaa.org and hitting the droplet's origin IP directly (ruled out Cloudflare: `cf-cache-status: DYNAMIC`).
- **Root cause:** `/opt/daanaa/restart.sh` (called by `deploy_browse.sh` and `deploy_similar_orgs.sh`) kills whatever PID is in a stale `api.pid` file and launches a **second, unmanaged** gunicorn bound to `0.0.0.0:5000` — but the systemd-managed `daanaa.service` is already bound to `127.0.0.1:5000`. The new process fails to bind and exits; the script's own `curl localhost:5000/health` then hits the *original, never-restarted* process and reports healthy. Confirmed via `systemctl show daanaa --property=MainPID,ActiveEnterTimestamp`: the serving process had a start time from hours earlier than the "restart."
- **Fix:** `systemctl restart daanaa` directly in both `deploy_browse.sh` and `deploy_similar_orgs.sh`, replacing the `restart.sh` call. `/opt/daanaa/restart.sh` itself is left in place but must not be used — it predates the systemd unit and actively lies about restart success.
- **Rule:** Any deploy script must verify against the *actual serving process* (systemd MainPID/ActiveEnterTimestamp, or the data itself), not just a health endpoint — a health check can pass against an old process while a new one silently failed to take over. This is the same shape of bug as the 2026-06-27 "kill -HUP doesn't cycle workers" lesson: a restart mechanism that looks successful but isn't.

## 2026-07-06 — Directory/search down 3.3h: root droplet_api.py shipped again (2nd occurrence)
- **Symptom:** daanaa.org /directory yielded no results; `/api/search` returned 500 from 13:25 to 16:43 CDT. Homepage and static precompute pages stayed 200.
- **Root cause:** `/opt/daanaa/droplet_api.py` had been replaced with a ~347KB root-lineage file (the home-API variant, 29 refs to `v4_scores`) during the 2026-07-06 donation-links session. Every DB-backed route died on `sqlite3.OperationalError` — `no such table: v4_scores` (fused_search), `no such column: subsection` (list_organizations), `no such table: org_embeddings` (startup) — schema that exists only in the home `merit_registry.db`, never in the droplet search.db contract.
- **Why detection lagged:** the watchdog DID alert at 13:25 (`search: ok -> down (HTTP 500)`) then went silent (state-change-only alerting). Discovery came from the founder noticing the empty directory.
- **Fix:** `bash scripts/ops/sync_droplet_api.sh` redeployed the correct 69KB `scripts/droplet_api.py`; smoke passed; verified search + org listing from the public URL. Prevention: the sync script now refuses any source referencing `v4_scores`/`org_embeddings` and its smoke test also checks `/api/organizations` (commit cedaf10854c).
- **Rules:**
  1. LESSONS 2026-07-05 rule #4 was violated within 24h by a session that read it — structural guards beat discipline. Only `sync_droplet_api.sh` may write `/opt/daanaa/droplet_api.py`; never hand-rsync it.
  2. "Code deployed" in a checkpoint is not evidence — curl the public URL before recording a deploy as done.
  3. Appends to shared docs (LESSONS/DECISIONS) from a session running parallel to another session can be silently lost — commit doc appends immediately.

## 2026-07-06 — Open findings from the same investigation (partially addressed)
- **DB path mismatch (OPEN):** the systemd unit sets BOTH `DB_PATH` and `LIVE_DB_PATH` to `/data/precompute/v1/search.db`, but `nightly_search_deploy.sh` ships fresh catalogs to `/data/search.db` — nightly refreshes have NOT reached the live DB since Jul 5. Live user tables (org_claims, waitlist, donor_users, …) also live inside that catalog file instead of `daanaa_live.db`; repointing requires migrating live rows first.
- **S3 deploy dead path (cron still enabled):** the 3:35am `deploy_via_s3.sh` cron writes a 2.0GB `merit_registry.db` to `/opt/daanaa/data/` which nothing reads (its relative `./scripts` path also never resolves under cron). The donate-link DATA did reach the live DB via the Jul 6 incremental sync — what blocks serving them is the deliberate `_strip_donate` policy gate in `scripts/droplet_api.py:282` (2026-06-10 legal posture), a product/legal decision, not a bug.
- **Droplet resized 2026-07-06:** $8→$16/mo plan (1 vCPU, 2GB RAM, 70GB NVMe) to resolve chronic disk pressure (96% since the Jul 6 S3 copy landed).

## 2026-07-07 — Sibling-module imports must match the script's actual invocation path, not just the test's
- **Symptom (caught before it shipped):** Task 1 of the enrichment-consolidation plan asked for `from scripts.donate_confidence import ...` inside `scripts/donation_link_pipeline.py` when extracting shared functions.
- **Root cause:** `donation_link_pipeline.py` is invoked directly as a script (`python3 scripts/donation_link_pipeline.py ...` via `cpu_night.sh`), not imported as `scripts.donation_link_pipeline` — under direct invocation, `sys.path[0]` is `scripts/` itself, so `from scripts.X import Y` raises `ModuleNotFoundError: No module named 'scripts'`. The file already had a working sibling-import for `check_link_health` (bare `from check_link_health import (...)`, relying on its own `sys.path.insert`), which was the correct pattern to follow instead.
- **Rule:** when adding an import to an existing script, check how *that specific file* is actually invoked (direct script vs. package import vs. both) before assuming the `scripts.X` package-style import used elsewhere in the repo (e.g. in `enrich_batch.py`, which IS both directly run and pytest-imported, hence its explicit `sys.path` shim) is the right pattern here too. Two files in the same directory can need two different import styles depending on their own invocation contract — pytest passing is not proof a script-invoked file still works under cron.

## 2026-07-07 — Task brief's own spec code assumed a table the shared test fixture doesn't create
- **Symptom:** Task 2 (`scripts/website_content.py`) brief specified `_cache_page()` doing a bare `INSERT OR REPLACE INTO page_cache (...)` against the shared `test_db` fixture (`tests/fixtures.py`). Running the brief's own test file verbatim gave `sqlite3.OperationalError: no such table: page_cache` on `test_validate_and_fetch_website_success` — only the one test that explicitly `CREATE TABLE IF NOT EXISTS page_cache` (the caching-specific test) passed; the fixture itself never defines that table.
- **Root cause:** `page_cache` is defined by `donation_link_pipeline.init_schema()`, not by the shared `test_db` fixture — the brief assumed the table would already exist wherever this code runs, but neither the fixture nor `website_content.py` itself guarantees that.
- **Fix:** made `_cache_page()` defensively run `CREATE TABLE IF NOT EXISTS page_cache (...)` (same schema as `donation_link_pipeline.py`) before the insert, since `page_cache` is shared infrastructure not owned by either caller. Idempotent — doesn't conflict with the one test that also creates it explicitly.
- **Rule:** when a brief's spec code touches a table it doesn't own (shared/cross-module schema), don't assume the caller's environment already created it — run the tests against the actual fixture before trusting a brief's "Expected: N passed" count, and make shared-table writes self-sufficient (`CREATE TABLE IF NOT EXISTS`) rather than assuming init order.

## 2026-07-09 — Full-API deploy crashed the droplet: 1.9GB RAM box cannot run daanaa_api.py (site down ~1.5h, power-cycle required)
- **Symptom:** After deploying `daanaa_api.py` (full backend) to the droplet with `--preload`, the service entered a 23-restart loop, ate all RAM + swap loading 537K embeddings (~2.2GB), and memory-thrashed the box so hard SSH banner exchange timed out. Site returned 502 → 522 → dead. Only a manual DigitalOcean power cycle recovered it.
- **Root cause:** the 2026-07-06 droplet resize was $16/mo = 1 vCPU / **2GB RAM** / 70GB **disk**. "70GB" is storage, not memory. `daanaa_api.py._load_embeddings()` needs more RAM than the whole box has; with `Restart=always` each OOM respawn re-triggered the load, so the box could never recover on its own.
- **Fix:** power cycle via DO console (service was `disabled` so it didn't auto-restart into the same crash); reverted systemd unit to `droplet_api:app` (precompute architecture); rebuilt search.db fresh via `scripts/build_search_db.py` (old June 22 artifact had the pre-`org_fts` schema → `mode:error`), rsynced + atomically swapped; all endpoints verified green from the public URL.
- **Rules:**
  1. Before deploying anything that loads big data at startup, check the target's RAM (`free -h`), not just disk. Embeddings-in-RAM (~2.2GB) is a hard floor daanaa_api.py imposes.
  2. The droplet runs `droplet_api.py` + precompute + search.db BY DESIGN, not as a compromise — that is the correct architecture for a 2GB box. `daanaa_api.py` is home-server/testing only unless the droplet is resized to 4GB+ RAM (a spend decision → ask).
  3. `Restart=always` + startup OOM = self-DoS. Any service whose startup can OOM needs `StartLimitBurst`/`RestartSec` tuning or a memory check in ExecStartPre.
  4. A stale search.db artifact fails soft (`mode:error`, search silently empty). After any search.db ship, smoke test `/api/search?q=food+bank` and require `"mode":"fts"` with hits.

## 2026-07-09 — Enrichment Layer 2 spun on the same 1,000 orgs all night (51+ batches, zero progress)
- **Symptom:** every batch logged the identical line `0 contact | 4 programs | 0 embeddings from 1000 orgs`. 115,702 orgs eligible; only 1,000 ever touched.
- **Root cause:** the Layer-2 SELECT had `LIMIT 1000` with no ORDER BY, no cursor, and no processed-marker filter — SQLite returned the same first rows every invocation. A yield-flag filter alone wouldn't fix it either: 99.6% of orgs produce no extract, get no flag, and would be re-selected forever. Bonus defect: the script UPDATEs `volunteer_url`, a column that doesn't exist in the live DB — those writes fail silently inside the per-org try/except.
- **Fix:** keyset pagination via `logs/enrich_l2_cursor.txt` (`WHERE EIN > ? ORDER BY EIN`), cursor written after each batch, auto-reset on wrap. No schema change needed. `volunteer_url` migration pending founder approval.
- **Rules:**
  1. Any batch job with `LIMIT` MUST have a progress mechanism (keyset cursor, offset state, or processed-marker) — and the identical log line repeating across batches is the tell; a loop that logs the same counts twice in a row should alarm, not reassure.
  2. Per-org `except: continue` blocks hide schema mismatches — verify every column a pipeline writes actually exists in the live DB before a run (PRAGMA table_info check at startup).

## 2026-07-09 — Crontab clobbered: ~60 jobs silently reduced to 2 for 26+ hours (found during "all deployed?" check)
- **Symptom:** watchdog.log, gpu_temp.log, and nightly_search_deploy.log all stop at Jul 8 ~20:30. Crontab contained only 2 entries (enrichment loop + morning deploy). Site monitoring, alerting, nightly scoring, search.db shipping, revocation sync, backups monitoring, and email triage were all dead — nobody noticed because the watchdog that would notice was among the casualties.
- **Root cause:** a session scheduling the enrichment window installed a fresh crontab (`crontab file`) instead of appending to the existing one, replacing ~60 jobs. The clobber was invisible: cron doesn't log removals, and the tonight-log looked healthy.
- **Fix:** restored critical-ops subset (watchdogs, metrics/alerts, overnight pipeline, nightly search deploy, revocation sync, backups, GPU window, email triage) from `backups/crontab.backup_20260622.txt`, verified each script exists first, excluded known-dead entries (night_batch_launcher, retired daily_backup.sh, AWS backup, hardcoded rotated Plausible key). Full review of remaining ~40 entries pending.
- **Rules:**
  1. NEVER `crontab <file>` from a constructed file without first `crontab -l >> file`. Append, don't replace. Always save `crontab -l` to `backups/crontab.backup_YYYYMMDD_HHMM.txt` before any crontab write.
  2. The watchdog can't watch itself — add a cron-integrity check to the watchdog (alert if crontab entry count drops below a floor).
  3. Secrets never belong in crontab lines (the Jun 22 backup carries a hardcoded Plausible API key — move to env file before restoring that job).

## 2026-07-10 — Directory empty + wrong count: precompute browse tree was deleted in the "stateless droplet" experiment, and in-process caches memoized the damage
- **Symptom:** /directory showed total 2,042,897 (raw registry incl. revoked) with zero results; single-category filters returned total 0.
- **Root cause (three layers):** (1) `/data/precompute/v1/browse/` (categories, hidden gems) and `orgs/` were deleted during the 2026-07-09 stateless-droplet mistake and never restored — browse endpoints are file-served with silent empty fallbacks. (2) `_multi_cache` and `_real_total_cache` in scripts/droplet_api.py cached the empty lists and raw count in-process, so even after files returned, responses stayed broken until a restart. (3) `_get_real_total`/`_db_filter_browse`/`_fts_directory` had no public-eligibility filter, so once the raw count surfaced (directory default changed away from hidden gems on Jul 9) users saw 2.04M and revenue/multi-cat results included revoked orgs — a stewardship violation, latent since the count fallback was added.
- **Fix:** rsynced browse (797MB) + orgs (7.6GB) trees back from home precompute_output/; added `subsection/deductibility/org_status/irs_revoked` to build_search_db.py LIVE_COLS (+ index); added `_public_filter()` (fails open on old artifacts) to `_get_real_total`, `_db_filter_browse`, `_fts_directory`; rebuilt + staged-swap search.db; deployed API via sync_droplet_api.sh. Verified: default total exactly 1,729,314 with results; all filter combos + FTS green.
- **Rules:**
  1. The droplet is BOTH file-served (browse/orgs precompute) AND search.db-served — restoring one without the other yields a half-alive site whose /health is green. Any droplet restore checklist must include: search.db, browse/, orgs/, content/, frontend/dist.
  2. Indefinite in-process caches (`_multi_cache`, `_real_total_cache`) memoize outage-era emptiness; after any data-file restore, a service restart is part of the fix, and caches that can memoize an error state should never cache falsy values.
  3. Every browse/filter/search surface must apply the public-eligibility filter; the raw registry (with revoked orgs) exists only for org-detail fallback.

## 2026-07-10 — Radius search silently missed 60% of orgs: zipcode was 40% populated
- **Symptom:** Houston (4th largest US city) + has-website returned 0 orgs; proximity totals generally low.
- **Root cause:** proximity matches `SUBSTR(zipcode,1,5) IN (...)` and zipcode was NULL for 1.22M of 2.04M rows — NULL never matches, so those orgs were invisible to every "near me" query. Same class of bug as the "Houston Texas" resolver: filters that silently drop rows look like working filters.
- **Fix:** `scripts/backfill_zipcodes.py` fills zipcode from `data/bmf.csv` (EIN→ZIP, never overwrites): 821,507 → 1,977,541 (96.8%) in 346s. Ships to droplet via the nightly search.db build. Also moved `nightly_search_deploy.sh` cron 04:00 → 08:15 — the 04:00 run died on "database is locked" against the overnight enrichment loop's writes.
- **Rule:** any filter implemented as `column IN/=/LIKE` must have its column's NULL-coverage checked at design time; a filter over a 40%-populated column is a 60% silent exclusion, not a filter.

## 2026-07-10 — v4_scores schema drift broke 3 endpoints silently (found while chasing an unrelated dev-server bug)
- **Symptom:** `daanaa_api.py`'s `/api/organizations/<ein>` 500'd on every request ("no such column: revenue_band"). Chasing why the dev server "stripped" donate_url/org_status/volunteer_url led here -- they weren't stripped, the whole endpoint was crashing and returning an error payload.
- **Root cause:** `v4_scores` was migrated to a 5-column schema (`EIN, score, tier, band, operating_model`) at some point after several queries were written expecting `revenue_band, peer_cell_size, metrics_json, percentiles_json, financial_health` on that table. Three call sites broke: `get_organization()`, the fused `/api/search`, and `/api/org/<ein>/submission-status` (the last one also referenced a `scored['visibility_tier']` dict key that was never in its own SELECT — a second, independent bug). All three fed `_attach_v4_scores()`, itself a documented no-op ("V4 scores disabled (v5 only)."), so the joins were pure dead weight even before they started crashing.
- **Fix:** removed the broken JOINs (safe — nothing downstream used the joined columns); fixed submission-status to read `tier` from v4_scores and `financial_health` from registry_enriched (where it actually lives).
- **Verification method:** `git stash` the fix, run the full test suite against an isolated DB copy (`DB_PATH=<backup>` env override sidesteps the live dev server's persistent DB lock — `daanaa_api.py` respects `DB_PATH`), record failure count, `git stash pop`, re-run, diff. 53→51 failed, +2 passed, zero regressions — a clean way to prove a fix is net-positive without needing production traffic.
- **Rules:**
  1. When a table gets migrated/simplified, grep the WHOLE codebase for its old column names before considering the migration done — `grep -n "v4_scores\|v4\." daanaa_api.py` found 3 more live call sites beyond the one I was originally fixing.
  2. `daanaa_api.py` holds a persistent DB connection once gunicorn starts (`--preload`), so a standalone `pytest` importing the same module hits `sqlite3.OperationalError: database is locked` at collection time even with a generous `busy_timeout` set on a manual test connection — the app's own connection-open path doesn't set one. Point `DB_PATH` at a read-only backup copy instead of fighting the lock.
  3. The `*/15 * * * * api_watchdog.sh` cron (restored 2026-07-09) auto-revives gunicorn within seconds of any kill — by design, but it means `fuser -k` + pytest doesn't reliably get a lock-free window; don't fight the watchdog, work around it (DB copy) instead.

## 2026-07-10 — "Ship the sitemap" had three different serving surfaces; trace before wiring
- **Symptom:** Task assumed daanaa.org/sitemap.xml contained org URLs that needed reordering.
  Reality: that file is a 4KB static-pages sitemap from `frontend/public/`; the org sitemaps
  only existed on data.daanaa.org (Cloudflare Pages, stale since Jul 1, EIN-ascending); and
  daanaa.org/sitemaps/* 404'd because nginx proxies all non-aliased paths to the API.
- **Root cause:** Three surfaces (frontend static file, droplet nginx, Cloudflare Pages
  overlay) all answer "the sitemap" and are deployed by three unrelated mechanisms
  (`deploy_morning.sh` --delete rsync, nginx aliases, interactive `wrangler pages deploy`).
  Also a false lead: the documented `dist/` vs `visibility/public/` mismatch didn't exist —
  `build_overlay.py` passes `--dist visibility/public` explicitly; the default only applies
  standalone.
- **Rule:** Before shipping any "static" artifact, curl the live URL AND read the nginx
  config AND find every deploy job that writes the target directory. A file placed in a
  directory that another cron rsyncs with `--delete` is not deployed, it's scheduled for
  deletion. Org sitemaps therefore live at `/opt/daanaa/visibility/`, never in the
  frontend dist.

## 2026-07-12 — Concierge tests must seed the activity table before asserting audit logs
- **Symptom:** `tests/test_concierge_confirm.py` passed the endpoint checks but failed on `org_activity` with `no such table: org_activity`.
- **Root cause:** The fixture seeded `registry_enriched` and `org_claims` but forgot the audit table that `_log_org_activity()` writes to.
- **Rule:** Any test that asserts event logging must create the audit table it inspects, or explicitly call the table-init helper before exercising the endpoint.

## 2026-07-12 — A hand-rolled equivalent measures the wrong system
- **Symptom:** First sqlite-vec benchmark (T7) logged a "fails on RAM" verdict (8GB > 2GB droplet)
  that turned out wrong on re-test — real process RSS during an actual `vec0` KNN query was ~41MB.
- **Root cause:** The first test loaded all 2.04M embeddings into Python/numpy arrays and brute-forced
  cosine similarity by hand, instead of exercising sqlite-vec's own `vec0` virtual table and `MATCH`
  query path. That measures "can Python hold 8GB of arrays," a different question than "can this
  library answer a query within a memory budget."
- **Real finding, on re-test with the actual API:** RAM is fine; the real bottleneck is that `vec0`
  has no approximate-nearest-neighbor index — it's a brute-force scan, so latency scales linearly
  with corpus size (67ms at 100K vectors → ~1.4s extrapolated at the full 2.04M corpus).
- **Rule:** When benchmarking a specific library's claimed capability, call the library's actual API
  under test, not a hand-written stand-in for what you assume it does internally. Correct openly per
  STEWARDSHIP.md Principle #6 rather than let a wrong negative result stand as institutional memory
  (see institution/research/DISCOVERIES.md, "CORRECTION to sqlite-vec on Droplet").


## 2026-07-12 — Enrichment ran "green" for a night while both inference servers were down
- **Symptom:** 2026-07-12 enrichment yielded only ~408 orgs (vs ~1,700 typical). Log was a wall of
  per-org "Connection refused" errors to :11437 (Qwen) and :11436 (embeddings), then a fatal
  IntegrityError killed the batch mid-run. Nobody was alerted.
- **Root cause (three stacked failures):** (1) llama-server instances aren't managed by systemd —
  after a reboot/stop nothing restarts them, unlike ollama and llama-warehouse which are units;
  (2) enrich_batch treats a refused connection as a per-org error and keeps burning through the
  queue producing nothing; (3) the enrichment_run INSERT crashed on the UNIQUE constraint when
  re-processing a same-day org, taking down the whole batch.
- **Fixes shipped:** INSERT OR REPLACE (idempotent re-runs), flock single-instance guard on the
  loop script, servers restarted (embed_server.sh + watchdog_llama.sh) and verified end-to-end
  with a 20-org smoke batch before tonight's window.
- **Preventing rule:** Before any overnight window, smoke-test the actual inference endpoints
  (one real completion + one real embedding), not just process presence. Remaining gap to close:
  systemd units for the :11436/:11437 servers so reboots can't silently kill enrichment again.

## 2026-07-12 (later) — Uncheckpointed batch buffered a night's work in RAM, wrote nothing
- **Symptom:** Tonight's freshly-launched enrichment loop ran 35+ minutes with 8 "workers" and
  wrote zero rows to enrichment_run. Found while doing the founder-requested hourly review.
- **Root cause:** `enrich_batch.py`'s default query had `LIMIT max_orgs or 1000000` — with no
  `--max-orgs` flag (the loop script's normal invocation), this matched ~1.96M orgs (effectively
  the entire active registry). All results were held in a Python list and written to the DB in
  one `_write_results()` call only after the ENTIRE loop finished. A run that size would take
  months; if killed at the 8am cutoff or by any crash, 100% of the night's work vanished with
  nothing ever committed. Separately, `--workers 8` was accepted by argparse but never used —
  the loop is single-threaded, so 4 of 5 Qwen concurrent slots sat idle the whole time.
- **Why the earlier 20-org smoke test didn't catch it:** `--max-orgs 20` kept the in-memory
  result set tiny, so the single end-of-run write was fast and looked fine. The bug only
  manifests at the scale of a real unbounded run — same class of mistake as the sqlite-vec
  benchmark lesson above (test the actual system under test, at the scale that matters).
- **Fix shipped:** default LIMIT capped at 5,000 per invocation; `_enrich_layer` now checkpoints
  (write + commit) every `batch_size` orgs via a `finally` block, so a kill/crash loses at most
  one chunk. Verified live: a 150s-timeout smoke test was killed mid-run and 10 rows had already
  landed on disk before the kill.
- **Deferred, not fixed:** actually parallelizing the per-org Qwen calls to use the server's 5
  idle slots. Founder said "credibility over speed" when I found this mid-review — a same-night
  concurrency rewrite of the core enrichment pipeline was the wrong call under time pressure.
  Do this in daylight, tested, not as a live-window hotfix.
- **Preventing rule:** any batch job with an in-memory result list must checkpoint incrementally,
  and any "workers" parameter must either be wired up or removed from the CLI — a silently dead
  concurrency flag reads as "already parallelized" to the next person who benchmarks capacity.

## 2026-07-13 — page_cache had been write-only since it was built; nothing ever read it
- **Symptom found while building tonight's known-website fix:** a new cache-read helper
  (`_cached_page_html`) returned 0 chars on every call, even for rows that definitely existed.
- **Root cause:** `_cache_page`'s `fetched_at` (via `donation_link_pipeline._now()`) stores a
  timezone-AWARE UTC isoformat string. The new read function compared it against a naive
  `datetime.now()` — Python raises TypeError subtracting aware from naive datetimes, which a
  broad `except (ValueError, TypeError): return None` silently swallowed as "cache miss."
- **Wider finding, not just this bug:** `page_cache` has existed for a while (used by both
  `website_content.py` and `donation_link_pipeline.py`) but every caller only ever WROTE to it —
  grep found zero pre-existing reads anywhere in the codebase. Every pipeline re-fetches pages it
  already fetched, forever.
- **Fix:** timezone-aware comparison in the new read path (`datetime.now(timezone.utc)`).
  Verified: cache read returned real content in 0.2ms after the fix, vs. silent 0-byte failure
  before it.
- **Preventing rule:** a broad except clause around a datetime comparison hides exactly this kind
  of bug — it fails the same way for "no row" and "comparison crashed," and only manual isolated
  testing (not the full pipeline, which degrades gracefully to the non-cached path either way)
  surfaced it. When adding a new consumer of existing shared infrastructure, test that consumer's
  new code path directly, not just the pipeline it's embedded in.

## 2026-07-13 — Deploy verifier: probe failure is not service failure (and must not skip rollback)
**Symptom:** sync_droplet_api.sh reported "Service did not restart cleanly" while
daanaa.org served every page fine; SSH was briefly refused mid-restart.
**Root cause:** single `systemctl is-active` probe over SSH conflated transport
failure with service failure — and the FAILED branch skipped the smoke test AND
the rollback, so a genuinely broken deploy would have been left live.
**Preventing rule:** health checks that gate rollback must (a) retry transient
probes, and (b) treat the public smoke test as the source of truth — pages users
see, not unit state. Rollback logic must be reachable from every failure path.

## 2026-07-15 — Crude health heuristic nearly labeled 49% of nonprofits "CRISIS"

**Symptom:** First full run of the Phase 11 financial health pipeline classified
264K of 537K orgs (49%) as CRISIS, based on a single-year operating-margin proxy.

**Root cause:** New heuristic written from scratch instead of checking for the
existing validated methodology. `merit_health_signal_v5` already covers 465K orgs
and deliberately caps its worst label (NEED_SUPPORT, was CAUTION) — the vocabulary
choice is a Charter Article 7 / Stewardship P5 decision, not a technical one.

**Preventing rule:** Before writing any classifier that labels organizations,
check whether a validated scorer already exists (grep for `_v5`, check
registry_enriched columns). If a user-facing label is harsher than the existing
methodology's vocabulary, that is a stewardship violation, not a tuning choice.
A single-year snapshot is never enough evidence for a "crisis" verdict.

**Fix:** Pipeline now sources health_signal from merit_health_signal_v5
(confidence 0.85), falls back to a heuristic whose floor is NEED_SUPPORT
(confidence ≤0.55). Distribution: 249,878 HEALTHY / 223,711 NEED_SUPPORT / 63,940 STABLE.

---

## 2026-07-15 — Language reframed from CAUTION to NEED_SUPPORT (Stewardship P5)

**Decision:** Renamed health_signal category from CAUTION to NEED_SUPPORT across
all tables, API responses, and documentation (migration 019, ~223K rows renamed).

**Why:** Nonprofits are structurally designed to run lean and reinvest all surplus
into mission. "CAUTION" shames them for healthy behavior (low reserves = mission-focused,
not reckless). "NEED_SUPPORT" reframes the identical data as an action signal: "more
supporters can help this org do more." Stewardship P5 (transparency without weaponization):
language shapes behavior. Users reading "CAUTION" think risk; reading "NEED_SUPPORT"
think opportunity. The financial reality is unchanged; the mission-aligned framing is not.

**Implementation:** (1) `nonprofit_financial_health` table schema updated (CHECK constraint);
(2) fallback heuristic in `populate_financial_health_full.py` returns NEED_SUPPORT;
(3) API response in `nonprofit_financial_narrative()` reframed from "some financial pressure"
to "ready for more supporters" — same data, different story; (4) CLAUDE.md updated with
P5 note; (5) all docs using CAUTION renamed (no hardcoded strings remain in code or tests).

**Verification:** `SELECT health_signal, COUNT(*) GROUP BY health_signal` returns expected
distribution with zero CAUTION rows. API endpoint `/api/nonprofit/<ein>/financial-health`
returns `signal: NEED_SUPPORT` + encouraging narrative. Frontend color mapping stays yellow
(same as before, denotes "action needed," not "alarm").

## 2026-07-14 — Hardcoded stats in JSX go stale silently; typed data contracts catch key renames

**Symptom:** /sector-health showed operating-model reserve averages 2-3x below live values
(card: 10.3 mo, live: ~30 mo) for weeks. Separately, the research Program Spending section
rendered an empty chart in production — component read `item.operating_model`, snapshot
had renamed the key to `archetype`; the .map threw inside a .catch that only console.logged.

**Root cause:** (1) Stats hardcoded into JSX from a one-time analysis snapshot have no
refresh path and no freshness label — they cannot age gracefully. (2) The snapshot
loader typed `spending` items with the old key, so tsc was satisfied while production
data disagreed; the runtime error was swallowed by a catch-and-log.

**Preventing rules:** Never hardcode derived statistics into JSX — render from the live
payload (and ship `generated_at`, display "As of" on data pages). When a precompute/snapshot
key is renamed, grep the frontend for the old key the same session. A .catch around data
mapping must surface a visible fallback state, not an empty section.

## 2026-07-16 — GPU discovery pipeline ran for a full day at 0 verified links; two silent-failure bugs stacked

**Symptom:** `gpu_optimized_discovery.py` (33 processes: 1 async fetcher + 32-worker parse
pool) logged "Verified 0 high-quality links" on every single batch since launch, despite
running continuously. Meanwhile the 9 plain `discovery_daemon.py` instances worked fine and
did all the actual link discovery.

**Root cause (two independent bugs, both silent):**
1. `registry_enriched.website` stores bare domains for 97.3% of rows (`hsctwarriors.org`,
   not `https://hsctwarriors.org`). `website_discovery_comprehensive.py` (used by the
   daemons) normalizes this with `https://` prepend; `BatchHTTPFetcher.fetch_batch` in the
   GPU pipeline never got the same normalization, so aiohttp raised `InvalidUrlClientError`
   on ~97% of fetches — caught by a bare `except Exception` and logged at `logger.debug`,
   invisible under the module's `INFO` root log level. Fetch success was 1-7/200 per batch.
2. Even after fixing (1), fetch success jumped to 60-70% but verified links stayed at 0.
   `QualityGate.link_context_match()` returns `matches / 3.0` where `matches` counts how
   many of ~9 keyword patterns appear in one anchor's text. The call site required
   `>= 0.7`, i.e. 3 simultaneous keyword hits in a single link's text — but a real donate
   button ("Donate Now") only ever matches one pattern, scoring 0.33. The gate was
   mathematically unpassable by any real-world anchor text.

**Preventing rules:** When a batch/pipeline script duplicates logic from an existing
working module (URL fetching, normalization, parsing), grep the working module for
edge-case handling first — do not re-derive it from scratch. Never let per-item fetch/parse
exceptions log at `debug` inside a loop meant to run for hours; log a periodic aggregate
count at `info` (e.g. "X/Y fetch failures this batch, most common: ...") so a stalled
pipeline is visible without a manual repro. Any confidence/quality-gate formula that gates
real production data must be sanity-checked against realistic sample inputs before deploy —
"0 output for a day" should trigger an immediate look at the gate math, not just the fetch
layer.

## 2026-07-16 — Link verification under network contention marked 324 live links dead

**Symptom:** Batch link verifier (8 threads) reported 35% pass rate on links that
dry-ran at 96% minutes earlier. 324 links were flipped to 'dead'; sequential re-check
showed 14/15 were alive.

**Root cause:** Two compounding effects. (1) The GPU discovery pipeline was fetching
200 sites every ~8s on the same connection — verification timeouts were local
congestion, not dead links. (2) Many donate links funnel through shared hosts
(PayPal, Zeffy, GivingFuel) that rate-limit per IP; concurrent HEADs triggered 429s,
which the verifier counted as failures.

**Preventing rules:** A verdict that writes 'dead' to the database must distinguish
definitive failures (404/410/401/403) from inconclusive ones (timeout, 429, 5xx) —
inconclusive keeps its prior status for a later retry, never gets condemned. Retry
failures sequentially before any negative verdict. When another bulk-network process
is running on the same box, verification concurrency must stay low (2 workers).
Restore path: status flips carry donate_checked_at timestamps, so a bad batch is
precisely reversible by timestamp window — this is why promotion is a status flip
and not a destructive write.

## 2026-07-17: Flask decorator order made 19 auth guards silent no-ops
**Symptom:** After adding `@require_admin_key` to all admin routes and deploying, live `/api/admin/claims` still returned 200 with PII to unauthenticated callers. Fix was "complete and committed" but the vulnerability was still live.
**Root cause (three stacked gaps):**
1. Batch script inserted `@require_admin_key` ABOVE `@app.route(...)`. Decorators apply bottom-up, so Flask registered the unwrapped function — the guard existed but never executed.
2. The fixed file was never loaded: home gunicorn kept running pre-fix code (no restart), and the droplet copy was scp'd to `/opt/daanaa/app.py` while gunicorn loads `droplet_api:app`.
3. Verification was misread: "HTTP 200 without key" was noted but attributed to caching instead of being treated as a failed fix.
**Preventing rules:**
- `@app.route` must always be the TOP decorator; auth/behavior decorators go below it. Grep-verify order after any scripted decorator insertion: `grep -A1 '@require_admin_key' | grep '@app.route'` must be empty.
- A security fix is not done until the failing request is re-run against the LIVE path and returns the expected denial (same principle as the 2026-07-05 deploy-verification lesson — restarting a service is not verifying it).
- Before shipping to a server, read the service's ExecStart to learn the real entrypoint filename; never assume.

## 2026-07-17 — setup_cron_schedules.sh wiped the entire existing crontab

**Symptom:** A new "install cron schedule" script was meant to add 4 pipeline jobs.
Its merge logic wrote the filtered old crontab to a temp file, then immediately
overwrote that same temp file with a heredoc containing only the new jobs —
silently deleting ~22 active jobs (backups, watchdogs, alerting, link deploys,
GPU night mode, email agent).

**Root cause:** `grep -v ... > "$TMP.new"` followed by `cat > "$TMP.new"` —
the second redirect truncates the first. Untested merge path; no diff shown
before `crontab` install.

**Recovery:** /var/log/syslog logs every cron execution with its exact command
line (`CRON[pid]: (user) CMD (...)`). Parsing timestamps per command recovered
all 25 jobs AND their schedules (run-count per day → interval). Full crontab
rebuilt and reinstalled same morning; no scheduled window was missed.

**Preventing rules:**
1. A crontab installer must be the single source of truth listing EVERY job
   (ours now is), or it must never use `crontab` (replace mode) — only append.
2. Always `crontab -l > backup` to a *persistent* path (repo logs/, not mktemp)
   before installing. The installer now does this.
3. After any crontab change, diff against the backup and count job lines.
4. Docs said overnight_pipeline ran "Saturdays"; syslog showed it ran daily at
   02:30. When scheduling around an existing job, verify its real schedule from
   syslog/logs, not from documentation.

## 2026-07-17 — new-org FTS insert ran before revocation marking

**Symptom:** Weekly IRS BMF delta-load inserted 13,937 new orgs into the FTS
search index; 1,101 of them were already on the IRS revocation list and entered
the index as searchable.

**Root cause:** The BMF (source of new orgs) lags the revocation list — a
newly-listed org can already be revoked. The sync inserted to FTS before
checking revocations.

**Preventing rule:** Any step that makes an org publicly visible (FTS insert,
precompute export, deploy) must run AFTER the revocation guard for the same
batch. sync_irs_data.py now marks new-org revocations before its FTS insert.
The API's serve-time filters (org_status='active') remain the fail-closed
backstop — they prevented any user exposure here.

## 2026-07-17 — deploy snapshot livelocked against continuous writers

**Symptom:** safe_deploy_droplet.sh sat in "Taking online .backup snapshot" for
34 minutes with the snapshot file stalled at 11.1GB of 15GB.

**Root cause:** SQLite's online backup restarts from page 0 whenever another
connection commits to the source DB. The 24/7 discovery daemon commits
constantly, so the backup could never finish a full pass — a livelock, not a
hang. Proof: after SIGSTOPping the writers, the snapshot completed in 39 s.

**Preventing rule:** Any full-DB .backup on the live registry must briefly
quiesce continuous writers first. SIGSTOP/SIGCONT is the right tool — pauses
in place, loses no work, and a shell EXIT trap guarantees resume even if the
deploy dies mid-snapshot. safe_deploy_droplet.sh now does this automatically
for discovery_daemon, reverify_donate_pages, and enrich_batch.

## 2026-07-17 — directory sort was a silent no-op on plain browse
- **Symptom:** founder reported "sorting is not working"; live test showed
  sort=asc and sort=desc returning byte-identical name-ordered pages.
- **Root cause:** the edge serves precompute .json.gz for bare browse; those
  files are baked in name order and the route never consulted sort/order.
  Sorting only worked with a search query or filter (DB paths). Second bug in
  the same report: the sort direction arrow lived in a hidden sm:flex container
  so mobile never rendered it, and FilterSheet had no direction control.
- **Preventing rule:** contract tests must guard behavior, not just route
  presence — test_edge_routes_explicit_sort_to_db now pins the routing
  condition at source level. When a param is accepted by both backends, verify
  the EDGE actually honors it (curl asc vs desc must differ) before calling a
  surface "shared".

## 2026-07-17 — nonprofit sign-in dead-ended via a Cloudflare redirect
- **Symptom:** /nonprofit/login 301'd to /org/login, which matched the SPA's
  /org/:id route and rendered a broken org page. Every nonprofit trying to
  sign in hit a dead end; org_claims shows 3 rows total.
- **Root cause:** a Cloudflare redirect rule pointed at a URL that was never
  created in the SPA. Redirects live in THREE layers here: Cloudflare rules,
  droplet nginx, and droplet_api _LEGACY_REDIRECTS — the audit only finds
  them by curling the live URL and reading the `server:` header.
- **Preventing rule:** when adding any redirect, curl the TARGET and confirm
  it renders real content; funnel entry URLs belong in the smoke-test list
  (added /org/login to the deploy smoke set).

## 2026-07-18 — Cloudflare edge-cached a GET before verifying the sort fix
- **Symptom:** re-tested the sort fix after the mega-deploy and got the OLD
  (broken) name-order result again — looked like a regression.
- **Root cause:** Cloudflare cached the exact GET URL from an earlier test
  (same query string). A cache-busting param (`&_cb=<ts>`) proved the fix
  was correct all along. Also found separately: the local API (daanaa_api.py,
  gunicorn --preload) had been running 1+ day and never picked up the
  page_health commit — --preload loads code once at start; restart_api.sh
  is required after any daanaa_api.py change, autonomous or not.
- **Preventing rule:** when live-verifying a fix, always append a cache-buster
  to GET requests against daanaa.org, and confirm the local API's process
  start time is AFTER the relevant commit before trusting a "still broken"
  result from it.

## 2026-07-18 — my own test script degraded live search for ~15 minutes
- **Symptom:** founder asked me to verify site health; a keyword search hit
  a 15s near-timeout. Root cause: my own background verification test (a
  full-DB-copy INSERT...SELECT with an unindexed NOT EXISTS correlated
  subquery) was still running at 98.8% CPU on one core, contending with the
  live gunicorn workers for CPU/IO on the same box.
- **Preventing rule:** before testing any query against a full DB copy,
  add `nice -n 19` (or run on a scratch box) so verification work can never
  compete with the live API for CPU. Always `ps -eo pid,pcpu,cmd
  --sort=-pcpu | head` after ANY background test to confirm nothing was
  left running, not just check its own completion status.
- **Also confirmed:** the query itself needs an index — NOT EXISTS against
  an un-indexed score_snapshots(EIN, snapshot_date) is an O(n·m) scan that
  gets worse every week as the table grows. Added
  `CREATE INDEX idx_score_snapshots_ein_date` before shipping the nightly
  snapshot-capture change.

## 2026-07-18 — main directory search (q=) was 15-21s for common words
- **Symptom:** founder asked "is search always fast" — a single, isolated,
  cache-busted request for q=health took 21s (reproduced identically direct
  on the droplet, ruling out network/CDN flakiness or my own concurrent
  testing). Droplet load average was only 0.51 — not CPU contention.
- **Root cause:** `_fts_directory()` (serves the main `/api/organizations?q=`
  path the Directory page actually calls) ran an UNCAPPED
  `COUNT(*) FROM org_fts s, registry_enriched o WHERE ... MATCH ?` — for a
  common word ("health" = 174,555 matches) this counts and joins every
  matching row against the full 1.87M-row table. The exact same bug, in the
  sibling `fused_search()` function, was already diagnosed and fixed
  2026-07-16 (see that function's comment: "16-20s per search on the
  droplet") — but the fix was never applied to this second query path,
  which is the one the main site search actually uses.
- **Preventing rule:** any COUNT(*) or join against org_fts + registry_enriched
  must use the bounded-candidate CTE pattern (bm25-rank inside FTS5, LIMIT
  cand_cap, then join/filter/count only the candidates) — never an
  unbounded join. Fixed in `_fts_directory()` to match `fused_search()`.
  Verified locally against a real copy of search.db: correctness confirmed
  (public-filter + category conditions honored), though the 2GB droplet's
  RAM-vs-1.7GB-file page-cache pressure (not raw CPU) is what makes this
  slow in production — a bigger/faster dev box won't reproduce the timing,
  only the droplet will.

## 2026-07-18 (follow-up) — bounded-candidate fix wasn't enough on its own
- **Symptom:** after capping the FTS candidate set to 20000 rows, q=health
  still took 6-8s (down from 15-21s, but not "fast").
- **Root cause:** EXPLAIN QUERY PLAN on the live droplet showed SQLite
  flipping the join order whenever an indexed o.* filter was present
  (idx_orgs_public for the public-content filter, idx_orgs_ntee1_rev for
  category filters) — it drove from the ~1.85M-row table and bloom-filtered
  each row against the small CTE, instead of scanning the small CTE and
  doing a primary-key lookup into the big table. Same latent bug existed in
  fused_search() too (triggered by ntee_list, confirmed via the same
  EXPLAIN), even though its own 2026-07-16 fix comment claimed this was
  already solved.
- **Fix:** CROSS JOIN instead of a plain JOIN. SQLite will not reorder an
  explicit CROSS JOIN, forcing the small-side-first plan. Confirmed via
  EXPLAIN QUERY PLAN + timed test on the droplet: 0.6s.
- **Preventing rule:** any bounded-candidate-CTE + big-table join in this
  file must use CROSS JOIN, never a plain JOIN — the query planner cannot
  be trusted to pick the small side just because the CTE is small; it goes
  by index availability, not row-count intuition. Guarded at source level
  in tests/test_contract_and_terminology.py.

## 2026-07-18 — deploy script's own smoke test/rollback can false-alarm on transient SSH blips
- **Symptom:** sync_droplet_api.sh reported "SMOKE TEST FAILED... Rolling
  back... ssh: connect... Connection refused... Rollback FAILED — MANUAL
  ACTION NEEDED" — sounds like a failed deploy plus a failed safety net.
  Site was actually up the whole time (0.1-1.3s responses) and the new code
  was correctly deployed (md5sum match, behavior match) — the deploy
  script's OWN health-check and rollback steps hit a transient SSH refusal
  (likely rate-limiting from the many rapid SSH connections used for
  EXPLAIN QUERY PLAN testing minutes earlier), not the application.
- **Preventing rule:** on a "SMOKE TEST FAILED" / "Rollback FAILED" message,
  do not assume the site is down — independently curl the public URL AND
  compare md5sum of local vs deployed droplet_api.py before taking any
  recovery action. SSH connection refusal is a distinct failure mode from
  an application failure and self-resolves; don't panic-rollback or
  re-deploy on top of a possibly-fine state.

## 2026-07-18 — the "30K pending links" backlog was a bookkeeping mirage
- **Symptom:** daemon progress report showed 30,429 links "queued at 90%+"
  pending deployment, while the 4-hourly deploy cron drained only ~38 per
  cycle — looked like a huge stuck backlog (and briefly like a huge win).
- **Root cause:** deploy_queued_links.py drains by `deployed_at IS NULL`
  and stamps deployed_at on deploy, but never updated the `status` column —
  30,392 rows were already deployed while still labeled status='pending'.
  The report counted status='pending'. Real undrained queue: 37 rows.
  Links were flowing discovered→queued→deployed within 4h the whole time.
- **Preventing rule:** when a queue has BOTH a status column and a
  timestamp column, every writer must keep them consistent, and reports
  must count from the column the DRAIN path actually uses. Before treating
  any "backlog" number as real, cross-check it against the drain query's
  own predicate.

## 2026-07-19 — task #15 frontend shipped calling endpoints prod never routed / never ran
- **Symptom:** After deploying #15 to the droplet, the wallet's
  report-bookmark call returned 405 (no route on droplet_api.py — fell
  through to SPA fallback), and once proxied it 500'd on every call:
  the handler's ON CONFLICT upserts targeted a table with no UNIQUE
  constraints, so SQLite rejected them. The endpoint had never worked,
  local or prod.
- **Root cause:** two-backend split (daanaa_api.py home / droplet_api.py
  prod) means a new home-server endpoint is invisible in prod until a
  proxy route is added; and the endpoint itself shipped without one
  behavior test (a single POST would have caught the 500 on day one).
- **Preventing rule:** any frontend change that introduces a fetch() to a
  new /api path must (1) grep droplet_api.py for the route/proxy before
  deploy, and (2) prove the endpoint with a real request — insert AND
  update/second-call paths — locally and through the public URL after
  ship. Route presence is not behavior.

## 2026-07-19 — a bare `except: pass` turned a one-word typo into a five-commit hunt
- **Symptom:** search_intent never appeared in /api/organizations responses
  across five debugging commits (import-order changes, preload theories,
  logging attempts) even though the classifier imported cleanly at startup.
- **Root cause:** handler called SearchIntentClassifier(db_path=str(DB)) but
  the module constant is DB_PATH → NameError on every request, swallowed by
  `except Exception: pass`. All the startup-time debugging was aimed at the
  wrong phase; the failure was per-request and invisible.
- **Preventing rule:** never pair a new integration with a silent except —
  log the exception from day one (app.logger.warning minimum). When a
  feature "silently does nothing," grep its code path for `except.*pass`
  FIRST, before theorizing about imports, caching, or process models.
