# Security Notes

## 2026-06-09 — Leaked TiDB credential (ACTION REQUIRED: rotate)

A TiDB/Aliyun `DATABASE_URL` credential was hardcoded in `scripts/daily_sync.sh` and
`scripts/batch_import.py`, committed since the initial commit (in git history).

**Done:**
- Scrubbed from working tree (both files now read from a gitignored `.env`).
- Disabled the dead `daily_sync` cron line (legacy TiDB pipeline; no live serving code
  uses TiDB — `daanaa_api`/`merit_api`/`droplet_api` are all SQLite). The pipeline was
  also already broken (shell preamble made batch_import.py un-runnable).

**Still required (owner action — cannot be done from code):**
- [ ] ROTATE the TiDB credential in the Aliyun/TiDB console. It remains valid and is
      exposed in git history. Rotation is the only real remediation.
- [ ] After rotation, if the TiDB pipeline is truly unused, delete
      `daily_sync.sh` / `batch_import.py` / `enrich_v2.py` / `logo_fetcher.py` outright.

## Deploy safety (2026-06-09)
- Droplet deploys go through `scripts/safe_deploy_droplet.sh` only (snapshot + integrity
  gate + link-integrity gate + disk guard + atomic swap). `sync_db_to_droplet.sh` is RETIRED.
