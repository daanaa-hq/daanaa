# Go-Live Checklist: Automation Stack

**Launch Date:** [Set by user]
**Owner:** Akbar  
**Status:** [In Progress / Ready for Launch / LIVE]

---

## Pre-Launch (48 Hours Before)

### Day Before: Final Testing & Staging

- [ ] Run full test suite from `TESTING_AUTOMATION_STACK.md`
  - [ ] All 4 email intent types respond correctly
  - [ ] Voice IVR answers and collects data
  - [ ] Chatwoot creates tickets on escalation
  - [ ] Metabase shows metrics from test runs

- [ ] Verify all service health
  ```bash
  docker-compose ps | grep -E "chatwoot|jambonz|n8n|postgres"
  # All should show "Up"
  ```

- [ ] Check database backups
  ```bash
  ls -lh /data/chatwoot_backups/ | tail -5
  ls -lh /data/n8n_backups/ | tail -5
  # Most recent backups <24h old
  ```

- [ ] Load test with 20 concurrent emails
  ```bash
  # See TESTING_AUTOMATION_STACK.md → Load Testing
  # Expected: all processed within 10 min, <5 escalations
  ```

- [ ] Verify Voxbeam DID balance
  ```bash
  # Log into https://www.voxbeam.com → Account → Credits
  # Expected: >$10 remaining (covers ~500 calls)
  ```

### Day Of: Final Checks (2 Hours Before Announcement)

- [ ] Spin up everything fresh
  ```bash
  # Restart all services to catch startup issues
  cd /opt/chatwoot && docker-compose restart
  cd /opt/jambonz && docker-compose restart
  cd /opt/n8n && docker-compose restart
  # Wait 60 seconds for containers to settle
  ```

- [ ] Make one test call + one test email
  - [ ] Call +1-833-DAANAA-2, press 1, say an EIN
  - [ ] Send an email to daanaa@daanaa.org with donation intent
  - [ ] Verify both show up in Chatwoot within 5 min

- [ ] Check all service ports are responding
  ```bash
  curl -s http://localhost:3000/health | grep -q status && echo "Chatwoot: OK" || echo "FAIL"
  curl -s http://localhost:5678 | grep -q n8n && echo "n8n: OK" || echo "FAIL"
  curl -s http://localhost:3000/admin | head -1 && echo "Jambonz: OK" || echo "FAIL"
  ```

- [ ] Review Chatwoot configuration one more time
  - [ ] Email inbox correctly forwarding to Chatwoot
  - [ ] Chatwoot API token stored in n8n credentials
  - [ ] Response templates are in place (optional but nice)

- [ ] Confirm no errors in logs (last 100 lines)
  ```bash
  docker-compose logs --tail 100 | grep -i error
  # Expected: 0 errors
  ```

---

## Go-Live Moment

### Announcement (Internal + Public)

Send to:
- **Internal:** Akbar + any team members
- **Public:** daanaa.org homepage, email to contacts, social media (if applicable)

**Announcement Text:**

```
🎉 Daanaa Now Offers Voice Support

Nonprofits can now call +1-833-DAANAA-2 to claim and verify their 
organization page in under 5 minutes. No emails, no waiting.

📞 Press 1 to claim your nonprofit page
✅ Say your EIN (e.g., "46 3120432")
✅ Say your domain email (e.g., "admin@nonprofit.org")
✅ Get your claim verification link

All support requests are automatically triaged and responded to within 
24 hours. Email support@daanaa.org if you have questions.

Learn more: daanaa.org/support
```

### Monitor First 2 Hours

- [ ] Watch Chatwoot dashboard in real-time
  ```bash
  # SSH into home server
  ssh root@192.168.1.73
  
  # Tail Chatwoot logs
  docker logs -f chatwoot_chatwoot_1 2>&1 | grep -i "email\|claim\|error"
  ```

- [ ] Track incoming calls/emails
  ```bash
  # Every 15 minutes, check counts
  curl http://localhost:3000/api/v1/account/conversations | jq '.payload[0].count'
  # Should show growth: 0 → 2 → 5 → 8, etc.
  ```

