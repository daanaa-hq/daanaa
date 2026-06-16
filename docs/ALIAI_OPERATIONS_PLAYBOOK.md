# All-AI Operations Playbook

**Phase:** Jul 1 — Aug 15 (Build) + Aug 15 — Oct 1 (Public Launch Ramp)

**Goal:** Build autonomous AI agents for onboarding, support, and growth with zero headcount.

---

## What You're Building (Overview)

Instead of hiring people, you're building AI agents that handle:

1. **Nonprofit Onboarding Agent** — Helps nonprofits verify their org, claim their profile, submit data
2. **Support Triage Agent** — Reads incoming support emails, categorizes issues, drafts responses
3. **Growth/Analytics Agent** — Analyzes user behavior, identifies engagement gaps, suggests content
4. **Data Validation Agent** — Checks incoming nonprofit data for quality, flags inconsistencies
5. **Compliance Monitor** — Watches for potential issues (privacy, fairness, principles drift)

---

## Technology Stack

### Local Inference (Your Home Server)

| Service | Port | Model | Use | Cost |
|---------|------|-------|-----|------|
| llama-server (Vulkan) | 11437 | Qwen2.5-32B-Instruct-Q4_K_M | Agent reasoning, text generation | Free (local) |
| llama-server (Vulkan) | 11436 | mxbai-embed-large | Embeddings, semantic search | Free (local) |
| Ollama | 11434 | mxbai-embed-large (fallback) | Backup embeddings | Free (local) |

**Why local:** Full auditability, no external API calls for sensitive data, cost control, privacy compliance.

### Claude API (Anthropic)

| Use | Cost | Budget |
|-----|------|--------|
| Complex reasoning, edge cases | $0.003/1K input tokens | $50–80K/year |
| Fact-checking, policy questions | $0.003/1K input tokens | (budgeted) |

**When to use Claude API:**
- Agent runs into something local models can't handle
- Need multi-step reasoning over domain data
- Compliance review or principle checking
- Research or analysis requiring long-context

**When NOT to use:**
- Routine text generation (use local)
- High-volume tasks (batches through local models)
- Anything touching private donor/nonprofit data

### Infrastructure

| Component | Tool | Cost/Year |
|-----------|------|-----------|
| **Orchestration** | FastAPI + APScheduler | Free (runs on home server) |
| **Database** | PostgreSQL (on server) | Free |
| **Monitoring** | Local dashboard (custom) | Free |
| **Logging** | PostgreSQL + JSON files | Free |
| **Secrets** | Environment variables | Free |

**Hardware requirement:** Your existing Ryzen 9700X + R9700 32GB GPU (already have this)

---

## Agent Design Pattern

Every agent follows this structure:

```
1. TRIGGER (cron, webhook, manual)
   ↓
2. INPUT (email, data file, webhook payload)
   ↓
3. CLASSIF & ANALYSIS (local model or Claude)
   - What is this? What does it need?
   ↓
4. ACTION (generate response, update database, flag for review)
   ↓
5. LOG (record decision, confidence, timestamp)
   ↓
6. HUMAN GATE (approval required for: external comms, data changes, policy decisions)
   ↓
7. EXECUTE (send email, update DB, notify Akbar)
```

**Human in command always.** AI proposes, human approves.

---

## Agent 1: Nonprofit Onboarding Agent

### What It Does

Nonprofits come to daanaa.org and want to claim their profile. This agent:
1. Reads the org claim form
2. Verifies the submitter is authorized (checks against IRS data)
3. Guides them through claiming steps
4. Generates welcome email
5. Logs everything for audit trail

### Build Plan (2 weeks, Jul 1–14)

**Week 1:**
- [ ] Design the claim form (Zod schema)
- [ ] Write failing tests for claim validation
- [ ] Build claim validation logic
- [ ] Write nonprofit lookup against IRS database
- [ ] Test with 5 manual claims

**Week 2:**
- [ ] Build email generation for welcome messages
- [ ] Add approval gate (human reviews claim before approval)
- [ ] Build logging + audit trail
- [ ] Test with 20 claims (partly automated, partly manual verification)
- [ ] Deploy to staging

### Tools & Technologies

- **Frontend:** React form (Zod validation)
- **Backend:** FastAPI endpoint `/api/claims/submit`
- **Database:** `org_claims` table (exists, has attestation history)
- **AI:** Claude API for permission verification if submission is ambiguous
- **Output:** Email via daanaa.org aliases + log entry

