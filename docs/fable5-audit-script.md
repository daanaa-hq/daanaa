# Daanaa — Fable 5 Audit Script

**Purpose:** Run this on `claude-fable-5` as six sequential audit sessions.
Each section is a self-contained prompt. Paste the CONTEXT block once per session,
then paste the PROMPT block. Take the output seriously — Fable 5 will press harder
than a real user because it has no politeness filter.

**Model:** `claude-fable-5`
**Date:** 2026-07-03
**Auditor:** Akbar Khowaja (founder)

---

## HOW TO USE

For each section below:
1. Start a fresh Fable 5 conversation
2. Paste the CONTEXT block (gives Fable 5 enough background to be useful)
3. Paste the PROMPT block
4. Read all output carefully — do not dismiss uncomfortable findings

---

---

# SECTION 1 — SECURITY AUDIT

## CONTEXT (paste this first)

```
You are auditing Daanaa (daanaa.org), a civic nonprofit-discovery platform built on Flask + SQLite (Python backend, port 5000) with a React/TypeScript/Vite frontend. The platform indexes 1.7M US nonprofits from IRS and ProPublica public data, assigns peer financial context scores, and surfaces them through a searchable directory. Users discover nonprofits and click out to donate on the org's own site — Daanaa never touches money.

Architecture:
- Backend: daanaa_api.py (~7,800 lines), Flask + SQLite, gunicorn 4-workers with --preload
- Frontend: React 19, TypeScript, Vite, Tailwind, deployed as a built SPA served by Flask
- Database: data/merit_registry.db (SQLite) with 1.7M orgs, FTS5 search, vector embeddings
- Auth: Nonprofit portal uses magic-link email auth. Vendor portal has separate login. Admin endpoints require X-Admin-Key header.
- Privacy: No user tracking. Wallet is localStorage-only. Plausible analytics (no cookies). DAANAA_PROD flag enables HTTPS-only CSP + HSTS.
- ML: Local llama.cpp servers on ports 11436 (embeddings) and 11437 (mission generation). No cloud LLM APIs for batch tasks.
- Deployment: DigitalOcean droplet at 162.243.97.179, behind Cloudflare (SSL/DDoS). Nginx + systemd.

Key security invariants the platform is built around:
1. Individual user data NEVER goes to an external LLM (privacy_check.sh pre-commit hook enforces this)
2. Admin endpoints gated by DAANAA_ADMIN_KEY env var
3. Secrets only from environment — never logged, never in code
4. ENABLE_SCORES=false env flag suppresses score output (for kill-switch)
5. SQLite parameterized queries only (no string interpolation in SQL)
6. Nonprofit portal: orgs can only modify their own claimed listing
```

## PROMPT (paste after context)

```
You are a senior security engineer doing a pre-launch security review of Daanaa. Your job is to identify real, exploitable vulnerabilities — not theoretical noise. Be direct, name specific attack vectors, and prioritize ruthlessly.

Using the architecture described above, answer these questions in order. For each finding, state: SEVERITY (CRITICAL/HIGH/MEDIUM/LOW), the specific attack vector, what an attacker gains, and what the fix is.

**A. Authentication & Authorization surface**
1. The nonprofit portal uses magic-link email auth. What are the most realistic ways this can be bypassed or abused? Consider: link expiry, replay attacks, account enumeration, org-claim verification.
2. Admin endpoints require an X-Admin-Key header from an env var. What fails if that key leaks? What compensating controls should exist?
3. Vendor portal has a separate login system from the nonprofit portal. Cross-contamination: can a vendor session claim nonprofit capabilities or vice versa?
4. Org claim flow: "orgs can only modify their own claimed listing." What's the most likely way claim authorization gets bypassed? Think about EIN-based lookups, email domain matching, and race conditions.

**B. Injection & Data Integrity**
5. Flask + SQLite with "parameterized queries only." Walk through the most common ways parameterized queries get circumvented in Python Flask apps — accidental f-strings, ORM misuse, dynamic column names. What should be audited?
6. The FTS5 search index. FTS5 has known edge cases. What are realistic FTS injection patterns and what's the blast radius on SQLite FTS5?
7. The React frontend sends user-controlled query parameters (q=, city=, ntee=, min_percentile=). Even with parameterized SQL, what client-side injection risks exist? Think XSS vectors in rendered search results.

**C. Privacy & Data Exfiltration**
8. The platform stores a localStorage-based Giving Wallet. What are the realistic browser-side attacks on this data? Consider: XSS persistence, cross-origin access, extension attacks.
9. "Individual user data NEVER goes to an external LLM" — but mission generation uses a local llama.cpp server on port 11437. What data flows into the mission generation pipeline and what happens if that server is compromised or exposed?
10. Plausible analytics ("no cookies, no tracking"). What does Plausible capture by default and does any of that constitute PII or create privacy risk for donors in privacy-sensitive jurisdictions?

**D. Infrastructure**
11. Droplet at 162.243.97.179 behind Cloudflare. What's exposed if Cloudflare goes down or gets bypassed? What direct-IP attack surface exists?
12. gunicorn 4-workers with --preload loads ~546K org vectors (numpy matrix) into RAM via CoW at startup. What's the memory safety risk profile here? Under what conditions does this create a denial-of-service vector or data exposure between workers?
13. The in-process response cache (dict with per-namespace TTLs) has no Redis — it's invalidated only on restart. What are the poisoning/staleness risks? What happens if a cache entry for one org leaks into another org's response?
14. Local inference servers on ports 11436 and 11437. Are these exposed on the droplet's public interface? What's the attack surface if they are?

**E. Supply Chain & Deployment**
15. The privacy_check.sh pre-commit hook is the primary enforcement mechanism for the "no user data to external LLMs" invariant. What are the most realistic ways this hook gets bypassed or becomes ineffective over time?

For each finding above, conclude with a specific, actionable fix. If the finding is not a real vulnerability given the architecture (e.g., SQLite doesn't have the same injection profile as PostgreSQL), say so plainly and explain why.
```

