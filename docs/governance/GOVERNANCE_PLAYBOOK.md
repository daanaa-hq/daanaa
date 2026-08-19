# GOVERNANCE PLAYBOOK — MINIMAL ESSENTIAL FRAMEWORK

**Version:** 1.0  
**Date:** 2026-08-10  
**Audience:** Founder, Engineering Lead, Governance Lead  
**Status:** COMPLETE & OPERATIONAL  

This playbook formalizes the minimal governance needed to run Daanaa as a stewardship-driven nonprofit. It's concise, actionable, and Founder-usable (not bureaucratic).

---

## SECTION 1: DECISION HIERARCHY

**Three tiers determine who decides what.** Use this to unblock decisions without ambiguity.

### Tier 1: Autonomous (No Approval Needed)

**What:** Reversible technical decisions  
**Who:** Engineering can decide  
**Examples:**
- Code changes (backend, frontend, scripts)
- Infrastructure changes (if reversible in < 1 hour)
- Local builds, staging deployments
- Experiments or prototypes
- Bug fixes, performance optimizations
- Testing, debugging, research

**Gate:** Does it change what Daanaa asserts to the public? If no → Tier 1.

**Logging:** Log non-obvious choices in `DECISIONS.md` (2-line format: chose/why/rejected)

---

### Tier 2: Founder Review (24h Approval)

**What:** User-facing or partially-reversible decisions  
**Who:** Propose to Founder; they approve within 24h  
**Examples:**
- Recurring spending: $100–1000 (one-time) or $100–500/month
- Public-facing changes (UI, copy, new features)
- Non-critical data migrations
- New hiring, contractor agreements
- Backend deploys to production (must pass smoke test + Founder review)

**Gate:** Takes 24h to review and is easy to reverse → Tier 2.

**Process:**
1. Email Founder: amount, vendor, rationale, duration
2. Wait 24h for approval
3. If unavailable: proceed, then justify when they return
4. Log decision in DECISIONS.md with approval

---

### Tier 3: Founder Decision (Discuss First)

**What:** Irreversible or high-stakes decisions  
**Who:** Founder + Engineering discuss, then Founder decides  
**Examples:**
- Spending > $1000 or > $500/month recurring
- Public claims about organization (privacy, methodology, scores, tax status)
- Schema migrations, data deletion, permission changes
- Major partnerships, vendor contracts
- Changing Stewardship principles or Charter

**Gate:** Can't be reversed or affects what Daanaa promises to public → Tier 3.

**Process:**
1. Engineering proposes with options + recommendation
2. Founder + team discuss (48–72h turnaround)
3. Founder decides
4. Log in DECISIONS.md with rationale

---

### Tie-Breaking & Escalation

**If decision type is ambiguous:**
- Default to the higher tier (when in doubt, get Founder input)
- Document the ambiguity in DECISIONS.md

**If Founder unavailable for Tier 2:**
- Proceed with urgent decisions, then justify
- For critical infrastructure: Emergency override (see Spending Policy below)

**If two goals conflict** (e.g., "ship fast" vs. "verify first"):
- Log both in DECISIONS.md with reasoning
- Founder resolves on next interaction

---

## SECTION 2: RISK REGISTER

**Ten critical risks that could harm Daanaa.** We track, mitigate, and audit each quarterly.