### Success Metric

By Aug 1: 50+ nonprofits have claimed profiles in sandbox. Agent handles 80% of claims with zero human intervention; flags 20% for manual review.

---

## Agent 2: Support Triage Agent

### What It Does

Emails come in to support@daanaa.org. This agent:
1. Reads incoming email
2. Classifies: bug report / question / partnership / claim issue / other
3. Drafts response (or flag for human)
4. Logs issue
5. Routes to appropriate team (Akbar, nonprofit onboarding, data team, etc.)

### Build Plan (2 weeks, Jul 15–29)

**Week 1:**
- [ ] Define support categories + response templates
- [ ] Build email parser (extract from Gmail API or IMAP)
- [ ] Classify using local LLM (Qwen2.5)
- [ ] Draft templates for common responses
- [ ] Test with 20 real support emails

**Week 2:**
- [ ] Add Claude API for edge cases + judgment calls
- [ ] Build approval gate (human reviews draft before send)
- [ ] Add metrics tracking (response time, resolution rate)
- [ ] Integrate with org claims if relevant
- [ ] Deploy

### Tools & Technologies

- **Email:** Gmail API (daanaa.org aliases)
- **AI:** Qwen2.5 (classification) + Claude API (judgment calls)
- **Database:** `support_tickets` table (new)
- **Output:** Draft email + classification + human approval gate

### Success Metric

By Aug 1: Agent handles 10+ emails/week. 90% of common questions answered automatically. 100% of emails read and classified correctly.

---

## Agent 3: Growth/Analytics Agent

### What It Does

Analyzes user behavior + engagement. Identifies:
- Which nonprofit profiles get visited most
- Which search queries fail (no results)
- Which donors add orgs to wallet but don't give
- Geographic hotspots
- Category gaps

Generates weekly report + growth recommendations.

### Build Plan (1.5 weeks, Jul 30 — Aug 6)

**Week 1:**
- [ ] Design analytics schema (log every user action)
- [ ] Write queries for key metrics
- [ ] Build weekly report generator
- [ ] Test with real user data from beta

**Bonus:**
- [ ] Identify "orphan" nonprofits (never visited)
- [ ] Suggest content for hidden gems
- [ ] Find category gaps

### Tools & Technologies

- **Database:** PostgreSQL event log (exists)
- **AI:** Local LLM for insight generation (Qwen2.5)
- **Output:** Weekly report + recommendations

### Success Metric

By Aug 15: Weekly reports identify 2–3 actionable insights. Recommendations lead to content or feature changes.

---

## Agent 4: Data Validation Agent

### What It Does

Nonprofit data (mission, tags, website, donation link) comes in from the pipeline. This agent:
1. Validates quality (is mission complete? are tags sensible? is website live?)
2. Flags inconsistencies (EIN mismatch? outdated address?)
3. Routes for human review if confidence is low
4. Updates database + logs findings

### Build Plan (1 week, Jul 15–22)

**Week 1:**
- [ ] Design validation rules (schema + constraints)
- [ ] Build validation logic (check website, verify EIN, etc.)
- [ ] Add human approval gate
- [ ] Test with 100 org records

### Tools & Technologies

- **Pipeline:** Existing scripts (precompute_orgs.py, etc.)
- **Validation:** Rules engine + local LLM for judgment calls
- [ ] Database:** `data_quality` table (new) + flags on existing records

### Success Metric

By Aug 1: Agent validates 99.5% of org records. Flags <1% as requiring human review. Database quality improves measurably.

---

## Agent 5: Compliance Monitor

### What It Does

Watches the system for principle drift:
- Are any orgs being ranked unfairly? (Check: scores by archetype + size)
- Are donors being tracked? (Check: privacy logs)
- Are partners getting special treatment? (Check: feature flags, algos)
- Are small orgs getting buried? (Check: search results quality)

Runs daily. Alerts Akbar if anything looks off.

### Build Plan (1 week, Aug 7–14)

**Week 1:**
- [ ] Design compliance checks per Stewardship Principle
- [ ] Build monitoring queries
- [ ] Set alert thresholds
- [ ] Test with sample data

### Tools & Technologies

- **Queries:** PostgreSQL + Python analysis scripts
- **Alerts:** Email to akbar@daanaa.org
- **Logging:** `compliance_log` table

### Success Metric

