# V6 Deployment Incident & Recovery — 2026-07-29

**Status:** IN RECOVERY  
**Severity:** P1 (code deployed, infrastructure issue)  
**Started:** 2026-07-29T18:40:00Z  
**Last Update:** 2026-07-29T19:09:00Z

---

## Incident Summary

V6 financial context code was successfully deployed to production droplet, but public endpoint returns HTML instead of JSON due to reverse proxy/Cloudflare caching issue.

**What worked:** Local endpoint on droplet returns JSON ✅  
**What failed:** Public HTTPS endpoint still serving SPA fallback ❌

---

## Root Cause Analysis

### Deployment Phase (18:40–18:50 UTC)
- ✅ Code changes prepared and reviewed
- ✅ Production approval received
- ✅ Old droplet_api.py backed up to S3
- ❌ **Smoke tests failed** — homepage/search not serving after restart
- ❌ **Rollback failed** — SSH connection lost

### Manual Recovery Phase (18:43–19:09 UTC)
- ✅ User manually restarted gunicorn on droplet
- ✅ Verified v6 route exists in droplet_api.py (line 2920)
- ✅ Copied v6_financial_context_api.py support module
- ✅ Restarted gunicorn with new code
- ✅ Local test: endpoint returns JSON for EIN 264837170
- ❌ Public test: endpoint still returns HTML (404 page)

### Infrastructure Gap Identified

The reverse proxy / Cloudflare layer is not routing API requests to the updated gunicorn.

**Likely causes:**
1. Cloudflare cache serving stale 404 response
2. Nginx reverse proxy not reloaded after gunicorn restart
3. Load balancer or proxy config pointing to wrong backend

---

## Verification Checklist

| Test | Result | Location |
|------|--------|----------|
| Local gunicorn module load | ✅ PASS | droplet:5000 |
| Local v6 route exists | ✅ PASS | grep line 2920 |
| Local endpoint returns JSON | ✅ PASS | http://127.0.0.1:5000/api/... |
| Public endpoint via HTTPS | ❌ FAIL | https://daanaa.org/api/... (returns HTML) |
| Database v6 tables populated | ❌ FAIL | Missing: v6_peer_context_assignments |

---

## Recovery Steps

### Step 1: Clear Cloudflare Cache (IMMEDIATE)
```bash
# Via Cloudflare dashboard or CLI:
cloudflare --zone daanaa.org purge-cache --files https://daanaa.org/api/organizations/*/financial-context
# OR restart nginx to force fresh backend fetch
ssh root@162.243.97.179 "systemctl restart nginx"
```

### Step 2: Verify Reverse Proxy is Routing to Gunicorn
```bash
# On droplet, check nginx is proxying to localhost:5000
ssh root@162.243.97.179 "grep -n 'proxy_pass.*5000' /etc/nginx/sites-enabled/*"
# Expected: proxy_pass http://127.0.0.1:5000;
```

### Step 3: Restart Web Stack
```bash
ssh root@162.243.97.179 "
  echo 'Restarting nginx...'
  systemctl restart nginx
  sleep 3
  echo 'Verifying gunicorn still running...'
  ps aux | grep gunicorn | grep -v grep
"
```

### Step 4: Public Verification
```bash
# Test from home server
curl -s https://daanaa.org/api/organizations/264837170/financial-context | python3 -c "import json,sys; d=json.load(sys.stdin); print('✅ PUBLIC V6 LIVE' if 'data_status' in d else '❌ Still broken')"
```

### Step 5: Populate v6 Database Tables (BLOCKING)
The endpoint returns error: `no such table: v6_peer_context_assignments`

**Required action:** Load v6 peer context data into database
```bash
# Pending: run v6 data population script
# scripts/populate_v6_peer_context.py (if exists)
# OR manual SQL schema + data import
```

---

## Known Issues

1. **Missing systemd service:** No daanaa-api.service exists on droplet
   - Current: gunicorn running via nohup (will die on reboot)
   - Fix: Create systemd service file + enable auto-restart

2. **Missing v6 database tables:** v6_peer_context_assignments not in schema
   - Current: Endpoint errors gracefully (returns JSON with error message)
   - Fix: Populate tables with peer group data before public launch

3. **Pre-existing startup warnings:** Some modules fail to import at startup
   - Not blocking: API still functions
   - Scope: Out of scope for v6 hotfix

---

## Rollback Procedure

If public endpoint still broken after recovery steps:

```bash
# Restore previous version from S3
ssh root@162.243.97.179 "
  aws s3 cp s3://daanaa-nonprofit-data/backups/droplet_api/droplet_api_20260729_133926.py /opt/daanaa/droplet_api.py
  pkill -9 gunicorn
  sleep 2
  cd /opt/daanaa && /opt/daanaa/venv/bin/gunicorn --workers 2 --worker-class sync --bind 127.0.0.1:5000 --timeout 60 droplet_api:app > /var/log/daanaa-gunicorn.log 2>&1 &
  systemctl restart nginx
"
```

---

## Evidence

- **S3 Backup:** s3://daanaa-nonprofit-data/backups/droplet_api/droplet_api_20260729_133926.py
- **Deployment Log:** .release_coordination/reports/deployment-log.txt
- **Gunicorn Log:** /var/log/daanaa-gunicorn.log (on droplet)
- **Production Record:** institution/handoffs/2026-07-29-v6-production-release.md
- **Local Test Pass:** confirmed v6 endpoint JSON via localhost:5000

---

## Post-Incident Actions

1. ✅ Create systemd service for daanaa-api (persistent across reboots)
2. ✅ Populate v6 peer context database tables
3. ✅ Document reverse proxy / Cloudflare configuration
4. ✅ Add smoke test for /api endpoints (not just homepage)
5. ✅ Add monitoring for v6 endpoint health

---

## Sign-Off

**Incident Owner:** User (akbar.khowaja@gmail.com)  
**Code Status:** Deployed and tested locally ✅  
**Infrastructure Status:** Blocking recovery step ⚠️  
**Timeline:** 40 minutes elapsed (deployment → manual recovery → proxy investigation)