---

---

# SECTION 2 — STEWARDSHIP LANGUAGE & TERMINOLOGY AUDIT

## CONTEXT (paste this first)

```
You are auditing Daanaa (daanaa.org), a nonprofit discovery platform governed by a Founding Stewardship Commitment with 11 binding principles. The three non-negotiables are:
1. Trust signals are evidence-based only
2. Donor privacy is structural
3. Independence is protected (no paid placement, no partner influence)

Other key principles:
- P4: Small orgs deserve fairness (peer benchmarking within NTEE groups, not absolute comparison)
- P5: We do not weaponize transparency (no shame language, no negative framing, no "F-rated")
- P7: Independence must be protected (no partner can influence scores, rankings, or visibility)

The platform calls itself "not a rating agency" and says it "does not rate, rank, endorse, or recommend organizations." It shows "Peer Financial Context" (a percentile score within same funding model + revenue band) and "Lamp Tiers" (visibility levels based on public data completeness, NOT org quality).

Health signals use these exact labels:
- HEALTHY → "Financially healthy"
- STABLE → "Financially stable"
- CAUTION → "Needs support"

The platform also runs an "Impact Network" (vendor marketplace for nonprofits) and has partner pages. Partner relationships explicitly must NOT affect scores, rankings, or visibility.

Pages that exist and their purpose:
- / (Home) — discovery entry point, hero search, causes grid, tier explainer
- /directory — searchable/filterable list of 1.7M orgs
- /org/:id — org detail: financials, mission, peer context, volunteer opportunities, claim status
- /methodology — how data works, peer context explainer, FAQs
- /about — mission and stewardship principles
- /tiers — lamp tier explainer
- /for-nonprofits — how orgs can claim their listing
- /partners — vendor partner directory
- /for-vendors — vendor pitch page
- /wallet — giving wallet (localStorage, no account required)
- /research — sector health research dashboard
- /compare — side-by-side org comparison (up to 4 orgs)
- /the-invisible-97 — landing page about the overlooked 97% of nonprofits
```

## PROMPT (paste after context)