By Aug 15: Daily scans complete. Zero false alarms. Catches real issues (if any) within 24 hours.

---

## Build Timeline (Jul 1 — Aug 15)

```
Week 1–2 (Jul 1–14):   Nonprofit Onboarding Agent ✅
Week 3–4 (Jul 15–29):  Support Triage + Data Validation ✅
Week 5 (Jul 30–Aug 6): Growth/Analytics Agent ✅
Week 6 (Aug 7–14):     Compliance Monitor ✅
Week 7 (Aug 15):       Deploy to public launch ✅
```

---

## Infrastructure Setup (Day 1: Jul 1)

**To run all agents, you need:**

- [ ] **FastAPI server** running on localhost:8000 (orchestrator)
- [ ] **PostgreSQL** running on localhost:5432 (database)
- [ ] **llama-server** running on ports 11436–11437 (inference)
- [ ] **APScheduler** (cron for agents)
- [ ] **Gmail API credentials** (for support emails)
- [ ] **Environment variables** (.env file with API keys, secrets)

**Scripts to create:**

1. `start_local_inference.sh` — Starts llama-server + Ollama
2. `start_orchestrator.sh` — Starts FastAPI + agents
3. `check_agent_health.sh` — Verifies all agents are running
4. `restart_agents.sh` — Clean restart

**Monitoring dashboard:**

- Simple web dashboard showing:
  - Agent status (running / idle / error)
  - Last execution time
  - Logs + alerts
  - Quick manual trigger buttons

---

## Cost Breakdown (Jul–Aug + First 3 Months)

| Item | Cost/Month | Cost/3mo |
|------|-----------|----------|
| Claude API (~$15K/month tokens) | $15K | $45K |
| Local inference (electricity, negligible) | $0 | $0 |
| PostgreSQL (on server, negligible) | $0 | $0 |
| FastAPI hosting (on server) | $0 | $0 |
| Gmail API (free tier, <100K/month) | $0 | $0 |
| **Total** | **$15K** | **$45K** |

**Note:** Claude API cost assumes heavy use during build + testing. Real production cost will be lower (50–70K/year for operations).

---

## Sandbox Testing (Aug 1–15)

Before launching publicly, test with 50 volunteer nonprofits:

**Week 1 (Aug 1–8):**
- [ ] Recruit 50 nonprofits (use network, past users, partner networks)
- [ ] Have them use claiming, support, search
- [ ] Agents handle their requests
- [ ] Collect feedback daily

**Week 2 (Aug 9–15):**
- [ ] Fix any agent issues found
- [ ] Refine workflows based on feedback
- [ ] Train agents on edge cases from beta
- [ ] Run final compliance scan
- [ ] Deploy to public launch

---

## Public Launch (Aug 15 onwards)

### Phase 1: Aug 15
- [ ] Claiming form live (agents active)
- [ ] Directory search live
- [ ] Support email handling live

### Phase 2: Aug 22 (after 1 week feedback)
- [ ] Support triage agent live (handles common Q&A)

### Phase 3: Sep 1 (after 2 weeks feedback)
- [ ] Growth agent live (weekly reports)

### Phase 4: Oct 1
- [ ] All agents fully active + monitored

---

## Keys to Success

1. **Human in command always.** Every agent has an approval gate for external actions.
2. **Log everything.** You need a complete audit trail for compliance + debugging.
3. **Monitor continuously.** Daily compliance check + weekly agent health review.
4. **Iterate fast.** Agents improve from feedback. Weekly reviews + updates.
5. **Keep scope tight.** These 5 agents do 80% of work. Don't build more until needed.
6. **Use local inference.** Keep cost down, privacy high, auditability perfect.

---

## FAQ

**Q: What if an agent makes a mistake?**
A: You have logs showing exactly what it did and why. You can audit, correct, and retrain. Approval gates catch errors before they reach users.

**Q: How much monitoring is needed?**
A: 30 min/day: Check agent status in morning, review logs, respond to alerts. Weekly: Deeper analysis of agent performance.

**Q: Can you scale this with 5 agents?**
A: Yes. With sandbox testing + refinement, 5 agents handle 1.87M nonprofits + 100K+ donors. At 10x scale, you'd add 1–2 more agents.

**Q: What if Claude API gets too expensive?**
A: Move more logic to local models. Or drop to 1 Claude call/week for compliance check instead of real-time.

---

*Last updated: Jun 15, 2026 (evening preparation for Jul–Aug build phase)*