- [ ] Monitor system resources
  ```bash
  # Check CPU/memory on home server
  htop
  # Expected: <60% CPU, <70% RAM
  ```

- [ ] Watch for error spikes
  ```bash
  # Check for new errors in logs
  docker-compose logs --since 30m | grep -i error | wc -l
  # If >5 new errors, investigate immediately
  ```

---

## First Week: Daily Monitoring

### Daily Standup (Morning, 15 min)

```bash
# 1. Check Chatwoot backlog
curl http://localhost:3000/api/v1/account/conversations \
  -H "Authorization: Bearer $CHATWOOT_API_TOKEN" | jq '.payload | length'
# Target: <10 unresolved tickets

# 2. Check email auto-response success rate
# Via Metabase dashboard
curl http://localhost:3000/api/card/1  # (adjust card ID)
# Target: >75% auto-response rate

# 3. Check IVR call completion rate
# Via Chatwoot voice claim tickets
curl http://localhost:3000/api/v1/inboxes/1/conversations \
  -H "Authorization: Bearer $CHATWOOT_API_TOKEN" \
  -d 'source_id=voice_claim' | jq '.payload | length'
# Target: 1-5 calls/day (early), trending up

# 4. Check error logs
docker-compose logs --since 24h | grep -i error | head -10
# Target: 0 errors (or known, non-critical only)
```

### Weekly Review (Monday AM)

**Owner:** Akbar  
**Duration:** 30 minutes

