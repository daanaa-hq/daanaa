# Integration Test Suite

Automated end-to-end tests to verify the entire automation stack works before go-live.

---

## Purpose

Tests that the complete flow works: email arrives → intent detection → auto-response/escalation → metric logged → visible in Metabase. Not unit tests; full-stack validation.

**Run before go-live and after any major change.**

---

## Test Framework Setup

### Prerequisites

```bash
# Install test dependencies
pip install pytest requests pytest-timeout

# Install curl (usually pre-installed)
which curl

# Verify test email address is accessible
echo "test-integration@example.com" | mail -s "Test" daanaa@daanaa.org
# (Manual check: you should receive confirmation in ~5 min)
```

### Test Email Address

Use a test email you control:
```bash
TEST_EMAIL="your-test-email@gmail.com"
```

---

## Test Suite: 12 Core Tests

### Test 1: Email Triage — Donation Intent

```bash
# Send email with donation keywords
curl -X POST "http://localhost:5678/webhook/email-test" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "How do I give to the Red Cross?",
    "body": "I want to donate to help with disaster relief.",
    "from": "'$TEST_EMAIL'"
  }'

# Expected:
# 1. n8n logs "intent detected: donation_link"
# 2. Auto-reply email arrives within 5 min
# 3. NO Chatwoot ticket created
# 4. Metabase metric logged: intent=donation_link, auto_responded=true

# Verify:
curl "http://localhost:3000/api/v1/account/conversations?limit=1" | jq '.payload | length'
# Should be 0 (no escalation)
```

**Pass/Fail:** ✅ Auto-reply received within 5 min, no Chatwoot ticket

---

### Test 2: Email Triage — Support Ticket Intent

```bash
curl -X POST "http://localhost:5678/webhook/email-test" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Your website is broken",
    "body": "The directory page keeps timing out. This is urgent!",
    "from": "'$TEST_EMAIL'"
  }'

# Expected:
# 1. n8n logs "intent detected: support_ticket"
# 2. NO auto-reply sent
# 3. Chatwoot ticket created with priority=high
# 4. Metric logged: intent=support_ticket, auto_responded=false

# Verify:
curl "http://localhost:3000/api/v1/account/conversations" | jq '.payload | length'
# Should be 1 (escalated)

curl "http://localhost:3000/api/v1/inboxes/1/conversations" | jq '.payload[0].priority'
# Should be "high"
```

**Pass/Fail:** ✅ Chatwoot ticket created, priority=high, no auto-reply

---

### Test 3: Email Triage — Volunteer Hours Intent

```bash
curl -X POST "http://localhost:5678/webhook/email-test" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "I logged 5 hours",
    "body": "I volunteered at our local food bank this weekend.",
    "from": "'$TEST_EMAIL'"
  }'

# Expected:
# 1. Auto-reply with log-hours link
# 2. NO Chatwoot ticket
# 3. Metric: intent=volunteer_hours, auto_responded=true

# Verify:
sleep 300  # Wait 5 min
curl "http://localhost:3000/api/v1/account/conversations" | jq '.payload | length'
# Should be 0
```

**Pass/Fail:** ✅ Auto-reply with link, no escalation

---

### Test 4: Email Triage — Unknown Intent (Escalation)

```bash
curl -X POST "http://localhost:5678/webhook/email-test" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Hi there",
    "body": "Just saying hello!",
    "from": "'$TEST_EMAIL'"
  }'

# Expected:
# 1. NO auto-reply
# 2. Chatwoot ticket created (escalate to human)
# 3. Metric: intent=unknown, auto_responded=false

# Verify:
curl "http://localhost:3000/api/v1/account/conversations" | jq '.payload | length'
# Should be ≥1
```

**Pass/Fail:** ✅ Chatwoot ticket created, no auto-reply

---

### Test 5: Voice IVR — Full Claim Flow

```bash
# From any phone, call your DID
# Follow prompts:
#   1. Press 1 (to claim)
#   2. Say EIN: "46 3120432"
#   3. Say email: "admin at example dot org"

# Expected:
# 1. IVR confirms: "Thank you! Check your email for verification link."
# 2. Chatwoot ticket created within 1 min
# 3. Ticket tagged: claim_type=voice, voice_verified=true
# 4. Metric logged

# Verify:
curl "http://localhost:3000/api/v1/inboxes/1/conversations" | \
  jq '.payload | map(select(.custom_attributes.claim_type=="voice")) | length'
# Should be 1
```

