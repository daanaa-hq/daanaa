# Weekly Operations Playbook

Exactly what Akbar does each week to keep the automation stack healthy, tuned, and improving.

---

## The Rhythm

- **Daily (5 min):** Health check
- **Weekly (1.5 hrs):** Deep dive + tuning decisions
- **Monthly (2 hrs):** Comprehensive review + strategy adjustment

This page focuses on **weekly** operations (Monday AM, typically 9-10:30 AM).

---

## Weekly Operations: Monday 9 AM — 10:30 AM

### Part 1: Dashboard Review (15 minutes)

**Open:** Metabase → Automation Stack KPI Dashboard

**Scan these 10 cards for red flags:**

| Card | Target | Red Flag | Action |
|------|--------|----------|--------|
| Email Volume | 5-50/day | 0 emails OR >100 | Check: Gmail auth expired? OR spam wave incoming? |
| Auto-Response Rate | >75% | <60% | Review "unknown" escalations; add new intent patterns |
| Intent Distribution | Balanced | 90% support? | Keyword patterns changing; update rules |
| Backlog Trend | <10 unresolved | >15 | Escalation rate up; prioritize oldest tickets |
| Response Time | <24h avg | >48h | Too many unhandled escalations; set email SLA |
| Voice Claims | 1-5/week | 0 OR >20 | Phone number working? OR word-of-mouth explosion? |
| Voice Success | >80% | <60% | Email validation failing? Listen to call recordings |
| Uptime | >99% | <98% | Service crashed? Check logs; add to incident playbook |
| Latency | <500ms | >1000ms | System overloaded? Check: database size, n8n queue |
| Weekly Summary | Trending up | Trending down | Overall health degrading; investigate |

**Document findings in a note:**

```
Monday 2026-06-20 Weekly Review:
- Auto-response rate: 78% (target >75%) ✅
- Backlog: 4 unresolved (target <10) ✅
- Response time: 8h avg (target <24h) ✅
- Voice claims: 3 this week (NEW: 1 EIN validation failed)
- Issues: None critical. One email had low FAQ confidence.

Action items for this week:
1. Review the failed voice claim transcript (email mismatch)
2. Add new FAQ: "What if my domain email changed?"
3. Monitor backlog—trending up slowly
```

**Time allocation:** 15 min reading + thinking

---

### Part 2: Chatwoot Ticket Triage (30 minutes)

**Goal:** Resolve or close stale escalations; identify patterns for automation

**Open:** Chatwoot → Inbox → Conversations (filter: status=open, oldest first)

**For each unresolved ticket:**

1. **Read it** (1 min)
2. **Categorize** (mental note):
   - Automated correctly? (ticket should not exist)
   - Simple answer available? (reply in 1 min)
   - Complex question? (needs investigation)
   - Duplicate? (already answered elsewhere)
   - Invalid/spam? (close without reply)

3. **Act**:
   - **If simple:** Reply now, mark resolved
   - **If complex:** Plan to handle Thursday, add to backlog note
   - **If automated wrong:** Screenshot for tuning (add intent pattern)
   - **If duplicate:** Link to previous conversation, mark resolved
   - **If spam:** Close, no reply

**Example flow:**

```
Ticket: "How do I donate to Doctors Without Borders?"
Analysis: Should have been auto-responded (donation_link intent)
Action: Reply with donate link; mark resolved
Note: "Intent detector missed this. Check why."
```

```
Ticket: "I want to start a nonprofit. Help?"
Analysis: Out of scope (Daanaa is org discovery, not startup advice)
Action: Reply: "Daanaa helps you discover existing nonprofits. 
         For startup help, contact IDEALIST.org or your state AG office."
         Mark resolved.
```

```
Ticket: "Why does my org show as 'needs support'?"
Analysis: FAQ question (should route to FAQ bot after integration)
Action: Reply with explanation; screenshot + add note "Add FAQ: 
         'What does "needs support" mean?'"
Mark resolved.
```

**By end:** Most tickets resolved, problematic ones noted

**Time allocation:** 30 min (4-5 tickets per week average)

---

### Part 3: Pattern Tuning (30 minutes)

