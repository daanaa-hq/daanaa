# Credit Applications — Daanaa / EcoMargins LLC

Single source of truth for startup credit applications.
Agent-drafted, human-approved, human-submits (web forms require a logged-in browser session).

**Status key:** ☐ not started · ⏳ drafted · ✅ submitted · 🎉 approved

---

## Master blurb (paste-adaptable for any form)

> Daanaa (daanaa.org) is a civic nonprofit-discovery platform that indexes 1.8 million
> IRS-registered 501(c)(3) organizations — the vast majority of which have no online
> presence, no mission statement, and no way for donors to find them. We call them the
> invisible 97%. Daanaa uses AI to generate mission descriptions, score organizations on
> peer financial context, and surface them through a searchable, privacy-first directory.
> No user accounts, no tracking, no data sold. A donor's giving record lives only on
> their device. The platform is built and operated by a single founder using AI agents
> for engineering, data pipelines, and operations — a direct demonstration that one
> person plus AI can build civic infrastructure at scale.

**One-liner:** Daanaa makes 1.8M invisible nonprofits findable — AI-powered, privacy-first, solo-built.

**Impact framing:** Every nonprofit that gains a mission statement, a donor signal, or a
verified donate link is a real organization that can now be found and supported. At current
pipeline velocity (500K+ missions generated), the platform is already changing discovery
outcomes for organizations that had zero online presence before.

---

## 1. Anthropic — API Credits

**Status:** ⏳ Submitted 2026-06-01
**Why first:** Fixes the starved Haiku key. Daytime mission generation resumes.
**Apply at:** anthropic.com/startups (or the "Contact sales" / credits form)
**Account to use:** accounts@daanaa.org
**GitHub:** github.com/daanaa-hq/daanaa

### Application answers

**Company name:** Daanaa (operated by EcoMargins LLC)
**Website:** daanaa.org
**What does your product do?**
> Daanaa is a civic nonprofit-discovery platform. We index 1.8 million IRS-registered
> nonprofits and use Claude (Haiku) to generate 1–2 sentence mission descriptions for
> organizations that have none — making them discoverable for the first time. The
> platform is privacy-first: no user tracking, no accounts, device-only giving records.

**How are you using the Anthropic API?**
> We use Claude Haiku for batch mission generation across ~650,000 scored nonprofits
> that currently have no mission statement. Each call generates a 1–2 sentence
> plain-language description grounded in the organization's IRS NTEE category, name,
> and location. Missions are labeled "AI · beta" in the UI and can be overridden by
> the org when they claim their page. We also use Claude for data quality review and
> lightweight classification tasks in the pipeline.

**Stage / funding:**
> Pre-revenue, bootstrapped. Solo founder. Live platform with real data and growing
> organic traffic.

**Monthly API spend estimate:** ~$50–200/month at scale (Haiku batch pricing)

---

## 2. Google for Startups — Cloud Credits

**Status:** ☐
**Why:** GCP credits cover hosting migration if/when we move off the local server.
**Apply at:** cloud.google.com/startup
**Account to use:** accounts@daanaa.org

### Application answers

**Company description:**
> (Use master blurb above)

**What Google Cloud products will you use?**
> Cloud Run or Compute Engine (API hosting), Cloud SQL (SQLite → Postgres migration),
> Cloud Storage (IRS/NCCS data archives), Vertex AI (optional future embedding pipeline).

**Stage:** Pre-revenue, bootstrapped, live product.

---

## 3. AWS Activate — Cloud Credits

**Status:** ☐
**Why:** $5K–$100K credits. Useful for S3 (IRS data), EC2 if server moves to cloud.
**Apply at:** aws.amazon.com/activate
**Account to use:** accounts@daanaa.org

### Application answers

**Company description:**
> (Use master blurb above)

**How will you use AWS?**
> S3 for IRS/NCCS bulk data archives and pipeline staging. EC2 or ECS for API hosting.
> RDS if migrating from SQLite. Lambda for lightweight pipeline triggers.

**Stage:** Pre-revenue, bootstrapped, solo founder, live product at daanaa.org.

---

## 4. Microsoft for Startups — Azure + GitHub Copilot

**Status:** ☐
**Why:** $150K Azure credits + free GitHub Copilot (useful for solo dev).
**Apply at:** startups.microsoft.com
**GitHub:** github.com/daanaa-hq/daanaa
**Account to use:** accounts@daanaa.org

### Application answers

**What does your startup do?**
> (Use master blurb above)

**How will you use Azure?**
> Azure Blob Storage for data archives. Azure Functions for pipeline scheduling.
> Potentially Azure AI for future embedding workloads.

---

## 5. GitHub for Startups

**Status:** ☐
**Why:** Free GitHub Team plan ($4/user/mo saved), plus partner perks.
**Apply at:** github.com/startups
**GitHub org:** github.com/daanaa-hq
**Account to use:** accounts@daanaa.org

### Application answers

**What does your startup do?**
> (Use one-liner: "Daanaa makes 1.8M invisible nonprofits findable — AI-powered,
> privacy-first, solo-built.")

**Stage:** Pre-revenue, bootstrapped.

---

## 6. Stripe Atlas / Stripe partner perks

**Status:** ☐
**Why:** Stripe partner credits + discounts. Useful when donate-link payment flows are needed.
**Note:** Daanaa never handles funds directly — but EcoMargins B2B side (ESG SaaS) will.
**Apply at:** stripe.com/atlas (or partner perk page via Atlas)
**Account to use:** accounts@daanaa.org

---

## Submission order (recommended)

**Reality check (researched 2026-06-01):** As a bootstrapped, pre-revenue, solo-founder
startup with no outside funding, we qualify for the *entry tiers* of each program. The
larger tiers ($150K Azure, $350K GCP) gate on investor backing — open later if we raise.
**GitHub for Startups** is skipped: it requires a partner affiliation AND outside
funding (we have neither).

1. **Anthropic Startup Program** — $25K–$100K credits, Airtable form, ~2 wk rolling review. Fixes Haiku pipeline if approved
2. **Google Cloud bootstrap tier** — $2K credits explicitly for "not yet backed with startup equity funding", ~3–5 day review
3. **Microsoft Founders Hub** — $1K initial → $5K after business verification, self-serve, no validation needed
4. **AWS Activate (Builders)** — $1K–$10K self-serve tier
5. **Stripe** — when B2B revenue track starts (later)

⏭️ **GitHub for Startups** — skip until we raise or get a partner affiliation

---

## Agent handoff notes

- Agent drafts all blurbs (done above).
- Founder reviews this doc, approves, then opens each URL and pastes.
- Agent cannot click Submit or complete OAuth login — those are founder actions.
- After submission, forward any confirmation emails to the inbox agent
  (orgs@/hello@) and it will track status and flag follow-ups.
- Target: all 5 core applications submitted in one sitting (~30 min).