```
You are a brand and stewardship auditor reviewing every piece of customer-facing language on Daanaa. Your job is to find places where the copy, labels, or UI language contradicts the platform's stated commitments or creates legal/trust risk. Be specific — quote exact phrases that are problematic.

**A. Rating agency language risk**
The platform says "we do not rate, rank, endorse, or recommend organizations." Find every place the following language patterns could appear and assess if they violate this commitment:
1. Any phrase that implies one org is "better than" another in absolute terms
2. Any use of "score" language that isn't qualified as peer-contextual
3. Any CTA or suggestion that implies Daanaa is recommending a giving decision
4. The comparison feature (/compare) — does showing 4 orgs side-by-side inherently imply ranking? What language on that page would make it safe vs. unsafe?
5. The home page hero headline "See the overlooked. Give with heart." — does this imply Daanaa knows which orgs deserve giving? What's the stewardship risk?

**B. Health signal language**
The platform maps CAUTION → "Needs support." Evaluate:
1. Is "Needs support" truly stewardship-aligned? Does it invite support (pro-giving) or does it suggest the org is struggling and donors should be wary?
2. What tooltip or contextual language should always accompany "Needs support" to prevent it from being read as a warning?
3. On the wallet card, the title attribute says: "Fewer reserves than most similar organizations. An invitation to give, not a judgment of the work." Is this enough? When would a user see this vs. not?
4. What happens on the compare page when one org shows "Financially healthy" and another shows "Needs support"? Does the visual presentation inadvertently shame the second org?

**C. Small org fairness**
Principle 4 requires equal dignity for small orgs. Audit:
1. The Lamp Tier system: Spark tier (55.1% of orgs) gets "Recognized nonprofit with minimal public information available." Is "minimal public information" stigmatizing? Could it discourage giving to legitimate small orgs?
2. The hidden gems mechanic surfaces "small but high-performing" orgs. Does the label "hidden gem" imply the platform is curating recommendations, contradicting the no-endorsement commitment?
3. The directory sorts by merit_score by default. Does default sort order constitute a ranking? What's the legal/stewardship risk?

**D. Independence and vendor language**
The platform runs vendor partner pages (/partners, /for-vendors):
1. The for-vendors page describes the Impact Network. Does any language on that page imply that being a partner gives an org better visibility or positioning on the platform?
2. The Terms page says "Partner participation — including any fees paid to Daanaa — never affects how any organization appears in search results, its financial context score, its tier, or any other trust signal." Is this statement specific enough? What edge case could create a credible claim that it does?
3. The guild referral page (/guild/:slug) drives vendor network growth. Does this page maintain independence framing or does it feel like a commercial sales pitch that could undermine user trust?

**E. AI-generated content**
The platform uses AI-generated mission summaries labeled "AI generated." Audit:
1. Is "AI generated" a sufficient label? What does it fail to communicate about accuracy, recency, or source?
2. Mission statements appear on org detail pages as the primary description of what an org does. If an AI-generated mission is wrong, what's the harm pathway to the org and to donors?
3. The methodology page says "When we use AI to generate a mission summary, we label it clearly." Does the label appear in contexts where it matters most — org detail pages, search results, the compare page?

**F. Data staleness**
990 data can lag 18-24 months per IRS filing timelines:
1. Is data staleness disclosed at the point of use (org detail page) or only in the methodology/terms pages?
2. The health signal ("Financially healthy/stable/needs support") is derived from potentially 2-year-old data. Does the UI make this clear? What's the specific harm if a user relies on an outdated health signal to make a giving decision?
3. What language changes would make staleness visible without being so prominent it undermines user confidence in all the data?

For each issue found, provide: (a) exact copy that's problematic, (b) the specific stewardship principle it risks violating, (c) a revised version of the copy.
```

---

---

# SECTION 3 — PAGE CONNECTIVITY & MISSION COHERENCE

## CONTEXT (paste this first)

```
Daanaa's mission is: "Help people make more informed and sincere giving decisions" by surfacing the overlooked 97% of nonprofits through public data, peer financial context, and stewardship-first design.

The user journey has two primary entry points:
1. Someone searching for a cause/org to support (donor discovery)
2. A nonprofit trying to understand and improve their visibility (nonprofit claiming/profile)

Secondary journeys:
- A vendor exploring the Impact Network (/for-vendors)
- A researcher looking at sector data (/research)

Page inventory and stated purpose:
- / → Entry; search + causes grid + tier explainer + hidden gems section
- /directory → Filtered browse of 1.7M orgs
- /org/:id → Full org detail: mission, financials, peer context, website link, volunteer, claim
- /causes/:id → Cause spotlight: what this cause area is, featured orgs
- /category/:id → NTEE category page
- /methodology → How data works, sources, peer context, what we don't measure, FAQ
- /about → Who built this and why, stewardship principles
- /tiers → Lamp tier explainer
- /wallet → Giving wallet (save orgs, note giving intent)
- /compare → Side-by-side up to 4 orgs
- /research → Sector health dashboard with charts
- /for-nonprofits → How orgs claim their listing
- /the-invisible-97 → Story-first landing about overlooked orgs
- /nonprofit/login + /nonprofit/dashboard/:ein → Nonprofit portal
- /volunteer → Volunteer search

Navigation: top nav has Home, Directory, Research, For Nonprofits. The wallet is accessible via a wallet icon.

Known dead ends or gaps mentioned in past sessions:
- No clear path from /research back to /directory with the research insight applied as a filter
- The /the-invisible-97 page has no link back into the product
- /compare has no next action after comparing (no "add to wallet" from comparison view was in scope but not confirmed shipped)
```

## PROMPT (paste after context)

