# Daanaa Customer Service Strategy: Automated, Zero-Staff

**Goal:** Self-hosted, privacy-first, **fully automated** customer service across 4 stakeholder groups. Humans handle exceptions only; AI + workflows handle routine flows.

**Status:** Architecture ready | Build begins immediately (no dependencies)

**Budget:** $240–600/year (SIP trunk only) | $0 staff

---

## 1. ARCHITECTURE: Automation-First

| Layer | Tool | GitHub | Why | Setup | Cost |
|-------|------|--------|-----|-------|------|
| **Helpdesk** | Chatwoot | chatwoot/chatwoot | Multi-channel inbox, auto-routing to Akbar | 3h | $0 |
| **Voice IVR** | Jambonz | jambonz/jambonz-platform | Nonprofit claim flow: collect EIN → validate → auto-create ticket | 6h | $0 (+$20–50/mo SIP) |
| **Email Triage** | n8n | n8n-io/n8n | Intent detection (claim? donate? volunteer?), route + auto-respond | 4h | $0 |
| **Donor FAQ Bot** | Local LLM (Qwen/Llama) | home server | "How do I give to X?" → semantic search → respond with donate link | 2h | $0 (GPU-enabled) |
| **CRM + Portal** | ERPNext | frappe/erpnext | Nonprofit self-service portal, minimal fields (claiming + updates) | 4h | $0 |
| **Metrics** | Metabase | metabase/metabase | Ticket backlog, resolution time, escalation rate (detect when Akbar is buried) | 2h | $0 |

**TOTAL SETUP: 21 dev hours (2–3 days) | $240–600/yr cost | 9/10 stewardship alignment**

---

## 2. FOUR FLOWS: Automated + Escalation

### Flow 1: Nonprofit Claiming (Voice-First)

**Automation:** Jambonz IVR → n8n validation → auto-ticket

```
Nonprofit calls (833) DAANAA (332-62) 
  → Jambonz: "Press 1 to claim your nonprofit page"
  → Collect: EIN (DTMF) + domain email (speech → transcribed)
  → Validate: EIN in registry? Email matches domain MX?
  → Success: "Check your email for claim link" + auto-create ticket
  → Failure: "That EIN isn't in our registry" + offer email support
  
Ticket auto-created in Chatwoot with:
  - EIN + name (pulled from registry)
  - Email + transcript
  - Auto-tag: "claim-voice-verified" (skips manual EIN validation)
  
Akbar gets ONE Chatwoot notification for review:
  - Quick check: voice accuracy OK?
  - If yes: send magic link email (auto, via n8n)
  - If no: reply via Chatwoot to clarify

Email magic link → self-serve claim flow (existing web form)
  
KPIs (auto-tracked):
- Claims/week (trend)
- Voice accuracy rate (transcription ≈ database EIN)
- IVR completion rate (calls that reach ticket creation)
- Claim-to-approval time (days)
- Backlog count (Chatwoot unresolved)
```

**When escalation needed:** Voice accuracy <90%, unresolved tickets >7 days (n8n alert to Akbar).

---

### Flow 2: Donor/Volunteer Support (FAQ Bot + Email)

**Automation:** Intent detection → FAQ bot answer OR escalate

```
Donor email → n8n email parser:

IF subject/body matches FAQ patterns:
  - "How do I give to [org]?" 
    → Semantic search: org name → donate URL → auto-reply
    → "Donate directly: [link]"
  
  - "How do I volunteer / log hours?"
    → Auto-reply with link to LogVolunteerHours page
  
  - Generic praise / feedback
    → Auto-reply "Thanks for caring"

ELSE (ambiguous or specific question):
  → Create Chatwoot ticket, tag as "donor-question"
  → Akbar reviews when he has time (not urgent)
  
Chat widget (daanaa.org):
  - Embedded Chatwoot
  - FAQ bot integration (same intent logic)
  - "Typical response: 2–4 hours" message (honest)

KPIs (auto-tracked):
- Auto-response rate (% handled by FAQ bot)
- FAQ match accuracy (did bot answer match intent?)
- Escalation rate (tickets created)
- Email volume / week
- Chat widget usage
```

**When escalation needed:** Auto-response rate <75%, ticket backlog >10 (n8n alert).

---

### Flow 3: Partner/Vendor Support (Self-Service + Escalation)

**Automation:** Self-service portal + smart escalation

```
Partner emails daanaa@daanaa.org → n8n:

IF sender in partner list:
  → Create/link ERPNext contact, tag with partner tier
  → Create Chatwoot ticket (priority: high)
  → Send auto-reply: "Partner support team reviewing"
  
Partner portal (ERPNext):
  - Login via magic link (no password)
  - Dashboard: referral performance (YTD, last 30d)
  - Download: referral reports, integration docs
  - Support history: past tickets
  - Self-serve: update contact info, download invoices
  
Chatwoot ticket for Akbar:
  - Auto-pull: last interaction, current referral metrics
  - SLA: first response <48h (Akbar gets reminder at 24h if unresolved)
  - Auto-tag: "partner-critical" if tier=premium, "partner-standard" if tier=growth

KPIs (auto-tracked):
- Partner portal logins / week
- Self-served requests (didn't create ticket)
- Ticket volume by tier
- SLA compliance (first response <48h)
- Escalation trends (pattern detection)
```

**When escalation needed:** SLA breach >2 weeks, or partner submits "urgent" tag (Akbar paged).

---

### Flow 4: Internal (Chatwoot Inbox + Metrics)

**All inbound** → Chatwoot unified inbox

