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

## Recovery Steps (Your Mission)

### Step 1: Reinstall Dependencies
```bash
ssh -i ~/.ssh/daanaa_do_cron root@107.170.26.8

cd /opt/daanaa
source venv/bin/activate
pip install -r requirements.txt  # or manually install numpy
# Or: pip install numpy flask requests
```

### Step 2: Restart Gunicorn
```bash
pkill -f droplet_api
cd /opt/daanaa
/opt/daanaa/venv/bin/gunicorn -w 3 -b 127.0.0.1:5000 -b 0.0.0.0:8880 \
  --timeout 120 --access-logfile logs/access.log \
  --error-logfile logs/error.log droplet_api:app &
```

### Step 3: Verify
```bash
curl -s https://daanaa.org/api/organizations?sub=P33 | jq '.total'
# Should return: 4152 (not 0)
```

### Step 4: Smoke Test
```bash
curl -s https://daanaa.org/directory?sub=P33 | grep -c "results"
# Should load without errors
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
- Then start: Domain guessing engine (`CODEX_HANDOFF_DOMAIN_GUESSING_ENGINE_PRODUCTION_20260813.md`)

---

## Authority

Full sys admin authority given:
- SSH to droplet 
- Restart services
- Modify venv/dependencies
- Report findings

**Report back when:** Droplet API is returning data again.

