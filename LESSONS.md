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