**Pass/Fail:** ✅ IVR responds, Chatwoot ticket created with claim_type=voice

---

### Test 6: Voice IVR — Invalid EIN (Escalation)

```bash
# From any phone, call your DID
#   1. Press 1
#   2. Say: "99 9999999" (fake EIN)

# Expected:
# 1. IVR says: "I couldn't find that EIN in our registry."
# 2. Chatwoot ticket created
# 3. Ticket tagged: ein_not_found=true

# Verify:
curl "http://localhost:3000/api/v1/inboxes/1/conversations" | \
  jq '.payload | map(select(.custom_attributes.ein_not_found==true)) | length'
# Should be 1
```

**Pass/Fail:** ✅ IVR rejects invalid EIN, ticket created

---

### Test 7: FAQ Bot — High Confidence Match

```bash
# Send email to FAQ bot webhook
curl -X POST "http://localhost:5678/webhook/faq-query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I donate to an organization?",
    "email": "'$TEST_EMAIL'",
    "subject": "Question"
  }'

# Expected:
# 1. Similarity score >0.7
# 2. Auto-reply with FAQ answer + source link
# 3. Metric logged: faq=true, confidence=0.8+

# Verify:
sleep 300
# Check email for FAQ response (should mention "donate directly")
```

**Pass/Fail:** ✅ Auto-reply with FAQ answer received

---

### Test 8: FAQ Bot — Low Confidence Escalation

```bash
curl -X POST "http://localhost:5678/webhook/faq-query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "I have a really weird edge case that is totally unique.",
    "email": "'$TEST_EMAIL'",
    "subject": "Weird question"
  }'

# Expected:
# 1. Similarity score <0.7
# 2. NO auto-reply
# 3. Chatwoot ticket created (faq_escalation source)
# 4. Metric logged: confidence=0.45

# Verify:
curl "http://localhost:3000/api/v1/inboxes/1/conversations" | \
  jq '.payload | map(select(.source_id=="faq_escalation")) | length'
# Should be ≥1
```

**Pass/Fail:** ✅ Low-confidence FAQ escalated to Chatwoot

---

### Test 9: Health Check Monitor — Detects Service Down

```bash
# Manually stop a service
docker-compose -f /opt/chatwoot/docker-compose.yml stop chatwoot

# Wait for health check (runs every 30 min, or manually trigger)
# Expected:
# 1. Alert email sent to Akbar
# 2. Subject: "🔴 DAANAA AUTOMATION ALERT — 1 Issue(s)"
# 3. Message includes: "Chatwoot: unhealthy"

# Verify:
sleep 30
curl "http://localhost:3000" 2>&1 | grep -q "refused\|Connection refused" && echo "✅ Chatwoot confirmed down"

# Restart to continue
docker-compose -f /opt/chatwoot/docker-compose.yml up -d
sleep 60
curl "http://localhost:3000" && echo "✅ Chatwoot back up"
```

**Pass/Fail:** ✅ Alert email received, service restoration detected

---

### Test 10: Backup Automation — Backup Created

```bash
# Run backup script
/home/akbar/meritgiving/scripts/backup_automation_stack.sh

# Verify:
ls -lh /data/automation_backups/*.sql.gz | tail -2
# Should show 2 recent files (chatwoot + n8n)

CHATWOOT_BACKUP=$(ls -t /data/automation_backups/chatwoot_*.sql.gz | head -1)
file "$CHATWOOT_BACKUP"
# Should show: gzip compressed data

# Verify integrity:
gunzip -t "$CHATWOOT_BACKUP" && echo "✅ Backup integrity OK"
```

**Pass/Fail:** ✅ Both backups created, gzip integrity verified

---

### Test 11: Metabase Dashboard — Metrics Visible

```bash
# Open Metabase
open "http://localhost:3000"

# Navigate to: Dashboards → Automation Stack KPI
# Verify all 10 cards display data:
#   ✅ Daily Email Volume (line chart, should show 4+ data points from tests)
#   ✅ Auto-Response Rate (gauge, should show ~75%+)
#   ✅ Intent Distribution (pie, should show donation + support + volunteer + unknown)
#   ✅ Chatwoot Backlog (should show trend)
#   ✅ Response Time (should show <24h)
#   ✅ Voice Claims (should show 2+ from tests)
#   ✅ Voice Success Rate (should show ≥50%)
#   ✅ Uptime (should show 99%+)
#   ✅ Latency (should show <500ms)
#   ✅ Weekly Summary (should show test data)
```