```
You are a product strategist and UX director doing a mission-coherence audit of Daanaa. The goal is not just to find broken links — it's to find places where the journey fails to advance the mission or where pages work against each other.

**A. Donor discovery journey — completeness**
Map the ideal donor journey: "I care about food insecurity in Chicago → I find relevant orgs → I understand them well enough to give → I give."

1. At which step does the current Daanaa product most commonly fail or create friction? Be specific about which page or interaction fails.
2. The home page has a search bar, a causes grid, and a tiers explainer. Do these three elements support the same entry intent or do they fragment attention?
3. /causes/:id shows cause-area orgs. What happens when a user on a cause spotlight page wants to narrow by location? Is there a path to the directory with the cause filter pre-applied?
4. The org detail page (/org/:id) is where the donor decision happens. What is the clearest next action? Is it "visit their website," "add to wallet," "volunteer," or "compare"? If the answer is unclear, name the friction that results.
5. The wallet (/wallet) stores giving intent. But after a user adds an org to the wallet, what should happen? Is there a "ready to give" moment or does the wallet become a dead end?

**B. "Invisible 97%" narrative thread**
The platform's thesis is that most nonprofits are overlooked. Test whether this narrative is coherent across pages:
1. Does the home page establish this thesis clearly enough that a first-time user understands what Daanaa is for before scrolling?
2. The /the-invisible-97 page tells the story. Does it link naturally into the product? What's the CTA from that page and does it match the narrative?
3. Hidden gems (small, high-performing orgs surfaced in the directory) are a core expression of this thesis. Is the hidden gems mechanic visible enough on the home page? Would a first-time user understand what a "hidden gem" is?
4. The Lamp Tier system is described as "not a verdict — it reflects how much public data is available." Does this framing survive contact with a real user? Would a donor skip a Spark-tier org because of the tier label even if the org is legitimate?

**C. Nonprofit journey — claiming and dashboard**
1. A nonprofit discovers they're on Daanaa. What's their most likely path to understanding what their profile says and how to claim it? Map the steps.
2. The /for-nonprofits page introduces the claim flow. Does it explain why claiming matters (better visibility, verify data) or does it only explain how?
3. After claiming, the nonprofit dashboard (/nonprofit/dashboard/:ein) — what can an org actually do there? If the answer is "not much yet," is there a clear expectation set that this will improve?
4. The volunteer feature (/volunteer, /volunteer/submit, /nonprofit/verify-hours) — how does this fit into the nonprofit journey vs. the donor journey? Does it create a coherent loop or does it feel tacked on?

**D. Research-to-action gap**
The /research page shows sector health data (financial archetype distributions, health signal breakdowns, sector trends). It's designed for researchers and informed donors.
1. After a user on /research learns that, say, "60% of human services orgs are in the CAUTION band," what should they do next? Is there a natural path from insight to discovery?
2. Does the research page link into the directory with filters that match what the user just learned? If not, what's the missed opportunity?
3. The research page exists somewhat separately from the main nav. Who is it for and does the product make that clear?

**E. Navigation coherence**
1. Top nav: Home, Directory, Research, For Nonprofits. Is this the right set? What's missing and what would a first-time donor expect to find there?
2. The /methodology page is critical for trust — it explains what scores mean and what Daanaa is not. But is it in the nav? Is it reachable from the org detail page at the moment of trust (when a user sees a peer score and asks "what does this mean")?
3. The /compare page holds up to 4 orgs. Is it discoverable? How does a user know comparison exists?
4. The /sector-health redirect (if any) and /research — is there potential confusion between these two URLs?

For each gap or failure point identified, state: (a) which page or transition is broken, (b) what the user experiences instead of the intended journey, (c) the simplest fix (could be a link, a CTA, a redirect, or a copy change).
```

---

---

# SECTION 4 — SCORING METHODOLOGY PRESSURE TEST

## CONTEXT (paste this first)

```
Daanaa uses a peer financial context system ("v5") to show where an org's reserve strength sits relative to genuinely similar organizations.

METHODOLOGY (verbatim from the platform):
- Scores are a PERCENTILE RANK within a peer cell, not a raw quality score
- Peer cell = funding model archetype (Donation-Funded, Fee-for-Service, Endowment-Funded) × revenue band (Micro <$150K, Professional $150K-$700K, Established >$700K)
- Data source: IRS Form 990 filings via IRS SOI, NCCS, and ProPublica 990 data
- Data lag: 990 filings can lag the current year by 18-24 months
- A score of 75 means stronger reserves than 75% of its peer cell — that is all
- Health signals: HEALTHY (top quartile), STABLE (middle), CAUTION (lower — renamed "Needs support" in UI)
- 411K+ orgs have v5 scores; coverage bounded by financial data availability
- Only 3 archetypes are assigned (Donation-Funded, Fee-for-Service, Endowment-Funded) — the NTEE mapping constraint limits this
- No org can pay to improve its score — it's computed from IRS data
- Lamp Tiers (Beacon/Torch/Candle/Spark) are separate from financial context — they measure public information completeness, not quality
- Scorer is deterministic from IRS data, versioned, and runs nightly

KNOWN LIMITATIONS:
- 990 data can be 18-24 months stale
- ~1.28M of 1.7M orgs have NO v5 score (no financial data available)
- Only 3 archetypes due to NTEE mapping constraint (not a full spectrum)
- Peer cells can be small for niche NTEE categories
- The scorer doesn't capture program effectiveness, only financial reserve position
- AI-generated mission statements are labeled but may be inaccurate
```

## PROMPT (paste after context)

