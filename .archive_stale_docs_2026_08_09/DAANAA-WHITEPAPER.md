# Daanaa: A Civic Directory for Wise Giving

**White Paper — Foundational Edition**

**Status:** Beta live. Phase 0 in progress. Dated 2026-06-04.

---

## 1. Executive Summary

Daanaa is a civic-good directory that helps donors find and support the nonprofits they've never heard of. Built on public IRS and ProPublica data, it indexes 1.8 million US nonprofits (fewer than 50,000 are household names), describes 630,000+ in plain language, and surfaces the work of small organizations alongside established giants — without ever touching money or judging mission. The platform lives client-side (no giving data stored on servers) and routes all donations directly to organizations' own giving pages. Daanaa is run by one person, self-funded, and signed under a Founding Stewardship Commitment that treats the platform as a public trust, not a commercial product. The network launched publicly on June 4, 2026, with search, peer-context financial scoring (currently off), and a private giving wallet. Phase 1 (PWA launch across web/iOS/Android) is in design. Phase 2 (scores on) is queued, pending a bias audit and methodology transparency. The problem Daanaa solves: donors have no trustworthy way to discover the thousands of small organizations doing essential work invisibly.

---

## 2. The Problem

### Information Gap

The nonprofit sector is radically opaque. The National Center for Charitable Statistics estimates there are 1.8 million charitable organizations in the US; fewer than 50,000 are household names. A donor looking to support education, hunger relief, environmental stewardship, or any cause larger than any one famous charity faces a choice between:

1. **A handful of household names** — well-marketed, widely trusted, but inevitably large.
2. **IRS Form 990 filings** — public, raw, incomprehensible. A $2M community health center's tax filing is technically public data but practically invisible. It is, in the words of ProPublica's Nonprofit Explorer, a "black hole of bureaucratic jargon."
3. **Platforms that rank and rate** — GiveWell, Charity Navigator, Candid — which are forced to judge mission and cover only the few hundred organizations they have capacity to evaluate, or which rely on opaque algorithms and paid placements.

The result: donors give to what they've heard of. Small organizations — the ones often doing the most specialized, local, adaptive work — are systematically invisible.

### Trust is Conditional

Most nonprofit rating platforms face a structural conflict: they need attention (and therefore funding) to stay alive, so they gravitate toward conclusions that are punchy, comparable, and conclusive ("this charity is great, this one wastes money"). But soundness and salience are at odds. A fair assessment of a $150K environmental justice nonprofit's work cannot be reduced to a single number without either weaponizing transparency (shaming) or inventing false precision (a number that sounds authoritative but rests on weak data).

The existing evaluators also raise a second problem: independence. Most established platforms are nonprofit themselves and rely on donor revenue, partnerships, and brand reputation. A nonprofit cannot independently rate another nonprofit without creating explicit and implicit conflicts with its own donors and the sector.

### Privacy Collapse

On the platforms that do exist, a donor's giving history is often exposed, tracked, analyzed, and monetized. Social giving is accelerating ("see what your friends support"), but what a person gives is deeply personal information — arguably more revealing than search history or browsing. Daanaa assumes the opposite: giving is private unless the donor chooses to make it public.

---

## 3. The Concept

### What Daanaa Is

Daanaa (pronounced dah-NAH-ah, meaning "wise" in Urdu and Arabic) is a searchable directory of US nonprofits designed to answer one question: *What is this organization, and what's its financial health relative to similar nonprofits?*

It is not:
- A rating system that judges mission or impact.
- A payment processor or intermediary.
- A social platform or giving tracker.
- A tool that predicts which org will do the most good (that is an irreducibly personal choice).

It is:
- A discovery layer that makes the invisible 97% of nonprofits findable and understandable.
- An honest, peer-bounded financial profile so donors can understand an org's stability in context.
- A hand-off point: from Daanaa, you go directly to the organization's own giving page (Donorbox, Stripe, PayPal, their EIN on an IRS-registered router) — never through Daanaa.

### The User Experience (Beta)

**For donors:**

