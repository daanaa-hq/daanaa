# MERIT Moats

**What makes this defensible? What can't an incumbent or a copycat easily replicate?**

---

## Moat 1: Privacy Architecture

**What it is:** Privacy isn't a policy at MERIT — it's a design constraint. The data model is built so that even MERIT cannot violate donor privacy. Giving wallet data is client-side or per-user encrypted. Donor identity is not aggregated. The system literally cannot do what privacy-violating competitors do.

**Why this is a moat:**
- Charity Navigator and Candid have business models that depend on aggregated donor/donation data
- They can't pivot without disrupting their existing revenue
- Re-architecting an existing system for privacy-by-default takes years
- The deeper they get into data-monetizing positions, the more switching costs they have

**How we protect it:**
- Mission lock principle 3 (IRS data only) in LLC operating agreement
- Architecture documented publicly
- External privacy audit at Phase 2

---

## Moat 2: GPO Vendor Ecosystem (Phase 2+)

**What it is:** A curated marketplace where mission-aligned vendors offer favorable terms to MERIT-listed nonprofits in exchange for vetted access. Networks effects compound:
- More nonprofits → more attractive to vendors
- More vendors → more attractive to nonprofits
- Better deals → harder to leave
- Aggregate cost savings → measurable impact for funders

**Why this is a moat:**
- Network effects are durable
- Charity Navigator can't build this — they're a rating service, not infrastructure
- Candid is closer but their business model conflicts (they sell data to vendors, opposite direction)
- Building takes time + trust; can't be shortcut

**How we build it (Phase 2):**
- Start with 3 mission-aligned vendors in narrow categories (payments via Give Lively, password mgmt via 1Password, similar)
- Transparent terms; published publicly
- Measured savings tracked per nonprofit
- Vendor agreement template (attorney-drafted) prevents pay-to-play

---

## Moat 3: Deterministic Transparent Scoring

**What it is:** Every MERIT badge is calculated by published rules, on IRS-public data, with full provenance. Anyone can audit. Anyone can replicate the score themselves.

**Why this is a moat:**
- Charity Navigator and Candid use proprietary scoring — opaque, contested
- When nonprofits dispute opaque ratings, raters lose credibility
- MERIT's open methodology builds trust faster than secrecy
- Once nonprofits trust the methodology, switching to opaque alternatives feels regressive

**How we protect it:**
- All scoring rules in public `meritgiving.org/methodology` page
- Open-source the scoring engine (Phase 1)
- Public errata when bugs found
- Versioned rules with change log

---

## Moat 4: Mission Lock

**What it is:** Non-negotiable principles encoded in LLC operating agreement, with amendment requiring unanimous advisor circle + 30-day notice + filing. Effectively makes MERIT unable to drift even under acquisition pressure or founder change.

**Why this is a moat:**
- Funders trust mission-lock orgs more
- Nonprofits trust mission-lock orgs more
- Talent (future contractors, advisors) prefers mission-lock
- Acquirers either accept the lock (low likelihood) or walk away (preserves mission)

**How we protect it:**
- Drafted into operating agreement by attorney
- Public commitment on `meritgiving.org/about`
- Annual public verification
- Advisor circle has veto on amendment attempts

---

## Adjacent moats (build over time)

### Moat 5: Build-in-Public Credibility
Two years of weekly build logs, transparent ADRs, honest failure reports — this creates a track record that opaque competitors cannot fabricate. Compounds slowly but durably.

### Moat 6: Sector Relationships
Advisor circle, sector journalist relationships, conference speaking, citation in nonprofit press. These are individual relationships that take years to build and don't transfer.

### Moat 7: Data Currency
Monthly IRS BMF refresh + verified self-correction layer means MERIT data is fresher than any incumbent. Trust compounds; users come back when accuracy is felt.

### Moat 8: Identity Verification Track Record
After 1,000+ verified claims with zero successful fraud, MERIT's verification process is itself a trust signal. Competitors entering Phase 1-equivalent must start from zero.

### Moat 9: Open Data Initiative
Free public API + monthly data drops creates a developer ecosystem that builds on MERIT. Once civic-tech projects integrate, switching cost is high.

### Moat 10: Cost Structure
AI-augmented one-person org with mission-aligned vendor credits = burn rate < $300/mo possible. Incumbents have headcount. Even small competitors have hiring obligations. MERIT can survive lean indefinitely.

---

## What is NOT a moat

Things that look defensive but aren't:

- **Domain name:** meritgiving.org is good but replaceable
- **First-mover in directory:** Candid was first; we're better, not first
- **Tech stack:** Next.js, Postgres, Stripe — all commodity
- **Founder personality:** Akbar is essential to current MERIT but the system shouldn't depend on irreplaceable individual
- **Newsletter list:** Audience matters but transfers; not durably defensible
- **Specific badge designs:** Cosmetic, copyable

We don't lean on any of these as defenses. We build the real moats above.

---

## Defensive timing

**Year 1:** Moat 1 (Privacy Architecture) and Moat 4 (Mission Lock) are foundational. Build them right.

**Year 2:** Moat 3 (Transparent Scoring) and Moat 5 (Build-in-Public) compound. Maintain discipline.

**Year 3:** Moat 6 (Sector Relationships) and Moat 8 (Verification Track Record) emerge. Invest deliberately.

**Year 4+:** Moat 2 (GPO Ecosystem) and Moat 9 (Open Data) start producing returns. Lean in.

---

## What would break our moats

Honest threats to watch for:

1. **Mission drift under funding pressure** → Mitigated by Moat 4 (Mission Lock)
2. **Acquisition by incumbent** → Mitigated by Moat 4 + advisor veto
3. **Founder burnout** → Mitigated by operating rhythm + Year 2+ contractor support
4. **Privacy breach incident** → Mitigated by Moat 1 architecture + insurance
5. **Sector politics (taking a "side" inadvertently)** → Mitigated by Principle 2 (equal treatment)
6. **Funder concentration** → Mitigated by diversified portfolio (no funder > 40%)
7. **Regulatory change** → Monitor via legal-lead; adapt

Each is a known threat with a planned response.
