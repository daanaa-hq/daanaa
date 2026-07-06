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

## Deployment Blocker (Resolved Below)

**Issue:** Database size mismatch  
**Local:** `merit_registry.db` = 12GB (full registry with 3,680 new donation links)  
**Droplet:** Only 1.7GB free disk space after cleanup  
**Impact:** Direct rsync impossible

**Root Cause:** Droplet stores pre-computed artifacts + old database. Upgrading from 2GB old DB to 12GB new DB requires infrastructure upgrade.  

---

## Solution Options (Evaluated)

### Option A: Incremental Sync ✅ BEST
Update existing droplet DB with donation links via SQL:
```bash
# Extract donation links from local DB
sqlite3 data/merit_registry.db "SELECT EIN, donate_url, donate_platform, donate_confidence, donate_status FROM registry_enriched WHERE donate_url IS NOT NULL;" > /tmp/donate_links.csv

# On droplet: UPDATE registry_enriched with new links
```
- **Payload:** ~500KB (just the 3,680 links)
- **Downtime:** <1 min
- **Risk:** Minimal (UPDATE-only, rollback simple)
- **Time:** 2 hours

### Option B: S3 Staging (User Suggestion) ✨ SCALABLE
Upload to S3, download on droplet:
```bash
# Local: upload to S3
aws s3 cp data/merit_registry.db s3://meritgiving/staging/

# On droplet: download and swap
aws s3 cp s3://meritgiving/staging/merit_registry.db /opt/daanaa/data/merit_registry.db.new
# Verify, then swap
```
- **Payload:** Streamed via S3 (handles large files)
- **Downtime:** 2-3 min
- **Risk:** Low (keep backup, rollback ready)
- **Time:** 1.5 hours
- **Bonus:** Scales for future 20GB+ DBs

### Option C: Droplet Storage Upgrade
Upgrade droplet from 33GB to 50GB+ via DO:
- **Cost:** ~$12/month more
- **Downtime:** ~5 min
- **Time:** 30 min + billing
- **Future-proof:** Handles DB growth

### Option D: Wait for Maintenance Window
- Keep old DB, deploy donation links next refresh
- **Risk:** None
- **Time:** Unknown (could be weeks)

---

## Recommendation

**Option A (Incremental Sync)** — ship donation links in 2 hours, no cost, minimal risk

**Then plan Option B (S3)** for future DB upgrades (scalable architecture)

---

## Next Steps

### Immediate (2 hours)
1. Execute **Option A: Incremental Sync**
   - Extract 3,680 donation links to CSV
   - SSH to droplet, UPDATE registry_enriched table
   - Test API returns donate fields
   - Verify "Give directly" button live

### Short-term (Next sprint)
2. Document and implement **Option B: S3 Staging**
   - Set up S3 bucket for DB staging
   - Create deployment script using S3
   - Test with next larger DB
   - Update deployment runbooks

### Medium-term (If needed)
3. If DB growth exceeds 20GB, upgrade droplet storage (Option C)

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