```
Chatwoot dashboard (Akbar's single source of truth):
- Unresolved tickets by priority: nonprofit-claim | partner | donor | feedback
- Response time: oldest unresolved ticket (age in hours)
- Escalation alerts: 
  - "Nonprofit claim backlog > 5" 
  - "Donor email unresponded >24h"
  - "Partner SLA at risk"

Weekly metrics review (Metabase, 15 min, every Monday):
- Backlog trend (ticket creation vs resolution)
- Response time by channel (voice, email, chat)
- Auto-response rate (FAQ bot effectiveness)
- Escalation triggers (when did alerts fire?)

Tuning loop (if Akbar has time):
- FAQ bot not matching? Update intent patterns in n8n
- IVR voice scripts unclear? Re-record in Jambonz
- Partner portal underused? Add a feature (e.g., download receipts)

KPIs (auto-tracked):
- Tickets created / week (demand signal)
- Avg resolution time (days)
- Backlog size (open tickets)
- Escalation frequency (how often alerts fired)
- Automation rate (% of inbound that didn't need human touch)
```

---

## 3. LOOP: Monitoring + Optimization (Zero Staffing)

### Daily
- Chatwoot inbox check (15 min): resolve escalated tickets

### Weekly (Monday, 15 min)
- Metabase review: any alerts? Any trends?
- If backlog >10: decide what to defer (all non-critical tickets get "thanks, will revisit next week" auto-reply)

### Monthly (1st of month, 30 min)
- Deep dive: 
  - What % of inbound was auto-handled? (target: >70%)
  - What was escalated? (patterns?)
  - Any FAQ bot failures? (retrain)
  - Any IVR failures? (re-record)
- Adjust alert thresholds if needed

### Quarterly (or when revenue permits)
- Consider: hire first person? (only when Chatwoot backlog >50 for 2+ weeks)

---

## 4. WORKFLOW: How it Actually Works Day-to-Day

### Morning (Akbar, 15 min)
```
1. Check Chatwoot: any escalated tickets?
   - Nonprofit claim ready to approve? → send magic link
   - Partner angry? → respond quickly
   - Donor confused? → answer their question
   
2. Check n8n automation logs:
   - Did IVR create tickets correctly? 
   - Did FAQ bot match queries?
   - Any errors to fix?
```

### Evening (Akbar, optional, 5 min)
```
Check escalation alerts:
- Backlog growing? Decide: close old tickets with "thanks, circling back" or answer them
- Any SLA breaches? Respond to partners immediately
```

### Weekend (Akbar, optional)
```
Review Metabase if automation rate is dropping
Update FAQ patterns if lots of "unclear answer" responses
```

---

## 5. STEWARDSHIP ALIGNMENT

| Principle | How Stack Respects It |
|-----------|----------------------|
| **P2: Privacy** | All self-hosted (no SaaS); no tracking of support interactions; email/voice on-prem; no 3rd party vendor access |
| **P3: Trust Signals** | Every ticket traceable; donor FAQ bot cites data source; escalations logged; no AI black-box (rule-based routing) |
| **P5: No Weaponization** | Support tone: helpful, never accusatory; partner support fair (same SLA for all tiers); no shaming language |
| **P7: Independence** | No Zendesk / Intercom / Firebase (all open-source self-hosted); can't be paywalled by vendor changes |
| **P10: AI as Tool** | LLM FAQ bot is local + rule-based (semantic search, not generative); outputs human-reviewed before deploy |

---

## 6. PHASE: V0 LAUNCH (Immediate)

### Week 1: Core Setup (4 days)
- **Day 1:** Chatwoot on droplet + domain email integration
- **Day 2:** Jambonz on home server + SIP trunk signup (Voxbeam $20/mo)
- **Day 3:** n8n for email triage + intent detection
- **Day 4:** ERPNext nonprofit portal + Metabase dashboards

### Week 2: Testing & Tuning (2 days)
- Test IVR: call in, verify claim ticket created
- Test email: send FAQ questions, verify auto-responses
- Test partner portal: login, view dashboard
- **Go-live:** Announce phone number to nonprofits

### Ongoing: Monitor & Tune
- Weekly Metabase review
- FAQ bot improvements (add patterns as new questions arrive)
- IVR script tuning (clarity)

---

## 7. COST BREAKDOWN

| Item | Cost |
|------|------|
| SIP trunk (Voxbeam/Plivo) | $20–50/month = $240–600/yr |
| Server power / cooling (Jambonz on home server) | Already running |
| LLM inference (Qwen on local GPU) | Already running |
| **TOTAL** | **$240–600/yr** |

No staffing cost. Automation handles 70–80% of inbound.

---

## 8. WHEN TO HIRE

**Trigger:** Chatwoot backlog stays >50 for 2+ weeks while Akbar is working 8+ hrs/day on support.

**Then:** Hire 1 part-time support lead (16 hrs/week) to handle overflow. Cost: ~$30K/yr.

---

## 9. SUCCESS CRITERIA (30 days)

- ✅ IVR live; ≥10 nonprofit claims via voice
- ✅ Email triage working; ≥80% auto-response rate for FAQ questions
- ✅ Partner portal used by ≥2 partners (self-served at least once)
- ✅ Backlog <5 tickets (all handled within 48h)
- ✅ Akbar spending <2 hrs/day on support (target: 1 hr/day)

---

## 10. NEXT STEPS

1. **Immediately:** Spin up Chatwoot on droplet (3h)
2. **This week:** Jambonz + n8n (10h dev time)
3. **Next week:** Test, tune, launch phone number
4. **Ongoing:** Weekly metrics review + monthly optimization

---

**Owner:** Claude Code (implementation) + Akbar (operational decisions)  
**Last Updated:** 2026-06-20  
**Next Review:** After Week 1 setup (go-live readiness check)
