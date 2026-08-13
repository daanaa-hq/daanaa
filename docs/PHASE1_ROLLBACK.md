# PHASE 1 Rollback Plan

## Critical Issues Requiring Rollback

Rollback is triggered if any of these occur within 24h of deployment:

1. **Percentile calculation errors** (> 5% mismatch from spot-check)
2. **API 500 errors** (> 3 per hour)
3. **Search endpoint broken** (returns empty results)
4. **Database migration failure** (cannot run scorer)
5. **Frontend rendering issues** (org pages white-screen)
6. **Accessibility regression** (WCAG AA failures in new UI)
7. **Donor privacy violation** (counts < 10 exposed)

## Automatic Rollback (Recommended)

The safest path. Uses the `.prev` state which is automatically backed up before each deploy.

```bash
# On local machine
bash scripts/ops/sync_droplet_api.sh --rollback

# Or SSH to droplet and run manually:
ssh root@167.170.26.8
cd /srv/daanaa
ls -la daanaa.org.prev/     # Verify backup exists
cp -r daanaa.org.prev/* daanaa.org/
systemctl restart daanaa-api
sleep 2
curl http://localhost:5000/health
```

**Expected output:**
```
gunicorn: starting workers
{"status":"ok"}
```

**Time to restore:** < 30 seconds

## Manual Git Rollback

If automated rollback fails or `.prev` is corrupt:

```bash
# On local machine
git revert HEAD --no-edit
git push origin master

# SSH to droplet
ssh root@167.170.26.8
cd /srv/daanaa/daanaa.org
git fetch origin
git reset --hard origin/master
systemctl restart daanaa-api
curl http://localhost:5000/health
```

**Expected:** Homepage loads, org pages render, no 500s

## Database Rollback

The migration (adding 3 columns) is idempotent. **No data deletion required.**

If the percentile columns cause issues:

### Option 1: Keep columns (safest)
- Old code ignores new columns
- Migration doesn't need to run again
- No data loss
- **Recommended for rollback < 72h**

### Option 2: Remove columns (if contaminated)
```sql
-- Connect to droplet database
sqlite3 /srv/daanaa/data/merit_registry.db

-- Drop the new columns
ALTER TABLE registry_enriched DROP COLUMN merit_percentile_v6;
ALTER TABLE registry_enriched DROP COLUMN merit_percentile_confidence_v6;
ALTER TABLE registry_enriched DROP COLUMN merit_peer_count_v6_scoreable;

-- Verify
PRAGMA table_info(registry_enriched);

-- Exit
.exit
```

**WARNING:** This is destructive. Only run if:
- Percentile values are corrupted (all NULLs, all 0s, etc.)
- Manual inspection shows data integrity issues
- Founder approves data removal

**After column removal:**
- Restart API: `systemctl restart daanaa-api`
- Re-run smoke test to verify

## Partial Rollback (Feature Flag)

If only the percentile display is problematic (not the calculation):

```bash
# On droplet, set env var
export HIDE_PERCENTILE=1

# Restart gunicorn
systemctl restart daanaa-api

# This will suppress percentile in API responses without reverting the commit
```

**Code path:** `daanaa_api.py` line ~2489, wrap response section:
```python
if not os.getenv('HIDE_PERCENTILE'):
  response['peer_percentile'] = org.peer_percentile
```

**Restore:**
```bash
unset HIDE_PERCENTILE
systemctl restart daanaa-api
```

## Verification Checklist

After any rollback, verify:

- [ ] API health: `curl daanaa.org/health`
- [ ] Org detail: `curl daanaa.org/api/organizations/010239880`
- [ ] Search: `curl daanaa.org/api/search?q=tutoring&limit=5`
- [ ] Frontend: Load https://daanaa.org, check console (F12) for errors
- [ ] Mobile: Verify org pages on iPhone SE simulator
- [ ] Error logs: `tail -20 /var/log/syslog` (no gunicorn ERROR)
- [ ] Database: `sqlite3 /srv/daanaa/data/merit_registry.db "SELECT COUNT(*) FROM registry_enriched LIMIT 1"`

## Communication Plan

If rollback is needed:

1. **Founder notification** (within 15 min):
   - "Rolled back Phase 1 due to [reason]. Working on fix."
   - Include diagnostic output

2. **Fix assessment** (within 1h):
   - Root cause analysis
   - Fix approach (new commit vs. feature flag)
   - Revised deployment plan

3. **Retry deployment** (24h+ after rollback):
   - Deploy to staging first
   - Extended smoke test (2h monitoring)
   - Founder re-approval before production

## Post-Rollback Documentation

Update `LESSONS.md`:
```markdown
### Rollback: Phase 1 Percentile (2026-08-13)

**Trigger:** [Reason]
**Duration:** [Time to detect] → [Time to rollback]
**Impact:** [Orgs affected, users impacted]
**Root cause:** [Technical reason]
**Fix:** [What changed in retry]
**Prevention:** [Rule to add to CLAUDE.md or automation]
```

---

**Last Tested:** 2026-08-13  
**Rollback Window:** 72 hours post-deployment  
**Owner:** Daanaa Deployment Team  
**Escalation:** Founder (any unplanned rollback)
