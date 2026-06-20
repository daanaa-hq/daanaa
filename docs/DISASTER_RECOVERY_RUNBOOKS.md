# Disaster Recovery Runbooks

Step-by-step procedures for specific failure scenarios. Follow these exactly when things break.

---

## Quick Decision Tree

**Is the system down?**
- Chatwoot not responding → [Chatwoot Recovery](#chatwoot-service-down)
- n8n not executing workflows → [n8n Recovery](#n8n-service-down)
- Jambonz not accepting calls → [Jambonz Recovery](#jambonz-service-down)
- All services down → [Full System Recovery](#full-system-down)

**Is there data loss?**
- Lost conversations in Chatwoot → [Database Recovery](#database-corruption)
- Lost workflows in n8n → [n8n Database Recovery](#n8n-database-corruption)
- Both → [Full Backup Restore](#full-backup-restore)

**Is there unusual behavior?**
- Auto-replies not sending → [Email Pipeline Broken](#email-pipeline-broken)
- Tickets not being created → [Webhook Integration Broken](#webhook-integration-broken)
- Calls not routed to webhook → [SIP Trunk Down](#sip-trunk-down)
- False positives in intent detection → [Retrain Intent Detector](#retrain-intent-detector)

---

## Chatwoot Service Down

**Symptoms:**
- http://localhost:3000 → Connection refused
- Health check script shows ❌ Chatwoot
- Incoming emails/calls not creating tickets

**Impact:** Escalations not tracked, but system still auto-responds  
**Time to fix:** 5-15 minutes  
**Data loss risk:** None (Docker volumes preserved)

### Recovery Procedure

```bash
# Step 1: Check container status
docker-compose -f /opt/chatwoot/docker-compose.yml ps
# Expected: chatwoot, postgres, redis all showing "Up"

# Step 2: If any container exited, restart
docker-compose -f /opt/chatwoot/docker-compose.yml restart

# Step 3: Wait for startup (Rails app takes 30-60 sec)
sleep 60

# Step 4: Verify Chatwoot responds
curl http://localhost:3000
# Expected: HTML response (login page)

# Step 5: Test creating a ticket manually
curl -X POST "http://localhost:3000/api/v1/inboxes/1/messages" \
  -H "Authorization: Bearer $CHATWOOT_API_TOKEN" \
  -d '{
    "email": "test@example.com",
    "content": "Recovery test",
    "source_id": "recovery_test"
  }' 2>&1 | grep -q "success" && echo "✅ API OK" || echo "❌ API Failed"

# Step 6: Check logs for errors
docker logs chatwoot_chatwoot_1 --tail 50 | grep -i error
```

**If recovery didn't work:**

1. **Check PostgreSQL health:**
   ```bash
   docker exec chatwoot_postgres_1 pg_isready
   # If not ready, PostgreSQL is down (see next section)
   ```

2. **Check disk space:**
   ```bash
   df /data
   # If >95% full, free up space (see Disk Full recovery)
   ```

3. **If still failing, restore from backup** (see [Full Backup Restore](#full-backup-restore))

**Verify fix:**
- Chatwoot login page loads ✅
- Can create a test conversation ✅
- Recent tickets visible in UI ✅

---

## n8n Service Down

**Symptoms:**
- http://localhost:5678 → Connection refused
- Emails not being processed
- Health check shows ❌ n8n

**Impact:** Email auto-responses stop, all emails escalate to Chatwoot (good: no loss)  
**Time to fix:** 5-10 minutes  
**Data loss risk:** None (workflows saved in database)

### Recovery Procedure

```bash
# Step 1: Restart n8n
docker-compose -f /opt/n8n/docker-compose.yml restart

# Step 2: Wait for startup (can take 60-90 sec)
sleep 90

# Step 3: Verify n8n responds
curl http://localhost:5678
# Expected: HTML response with n8n UI

# Step 4: Check all workflows are active
curl "http://localhost:5678/api/v1/workflows?active=true" | jq '.data | length'
# Expected: should see 4+ (email-triage, claim-verify, faq-bot, health-check)

# Step 5: Test email processing
# Send a test email to daanaa@daanaa.org
# Wait 2 minutes
# Check Metabase or n8n execution logs for "intent_detected"

# Step 6: Verify auto-response
# Within 5 minutes, you should receive auto-reply in your inbox
```

**If n8n still not responding after restart:**

1. **Check PostgreSQL (n8n database):**
   ```bash
   docker exec n8n_postgres_1 pg_isready
   # If not ready, database is down
   ```

2. **Check n8n logs for startup errors:**
   ```bash
   docker logs -f n8n --tail 50
   # Look for: "Cannot connect to database", "Out of memory", etc.
   ```

3. **If database connection error:**
   ```bash
   # Verify n8n .env has correct DB credentials
   cat /opt/n8n/.env | grep DB_POSTGRES
   
   # If wrong, fix and restart:
   docker-compose -f /opt/n8n/docker-compose.yml down
   # [Edit .env with correct credentials]
   docker-compose -f /opt/n8n/docker-compose.yml up -d
   ```

**Verify fix:**
- n8n login page loads ✅
- All 4 workflows show "active" ✅
- Test email receives auto-reply ✅

---

## Jambonz Service Down

**Symptoms:**
- Calling the DID goes straight to voicemail (no IVR prompt)
- Health check shows ❌ Jambonz
- SIP port 5060 not listening

**Impact:** Voice claims not possible, callers try again later or email  
**Time to fix:** 5-10 minutes  
**Data loss risk:** None

### Recovery Procedure

```bash
# Step 1: Check if port is actually listening
netstat -tlnp | grep :5060
# Expected: LISTEN state on port 5060

# Step 2: If not listening, restart Jambonz
docker-compose -f /opt/jambonz/docker-compose.yml restart

# Step 3: Wait for startup (30-60 sec)
sleep 60

# Step 4: Verify port is now listening
netstat -tlnp | grep :5060
# Expected: tcp LISTEN

# Step 5: Test with a call
# From any phone, dial your DID
# Expected: Ring 2-3 times, then: "Welcome to Daanaa. Press 1 to claim..."

# Step 6: Complete a full claim flow test
# 1. Press 1
# 2. Say an EIN: "46 3120432"
# 3. Say an email: "admin at example dot org"
# Expected: "Check your email..." + Chatwoot ticket created within 1 min
```

**If Jambonz won't start:**

1. **Check if another process is using port 5060:**
   ```bash
   lsof -i :5060
   # If something else is there, kill it:
   sudo kill -9 [PID]
   ```

2. **Check SIP trunk connectivity (Voxbeam):**
   ```bash
   # Verify Voxbeam account has:
   # - Active credit (>$5 remaining)
   # - DID enabled and active
   # - SIP routing configured
   
   # Check Voxbeam dashboard: https://www.voxbeam.com/user
   # Or email support@voxbeam.com: "DID not working, port 5060"
   ```

3. **Check Jambonz config:**
   ```bash
   cat /opt/jambonz/config/sip-config.json | grep -i "voxbeam\|username\|password"
   # Verify credentials match what's in your Voxbeam account
   ```

**Verify fix:**
- Port 5060 shows LISTEN ✅
- Call receives IVR prompt ✅
- Full claim flow creates Chatwoot ticket ✅

---

## Full System Down (All Services Offline)

**Symptoms:**
- http://localhost:3000 → Connection refused (Chatwoot)
- http://localhost:5678 → Connection refused (n8n)
- Port 5060 not listening (Jambonz)
- Power failure or server crash

**Impact:** Complete system outage, no email auto-response, calls fail  
**Time to fix:** 10-30 minutes  
**Data loss risk:** Low (backups exist, but recent data in-flight could be lost)

### Recovery Procedure

```bash
# Step 1: Check if Docker daemon is running
docker ps
# If not, Docker service crashed. Restart:
sudo systemctl restart docker

# Step 2: Start all services
docker-compose -f /opt/chatwoot/docker-compose.yml up -d
docker-compose -f /opt/n8n/docker-compose.yml up -d
docker-compose -f /opt/jambonz/docker-compose.yml up -d

# Step 3: Wait for all services to stabilize (120 sec)
sleep 120

# Step 4: Run full health check
/home/akbar/meritgiving/scripts/health_check.sh
# Expected: All ✅

# Step 5: Test each component
# A. Email: send test to daanaa@daanaa.org, wait 5 min for auto-reply
# B. Voice: call DID, complete IVR flow, check Chatwoot
# C. Metrics: open Metabase, verify recent data shows up

# Step 6: If any component still down, follow specific recovery above
```

**If Docker daemon won't restart:**

```bash
# Check system resources
df -h /data
free -h
# If disk full (>95%), delete old backups:
rm -f /data/automation_backups/*_*_[0-3]0*.sql.gz  # Keep only last 10 days
# If memory low, restart server

# If still won't start, server may have disk corruption
# Last resort: power down, power up
sudo shutdown -r now
# Wait 120 seconds
# Retry Docker start
```

**Verify fix:**
- All 3 services up ✅
- Email test receives auto-reply ✅
- Voice test completes claim flow ✅
- Health check all ✅

---

## Database Corruption

**Symptoms:**
- Chatwoot shows error: "database is locked" or "disk I/O error"
- Conversations list is empty or shows errors
- Recovery from backup may be needed

**Impact:** Can't read/write conversations  
**Time to fix:** 15-30 minutes  
**Data loss risk:** HIGH (if not using backups)

### Recovery Procedure

**Option A: Soft Recovery (Lock Cleanup)**

```bash
# Step 1: Stop Chatwoot
docker-compose -f /opt/chatwoot/docker-compose.yml down

# Step 2: Check PostgreSQL
docker exec chatwoot_postgres_1 pg_isready
# Should show: accepting connections

# Step 3: Try to clean locks
docker exec chatwoot_postgres_1 psql -U postgres -d chatwoot_production -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
   WHERE state = 'idle' AND query_start < NOW() - INTERVAL '5 minutes';"

# Step 4: Restart Chatwoot
docker-compose -f /opt/chatwoot/docker-compose.yml up -d
sleep 60

# Step 5: Verify
curl http://localhost:3000
```

**Option B: Full Backup Restore** (if Option A fails)

See [Full Backup Restore](#full-backup-restore) section below.

---

## Email Pipeline Broken

**Symptoms:**
- Emails arrive at daanaa@daanaa.org
- n8n shows error: "Gmail authentication failed" or "SMTP error"
- Emails not appearing in Chatwoot
- Auto-replies not being sent

**Impact:** Email support offline  
**Time to fix:** 5-15 minutes  
**Data loss risk:** Emails queue in Gmail, no loss

### Recovery Procedure

```bash
# Step 1: Check Gmail authentication
# In n8n UI: Credentials → Gmail
# Click "Reauthenticate"
# Complete OAuth flow

# Step 2: Test email trigger
# In n8n UI: email-triage workflow → Gmail Trigger node
# Click "Test" → should show 1+ emails

# Step 3: If no emails shown, check Gmail settings
# https://myaccount.google.com/security
# Verify "Less secure app access" is ON
# (Or use OAuth if available)

# Step 4: Manually re-trigger n8n
# In n8n UI: Workflows → email-triage → Execute
# Or restart n8n entirely:
docker-compose -f /opt/n8n/docker-compose.yml restart

# Step 5: Test full flow
# Send test email to daanaa@daanaa.org
# Wait 2 minutes for n8n polling
# Should see in Metabase metrics within 5 min
```

**If Gmail auth keeps failing:**

```bash
# Option A: Check Gmail app password (if using 2FA)
# https://myaccount.google.com/apppasswords
# Generate new password, update n8n credentials

# Option B: Create new Gmail service account
# (If daanaa@daanaa.org account is compromised)
# This is complex; email ops/admin for help
```

**Verify fix:**
- n8n Gmail node shows ✅ authenticated
- Test email received auto-reply ✅
- Metric logged to Metabase ✅

---

## Webhook Integration Broken

**Symptoms:**
- Voice claims not creating Chatwoot tickets
- Jambonz call completes but no ticket appears
- n8n shows error: "Failed to send HTTP request to Chatwoot"

**Impact:** Voice claims tracked manually only  
**Time to fix:** 5-10 minutes  
**Data loss risk:** Calls logged locally, can be manually entered

### Recovery Procedure

```bash
# Step 1: Verify Chatwoot API is working
curl "http://localhost:3000/api/v1/account" \
  -H "Authorization: Bearer $CHATWOOT_API_TOKEN"
# Expected: JSON response with account info

# Step 2: If 401 or 403, regenerate API token
# In Chatwoot UI: Settings → API Tokens → Generate New
# Copy new token

# Step 3: Update n8n credentials
# In n8n UI: Credentials → chatwoot_api
# Paste new token
# Click "Test Connection" → should show ✅

# Step 4: Check Chatwoot webhook endpoint
# In n8n UI: claim-verify workflow → "Create Chatwoot Ticket" node
# Verify URL: "http://chatwoot:3000/api/v1/inboxes/1/messages"
# (Should point to chatwoot service, not localhost)

# Step 5: Test claim flow
# From phone: Call DID → complete claim (EIN + email)
# Wait 2 minutes
# Check Chatwoot: Inboxes → [Email] → New conversation should appear
```

**If webhook still failing:**

```bash
# Check n8n logs for exact error
docker logs -f n8n 2>&1 | grep -i "chatwoot\|webhook\|error" | tail -20

# If error says "connection refused":
#  Chatwoot is down or not responding
#  (See Chatwoot Service Down recovery)

# If error says "401 Unauthorized":
#  API token is invalid or expired
#  Regenerate token (Step 2 above)

# If error says "timeout":
#  Network latency too high between n8n and Chatwoot
#  Check: docker network ls, docker network inspect
```

**Verify fix:**
- Chatwoot API responds with 200 ✅
- n8n credentials test shows ✅
- Voice claim creates ticket ✅

---

## SIP Trunk Down

**Symptoms:**
- Calls to DID fail immediately (no ring)
- "All circuits are busy" or "Service unavailable"
- Jambonz logs show: "Cannot register with SIP server"

**Impact:** Voice support completely offline  
**Time to fix:** 5-30 minutes (depends on Voxbeam)  
**Data loss risk:** None

### Recovery Procedure

```bash
# Step 1: Verify Voxbeam account is active
# Go to: https://www.voxbeam.com/user
# Check:
#   - Account has credit (>$5 remaining)
#   - DID is "Active"
#   - SIP routing is enabled

# Step 2: Verify Jambonz SIP config
cat /opt/jambonz/config/sip-config.json
# Expected:
# {
#   "sip_servers": [{
#     "domain": "voxbeam.com",
#     "username": "[YOUR_USERNAME]",
#     "password": "[YOUR_PASSWORD]"
#   }]
# }

# Step 3: Check Jambonz logs for SIP registration
docker logs jambonz_jambonz_1 2>&1 | grep -i "register\|sip\|voxbeam" | tail -20
# Expected: "REGISTER success" or similar

# Step 4: If registration failing, check:
docker logs jambonz_jambonz_1 2>&1 | grep -i "401\|403\|authentication"
# 401 = Wrong password
# 403 = Account inactive

# Step 5: If credentials wrong, update:
nano /opt/jambonz/config/sip-config.json
# Fix username/password
# Restart Jambonz:
docker-compose -f /opt/jambonz/docker-compose.yml restart
sleep 60

# Step 6: Test registration
docker logs jambonz_jambonz_1 2>&1 | grep "REGISTER"
```

**If Voxbeam account is inactive:**

```bash
# 1. Log in to Voxbeam: https://www.voxbeam.com/user
# 2. Check account status → may need to:
#    - Add credit (account suspended for non-payment)
#    - Verify email (security hold)
#    - Contact support (technical issue)

# 3. Contact Voxbeam support:
#    Email: support@voxbeam.com
#    Subject: "SIP DID registration failing for [YOUR_DID]"
#    Include: "Trying to register from [YOUR_IP]:5060"

# This can take 1-4 hours. In the meantime:
#    Email daanaa@daanaa.org subscribers: 
#    "Voice support temporarily offline. Please email support@daanaa.org"
```

**Verify fix:**
- Voxbeam account shows active ✅
- Jambonz logs show REGISTER success ✅
- Call to DID rings (not "number unavailable") ✅
- IVR prompt plays ✅

---

## Full Backup Restore

**When to use:** Database corruption, accidental deletion, ransomware, major data loss

**Impact:** Lose data from last backup to now (typically <24h)  
**Time to restore:** 15-30 minutes  
**Data recovery:** 99% (encrypted backups; immutable copies optional)

### Restore Chatwoot

```bash
# Step 1: Stop Chatwoot
docker-compose -f /opt/chatwoot/docker-compose.yml down

# Step 2: List available backups
ls -lh /data/automation_backups/chatwoot_*.sql.gz | tail -5
# Example: chatwoot_20260620_020000.sql.gz (2GB)

# Step 3: Choose backup date (usually yesterday)
BACKUP_FILE="/data/automation_backups/chatwoot_20260620_020000.sql.gz"

# Step 4: Restore
gunzip -c "$BACKUP_FILE" | \
  docker-compose -f /opt/chatwoot/docker-compose.yml exec -T postgres \
  psql -U postgres -d chatwoot_production

# Step 5: Start Chatwoot
docker-compose -f /opt/chatwoot/docker-compose.yml up -d
sleep 60

# Step 6: Verify
curl http://localhost:3000
# Login → check conversations are restored
```

### Restore n8n

```bash
# Same procedure, but for n8n:

docker-compose -f /opt/n8n/docker-compose.yml down

BACKUP_FILE="/data/automation_backups/n8n_20260620_020000.sql.gz"

gunzip -c "$BACKUP_FILE" | \
  docker-compose -f /opt/n8n/docker-compose.yml exec -T postgres \
  psql -U n8n -d n8n

docker-compose -f /opt/n8n/docker-compose.yml up -d
sleep 90

# Verify all workflows are still there
curl "http://localhost:5678/api/v1/workflows" | jq '.data | length'
```

### Restore Both (Full Stack)

```bash
# Stop all services
docker-compose -f /opt/chatwoot/docker-compose.yml down
docker-compose -f /opt/n8n/docker-compose.yml down
docker-compose -f /opt/jambonz/docker-compose.yml down

# Restore databases (use same BACKUP_FILE from step 2 above)
gunzip -c /data/automation_backups/chatwoot_*.sql.gz | \
  docker exec -i chatwoot_postgres_1 psql -U postgres -d chatwoot_production

gunzip -c /data/automation_backups/n8n_*.sql.gz | \
  docker exec -i n8n_postgres_1 psql -U n8n -d n8n

# Restart all services
docker-compose -f /opt/chatwoot/docker-compose.yml up -d
docker-compose -f /opt/n8n/docker-compose.yml up -d
docker-compose -f /opt/jambonz/docker-compose.yml up -d

# Wait 180 seconds
sleep 180

# Full health check
/home/akbar/meritgiving/scripts/health_check.sh
```

**After restore:**

```bash
# Email incident notification
echo "
System recovered from database backup (20260620).
Data recovered up to: [DATE] 2 AM UTC
Data lost: [EST] <24 hours recent (in-flight emails/calls)

Actions taken:
1. Restored Chatwoot database
2. Restored n8n workflows
3. Verified all services online
4. Full system health check passed

Customers notified: N/A (transparent recovery)
Next steps: Monitor logs for errors over next 24h
" | mail -s "Recovery Complete: Automation Stack" akbar.khowaja@gmail.com
```

---

## Retrain Intent Detector

**When:** New intent patterns emerge, false positives/negatives common

**Symptoms:**
- 10%+ of emails misclassified
- Same keyword triggering wrong intent
- New use case not covered

**Time to fix:** 30-60 minutes (includes testing)  
**Data loss:** None

### Recovery Procedure

```bash
# Step 1: Identify the problem pattern
# Look in Chatwoot for tickets that should have been auto-handled
# Example: "support" emails being classified as "feedback"

# Step 2: Extract problematic keywords
PROBLEM_KEYWORD="broken"
SHOULD_BE_INTENT="support_ticket"
CURRENTLY_DETECTED="feedback"

# Step 3: Update Intent Detector in n8n
# In n8n UI:
# - Workflows → email-triage
# - Double-click "Intent Detector" node
# - Find current detection logic (~line 15):
#   if (text.includes('feedback') || text.includes('suggestion')) {
#     intent = 'feedback';
#   }
# 
# Update logic to catch new pattern:
#   if (text.includes('broken') || text.includes('not working')) {
#     intent = 'support_ticket';
#     priority = 'high';
#   }

# Step 4: Deploy updated workflow
# In n8n UI: Save the workflow

# Step 5: Test with sample emails
for keyword in "my site is broken" "not working" "something is wrong"; do
  curl -X POST "http://localhost:5678/webhook/email-test" \
    -H "Content-Type: application/json" \
    -d '{
      "subject": "Problem",
      "body": "'$keyword'",
      "from": "test@example.com"
    }'
  sleep 5
done

# Step 6: Verify results
# Should see:
# - 3 Chatwoot tickets created (not auto-replied)
# - Metric logs show: intent=support_ticket × 3
```

**If update breaks other intents:**

```bash
# Revert to previous version
# In n8n UI:
# - Workflows → email-triage → Version history
# - Revert to "stable" version

# Then make more careful update:
# - Instead of removing a keyword, ADD specificity
# Before: if (text.includes('support'))
# After:  if (text.includes('support') && !text.includes('volunteer support'))
```

**Verify fix:**
- All test emails classified correctly ✅
- No false positives (feedback still detected as feedback) ✅
- No false negatives (support still detected as support) ✅

---

## When to Escalate to External Help

**You can fix alone:**
- Service restart fails → restore from backup
- Intent patterns wrong → update rules
- Chatwoot/n8n credentials expired → regenerate
- Low disk space → cleanup backups

**Call Voxbeam support (+1-844-VOXBEAM or support@voxbeam.com):**
- SIP trunk cannot register with Voxbeam
- DID is "blocked" or inactive in Voxbeam UI
- Account suspension for non-payment
- Inbound calls routing to wrong destination

**Call hosting provider / server admin:**
- Server won't boot
- Disk controller failure
- Network connectivity lost
- Power/cooling issues

**Email Docker support (if severe):**
- Docker daemon won't start after system recovery
- Persistent volume corruption
- Network isolation issues affecting services

**Internal escalation:**
- If recovery takes >30 min, notify stakeholders
- If data loss confirmed, follow incident postmortem (LESSONS.md)

---

## Testing Disaster Recovery

**Monthly drill (first Sunday):**

```bash
# 1. Pick a random backup file
BACKUP=$(ls /data/automation_backups/chatwoot_*.sql.gz | shuf | head -1)

# 2. Restore to test environment (if available)
# OR simply verify backup integrity:
gunzip -t "$BACKUP" && echo "✅ Backup valid"

# 3. Time a mock restore (without actually restoring)
# Record how long it would take

# 4. Document in LESSONS.md:
#    "Tested backup restore 2026-06-27. 
#     Chatwoot would restore in ~10 min. 
#     All backups valid. Last 30 days available."
```

This ensures when you need backups, you know they work.

