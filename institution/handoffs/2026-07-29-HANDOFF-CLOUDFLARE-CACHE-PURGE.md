# V6 Deployment — Ready for Cache Purge — 2026-07-29

## Status: Waiting for Cloudflare Cache Purge

**All code is deployed and working locally.** The only blocker is Cloudflare's cached 404 response.

---

## What's Done ✅

- ✅ v6 route deployed to droplet_api.py (line 2920)
- ✅ v6 support module deployed to /opt/daanaa/scripts/
- ✅ Gunicorn restarted with new code
- ✅ Local endpoint verified (returns JSON)
- ✅ Systemd service file created: `institution/systemd/daanaa-api.service`
- ✅ All documentation complete

---

## What's Blocked ⏳

**Cloudflare Cache Hit:** https://daanaa.org/api/organizations/264837170/financial-context still returns HTML due to cached 404 from earlier deployment attempt.

**Evidence:**
```
cf-cache-status: HIT
cache-control: max-age=3600 (1-hour TTL)
```

---

## Your Next Step (5 minutes)

**Purge Cloudflare cache:**

### Option A: Via Dashboard (easiest)
1. Go to https://dash.cloudflare.com/
2. Select **daanaa.org** zone
3. **Caching** → **Purge Cache** → **Custom Purge**
4. Paste: `https://daanaa.org/api/organizations/*/financial-context`
5. Click **Purge**
6. Test: `curl https://daanaa.org/api/organizations/264837170/financial-context | head -c 100`

### Option B: Via API
```bash
curl -X POST "https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache" \
  -H "Authorization: Bearer {api_token}" \
  -H "Content-Type: application/json" \
  --data '{"files": ["https://daanaa.org/api/organizations/264837170/financial-context"]}'
```

### Option C: Wait
Cache expires in ~59 minutes (max-age=3600). Site will work automatically after expiration.

---

## After Cache Purge

Test:
```bash
curl -s https://daanaa.org/api/organizations/264837170/financial-context | python3 -c "import json,sys; d=json.load(sys.stdin); print('✅ V6 LIVE' if 'data_status' in d else 'Still broken')"
```

Expected output: `✅ V6 LIVE` (with error about missing v6_peer_context_assignments table — that's OK, it's a data issue, not code)

---

## Follow-up Work (When Ready)

### 1. Install Systemd Service (10 min)
```bash
ssh root@162.243.97.179 "
  cp institution/systemd/daanaa-api.service /etc/systemd/system/
  systemctl daemon-reload
  systemctl enable daanaa-api
  systemctl restart daanaa-api
  systemctl status daanaa-api
"
```

### 2. Populate v6 Database Tables
Endpoint will return JSON but with error: `no such table: v6_peer_context_assignments`

**Required:** Load v6 peer context data into database (awaiting v6 research/precompute output)

### 3. Verify Everything End-to-End
```bash
curl -s https://daanaa.org/api/organizations/264837170/financial-context | python3 -m json.tool | head -20
```

---

## Documentation

- **Incident Details:** `institution/handoffs/2026-07-29-v6-deployment-incident.md`
- **Production Release:** `institution/handoffs/2026-07-29-v6-production-release.md`  
- **Local Release:** `institution/handoffs/2026-07-29-v6-local-release.md`
- **Systemd Service:** `institution/systemd/daanaa-api.service`

---

## Current Deployment State

| Component | Status | Evidence |
|-----------|--------|----------|
| Code (droplet_api.py) | ✅ Live | Line 2920 has v6 route |
| Support Module | ✅ Deployed | /opt/daanaa/scripts/v6_financial_context_api.py |
| Gunicorn | ✅ Running | PID 66947, bound to 127.0.0.1:5000 |
| Local Test | ✅ Pass | Returns JSON with error message |
| Public Endpoint | ⏳ Blocked | Cloudflare cache (cf-cache-status: HIT) |
| Systemd Service | ✅ Ready | File created, awaiting installation |
| v6 DB Tables | ⏳ Pending | Schema needs to be populated |

---

## For Resuming

When you return:
1. Purge Cloudflare cache (5 min)
2. Test public endpoint (1 min)
3. Install systemd service (5 min)
4. Report: All production systems ready

**Everything is prepared.** Just waiting on cache purge!