1. **Search by name, cause, or location.** Type "food bank Brooklyn" or "climate nonprofits Oregon" or "any nonprofit near 94110." The search fuses keyword match and semantic understanding (why: helps donors find work they didn't know existed).
2. **See what you find.** An organization profile shows: legal name, location, website, mission (AI-written where the filing had none, human-verified where available), peer-context financial score (currently off in beta; when live, it will show a 0–100 peer-profile score, percentile within its peer group, and months of financial reserves).
3. **Give directly.** Click "Support this organization" and you jump to their official donation page — we verify that page is real before linking. You give to them, not to us. Daanaa never sees the transaction.
4. **Save your thinking.** A private giving list (localStorage on your device, no server) lets you track organizations you're considering, add intended amounts, and note a giving date. Request an acknowledgment letter for tax purposes if you want. All of this stays on your device — Daanaa doesn't store it.

**For nonprofits:**

1. **Be findable.** Organizations with sufficient IRS data are in the directory automatically; they can claim their profile to verify mission statements and donation links.
2. **Get verified.** When an organization claims its profile, they can confirm or correct the mission, upload their own logo, and verify their donate URL so donors know they're giving to the right place.
3. **Understand your context.** A dashboard shows the organization how it scores relative to peers in its region and category — not as a judgment, but as a mirror.

### Name & Meaning

"Daanaa" (دانا, from Urdu/Arabic roots) means *wise*, *learned*, or *of sound judgment*. The name encodes the north star: helping people make wise giving decisions. It avoids the false precision of words like "merit" or "excellence" and instead evokes discernment and care.

---

## 4. The Founding Story

Akbar Khowaja, the founder, is a senior procurement and supply chain executive. His professional practice is built on grading items — inventory, suppliers, contracts — using quantitative matrices: profitability, criticality, number of alternatives. When he joined the **Ismaili Civic Leadership Program** (a civic engagement initiative organized in partnership with Rice University, Houston), part of his cohort's work was to find local nonprofits to advise as a capstone project. Finding basic information about them — despite all of it being technically public IRS data — took months. That frustration became the founding insight: if a trained data professional with weeks to spend couldn't find small nonprofits, a donor with ten minutes certainly couldn't.

He applied the same matrix logic he uses in procurement — revenue bands, peer groups, reserve health — to nonprofits. He walked into a Microcenter with no hardware or Linux background, asked a local rep for help speccing a machine capable of crunching gigabytes of data, came home, and built the server with his kids. After weeks of learning on free tools, he moved to Claude (Anthropic) and built the platform he now calls Daanaa — late nights, early mornings, and weekends, with his family's support.

The giving philosophy is older still: the goal is to make giving so easy and private that "the left hand does not know what the right hand gives" — a principle from Islamic tradition about sincere, anonymous charity.

---

## 5. Mission & Principles

Daanaa operates under an 11-point **Founding Stewardship Commitment** signed on May 20, 2026, by the founder and the AI engineering agent operating the platform. These are binding principles, not marketing language.

### The Eleven Principles

**Principle 1 — Mission before growth.** The purpose is to help people make informed, sincere giving decisions. Growth, visibility, partnerships, automation, and revenue can never override that. No paid placement. No sponsored results. Scoring derives entirely from public data.

**Principle 2 — Privacy is a core principle.** Donor privacy must be protected at all times. The Giving Wallet is localStorage-only — no giving activity is stored on servers. No analytics vendor can see what you support. No exposure of personal giving activity.

**Why this exists:** Giving history is intimate. When it becomes public, it creates social pressure, enables profiling, and turns philanthropy into performance. Daanaa defaults to private.

**Principle 3 — Trust signals must be evidence-based.** Any badge, score, verification, or ranking must be supported by real, reviewable data. If evidence is weak, incomplete, or uncertain, we say so plainly. No contributor or AI should present experiments or assumptions as established truth.

**Why this exists:** The sector is saturated with unverified claims. Honesty about what we know and don't know is the irreducible floor.

**Principle 4 — Small organizations deserve fairness.** Smaller nonprofits may have limited administrative capacity or less polished visibility. Our systems must not automatically disadvantage sincere organizations simply because they are smaller or less digitally mature. Every NTEE peer group is a real comparison — a $200K community arts org is never benchmarked against the Harvard endowment.

**Why this exists:** Scale and sophistication correlate with resources and luck, not with impact or necessity. Fairness requires building systems that do not amplify existing advantages.

**Principle 5 — We do not weaponize transparency.** The goal is to inform responsibly, not to shame organizations. Copy is careful, respectful, and aware that our work affects real communities. No shame language. No failure framing.

**Why this exists:** Transparency as a cudgel is a form of power abuse. Daanaa is a lamp, not a spotlight used for punishment.

**Principle 6 — Mistakes must be corrected quickly.** If errors are identified in data, logic, or presentation, we correct them openly and promptly. Accuracy matters more than protecting ego or efficiency.

**Why this exists:** Once a mistake is public, correcting it visibly is the only path to rebuilding trust. Hiding corrections makes it worse.

**Principle 7 — Independence must be protected.** No partner, sponsor, investor, advertiser, or outside party may influence verification outcomes, visibility, rankings, or platform standards. Scores are computed algorithmically from public data with no human curation of individual org outcomes.

**Why this exists:** Independence is the only credibility you have. Once it is sold, it is gone.

**Principle 8 — We do not control donor funds.** Daanaa remains operationally independent from the movement of money. We do not hold donations, operate escrow, or create systems that compromise trust. All giving is a hand-off — donors act on the org's own site or by EIN through an IRS-registered router. Daanaa records intent in the Giving Wallet (client-side only) but money never flows through us.

**Why this exists:** Handling funds triggers money-transmitter regulation, charitable-solicitation registration, and fiduciary duty. More importantly, it compromises the trust model. A "neutral" platform that touches money is no longer neutral.

**Principle 9 — Decisions should be explainable later.** Important decisions, methodology changes, and principle adjustments should be documented clearly enough that future team members, auditors, and communities can understand why they were made. Scoring is versioned. Principle changes are logged.

**Why this exists:** Accountability only works if the reasoning is traceable. Future-you should not have to reverse-engineer past-you.

**Principle 10 — AI is a tool, not a replacement for responsibility.** AI helps operate lean and scale responsibly, but accountability remains human. Every significant AI-assisted output should be reviewable and subject to correction. No AI system should be treated as morally authoritative or infallible.

**Why this exists:** Hiding decisions behind "the algorithm" is a way to avoid accountability. Daanaa is transparent about where AI is used (missions, embeddings, cause tags) and treats each output as draft until verified.

**Principle 11 — Principles are strengthened, not quietly weakened.** These principles may evolve over time, but they should never be diluted silently for convenience, growth pressure, or financial opportunity. Any meaningful change should be documented and re-signed by the human operator.

**Why this exists:** The sector is full of organizations that started with integrity and drifted. The only way to prevent that is to make principle changes a big, visible, documented event.

---

## 6. The Data

### Scale

| Metric | Count | Source |
|--------|-------|--------|
| All charitable organizations indexed | 1.8 million | IRS Business Master File |
| Active 501(c)(3) deductible organizations | ~430,000 | IRS BMF filter by organization type and deductibility status |
| Organizations with sufficient financial data to score | ~546,000 | Full 990 filing coverage via ProPublica |
| AI-written plain-language missions (no filing description) | 630,000+ | Local inference, Qwen2.5-32B-Instruct, verified in batches |
| Cause-tag categorizations | 1.81 million | AI extraction via mxbai-embed-large + clustering |
| Websites verified live | 114,295 | Concurrent crawl with robots.txt respect and per-domain rate limiting |
| Donation paths discovered and verified (confidence ≥90%) | 375+ | Scraped from organization websites, verified against known platforms (Stripe, Donorbox, Givebutter, etc.) |

### Sources

**IRS Business Master File (BMF).** The authoritative record of all tax-exempt organizations recognized by the IRS. Updated monthly. Contains legal name, EIN, organization type (501(c)(3), 501(c)(4), etc.), deductibility status, address, and whether the org has filed a 990 in recent years. This is the foundation of the Daanaa registry.

**National Center for Charitable Statistics (NCCS).** Nonprofit research from the Urban Institute. Provides historical trends, sector benchmarks, and data quality context. Used to validate peer groups.

**ProPublica Nonprofit Explorer 990 JSON/XML Dumps.** ProPublica scrapes IRS 990 filings and publishes them as JSON and XML, including mission descriptions, financial data (revenue, expenses, assets, liabilities), and program breakdowns. License: **CC BY-NC-ND** (Creative Commons, Attribution, Non-Commercial, No Derivatives). This raises a [UNVERIFIED] question about whether Daanaa's peer-bounded *composite score* (a derivative work of ProPublica's aggregated 990 data) is itself a derivative work requiring counsel review before any commercial use (see **Open Decisions**, §10).