**Goal:** Identify where automation failed, improve rules

**Data sources:**
1. **Screenshot list from Part 2** — Tickets that should have been auto-handled
2. **Metabase "Unknown Intent" card** — What % of emails are unclassified?
3. **FAQ escalations** — Low-confidence matches
4. **Voice escalations** — Email validation failures

**For each pattern, decide:**

| Pattern | Decision | Action | Test |
|---------|----------|--------|------|
| Email says "donate" but not auto-replied | Update Intent Detector | Add keyword "give", "contribution" | Send 3 test emails |
| FAQ query not recognized | Update FAQ rules | Lower confidence threshold 0.7 → 0.65 | Send 3 test FAQs |
| Voice email validation too strict | Update regex | Allow subdomains | Call + test |
| Support ticket not escalated | Update rules | Add keyword "broken", "urgent" | Send 3 tests |

**Example tuning session:**

```
FINDING: 2 emails this week had "support" keyword but were classified as "feedback"
ROOT CAUSE: Intent detection checks for "broken" but these said "not working"
DECISION: Add "not working" to support_ticket keywords
CODE: In n8n Intent Detector, line 25:
  Before: if (text.includes('broken') || text.includes('issue'))
  After:  if (text.includes('broken') || text.includes('issue') || text.includes('not working'))
TESTING: Send 3 test emails with "not working"
        Verify all get auto-escalated to Chatwoot
        Done ✅
```

**Time allocation:** 30 min (4-5 quick decisions, update code, test)

---

### Part 4: Decision Log (15 minutes)

**Update two files:**

#### 1. docs/LESSONS.md

Add a new entry:

```markdown
## Week of 2026-06-20

**Issue:** Email intent detector missing "not working" language
**Root Cause:** Keyword matching only checked "broken", not synonyms
**Fix:** Added "not working" to support_ticket pattern
**Prevention Rule:** When tuning, always test synonyms (broken/issue/not working/fails/error)
**Impact:** Reduced false-negative support tickets by ~20%

**Issue:** Voice claim email validation too strict for subdomains
**Root Cause:** Regex didn't account for org.*.com domains (e.g., giving.redcross.org)
**Fix:** Updated email domain matcher to allow subdomains
**Prevention Rule:** Always ask: "Could this org use a subdomain?"
**Impact:** Reduced voice escalations due to email mismatch

**Learnings:**
- Keyword patterns need regular review (language changes over time)
- Edge cases (subdomains, new syntax) emerge after real traffic
- Weekly tuning prevents small issues from becoming big ones
```

#### 2. docs/DECISIONS.md

Add any non-obvious implementation choices:

```markdown
## 2026-06-20: Email Intent Thresholds

**Decision:** Set auto-response confidence threshold at 0.95 for donation/volunteer, 
0.80 for support_ticket (stricter for negative cases)

**Rationale:** False-positive support ticket (sending wrong auto-reply to angry user) 
is worse than false-negative (escalates to human review). So we're stricter on 
positive actions, looser on escalations.

**Alternative Rejected:** Equal threshold (0.85) across all intents. Risk: angry 
customers get wrong auto-reply, lose trust.

**Monitoring:** Weekly check Chatwoot escalations; if >10% are "I already got an auto-reply", 
lower threshold.
```

**Time allocation:** 15 min writing (not code, just notes)

---

## Daily Operations: Morning Check-In (5 minutes)

**Every morning, run:**

```bash
/home/akbar/meritgiving/scripts/health_check.sh
```

**Expected output:**

```
✅ Chatwoot: healthy
✅ n8n: healthy
✅ Jambonz: healthy
✅ API: healthy
✅ Unresolved: 3 (<10)
✅ Disk: 45% used (<80%)
```

**If any ❌:**
- Stop what you're doing
- Check logs: `docker logs -f [service]`
- Restart if needed: `docker-compose restart`
- If doesn't recover in 5 min, page emergency contact or file incident

---

## Monthly Deep Dive: 1st of Month (2 hours)

**Set aside time (typically Monday 2-4 PM):**

### Review System Health

