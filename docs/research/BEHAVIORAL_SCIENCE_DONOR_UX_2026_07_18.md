# Behavioral Science, Small-Nonprofit UX, and Donor Trust — Research Report

**Date:** 2026-07-18
**Prepared for:** Daanaa product and stewardship review
**Scope:** Web research on (1) ethically usable behavioral science in charitable giving, (2) what small nonprofits (<$700K revenue) want and resent in directory/rating platforms, (3) what makes donors trust a discovery/evaluation platform.
**Constraint frame:** Everything below was filtered against STEWARDSHIP.md. Tactics that work but violate the charter are in the "Do NOT adopt" list, not the recommendations.

---

## Executive summary

Three findings dominate the literature and practitioner discussion:

1. **The overhead myth is the single most damaging donor belief, and correcting it honestly is both effective and rare.** Gneezy et al. (Science, 2014) showed donors are averse to paying overhead themselves, not to overhead existing; framing and context dissolve the aversion. Daanaa's v5 archetype/peer-context model is already structurally positioned to be the anti-overhead-ratio evaluator. Almost no platform occupies this position credibly.
2. **Small nonprofits' core complaints about existing platforms are: ratings that punish smallness and non-growth, time-expensive profile maintenance, stale/wrong data they can't easily fix, and pay-to-play dynamics.** A free, prefilled, fast-to-claim, correction-friendly listing that never scores them on overhead or growth is exactly the gap.
3. **Donor trust in platforms is driven by accuracy, transparency, and consent** (Give.org 2026: accurate charity info 51%, fee/fund transparency 53%, assurance charities agreed to be listed 43%; 60% of platform users want platforms to get permission before creating profiles). Daanaa lists orgs from public data without opt-in, so honest labeling of unclaimed profiles and a visible corrections path are trust-critical, not nice-to-haves.

---

## (a) Top recommendations, ranked by impact vs. effort

| # | Recommendation | Impact | Effort | Check against |
|---|---------------|--------|--------|---------------|
| 1 | Overhead-myth correction module on org pages | High | Low | P3, P4, P5 |
| 2 | "Built from public data — not yet reviewed by this org" honesty label on unclaimed profiles | High | Low | P3, P9 |
| 3 | 15-minute, prefilled, forever-free claim flow designed for zero-staff orgs | High | Med | P4, P1 |
| 4 | Public methodology page + surfaced Mistake Registry + freshness dates everywhere | High | Med | P3, P6, P9 |
| 5 | Friction-minimal hand-off (verified donate links, EIN fallback, no interstitials) | High | Med | P8, P2 |
| 6 | Warm-glow, autonomy-first copy voice codified in the design system | Med | Low | P5, P2 |
| 7 | User-initiated giving rhythms in the Wallet (self-set reminders, never platform-pushed) | Med | Med | P2, P1, P5 |
| 8 | Honest storytelling: org-authored missions + scope statistics side by side | Med | Med | P3, P5 |
| 9 | No amount anchoring anywhere; the org's own page sets the ask | Med | Low | P1, P7 |
| 10 | "Third-party monitor" positioning: context, not verdict | Med | Low | P3, P4, P5 |