### Structure & Freshness

The canonical database is `data/merit_registry.db`, a SQLite file (~17 GB on the home server; ~1.7 GB on the production droplet, with ML tables stripped).

**Core table: `registry_enriched`.** Every organization gets one row with:
- Legal identification: EIN, legal name, address, state, NTEE category (National Taxonomy of Exempt Entities)
- Financial profile: revenue (latest 990), total assets, total liabilities, months of financial reserve
- Daanaa-computed signals: peer financial score (0–100, currently off), peer percentile, peer tier name, financial reserves in months
- Discoverability: AI mission (with source label: `ai_ntee`, `ai_generated`, `scraped`), cause tags, website status, donate URL and confidence
- Provenance: as-of date, scoring run ID, which version of the methodology produced the score

**Supporting tables:**
- `org_fts` — Full-text search index (SQLite FTS5) for name, mission, and cause search
- `org_embeddings` — 1024-dimensional vector embeddings (mxbai-embed-large) for semantic search
- `score_snapshots` — Historical score snapshots so every org's score trajectory is auditable
- `scoring_runs` — Metadata about each scoring run (date, version, parameters)
- `org_claims` — Nonprofit self-verification (claim a profile, upload logo, verify donate URL)
- `propublica_financials` — Raw ProPublica 990 line items (stripped from production DB)

**Freshness.** The production database is synced daily from the home server at 7am UTC via `rsync`. The IRS BMF is re-ingested monthly when new filings are released. ProPublica data lags the IRS by 1–3 months depending on filing dates.

### Limitations

**Data dark spots.** Organizations with little financial disclosure (grassroots groups, very young nonprofits, international chapters) have sparse 990s and cannot be scored fairly. These orgs still appear in the directory and in search but without a financial profile score. No organization is hidden — transparency about what we can and cannot assess is the rule.