```bash
# 1. Check database size
docker exec chatwoot_postgres_1 psql -U postgres -d chatwoot_production -c \
  "SELECT pg_size_pretty(pg_database_size(current_database()));"
# Should be <2GB. If >5GB, archiving needed.

# 2. Review error logs (last 30 days)
docker logs --since 30d n8n 2>&1 | grep -i error | wc -l
docker logs --since 30d jambonz 2>&1 | grep -i error | wc -l
# Should each be <10. If >50, underlying problem.

# 3. Check backup status
ls -lh /data/automation_backups/*.sql.gz | wc -l
# Should be ~30 (30 days of backups)
```

### Review Metrics Trends

**Metabase → Export last 30 days as CSV:**

```
Week 1: Auto-response: 74%, Backlog: 6, Response time: 12h
Week 2: Auto-response: 76%, Backlog: 8, Response time: 14h
Week 3: Auto-response: 79%, Backlog: 5, Response time: 11h
Week 4: Auto-response: 78%, Backlog: 7, Response time: 13h

30-day avg: 77% auto-response, 6.5 backlog, 12.5h response
Trend: Slightly up (good), stable, slightly up (slightly worse, but <24h target)
```

**Decision:** Are metrics trending in right direction? If not, why?

### Review Escalation Patterns

**Chatwoot → Filter → escalated tickets (last 30 days):**

```
Total escalated: 45
By type:
  - Email: 30 (67%)
  - Voice: 10 (22%)
  - FAQ: 5 (11%)

By reason:
  - "unknown" intent: 15 (33%)
  - FAQ low confidence: 5 (11%)
  - Voice email mismatch: 8 (18%)
  - Complex questions: 17 (38%)

Pattern: "Unknown" intent cluster. Action: Add FAQ + intent patterns
```

### Capacity Planning

**Question:** Is Akbar getting buried?

```
Hours spent on support last month:
  - Daily check-ins: 5 min × 20 days = 1.5h
  - Weekly deep dives: 1.5h × 4 = 6h
  - Ad-hoc tuning: ~5h
  - Total: ~12.5h (target: <12h/month, i.e., <3h/week)

Trending: Stable. No need to hire yet.

If spending >20h/month: consider hiring 16h/week support contractor ($20-30K/yr)
```

### Roadmap for Next Month

**What to focus on:**

```
Priority 1: Lower "unknown" intent rate
  - Add 5 new intent patterns (from escalations)
  - Test with sample emails

Priority 2: Improve voice success rate (currently 75%, target 85%)
  - Listen to 5 failed claim calls
  - Identify speech recognition issues
  - Adjust Jambonz script for clarity

Priority 3: Scale FAQ bot if helpful
  - Currently 11% of escalations are FAQ low-confidence
  - Add 10 new FAQs (harvest from "unknown" escalations)
  - Retrain FAQ embeddings

Action items:
  [ ] Add 5 intent patterns (est. 1h)
  [ ] Listen to 5 voice calls (est. 30m)
  [ ] Add 10 FAQs (est. 2h)
  [ ] Compute FAQ embeddings (est. 20m)
  [ ] Test all changes (est. 1h)
  Total: ~5h for month (spread across Mondays)
```

---

## Exceptional Cases

### Case 1: Backlog Spike (>15 unresolved)

**When:** Suddenly have 20+ unresolved tickets  
**Why:** Email volume spike, or auto-response rate dropped  
**Action (immediate):**

```bash
# 1. Check what happened
docker logs --tail 100 n8n 2>&1 | grep -i error
# Is n8n crashing? Intent detection broken?

# 2. If n8n is crashing, restart
docker-compose -f /opt/n8n/docker-compose.yml restart

# 3. Set auto-reply on daanaa@daanaa.org
echo "Thanks for reaching out! We're handling a high volume right now. 
Expected response: 48-72h." > /tmp/auto_reply.txt
# (Manual: Set auto-reply in Gmail UI)

# 4. Prioritize: work through backlog by oldest first
curl "http://localhost:3000/api/v1/account/conversations?sort=-created_at&limit=20" | jq
# Close non-critical ones with canned response: "Thanks! Will follow up next week."

# 5. Email Akbar's team/partner: "Temporarily backlogged. No data loss. ETA 48h to normal."
```

