# Daanaa Infrastructure Operations Guide

Complete reliability, safety, and performance infrastructure for production operations.

## What's Included

### 1. Monitoring & Alerting (`monitoring/`)

**Real-time system & application metrics** with threshold-based alerting.

```bash
# Collect metrics (runs every minute via cron)
python3 infrastructure/monitoring/metrics_collector.py

# Process alerts (sends CRITICAL emails, daily digest at 9 AM)
python3 infrastructure/monitoring/alert_manager.py
```

**Metrics collected:**
- System: CPU, memory, disk, load average, uptime
- API: response times, error rates, health status
- Database: size, org count, FTS5 health, scoring coverage
- Pipeline: scorer age, embeddings status, v5 coverage
- Alerts: threshold violations (disk >80%, API down, scorer stale, etc.)

**Alert integration:**
- Critical alerts sent immediately (email)
- Deduplicates to prevent spam
- Daily digest at 9 AM summarizes all events

### 2. Backup & Disaster Recovery (`backup/`)

**Automated encrypted backups with point-in-time recovery.**

```bash
# Daily home server backup (2 AM)
bash infrastructure/backup/daily_backup.sh

# Droplet backup (3 AM, runs via SSH)
bash infrastructure/backup/backup_droplet.sh

# Test restore (monthly)
bash infrastructure/backup/test_restore.sh

# Cleanup old backups (weekly)
bash infrastructure/backup/cleanup_old_backups.sh
```

**Backup schedule:**
| Target | Frequency | Retention | RTO |
|--------|-----------|-----------|-----|
| merit_registry.db | Daily | 30 days | 10 min |
| search.db (droplet) | Daily | 14 days | 5 min |
| browse cache | Weekly | 8 weeks | 15 min |

**Recovery procedures** for 5 failure scenarios documented in `backup_strategy.md`:
1. Database corruption → restore from backup
2. Search index failure → restore from snapshot
3. Disk full → identify + clean large files
4. Scorer failure → manual trigger
5. Complete droplet failure → redeploy + restore

### 3. Deployment Safety (`deployment/`)

**Zero-risk deployments with automatic rollback.**

```bash
# Pre-deployment safety checks (7-point audit)
bash infrastructure/deployment/pre_deploy_checks.sh

# Safe deployment (snapshot → deploy → verify → rollback if fail)
bash infrastructure/deployment/safe_deploy.sh

# Emergency rollback (1-minute recovery)
bash infrastructure/deployment/rollback.sh /tmp/deploy_snapshot_XXX
```

**Checks before deploy:**
1. No uncommitted changes (git clean)
2. Frontend builds without errors
3. Database integrity (PRAGMA check)
4. API dependencies available
5. FTS5 index healthy
6. Recent backup exists (<26h)
7. Droplet reachable (SSH connectivity)

**Deploy process:**
1. Snapshot current state (for rollback)
2. Deploy frontend assets
3. Deploy API if changed
4. Restart services
5. Verify health (API, homepage, directory)
6. Auto-rollback if any check fails

### 4. Data Pipeline (`pipeline/`)

**Health monitoring and automatic repair for scorer, FTS, embeddings.**

```bash
# Check pipeline health (runs every 6 hours)
python3 infrastructure/pipeline/pipeline_health.py

# Auto-repair pipeline (rebuild FTS, recompute embeddings, run scorer if needed)
bash infrastructure/pipeline/repair_pipeline.sh

# Performance profiling (measures latency, cache effectiveness)
python3 infrastructure/performance/measure_performance.py
```

**Health checks:**
- Scorer: ran within last 24 hours
- FTS5: indexed count == source count
- Embeddings: have ~546K computed
- v5 scores: coverage > 90%
- Database: reasonable size, no corruption

**Auto-repair actions:**
- Rebuild FTS5 if out of sync
- Recompute stale embeddings
- Trigger scorer if stale (takes ~30 min)
- VACUUM database to reclaim space

### 5. Operations Schedule (`OPERATIONS_SCHEDULE.md`)

**Cron jobs and manual tasks.**

```bash
# Install cron jobs (copy commands from OPERATIONS_SCHEDULE.md to crontab)
crontab -e

# Weekly operations checklist (15 min)
# - Check nightly logs
# - Verify backups created
# - Review alerts
# - Check database growth
# - Verify droplet disk

# Monthly tasks (30 min)
# - Test restore
# - Database analysis
# - Performance baseline
```

---

## Quick Start

### Installation

```bash
# 1. Create directories
mkdir -p /backups/{merit_registry,search.db}
chmod 700 /backups  # Restrict access

# 2. Install cron jobs
crontab -e
# Copy relevant lines from OPERATIONS_SCHEDULE.md

# 3. Test monitoring
python3 infrastructure/monitoring/metrics_collector.py
cat /tmp/daanaa_metrics.json

# 4. Test backup
bash infrastructure/backup/test_restore.sh

# 5. Verify deployment gates
bash infrastructure/deployment/pre_deploy_checks.sh
```

### Normal Operations

**Every minute (automatic):**
- Collect metrics
- Check for alerts

**Every 6 hours (automatic):**
- Pipeline health check
- Auto-repair if issues detected

**Daily (automatic):**
- Backup home DB (2 AM)
- Backup droplet (3 AM)
- Daily digest email (9 AM)