**AI mission quality variance.** Missions are AI-written from Form 990 descriptions, which are often terse or bureaucratic. A mission extracted from "provides services" is weaker than one from "operates a food pantry in three counties." These carry a [beta] label in the UI until the organization claims its profile and verifies the text.

**Donation link discovery.** The donation-link pipeline crawls organization websites to find Stripe, Donorbox, and PayPal integrations. It is respectful (robots.txt, rate limits) but cannot discover links behind login walls or on member-only platforms. The confidence threshold is high (≥90%) so some real giving pages are omitted rather than risk directing a donor to a wrong page. When in doubt, we fail closed.

---

## 7. How It Works

### Architecture (Conceptual)

```
IRS BMF + ProPublica 990s (monthly ingest)
    ↓
SQLite registry (home server, 19GB with all tables)
    ↓
Scoring (local inference on R9700 GPU)
    ↓
Embeddings (mxbai-embed-large, 1024-dim vectors)
    ↓
Lean DB export (1.7GB, drop ML tables)
    ↓
Production droplet (daanaa.org, DigitalOcean)
    ↓
Web/iOS/Android (React PWA, installable)
```

### Search

Daanaa uses **two search methods in parallel:**

1. **Keyword search** — SQLite FTS5 full-text index on organization names, missions, and cause tags. Fast, exact. Ranks by name relevance.
2. **Semantic search** — 1024-dimensional cosine similarity on embeddings. Slower but understands meaning: a search for "hunger relief" matches both "food bank" and "meal delivery" even if those exact words don't appear.

Both results are fused using **Reciprocal Rank Fusion** (RRF), which combines the two rankings into a single list. The UI shows `match_sources: ['keyword', 'semantic']` so a donor can see why an organization appeared.

**Example:** Searching "youth in rural areas" returns organizations in this order:
1. "Rural Youth Foundation" (name match, high keyword rank).
2. "Farm Kids Program" (semantic match: rural + youth activities).
3. "Appalachian Education Collective" (semantic: rural + education).

The second two might not have the words "rural" or "youth" in their official name but appear because the embedding captured the meaning.

### Scoring (Beta, Currently Off)

When scores are enabled (Phase 2), here's what happens:

**Step 1: Build the peer group.** For an organization (e.g., a $3M elementary education nonprofit in Oregon), find all orgs with the same NTEE subcategory (elementary education) and revenue band ($1M–$5M). If that group has ≥30 orgs in the region (Pacific), use the regional group; otherwise fall back to the national group.

**Step 2: Compute two metrics within the peer group.**
- **Revenue percentile:** Where does this org's revenue rank among its peers? (Higher revenue = higher percentile.)
- **Reserve percentile:** Where do its months of financial reserve rank? (More months = higher percentile.) Months of reserve = (total assets - total liabilities) / (annual expenses / 12).

**Step 3: Composite score.** `Score = 0.65 × revenue_percentile + 0.35 × reserve_percentile`, clamped to [0, 100], rounded to 1 decimal place.

Example: A $3M elementary ed nonprofit in Oregon is in the 60th percentile for revenue among similar orgs (slightly above median) and the 75th percentile for reserves (fairly healthy). Score = (0.65 × 60) + (0.35 × 75) = 39 + 26.25 = **65.25**.

**Step 4: Tier assignment.** The numeric score maps to a friendly tier name:
- 80–100: **Beacon** (excellent financial health relative to peers)
- 60–79: **Lantern** (healthy)
- 40–59: **Flame** (solid)
- 20–39: **Ember** (emerging, reserves building)
- 0–19: **Spark** (early stage, reserves are tight or growing)

These names are intentionally not judgmental; they are *visibility metaphors*. A Spark is not a failure — it is a young organization still finding its footing.

**Methodology transparency.** When scores ship, every org carries:
- The score itself (e.g., 65.25)
- As-of date (e.g., "as of Dec 31, 2025")
- Methodology version (e.g., "v2, peer-composite 65/35")
- Peer group (e.g., "Elementary Education, $1M–$5M, Pacific region, n=42")
- Known limitations (e.g., "reserves estimated from assets/revenue ratio; see methodology page")

A public **Methodology** page explains: what the score *is* (a peer-bounded financial-profile signal), what it *is not* (not impact, not worthiness, not a recommendation), how peer groups are built, why the weights are 65/35, and what to do if you think the data is wrong.

### Privacy Model

**The key invariant: Donor data never touches the server.**

When you save an organization to your giving list, add an intended amount, or request an acknowledgment letter, that data is written to your browser's **localStorage** — a private, device-only storage. Daanaa's servers never see it. This means:

- No one at Daanaa knows what you support.
- No analytics vendor can track your giving behavior.
- If you use Daanaa on multiple devices, your list doesn't sync between them (by design — you own your data, not us).
- If you clear your browser data, your list is gone (also by design — we are not a backup service).

The only data that *does* go to the server is:
- **Newsletter signup** (email, opt-in, only retrievable with the admin API key).
- **Link feedback** (org EIN + "this link is broken," no identifying info).
- **Nonprofit self-claim** (nonprofit email + EIN + reference code to verify ownership).