```
You are a skeptical donor, a nonprofit executive, and a journalist — playing all three roles. Your job is to ask Daanaa the hardest possible questions about its scoring methodology and expose every gap in the answer. After asking each question, answer it yourself as Daanaa should answer, then critique the answer for any remaining weaknesses.

**Role 1: The Skeptical Donor**

1. "You say an org's score is 'peer financial context' not a rating. But you show it prominently on every org page and it's the default sort in the directory. If it's not a ranking, why does it drive discovery? What's the real difference between a 'financial context score' and a star rating?"

2. "I see Organization A has a 'Financially healthy' badge and Organization B has 'Needs support.' I'm giving to food banks this year. Am I wrong to pick A over B based on this?"

3. "I searched for 'climate' and the first results are orgs with high peer scores. If score drives default sort, and orgs with more financial data get scores while small new orgs don't, isn't the directory just showing me bigger, more established orgs first under a different name?"

4. "Your data is from IRS 990 filings which lag 18-24 months. That means I could be looking at financial data from 2022 right now. Why should I trust this for a 2026 giving decision?"

5. "A score of 75 means better reserves than 75% of peers. Better reserves isn't the same as a better organization. An org spending 95% of revenue directly on programs will have terrible reserves and a low score. Doesn't this systematically reward orgs that hoard money?"

**Role 2: The Nonprofit Executive**

6. "My org has operated for 30 years. We are well-respected in our community. Daanaa says we're a 'Spark' tier org with no financial context score. A donor found us on your site and didn't donate because our page looked sparse. How is this fair to small orgs with limited administrative capacity?"

7. "Our latest 990 was filed 8 months ago but Daanaa still shows our 3-year-old data. Why is your data stale? And who do I call to fix it?"

8. "We're classified as 'Fee-for-Service' by your system. We're actually a community health center that receives significant government grants. How did you determine our archetype and can we dispute it?"

9. "We claimed our Daanaa listing and updated our mission description. But the score hasn't changed. What does 'claiming' actually do for us? Why bother?"

10. "If I have a high-performing program but modest financial reserves, your platform essentially hides me from donors who sort by your default. You say you're for the overlooked 97%, but your design makes it worse for small healthy orgs that don't hoard cash."

**Role 3: The Journalist**

11. "Who decides the peer group boundaries? You set Micro as <$150K, Professional as $150K-$700K, Established as >$700K. Why these cutoffs? Did you publish the methodology for the cutoff selection or did you just pick numbers?"

12. "You have 3 funding archetypes: Donation-Funded, Fee-for-Service, Endowment-Funded. But nonprofit funding models are highly varied — some orgs are hybrid. How does your system handle an org that gets 40% donations, 40% fees, 20% endowment? Which bucket is it in and why?"

13. "You say 'no org can pay to improve its score.' But you also run a vendor marketplace where partners pay Daanaa fees. The Terms page says partner fees don't affect scores. How is that structurally enforced, not just contractually promised? What stops a future team from changing this?"

14. "Your 'hidden gems' feature surfaces orgs you describe as 'small but high-performing.' But 'high-performing' by your definition means high reserve percentile in their peer group. Isn't calling a high-reserve org a 'gem' just sneaking in a quality judgment under a different label?"

15. "Daanaa uses AI to generate mission statements for orgs that don't have one. If a donor relies on an AI-generated mission to make a giving decision, and it turns out to be wrong, who is liable? What's Daanaa's disclosure obligation?"

For each question:
(a) Answer it as Daanaa should answer — honest, specific, not defensive
(b) Identify the weakest part of the answer — the thing a smart follow-up question would expose
(c) Recommend what change (product, copy, policy, or disclosure) would close the gap
```

---

---

# SECTION 5 — UX EFFICIENCY & USER-FRIENDLINESS AUDIT

## CONTEXT (paste this first)

```
Daanaa's design philosophy: "giving should feel like second nature — private, frictionless, natural. Every barrier is a product failure." The visual language uses a warm cream / deep navy / soft gold palette. The typography is a mix of display (serif italic) and body (clean sans-serif). Tailwind CSS + Radix UI.

Key user-facing pages and their current state:
- Home (/) — hero search bar, causes grid (8 pinned + rotated), hidden gems strip, tier explainer strip, "how it works" 3-step, trust callout
- Directory (/directory) — searchable, filterable (cause, state, revenue band, tier, hidden gems toggle), default sort by merit_score, 12 per page pagination
- Org detail (/org/:id) — hero header with name/city/tier badge, mission, peer financial context (V5Context component), lamp tier section, volunteer opportunities, similar orgs, leadership/compensation (from 990), full financials tab, score history chart, mistake report form
- Compare (/compare) — side-by-side, up to 4 orgs
- Wallet (/wallet) — saved org cards with health signal badges, notes field, "visit website" CTA
- Methodology (/methodology) — long-form explainer with sticky sidebar TOC, FAQ section

Known friction points from prior sessions:
- Score/tier UI has two parallel systems (v4 lamp tiers + v5 financial context) that can confuse users
- The org detail page is very long; key giving-intent actions (website link, add to wallet) may require scrolling
- Search relevance: FTS5 keyword + semantic (cosine similarity on embeddings) — results quality depends heavily on mission text and cause tags
- Directory default sort is merit_score, which favors orgs with financial data over orgs without
```

