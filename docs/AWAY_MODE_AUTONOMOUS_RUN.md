# Away Mode: Autonomous Aug 1-7 Quality Gate

**Owner:** Akbar Khowaja  
**Away:** Aug 1-7, 2026 (returns Tuesday Aug 6)  
**Mode:** Autonomous monitoring + backup automation  
**Status:** All systems running without human intervention

---

## What's Running While You're Away

### 1. Hourly Backups (Every Hour)
**Cron:** `5 * * * * /home/akbar/meritgiving/scripts/backup_strategy.sh`
- Creates hourly snapshots (24h rolling retention)
- Logs to: `/home/akbar/meritgiving/logs/backup_cron.log`
- Auto-rotates old backups to archive

### 2. Daily Backups (2 AM UTC / 9 PM CDT)
**Cron:** `0 2 * * * /home/akbar/meritgiving/scripts/backup_strategy.sh`
- Creates daily full backup (30-day retention)
- Logs to: `/home/akbar/meritgiving/logs/backup_cron.log`

### 3. Daily Monitoring Checks (Every Hour at :06)
**Cron:** `6 * * * * /home/akbar/.claude/skills/phase1-monitor/bin/run-daily.sh`
- IRS sync verification
- Signal accuracy sampling (10 random orgs)
- Performance latency checks (org pages + search)
- Engagement metrics (Plausible placeholder)
- Logs to: `/home/akbar/meritgiving/logs/phase1_monitor.log`
- Reports to: `~/.daanaa/phase1-monitoring/*.json`

### 4. Weekly Report (Friday 8 PM UTC / 3 PM CDT)
**Cron:** `0 20 * * 5 /home/akbar/.claude/skills/phase1-monitor/bin/run-weekly.sh`
- Aggregates 7 days of daily checks
- Generates founder report with gate recommendation
- Report: `~/.daanaa/phase1-monitoring/2026-08-07-weekly.md`

---

## Status Checks (You Can Review on Return)

### Check 1: Backup Health
```bash
ls -lh ~/meritgiving/backups/production/ | tail -10
```
**Expected:** 7 hourly + 1 daily backup, all ~24GB each

### Check 2: Monitoring Logs
```bash
tail -50 ~/meritgiving/logs/phase1_monitor.log
```
**Expected:** 7 days of daily checks, no critical errors

### Check 3: Weekly Report (Ready Tuesday morning)
```bash
cat ~/.daanaa/phase1-monitoring/2026-08-07-weekly.md
```
**Expected:** PASS/FAIL/CONDITIONAL recommendation + metrics

### Check 4: API Health
```bash
curl http://localhost:5000/health
```
**Expected:** `{"db_exists": true, "status": "ok"}`

### Check 5: Org Page Sample
```bash
curl http://localhost:5000/api/organizations/264837170 | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"Status: {d.get('organization_name', 'ERROR')[:50]}...\")"
```
**Expected:** Org name loads, no 500 errors

---

## If Something Goes Wrong

**Red Flag 1: Backup cron failed (no new backups for 2+ hours)**
- Check: `tail -20 ~/meritgiving/logs/backup_cron.log`
- Action: Manually run: `/home/akbar/meritgiving/scripts/backup_strategy.sh`
- Recovery: `scripts/backup_strategy.sh list` then restore if needed

**Red Flag 2: Monitoring cron failed (no new reports for 24h)**
- Check: `tail -20 ~/meritgiving/logs/phase1_monitor.log`
- Action: Manually run: `/home/akbar/.claude/skills/phase1-monitor/bin/run-daily.sh`

**Red Flag 3: API not responding (curl returns connection refused)**
- Action: Check if server crashed: `ps aux | grep daanaa_api`
- Restart: `cd ~/meritgiving && nohup python3 daanaa_api.py > /tmp/daanaa_api.log 2>&1 &`
- Restore DB if needed: `scripts/backup_strategy.sh restore [backup_file]`

**Red Flag 4: Database corrupted (org pages return 500 errors)**
- Action: Restore from most recent hourly backup
- Command: `scripts/backup_strategy.sh restore ~/meritgiving/backups/production/merit_registry_hourly_*.db` (pick most recent)

---

## What You'll Review on Tuesday

### 1. Phase 1 Quality Gate Report
**File:** `~/.daanaa/phase1-monitoring/2026-08-07-weekly.md`

Contains:
- Signal accuracy metrics (7-day avg)
- IRS sync health (max lag observed)
- Performance baseline (org page latency, search latency)
- User engagement (Plausible stats)
- **Decision recommendation:** ✅ PASS / ⚠️ CONDITIONAL / ❌ FAIL

### 2. Backup Audit Trail
**Run:** `ls -lht ~/meritgiving/backups/production/` 

7 hourly + 1 daily = 8 backups if everything ran smoothly.

### 3. Monitoring Log Summary
**Run:** `grep -c "✅\|⚠️" ~/meritgiving/logs/phase1_monitor.log`

7 "✅" = all checks passed daily  
Any "⚠️" or "🔴" = investigate

### 4. Decision Readiness
If gate report says **PASS:**
- Proceed to Phase 2 internal review (Aug 8-14)
- Build wallet backend + frontend
- Prepare for Phase 2 founder review

If gate report says **CONDITIONAL:**
- Minor issues detected
- Request revisions or additional checks
- Delay Phase 2 by 2-3 days

If gate report says **FAIL:**
- Critical issue found
- Debug root cause
- Extend monitoring window
- Delay Phase 2

---

## Timeline (Aug 1-7)

| Day | Time (CDT) | Event | Logs |
|-----|-----------|-------|------|
| Thu Aug 1 | 00:00 | Quality gate monitoring starts | phase1_monitor.log |
| Thu-Fri | Hourly | Daily checks run (:06 past hour) | phase1_monitor.log |
| Fri Aug 2 | 2:00 AM | Daily backup #1 | backup_cron.log |
| Fri Aug 2 | 3:00 PM | Integrity check | integrity_check.log |
| Fri Aug 2 | 3:00 PM | Weekly report generated | phase1_monitor/weekly.md |
| Sat-Sun | Hourly | Continued monitoring | phase1_monitor.log |
| Mon Aug 5 | 2:00 AM | Daily backup #2 | backup_cron.log |
| Tue Aug 6 | 9:00 AM | YOU RETURN | Ready for review |

---

## Emergency Contact (If Something Breaks)

If critical issue on local server while you're away:
1. Check `/home/akbar/meritgiving/logs/phase1_monitor.log` for alerts
2. Review `/home/akbar/meritgiving/logs/backup_cron.log` for backup status
3. Can restore from backup anytime with: `scripts/backup_strategy.sh list`

**Production (daanaa.org) is FROZEN** until Tuesday approval.
Local server is self-healing via automated backups.

---

## Post-Return Checklist (Tuesday Aug 6)

- [ ] Read Phase 1 weekly report
- [ ] Check if gate passed/failed
- [ ] Review backup audit trail
- [ ] Verify monitoring logs (no critical alerts)
- [ ] Decide on Phase 2 approval + timeline
- [ ] Prepare for Aug 8-14 internal review

---

**All systems nominal. Ready for autonomous run.**

*Last updated: Aug 1, 2026 00:00 UTC*  
*Next update: Tuesday Aug 6, 2026 (on your return)*
