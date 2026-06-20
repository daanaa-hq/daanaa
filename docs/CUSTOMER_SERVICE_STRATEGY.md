# Daanaa Customer Service Strategy: Next Level
**Goal:** Self-hosted, privacy-first, loop-driven customer service across 4 stakeholder groups with continuous KPI improvement.

**Status:** Research complete | Ready for Phase 2 implementation (Aug 15 - Sep 30)

---

## 1. RECOMMENDED STACK

### Core Tools (Best-in-Class)

| Layer | Tool | GitHub | Why | Setup | Cost |
|-------|------|--------|-----|-------|------|
| **Helpdesk** | Chatwoot | chatwoot/chatwoot | Multi-channel (email+chat), role-based routing, voice-ready | 4h | $0 |
| **Voice IVR** | Jambonz | jambonz/jambonz-platform | Node.js native, webhook-driven, self-hosted SIP | 8h | $0 (+$10-50 SIP) |
| **CRM + Workflows** | ERPNext | frappe/erpnext | Python-native, nonprofit-friendly, custom doctypes | 6h | $0 |
| **Analytics/KPI** | Metabase | metabase/metabase | Zero-code dashboards, perfect for improvement loops | 3h | $0 |
| **Orchestration** | n8n | n8n-io/n8n | Route support tickets, trigger voice calls, sync data | 4h | $0 |

**TOTAL SETUP: 25 dev hours (3 days) | $0 cost | 8.5/10 stewardship alignment**

---

## 2. FOUR STAKEHOLDER FLOWS

### Flow 1: Nonprofit Backend (Voice + Web)
**Users:** Nonprofit staff claiming pages, entering data, updating info  
**Channels:** Voice IVR (phone), web (form), email (support)

```
Nonprofit calls → Jambonz IVR → "Press 1 to claim page" 
  → Voice script collects EIN/domain email
  → Transcribed + validated → ERPNext creates claim record
  → Chatwoot ticket to verify → Email confirmation with magic link
  → Staff completes onboarding in web form
  → Updates sync back to voice (status available via IVR)

KPIs: Claims/week, avg time to claim, voice accuracy, abandonment rate
```

### Flow 2: Donor/Volunteer Support (Chat + Email)
**Users:** Donors asking about orgs, volunteers logging hours  
**Channels:** Email, in-app chat, FAQ bot

```
Donor email → n8n filters → route by intent:
  - "How do I give to X?" → Chatwoot (find donation link)
  - "I volunteered" → Chatwoot (direct to LogVolunteerHours)
  - FAQ match → auto-respond (n8n template)

Chat widget on daanaa.org → Chatwoot → Canned responses + escalate if needed

KPIs: Response time, resolution rate, CSAT, chat/email volume, FAQ effectiveness
```

### Flow 3: Partner/Vendor Support (Ticketing + CRM)
**Users:** Vendors managing referral links, partners checking integrations  
**Channels:** Email, dedicated portal (ERPNext)

```
Partner email → n8n → ERPNext CRM contact → Chatwoot ticket
  - Assign to account manager
  - Auto-attach referral performance data (Metabase snapshot)
  - Track SLA (48h first response, 2wk resolution)
  - Post-resolution: survey for CSAT

Portal: Self-service referral dashboard (ERPNext portal), ticket history, docs

KPIs: Partner satisfaction, ticket volume, SLA compliance, average revenue per partner
```

### Flow 4: Internal (Backend Office)
**Users:** Daanaa ops team handling all support  
**Channels:** Chatwoot (unified inbox), ERPNext (CRM), Metabase (metrics)

```
All inbound → Chatwoot unified inbox (email + voice transcripts)
  - Dashboard: open tickets by type (nonprofit claim, donor question, vendor issue)
  - Route to specialist (voice tech, data entry, partner manager)
  - SLA monitoring (priority: nonprofit > partner > donor > internal)

Weekly retrospective (Metabase):
  - Response time trend by channel
  - Resolution rate by type
  - Bottleneck identification
  - Staffing adjustment signals

KPIs: Team productivity, ticket backlog, SLA compliance, issue categories, automation rate
```

---