## PROMPT (paste after context)

```
You are a product designer and UX director who has never used Daanaa before, but you understand the mission: help people discover overlooked nonprofits and give with confidence. You have a direct opinion. Be honest about what's broken.

**A. First impression (Home page)**
1. The home page hero says "See the overlooked. Give with heart." followed by a search bar. A first-time user has 5 seconds before they judge the page. Does this setup tell them what Daanaa actually is — what they can do here — or does it require them to already know?
2. The home page has: hero search, causes grid, hidden gems strip, tier explainer strip, how it works 3-step, trust callout. Is this the right sequence? Is there a section that should be higher or lower?
3. The search bar placeholder says "Search by name, cause, or city…" A user who doesn't have a specific org in mind might not know where to start. What's the best entry point for an exploratory donor (someone who hasn't decided what cause to give to yet)?
4. The tier explainer on the home page shows Beacon/Torch/Candle/Spark with percentages. Is this the right place for this information? Is a first-time user ready to understand tiers before they've found a single org?

**B. Directory experience**
5. The directory defaults to sorting by merit_score. An org with no financial data gets no score. So the default sort surfaces scored orgs over unscored ones — regardless of which is more mission-aligned for the donor. What's the most user-friendly default sort and why?
6. The hidden gems toggle in the directory filters to 33K+ orgs. But most users won't know what a "hidden gem" means from the filter label alone. What should the tooltip/label say?
7. The directory shows 12 org cards per page with pagination. Is pagination the right pattern for a directory of 1.7M orgs? What's the alternative and when would it help?
8. Filter state: if a user applies filters (Chicago + Human Services + Healthy), navigates to an org, then hits back — do their filters persist? What does the UX feel like if they don't?

**C. Org detail page**
9. The org detail page is described as long. A donor who has decided to give needs two things: a reason to trust the org and a way to act (visit their website). How far down the page does the website link appear and what's in between? Is this the right order?
10. The page shows two parallel systems: Lamp Tier (visibility completeness) AND Peer Financial Context (reserve strength). A casual user will not distinguish these. What's the cognitive load risk and how would you simplify the presentation without losing the information?
11. The "similar orgs" section surfaces 9 orgs in the same NTEE + city. Is this a useful feature at the moment in the user journey where it appears (bottom of a long org page) or is it more friction than help?
12. The mistake report form is on every org page. What percentage of users who see a data error will scroll to find the mistake report form vs. just leave? What's a better UX pattern for data corrections?

**D. Wallet UX**
13. The wallet stores bookmarks and giving intent. It's localStorage only (no account required). What happens when a user switches devices? Is the loss of wallet data on device switch a friction point that needs to be surfaced proactively?
14. The wallet card shows org name, health signal badge, and notes field. What action should the wallet primarily support — reviewing saved orgs before giving, or tracking past giving? The answer changes what information belongs on the card.
15. There's no "I gave to this org" confirmation step in the wallet. After a user visits an org's website and presumably donates, they return to Daanaa with no way to close the loop. What's the simplest "close the loop" UX that doesn't require Daanaa to handle funds?

**E. Cross-cutting efficiency**
16. The methodology page is the trust anchor for the whole platform. It's accessible via a nav link, but is it surfaced at the exact moment users need it — when they're on an org page wondering "what does this score mean"? Propose a pattern that answers the question in context without requiring a full page visit.
17. The compare feature (/compare) supports up to 4 orgs. How does a user find and use this feature? Is there a discoverable "compare" action on org cards in the directory or detail pages?
18. Accessibility: the platform uses a warm cream background with cool grey text. Name the two most common accessibility failures for this kind of color palette and what to check.
19. Mobile: the directory filters (5+ filter controls) were designed for desktop. What breaks first on mobile and what's the minimum viable mobile filter UX?
20. The platform has no loading states visible in this description. For a site backed by SQLite with FTS5 and vector search, what are the latency pain points and what UX pattern prevents them from feeling slow?

For each finding:
(a) Name the specific problem in one sentence
(b) State who is most harmed (exploratory donor, returning donor, nonprofit, researcher)
(c) Propose the simplest fix — resist the urge to redesign everything
```

---

---

# HOW TO SYNTHESIZE RESULTS

After running all 5 sections, review the outputs together and answer:

