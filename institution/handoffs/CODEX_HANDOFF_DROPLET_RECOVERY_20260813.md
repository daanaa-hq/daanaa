# Codex Handoff: Production Droplet Recovery (CRITICAL)
**Date:** 2026-08-13  
**From:** Claude Code  
**To:** Codex  
**Urgency:** 🔴 CRITICAL — Production site down

---

## Problem Identified

**Droplet:** 107.170.26.8 (NOTE: NOT 167.170.26.8)  
**Status:** API running but broken  
**Symptom:** `curl https://daanaa.org/api/organizations?sub=P33` returns 502 Bad Gateway

**Root Cause:** Gunicorn venv missing numpy dependency

```
ModuleNotFoundError: No module named 'numpy'
gunicorn.errors.HaltServer: Worker failed to boot.
```

---

## What's Running

- **API Server:** Gunicorn (crashed, needs restart)
- **Web Server:** Nginx proxying to gunicorn:5000
- **Location:** /opt/daanaa/
- **Code:** droplet_api.py (latest version copied)
- **Database:** merit_registry.db (old, 276MB from Aug 8)
- **Venv:** /opt/daanaa/venv (missing dependencies)

---

## Status Update (Claude's Investigation)

✅ **Issue Found:** Droplet IP was wrong (167 vs 107)  
✅ **Network:** Droplet is reachable  
✅ **Gunicorn:** Running with backup code  
⚠️ **Problem:** Backup droplet_api.py.prev incompatible with current database  
❌ **API Result:** Returning 0 organizations (should return 4152 for P33)

---

## Recovery Steps (Your Mission)

### Recommended: Use standard deployment path
```bash
# Prerequisite: verify local API is healthy
curl http://localhost:5000/health
# Should return: {"db_exists":true,"status":"ok"}

# Then deploy
bash scripts/safe_deploy_droplet.sh --code-only
```

**Why this:** Tested, stable process. Auto-rollback on failure. Never corrupts DB.

---

### Alternative: Manual quick fix
```bash
ssh -i ~/.ssh/daanaa_do_cron root@107.170.26.8
cd /opt/daanaa

# Get latest droplet_api.py from local
scp /home/akbar/meritgiving/droplet_api.py root@107.170.26.8:/opt/daanaa/

# Install all dependencies
source venv/bin/activate
pip install flask flask-cors flask-limiter twilio pyjwt numpy requests sqlalchemy

# Restart
pkill -9 -f gunicorn
/opt/daanaa/venv/bin/gunicorn -w 3 -b 127.0.0.1:5000 -b 0.0.0.0:8880 \
  --timeout 120 --access-logfile logs/access.log \
  --error-logfile logs/error.log droplet_api:app &
```

---

### Verification
```bash
# Wait 5 seconds then test
sleep 5
curl -s https://daanaa.org/api/organizations?sub=P33 | jq '.total'
# Should return: 4152 ✅ (currently returns 0 ❌)

curl -s https://daanaa.org/directory?sub=P33
# Should load and show results
```

---

## Testing Results (Before Recovery)

| Endpoint | Local | Droplet | Status |
|----------|-------|---------|--------|
| `/api/stats` | ✅ JSON | ❌ Missing | Need dependency fix |
| `/api/organizations?sub=P33` | ✅ 4,152 orgs | ❌ 502 | Gunicorn crash |
| `/directory?sub=P33` | ✅ Loads | ❌ Error | API dependency chain |

---

## Timeline

After recovery:
- Production site: ✅ Restored
- Directory page: ✅ Loads and shows results
- Data: ✅ Current (once DB synced if needed)

---

## Full Context

**Priority 1 (This):** Fix droplet API  
**Priority 2 (Parallel):** Execute domain guessing engine (ready to go)

Once you fix the droplet:
- Report back: "Droplet recovered, /api/organizations returns data"
- Then start: Domain guessing engine (`docs/operations/deployment/handoffs/CODEX_HANDOFF_DOMAIN_GUESSING_ENGINE_PRODUCTION_20260813.md`)

---

## Authority

Full sys admin authority given:
- SSH to droplet 
- Restart services
- Modify venv/dependencies
- Report findings

**Report back when:** Droplet API is returning data again.