### 1. Overhead-myth correction module (High impact / Low effort)
Gneezy, Keenan & Gneezy ([Science, 2014](https://rady.ucsd.edu/_files/faculty-research/uri-gneezy/Science-2014-Gneezy-632-5.pdf); [Behavioral Scientist summary](https://behavioralscientist.org/the-psychology-of-overhead-aversion-and-what-it-means-for-charitable-work/)) showed donation rates fall as overhead rises **only when donors feel they personally pay for it**; when overhead is contextualized or covered, aversion disappears. Follow-up work ([Hung, Berrett & Ma, 2025](https://journals.sagepub.com/doi/10.1177/08997640241254079); [Charles, Sloan & Schubert, 2020](https://journals.sagepub.com/doi/abs/10.1177/0275074020913989)) confirms the aversion is a framing artifact. Even GuideStar, Charity Navigator, and BBB WGA jointly campaigned against the ["Overhead Myth"](https://nla1.org/nonprofit-overhead-costs/) in 2013 — then kept publishing ratio-driven products. **Action:** a short, evidence-linked "What overhead actually means" explainer on every org page where financials appear, tied to the v5 archetype context ("Donation-Funded orgs of this size typically spend X–Y on operations; that funds the staff and systems that deliver the mission"). This is honest education, not persuasion. *Check: P3 (evidence-based), P4 (protects small orgs), P5 (no shame framing of admin spend).*

### 2. Honesty label on unclaimed profiles (High / Low)
Give.org's platform research ([NonProfit Times summary](https://thenonprofittimes.com/npt_articles/donors-want-giving-platforms-to-be-accurate-transparent-charities-consent/)) found 60% of platform users want platforms to get permission before creating charity profiles, 53–55% prefer platforms listing only consenting charities, and state AGs have investigated platforms that list nonprofits without permission. Daanaa's public-data model is legitimate and common (ProPublica does the same), but the trust-preserving move is explicit provenance: "This profile is generated from IRS public filings. [Org] has not yet reviewed it. Are you with this org? Claim and correct it free." Also note that 62% of platform users say a charity's presence on a platform increases their trust in the charity — so the label protects orgs from being blamed for our data errors. *Check: P3 (honestly stated evidence), P9 (explainable), and it converts the consent gap into a claiming funnel.*

### 3. Zero-staff claim flow (High / Med)
NTEN's [Tech Accelerate data](https://www.nten.org/blog/tech-accelerate-analysis) shows micro-orgs (<1 FTE) trip risk flags on 65% of capacity measures, and the #1 scarce resource is **time** (54%), ahead of money (47%). Candid's claim flow requires approval waits of 24–48h and its [seal ladder](https://candid.org/claim-nonprofit-profile/how-to-earn-a-candid-seal-of-transparency/claim-your-profile/) (Bronze→Platinum) rewards orgs with staff capacity to feed it — practitioner blogs openly say maintaining the profile "needs to be part of a staff person's job" ([Clark Nuber](https://clarknuber.com/articles/five-tips-to-improve-your-guidestar-candid-profile/)). **Action:** claim in under 15 minutes, everything prefilled from IRS/BMF data, only corrections required, no tiered seal ladder that structurally rewards capacity, never a fee, and no recurring maintenance burden (we refresh from filings automatically). This is the strongest small-org differentiator available. *Check: P4 (equal dignity for small orgs), P1 (mission before growth — no upsell path).*

### 4. Methodology page + surfaced corrections + freshness dates (High / Med)
Give.org's [Donor Trust Report series](https://give.org/donor-trust-report) finds a persistent trust gap (67.7% say trust is essential before giving; only ~18% report high trust in charities), and that among info-seeking donors, 39% are influenced by third-party monitors. Platform trust drivers: accurate info (51%), transparency (53%). The already-planned methodology page must ship before broad outreach (per STEWARDSHIP P3 implementation note); the Mistake Registry exists but should be *visibly linked* from every score/context display, and every financial figure should carry its filing year (the 2026-07-01 compliance fix for compensation should be the pattern everywhere). Only 49% of donors currently *expect* platforms to keep info accurate — exceeding that expectation is cheap differentiation. *Check: P3, P6 (open correction), P9 (traceable decisions).*

### 5. Friction-minimal hand-off (High / Med)
ideas42's [Behavior and Charitable Giving review](https://www.ideas42.org/wp-content/uploads/2016/03/Behavior-and-Charitable-Giving_ideas42.pdf) identifies hassle friction as a first-order barrier: intention-action gaps kill more gifts than motivation deficits. Daanaa's verified donate-link pipeline is the right instrument; the recommendations are (a) keep pushing donate-link coverage and confidence, (b) never insert interstitial pages, email gates, or "before you go" prompts between intent and the org's own donate page, (c) keep the EIN fallback path (bank/DAF/check) one tap away for orgs without processors. Friction *reduction* is the one nudge with no autonomy cost. *Check: P8 (we never touch funds — hand-off purity is the feature), P2 (no capture of intent for outreach).*

### 6. Warm-glow, autonomy-first copy (Med / Low)
Warm-glow giving ([Andreoni; overview](https://en.wikipedia.org/wiki/Warm-glow_giving); [The Decision Lab](https://thedecisionlab.com/reference-guide/psychology/warm-glow-giving)) is the honest emotional frame: giving feels good, and saying so is true. Field evidence ([JEBO 2014](https://www.sciencedirect.com/science/article/abs/pii/S0167268114002492)) also warns that *manipulating* the act of giving can backfire and reduce giving. So: celebrate the donor's own choice after the fact ("you supported X"), never engineer the emotion before it. Codify in the design system: positive framing, no urgency language, no comparative framing against other donors, confirmation moments that reinforce agency. *Check: P5 (no manipulation/outrage), P2 (celebration stays private to the user).*

### 7. User-initiated giving rhythms in the Wallet (Med / Med)
Recurring/planned giving roughly quadruples lifetime donor value (median $275/yr vs $100 — [GivingTuesday data lab](https://www.givingtuesday.org/blog/recurring-giving/)), and habit formation is the mechanism. Daanaa can support habit *scaffolding* without pressure: let users set their own giving cadence reminders in the Wallet ("remind me each December", "quarterly"), fully opt-in, user-configured, device-local, silent by default. The default-effects literature ([Goswami & Urminsky](https://home.uchicago.edu/ourminsky/Charity_Default_Goswami_Urminsky.pdf)) shows defaults work but carry autonomy costs — so the user sets the default, never us. No streaks, no lapse-guilt ("you missed…"), no escalating asks. *Check: P2 (device-first, never used for outreach), P1, P5.*

### 8. Honest storytelling: identifiable missions + scope statistics (Med / Med)
The identifiable-victim effect is real ([Small, Loewenstein & Slovic, 2007](https://www.sciencedirect.com/science/article/abs/pii/S0749597806000057); [field evidence](https://www.tandfonline.com/doi/full/10.1080/00036846.2014.962226); [unit asking, 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC10977801/)) — but the ethical implementation is: surface each org's *own real* mission narrative (already generated/scraped, with `mission_source` provenance) alongside honest scale statistics, never fabricating composite "victims" or cherry-picking a single story to misrepresent scope. Notably, Small et al. found that *debiasing* people (teaching them about the effect) reduces giving to identifiable victims without raising it for statistical ones — so don't lecture donors about the bias either; just pair story and statistic honestly. *Check: P3 (traceable to evidence), P5 (no pity framing of communities).*

### 9. No amount anchoring (Med / Low)
Anchors and suggested amounts reliably pull donation sizes ([Fresh Egg overview](https://www.freshegg.co.uk/blog/the-generosity-bug-how-behavioural-science-makes-giving-addictive/); [Goswami & Urminsky](https://home.uchicago.edu/ourminsky/Charity_Default_Goswami_Urminsky.pdf)) — which is precisely why Daanaa should not use them. We are a discovery layer; the ask belongs to the org on its own page. Making "Daanaa never suggests an amount" an explicit written rule prevents future feature creep. *Check: P1, P7 (no mechanism a partner could ever pay to tune), P8.*

### 10. Position as "context, not verdict" (Med / Low)
The strongest critiques of Charity Navigator ([Chronicle of Philanthropy](https://www.philanthropy.com/opinion/charity-navigators-ratings-are-inherently-flawed-heres-a-simple-solution/), [CharityWatch on gaming](https://blog.charitywatch.org/nonprofits-might-game-the-system-economics-professor-says-of-charity-navigators-star-ratings/)) are that single scores oversimplify, punish non-growth and volunteer-heavy models, and induce orgs to game classifications. Vu Le / Nonprofit AF's long-running critique ([donor-centrism piece](https://nonprofitaf.com/2017/05/how-donor-centrism-perpetuates-inequity-and-why-we-must-move-toward-community-centric-fundraising/), [Charity Charge interview](https://www.charitycharge.com/nonprofit-resources/vu-le-nonprofit-af-funding-transparency/)) adds that ratings pressure orgs to perform accountability theater. Daanaa's existing "starting point, not a verdict" framing (2026-06-09 compliance log) is the right answer — apply it consistently to every v5 health signal and peer-context display, and say explicitly in marketing what we do NOT do (no stars, no overhead ratios, no growth requirement, no fees). *Check: P3, P4, P5.*

---

## (b) Do NOT adopt — effective-but-forbidden tactics

These appear throughout fundraising-optimization literature and convert in the short term. Each violates the charter and, per the retention research, most also damage long-term trust.

| Tactic | Why it "works" | Why forbidden | Principle |
|--------|----------------|---------------|-----------|
| **Urgency countdowns / false scarcity** ("only 3 hours left") | Loss aversion, scarcity heuristic | Manufactured urgency breeds mistrust and donor fatigue ([fundsforNGOs](https://www2.fundsforngos.org/articles-searching-grants-and-donors/how-ngos-can-balance-urgency-with-honesty-in-fundraising-appeals/), [Zeffy donor-fatigue research](https://www.zeffy.com/en-gb/blog/fundraising-fatigue)) | P5 |
| **Guilt appeals** ("while you read this, a child…") | ~3 in 5 donors admit guilt/social pressure motivated a gift | Short-term wins, long-term disengagement; savior/pity power dynamics ([Kordane](https://substack.com/home/post/p-157065992); [karma/guilt study, 2026](https://www.sciencedirect.com/science/article/pii/S0001691826001277)) | P5 |
| **Public giving displays, leaderboards, social sharing of gifts** | Social proof is a strong motivator | Structural violation of donor privacy; encourages performance giving | P2 |
| **Donor-visible peer comparisons** ("people like you gave $50") | Social norms nudge | Implies tracking, applies pressure | P2, P5 |
| **Pre-selected donation amounts or pre-checked recurring/tip boxes** | Default effect is one of the strongest nudges | Autonomy cost; we are not the ask layer anyway | P1, P8 |
| **Streaks, badges, lapse-shaming, gamified giving** | Habit-loop engagement mechanics | Engagement manipulation; guilt on lapse | P5, P1 |
| **Overhead/efficiency star ratings** | Donors ask for them; simple to compute | Punishes small orgs, drives misreporting and gaming, perpetuates the overhead myth ([Chronicle](https://www.philanthropy.com/news/with-200-000-nonprofits-rated-the-new-charity-navigator-aims-high-falls-short/)) | P4, P5 |
| **Paid seals, promoted listings, pay-to-fix visibility** | Standard directory revenue model | Independence violation; no mechanism may exist to buy visibility | P7, P1 |
| **Fabricated/stock "identifiable victims"** | IVE boosts response | Not traceable to evidence; dishonest | P3 |
| **Debiasing lectures about giving psychology at the point of giving** | Seems transparent | Empirically backfires — reduces giving without improving allocation ([Small et al.](https://www.sciencedirect.com/science/article/abs/pii/S0749597806000057)); also patronizing | P5, P10 |
| **"Before you go" interstitials / email capture gates on the donate hand-off** | Captures leads | Friction + implies outreach use of intent data | P2, P8 |

---

## (c) What small nonprofits actually say about existing platforms (synthesis)

Direct Reddit thread capture was blocked (reddit.com unfetchable from this environment; search engines returned no indexed r/nonprofit threads for these queries), so this synthesis rests on practitioner blogs, the trade press, and NTEN survey data. Recurring complaints:

- **Ratings punish smallness and stability.** Charity Navigator "rewards organizations that grow and grow and punishes organizations with humble and local goals," over-weights financials, and ignores volunteer labor ([Chronicle of Philanthropy](https://www.philanthropy.com/news/charity-navigator-confronts-its-critics-as-it-seeks-to-expand/), [Philanthropy Daily](https://philanthropydaily.com/ignore-charity-navigator/)).
- **Profile upkeep is a staffing tax.** Candid's seal ladder effectively requires a staff owner; micro-orgs (the majority of the sector, and Daanaa's <$700K bands) don't have one ([NTEN](https://www.nten.org/blog/tech-accelerate-analysis), [Clark Nuber](https://clarknuber.com/articles/five-tips-to-improve-your-guidestar-candid-profile/)).
- **Stale data with slow correction paths.** IRS 990 data lags 18–24 months; platforms present it without dating it, and orgs struggle to get errors fixed ([ProPublica data notes](https://projects.propublica.org/nonprofits/), [IRS EO BMF](https://www.irs.gov/charities-non-profits/exempt-organizations-business-master-file-extract-eo-bmf)).
- **Gaming and accountability theater.** Orgs reclassify expenses to chase ratings ([CharityWatch blog](https://blog.charitywatch.org/nonprofits-might-game-the-system-economics-professor-says-of-charity-navigators-star-ratings/)); Vu Le's critique is that watchdog pressure makes orgs perform for donors instead of communities.

**What would make them trust and engage with a free claimable listing:** free forever with no upsell ladder; claimable in minutes with everything prefilled; a real human-speed correction path; no overhead ratio, star rating, or growth expectation anywhere; peer context that makes a $200K org look coherent next to peers rather than deficient next to giants; filing-year dates on every number so stale data isn't blamed on them; and explicit labeling when a profile is machine-generated versus org-reviewed.

---

## Sources

**Behavioral science**
- Gneezy, Keenan & Gneezy, "Avoiding overhead aversion in charity," Science (2014) — [PDF](https://rady.ucsd.edu/_files/faculty-research/uri-gneezy/Science-2014-Gneezy-632-5.pdf) · [Science](https://www.science.org/doi/10.1126/science.1253932) · [Behavioral Scientist essay](https://behavioralscientist.org/the-psychology-of-overhead-aversion-and-what-it-means-for-charitable-work/)
- Hung, Berrett & Ma, "How High Is Too High?" NVSQ (2025) — [SAGE](https://journals.sagepub.com/doi/10.1177/08997640241254079)
- Charles, Sloan & Schubert, "If Someone Else Pays for Overhead…" (2020) — [SAGE](https://journals.sagepub.com/doi/abs/10.1177/0275074020913989)
- ideas42, "Behavior and Charitable Giving" — [PDF](https://www.ideas42.org/wp-content/uploads/2016/03/Behavior-and-Charitable-Giving_ideas42.pdf)
- Goswami & Urminsky, "When Should the Ask Be a Nudge?" — [PDF](https://home.uchicago.edu/ourminsky/Charity_Default_Goswami_Urminsky.pdf)
- Small, Loewenstein & Slovic, "Sympathy and Callousness" (2007) — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0749597806000057)
- Identifiable victim effect field experiment, Applied Economics (2014) — [Taylor & Francis](https://www.tandfonline.com/doi/full/10.1080/00036846.2014.962226)
- Victim identifiability & unit asking (2024) — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10977801/)
- Warm-glow giving — [Wikipedia](https://en.wikipedia.org/wiki/Warm-glow_giving) · [The Decision Lab](https://thedecisionlab.com/reference-guide/psychology/warm-glow-giving) · ["Feel the Warmth" field experiment, JEBO](https://www.sciencedirect.com/science/article/abs/pii/S0167268114002492) · [Shape of warm glow, JEBO](https://www.sciencedirect.com/science/article/abs/pii/S0167268121003991)
- Global Council for Behavioral Science overview — [gc-bs.org](https://gc-bs.org/articles/behavioral-economics-in-charitable-giving-motivations-and-barriers/)
- USC Schaeffer, "The Science of Giving" — [schaeffer.usc.edu](https://schaeffer.usc.edu/research/the-science-of-giving-using-behavioral-research-to-understand-and-expand-charitable-donations/)
- Recurring giving data — [GivingTuesday](https://www.givingtuesday.org/blog/recurring-giving/) · [Fresh Egg behavioral overview](https://www.freshegg.co.uk/blog/the-generosity-bug-how-behavioural-science-makes-giving-addictive/)

**Guilt/urgency harms**
- [fundsforNGOs: urgency vs honesty](https://www2.fundsforngos.org/articles-searching-grants-and-donors/how-ngos-can-balance-urgency-with-honesty-in-fundraising-appeals/) · [Ethics of emotional appeals](https://www2.fundsforngos.org/articles-searching-grants-and-donors/the-ethics-of-emotional-appeals-in-fundraising-campaigns/)
- [Zeffy: donor fatigue research](https://www.zeffy.com/en-gb/blog/fundraising-fatigue)
- [Kordane, "Moving Beyond Guilt-Based Fundraising"](https://substack.com/home/post/p-157065992)
- [Guilt appeals & organizational stereotypes, Acta Psychologica (2026)](https://www.sciencedirect.com/science/article/pii/S0001691826001277)

**Small-nonprofit platform experience**
- [Chronicle of Philanthropy: "Charity Navigator's Ratings Are Inherently Flawed"](https://www.philanthropy.com/opinion/charity-navigators-ratings-are-inherently-flawed-heres-a-simple-solution/) · ["Aims High, Falls Short"](https://www.philanthropy.com/news/with-200-000-nonprofits-rated-the-new-charity-navigator-aims-high-falls-short/) · ["Confronts Its Critics"](https://www.philanthropy.com/news/charity-navigator-confronts-its-critics-as-it-seeks-to-expand/)
- [Philanthropy Daily: "Ignore Charity Navigator"](https://philanthropydaily.com/ignore-charity-navigator/)
- [CharityWatch: "Nonprofits Might Game the System"](https://blog.charitywatch.org/nonprofits-might-game-the-system-economics-professor-says-of-charity-navigators-star-ratings/)
- [Nonprofit AF: donor-centrism critique](https://nonprofitaf.com/2017/05/how-donor-centrism-perpetuates-inequity-and-why-we-must-move-toward-community-centric-fundraising/) · [Vu Le interview, Charity Charge](https://www.charitycharge.com/nonprofit-resources/vu-le-nonprofit-af-funding-transparency/)
- [NTEN Tech Accelerate analysis](https://www.nten.org/blog/tech-accelerate-analysis) · [NTEN publications](https://www.nten.org/publications)
- [Candid claim-profile flow](https://candid.org/claim-nonprofit-profile/how-to-earn-a-candid-seal-of-transparency/claim-your-profile/) · [Clark Nuber: improving a GuideStar profile](https://clarknuber.com/articles/five-tips-to-improve-your-guidestar-candid-profile/)
- [Nonprofit Leadership Alliance: overhead myths vs reality](https://nla1.org/nonprofit-overhead-costs/)

**Donor trust in platforms**
- [Give.org Donor Trust Report archive](https://give.org/donor-trust-report) · [2025 sector-challenges edition](https://give.org/donor-trust-report/2025-public-awareness-charity-challenges) · [2026 openness & trust gap](https://give.org/news/donor-trust-report-2026-openness-trust-gap)
- [NonProfit Times: "Donors Want Giving Platforms To Be Accurate, Transparent, Consent Of Charities"](https://thenonprofittimes.com/npt_articles/donors-want-giving-platforms-to-be-accurate-transparent-charities-consent/)
- [Independent Sector: Trust in Nonprofits and Philanthropy 2025](https://independentsector.org/resource/trust-in-civil-society/)

---

*Research limitation noted per P3: direct Reddit thread evidence (r/nonprofit, r/NonProfitCritical) could not be captured — reddit.com is unfetchable from this environment and search engines surfaced no indexed threads for these queries. The small-org synthesis therefore leans on trade press, practitioner blogs, and NTEN survey data. A follow-up manual Reddit review would strengthen section (c).*