1. **Top 3 security issues** — sorted by realistic exploitability, not severity label
2. **Top 3 stewardship language risks** — what could damage trust or create legal exposure if published today
3. **Biggest connectivity gap** — the single journey break that most undermines the mission
4. **Most vulnerable scoring claim** — the question a journalist would ask that Daanaa can't fully answer yet
5. **Highest-impact UX fix** — the change that would improve the most users' experience with the least code

Use this synthesis to prioritize the next sprint.

---

---

---

# SECTION 6 — SEARCH VISIBILITY & DISCOVERABILITY AUDIT

## CONTEXT (paste this first)

```
Daanaa (daanaa.org) is a React SPA (Vite) served by a Flask backend. All meta tags (title, description, og:*, canonical) are injected client-side via a usePageMeta React hook — NOT server-side rendered. The backend serves the same index.html shell for every route, and JavaScript populates the meta tags after the page loads.

Current SEO infrastructure:
- robots.txt: exists at /robots.txt (static file). Allows /directory, /category/, /org/, /about, /methodology, /for-nonprofits, /the-invisible-97, /volunteer, /events/. Disallows /api/, /admin/, /wallet, /compare.
- sitemap.xml: exists at /sitemap.xml (42 URLs) — covers static pages only. Does NOT include individual org pages (/org/:ein). References a second sitemap at https://data.daanaa.org/sitemap-index.xml (org-level pages, existence unverified).
- The sitemap includes stale URLs (/stewardship, /principles) that now redirect 301 to /about
- JSON-LD structured data: useJsonLd hook injects WebSite, FAQPage, Organization schemas client-side on relevant pages
- No server-side rendering or prerendering layer — Cloudflare Workers/Pages is not in use
- OG image: og-image.png exists in /public/. No per-org or per-cause OG images are generated at the moment
- Plausible analytics for traffic measurement (cookie-free)

Key pages and their SEO stakes:
- /org/:ein — 1.7M potential org pages; each is a unique URL that Google could index and serve for "[org name] nonprofit" queries
- /directory — the main browse page; useful for broad "nonprofit directory" queries
- /methodology — high-value for "how does Daanaa work" and long-tail "nonprofit financial context" queries
- /the-invisible-97 — story page, potential for viral/link-based discovery
- /causes/:id — cause area pages, potential for "climate nonprofits" type queries
- /category/:id — NTEE category pages

The platform's main organic search opportunity: people Googling specific nonprofit names ("[Org Name] nonprofit", "[Org Name] EIN") landing on Daanaa org pages and discovering the platform. Secondary: category/cause pages for topical giving queries.
```

## PROMPT (paste after context)

