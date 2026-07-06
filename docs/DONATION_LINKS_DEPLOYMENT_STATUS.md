# Donation Links Deployment Status

**Date:** 2026-07-06  
**Status:** ✅ **Code Ready, Deployment Blocked by Infrastructure**

---

## What's Ready to Ship

### ✅ Backend (100% Complete)
- `daanaa_api.py`: Donate fields added to API response (line 653, 3462, 3493)
- Database: 3,680+ verified donation links extracted and stored
- Routes: `/api/org/{ein}` returns `donate_url`, `donate_platform`, `donate_confidence`, `donate_status`

### ✅ Frontend (100% Complete)
- `OrganizationDetail.tsx`: Donate button component (lines 1561-1579)
- UI: "Give directly" button shown when `donate_url` is present and `status='ai_suggested'`
- Behavior: Opens donation link in new tab with proper security headers
- Frontend built and deployed to droplet ✅

### ✅ Data (100% Complete)
- Extraction: 3,680 verified donation links from 25+ platforms
- Quality: Confidence scores (80-90% = AI-suggested; 95%+ = high confidence)
- Database: Links stored in `registry_enriched.donate_url`, `donate_platform`, `donate_confidence`, `donate_status`

---

## Deployment Blocker

**Issue:** Droplet `/opt/daanaa/data/` disk full (28 error)  
**Size:** `merit_registry.db` = ~2.4GB (with 3,680 new links)  
**Impact:** Cannot sync new database to droplet

**Root Cause:** Droplet disk space is constrained; previous cleanups didn't fully free space  

---

## Solution Options

### Option A: Incremental Sync (Recommended)
Instead of full DB sync, sync only the donation links:
```sql
-- On local
sqlite3 data/merit_registry.db "SELECT EIN, donate_url, donate_platform, donate_confidence FROM registry_enriched WHERE donate_url IS NOT NULL;" > /tmp/donate_links.csv

-- On droplet (run script to UPDATE existing rows)
```
- Pros: Small payload (~500KB), no full DB replacement
- Cons: Requires custom update script
- Time: 1 hour

### Option B: Clean Droplet & Rebuild
1. Stop API
2. Backup current DB
3. Clean temp files / old artifacts
4. Sync new merged database
5. Restart API
- Pros: Fresh state, reliable
- Cons: Requires ~30 min downtime
- Time: 2-3 hours with verification

### Option C: Keep as-is Until Scheduled Maintenance
- Deploy donation links at next scheduled DB refresh (when droplet gets decommissioned/rebuilt)
- Pros: No risk, minimal effort
- Cons: Feature waits for infrastructure maintenance
- Time: TBD (next maintenance window)

---

## Recommendation

**Option A (Incremental Sync)** because:
- Smallest change, lowest risk
- No downtime
- Can ship donation links today/tomorrow
- Aligns with "results need to be reliable"

---

## Next Steps

1. **Choose option A/B/C above**
2. If A: Create `sync_donate_links.sh` script (1 hour)
3. If B: Schedule droplet maintenance window
4. If C: Document for next refresh cycle

---

## Testing Plan (When Live)

Once donation links are live:
1. Browse to https://daanaa.org/directory
2. Click 5 random orgs → Verify "Give directly" button appears
3. Click button → Verify link opens in new tab to correct processor (PayPal, GiveButtery, etc.)
4. Check API response: `curl https://daanaa.org/api/org/{EIN}` → Verify `donate_url` present
5. Monitor error logs for 24h → Verify no crashes or 404s

---

## Rollback Plan (If Needed)

If donation links cause issues:
1. Stop API: `ssh root@162.243.97.179 systemctl stop daanaa`
2. Restore backup (if made)
3. Restart: `systemctl start daanaa`
4. Downtime: <5 min

---

## Related Infrastructure Issues

- Droplet disk space needs cleanup (documented in backup_architecture.md)
- Consider: Archive old score snapshots, clean temp files
- Long-term: Upgrade droplet storage or migrate to S3-backed DB

