# PHASE 1 Deployment Checklist

## Pre-Flight (Local Verification)

- [ ] Run smoke test suite: `bash scripts/smoke_test_phase1.sh`
  - API health check passes
  - Percentile contract verified (peer_percentile + confidence fields present)
  - Privacy guardrails working (donation_count < 10 suppressed)
  - Search endpoint returns v6 fields
  - Stats endpoint responsive
  - HTTP 200 on 3+ sample orgs
  - Frontend builds clean

- [ ] Database migration executed: `sqlite3 data/merit_registry.db < scripts/migrations/001_add_v6_percentile_columns.py`
  - Verify columns exist: `PRAGMA table_info(registry_enriched)` should show:
    - `merit_percentile_v6 (INTEGER)`
    - `merit_percentile_confidence_v6 (TEXT)`
    - `merit_peer_count_v6_scoreable (INTEGER)`

- [ ] Git state clean: `git status`
  - No uncommitted changes
  - Latest commit includes v6 percentile + privacy guardrails

- [ ] Browser smoke test (localhost:5000)
  - Homepage loads without errors
  - Org detail page displays peer context section
  - Percentile badge shows confidence level (HIGH/MEDIUM/LOW)
  - Confidence badge color matches design system
  - Search results show v6 tiers
  - No console errors (F12)

## Staging Deployment

- [ ] Build frontend: `npm run build --prefix frontend`
  - 0 TypeScript errors
  - Build completes in < 10s
  - `frontend/dist/` updated

- [ ] Sync to droplet: `bash scripts/ops/sync_droplet_api.sh`
  - No `rsync` errors
  - Deployment artifacts uploaded
  - Rollback `.prev` state preserved

- [ ] Verify droplet health: `curl https://daanaa.org/health`
  - Returns `{"status":"ok"}`
  - No 502/503 errors

- [ ] Test on droplet (production-like environment)
  - Homepage loads (daanaa.org)
  - Org detail page renders peer context
  - Search works end-to-end
  - Percentile values visible
  - No 500s in droplet API logs

## Production Readiness Gates

- [ ] Founder approval: V6 percentile methodology sign-off
  - Percentile calculation reviewed
  - Confidence tiers (HIGH/MEDIUM/LOW) approved
  - Publication to donors authorized

- [ ] Stewardship audit: All 11 principles + Charter v1.0 aligned
  - Privacy guardrails verified
  - Small org fairness confirmed
  - No false confidence (LOW tier when < 5 peers)

- [ ] Data quality: Percentile coverage >= 94%
  - Run: `sqlite3 data/merit_registry.db "SELECT COUNT(*) FROM registry_enriched WHERE merit_percentile_v6 IS NOT NULL" | awk '{print $1 / 2053000 * 100}'`
  - Expected: ~94%

- [ ] Legal/Compliance: No new risk vectors
  - Percentile is informational (not a ranking)
  - No scoring/tier changes to public methodology
  - Tax-deductibility unchanged

## Go/No-Go Decision

**Criteria for production push:**
1. All pre-flight checks pass ✅
2. Staging deployment stable ✅
3. Founder methodology sign-off received ✅
4. Zero blocking accessibility issues ✅

**If any check fails:**
- Rollback: `bash scripts/ops/sync_droplet_api.sh --rollback`
- Revert commit: `git revert HEAD`
- Investigate root cause, update DECISIONS.md, retry

## Rollback Procedure

**Automated:**
```bash
bash scripts/ops/sync_droplet_api.sh --rollback
```
- Restores `.prev` state
- Restarts gunicorn
- Verifies health (curl /health returns 200)

**Manual:**
```bash
ssh root@167.170.26.8
cd /srv/daanaa
# Restore previous code
cp -r daanaa.org.prev/* daanaa.org/
# Restart
systemctl restart daanaa-api
# Verify
curl localhost:5000/health
```

**Database rollback note:**
- Migration is idempotent (adds columns only if not exists)
- If rollback needed, columns can remain (backward-compatible)
- No data loss; v6 fields simply unpopulated on older code

## Post-Deployment

- [ ] Monitor error logs for 24h
  - Check droplet syslog: `ssh root@167.170.26.8 tail -f /var/log/syslog | grep gunicorn`
  - Alert on 500 errors (threshold: > 3 per hour)

- [ ] Verify API response contract
  - peer_percentile values in range [0, 100]
  - confidence values in set [HIGH, MEDIUM, LOW]
  - No null percentiles where confidence = HIGH (< 5 peer rule)

- [ ] Analytics check (24h+)
  - Plausible shows traffic to org pages up (not down)
  - No unusual spike in error pages
  - Mobile views working

- [ ] Founder spot check
  - Walk through 3 orgs (small, mid, large)
  - Verify percentile display accuracy
  - Check mobile rendering

---

**Prepared by:** Claude Code  
**Date:** 2026-08-13  
**Next Review:** 24h post-deployment  
**Rollback Window:** 72h (after which rollback becomes data-recovery work)
