# Task #5 Deployment Countdown
**Date:** August 13, 2026  
**Deployment Window:** 2:30am - 4:00am (Overnight Pipeline + Index Migration)  
**Current Time:** ~21:00 (9pm)  
**Hours Until Deployment:** ~5.5 hours

---

## Timeline

| Time | Event | Owner | Status |
|------|-------|-------|--------|
| 21:00 (9pm) | Codex starts P1 fixes (directory, colors, API contract) | Codex | 🔄 IN PROGRESS |
| 23:00 (11pm) | Codex completes fixes / Claude Code verifies + merges | Codex + Claude | ⏳ PENDING |
| 00:30 (12:30am) | Final QC pass on live site | Claude | ⏳ PENDING |
| 02:30 (2:30am) | Overnight pipeline completes (scores 2M orgs, precomputes data) | Droplet (automated) | ⏳ PENDING |
| 02:45 (2:45am) | Monitor pipeline completion log | Claude | ⏳ PENDING |
| 03:00 (3:00am) | Run deployment automation script on droplet | Claude | ⏳ PENDING |
| 03:15 (3:15am) | Deploy indexes, smoke tests pass | Droplet | ⏳ PENDING |
| 03:30 (3:30am) | Capture post-deployment benchmarks | Claude | ⏳ PENDING |
| 04:00 (4:00am) | Document results (5-10% improvement expected) | Claude | ⏳ PENDING |

---

## Pre-Deployment Checklist (For Claude Code)

**Before 2:30am pipeline trigger:**
- [ ] Codex fixes verified and merged to master
- [ ] Live site re-tested (colors, directory speed, API contract)
- [ ] Baseline benchmarks captured (already done: 1ms avg per query)
- [ ] Deployment script tested locally (run through logic without executing)
- [ ] Droplet SSH access verified (`ssh root@167.170.26.8`)
- [ ] Database backups exist (`scripts/ops/daanaa_backup.sh`)

**After pipeline completes (2:45am):**
- [ ] Check `logs/overnight_pipeline.log` for "completed" status
- [ ] Verify precomputed data exists: `/data/precompute/v1/search.db`
- [ ] Health endpoint responds from droplet
- [ ] Smoke tests pass (health, search, orgs endpoints)

**During deployment (3:00-3:15am):**
- [ ] Run `deploy_task5_if_overnight_passes.sh`
- [ ] Indexes created: idx_state_organization_name, idx_merit_score_organization_name, idx_ntee1
- [ ] All 3 indexes appear in `PRAGMA index_list(registry_enriched)`
- [ ] Droplet endpoints still return 200 after indexes

**Post-deployment (3:30am):**
- [ ] Capture post-deployment benchmarks (10 iterations, same queries)
- [ ] Calculate improvement: (baseline - post_deploy) / baseline * 100
- [ ] Expected: 5-10% faster on indexed queries

---

## Codex Deliverables Expected (Before 23:00)

**From P1 fixes (3 issues):**
1. Directory page: Identify + fix 5 failed requests and 6 console errors
   - Load time should drop from 5923ms to <2000ms
   - Evidence: Screenshot of DevTools Network, load time graph

2. Color contrast: Update CSS tokens to WCAG AA
   - Axe scan results showing contrast violations resolved
   - Evidence: Before/after Axe reports

3. API contract: Update frontend to use EIN/organization_name
   - No more data access errors
   - Tests aligned with live API response shape
   - Evidence: Code changes committed

**Commit messages expected:**
```
fix: Directory page slowness - fix 5 failed requests in FTS search
fix: WCAG accessibility - update color tokens to meet AA contrast ratio
fix: API contract alignment - use EIN/organization_name in frontend
```

---

## Backup Plans (If Issues Arise)

**If Codex fixes don't complete by 11pm:**
- Deploy Task #5 anyway (it's independent of UX fixes)
- Schedule follow-up UX fixes for day after deployment
- Document as "Known issues, fixing day after"

**If overnight pipeline fails (unlikely but plan for it):**
- Check `/var/log/syslog` on droplet for errors
- Manually run `scripts/core/overnight_pipeline.py` on droplet
- If that fails, defer Task #5 to next night, proceed with hotfixes

**If deployment script fails:**
- Manual fallback: SSH to droplet, run `python3 scripts/migrations/run_migration_003.py`
- Verify indexes with `sqlite3 /data/precompute/v1/search.db "PRAGMA index_list(registry_enriched)"`
- Restore from backup if needed

---

## Success Criteria

✅ **Task #5 is "done" when:**
1. Three indexes created in droplet database
2. All smoke tests pass on droplet
3. Post-deployment benchmarks show 5-10% improvement
4. Results documented in DECISIONS.md

✅ **Night is "successful" when:**
1. P1 fixes merged and verified on live site
2. Task #5 deployed and verified on droplet
3. Both changes logged and documented

---

## Communication Plan

**Updates to user:**
- 11pm: Codex fixes status (merged? any blockers?)
- 2:45am: Pipeline completion confirmed
- 3:15am: Deployment successful + benchmarks captured
- 4:00am: Final summary (improvements measured)

**If something breaks:**
- Immediately notify via message
- Document root cause
- Plan rollback or fix

---

**Prepared by:** Claude Code  
**Last Updated:** 2026-08-13 21:00 UTC  
**Next Action:** Wait for Codex + Monitor overnight pipeline at 2:30am
