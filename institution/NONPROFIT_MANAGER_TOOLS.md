# Nonprofit Manager Tools — Capacity Stewardship Implementation

**Authority:** Stewardship Board Resolution 2026-07-11, Decision #6 (Capacity Stewardship as binding principle)  
**Rationale:** "Every feature increases nonprofit capacity." Test: "What capability does this organization possess after this interaction that it didn't before?"  
**Scope:** Tools for nonprofit managers, especially small orgs (<$700K revenue), that build real capability across the 11 canonical dimensions  
**Status:** Specification (founder review required before design/implementation)

---

## The 11 Canonical Capacity Dimensions

From Board Resolution §7 (Capacity Framework), the stable dimensions are:

1. **Clarity** — Can the org articulate its mission, impact, and financial health in simple terms?
2. **Financial** — Can the org understand its financial position and peer context?
3. **Leadership** — Can the org identify and develop leaders?
4. **Technology** — Can the org adopt digital tools and manage data?
5. **Community** — Can the org engage and listen to its community?
6. **Governance** — Can the org make decisions transparently and accountably?
7. **Sustainability** — Can the org sustain its mission over time?
8. **Data** — Can the org collect, store, and act on data responsibly?
9. **Communication** — Can the org tell its story clearly to stakeholders?
10. **Growth** — Can the org scale impact responsibly?
11. **Impact** — Can the org measure and improve what it cares about?

---

## Current Daanaa Surfaces (for or against capacity)

### Surfaces that INCREASE capacity:

- **Org detail page + financial context** (Financial dimension) — peer-context framing helps smaller orgs see their financial health without shame language or size-ranking
- **Giving Wallet + bookmarking** (Communication/Community dimension) — orgs see who might support them, can track giving patterns they inspire
- **Mistake Registry** (Governance/Clarity dimension) — orgs can correct inaccurate data, building trust and transparency
- **Mission/cause-tag crowdsourcing** (Clarity/Communication dimension) — orgs can claim their data and add nuance to how they're described

### Surfaces that currently DO NOT exist (gaps):

- **Peer benchmark dashboards** (Financial/Leadership dimension) — "here's how orgs like you (same revenue band, NTEE) manage reserves, program spend, growth"
- **Nonprofit manager onboarding toolkit** (Technology/Data dimension) — "you're new to nonprofit work; here's what financial metrics matter, why, and how to track them"
- **Org capability self-assessment** (all dimensions) — "rate yourself on these 11 dimensions; here's where similar orgs focus first; here's what Daanaa can help with"
- **Donor/stakeholder communication templates** (Communication dimension) — "use this template to explain your financial context to your board, funders, community"
- **Peer learning / peer group directory** (Community/Leadership dimension) — "connect with orgs of your size/type/cause to share how you solved X"
- **Data governance quick-start** (Data/Governance dimension) — "here's a checklist: what to track, what NOT to track (privacy), how to store it, when to share it"
- **Sustainability planning tool** (Sustainability dimension) — "input your revenue, expenses, reserves; we show you runway, growth scenarios, and what peers do"

---

## Proposed Phased Rollout

### Phase 1: Self-Assessment + Peer Benchmarking (3–4 weeks)

**Goal:** Help small orgs see their capacity gaps and learn from peers.

**Deliverables:**
1. **Capacity self-assessment (web form):**
   - 11 questions (one per dimension), Likert scale 1–5
   - Takes 5 minutes
   - Saved to wallet (device-first, optional account sync)
   - Never shared publicly

2. **Peer comparison (read-only dashboard):**
   - "Your score: Financial 3/5. Peers (same revenue band + NTEE): median 3.5/5"
   - Shows which dimensions peers focus on first (based on anonymized survey data)
   - No names, no org-specific data, just aggregated insights

3. **Capacity-guided tour:**
   - After assessment, show 2–3 "here's what Daanaa offers for your top gap" cards
   - Links to relevant surfaces (Mistake Registry for Clarity gap, Peer benchmarks for Financial, etc.)

**Why this phase:** Closes the "I don't know what to focus on" problem; costs us nothing (no new backend, just survey aggregation); builds the research dataset for later phases.

### Phase 2: Communication & Learning (6–8 weeks, dependent on Phase 1 data)

**Goal:** Give orgs words and peer examples.

