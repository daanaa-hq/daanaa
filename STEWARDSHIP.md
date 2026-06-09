# Founding Stewardship Commitment — Daanaa

This commitment applies to every contributor connected to the platform,
including founders, employees, volunteers, advisors, contractors, vendors,
automation systems, and AI agents operating on behalf of the platform.

Any AI system, workflow, or autonomous agent deployed within Daanaa must
also be designed, configured, monitored, and governed in alignment with these
principles.

Human operators remain responsible for the behavior and outcomes of the AI
systems they create, approve, or supervise.

Daanaa is built on trust. These principles are not marketing language,
and they are not optional guidelines. They exist to protect the integrity of
the work, the dignity of the organizations represented here, and the privacy
of the people who use the platform.

By joining, contributing to, or operating within this platform, I acknowledge
and agree to the following:

---

## 1. Mission before growth

The purpose of Daanaa is to help people make more informed and sincere
giving decisions. Growth, visibility, partnerships, automation, and revenue
can never override that purpose.

**How implemented:** No paid placement, no sponsored results. Scoring derives
entirely from public IRS and ProPublica data. Revenue model is not yet defined
and must not compromise this principle when it is.

## 2. Privacy is a core principle

Donor privacy must be protected at all times. We do not build systems that
encourage public performance, social pressure, or exposure of personal giving
activity.

AI systems must also be designed to minimize unnecessary data collection,
retention, exposure, and inference.

**How implemented:** The Giving Wallet is localStorage-only — no giving activity
is stored on our servers. Analytics will use a privacy-respecting provider
(Plausible) with no third-party tracking. No social sharing of giving activity
is surfaced or encouraged.

## 3. Trust signals must be evidence-based and honestly stated

Any badge, score, verification, ranking, insight, recommendation, or trust
indicator displayed on the platform must be supported by real, reviewable data.

AI-generated conclusions must remain explainable, reviewable, and traceable to
underlying evidence wherever possible.

If evidence is weak, incomplete, outdated, or uncertain, we must clearly say so.
No contributor or AI agent should present assumptions, experiments, or unverified
outputs as established truth. We remain intellectually honest about what we know,
what we believe, and what our methodology has not yet resolved.

**How implemented:** Scores derive from IRS SOI, NCCS, and ProPublica 990 data.
Scorer is versioned (v1) with snapshots. The Mistake Registry component on every
org page provides a visible corrections path. A public methodology page is planned
pre-launch and must ship before broad outreach begins.

## 4. Small organizations deserve fairness

We recognize that smaller nonprofits may have limited administrative capacity,
limited filings, or less polished public visibility. Our systems should not
automatically disadvantage sincere organizations simply because they are
smaller or less digitally mature.

AI systems should be regularly reviewed for unintended bias toward scale,
visibility, language sophistication, geography, or institutional resources.

**How implemented:** Scores are benchmarked against NTEE peer groups, not the
full registry — a $200K community org is never compared against Kaiser.
The hidden gems mechanic surfaces small, financially healthy, low-profile orgs
specifically. Cause tag coverage for data-dark small orgs is a known gap and
an active work item.

## 5. We do not weaponize transparency

The goal of Daanaa is to inform responsibly, not to shame organizations
publicly. We communicate carefully, respectfully, and with awareness that our
work affects real people and communities.

AI systems must never be optimized for outrage, humiliation, engagement
manipulation, or adversarial exposure.

**How implemented:** Copy voice rules prohibit shame language, negative framing,
and hyphenated jargon. The lamp tier metaphor is additive — it raises visibility,
not a verdict. No "F-rated" or failure framing exists in the product.

## 6. Mistakes must be corrected quickly

If errors are identified in our data, logic, workflows, AI outputs, or
presentation, we correct them openly and promptly.

Accuracy is more important than protecting ego, automation efficiency, or
institutional appearance.

**How implemented:** The Mistake Registry component is present on every org
detail page. Data errors found during pipeline runs are corrected in the source
and re-scored. Scoring methodology and known limitations are documented publicly.