1. **Metabase Review** (10 min)
   - [ ] Pull weekly metrics dashboard
   - [ ] Email volume: [#]
   - [ ] Auto-response rate: [%]
   - [ ] Escalation rate: [%]
   - [ ] Avg response time (escalated): [hours]
   - [ ] Voice claims attempted: [#]
   - [ ] Voice claims successful: [%]

2. **Chatwoot Backlog Review** (10 min)
   - [ ] Oldest unresolved ticket age: [hours]
   - [ ] Critical/high-priority tickets: [#]
   - [ ] Response SLA breaches: [#]
   - [ ] Any patterns in escalations?

3. **Tuning Loop** (10 min)
   - [ ] Any new intent patterns to add? (yes/no)
   - [ ] Any IVR failures? (yes/no + details)
   - [ ] Any FAQ gaps? (yes/no + details)
   - [ ] Update intent rules if needed (n8n Intent Detector node)
   - [ ] Document learnings in `docs/LESSONS.md`

### Escalation Triggers

If any of these conditions occur, **Akbar is alerted immediately:**

- **Email backlog >10 unresolved** → Set auto-reply: "Thanks for reaching out. We're processing a high volume right now. Expect a response within 24-48h."
- **Voice call failures >20%** → Investigate Jambonz logs + SIP trunk health
- **Auto-response rate drops below 60%** → Update intent detection rules
- **Chatwoot down >30 min** → Check Docker, restart if needed
- **n8n workflow errors >5 in 1h** → Check credentials, webhook endpoints, database connections

---

## First Month: System Stabilization

### Week 2-4 Review

Update `CUSTOMER_SERVICE_STRATEGY.md` with:
- [ ] Actual email volume vs. forecast
- [ ] Actual voice claim volume vs. forecast
- [ ] Auto-response accuracy (% of correct classifications)
- [ ] Average Akbar response time on escalations
- [ ] Any new insights on nonprofit needs (via tickets)

### Tuning Decisions

**If auto-response rate is high (>80%):**
- Akbar spending <1 hr/day on support ✅
- Stack is working as designed
- Continue monitoring; no changes needed

**If auto-response rate is low (<60%):**
- Need to add more intent patterns
- Potential gaps in FAQ coverage
- Actions: review failed escalations, update n8n rules

**If call completion rate is low (<40%):**
- IVR script clarity issue or SIP trunk problem
- Actions: listen to sample recordings, adjust Jambonz script

---

## Disaster Recovery

### If Chatwoot Goes Down

```bash
# 1. Restart immediately
cd /opt/chatwoot
docker-compose restart

# 2. Wait 60 seconds for startup
sleep 60

# 3. Verify it's back
curl http://localhost:3000/health

# 4. If still down, check logs
docker-compose logs --tail 50

# 5. If database issue, restore from backup
# (See ROLLBACK.md section below)
```

**Impact:** Incoming emails/calls will queue in n8n/Jambonz; they will auto-process once Chatwoot is back up.  
**Max acceptable downtime:** 4 hours (after that, calls start failing)

### If n8n Goes Down

```bash
# 1. Restart immediately
cd /opt/n8n
docker-compose restart

# 2. Wait 60 seconds
sleep 60

# 3. Check n8n web UI
curl http://localhost:5678

# 4. Verify all workflows are still enabled
# (They should resume automatically)
```

**Impact:** Emails queued in Gmail will not be processed until n8n restarts. Voice calls will fail to create Chatwoot tickets.  
**Max acceptable downtime:** 2 hours

### If Jambonz Goes Down

```bash
# 1. Restart immediately
cd /opt/jambonz
docker-compose restart

# 2. Verify SIP port is listening
netstat -tlnp | grep 5060

# 3. Test with a call
# (Dial +1-833-DAANAA-2, should ring)
```

**Impact:** Incoming calls will fail with "no answer."  
**Max acceptable downtime:** 30 minutes (callers will try again or email)

---

## Rollback Plan

### If Automation Stack is Causing Harm

**Decision:** Should we disable the automation and go back to manual-only mode?

**Conditions that might warrant rollback:**
1. Email intent detection is **destroying** trust (sending dangerous wrong responses)
2. Voice IVR is **breaking** regulatory compliance (e.g., inadvertent data exposure)
3. System is **non-recoverable** after >4 hours of work

**Rollback procedure:**

```bash
# Step 1: Disable all auto-responses (immediate, <5 min)
cd /opt/n8n
docker-compose down  # Kill n8n; emails won't auto-respond

# Step 2: Redirect email manually to Chatwoot
# In daanaa@daanaa.org settings, disable n8n filters
# Let all emails flow to Chatwoot only (manual mode)

# Step 3: Disable voice IVR (immediate)
cd /opt/jambonz
docker-compose down  # Kill Jambonz; calls fail → voicemail → email

# Step 4: Notify users
# Email: "Our automated support system is temporarily offline. 
#         Please email support@daanaa.org with your request."

# Step 5: Investigate root cause
# Review logs, identify the problem, patch, test in staging first

# Step 6: Re-enable incrementally
# Bring up one service at a time
# Start with email triage (low-risk)
# Then voice (higher risk)
```

**Expected outcome:** Back to manual-only mode within 15 minutes. All functionality preserved; just slower.

---

## Sign-Off

**Ready for Launch?**

```markdown
Pre-Launch Checklist:     ☐ Complete
Testing Results:         ☐ All Pass
Service Health:          ☐ All Green
Load Test:               ☐ Passed
Staff Training:          ☐ Complete (Akbar reviewed all docs)

Launch Approved By:      _________________________ (Akbar)
Launch Date/Time:        _________________________
Tester Name:             _________________________

Comments:
[Any last-minute notes or known issues]
```

Once signed off, announce the DID publicly:

> **Call +1-833-DAANAA-2 to claim your nonprofit page and get voice support.**

---

## References

- `CUSTOMER_SERVICE_STRATEGY.md` — Overall architecture & goals
- `DEPLOY_CHATWOOT.md` — Helpdesk setup
- `DEPLOY_JAMBONZ_IVR.md` — Voice IVR setup
- `DEPLOY_N8N_EMAIL_TRIAGE.md` — Email automation setup
- `TESTING_AUTOMATION_STACK.md` — Complete test procedures
- `docs/LESSONS.md` — Ongoing learnings & improvements