| Risk | Impact | Owner | Mitigation | Check | Escalate If |
|------|--------|-------|-----------|-------|---|
| **Cron/Inference servers down** | LLM pipeline stalled, enrichment stops | Eng | Watchdog + auto-restart (P6 fixes this week) | Weekly health check | >2h downtime |
| **Database corruption/loss** | Can't query orgs, search broken | Eng | Daily S3 backup, tested recovery | Monthly restore test | Restore fails |
| **Search/indexing out of sync** | Search returns wrong results | Eng | Nightly rebuild, pre-deploy validation | Post-deploy check | Drift detected |
| **Founder unavailable** | No one can make critical decisions | Gov | P11 succession mechanism (in progress) | Quarterly | Successor not ready |
| **Principles violated silently** | Code/data drifts from Stewardship | Eng | P6 audits, privacy_check.sh enforcement | Monthly privacy check | Violations found |
| **Decision paralysis** | Ambiguous authority blocks progress | Founder | 3-tier decision framework (this playbook) | Quarterly review | Tiers not working |
| **Data breach** | User wallet or org info exposed | Eng | Firestore uid-scoped rules, encrypt at rest | Quarterly security audit | Vulnerability found |
| **Unauthorized access** | Someone accesses data they shouldn't | Eng | RBAC, audit logs, access reviews | Quarterly access audit | Unexpected access |
| **Public criticism** | Trust damage to platform | Founder | P3 evidence-based approach, corrections | Monthly feedback review | Major negative surge |
| **Service outage (peak season)** | Donors can't discover orgs | Eng | Redundancy, monitoring, IR plan | Quarterly DR drill | Drill fails |

**Quarterly ritual:** Governance Lead reviews all mitigations with Founder (30 min).

---

## SECTION 3: PUBLIC COMMITMENTS

**What we promise. What we must deliver to maintain trust.**

### Commitments We're Making (and Keeping)

✅ **On daanaa.org:**
- Independent discovery platform (P7)
- Evidence-based scores from IRS/ProPublica data (P3)
- Donor privacy protected — no tracking, no exposure (P2)
- Never sponsored results (P7)
- Small orgs treated fairly — peer-group benchmarking, not raw size (P4)

✅ **On DAANAA-CHARTER (10 never-promises):**
- Never track users
- Never sell data
- Never hide errors
- Never accept paid placement
- Never handle donor funds
- [7 more — see `DAANAA-CHARTER.md`]

✅ **On STEWARDSHIP.md (11 principles):**
- Mission-first approach
- Privacy by structural design
- Trust signals are evidence-based
- [8 more — see `STEWARDSHIP.md`]

### Commitments We Need to Clarify

❓ **Data Retention Policy** (P2 requires clarity)
- How long do we keep wallet data after user deletes account?
- How long do we keep backups?
- **Action:** Draft 2-page privacy policy, publish before major launch

❓ **Uptime SLA** (implied by live site)
- What uptime do we target? (99.5%? 99.9%?)
- **Action:** Define, monitor, and publish quarterly

❓ **Correction Process** (P6 requires this)
- How do users report errors about orgs?
- How fast do we fix them?
- **Action:** Add "Report error" button to every org page, link to process

### Commitments at Risk

❌ **P6 (Verification)** — Currently broken (2 systems down, 1,000+ errors/day)
- What we said: Scores are evidence-based and kept current
- What's happening: Some enrichment is stalled
- **Action:** Fix Cron + Inference servers this week (already approved)

❌ **P9 (Explainability)** — Decisions not documented
- What we said: Decisions should be explainable
- What's happening: Some decisions have no rationale recorded
- **Action:** Use this Decision Hierarchy and log all Tier 2/3 decisions going forward

### Quarterly Commitment Review

Every quarter, review:
1. Are we keeping all commitments?
2. Are any at risk?
3. Do we need to add/remove commitments?
4. (Public update if anything changed)

---

## SECTION 4: SPENDING POLICY

**Three tiers of approval. Lean oversight without bureaucracy.**

### Tier 1: Autonomous Spending ($0–100)

**Examples:** npm packages, small SaaS tools, minor services, licenses

**Approval:** None needed  
**Process:** Just buy it  
**Logging:** Log in DECISIONS.md if curious or controversial

**Monthly budget:** Assume $50–100/month for small autonomous spend

---

### Tier 2: Founder Review ($100–1000 or $100–500/month)

**Examples:** 1Password, S3 backups, Cloudflare, new tool subscriptions, hardware < $500

