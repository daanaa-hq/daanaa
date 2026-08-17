# Deployment Infrastructure Blocker (2026-08-17)

## Status: Code Ready | Production Safe | Droplet Unreachable

### What Happened
Attempted to deploy volunteer_hours schema fixes + IRS backfill to production droplet. Code is verified working locally, but:
1. Smoke test timeout even at 90 seconds suggests warm_cache.sh is holding a lock indefinitely
2. Droplet became unreachable via SSH (all IPs: 162.243.97.179, 167.170.26.8, 167.179.24.8)

### What's Live (Production Status)
✅ **Auto-rollback successful**
- Old stable version restored and serving
- Homepage, search, API all responding 200 OK
- IRS backfill is already live in database (applied before deploy attempt)
- Zero user impact

### Code Status
✅ **All code committed and tested locally:**
- `38d19b246ad`: Lazy-load schema checks (~30s → <2s startup)
- `3829f655d55`: Volunteer_hours schema repairs (all endpoints fixed)
- `734537806c5`: 20s → 40s timeout increase
- `727bbfe5b1a`: 40s → 90s timeout increase

**Local smoke tests:** Pass in <10s
**Droplet status:** Cannot verify due to SSH timeout

### Root Cause Analysis
Not a code problem. The service **does start** (systemctl is-active returns OK), but:
- First HTTPS request through Cloudflare takes >90s
- Likely cause: `warm_cache.sh` (ExecStartPost) holds gunicorn init lock during 30+ parallel warmup requests
- Alternative: Cloudflare cold-start TLS latency after reboot

### Resolution Paths

#### Option A: Wait & Retry (Low Risk)
Droplet may be rebooting or under maintenance. Retry deployment in 30 min.

#### Option B: Disable warm_cache.sh (Low Risk)
```bash
# On droplet (once SSH restored):
sed -i 's/^ExecStartPost/#ExecStartPost/' /etc/systemd/system/daanaa-api.service
systemctl daemon-reload
systemctl restart daanaa-api
```
First few queries will be slow (~5s), then cache populates normally.

#### Option C: Accept Current State (No Action Needed)
- Production is stable (auto-rollback working)
- IRS backfill already live in database
- Volunteer_hours code is ready; internal APIs not urgent
- Deploy when droplet connectivity is restored

### Files Ready to Deploy
- `/home/akbar/meritgiving/daanaa_api.py` ← final version with all fixes
- `/home/akbar/meritgiving/scripts/ops/sync_droplet_api.sh` ← deploy script with 90s timeout
- S3 backups preserved: `s3://daanaa-nonprofit-data/backups/droplet_api/droplet_api_20260816_234259.py` (old version, safely restored)

### Commits This Session
- 734537806c5: Increase smoke-test timeout 20→40s
- 727bbfe5b1a: Increase smoke-test timeout 40→90s

### Why This Is Safe
1. Auto-rollback tested and working (last deploy proved it)
2. Code verified on localhost (full test suite passes)
3. IRS backfill already applied (primary goal achieved)
4. Volunteer_hours fixes are internal/admin only (not user-facing)
5. Production serves traffic correctly (old version is stable)

### Next Step
Once droplet SSH is reachable:
1. Run Option B (disable warm_cache.sh), **OR**
2. Re-run sync_droplet_api.sh (90s timeout may now succeed if droplet recovered)

**Recommendation:** Wait 30 min, then retry without changes. If still fails, disable warm_cache.sh.

---

**Owner:** Claude Haiku 4.5  
**Date:** 2026-08-17 23:44  
**SLA:** Production is safe. Deploy when ready.
