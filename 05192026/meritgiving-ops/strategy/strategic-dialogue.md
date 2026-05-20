# Strategic Dialogue — MERIT

**A running synthesis between Akbar and Claude. Updated as we go.**

Not chat history. A curated record of strategic thinking. When Akbar makes a call, it lands here. When Claude sees a pattern across departments, it surfaces here. Quarterly, this becomes the prompt context for the next quarter's work.

---

## Founding context (May 19, 2026)

### Who Akbar is
- Founder of MERIT (DBA under EcoMargins Consulting LLC, transitioning to MeritGiving LLC)
- Houston, TX
- Background includes nonprofit sector understanding, technical capability
- Building MERIT alongside full-time employment
- Time commitment: 2-3 hours/day, structured as morning/lunch/night sessions
- Funding: self-funded through EcoMargins consulting income
- No intent to profit personally from MERIT

### Who MERIT is
- Civic technology platform
- Privacy-first nonprofit directory grounded in IRS public data
- Tagline: "Easy. Private. Fair."
- Phase 0 (current): directory + badges + tip jar, no transactions
- Phase 1 (Months 7-18): nonprofit claims + onboarding
- Phase 2 (Months 19+): GPO vendor marketplace for nonprofits
- 5-year vision: civic infrastructure for the US nonprofit sector

### Why this might work
1. **Mission is timeless** — nonprofit sector problems aren't going away
2. **Architecture is right** — privacy-first compounds trust over time
3. **AI-augmented org model fits** — one founder + Claude can operate at scale that wasn't possible 2 years ago
4. **Market is real** — Charity Navigator and Candid succeed; room for a third positioned differently
5. **Funder thesis is strong** — civic tech with privacy + transparency is exactly what mission-aligned funders want

### Why it might not
1. Solo founder burnout (addressed in operating rhythm)
2. Slower growth than expected (directory is a long game)
3. Vendor/regulatory changes (risk-managed)
4. Competitor pivots (Candid going free?)
5. Mission drift under funding pressure (addressed by mission lock)

---

## Strategic calls made so far

### May 19, 2026

**Call 1: Run in parallel, don't wait for LLC.**
EcoMargins LLC funds everything via DBA structure. Truing up to MeritGiving LLC when ready. Documented in ADR-001.

**Call 2: Heavy upfront scaffolding investment.**
Generating 50+ org files + dashboards before writing product code. Rationale: the org structure should be solid before the product is built on top.

**Call 3: 10 departments with agent structure.**
More structure than a typical startup has, because Claude is doing most of the work. Each department head agent has clear charter; workers execute on schedules. Documented in ADR-005.

**Call 4: 2-3 hours/day operating rhythm.**
Morning/lunch/night sessions. Async-first. Skip-friendly. Documented in operating-rhythm.md.

**Call 5: 7-gate structure for Phase 0.**
Each gate is pass/fail. Gates protect quality, not bureaucracy. Documented in phase-plan.md.

**Call 6: No payment rails in Phase 0.**
Donate buttons link OUT. Tip jar is for MERIT operations only. Removes biggest liability category.

---

## Strategic questions still open

### Need decision soon (Weeks 1-4)
1. **LLC formation path** — DIY ($300, 1-2 wks), service ($500, 3-5 days), or attorney ($1,500, 1-2 wks)? Recommendation: service-assisted via Northwest Registered Agent.
2. **First attorney engagement** — Texas business attorney for LLC + ToS review. Budget: ~$1-2K initial.
3. **First CPA engagement** — Houston-area CPA familiar with civic-tech/nonprofit-adjacent. Budget: ~$500/qtr.
4. **Insurance broker** — start conversation now for Tech E&O + Cyber pricing.

### Need decision by Halfway Mirror (Week 12)
1. **501(c)(3) formation timing** — parallel entity or wait for Phase 1?
2. **Newsletter platform** — Buttondown vs. self-hosted vs. ConvertKit.
3. **Community presence** — Discord, Slack, or just GitHub + Twitter?

### Need decision by Pre-Launch (Week 20)
1. **Public launch strategy** — Hacker News? Civic-tech Slack first? Sector press?
2. **Founding sponsor messaging** — explicit sponsor wall or stealth?
3. **First sector report topic** — "The Invisible Majority" was identified earlier; lock in or pivot?

---

## Patterns Claude is noticing

(This section updates as Claude observes things across departments.)

### Pattern: Heavy emphasis on transparency
Every strategic doc (mission lock, moats, north star, decision log, dashboards) leans toward public visibility. This is a deliberate moat strategy but also creates an obligation: once public, hard to walk back. Make sure each layer of transparency is sustainable.

### Pattern: Risk-averse on revenue
Every potential revenue stream has been evaluated against "perception risk" and most rejected. This is correct for trust-building but creates funding pressure. Mitigation: front-load grant pipeline aggressively in Year 1.

### Pattern: Solo-founder + AI is a new model
Most playbooks assume team formation by Month 6-12. MERIT's plan stays solo through Year 1 by leaning on AI augmentation. This is the experiment. If it works, it's a template; if it doesn't, the dependency on Akbar is a risk.

---

## What we're learning (to be filled in over time)

### What's working
- (To be observed)

### What's not working
- (To be observed)

### What we're changing
- (To be logged as ADRs)

---

## How to use this document

**Akbar:** Add notes whenever something clicks, surprises, or shifts. Don't make it polished. Stream of consciousness is fine.

**Claude:** At end of every session where strategic thinking happened, propose 1-3 sentences to add. Don't pad. Don't summarize. Capture what's actually new.

**Quarterly:** Read the whole thing. Synthesize into `strategic-state-of-the-union.md` that becomes context for next quarter.

**Annually:** Archive the year's dialogue. Start fresh while keeping the founding context section.