**Deliverables:**
1. **Template library (document export, not a tool):**
   - "Explaining our financial context to our board" (uses Daanaa's peer-context language)
   - "Annual stakeholder report template"
   - "Donor thank-you framework" (P2 compliant: no giving data exposed)
   - Editable, downloadable as PDF or Google Docs

2. **Peer learning directory (search + filter):**
   - Opt-in: orgs can list themselves as "peer learning contact" (name, email, causes)
   - Filterable by size, location, NTEE, cause tag
   - No endorsement — just a directory; Daanaa never mediates the connection
   - Complies with P7 (independence): zero platform benefit from who peers connect with

3. **Data governance checklist:**
   - 1-pager: what to track (mission, financials, impact), what NOT to track (sensitive personal data), how to store it, when to share
   - Authored by Daanaa + nonprofit data experts (external advisory board)
   - Sits on the research page, not in product

### Phase 3: Planning Tools (10–12 weeks, if Phases 1–2 succeed)

**Goal:** Help orgs model their future and test assumptions.

**Deliverables:**
1. **Sustainability runway calculator:**
   - Input: revenue, expenses, reserves
   - Output: months of runway, break-even sensitivity, what-if scenarios (10% growth, 20% revenue drop)
   - Peer comparison: "if your revenue dropped 20%, you'd have X months runway; peers average Y"
   - Optional sign-in for multi-year tracking

2. **Nonprofit manager onboarding (interactive guide):**
   - "You're new to nonprofit finance" → walk through 11 dimensions, explain why each matters
   - Linked to Daanaa data (e.g., "Here's your peer group's median program spend %")
   - Optional email sequence (one per week for 8 weeks)

---

## Nonprofit Benefit (Board Resolution §6 test)

**Capability gained after interaction:**

| Dimension | Baseline | After Daanaa Capacity Tools |
|-----------|----------|----------------------------|
| Clarity | "We're not sure how to describe our impact" | "We know our peer-group financial position; we can explain it clearly" |
| Financial | "Our board doesn't understand our reserves" | "We can show our board a peer benchmark + sustainability model" |
| Leadership | "We don't know how other orgs build leadership" | "We can connect with peer orgs' leaders; we've self-assessed our gaps" |
| Technology | "We don't have data systems" | "We have a checklist (what to track, what not to); we know we're not alone" |
| Community | "We don't know how to engage donors" | "We have a template for stakeholder communication; we see peer-giving patterns" |
| Governance | "We don't know if our decisions are transparent" | "We have a self-assessment; we see peer governance patterns" |
| Sustainability | "We don't plan for the long term" | "We can model our runway and test scenarios vs. peers" |
| Data | "We're overwhelmed by compliance" | "We have clear guidance on what matters vs. what's overkill" |
| Communication | "We struggle to tell our story" | "We have peer-vetted templates" |
| Growth | "We don't know if we should grow" | "We can model growth scenarios and see peer approaches" |
| Impact | "We don't measure impact consistently" | "We see how peers measure; we have a framework" |

**For small orgs specifically:** every tool is designed to take <10 minutes of setup, work offline-first, and never require fundraising or hiring a consultant. The cost is zero; the capacity gain is real.

---

## Design Constraints

1. **No surveillance.** Data from self-assessments is never used for marketing, fundraising, or external targeting (P2).
2. **No shame language.** Peer comparisons use neutral framing ("median 3.5", not "average org scores higher").
3. **No size-ranking.** All comparisons are within revenue band + NTEE, never cross-org.
4. **Opt-in participation.** Survey responses are optional; comparisons use only consenting orgs.
5. **Export-first design.** Templates are downloadable (Google Docs, PDF, Markdown); orgs never depend on Daanaa to access their work.
6. **Peer directory is truly neutral.** Zero platform curation; Daanaa doesn't gain if orgs connect or don't.

---

## Founder Decisions Needed Before Design

1. **Timeline:** Phase 1 only (4 weeks) → ship → measure → decide on Phase 2/3? Or commit to the full roadmap now?
2. **Advisory board:** Should Daanaa convene a nonprofit data/governance advisory board to co-author the data checklist and onboarding? (adds credibility; costs ~2–4 hours/month of founder + 1–2 external experts).
3. **Peer learning directory:** Include nonprofit-focused vendors (payment processors, accounting software, HR platforms) as "partner recommendations"? This risks P7 (independence); recommend against it unless founder sees a strong reason.
4. **Email sequence:** If we build the onboarding, should it include an optional 8-week email series? (light lift; adds retention; must be unsubscribable 1-click per P2).

---

## Success Metrics (after Phase 1 ships)

- % of browsing users who take the self-assessment (target: 5–10%)
- Completion rate (target: >80% of starters finish it)
- Engagement with peer-comparison dashboard (target: >40% of completers view it)
- Click-through to Daanaa features from "guided tour" (e.g., "fix this gap in Mistake Registry")
- Nonprofit manager sentiment on a follow-up survey: "I learned something new about my org's capacity" (target: >70% agree)

---

## Not in Scope (explicitly)

- **Fundraising tools.** Daanaa will never help orgs fundraise or prospect donors. Period. (P8 — we don't control funds.)
- **Compliance automation.** We don't generate 990s, grant applications, or legal documents. We point to external tools.
- **Vendor endorsement.** We recommend *categories* (accounting software, payroll, CRM) but never single vendors unless fully transparent + P7-compliant.
- **Internal tools.** These are for nonprofit *managers* to understand their org, not for Daanaa to manage orgs.

---

## Implementation Order (if approved)

1. Draft self-assessment questions with founder + advisory board (2 weeks)
2. Build the survey form + response storage (2 weeks)
3. Build peer-comparison aggregation + dashboard (2 weeks)
4. Run a beta with 50 pilot orgs (2 weeks)
5. Iterate based on feedback, then Phase 1 launch
6. Measure success metrics for 4 weeks
7. Founder + team decide: Phase 2 go/no-go

---

## Alignment with Stewardship Principles

- **P1 (Mission before growth):** Every tool focuses on helping orgs improve, not on driving Daanaa engagement metrics.
- **P2 (Privacy structural):** No collection, retention, or sharing of org-identifying data beyond what orgs consent to.
- **P3 (Evidence-based):** All peer comparisons are from public data + opt-in surveys; no guessing.
- **P4 (Small org fairness):** Explicit design for <$700K orgs; peer groups are revenue-banded so small orgs never compare against scale.
- **P6 (Mistakes corrected):** Self-assessment feedback loop allows orgs to dispute or update their data.
- **P7 (Independence):** Zero paid placement, zero vendor influence, zero org-specific prioritization.

