# Event Platform Deployment Guide

## Pre-Deployment Checklist

### 1. Staging Database
```bash
# Backup current database
cp data/merit_registry.db data/merit_registry.db.backup-$(date +%Y%m%d)

# Run migration
sqlite3 data/merit_registry.db < database/migrations/027_event_volunteer_platform.sql

# Verify tables created
sqlite3 data/merit_registry.db ".tables" | grep event
# Expected output: event_audit_log event_stats event_teams event_volunteers events volunteer_hours
```

### 2. Backend Verification
```bash
# Activate venv
source ~/meritgiving/venv/bin/activate

# Check Python syntax
python3 -m py_compile event_platform_api.py

# Test imports (run in Python shell)
python3 << 'EOF'
from event_platform_api import init_event_platform
from flask import Flask
app = Flask(__name__)
init_event_platform(app)
print(f"✓ Event platform initialized")
print(f"✓ Routes registered: {[str(r) for r in app.url_map.iter_rules() if 'events' in str(r)][:5]}")
EOF
```

### 3. Frontend Verification
```bash
cd frontend

# Check TypeScript
npx tsc --noEmit
# Should complete with no errors

# Build
npm run build
# Should generate frontend/dist/ with no errors

# Verify routes exist
grep -c "event/:eventId" src/App.tsx
# Should output: 5 (5 event routes)
```

### 4. API Smoke Test (Local Dev Server)
```bash
# Terminal 1: Start API
source ~/meritgiving/venv/bin/activate
python3 daanaa_api.py

# Terminal 2: Test endpoints
# Create event
curl -X POST http://localhost:5000/api/events \
  -H "Authorization: Bearer test_user_123" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Event",
    "event_date": "2026-09-21",
    "organizer_name": "Test Org"
  }'
# Expected: 201 response with event ID

# Get event
curl http://localhost:5000/api/events/evt_xxxxx
# Expected: 200 response with event data

# Register volunteer
curl -X POST http://localhost:5000/api/events/evt_xxxxx/volunteers \
  -H "Content-Type: application/json" \
  -d '{
    "volunteer_name": "John Doe",
    "volunteer_email": "john@example.com",
    "role": "Setup"
  }'
# Expected: 201 response with volunteer ID

# Log hours
curl -X POST http://localhost:5000/api/events/evt_xxxxx/hours \
  -H "Content-Type: application/json" \
  -d '{
    "volunteer_id": "vol_xxxxx",
    "hours": 4.5,
    "service_date": "2026-09-21",
    "job_description": "Setup"
  }'
# Expected: 201 response with hour ID
```

## Deployment to Staging

### Step 1: Database
```bash
ssh root@162.243.97.179
cd /home/akbar/meritgiving

# Backup (CRITICAL)
cp data/merit_registry.db data/merit_registry.db.backup-$(date +%Y%m%d)

# Run migration
sqlite3 data/merit_registry.db < database/migrations/027_event_volunteer_platform.sql

# Verify
sqlite3 data/merit_registry.db "SELECT COUNT(*) as table_count FROM sqlite_master WHERE type='table' AND name LIKE 'event%';"
# Should output: 6
```

### Step 2: API Code
```bash
# Already in SSH session at /home/akbar/meritgiving

# Update code (git pull if tracking, or manual copy)
git pull origin master

# Verify file exists
ls -l event_platform_api.py
# Should output: ~14KB file

# Restart API
./restart_api.sh

# Wait 5 seconds for server to restart
sleep 5

# Health check
curl http://localhost:5000/health
# Expected: {"status": "ok"}
```

### Step 3: Frontend Build & Deploy
```bash
# On local machine
cd frontend
npm run build

# Sync to droplet (already configured in sync_droplet_api.sh)
./scripts/ops/sync_droplet_api.sh

# Verify on droplet
curl https://daanaa.org/
# Should render home page successfully
```

### Step 4: Final Smoke Test
```bash
# On local machine
curl https://daanaa.org/event/test-event-page
# Should render EventDetails page (or 404 if no event exists yet)

# Create test event via API
FIREBASE_TOKEN="YOUR_TEST_TOKEN"
curl -X POST https://daanaa.org/api/events \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "AKF Golf Tournament",
    "event_date": "2026-09-21",
    "organizer_name": "Akbar Khowaja",
    "donation_url": "https://fundraise.funraisin.com/akf-golf-2026"
  }'
# Expected: 201 with event ID like evt_abc123

# Get event
EVENT_ID="evt_abc123"
curl https://daanaa.org/api/events/$EVENT_ID
# Expected: 200 with event data
```

## Rollback Procedure

If deployment fails:

```bash
# On droplet
ssh root@162.243.97.179
cd /home/akbar/meritgiving

# Option 1: Restore database
cp data/merit_registry.db.backup-YYYYMMDD data/merit_registry.db

# Option 2: Revert code
git revert HEAD

# Restart API
./restart_api.sh

# Verify health
curl http://localhost:5000/health
```

## Post-Deployment Monitoring

### Logs
```bash
# API errors
tail -f /var/log/gunicorn/daanaa_api.log

# Application logs
journalctl -u daanaa_api -f

# Nginx errors
tail -f /var/log/nginx/error.log
```

### Database Integrity
```bash
# Check for errors
sqlite3 data/merit_registry.db "PRAGMA integrity_check;"
# Expected: ok

# Verify event tables are empty (new deployment)
sqlite3 data/merit_registry.db "SELECT COUNT(*) FROM events;"
# Expected: 0
```

### Performance
```bash
# API response time
time curl https://daanaa.org/api/events
# Expected: < 200ms

# Check database file size
ls -lh data/merit_registry.db
# Expected: Increase by ~1MB from new tables
```

## Verification Checklist

After deployment, verify these work end-to-end:

- [ ] Create event via API
- [ ] View event details on website
- [ ] Register as volunteer
- [ ] Log volunteer hours
- [ ] View dashboard stats update
- [ ] View pending approvals
- [ ] Approve hours
- [ ] Check donation link shows (if configured)
- [ ] Database audit log has entries
- [ ] No errors in logs

## Troubleshooting

### "Event not found" on details page
- Check event ID in URL is correct
- Verify database migration ran (check `sqlite3 data/merit_registry.db ".tables"`)
- Check API returned 201 status on creation

### "Authorization failed" on approval endpoint
- Verify Firebase token is valid
- Check organizer_id in event matches auth token
- Ensure `Authorization: Bearer <token>` header format is correct

### "Volunteer already registered" error
- This is expected! Database has UNIQUE constraint on (event_id, volunteer_id)
- Check if volunteer already in database: `sqlite3 data/merit_registry.db "SELECT * FROM event_volunteers WHERE event_id='evt_xxx' AND volunteer_email='email@example.com';"`

### Frontend shows blank page
- Check browser console for errors
- Verify `VITE_API_URL` environment variable is set correctly
- Check Nginx is reverse-proxying API calls to Flask

---

**Deployment Owner:** Akbar Khowaja  
**Escalation:** Claude Code AI Engineering Agent  
**Last Updated:** 2026-07-22