**Approval:** Founder (24h turnaround)  
**Process:**
```
To: Founder
Subject: Spending Request — [Vendor/Item]

Amount: $X [one-time | per month]
Duration: [if recurring: how long expected]
Vendor: [name]
Rationale: [1–2 sentences why we need this]

Approval needed by: [date 24h from now]
```

**If Founder unavailable:**
- Critical infrastructure: Spend up to $500, then justify
- Non-critical: Wait

**Logging:** Track in DECISIONS.md with approval date

---

### Tier 3: Founder Decision ($1000+ or $500+/month)

**Examples:** Major hardware, long-term services, critical infrastructure, annual contracts

**Approval:** Founder + Engineering discuss, then Founder decides  
**Process:**
1. Engineering prepares proposal with 2–3 options
2. Schedule 30-min discussion with Founder
3. Founder decides
4. Log in DECISIONS.md with decision + rationale

**SLA:** 48–72h response (not always 24h for big decisions)

---

### Quarterly Cost Audit

**Every 3 months:**
1. List all active subscriptions/recurring costs
2. For each: Is it still needed? Can we reduce it? Kill zombies?
3. Report to Founder (5 min review)
4. Execute cancellations

**Current recurring costs (estimated):**
- 1Password: $20/month ✅
- Firebase: $0–50/month ✅
- S3: $5–20/month ✅
- Domain: $1/month ✅
- Unknown: $50–100/month (audit will find these)

---

## SECTION 5: IMPLEMENTATION

### Who Does What

| Function | Owner | Frequency |
|----------|-------|-----------|
| Log decisions in DECISIONS.md | Engineer proposing | Per decision |
| Quarterly risk review | Governance Lead | Q1/Q2/Q3/Q4 |
| Monthly privacy checks | Engineering | 1st of month |
| Quarterly cost audit | Founder + Eng | Q1/Q2/Q3/Q4 |
| Quarterly commitment review | Founder | Q1/Q2/Q3/Q4 |
| Quarterly DR drill | Engineering | Q1/Q2/Q3/Q4 |

### When to Use This Playbook

1. **Before deciding anything significant:** "Which tier does this fall into?"
2. **Approving Tier 2 spending:** Follow the email template
3. **At the start of each quarter:** Run risk review + cost audit + commitment review
4. **When Founder is unavailable:** Reference the escalation rules
5. **When a decision is ambiguous:** Default to the higher tier, log it

---

## SECTION 6: QUICK REFERENCE

### Decision Tier Flowchart

```
Is it reversible in < 1 hour AND doesn't change public claims?
  YES → Tier 1 (just do it)
  NO  → Does it affect users or take 24h to reverse?
          YES → Tier 2 (ask Founder, 24h)
          NO  → Tier 3 (discuss first, then decide)
```

### Spending Tier Quick Check

```
How much?
  $0–100      → Tier 1 (autonomous)
  $100–1000   → Tier 2 (Founder review, 24h)
  $1000+      → Tier 3 (discuss first)

How often?
  One-time    → Use amount above
  $100–500/mo → Tier 2
  $500+/mo    → Tier 3
```

### Risk Escalation Thresholds

```
Servers down  → Escalate if >2h
Backup fails  → Escalate if restore doesn't work
Search off    → Escalate if drift detected
Data breach   → Escalate immediately
Founder gone  → Escalate after 7 days (P11 succession)
Decision stuck → Escalate if blocking work >1 week
```

---

## CLOSING

This playbook formalizes what's already working. **No major changes to actual practice** — just clarity on authority, risk mitigation, and quarterly discipline.

**Review this quarterly.** If the three decision tiers aren't working, update them. If risks change, add them. If commitments shift, update those too.

**Questions?** Refer to `STEWARDSHIP.md` for principle context, `CLAUDE.md` for autonomy guidance, or `DECISIONS.md` for decision history.

---

**Version:** 1.0 | **Last Updated:** 2026-08-10 | **Next Review:** 2026-11-10

