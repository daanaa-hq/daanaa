# Gate 0: Operational Stability Monitoring

**Status:** Active Aug 11 - Aug 17, 2026  
**Monitoring window:** 7 days continuous  
**Progress:** Day 1/7 ✅

## Pass Criteria

All of the following must be true for Gate 0 to PASS:

1. **Uptime:** >99% (max 14 minutes downtime in 7 days)
2. **Import errors:** 0 per day (check logs for "ImportError")
3. **Watchdog false positives:** 0 (restarts only on real issues)
4. **Search latency:** p95 <300ms (baseline 212ms)
5. **API errors:** <0.1% (health endpoint 200 OK)

## Daily Checklist (Automated via daemon_health_lib)

### Morning (06:00 UTC)
- [ ] Check daemon health logs
- [ ] Verify discovery_daemon.py is running
- [ ] Check for any overnight errors

### Midday (12:00 UTC)
- [ ] Sample 10 searches, measure p95 latency
- [ ] Verify API endpoints responding
- [ ] Check watchdog restart history

### Evening (18:00 UTC)
- [ ] Review 24-hour uptime
- [ ] Check error rate dashboard
- [ ] Escalate if any anomalies

### Before bed (22:00 UTC)
- [ ] Final health check
- [ ] Review daily summary

## Alert Triggers (Escalate Immediately)

- Uptime <99.5% in any 24-hour window
- Any ImportError in logs
- Search latency p95 >400ms
- Watchdog restart loop (>2 restarts in 1 hour)
- API error rate >1%

## Escalation Procedure

If any alert triggered:
1. Check `/tmp/daemon_health.json` for root cause
2. Review recent commits/changes
3. Attempt local reproduction
4. Roll back if needed
5. Post incident to LESSONS.md

## Success Definition

At end of Aug 17:
- Zero critical incidents
- Platform healthy and stable
- Confidence high for Gates 1-8

