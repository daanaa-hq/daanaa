# Daanaa — Mozilla Foundation Application (ADAPTED)

**Funder:** Mozilla Foundation (Internet Health, Trustworthy AI)
**Focus:** Open internet infrastructure; trustworthy AI; civic participation
**Award:** $50K–$200K+
**Deadline:** [Verify current program deadline]

---

## The Problem (Mozilla Angle)

### The Internet Health Crisis in Philanthropy

The internet was supposed to democratize information. But philanthropy—where billions in civic resources flow—remains opaque.

**The breakdown:**
- 1.9M nonprofit organizations exist
- But discovery is controlled by brand halo (large orgs dominate)
- Nonprofit financial data *is public* (IRS 990s) but *is fragmented* (50 databases, no standards)
- AI-driven "nonprofit ratings" platforms are emerging (proprietary, black-box, extractive)
- Donors have no open-source, transparent way to access public data + make informed decisions

**The risk:** Without transparent infrastructure, AI will fill the gap with proprietary black-box solutions. Donors will trust algorithmic rankings instead of facts. Small organizations will be further marginalized.

**This is an internet health problem:** Information infrastructure should be open, transparent, and respect human agency. Philanthropy needs that infrastructure.

---

## The Opportunity: Open Infrastructure for Civic Information

Mozilla funds trustworthy technology for the open internet. Daanaa is that infrastructure for philanthropy.

**What we do:**
- Build an **open data platform** for nonprofit financial transparency
- Use **local AI** (not cloud-dependent, not proprietary) for benchmarking
- Provide **tools for human agency** (discovery, context, facts—not rankings or nudges)
- Keep **data open** and methodology transparent

**Why Mozilla should care:**
1. **Open internet principles apply to philanthropy.** Public data should be accessible, not locked in proprietary platforms.
2. **Trustworthy AI matters here.** If nonprofits are benchmarked, it should be via transparent methodology, not black-box ML.
3. **Human agency is critical.** Donors should decide, not algorithms. Information infrastructure should enable choice, not influence it.

**Current state:**
- 1.97M nonprofits indexed
- Methodology is public + reproducible
- Local AI (Qwen2.5-32B) instead of cloud APIs
- Zero proprietary black-box models
- Platform live and operational

---

## The Trustworthy AI Angle

**Daanaa demonstrates trustworthy AI in practice:**

### How We Use AI (Responsibly)

1. **Mission generation** (Qwen2.5-32B, local)
   - Generates 1–2 sentence org description from IRS data
   - Reviewed before surfacing
   - Fails openly (shows "no description available" if uncertain)
   - Not used for trust signals or rankings

2. **Financial benchmarking** (deterministic, not ML)
   - Scores derived from IRS data (revenue, expenses, efficiency ratios)
   - Methodology is published and reproducible
   - No black-box ML models predicting "goodness"
   - Clear peer groups (NTEE code + revenue band) = fair comparison

3. **Semantic search** (embedding-based, local)
   - Helps donors find causes they care about
   - Transparent ranking (relevance only, not quality judgment)
   - User controls the query

### Why This Matters

**The contrast:** Proprietary nonprofit rating platforms (Charity Navigator, GiveWell) use proprietary scoring, black-box algorithms, and top-down judgment.

**Daanaa:** Open methodology, local compute, transparent peer groups, human agency.

**For Mozilla:** This is what trustworthy AI looks like in civic infrastructure. Transparent. Local. Respectful of human choice.

---

## The Open Internet Principle

**Mozilla believes information should be open.** So does Daanaa.

**What we do:**
- All methodology published (METHODOLOGY.md)
- IRS data is public; we organize and surface it
- No proprietary models; all code is auditable
- Peer groups are clear (not algorithmic black boxes)
- Data is accessible (via API, bulk download, search)

**What we don't do:**
- Lock data behind a paywall
- Use proprietary scoring as a black box
- Accept funding that compromises transparency
- Influence outcomes based on funder relationships

---

## The Business Model: Sustainable Open Infrastructure

We remain free for nonprofits and donors. Funded by:

1. **Grants** (like Mozilla) — Core infrastructure development
2. **Partnerships** (ethical, transparent) — Community partners offer tools at discounts; we earn referrals
3. **Services** (optional) — Group purchasing for nonprofits, not funded by donations

**We will never:** Sell data, accept paid placement, use proprietary AI to rank organizations, or compromise independence.

---

## 12-Month Impact (For Mozilla)

- **Open data infrastructure** live and operational (1.97M nonprofits indexed)
- **Trustworthy AI case study** (transparent methodology, local compute, human agency)
- **Partnership model** demonstrating how open platforms can be sustainable
- **Community adoption** (500K+ nonprofits claimed, 50K+ donors engaged)

---

## Why Mozilla, Why Now

1. **Trustworthy AI is urgent.** Without open-source alternatives, proprietary platforms will dominate. This is a moment to fund transparent infrastructure.

2. **Open internet principles apply to civic tech.** If Mozilla funds health, climate, and rights—it should fund transparent civic information infrastructure too.

3. **AI governance is being decided now.** By demonstrating that trustworthy, transparent AI works in practice, we shape expectations for what "good" looks like.

---

## The Stewardship Commitment (Why This Matters to Mozilla)

Daanaa operates under **11 founding principles** (see STEWARDSHIP.md):

- **Independence protected** — No funder influences results
- **Evidence-based trust signals** — Only public data, transparent methodology
- **AI as tool, not replacement** — Humans make decisions; AI handles data engineering
- **Privacy by default** — No donor tracking, no data extraction
- **Mistakes corrected openly** — Public correction registry

**For Mozilla:** This is open-source thinking applied to nonprofit governance. Principles > funding pressure.

---

## Architecture & Local Compute

**Why we built this way:**

1. **Local AI (Qwen2.5-32B on Ryzen server)** — No cloud dependency, no API lock-in, transparent inference
2. **SQLite + FAISS** — Lightweight, auditable, no enterprise database vendor lock
3. **Open-source stacks** — No proprietary dependencies
4. **Reproducible methodology** — Anyone can verify our scores using public data

**For Mozilla:** This is how open infrastructure should be built.

---

## Budget & Use of Funds

**Total ask:** $[X]

- Infrastructure: Local servers, data pipelines, open-source dependencies
- Attorney: Legal structure protecting independence + data governance
- Product: Peer benchmarking, trustworthy AI case studies, open APIs
- Community: Nonprofit onboarding, donor education, transparency reporting

**Execution:** Founder + AI agents (lean, mission-first)

---

## Appendices (To Attach)

- Founding Stewardship Commitment (full)
- Open methodology documentation
- Trustworthy AI case study (mission generation + benchmarking)
- Data governance + privacy architecture
- Local compute infrastructure (server specs, reproducibility)
- Open-source dependencies (license audit)
- API documentation (public access)
