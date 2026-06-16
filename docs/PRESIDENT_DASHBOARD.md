# President Dashboard — Daanaa Operations

**Executive view of all active workstreams, pending items, deadlines, blockers.**

**Last updated:** 2026-06-15
**Next review:** 2026-06-22 (weekly Friday EOD)

---

## 🔴 URGENT — This Week (Jun 15–21)

**YOU MUST DO:**

| Item | Status | Deadline | Owner | Action |
|------|--------|----------|-------|--------|
| **Attorney engagement** | BLOCKED | Jun 21 | You | Identify nonprofit + tech attorney; send G1 packet + request bundled quote (~$500–1.2K) |
| **Master narrative editing** | BLOCKED | Jun 21 | You | Read in your voice; edit tone, budget ($X–$Y), team details |
| **Funder deadline verification** | BLOCKED | Jun 21 | You | Check Fast Forward, Knight, Mozilla, Omidyar websites for exact 2026 deadlines |
| **Fiscal sponsor research** | BLOCKED | Jun 28 | You | ID 2–3 candidates (Fast Forward, Tides, TECHSoup); check their application process |

**I CAN'T DO WITHOUT YOU:**
- [ ] Attorney name + email (need to send G1 packet)
- [ ] Budget ask (master narrative needs $X–$Y range)
- [ ] Funder deadline dates (can't submit without confirmed dates)
- [ ] Fiscal sponsor preference (affects legal structure decision)

---

## 🟡 HIGH PRIORITY — Next Week (Jun 22–28)

| Item | Status | Deadline | Owner | Action |
|------|--------|----------|-------|--------|
| **Attorney feedback received** | IN PROGRESS | Jun 28 | Attorney | 3 critical questions answered (entity, solicitation, GPO) |
| **Application tracker setup** | BLOCKED | Jun 28 | You | Copy G0_APPLICATION_TRACKER.md to Google Sheets; fill in all 15 funders |
| **Growth tooling finish** | BLOCKED | Jun 28 | You | Uptime Kuma: set up admin account + daanaa.org monitor (2 min). Plausible: docker compose up + Cloudflare tunnel config |
| **Narrative adaptations edits** | IN PROGRESS | Jun 28 | I'm doing | 9 remaining summaries ready (Echoing Green, Open Society, etc.) |

**I CAN'T DO:**
- [ ] Set up Uptime Kuma dashboard (needs your login to test on 192.168.1.73:3101)
- [ ] Configure Plausible tunnel (needs your Cloudflare account)
- [ ] Final sign-off on budget (only you know what you're comfortable asking)

---

## 🟠 CRITICAL PATH — Week of Jun 29 (First Submissions)

| Item | Status | Deadline | Owner | Action |
|------|--------|----------|-------|--------|
| **First 3 applications submitted** | READY | Jul 5 | You | Submit Fast Forward, Knight, Mozilla (post-attorney review) |
| **Attorney feedback incorporated** | BLOCKED ON ATTORNEY | Jun 28 | I'm doing | Omidyar, DRK, Schmidt narratives updated with legal guidance |
| **Donation link legal model confirmed** | COMPLETE ✅ | Jun 15 | DONE | Only claimed orgs get "Give Now" buttons (org provides link, not us) |
| **Partner onboarding live** | COMPLETE ✅ | Jun 13 | DONE | One-click approve, triage agent, admin review endpoint all deployed |

**I CAN'T DO:**
- [ ] Click "submit" on funder portals (only you can authenticate)
- [ ] Sign applications (need your signature if required)

---

## 📊 ACTIVE WORKSTREAMS (Status Summary)

### G0: Funding Pipeline
| Phase | Status | By When | Owner |
|-------|--------|---------|-------|
| Attorney engagement | 🔴 BLOCKED (waiting on you) | Jun 21 | You |
| Narrative adaptations | 🟡 15/15 DRAFTED | Jun 28 | Done |
| Application tracker | 🔴 BLOCKED (needs your setup) | Jun 28 | You |
| Funder submissions (Tier A) | 🟡 READY | Jul 5 | You |
| First decision received | 🟠 TIMELINE | Aug 15 | Funder |
| Grant funding received | 🟠 TARGET | Sep 30 | Funder |

**Blockers:** Attorney name, budget finalization, deadline verification

---

### Product: Retention Features (G2)
| Feature | Status | By When | Owner |
|---------|--------|---------|-------|
| One-click giving from Wallet | 📋 SPEC DONE | G2 build | Engineering |
| Org-provided donation links | 📋 SPEC DONE | G2 build | Engineering |
| Nonprofit claiming flow | 📋 SPEC DONE | G2 build | Engineering |
| Every.org integration | 🔴 BLOCKED | G2 build | Needs partnership |
| Legal: Donation link model | ✅ COMPLETE | Jun 15 | You approved |

**Blockers:** Engineering capacity, Every.org partnership negotiation

---

### Growth Tooling
| Tool | Status | By When | Owner |
|------|--------|---------|-------|
| **Uptime Kuma** | 🔴 BLOCKED | Jun 28 | You (2-min setup) |
| **Plausible CE** | 🔴 BLOCKED | Jun 28 | You (docker + Cloudflare) |
| **Axe-core a11y** | ✅ COMPLETE | Jun 15 | Done |
| **Satori OG images** | ✅ COMPLETE | Jun 15 | Done |

**Blockers:** Server access for final config

---

### Partners & Nonprofits Onboarding
| Workstream | Status | Metrics | Owner |
|------------|--------|---------|-------|
| **Partner applications** | ✅ LIVE | Pending review, triage agent running | Platform |
| **Admin approval endpoint** | ✅ LIVE | `/api/admin/guild/partners-review` | Platform |
| **One-click approve** | ✅ LIVE | HMAC tokens, email notifications | Platform |
| **Nonprofit claiming** | ✅ LIVE | 500K+ eligible, claiming form published | Platform |
| **Partner voice support** | 📋 ROADMAP | Trigger: 20+ emails/week (mid-July) | Future |

**Next:** Monitor application volume; trigger voice support if 20+ emails/week hit

---

### Data Pipeline & Infrastructure
| Item | Status | Notes | Owner |
|------|--------|-------|-------|
| Web discovery (Phase 1-2) | ✅ COMPLETE | 3,780 websites saved, Phase 3 running | Running |
| Phase 4 GPU verification | 🟡 DEFERRED | Ready when GPU idle time available | Capacity |
| Donation link verification | 🟡 150 LIVE | 46 unpublished (confidence <90%) | Continuous |
| Precompute pipeline | ✅ RUNNING | Nightly orgs, content, FAISS | Running |
| Droplet deployment | ✅ LIVE | 1.87M orgs, static files served | Healthy |

**No immediate action needed; all automated.**

---

## ⏰ DEADLINES (Next 30 Days)

### This Week (Jun 15–21)
- [ ] **Jun 21:** Attorney identified + G1 packet sent
- [ ] **Jun 21:** Master narrative finalized (voice, budget)
- [ ] **Jun 21:** All funder deadlines verified
- [ ] **Jun 21:** Fiscal sponsor candidates identified

### Next Week (Jun 22–28)
- [ ] **Jun 28:** Uptime Kuma + Plausible configured
- [ ] **Jun 28:** Application tracker live (Google Sheets)
- [ ] **Jun 28:** Attorney preliminary feedback received
- [ ] **Jun 28:** Narrative edits complete

### Week of Jun 29
- [ ] **Jun 30:** Fast Forward application submitted
- [ ] **Jul 5:** Knight + Mozilla submitted
- [ ] **Jul 5:** First funder confirmation received (hopefully)

### July
- [ ] **Jul 15:** Omidyar + DRK submitted
- [ ] **Jul 31:** Echoing Green submitted (fellowship deadline)
- [ ] **Jul 31:** Partner onboarding monitoring (20+ emails/week signal?)

### August
- [ ] **Aug 15:** First funding decision expected (Fast Forward)
- [ ] **Aug 15:** Follow-up calls on early submissions
- [ ] **Aug 30:** 7–10 total applications out

---

## 🚨 BLOCKERS (Waiting on You)

### Funding Pipeline (CRITICAL PATH)

| Blocker | Impact | What You Need to Do | Timeline |
|---------|--------|-------------------|----------|
| **Attorney not engaged** | Can't finalize 3 lead narratives (Omidyar, DRK, Schmidt) | Identify attorney + send G1 packet | By Jun 21 |
| **Budget not set** | Master narrative incomplete; all 15 adaptations waiting | Decide: $250K? $500K? $1M ask? | By Jun 21 |
| **Funder deadlines unverified** | Can't lock submission timeline | Check Fast Forward, Knight, Mozilla websites | By Jun 21 |
| **Fiscal sponsor not chosen** | Legal entity structure decision pending | Research + pick 1 candidate | By Jun 28 |

**Impact if not resolved:** Funding applications slip 1–2 weeks

---

### Growth Tooling (MEDIUM PRIORITY)

| Blocker | Impact | What You Need to Do | Timeline |
|---------|--------|-------------------|----------|
| **Uptime Kuma not configured** | Monitoring dashboard not live | SSH to 192.168.1.73:3101, create admin + daanaa.org monitor (2 min) | By Jun 28 |
| **Plausible not deployed** | Analytics not tracking; CSP headers need updating | Docker compose up, tunnel config, `stats.daanaa.org` DNS | By Jun 28 |

**Impact if not resolved:** Visibility/monitoring gap (non-blocking for core product)

---

### Product & Partnerships

| Blocker | Impact | What You Need to Do | Timeline |
|---------|--------|-------------------|----------|
| **Every.org partnership unclear** | G2 giving paths spec complete but integration path TBD | Clarify: Do we want Every.org vs. other processor? | By Jul 15 |
| **Partner network: voice support trigger** | Not needed yet, but monitoring for signal | Track partner application volume; if 20+ emails/week, trigger Vapi/Bland.ai setup | By Jul 31 |

**Impact if not resolved:** Non-blocking; future features only

---

## 📈 KEY METRICS (Live Tracking)

### Funding Pipeline

| Metric | Current | Target (Sep 30) | Trend |
|--------|---------|-----------------|-------|
| Applications submitted | 0 | 10+ | 📊 Starting |
| Funding approved | $0 | $250K–$500K | 📊 Starting |
| Funder relationships opened | 0 | 15 | 📊 Starting |

### Nonprofit Onboarding

| Metric | Current | Target (Sep 30) | Trend |
|--------|---------|-----------------|-------|
| Total searchable orgs | 1.87M | 1.87M+ | ✅ Stable |
| Claimed/verified orgs | ~500K (estimate) | 500K+ | 📊 Monitoring |
| Donation links live (claimed) | Unknown | 500K+ | 📊 TBD |

### Partner Onboarding

| Metric | Current | Target (Sep 30) | Trend |
|--------|---------|-----------------|-------|
| Applications submitted | TBD | 50+ | 📊 Starting |
| Approved partners | TBD | 20+ | 📊 Starting |
| Active referral codes | TBD | 10+ | 📊 Starting |

### Growth Tooling

| Tool | Status | Next Action |
|------|--------|------------|
| Uptime Kuma | 🔴 Pending config | You: 2-min setup |
| Plausible | 🔴 Pending deploy | You: Docker + Cloudflare |
| Axe-core a11y | ✅ Live | Monitoring (no action) |
| Satori OG | ✅ Live | Monitoring (no action) |

---

## 📋 THINGS I CAN'T SEE (Hidden from Automation)

**Items you own that I can't track unless you tell me:**

1. **Attorney conversations** — When you call/email attorney, what do they say? Share key feedback in tracker.
2. **Funder conversations** — Any calls with program officers? Notes go in tracker.
3. **Fiscal sponsor progress** — Which one are you leaning toward? Timeline for agreement?
4. **Budget decisions** — Have you settled on the ask ($250K, $500K, $1M)?
5. **Team/advisor changes** — Any new board members, advisors, or team decisions?
6. **Legal/compliance issues** — Any unexpected legal questions or compliance concerns?
7. **Partner/nonprofit feedback** — What are they saying about the platform? Any patterns in applications/claims?
8. **Market/funder changes** — Any funders you learned about or dropped? Deadlines that shifted?

**You need to surface these so I can update the dashboard.**

---

## 📅 WEEKLY DASHBOARD UPDATE (5-Minute Template)

**Do this every Friday EOD:**

```markdown
## Week of [Jun 22–28]

### Completed This Week
- [ ] Attorney engaged? YES/NO — Details: [name, timeline]
- [ ] Master narrative finalized? YES/NO — Budget ask: $[X]
- [ ] Funder deadlines verified? YES/NO — Count: [X/15]
- [ ] Tracker set up? YES/NO — Link: [Google Sheets URL]

### Blockers Resolved
- [Item that was blocked, now done]

### New Blockers
- [New thing that's in the way]

### Funder Updates
- [Calls, feedback, deadlines changed]

### Next Week Priority
- [1 most important thing]
- [2nd most important thing]
```

---

## 🎯 NORTH STAR (Why This Matters)

| Goal | By When | Current | Progress |
|------|---------|---------|----------|
| **$500K in grants committed** | Sep 30 | $0 | 0% |
| **500K nonprofits claimed** | Dec 31 | ~0 | 0% (tracking) |
| **50+ active partners** | Dec 31 | ~TBD | TBD |
| **G2 (giving paths) live** | Aug 31 | Spec done | 0% (awaiting funding) |

**Your job:** Keep funding + partnerships on pace. Everything else scales from there.

---

## 💬 Questions for You (If Stuck)

1. **Which attorney?** — Do you know a nonprofit + tech lawyer, or should I research?
2. **What's the ask?** — $250K (conservative), $500K (confident), $1M (ambitious)?
3. **Fiscal sponsor?** — Which of Fast Forward/Tides/TECHSoup appeals most?
4. **Funder relationships?** — Do you have existing contacts at any of the 15? (Prioritize those)
5. **Growth tooling:** — Can you SSH to the home server to finish Uptime + Plausible config?

---

## 📌 How to Use This Dashboard

1. **Bookmark it.** Read Friday EOD (5 min) + Monday morning (2 min).
2. **Update weekly.** Use the template above; send me updates in Slack/email.
3. **Escalate blockers.** If something's stuck, flag it here (don't let it linger).
4. **Check "This Week" daily.** If you have attorney/funder news, update immediately.

---

**PRINT THIS & POST IT.** Update every Friday EOD. This is your exec summary.

**Next review:** Friday Jun 21, EOD.
