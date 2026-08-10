# AI Governance Framework for Civic & NGO Organizations

**A Reusable, Team-Driven Approach to Responsible AI — Globally**

This framework is designed for teams building civic technology, NGO platforms, and public-benefit AI systems across any country or regulatory context. It's built on the Daanaa project (USA-focused, 2M+ nonprofits) and tested in production. The principles are culture-agnostic and legally replicable.

**Applies to:** Nonprofits, NGOs, charities, social enterprises, community organizations, civic-tech platforms, volunteer networks, grant finders, donation platforms—anywhere trustworthy AI serves public good.

---

## Why This Matters

AI systems operating in civic space—nonprofit discovery, donor privacy, grant matching, volunteer coordination—need governance that is:

- **Structural** (not bolted on after building)
- **Team-enforceable** (not dependent on founder vigilance)
- **Transparent** (auditable by users and peers)
- **Humble** (explicit about uncertainty and limits)

This framework provides that.

---

## The Three-Layer Model

### Layer 1: Constitutional Principles (11 rules that bind everyone)

**Who writes:** Founders + leadership team + community  
**Who approves:** Board or governance body  
**Who enforces:** Automated gates + peer review  
**Change process:** Explicit amendment with rationale logged  

These are your north star. They should be:
- Public and unchanging (or changed explicitly with reasoning)
- Grounded in your mission, not generic ethics
- Tested against edge cases before adopting

**Example (Daanaa):**
- Principle #1: Mission before growth
- Principle #2: Privacy is structural
- Principle #3: Trust signals are evidence-based

### Layer 2: Operational Governance (how decisions are made)

**Who writes:** The team building the system  
**Who approves:** Project leadership  
**Who enforces:** Decision logs + peer review  
**Change process:** Version control, updated as lessons emerge  

This is your decision matrix:
- What decisions require founder/board approval?
- What can the team decide autonomously?
- What needs user or community input?
- How do you handle conflicts?

**Structure:**
```
Decision | Authority | Gate | Documentation
---------|-----------|------|---------------
Public claims | Founder/Board | Yes | DECISIONS.md
Data changes | Team lead | Yes | DECISIONS.md
Code (reversible) | Team | No | Git commit
Architecture | Team lead + tech review | Yes | DECISIONS.md
Spending | Founder/Board | Yes | Finance log
Privacy-touching | Automated gates | Yes | privacy_check.sh
```

### Layer 3: Automated Enforcement (gates that stop bad commits)

**Who writes:** Engineers + security team  
**Who maintains:** The team  
**Who can bypass:** Nobody (by design)  
**Change process:** Pull request + 2 approvals  

These are your technical guardrails. They catch:
- Credential leakage (tokens, keys in code)
- Logging of sensitive data (user behavior, PII)
- Config mismatches (production secrets in dev)
- Boundary violations (data flows that violate principles)

**Example (Daanaa):** `privacy_check.sh` runs on every commit, blocks 8 categories of risk.

---

## Implementation Checklist

### Phase 1: Foundation (Week 1-2)
- [ ] Write 8-12 constitutional principles (board approval)
- [ ] Define your decision matrix (team alignment)
- [ ] Identify automated gates you need (engineer review)
- [ ] Set up DECISIONS.md log (git repository)
- [ ] Draft CONTRIBUTING.md (team norms)

### Phase 2: Integration (Week 3-4)
- [ ] Add pre-commit hooks for privacy gates
- [ ] Add decision log requirement to PR template
- [ ] Document AI autonomy rules (when agents can act)
- [ ] Set up governance audit trail (version control)
- [ ] Run one "constitutional test" scenario

### Phase 3: Scaling (Month 2+)
- [ ] Add peer review for principle-touching code
- [ ] Expand decision log to lessons learned (LESSONS.md)
- [ ] Conduct quarterly principle audit
- [ ] Publish methodology + limitations
- [ ] Build team muscle (decision-making under governance)

---

## Template: 11 Core Principles

Daanaa's 11 principles, as a starting point for your team:

1. **Mission before growth** — Your mission is non-negotiable; everything else serves it
2. **Privacy is structural** — Design for privacy, don't add it after
3. **Trust signals are evidence-based** — Real data only; honest about limits
4. **Fairness to small orgs** — Don't disadvantage by size, resources, or polish
5. **Don't weaponize transparency** — Inform, don't shame or manipulate
6. **Fix mistakes quickly** — Speed of correction > protecting ego
7. **Independence is protected** — No partner influence on core outputs
8. **Don't control funds** — Never be the merchant of record
9. **Decisions are explainable** — Document why you chose what you chose
10. **AI is a tool, not authority** — Humans remain responsible
11. **Principles strengthen over time** — Don't dilute them for convenience

---

## Template: Decision Matrix