**Weekly:**
- Run operations checklist (15 min, Monday)
- Deploy to production (whenever ready)
  - Run `pre_deploy_checks.sh`
  - Run `safe_deploy.sh`

**Monthly:**
- Test restore procedure
- Database analysis
- Performance baseline

### Responding to Alerts

| Alert | Action | SLA |
|-------|--------|-----|
| Disk >80% | Free space or expand | 4h |
| API down | Check logs, restart gunicorn | 15 min |
| Scorer stale | `bash infrastructure/pipeline/repair_pipeline.sh` | 2h |
| FTS5 out of sync | Auto-repairs, verify with health check | 1h |
| Backup missing | Check cron, run manually | 2h |

---

## Architecture Decisions

### Why Encrypted Backups?
- `merit_registry.db` contains derived data (from public IRS records)
- But configuration and precomputed artifacts shouldn't be publicly readable
- Encryption at rest (AES-256) + in transit (SCP)

### Why Automatic Rollback?
- Bad frontend deploys are easy to spot (page doesn't load)
- Automatic health checks catch 95% of failures
- Manual rollback takes 10+ minutes; automatic takes 2 minutes
- Zero-risk deploys enable frequent, confident updates

### Why Pipeline Auto-Repair?
- Scorer/FTS/embeddings are deterministic (can rebuild from source)
- Automatic detection+repair prevents cascading failures
- Data pipeline is most critical path (no data = no product)

### Why Not Real-time Dashboard?
- Grafana/Prometheus add operational overhead
- Alerts (email) are sufficient for current scale (1.8M orgs, moderate traffic)
- JSON metrics can power future dashboard when needed

---

## Monitoring Runbook

### Check Current Health

```bash
python3 infrastructure/monitoring/metrics_collector.py && \
cat /tmp/daanaa_metrics.json | jq '.'
```

**Expected output:**
```json
{
  "system": {
    "memory_percent": 45.2,
    "disk_percent": 60.1,
    "load_1min": 2.3
  },
  "api": {
    "healthy": true,
    "health_status": 200,
    "directory_latency_ms": 245.3
  },
  "database": {
    "total_orgs": 1847293,
    "coverage_percent": 98.5,
    "fts5_healthy": true
  },
  "alerts": []
}
```

### Investigate a Performance Problem

```bash
# 1. Collect baseline
python3 infrastructure/performance/measure_performance.py

# 2. Compare to previous baseline
diff -u /tmp/daanaa_performance_baseline.json.old /tmp/daanaa_performance_baseline.json

# 3. Profile slow queries
# (edit pipeline_health.py to add slow_query_log = sqlite3.set_trace())

# 4. Check resource constraints
python3 infrastructure/monitoring/metrics_collector.py | jq '.system'
```

### Recover from Data Corruption

```bash
# 1. Check health
python3 infrastructure/pipeline/pipeline_health.py

# 2. Repair
bash infrastructure/pipeline/repair_pipeline.sh

# 3. Verify
python3 infrastructure/pipeline/pipeline_health.py
```

---

## Troubleshooting

### Metrics collector crashes
```bash
tail -50 /var/log/daanaa_metrics.log  # Check logs
python3 -m py_compile infrastructure/monitoring/metrics_collector.py  # Syntax check
```

### Backup never completes
```bash
tail -50 /var/log/daanaa_backup.log
# Check if /backups has write permission
# Check if droplet reachable (SSH)
```

### Deploy health checks fail
```bash
bash infrastructure/deployment/pre_deploy_checks.sh  # See which check fails
sqlite3 data/merit_registry.db "PRAGMA integrity_check;"  # DB check
python3 scripts/build_fts_index.py --test  # FTS check
```

### Pipeline repair takes too long
```bash
# Scorer is slow (30+ min)
# Run overnight or manually:
python3 scripts/merit_scorer_v4_0.py

# Embeddings are slow (if recomputing all)
# Can run with --recent to just update new orgs:
python3 scripts/build_org_embeddings.py --recent
```

---

## Testing Infrastructure

### Pre-flight Test (before major deployment)
```bash
bash infrastructure/deployment/pre_deploy_checks.sh
```

### Monthly Backup Test
```bash
bash infrastructure/backup/test_restore.sh
```

### Performance Baseline (first time, then monthly)
```bash
python3 infrastructure/performance/measure_performance.py
# Save output, compare trends month-to-month
```

### Alert Test
```bash
# Manually create alert condition (e.g., fill disk partway)
# Verify email arrives within 5 minutes
# Verify daily digest sent at 9 AM
```

---

## Cost & Dependencies

| Component | Cost | External Dep |
|-----------|------|--------------|
| Monitoring | $0 | Email (Gmail SMTP) |
| Backup | $0 | /backups partition |
| Deployment | $0 | Droplet SSH |
| Pipeline | $0 | Local Python |

**Total:** $0 (email service not counted as it's personal account)

---

## Future Enhancements

1. **Grafana Dashboard** — visual performance trends
2. **Prometheus Integration** — industry-standard metrics
3. **PagerDuty/OpsGenie** — on-call alerting for critical events
4. **CloudFlare Analytics** — edge-based traffic monitoring
5. **Sentry** — application error tracking
6. **Database Replication** — HA for merit_registry.db

All optional; current infrastructure is production-sufficient for 1.8M orgs and moderate traffic.

---

**Last updated:** 2026-06-20  
**Next review:** 2026-07-20