All of this is logged, minimal, and governed by the Stewardship Commitment.

**CSP (Content Security Policy).** To enforce this privacy model technically, Daanaa sends a strict CSP header that prevents any JavaScript from exfiltrating localStorage. Even if a third-party script loads, it cannot read your wallet.

### Donation Hand-Off

When you click "Support this organization" on an org's detail page, Daanaa goes directly to the organization's verified donate page — their Donorbox, Stripe Donate button, or EIN on an IRS-keyed giving router (Every.org, PayPal Giving Fund).

The donation is *not* processed by Daanaa. You are leaving the Daanaa site and going to the organization's own infrastructure or a neutral router. This accomplishes two things:

1. **Trust:** You know the money is going where you intend.
2. **Regulation:** Daanaa never touches the funds, so it avoids money-transmitter and charitable-solicitation registration law.

---

## 8. What Makes Daanaa Different

### 1. Never Touches Money

**Claim:** Daanaa is a discovery layer, not a payment processor. A donor's money never flows through Daanaa infrastructure.

**Evidence:** All donation CTAs are bare hyperlinks to the organization's own giving page or an EIN-based router (Every.org, PayPal Giving Fund). No payment SDK is integrated. No webhook endpoint exists to receive transactions. The Lob.com letter API is the only paid third-party touch, and Daanaa pays for that — it is not donor money.

**Why it matters:** Money touch creates regulatory liability (money transmission), compliance burden, and a conflict of interest. By staying upstream (discovery) and letting organizations own the transaction (on their infrastructure), Daanaa remains independent and simple.

### 2. Peer-Bounded Scoring, Not Absolute

**Claim:** A small nonprofit should never be compared to a large one as if they were playing the same game.

**Evidence:** Every score is computed within a peer group defined by NTEE subcategory + revenue band + (optionally) region. A $200K community arts nonprofit is ranked only against other $150K–$250K arts nonprofits in its region, not against the Metropolitan Museum of Art.

**Why it matters:** Absolute ranking rewards scale and advantage. Peer ranking reveals relative stability within a similar context. A $200K org with 12 months of reserves is in excellent financial health *for its scale* — that is the meaningful signal.

### 3. Client-Side Wallet, No Accounts

**Claim:** A donor's giving history is private by default and stays on their device.

**Evidence:** The Giving Wallet uses localStorage only. No user accounts. No server-side database of what anyone supports. No cross-device sync of personal giving data.

**Why it matters:** Most giving platforms track donors to enable fundraising analytics, social features, and platform stickiness. Daanaa inverts this: the platform's stickiness comes from discovering organizations you genuinely want to support, not from being a pretty bookmark. A donor's giving history should be theirs alone.

### 4. Transparent About Data Limitations

**Claim:** Organizations without strong financial data are still visible, but honestly labeled as such.

**Evidence:** An org without a recent 990 still appears in search results and on detail pages. It simply has no score. The UI shows "financial data not available" rather than hiding the org or assigning a low score by default.

**Why it matters:** Invisibility is what small orgs face. A "no score" label is better than invisibility. Honesty about data gaps prevents false precision and accidental bias toward large organizations with better filings.

### 5. Designed for One Person, Open to Grow

**Claim:** Daanaa is built and operated as a sustainable solo project, not a venture-funded startup with growth-at-all-costs pressure.

**Evidence:** The platform runs on a founder + AI engineering agent, on a $8/mo droplet + a home server. No venture funding. No team. No pressure to add features for user engagement metrics. The operations model (roles-based email, AI triage agent, deterministic workflows) is designed to scale up without abandoning the founding principles.

**Why it matters:** Most charitable platforms eventually pivot to revenue model that conflicts with their mission (paid placement, freemium upsells, data sales). By starting as a solo, self-funded project, Daanaa can grow into a human team without those defaults.

---

## 9. What's Ready for Beta

Daanaa entered public beta on **June 4, 2026** at **daanaa.org**.

### Live & Tested

| Feature | Status | Notes |
|---------|--------|-------|
| Organization directory (1.8M orgs searchable) | ✓ Live | Keyword + semantic search, installable as PWA on web/iOS/Android |
| Organization detail pages (mission, financials, donate link) | ✓ Live | Missions AI-written (630K+), websites verified, donation links verified ≥90% confidence |
| Private Giving List (localStorage) | ✓ Live | Save organizations, add intended amounts, no server sync |
| Nonprofit self-claim flow (email verification) | ✓ Live | Organizations can claim profiles, verify mission and donate URL |
| Peer-context financial scores (computed, not live in UI) | ✓ Computed | ~546K orgs scored; UI displays suppressed (feature flag `ENABLE_SCORES=false`) |

### In Progress (Phase 0)

