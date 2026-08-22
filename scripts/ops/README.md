# Ops — Operations & Deployment

## Canonical Files

- **`sync_droplet_api.sh`** — Deploy backend to droplet (auto-syncs when droplet_api.py changes, smoke tests, auto-rollbacks)
- **`safe_deploy_droplet.sh`** — Full deployment with code + frontend (safer than piecemeal, includes schema validation)
- **`daemon_health_lib.py`** — Standard health check library (all watchers use this, not log parsing)
- **`daanaa_backup.sh`** — Backup orchestrator (copies to S3, tracks checksums, hardened 2026-07-12)

## Monitoring & Watchdogs

`api_watchdog.sh` restarts `daanaa-api` if unhealthy, and
`daemon_health_lib.py` is the canonical library for daemon health checks. For a
manual public-site check, use `health_check.sh`.

## Database Operations

There is no `scripts/ops/database/` directory. Review `scripts/migrations/`
for the applicable migration script; do not apply database changes without the
required approval and backup verification.

## Backup

```bash
./scripts/ops/daanaa_backup.sh                      # Runs nightly, uploads to S3
# Backup location: s3://daanaa-nonprofit-data/backups/
# Restore: contact Akbar (manual process, not automated)
```

## How To...

**Deploy new API code to droplet:**
```bash
./scripts/ops/sync_droplet_api.sh
# What it does:
# 1. Checks local droplet_api.py is correct (no home-only schema)
# 2. Backs up old version to S3
# 3. Syncs to droplet via rsync (preserves .prev file)
# 4. Restarts daanaa-api systemd service
# 5. Smoke tests: homepage + /api/search must return 200
# 6. Auto-rollback if smoke test fails
```

**Deploy frontend only:**
```bash
./scripts/ops/safe_deploy_droplet.sh --frontend-only
# Rebuilds frontend/dist/, syncs to droplet, restarts nginx
```

**Deploy both API + frontend:**
```bash
./scripts/ops/safe_deploy_droplet.sh --code-only
# Syncs both droplet_api.py + frontend dist
```

**Check if droplet is healthy:**
```bash
./scripts/ops/health_check.sh
# Checks the public homepage, directory, volunteer page, and /health endpoint.
```

**Restart monitoring daemon:**
```bash
systemctl restart api_watchdog    # Or specific watchdog
systemctl status api_watchdog      # Check status
tail -f logs/api_watchdog.log      # Follow logs
```

## Systemd Services

Canonical location: `/etc/systemd/system/daanaa-api.service`
Repo mirror: `institution/systemd/daanaa-api.service`

Key points:
- ExecStartPre: Forceful cleanup (pkill -TERM, then -KILL) to prevent port conflicts
- ExecStopPost: Guaranteed cleanup after stop
- Restart: always (will retry indefinitely with exponential backoff)
- TimeoutStopSec: 45s (gives graceful shutdown time)

**Reload after editing:**
```bash
systemctl daemon-reload && systemctl restart daanaa-api
```

## Do Not Use

- Manual SSH restarts (use systemctl)
- Log parsing for health checks (use `daemon_health_lib.py`)
- Direct database restores without backup verification
- `rm -rf` on live directories (use `.prev` rollback instead)

## Lessons Learned (Recent)

| Date | Incident | Fix |
|------|----------|-----|
| 2026-08-12 | Wrong precompute path | Added sharded `orgs/<ein[:3]>/<ein>.json.gz` validation |
| 2026-08-10 | Droplet DNS failed | Updated all 19 scripts to use 107.170.26.8 |
| 2026-08-08 | Gunicorn crash loop | Added ExecStartPre/ExecStopPost forceful cleanup |
| 2026-07-13 | Smoke test incomplete | Made smoke test unconditional (checks if service "active" is not enough) |
| 2026-07-05 | SPA fallback outage | Never ship local daanaa_api.py to droplet (only droplet_api.py) |

## See Also

- `docs/operations/deployment/DEPLOYMENT.md` — Deployment procedures
- `LESSONS.md` — Historical incidents + preventing rules
- `institution/systemd/` — Service file templates