```markdown
# Decision Authority Matrix

| Decision Type | Team | Lead | Founder | Board | Gate |
|---------------|------|------|---------|-------|------|
| Architecture | 🟢 Yes | Review | - | - | Design review |
| Algorithm change | 🟡 With lead | 🟢 Yes | Review | - | Tests + DECISIONS.md |
| Public claims | 🔴 No | 🟡 Draft | 🟢 Approve | - | Founder gate |
| Spending >$5K | 🔴 No | 🟡 Request | 🟡 Review | 🟢 Approve | Finance review |
| Data schema | 🟡 With lead | 🟢 Yes | - | - | Automated gates |
| Privacy-touching | 🟡 Code | 🟢 Review | - | - | privacy_check.sh |
| User feedback loop | 🟢 Yes | - | - | - | None (team calls) |
```

---

## Template: Automated Gates

```bash
# privacy_check.sh — runs on every commit

GATES=(
  "1. Credentials: no tokens, keys, passwords"
  "2. Logging: no user IDs, email, payment data in logs"
  "3. Config: no production secrets in code"
  "4. Exfiltration: no data exfiltration vectors (curl to external APIs)"
  "5. Boundaries: data flows match privacy invariants"
  "6. Tracking: no analytics of user behavior without consent"
  "7. Entity firewall: consulting/vendor conflicts separated"
  "8. Invariants: core privacy rules (e.g., 'never store giving history')"
)

# These gates block commits. No bypasses.
```

---

## Template: Decision Log (DECISIONS.md)

```markdown
# DECISIONS.md — Why we chose what we chose

## 2026-08-10: Website Discovery Confidence Threshold (90% vs. 95%)

**Decision:** Set minimum confidence at 90% for discovered websites.

**Reasoning:** 
- 95% would exclude 15% of real sites (too strict)
- 90% balances precision + recall
- Manual review can handle moderate false positives
- Verified by semantic validation (GPU embedding check)

**Rejected alternatives:**
- 99% confidence: Would leave many real sites undiscovered
- 75% confidence: Would require extensive manual review

**Reversibility:** Medium (can re-threshold and re-integrate)

**Affected:** frontend, database schema, discovery_daemon.py

---

## 2026-08-09: Repository Consolidation (42 items vs. 243)

**Decision:** Consolidate root from 243 items to 42 (archive historical docs).

**Reasoning:**
- 180+ root docs = impossible navigation
- Archived docs are still accessible (git history)
- Canonical paths in REPO_MAP reduce token overhead
- New contributors can find answers in <30 seconds

**Reversibility:** High (pure organization, no code changes)

---
```

---

## How to Adapt This for Your Team

### For Civic Tech Platforms
- Add principle: "Small communities deserve equal visibility"
- Add gate: "No algorithmic suppression of minority voices"
- Decision matrix: Give community members veto on public claims

### For Nonprofit Platforms
- Add principle: "Org data is never sold or licensed"
- Add gate: "Donation flows never used for targeting"
- Decision matrix: Nonprofits get 30-day notice before data changes

### For Volunteer Networks
- Add principle: "Volunteer time is never exploited for data"
- Add gate: "No tracking of volunteer availability without consent"
- Decision matrix: Volunteers can audit what's recorded about them

### For Grant Matching
- Add principle: "Algorithms never disadvantage historically underfunded sectors"
- Add gate: "Fairness audit runs before every algorithm change"
- Decision matrix: Community partners review new matching rules

### For Global NGO Networks
- Add principle: "Organizations in all regions treated with equal dignity (not biased toward Global North)"
- Add gate: "Fairness audit includes geographic representation, language accessibility, local expertise"
- Add principle: "Local regulatory compliance is non-negotiable (GDPR, local data laws, etc.)"
- Gate: Automated check against all jurisdictions where data is stored or accessed
- Decision matrix: Legal review required for cross-border data flows

### For NGOs in Restrictive Contexts
- Add principle: "Platform cannot be weaponized against vulnerable populations"
- Add gate: "Audit against use-by-bad-actors (if data leaked, does it harm activists, minorities, dissidents?)"
- Decision matrix: Leadership approves any feature that increases surveillance or tracking
- Data policy: Clear retention limits (what we delete, on what schedule)

### For International Donor Platforms
- Add principle: "No donor data crosses borders without explicit consent"
- Add gate: Automated check that data storage matches donor jurisdiction
- Decision matrix: Different privacy rules for GDPR regions, CCPA regions, and countries without strong data law
- Extra principle: "Donors in restrictive countries can give anonymously, always"

---

## Staffing for Governance

You don't need a compliance department. You need:

1. **One engineer** (40% time): Maintains gates, reviews privacy-touching code
2. **One decision-keeper** (part-time): Logs decisions, facilitates governance meetings
3. **Your team** (continuous): Asks "does this violate a principle?" before shipping

That's it. The rest is culture and discipline.

---

## Measuring Success

✅ **Good signs:**
- Decisions are logged before shipping (DECISIONS.md is up-to-date)
- New team members ask "which principle does this touch?" without prompting
- Gates catch actual problems (not false positives)
- Principles survive a conflict (team honors them even when inconvenient)
- Users understand what data is/isn't collected