```
You are an SEO director and technical search visibility expert auditing Daanaa — a React SPA serving 1.7M nonprofit pages. The platform's biggest growth lever is organic search: donors Googling specific nonprofits, cause areas, and giving questions. Your job is to find every place where the current architecture limits that visibility and prioritize fixes ruthlessly.

**A. The SPA meta-tag problem**
1. All meta tags (title, description, OG) are set client-side by a React hook after the page loads. Google crawls JavaScript but delays it — and for a 1.7M-page site, most pages will be in the "crawl budget" queue for a long time before JS is executed. What is the realistic impact of client-side-only meta injection on Google's ability to index org pages? Be specific about:
   (a) How Google handles SPAs with dynamic meta tags
   (b) Whether Googlebot will see the correct title and description for /org/13-2661936 (a specific org page)
   (c) What percentage of the 1.7M org pages are realistically indexed within 6 months under this architecture

2. The backend serves the same index.html shell for every /org/:ein URL. That shell's <title> is "Daanaa" and the <meta description> is generic. What does Google see when it first crawls https://daanaa.org/org/13-2661936 before it executes JavaScript? What's in Google Search Console's "HTML improvements" for a site like this?

3. What is the minimum viable fix to make org page meta tags visible to crawlers? Rank these options by effort vs. impact:
   (a) Server-side meta injection in the Flask backend (inject org-specific title/description into the HTML shell before serving)
   (b) Prerendering via a service like Prerender.io or a Cloudflare Worker
   (c) Migrating to Next.js or Remix for SSR
   (d) Dynamic sitemap with org-specific metadata for Google's sitemap-based crawl hints
   Name the option that gives 80% of the benefit with 20% of the effort.

**B. Sitemap and crawl budget**
4. The sitemap.xml has 42 URLs covering static pages. The reference to data.daanaa.org/sitemap-index.xml is intended to cover org pages. If that second sitemap doesn't exist or isn't kept current, what happens to crawl coverage of the 1.7M org pages?

5. The sitemap includes /stewardship and /principles, both of which 301 redirect to /about. What does a 301 in a sitemap do to crawl budget and link equity? Should these be removed?

6. For a site with 1.7M org pages, what is the right sitemap strategy? Evaluate:
   (a) One giant sitemap (50K URLs max per sitemap is the spec limit)
   (b) Sitemap index with monthly-generated sub-sitemaps organized by NTEE or state
   (c) Dynamic sitemap endpoint (/sitemap/orgs/{page}.xml) generated on-demand by Flask
   (d) Sitemap-less reliance on Googlebot crawling through directory pagination
   Name the approach that matches Daanaa's infrastructure constraints (Flask + SQLite).

**C. Org page SEO content quality**
7. For an org like "St. Jude Children's Research Hospital" with a complete Daanaa page, what does Google see as the page's primary topic? What unique value does the Daanaa page offer over the org's own website, Wikipedia, or Charity Navigator for a searcher who Googles the org's name?

8. For a small org with no website, an AI-generated mission, and no 990 financial data — the Spark tier — what does the Daanaa page offer a searcher? Is it substantial enough content to rank, or is it thin content that Google may penalize?

9. The "similar orgs" section on org detail pages links to 9 related organizations. This is both UX and SEO-relevant (internal linking for crawl distribution). Evaluate the internal linking architecture:
   (a) How many clicks from the homepage does it take to reach a random Spark-tier org?
   (b) Does the directory pagination create a crawlable path to all 1.7M orgs?
   (c) Are the cause spotlight pages (/causes/:id) and category pages (/category/:id) effective internal linking hubs?

10. The platform has peer financial context data that no other site has. The methodology page explains it well. But is this unique content visible to search engines on org pages (where it would actually drive "XYZ nonprofit financial health" queries), or is it JavaScript-rendered only?

**D. Structured data**
11. The useJsonLd hook injects Organization and FAQPage schemas client-side. For the FAQ on /methodology, does client-side JSON-LD injection get picked up by Google's rich results? What's the delay/reliability compared to server-side injection?

12. For org pages, what structured data schema would most improve search appearance? Evaluate:
   (a) Organization schema (name, EIN, address, URL, description)
   (b) NonProfit schema (if it exists in schema.org)
   (c) Dataset schema for the financial context data
   (d) Review/Rating schema — and whether using this would conflict with Daanaa's "not a rating agency" commitment
   Name the highest-impact schema for org discovery.

13. The cause spotlight pages (/causes/:id) could potentially target queries like "best climate nonprofits 2026" or "how to give to food banks." What structured data and content structure would make these pages competitive for those queries? Note: answer must respect the no-endorsement/no-ranking commitment.

**E. Brand and discovery keyword strategy**
14. Daanaa is a new brand. What's the realistic organic search strategy for a platform in this space competing against Charity Navigator, GuideStar/Candid, and GiveWell? Where does Daanaa have a structural advantage in search and where is it disadvantaged?

15. The home page meta description is: "1.7M+ U.S. nonprofits, public records, peer context. No ads, no paid placement, no pressure." Evaluate this for:
   (a) Keyword density (does it target any specific queries?)
   (b) Click-through appeal (does it make someone searching for "nonprofit directory" want to click?)
   (c) Differentiation (does it communicate what's different from Charity Navigator?)
   Propose a revised meta description.

16. The /the-invisible-97 page is a story-first landing page about overlooked nonprofits. What's the SEO potential of this page? What query should it target, and what would need to change in the content to be competitive for that query?

**F. Technical crawlability**
17. Cloudflare is in front of Daanaa. What Cloudflare settings could inadvertently block or throttle Googlebot? What should be verified in Cloudflare's configuration?

18. The SPA uses React Router for client-side navigation. A user landing on /org/12-3456789 gets the page. But when Googlebot crawls that URL directly, it gets the index.html shell. Are there any circumstances where Googlebot would get a 404 or an error page for a valid org URL?

19. The robots.txt references /org/ as allowed. But there's no actual links from any server-rendered page pointing to org URLs (since the SPA renders everything client-side). If Google's crawl relies on link discovery rather than the sitemap, what's the implication?

For each finding:
(a) State the specific SEO impact (indexation, ranking, crawl budget, rich results)
(b) Name the user journey that suffers (a donor Googling a specific org won't find the Daanaa page)
(c) Recommend a fix ordered by: (1) quick wins in Flask/HTML, (2) medium-effort frontend changes, (3) larger infrastructure changes
```

---

---

# HOW TO SYNTHESIZE RESULTS

After running all 6 sections, review the outputs together and answer:

1. **Top 3 security issues** — sorted by realistic exploitability, not severity label
2. **Top 3 stewardship language risks** — what could damage trust or create legal exposure if published today
3. **Biggest connectivity gap** — the single journey break that most undermines the mission
4. **Most vulnerable scoring claim** — the question a journalist would ask that Daanaa can't fully answer yet
5. **Highest-impact UX fix** — the change that would improve the most users' experience with the least code
6. **Top 3 search visibility actions** — ordered by expected organic traffic impact within 90 days

Use this synthesis to prioritize the next sprint.

---

*Generated 2026-07-03 — run quarterly or before major launches*