## 3. LOOP DEVELOPMENT (Continuous Improvement)

### Weekly Cycle
```
Monday 9am: Review Metabase dashboards (15 min)
- Response time by channel (target: <4h nonprofit, <24h donor)
- Resolution rate (target: 90%)
- Open ticket count (trend)
- Voice call success rate (target: 95% completion)

Tuesday 2pm: Team sync (30 min)
- Bottlenecks from last week
- Top 3 unresolved tickets
- Automation opportunities (e.g., FAQ q's that should be auto-response)
- Staffing needs

Thursday: Implement improvements
- Update FAQ in Chatwoot (auto-responses)
- Add n8n rule (if email matches pattern X, auto-response Y)
- Retrain voice script (Jambonz webhook)

Friday 4pm: Retrospective (15 min)
- Did improvements move metrics?
- New blockers?
- Next week priorities
```

### Monthly Cycle
```
Month-end: Deep dive (1 hour)
- CSAT analysis (partner survey results, email sentiment)
- Cost per resolution (dev hours invested / tickets resolved)
- Automation rate (tickets with zero human touch)
- Nonprofit onboarding funnel (claim start → completion)
- Partner net retention (churn + expansion)

Adjust targets, staffing model, or tool config based on trends
```

---

## 4. KPI DASHBOARD (Metabase)

### Nonprofit Onboarding
- Claims started/week (funnel: start → email verified → form completed)
- Days to first response (voice or email)
- Days to claim approved
- Voice vs web claim ratio
- Claim abandonment rate

### Donor/Volunteer Support
- Email response time (target: <4h)
- Chat response time (target: <1h)
- Resolution rate (1st response closes issue)
- CSAT (post-resolution survey)
- Most common questions (for FAQ automation)

### Partner/Vendor
- Partner satisfaction score (quarterly survey, Metabase snapshot)
- Ticket volume by partner tier
- SLA compliance (48h first response, 2wk close)
- Average revenue per partner (track growth)
- Churn rate (target: <5%/year)

### Internal Operations
- Team capacity utilization (hours/person on tickets)
- Burndown rate (tickets closed/week)
- Backlog trend (new vs closed, target: zero growth)
- Automation rate (% of tickets requiring zero human touch)
- Cost per resolution (staff hours / tickets closed)

---

## 5. STEWARDSHIP ALIGNMENT

| Principle | How Stack Respects It |
|-----------|----------------------|
| **P2: Privacy** | All self-hosted (no SaaS vendor); email/voice data stays on-prem; no donor tracking; transcripts encrypted |
| **P3: Trust Signals** | Support email is @daanaa.org (not generic/shared); all responses traceable; no AI black-box (Jambonz scripts auditable) |
| **P5: No Weaponization** | Support tone guides: helpful, respectful, no shame language; partner support is fair (no favoritism) |
| **P7: Independence** | No third-party dependencies (own Jambonz instance, own Chatwoot, own Metabase); stack is open-source auditable |
| **P10: AI as Tool** | Voice transcripts + IVR scripts are deterministic (Jambonz templates, not LLM-generated); team reviews before deploy |

---

## 6. PHASE 2 ROADMAP (Aug 15 - Sep 30)

### Week 1-2: Foundation (Aug 15-29)
- Metabase on droplet + dashboard config (3h)
- Chatwoot setup + Daanaa mailbox integration (4h)
- n8n orchestration layer (email → Chatwoot routing) (3h)
- **Test:** Send internal test emails, confirm routing works

### Week 3-4: Voice (Aug 30-Sep 12)
- Jambonz setup on home server (6h)
- SIP trunk config (Twilio or open-source SIP provider) (2h)
- IVR script for nonprofit claim flow (3h)
- Chatwoot webhook integration (Jambonz → ticket) (2h)
- **Test:** Call in, trigger claim workflow, confirm transcript captured

### Week 5-6: CRM + Automation (Sep 13-26)
- ERPNext nonprofit onboarding doctype (4h)
- n8n advanced rules (partner tickets → CRM, donor → FAQ-check) (3h)
- Partner portal setup (ERPNext) (2h)
- Metabase partner metrics dashboard (2h)
- **Test:** Full end-to-end flow for each stakeholder