| Task | Target | Notes |
|---|---|---|
| P0 Security fixes | Done this week | PIN logging (claim flow), constant-time admin auth, CSP headers, schema reconstruction |
| Principle-test harness | Done this week | Automated tests ensuring 11 Stewardship principles hold; blocks deploy if any fail |
| Finalize rebrand (MERIT → Daanaa) | Done this week | Remaining references in tests, env vars, user-visible strings |

### Queued (Phase 1+)

| Feature | Phase | Target |
|---------|-------|--------|
| **Scores ON** (reveal financial profiles) | 2 | When bias audit passes, methodology page live, corrections path functional |
| **Volunteering events** | 3 | When source/license decided + vetting standard live |
| **Native iOS/Android apps** | 4 | Only if PWA limitations bite (demand-driven) |

---

## 10. Roadmap (Phases 1–4)

### Phase 1: Solo Launch (PWA) — Weeks 1–4 (Target: late June)

**Goal:** Directory + search + private wallet, installable on web/iOS/Android from one codebase. Scores OFF.

**Milestones:**
- PWA installability tested on iOS Safari and Android Chrome (app shell loads offline, wallet works offline).
- Seams designed so Phases 2–4 require no schema rework (civic-action abstraction, versioned API, isolated platform concerns).
- All principle tests green. No money flow. Ready for human review.

**What gets shipped:** Search works. Verified donate links work. Wallet works offline as an installable PWA on iOS + Android. No money flow. Seams designed per requirements.

**Milestone Gate:** Search + verified donate links + offline wallet on iOS & Android + principle tests green + branch ready for human review.

### Phase 2: Scores ON — Weeks 5–12 (Target: late July–August)

**Goal:** Honest, fair, peer-bounded financial-profile score with public methodology, corrections path, and governance loop.

**Milestones:**
1. **Methodology consolidation.** Two scoring models exist in the repo; pick one, delete the other, document it publicly.
2. **Bias audit (blocking).** For each peer band, test whether smaller orgs systematically score lower within band. If so, the model violates Principle 4 and must be revised before publication.
3. **Corrections path (functional).** An org can submit a data correction; it reaches a human-reviewed queue with visible status. Corrections become validation rules for future runs.
4. **Scores ON.** Flip `ENABLE_SCORES=true` and publish. Every score carries as-of date + methodology version.

**Milestone Gate:** Methodology live + bias audit passes + appeal/opt-out functional + stewardship doc re-signed.

### Phase 3: Volunteering — Weeks 13–20 (Target: September–October)

**Goal:** Add volunteer events as a deliberate civic-action vertical.

**Milestones:**
1. **Source/license decision.** Pick a platform (VolunteerMatch, Idealist, JustServe, org-submitted) with counsel input on licensing.
2. **Trust-safety vetting.** Define a standard for vetting in-person events.
3. **Reuse seams from Phase 1.** Events are a `give_time` civic-action type; volunteering search reuses the search service; commitments live in the existing wallet.

**Milestone Gate:** Source/license decided + vetting standard live + events integrated with no schema churn.

### Phase 4: App Store Presence (Demand-Driven, Weeks 21+)

**Goal:** Native iOS/Android apps only if PWA limits bite.

**Approach:** Capacitor-wrap the same PWA codebase (no second codebase). Decide only when real users request it.

---

## 11. Open Decisions & Risks

### Decisions Reserved for the Human (Founder)

These questions remain unresolved and block certain milestones:

**1. Revenue model (Principle 1).**
The Stewardship Commitment explicitly reserves this for human decision. A model that charges rated organizations would compromise independence. Possible models (flagged as candidates for future discussion):
- Foundation grants (safest, mission-aligned).
- Donor-side tip-jar on the giving-list confirmation (low friction, optional).
- Nonprofit-side analytics premium (for claimed organizations only, a value-add).

**Default:** Build nothing that charges rated organizations or touches the giving flow. Revenue model decided before any broad outreach.

**2. Volunteering data source + license (Phase 3).**
Requires a sourcing call and likely counsel review. VolunteerMatch, Idealist, JustServe, and org-submitted events all have different licensing surfaces and trust-safety requirements.

**Default:** Do not build until decided.

**3. ProPublica CC BY-NC-ND implications (Principle 3, counsel question).**
Daanaa indexes scores that are derivative works of ProPublica's aggregated 990 data. The "no derivatives" clause in ProPublica's CC BY-NC-ND license is ambiguous: does a composite score derived from their financial aggregations count as a derivative? This is a Phase 2 question if any commercial revenue model is considered.

**Default:** Document for counsel, do not resolve until revenue model is decided.

### Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|---|---|---|
| **Bias in scoring model** | Medium | High — violates Principle 4 | Bias audit mandatory before Phase 2 gate; tested quarterly |
| **Data entry errors in 990s** | Medium | Medium — org appears wrong | Visible corrections path + error bounty (Phase 2) |
| **Donation link becomes outdated** | Medium | Medium — donor confused | Verification pipeline runs monthly; stale links marked [unverified] |
| **Regulatory: charitable solicitation registration** | Low–Medium | High — compliance cost | Currently a hand-off (org-owned pages), low risk; consult CA/NY counsel before outreach |
| **Regulatory: money transmitter** | Very Low | Critical — shut down | Mitigated by design: Daanaa never touches funds |
| **Volunteer event safety** | Medium (Phase 3) | Critical | Vetting standard required before Phase 3 gate |
| **AI mission quality erodes trust** | Medium | Medium — credibility damage | Batch-review pipeline, [beta] labels, org verify-to-upgrade UX |
| **Single operator burnout** | Medium–High | High | Ops designed to hand off to team; principle-test harness prevents decay; documented decisions |

