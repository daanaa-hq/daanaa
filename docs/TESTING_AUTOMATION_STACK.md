# Testing the Automation Stack (Days 1-4)

All components must pass integration testing before go-live announcement.

---

## Pre-Flight Checklist (Before Any Testing)

```bash
# Verify all services are running
docker-compose -f /opt/chatwoot/docker-compose.yml ps
docker-compose -f /opt/jambonz/docker-compose.yml ps
docker-compose -f /opt/n8n/docker-compose.yml ps

# Confirm database connectivity
docker-compose -f /opt/n8n/docker-compose.yml exec -T postgres psql -U n8n -d n8n -c "SELECT 1;" 
# Expected: (1 row)

docker-compose -f /opt/chatwoot/docker-compose.yml exec -T postgres psql -U postgres -d chatwoot_production -c "SELECT 1;"
# Expected: (1 row)
```

---

## Phase 1: Chatwoot Inbox (Day 1)

### 1.1 Web UI Access

```bash
# Access Chatwoot
open http://localhost:3000
# Log in with admin credentials set during setup
# Verify you can see the dashboard
```

**Expected:** Chatwoot dashboard loads, inbox shows 0 conversations.

### 1.2 Create Test Inbox

```bash
# Via Chatwoot UI:
# Settings → Inboxes → New Inbox
# Name: "Test Email"
# Channel: Email
# Email: test-daanaa@daanaa.org
# Save
```

**Expected:** Inbox created, IMAP credentials generated, email forwarding ready.

### 1.3 Send Manual Test Email

```bash
# From your personal email, send to: test-daanaa@daanaa.org
Subject: Test from manual send
Body: This is a test email to verify Chatwoot ingestion

# Check Chatwoot UI after 30 seconds
# Settings → Inboxes → [Email] → Conversations
```

**Expected:** Email appears in Chatwoot inbox as a new conversation.

---

## Phase 2: Email Triage (n8n) — Day 3

### 2.1 Test Email Intent Detection

Create a test email and send to `daanaa@daanaa.org`:

**Test Case 1: Donation Link Intent**
```
Subject: How do I give to Red Cross?
Body: I want to support the Red Cross. Can you help me donate?

Expected: Auto-reply sent, Chatwoot ticket NOT created, metric logged as intent=donation_link
```

**Test Case 2: Volunteer Hours Intent**
```
Subject: Logging volunteer hours
Body: I volunteered 5 hours at our local food bank. How do I log that?

Expected: Auto-reply sent with link to log-hours page, no ticket, metric logged as intent=volunteer_hours
```

**Test Case 3: Support Ticket Intent**
```
Subject: Your website is broken
Body: I can't search organizations. The directory page keeps timing out.

Expected: NO auto-reply, Chatwoot ticket created with priority=high, metric logged as intent=support_ticket
```

**Test Case 4: Unknown Intent**
```
Subject: Hi there
Body: Just saying hello to your team.

Expected: NO auto-reply, Chatwoot ticket created for manual review, metric logged as intent=unknown
```

### 2.2 Verify n8n Logs

```bash
# Check n8n execution logs
docker-compose -f /opt/n8n/docker-compose.yml logs -f n8n 2>&1 | grep -i "intent\|email"

# Expected output pattern:
# Intent Detector: detected intent=donation_link
# Send Donation Link Response: email sent to sender
# Log Metric: logged to metabase
```

### 2.3 Verify Auto-Responses Arrive

```bash
# Send test email to daanaa@daanaa.org (Test Case 1)
# Wait 2-5 minutes
# Check your inbox for auto-reply with subject "Re: How do I give to Red Cross?"

# Expected reply:
# "Hi there, Thanks for reaching out to Daanaa. To make a donation directly 
#  to the organization, visit: [donate_url]. You can also browse similar 
#  organizations on our directory."
```

**Expected:** Auto-reply email arrives within 5 minutes, comes from daanaa@daanaa.org with proper threading.

---

## Phase 3: Jambonz Voice IVR — Day 2

