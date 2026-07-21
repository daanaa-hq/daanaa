# Mission Lock — Non-Negotiable Principles

**Status:** Permanent. Changes require unanimous advisor circle + 30-day notice + CEO + filing amendment.

These principles are encoded in:
1. LLC operating agreement (when MeritGiving LLC forms)
2. Root `CLAUDE.md` (every Claude session inherits)
3. Every department's `DEPT.md` (operationalized into agent behavior)
4. Public `meritgiving.org/about` page (visible to everyone)

---

## Principle 1: MERIT never holds donor money in Phase 0

We do not custody, route, or process donations. Phase 0 donate buttons link OUT to nonprofit-owned pages. Our own tip jar (Stripe Payment Link) is clearly a service tip to support EcoMargins/MeritGiving operations, not a charitable donation.

**Why this matters:**
- Removes single largest liability category
- Removes need for money transmitter licenses (50 states)
- Removes PCI compliance burden
- Builds trust: we have no incentive misalignment

**Phase 2 reconsideration:** Even at Phase 2 scale, if we ever route donations, they go through partners (e.g., Give Lively with webhook only). We never custody.

---

## Principle 2: MERIT treats all 501(c)(3)s equally

Regardless of cause, religion, politics, geography, or size. Same data, same scoring rules, same visibility.

**Why this matters:**
- Trust requires neutrality
- The IRS already determines who's a 501(c)(3); we don't second-guess
- Bias accusations would be devastating; structural neutrality prevents them
- Sector trust depends on us being seen as fair infrastructure

**What this means:**
- No cause-based exclusion or de-prioritization
- No "approved cause" lists
- No editorial preference in directory ranking
- Ranking only on deterministic scoring rules (badges)
- If we ever publish a sector report critical of a specific cause area, it's data-driven and reviewed by advisor circle

---

## Principle 3: MERIT data is sourced from IRS public records

Private data stays private. We never enrich from non-public sources. We never sell donor or nonprofit data.

**Why this matters:**
- Privacy by architecture, not policy
- No data licensing temptation creates moral hazard
- Auditability: anyone can verify our data source
- Compliance: GDPR-style data minimization by default

**Approved sources:**
- IRS Exempt Organizations BMF (Public Domain U.S. Government)
- IRS Form 990 filings via ProPublica (CC BY-NC-ND 3.0 US, attributed)
- NCCS harmonized files (when applicable, attributed)
- Self-reported corrections from verified claimants (in Phase 1+, layered as metadata)

**Forbidden sources:**
- Web scraping of nonprofit-controlled sites without explicit permission
- Social media scraping
- Third-party data brokers
- Donor information from any source

---

## Principle 4: MERIT never charges nonprofits for core services

Profile listing, directory inclusion, donate button placement, claim verification, basic support, badge calculation — all free. Forever. For all nonprofits.

**Why this matters:**
- The "invisible majority" can't afford to pay; charging excludes them
- Pay-to-be-visible is a perception risk and mission betrayal
- Funder thesis depends on this — they fund infrastructure, not gatekeeping

**Sustainability model:**
- Tips from donors and supporters (Phase 0+)
- Sponsorships from mission-aligned tools/services (Phase 1+)
- Foundation grants (Phase 2+)
- GPO marketplace vendor referral fees (Phase 2+, transparent, no payola)

**What we will NEVER charge for:**
- Profile listing or visibility
- Verification
- Donate link inclusion
- Basic data access via public API
- Badge calculation
- Inclusion in sector reports

---

## Principle 5: MERIT publishes transparently

Build-in-public. Public risk register. Public methodology. Public ADRs (with sensitive details redacted). Public sector reports.

**Why this matters:**
- Transparency compounds trust over time
- Forces us to make good decisions (others are watching)
- Builds audience naturally
- Differentiates from opaque incumbents

**Where transparency applies:**
- Build progress (weekly log)
- Decision-making (ADRs published)
- Risk awareness (public risk register)
- Data methodology (full algorithm documentation)
- Finances (annual public summary)
- Operations (status page, postmortems)

**Where it doesn't:**
- Individual donor data (always private)
- Claimant personal information
- Pre-disclosure security vulnerabilities
- Personnel matters
- Specific advisor discussions
- Active legal matters

---

## Principle 6: MERIT acknowledges its limits

We are not lawyers, accountants, regulators, or fundraising consultants. We don't pretend to be. We surface IRS data; we don't enforce. We provide infrastructure; we don't advise.

**Why this matters:**
- Liability protection by clarity
- Trust requires honest scope
- Defers to professionals on regulated matters

**Standard disclaimers:**
- "This is not legal/tax/financial advice"
- "Consult a qualified professional"
- "MERIT does not verify legal authority to represent an organization"
- "Data displayed reflects IRS records as of [date]"

---

## Principle 7: MERIT defers to professionals on regulated matters

Attorney for legal. CPA for tax. Insurance broker for risk. Security professional for vulnerability response. No exceptions.

**Why this matters:**
- We're solo + AI; we're not licensed professionals
- Mistakes in regulated areas have outsized consequences
- Cost of professionals is far less than cost of errors

**When to engage:**
- Quarterly: attorney consultation
- Quarterly: CPA review
- Annually: insurance review
- On-demand: anything in escalation rules

---

## Principle 8: MERIT prioritizes long-term trust over short-term growth

We will NOT take actions that boost short-term metrics at the cost of long-term sector trust. We will NOT use dark patterns, growth hacks that mislead, or shortcuts that erode credibility.

**Why this matters:**
- We're building civic infrastructure, not a startup MAU chart
- Trust is the only durable competitive advantage
- One bad incident sets us back years

**Tradeoffs we will make:**
- Slower growth for cleaner attribution
- Smaller audience for better-quality audience
- Lower revenue for higher mission alignment
- Less convenience for more privacy

---

## What this means in practice

When any decision is contested, ask:

1. Does this honor mission lock?
2. Does this prioritize long-term trust over short-term growth?
3. Could this be perceived as unfair, opaque, or self-serving?
4. Would I be comfortable explaining this in a sector report?

If any of those raises concern, **the answer is no, even if it's tactically convenient.**

This is the contract MERIT makes with the nonprofit sector and with donors. It's also the contract Akbar makes with himself. The system protects it.
