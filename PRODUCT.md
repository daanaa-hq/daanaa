# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

**Primary audiences (equal priority):**

1. **Individual donors** — People looking for where to donate their own money to causes they care about. Job: discover and evaluate nonprofits, make informed giving decisions, track giving over time.

2. **Nonprofit leaders** — People running nonprofits who want to understand how Daanaa presents their organization, claim profiles, and see financial context.

3. **Researchers / data consumers** — Academics, journalists, policy researchers, and grant makers studying the nonprofit sector. Job: bulk analysis, trend analysis, sector benchmarking.

## Product Purpose

Daanaa helps people make more informed and sincere giving decisions by indexing 1.7M+ U.S. nonprofits from IRS public records and providing fair, peer-group-based financial context. It is a discovery layer for the nonprofit sector, not a payment processor.

Success means:
- Donors find organizations working on causes they care about
- Nonprofits are benchmarked fairly against genuinely similar peers, not absolute ratings
- The sector gets accurate, transparent, evidence-based information
- Trust is earned, not claimed

## Positioning

Daanaa's mechanism is three integrated ideas:

1. **Peer-group benchmarking** — Financial context positioned relative to similar organizations, not a one-size-fits-all rating. A $200K community org is compared against $150K–$700K peer groups in its NTEE category, not against $40M foundations.

2. **IRS data only** — Public source authority with structural independence. No crowd ratings, no paid placement, no outside influence over outcomes. Data comes from IRS Form 990 filings, the Business Master File, and Publication 78.

3. **Fair treatment of small orgs** — Smaller nonprofits are never disadvantaged by design. Scoring is benchmarked by peer group and revenue band; a high-performing food bank gets equal visibility to a high-performing research institute.

No neighboring product can truthfully claim all three.

## Operating Context

**Workflows:**
- Donor: browse directory, search by cause/location, view org profile, add to wallet, donate via org's own processor, snapshot wallet state over time
- Nonprofit leader: claim profile, view how Daanaa presents org, see financial metrics and peer context, understand IRS eligibility status
- Researcher: bulk data queries, sector analytics, trend analysis, export datasets
- Admin: monitor platform health, manage org claims, coordinate with IRS data sources

**Environment:**
- Live at daanaa.org (staging: staging.daanaa.org)
- Backend: Flask + SQLite (merit_registry.db), 2.056M org database
- Frontend: React 19 + TypeScript + Vite, Tailwind CSS, Radix UI
- Local inference: Qwen3-30B for mission generation, mxbai-embed-large for org embeddings

**Data refresh:**
- Nightly precompute pipeline: scores, FTS index, embeddings, org JSON files
- IRS data updates: monthly (Pub78, BMF)
- User-facing data: 12–24 months old by IRS publication lag

## Capabilities and Constraints

**Capabilities:**
- Search and filter 1.7M+ nonprofits by cause, location, financial context
- View org profiles with financial metrics, mission, leadership, IRS eligibility status
- Add orgs to a Giving Wallet (device-first, optional cloud sync)
- Volunteer interest capture for events
- Claim nonprofit profiles and attest information
- Design for donors, nonprofit leaders, and researchers equally

**Constraints:**
- Never handle donor funds (hand-off to org or EIN-based routing)
- Never track giving activity beyond wallet intent (privacy-structural)
- No social features (no public giving profiles, no performance pressure)
- No real-time data (batch updates only, 12–24mo lag from IRS)
- No paid placement or sponsored results
- No API keys or commercial licensing (public data only)

**Terminology:**
- "IRS eligibility status" (verified/unverified/revoked/unknown/exception_possible)
- "Financial health" (HEALTHY/STABLE/NEED_SUPPORT) — supportive framing, never shame
- "Peer group" (NTEE category + revenue band + geographic region)
- "Giving Wallet" (intent tracking, not transaction tracking)

**Explicitly undecided:**
- Native mobile app (web-only for now; PWA possible future)
- Nonprofit analytics dashboard (CRM-like nonprofit portal planned, roadmap undecided)
- DAF / donor-advised fund integration (shipping late 2026)

## Brand Commitments

**Stewardship Commitment:** Daanaa operates under 11 founding principles (STEWARDSHIP.md) binding all contributors and AI agents:
- P1: Mission before growth
- P2: Privacy is structural
- P3: Trust signals are evidence-based
- P4: Small orgs treated with equal dignity
- P5: No shame language
- P6: Mistakes corrected openly
- P7: Independence protected
- P8: Never handle funds
- P9: Decisions explainable later
- P10: AI is a tool, not moral authority
- P11: Principles strengthened, not weakened

**Daanaa Charter** (daanaa.org/charter): Public never-promises binding all contributors.

**Voice:**
- Specific over generic ("1.7M nonprofits from IRS records" vs. "discover causes")
- Evidence-based over aspirational (show data, acknowledge uncertainty)
- Respectful of all orgs over praising large ones (peer groups, not rankings)
- Transparent about gaps ("This data is 12–24mo old. Contact the org directly for real-time info.")

**Visual identity:** Navy + cream + gold palette with Cormorant Garamond serif for display headings. Signals trust (navy), warmth (cream), and intention (gold) — intentionally avoids purple-gradient SaaS defaults.

## Evidence on Hand

**Real content & data:**
- IRS data: Pub78 (35K+ orgs), Business Master File (1.7M+), auto-revocation list (updated regularly)
- 1.7M org profiles with financials, missions (AI-generated for 80%+), volunteer links, donation links
- Research page: published methodology, financial context benchmarking documentation
- Peer context snapshots: 411K+ orgs scored with v5 archetype system

**Case studies & press:**
- None yet (pre-launch phase). Charter and methodology published at daanaa.org/charter and /methodology.

**Assets:**
- Logo and brand mark (TBD final deployment)
- Daanaa typefaces: Cormorant Garamond (display), Inter (body/UI, provisional)
- Color tokens: CSS custom properties in frontend/src/index.css

**Absences:**
- No testimonials or customer quotes yet (not fabricated)
- No pricing or commercial model (mission is pure discovery, revenue model undecided)
- No investor/press materials
- No case studies from nonprofit partners

## Product Principles

1. **Evidence gates everything.** Trust signals come from real IRS data, not crowd voting or AI heuristics. Unverified claims are labeled; gaps are acknowledged.

2. **Peer context, not ratings.** Organizations are benchmarked against truly similar peers, not absolute scales. A 99th-percentile reserve level means something different for a $200K org than a $200M org.

3. **Dignity and equal visibility.** Small organizations are never disadvantaged by design. The algorithm, UI, and content voice treat a community food bank with as much respect as a national research institute.

4. **Structural privacy.** User data — what they browse, save, or intend to donate — is never collected, tracked, or exposed. The default is device-first; cloud backup is optional, never required.

5. **Independence above growth.** No partner influence over outcomes, no paid placement, no secret tuning toward high-revenue orgs. The public deserves a neutral platform.

## Accessibility & Inclusion

**Required standards:**
- WCAG 2.1 AA minimum (aiming for AAA where feasible)
- Keyboard navigation fully supported (no mouse-only interactions)
- Screen reader compatible (semantic HTML, ARIA labels where needed)
- Color contrast ratio 4.5:1 for normal text, 3:1 for large text
- Responsive design: mobile-first, tested on 320px–4K

**Product-specific needs:**
- No time-limited interactions (Giving Wallet has no session timeout)
- Clear language: avoid jargon, explain "peer group," "NTEE," "IRS eligibility"
- Financial tables: support export to CSV for analysis
- Search: support filters for users with limited vision or cognitive load concerns