**Time to stabilize:** 15-30 min  
**Post-mortem:** What caused spike? Add to LESSONS.md

### Case 2: Service Down (Chatwoot/n8n/Jambonz Unresponsive)

**When:** Health check shows ❌  
**Action (immediate):**

```bash
# 1. Restart the service
docker-compose -f /opt/[chatwoot|n8n|jambonz]/docker-compose.yml restart

# 2. Wait 60 seconds, verify
curl http://localhost:[3000|5678|3000]/health

# 3. If still down, check logs
docker logs -f [service] --tail 50

# 4. If database corruption, restore from backup
# (See MONITORING_ALERTING.md → Recovery procedures)

# 5. Email incident report to stakeholders (if down >30 min)
```

**Target recovery time:** <15 min  
**Post-incident:** Add root cause to LESSONS.md, update MONITORING_ALERTING.md

### Case 3: Email Flooding (Spam or Legitimate Volume Surge)

**When:** >100 emails in 1 hour  
**Action:**

```bash
# 1. Check if real traffic or spam
curl "http://localhost:5000/api/metrics?hours=1" | jq '.emails_received'

# 2. If spam, Gmail auto-filters. Can also:
#    - Blacklist domain in n8n Intent Detector
#    - Add filter rule to Gmail UI

# 3. If legitimate surge (e.g., press coverage):
#    - System auto-handles 75-90%, so backlog grows linearly
#    - Monitor but don't panic
#    - If backlog >50, enable auto-reply for 48h
```

**Example:** Daanaa gets featured in Forbes → 500 emails in 24h  
**Impact:** Auto-response handles 375-450, 50-125 escalate to Chatwoot  
**Action:** Set auto-reply, batch process next day

---

## Tools & Commands Reference

### Chatwoot

```bash
# Get backlog count
curl "http://localhost:3000/api/v1/account/conversations" | jq '.payload | length'

# Get oldest unresolved
curl "http://localhost:3000/api/v1/account/conversations?sort=-created_at" | jq '.payload[0]'

# Create support ticket (manual)
curl -X POST "http://localhost:3000/api/v1/inboxes/1/messages" \
  -H "Authorization: Bearer $CHATWOOT_TOKEN" \
  -d '{"email": "test@example.com", "content": "Test ticket"}'
```

### n8n

```bash
# Check active workflows
curl "http://localhost:5678/api/v1/workflows?active=true" | jq '.data | length'

# Trigger workflow manually
curl -X POST "http://localhost:5678/api/v1/workflows/[ID]/execute"

# View execution logs (last 10)
docker logs -f n8n --tail 10
```

### Metabase

```bash
# Query custom metric
curl "http://localhost:3000/api/card/1" | jq '.data'

# Generate export (CSV)
# (Via web UI: Dashboard → Export as CSV)
```

### Monitoring

```bash
# Health check
/home/akbar/meritgiving/scripts/health_check.sh

# Full system status
docker ps
df -h /data
du -sh /data/*
```

---

## Weekly Checklist Template

```markdown
## Week of [DATE]

### Monday Morning (9 AM)

[ ] Run health_check.sh
    Status: [output]

[ ] Review Metabase dashboard (15 min)
    - Auto-response rate: __% (target >75%)
    - Backlog: __ (target <10)
    - Response time: __h (target <24h)
    - Issues: [list or "None"]

[ ] Triage Chatwoot escalations (30 min)
    - Tickets reviewed: __
    - Resolved: __
    - Patterns identified: [list]

[ ] Tuning decisions (30 min)
    - Changes made: [list]
    - Tests run: [list]
    - All tests passed: Y/N

[ ] Update LESSONS.md
    - Entry added: Y/N
    - URL: [link to commit]

### Summary

Automation health: [Good / Fair / Needs Attention]
Akbar time spent: __h (target <3h/week)
Trend: [Improving / Stable / Degrading]
Next week priorities: [list]
```

---

## Success = Invisible

When everything is working:
- Akbar spends <3h/week on support
- Email auto-response rate >75%
- Voice claims working
- Chatwoot backlog <10
- No pages/alerts
- Metrics trending up

That's when you know the stack is doing its job.