❌ **Warning signs:**
- DECISIONS.md is stale
- "We'll document it later" becomes default
- Gates are bypassed regularly
- Principles are mentioned but not enforced
- Users are surprised by what data is collected

---

## Templates You Can Copy

- **STEWARDSHIP.md** — Constitutional principles (Daanaa example)
- **CLAUDE.md** — Operating agreement for builders
- **governance/DECISIONS.md** — Decision log template
- **governance/LESSONS.md** — What broke and how we fixed it
- **institution/AUTONOMY_FRAMEWORK.md** — When AI agents can decide
- **privacy_check.sh** — Automated gates (bash, hackable)

All are in this repo. Use them.

---

## Open Questions (for your team to answer)

1. **Who owns the principles?** (Board? Founders? Community vote?)
2. **When do principles change?** (Unanimity? 2/3 vote? Founder veto?)
3. **What does "independence" mean in your context?** (No corporate sponsors? No VC funding? Something else?)
4. **How do you handle principle conflicts?** (E.g., privacy vs. transparency)
5. **Who has final say on reversibility?** (Can team agree a change is reversible, or does founder decide?)

**These are not abstract.** Answer them before your first conflict arises.

---

## Legal & Regulatory Adaptation by Region

### Europe (GDPR, DPA, local data laws)
- Add gate: "Data controller agreements reviewed before every data sharing"
- Add principle: "Data minimization—collect only what's necessary"
- Decision matrix: Legal review required for cross-border transfers
- Extra: Right to be forgotten must be technically enforced (not just promised)

### Global South (limited infrastructure, varied regulation)
- Add principle: "Platform must work on slow internet and basic devices"
- Add gate: "Every feature tested on 2G/3G connection"
- Decision matrix: Government request procedures (transparency + legal challenge)
- Extra: Consider offline-first design (sync when possible, work without internet)

### Asia-Pacific (varied regulatory landscape)
- Add principle: "Compliance with local NGO registration laws"
- Decision matrix: Different data residency rules per country
- Gate: Automated check that data doesn't leave jurisdiction unless required
- Extra: Language localization not just translation

### Middle East & North Africa
- Add principle: "Platform cannot discriminate by gender, religion, political affiliation"
- Gate: Bias audit by local experts before feature launch
- Decision matrix: Leadership approval for any feature that could expose vulnerable groups
- Extra: Anonymous donation option, always

### Americas (Brazil LGPD, Canada PIPEDA, etc.)
- Add gate: "Compliance check against each jurisdiction's data law"
- Decision matrix: Varied consent mechanisms per region
- Extra: Transparency requirements vary—document each jurisdiction's rules

### Africa (varied infrastructure and regulation)
- Add principle: "Data benefits the continent, not extracted to elsewhere"
- Decision matrix: Local data storage required, clear retrieval rights
- Gate: Annual audit that data flows serve local organizations first
- Extra: Offline functionality, SMS support, feature prioritization for actual users

---

## Questions to Answer for Your Context

**Legally:**
- What data law applies to us? (GDPR? Local law? Multiple?)
- Do we need local data residency?
- What are the government request procedures in each country?
- What's our legal liability model (nonprofit vs. for-profit vs. cooperative)?

**Operationally:**
- What languages do our users speak?
- What infrastructure (internet, electricity) can we rely on?
- What risks exist if data leaked? (Could it harm activists, minorities, government critics?)
- What's our contingency if government demands data?

**Culturally:**
- What does "privacy" mean in our context? (Individual? Family? Community? Collective?)
- What does "trust" require? (Transparency? Personal relationships? Authority?)
- What decision-making style fits our culture? (Consensus? Authority? Community vote?)
- How do we involve local experts (not just imported frameworks)?

---

## Getting Help

- **Daanaa's implementation:** [governance/DECISIONS.md](../governance/DECISIONS.md), [STEWARDSHIP.md](../STEWARDSHIP.md)
- **Peer governance frameworks:** See institution/library/
- **Privacy gates template:** [institution/PRIVACY_GATES.md](../institution/PRIVACY_GATES.md)
- **Global NGO context:** [TEAM_STORY.md](../TEAM_STORY.md) — read "Daanaa is just a platform in US..."
- **Question for your team:** Open an issue on this repo; include your country/context

---

## License & Reuse

This framework is part of Daanaa and governed by the Founding Stewardship Commitment.

**You can:**
- Adapt it for your nonprofit/civic project
- Cite it and improve it
- Build your own 11 principles on this model
- Use the decision matrix template

**Please:**
- Don't claim this as your invention
- Link back to Daanaa
- Share improvements (open a pull request)

**Your principles belong to your team**, not to us. Own them.

---

**Built by:** The Daanaa team (Akbar, Claude, community contributors)  
**Last updated:** August 2026  
**Status:** Production-tested, team-proven