**Pass/Fail:** ✅ All 10 cards populated with test data

---

### Test 12: End-to-End Load Test

```bash
# Send 10 emails in rapid succession (2 min window)
for i in {1..10}; do
  curl -X POST "http://localhost:5678/webhook/email-test" \
    -H "Content-Type: application/json" \
    -d '{
      "subject": "Test email '$i'",
      "body": "How do I donate? I want to give!",
      "from": "'$TEST_EMAIL'"
    }'
  sleep 12  # 12 sec between sends
done

# Wait 5 min for processing
sleep 300

# Verify:
# 1. All 10 emails received auto-replies (check inbox)
# 2. Chatwoot backlog still <10
curl "http://localhost:3000/api/v1/account/conversations" | jq '.payload | length'
# Should be <10

# 3. n8n had no execution errors
docker logs -f n8n 2>&1 | grep -i "error" | wc -l
# Should be 0

# 4. Metabase shows 10 new email metrics
# (Metabase UI: Daily Email Volume card should show spike)
```

**Pass/Fail:** ✅ 10 emails auto-handled, no backlog growth, no errors

---

## Running All Tests

### Automated Test Runner

```bash
#!/bin/bash
# scripts/run_integration_tests.sh

set -e

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║         DAANAA AUTOMATION INTEGRATION TEST SUITE          ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

TEST_EMAIL="your-test@gmail.com"
PASSED=0
FAILED=0

# Test 1
echo "Test 1: Email Triage - Donation Intent"
if curl -X POST "http://localhost:5678/webhook/email-test" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "How do I give to Red Cross?",
    "body": "I want to donate.",
    "from": "'$TEST_EMAIL'"
  }' 2>/dev/null | grep -q "success"; then
  echo "✅ PASS"
  ((PASSED++))
else
  echo "❌ FAIL"
  ((FAILED++))
fi

# Test 2-11...
# (Follow same pattern for each test)

# Summary
echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                      TEST SUMMARY                         ║"
echo "║  Passed: $PASSED/12"
echo "║  Failed: $FAILED/12"
if [ $FAILED -eq 0 ]; then
  echo "║  Status: ✅ ALL TESTS PASSED"
else
  echo "║  Status: ❌ SOME TESTS FAILED"
fi
echo "╚═══════════════════════════════════════════════════════════╝"

exit $FAILED
```

### Manual Test Checklist

```
[ ] Test 1: Email donation intent
[ ] Test 2: Email support ticket
[ ] Test 3: Email volunteer hours
[ ] Test 4: Email unknown (escalation)
[ ] Test 5: Voice claim full flow
[ ] Test 6: Voice invalid EIN
[ ] Test 7: FAQ high confidence
[ ] Test 8: FAQ low confidence
[ ] Test 9: Health check alert
[ ] Test 10: Backup creation
[ ] Test 11: Metabase dashboard
[ ] Test 12: Load test (10 concurrent)

Total: _/12 passed
```

---

## Success Criteria

**All tests MUST pass before go-live announcement.**

| Test | Must Pass | Target |
|------|-----------|--------|
| Email intent detection (1-4) | Yes | 4/4 ✅ |
| Voice IVR (5-6) | Yes | 2/2 ✅ |
| FAQ bot (7-8) | Yes | 2/2 ✅ |
| Health checks (9) | Yes | 1/1 ✅ |
| Backup (10) | Yes | 1/1 ✅ |
| Metabase (11) | Yes | 1/1 ✅ |
| Load test (12) | Yes | 1/1 ✅ |
| **Total** | **Yes** | **12/12 ✅** |

If any test fails:
1. Note which test failed
2. Check logs: `docker logs -f [service]`
3. Fix root cause
4. Re-run that test
5. Repeat until all pass

---

## Regression Testing (Weekly Post-Launch)

After system is live, run simplified test suite weekly:

```bash
# Monday morning: 15 min regression check

# 1. Send 1 test email per intent (4 tests)
for intent in "donate" "broken" "volunteer" "hi"; do
  # Send email with keyword
done

# 2. Make 1 test call to IVR
# (Full claim flow)

# 3. Check Metabase for yesterday's metrics
# (All cards should have data)

# 4. Check backlog
curl "http://localhost:3000/api/v1/account/conversations" | jq '.payload | length'
# Should be <10

# Done
```

This catches regressions early before they impact real users.