### 3.1 Test Call Routing

```bash
# Call the DID: +1-833-DAANAA-2 (from any phone)
# If using Voxbeam test extension, dial the SIP URI:
# sip:+1833...@your-sip-endpoint.com

# Expected flow:
# 1. Ring 2-3 times
# 2. Hear: "Welcome to Daanaa. Press 1 to claim your nonprofit page."
# 3. Press 1
# 4. Hear: "Please say your organization's EIN..."
```

**Expected:** Call connects, greeting plays, IVR awaits input.

### 3.2 Test EIN Collection

```bash
# While in IVR after greeting:
# 1. Press 1
# 2. When prompted, say: "46 3120432" (example EIN)
# 3. Wait for response
```

**Expected Responses by EIN Status:**
- **EIN found:** "Thank you! We found [ORG NAME]. Now please provide your organization's domain email..."
- **EIN not found:** "I couldn't find that EIN in our registry. Please email support@daanaa.org."

### 3.3 Test Email Collection & Verification

```bash
# In IVR, after EIN is verified:
# Say: "my email is admin at example dot org"
# (assuming example.org is the org's registered domain)

# Expected: "Perfect! Check your email for a claim verification link. Goodbye."
```

**Check Chatwoot for new ticket:**
```bash
# Open Chatwoot UI
# Inboxes → [Voice Claims] → Conversations
# Should see new ticket with EIN, email, phone, and transcript attached
```

**Expected:** Chatwoot ticket created with `claim_type=voice, voice_verified=true`.

### 3.4 Test Failed Email Domain Match

```bash
# In IVR, after EIN is verified (example: Red Cross, domain redcross.org):
# Say: "my email is admin at unrelated dot com"

# Expected: "That email doesn't match your organization's domain. Please try again..."
# Chatwoot ticket created with priority=high, email_mismatch=true
```

---

## Phase 4: End-to-End Integration (Day 4)

### 4.1 Complete Claim Flow via Voice

```
Scenario: A real nonprofit wants to claim their page via phone.

Steps:
1. Call +1-833-DAANAA-2
2. Press 1
3. Say their actual EIN (from registry)
4. Say their domain email (e.g., director@nonprofit.org)
5. Hang up

Verification Checklist:
☐ Call connects without error
☐ IVR guides through all steps
☐ Chatwoot ticket created within 30 seconds
☐ Ticket shows voice_verified=true if email matched
☐ Metric logged to Metabase
☐ No internal errors in Jambonz logs
```

### 4.2 Complete Email + Auto-Response Flow

```
Scenario: A donor emails multiple questions, system handles 3 types:

Step 1: Donation link question
  From: donor@example.com
  Subject: I want to support the Salvation Army
  
  Expected: Auto-reply within 5 min, no Chatwoot ticket
  Verification:
  ☐ Auto-reply received with donate link
  ☐ Chatwoot inbox empty (no escalation)
  ☐ Metabase shows intent=donation_link, auto_responded=true

Step 2: Volunteer logging
  From: volunteer@example.com
  Subject: I logged 8 hours
  
  Expected: Auto-reply with log-hours link, no ticket
  Verification:
  ☐ Auto-reply received within 5 min
  ☐ Chatwoot inbox empty

Step 3: Website bug report
  From: user@example.com
  Subject: Directory search is broken
  
  Expected: No auto-reply, Chatwoot ticket created, high priority
  Verification:
  ☐ NO auto-reply sent
  ☐ Chatwoot shows new ticket with subject "Website: Directory search is broken"
  ☐ Metric shows intent=support_ticket, auto_responded=false
```

### 4.3 Backlog Monitoring

```bash
# Simulate Akbar's Monday morning check-in

# Step 1: Open Chatwoot dashboard
open http://localhost:3000

# Step 2: Count unresolved tickets
# Dashboard → Conversations (should show count)
# Expected: <5 unresolved (most auto-handled)

# Step 3: Check Metabase metrics
open http://localhost:3000  # Metabase (different port if deployed)
# Navigate to "Email Triage Dashboard"
# Expected metrics visible:
#  - Emails received: N
#  - Auto-response rate: >75%
#  - Escalation count: <30%
#  - Avg response time (for escalated): <24h
```

