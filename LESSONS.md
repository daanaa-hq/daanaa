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