### Week 7-8: Loop + Deploy (Sep 27-30)
- Team training on daily/weekly loop (1h)
- Metabase board on ops dashboard (1h)
- Deploy to staging, 1-week pilot with ops team
- Cutover to production (go-live Sep 30)

---

## 7. STAFFING MODEL

### For Daanaa's Phase 2 (Launch + First 6mo)

| Role | Hours/Week | Responsibilities |
|------|-----------|------------------|
| **Support Lead** (1 FTE) | 40h | Chatwoot inbox, nonprofit claims, partner escalations |
| **Ops/Data** (0.5 FTE) | 20h | Metabase dashboards, n8n rule management, voice script updates |
| **Dev** (on-call) | 5h | Jambonz webhook debugging, ERPNext custom fields, stack maintenance |

**Cost:** ~$120K/year (assuming $60K/FTE support, $80K ops, $100K dev on-call)

### How it Scales
- **2M → 5M donors:** +1 support (now 2 FTE)
- **100 → 500 nonprofit claims/month:** +0.5 FTE ops (data entry & voice script tuning)
- **10 → 50 partners:** +0.25 FTE partner manager (within ops)

---

## 8. BUDGET & RISKS

### Total Cost (Year 1)
| Item | Cost |
|------|------|
| Software licenses | $0 (all open-source) |
| SIP trunk (Jambonz) | $50-200/mo = $600-2400/yr |
| Droplet upgrades (compute) | $0 (existing capacity) |
| Home server power (voice) | ~$20/mo = $240/yr |
| Staffing (support + ops) | $90-120K |
| **TOTAL** | **$91-123K** |

### Risks & Mitigations
| Risk | Mitigation |
|------|-----------|
| Jambonz setup complexity | Use Jambonz managed SIP (if needed) vs self-hosted SIP; 2-week buffer |
| Voice transcription accuracy | Jambonz webhook → manual QA, update scripts if <95% accuracy |
| Support volume ramp | Build in 20% over-capacity; monitor weekly, scale at 80% utilization |
| Vendor SIP dependency | Keep Jambonz *control* self-hosted; only SIP *trunk* outsourced (commoditized) |

---

## 9. SUCCESS CRITERIA (90 days)

- ✅ **Nonprofit:** <4h email response, claim completion rate >80%
- ✅ **Donor:** 90%+ FAQ autoresponse rate, CSAT >4.5/5
- ✅ **Partner:** SLA 100% met, partner satisfaction >4/5
- ✅ **Internal:** Zero backlog (closed ≥ opened weekly), automation rate >30%
- ✅ **Stewardship:** Zero SaaS vendors, 100% audit trail in self-hosted stack

---

## 10. NEXT STEPS

1. **Align with Akbar** (this week)
   - Confirm staffing model (support lead + ops FTE)
   - Approve SIP trunk provider (Twilio, Plivo, or Voxbeam)
   - Lock Phase 2 timeline (Aug 15 start)

2. **Spin up repos** (Week 1)
   - Fork Chatwoot, Jambonz, ERPNext, Metabase to Daanaa GitHub
   - Document deployment: runbooks for each tool
   - CI/CD pipeline for config-as-code

3. **Staffing** (Immediate)
   - Hire or designate support lead
   - Identify ops person (could be Akbar part-time initially)
   - On-call dev (Paris or junior contractor)

---

## References

- **Chatwoot:** https://github.com/chatwoot/chatwoot (14K stars, Docker, multi-tenant ready)
- **Jambonz:** https://github.com/jambonz/jambonz-platform (1.5K stars, Node.js, webhook-driven)
- **ERPNext:** https://github.com/frappe/erpnext (10K stars, Python, nonprofit use cases documented)
- **Metabase:** https://github.com/metabase/metabase (27K stars, Docker, zero-code dashboards)
- **n8n:** https://github.com/n8n-io/n8n (Workflow orchestration, self-hosted, active community)

**Owner:** Claude Code + Akbar (product/strategy)  
**Last Updated:** 2026-06-20  
**Next Review:** Aug 1 (pre-Phase 2 kickoff)