---

## Failure Testing

### Test: Email Intent Detection Misses a Real Support Ticket

```bash
# Send ambiguous email that should have been escalated but wasn't
Subject: Question
Body: Not sure about something.

# Expected behavior: Intent detector should classify as "unknown", create Chatwoot ticket
# Verify: Chatwoot has new ticket in escalated state
```

**Failure Mode:** Intent marked as "feedback" instead of "support_ticket"
- **Root cause:** Keyword matching too loose
- **Fix:** Tighten regex in n8n Intent Detector node
- **Prevention:** Review weekly escalation failures; update patterns

### Test: Jambonz Call Drops Mid-Collection

```bash
# Call +1-833-DAANAA-2
# Press 1, say EIN
# Hang up before email step

# Expected: Chatwoot ticket created with partial data
# Email: support@daanaa.org
# Content: "Incomplete claim flow: EIN provided but email not collected"
```

**Failure Mode:** No ticket created, call silently ends
- **Root cause:** Jambonz webhook timeout or network error
- **Fix:** Add fallback hangup handler with callback to n8n
- **Prevention:** Monitor Jambonz error logs daily

---

## Load Testing (Optional, Pre-Launch)

### Simulate Peak Email Load

```bash
# Send 20 emails in rapid succession (2 min window)
for i in {1..20}; do
  curl -X POST https://daanaa.org/api/test-email \
    -H "Content-Type: application/json" \
    -d '{
      "to": "daanaa@daanaa.org",
      "subject": "Test email '$i'",
      "body": "This is test email number '$i'"
    }'
  sleep 6  # 6 sec delay between sends
done

# Monitor:
# - Chatwoot: count new conversations (should be ≈6, rest auto-handled)
# - n8n: execution queue (should process all within 10 min)
# - Jambonz: SIP trunk: logs (no connection drops)
```

**Expected Results:**
- All 20 emails processed within 10 minutes
- No timeouts or dropped connections
- n8n queue clears with no stuck jobs
- Chatwoot shows ≥15 auto-responses, <5 escalations

---

## Regression Testing (Weekly)

After any code change, verify:

```bash
# 1. Email triage still works
# Send one test email per intent type (4 tests)
# Verify auto-responses and escalations are correct

# 2. Voice IVR still works
# Call and complete one full claim flow (5 min)
# Verify Chatwoot ticket created with correct data

# 3. Metrics still logging
# Check Metabase dashboard for today's data (should have >0 entries)

# 4. No new errors in logs
docker-compose logs --tail 50 | grep -i error
# Expected: 0 new errors related to automation components
```

---

## Troubleshooting Reference

| Symptom | Likely Cause | Test Fix |
|---------|---|---|
| Auto-replies not arriving | n8n Gmail node auth expired | Re-authenticate Gmail in n8n credentials |
| Chatwoot tickets appearing but empty | n8n HTTP request malformed body | Check payload format in n8n HTTP node |
| IVR not answering calls | Jambonz container crashed | `docker-compose restart jambonz` |
| Intent detection too aggressive | Keyword regex too broad | Add negative lookahead patterns |
| Email takes >5 min to trigger | n8n Gmail polling too slow | Reduce pollTimes.item[0].mode to "everyMinute" |
| Metabase logging failing silently | Metabase API auth issue | Verify genericCredentials=metabase_api in n8n |

---

## Sign-Off

Once all phases pass:

```markdown
**Testing Completed:** [DATE]
**Tester:** [NAME / Akbar]
**All Tests Passed:** ☐ Yes / ☐ No

Issues Found: [List any bugs discovered]
Fixes Applied: [List fixes]

**Ready for Go-Live:** ☐ Yes / ☐ No
```

If all tests pass, announce the phone number (`+1-833-DAANAA-2`) publicly.