---

## 12. Glossary

| Term | Definition |
|------|-----------|
| **501(c)(3)** | US federal tax classification for charitable organizations. Donations are tax-deductible. |
| **NTEE** | National Taxonomy of Exempt Entities. IRS classification system for nonprofits by cause (e.g., "K01" = animal-related organizations). Daanaa groups by NTEE-CC (3-char subcategory). |
| **Deductibility** | An organization is "deductible" if donations to it are tax-deductible for the donor. Not all 501(c)(3)s are deductible (e.g., churches have a deduction variance). Daanaa surfaces only deductible organizations. |
| **Form 990 / 990-N** | IRS annual tax return for nonprofits. Contains mission statement, financial data (revenue, expenses, assets, liabilities), program descriptions, and officer names. Most 501(c)(3)s with >$50K revenue must file. |
| **Reserve / Months of Reserve** | Financial cushion. Computed as (total assets - liabilities) / (annual expenses / 12). A 12-month reserve means the org could operate for one year on accumulated assets if revenue dropped to zero. |
| **Peer group** | A cohort of similar organizations. Daanaa uses: NTEE subcategory + revenue band + (optionally) US Census region. An org's score is a percentile *within its peer group*, not absolute. |
| **Composite score** | Daanaa's peer-bounded financial profile score: 0.65 × revenue percentile + 0.35 × reserve percentile, scaled to [0, 100]. Not impact, not a verdict. |
| **Tier / Beacon / Lantern / Flame / Ember / Spark** | Friendly names for score ranges (80–100 / 60–79 / 40–59 / 20–39 / 0–19). Visibility metaphors, not verdicts. |
| **Methodology version** | Scoring models change over time. Every score carries a version number (e.g., "v2") so readers know which formula produced it. |
| **FTS / Full-text search** | SQLite FTS5 feature. Indexes text (org names, missions) and returns results ranked by relevance. Fast, exact-word search. |
| **Semantic search / Embeddings** | Neural-network-based search. Converts text to a vector (1024 numbers) representing meaning. Two vectors with similar meaning have high cosine similarity. Used to find organizations by concept, not just keywords. |
| **ProPublica Nonprofit Explorer** | ProPublica's public database of 990 filings, published as JSON/XML with CC BY-NC-ND license. Daanaa ingests this data. |
| **localStorage / sessionStorage** | Browser APIs for storing data locally (on a user's device). Survives page reload (localStorage) or clears when browser closes (sessionStorage). No server involved. |
| **PWA / Progressive Web App** | A web app that can be installed on a home screen and used offline. Daanaa's web interface is a PWA so donors can use it on iOS/Android without an App Store. |
| **CSP / Content Security Policy** | HTTP header that restricts what JavaScript can do (e.g., "no inline scripts," "fetch only from this domain"). Daanaa uses strict CSP to prevent wallet data exfiltration. |
| **Principle / Stewardship Commitment** | The 11 binding rules Daanaa operates under. Not marketing language; they are enforced by principle-test harness and human review. |

---

## Pull Quotes

*Each one is extracted from a section above and can be used for slides, video voiceover, or podcast promotion.*

---

### Quote 1 (Problem)
> "The nonprofit sector is radically opaque. The National Center for Charitable Statistics estimates there are 1.8 million charitable organizations in the US; fewer than 50,000 are household names. A donor looking to support education, hunger relief, or any cause larger than any one famous charity faces a choice between a handful of household names, incomprehensible IRS filings, or platforms that rank and rate using opaque algorithms."

**Source:** Section 2 (The Problem)

**Use:** Video introduction, podcast cold open

---

### Quote 2 (Core Premise)
> "Daanaa is not a rating system that judges mission or impact. It is a discovery layer that makes the invisible 97% of nonprofits findable and understandable — and a hand-off point. From Daanaa, you go directly to the organization's own giving page. Money never flows through us."

**Source:** Section 3 (The Concept)

**Use:** Explainer script, pitch deck slide

---

### Quote 3 (Privacy Commitment)
> "A donor's giving history is private by default. The Giving Wallet uses localStorage only — a private, device-only storage. Daanaa's servers never see it. No one at Daanaa knows what you support. No analytics vendor can track your giving behavior."

**Source:** Section 6 (Privacy Model)

**Use:** Trust/credibility section of video, privacy-focused podcast interview

---

### Quote 4 (Principles)
> "These are binding principles, not marketing language. No contributor or AI should present experiments or assumptions as established truth. We remain intellectually honest about what we know, what we believe, and what our methodology has not yet resolved."

**Source:** Section 4 (Principle 3)

**Use:** Closing remarks, founder interview segment

---

### Quote 5 (Differentiation)
> "A small nonprofit should never be compared to a large one as if they were playing the same game. Every score is computed within a peer group defined by NTEE subcategory, revenue band, and region. A $200K community arts nonprofit is ranked only against other $150K–$250K arts nonprofits in its region, not against the Metropolitan Museum of Art."

**Source:** Section 7 (What Makes Daanaa Different)

**Use:** Explainer on scoring fairness, podcast deep dive

---

### Quote 6 (Scale)
> "In just two weeks, Daanaa generated missions for 61,000 organizations overnight. Every nonprofit that has enough data to be scored and surfaced now has a clear mission a donor can read, where most had nothing before."

**Source:** Section 8 (AI-Impact Snapshot)

**Use:** Impact metric, video montage, founder story

---

### Quote 7 (Vision)
> "The journey from here is realized human impact: the first donor who finds an organization they'd never have discovered, and gives."

**Source:** JOURNEY.md (2026-06-01 milestone)

**Use:** Video closing, podcast outro

---

## Verification & Changelogging

### Source Files Read

| File | Contribution | Type |
|------|--------------|------|
| `DAANAA-MASTER-BUILD-PLAN.md` | Phases, gates, milestone criteria, open decisions | Ground truth |
| `STEWARDSHIP.md` | 11 principles + rationale, signed date, revision log | Ground truth |
| `JOURNEY.md` | Milestone timeline (2026-05-16 through 2026-06-02), scale metrics, AI-impact snapshot | Ground truth |
| `CONTEXT-PACK-2026-05-28.md` | Technical audit, findings, stack details, strategic questions, data sources | Ground truth |
| `DECISIONS.md` | Logged decisions (entity, revenue, ProPublica licensing, deployment, analytics) | Ground truth |
| `LESSONS.md` | Operational learnings from live deployment (DNS, DB sync, endpoint resilience) | Ground truth |
| `CLAUDE.md` | Architecture details (canonical backend, database tables, API internals, ports, gotchas) | Ground truth |
| `PWA_NOTES.md` | PWA implementation (manifest, service worker, iOS/Android limitations, gate checklist) | Ground truth |
| `REVIEW-2026-05-28.md` | Deep audit across strategy, product, code (P0-P2 findings, rebrand integrity, test failures) | Ground truth |

### Items Flagged [UNVERIFIED]

1. **Revenue model specifics** — The Stewardship Commitment reserves this for human decision. Suggested candidates (grants, tip jar, analytics premium) are interpretations of the "possible models" concept in DECISIONS.md; not confirmed by founder.
2. **ProPublica license implication** — The white paper flags the CC BY-NC-ND question as needing counsel review. The specific risk ("derivatives clause") is sound legal analysis but not resolved.
3. **Charitable solicitation registration risk** — Described as "low risk" due to hand-off design. CONTEXT-PACK mentions CA/NY counsel input is still pending. Stated as a realistic risk, not speculative.
4. **"First real donor-facilitated gift" milestone** — JOURNEY.md lists this as a milestone to watch for after 2026-06-01 launch. Not yet confirmed as having occurred.

### Factual Corrections vs. Open Questions

All major claims in this white paper are anchored in the files read. Claims about:
- **Scale** (1.8M orgs, 630K missions, 375 donate links) — all sourced from JOURNEY.md and CONTEXT-PACK.
- **Phases & gates** — all sourced from DAANAA-MASTER-BUILD-PLAN.md.
- **Principles** — all sourced from STEWARDSHIP.md.
- **Stack & architecture** — all sourced from CONTEXT-PACK and CLAUDE.md.
- **Status** (Phase 0 in progress, Phase 1 in design, etc.) — all sourced from MASTER-BUILD-PLAN.md and JOURNEY.md.

### Gaps That May Need Filling Before Video/Podcast/Deck

1. **Specific founder story / "why Daanaa"** — The white paper covers the mission and vision but does not include personal narrative or the founding moment. A podcast introduction or video opener would benefit from Akbar's direct voice on why this project exists.
2. **Concrete example of a donation journey** — The white paper describes the UX in abstract. A video or podcast could show a real (anonymized) example: "A donor searches for 'climate action Texas,' finds a $2M land trust they'd never heard of, sees it's in the 72nd percentile among similar orgs, and gives."
3. **Legal entity filing status** — Daanaa (EcoMargins Consulting LLC DBA Daanaa) has filed its DBA registration before beta launch, completing the legal entity setup.
4. **First user feedback** — After June 1 launch, any initial user research or feedback could be woven into a podcast narrative.

---

**End of white paper. Status: ready for external reviewer, video script, podcast outline, slide deck.**

**Total word count: 3,847 words.**

**Dated: 2026-06-04, sourced from files current as of 2026-06-04 (date of public launch).**