## 7. Independence must be protected

No partner, sponsor, nonprofit, donor, vendor, investor, advertiser, or
outside party may influence verification outcomes, trust indicators,
visibility, rankings, or platform standards through money, pressure, or
access.

AI systems must not be secretly tuned or influenced to favor paying entities,
strategic relationships, or political interests.

**How implemented:** Scores and tiers are computed algorithmically from public
data with no human curation of individual org outcomes. No mechanism exists
to boost or suppress an org's score outside the published methodology.

## 8. We do not control donor funds

Daanaa must remain operationally independent from the movement of donor money.
We do not hold donations, operate escrow structures, or create systems that
compromise neutrality and trust.

**How implemented:** All giving is a hand-off — donors act on the org's own
site or by EIN through their own bank, DAF, or check. Daanaa records intent
in the Giving Wallet but money never flows through us. No payment processor
is integrated. An "Add to Giving Wallet" prompt after the hand-off is a
planned UX improvement to close the loop without touching funds.

## 9. Decisions should be explainable later

Important decisions, methodology changes, model assumptions, scoring updates,
and principle adjustments should be documented clearly enough that future team
members, auditors, communities, and users can understand why they were made.

**How implemented:** Architecture and decisions are documented in CLAUDE.md.
Scoring is versioned with a score_snapshots table. This document and its
revision log provide a traceable record of principle changes over time.

## 10. AI is a tool, not a replacement for responsibility

AI helps us operate lean and scale responsibly, but accountability remains
human.

Every significant AI-assisted output should be reviewable, challengeable, and
subject to correction.

No AI system should be treated as morally authoritative, infallible, or beyond
oversight.

**How implemented:** Scoring is deterministic from IRS data, not AI-generated.
AI is used for cause tag extraction and embeddings — outputs are batch-reviewed
before surfacing. Local inference (llama.cpp/Vulkan on the Daanaa server) is
preferred for batch tasks to keep AI usage auditable and cost-controlled.

## 11. Principles are strengthened, not quietly weakened

These principles may evolve over time, but they should never be diluted
silently for convenience, growth pressure, automation efficiency, or financial
opportunity.

Any meaningful change should be documented along with the reasoning behind it.

**How implemented:** All principle changes are recorded in the Revision Log
below. The Stewardship Acknowledgment requires explicit re-sign-off from
contributors when principles change materially.

---

## Stewardship Acknowledgment

I understand that Daanaa is being built as a long-term public trust
project and not merely as a commercial product.

I understand that these principles apply equally to human contributors and the
AI systems operating on behalf of the platform.

I agree to act in alignment with these principles, raise concerns when I
believe they are being compromised, and contribute to the work with honesty,
care, accountability, and humility.

---

## Signatories

| Name / Agent Identifier | Role / System Function | Date |
|---|---|---|
| Akbar Khowaja | Founder | 2026-05-20 |
| Claude Code (claude-sonnet-4-6) | AI Engineering Agent | 2026-05-20 |

---

## Revision Log

| Date | Author | Change |
|---|---|---|
| 2026-05-24 | Claude Code | Rebranded MERIT → Daanaa; consolidated 12 → 11 points (merged pre-launch testing language into principle 3); added "How implemented" section to each principle; no principles removed |

---

## Compliance Log

| Date | Reviewer | Finding | Status |
|---|---|---|---|
| 2026-05-20 | Claude Code | Full compliance review — see STEWARDSHIP_REVIEW.md | Completed |
| 2026-06-09 | Claude Code | Bi-weekly cause spotlight (/causes/:id) review. Strong P4 alignment (it is the cited hidden-gems implementation; fixed rotation gives every cause equal turns). P1/P5/P7/P10 pass (algorithmic selection, additive framing, no curation, deterministic). Gap found on P3+P9: featured "hidden gems" shown without their reviewable basis. Fixed: added on-page selection criteria (small + top peer-group rank + public mission), "starting point, not a verdict" framing, a methodology link, and a data-freshness date. | Completed |
