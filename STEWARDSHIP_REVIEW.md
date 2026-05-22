# Stewardship Compliance Review

**Date:** 2026-05-20  
**Reviewer:** Claude Code (claude-sonnet-4-6)  
**Scope:** Full codebase audit against all 12 principles of the Founding Stewardship Commitment

---

## Review Method

Grep-based scan of all frontend pages, components, API layer, and data pipeline scripts.
Findings are organized by principle. Each principle received a finding and a status.

---

## Findings by Principle

### Principle 1 — Mission before growth

**Finding:** No upsell flows, referral loops, or engagement-optimization patterns found.
The platform has no advertising infrastructure, no viral sharing mechanics, and no dark
patterns to inflate session time. The Giving Wallet is private and local-only. The directory
is open without login. Revenue disclosure in FAQ is transparent: "We are currently in public
beta and not yet monetized. When we do generate revenue, it will come from institutional
tools, never from listing fees, score manipulation, or selling donor data."

**Status: Compliant**

---

### Principle 2 — Privacy is a core principle

**Finding:** No analytics services (Google Analytics, Mixpanel, Segment) found in any
frontend file. No tracking cookies set. Giving Wallet and saved organizations use
`localStorage` only — data never leaves the browser. Legal.tsx explicitly states the
platform does not collect personal information from visitors, does not use tracking cookies,
and does not sell or share user data. No AI inference on user behavior detected.

**Status: Compliant**

---

### Principle 3 — Trust signals must be evidence-based

**Finding:** Every trust indicator (tier, score, IRS badge, financial metrics) traces to a
specific public record: IRS Business Master File, ProPublica 990 XML, or computed percentile.
No synthetic or imputed claims presented without a source label. DataFreshnessBadge component
shows the tax year every score is based on. Score explainer ("How is this scored?") is always
available inline. Partial and unavailable data states are shown honestly rather than omitted.

One prior issue resolved: program_expense_pct was displaying values outside the valid 0–100
range. This has been removed from all displays and nulled in the database via
`scripts/data_audit_fix.py` (2026-05-20).

**Status: Compliant**

---

### Principle 4 — We are still testing and validating our methods

**Finding:** FAQ page states "We are currently in public beta." No component presents
MERIT tiers or scores as finalized or certified. Score explainer describes methodology
transparently ("We compare reserves, program spending, and revenue stability against
nonprofits in the same cause area and revenue range"). No claim of predictive accuracy
or impact measurement is made.

**Status: Compliant**

---

### Principle 5 — Small organizations deserve fairness

**Finding:** Spark and Ember tiers have explicitly non-judgmental copy:
- Spark: "A starting point, not a judgment. Many excellent community organizations begin here."
- Ember: "It reflects data availability, not the quality of its work."
- TiersPage includes a dedicated section: "A lower tier is not a grade," explaining that
  a 990-N filing reflects what the government collects, not organizational quality.

Score calculation uses peer groups (same NTEE category, similar revenue band) to prevent
large organizations from appearing superior by size alone. The scorer treats all organizations
in a peer group on equal footing.

**Status: Compliant**

---

### Principle 6 — We do not weaponize transparency

**Finding:** No shaming language found in any UI copy. Negative states (low score, limited
data, no website) are framed as information gaps, not failures. Financial distress indicators
(negative net assets, low savings runway) are shown with neutral labels and warm amber/red
colors that signal "be aware" rather than "avoid." No org is labeled untrustworthy or
fraudulent based on data alone. The platform links to IRS Tax Exempt Search and ProPublica
as external verification, not as indictment tools.

**Status: Compliant**

---

### Principle 7 — Mistakes must be corrected quickly

**Finding:** MistakeRegistry component exists and is displayed on every org detail page.
Legal.tsx provides a correction contact (hello@meritgiving.org). FAQ answer for data errors
explains the IRS-first correction path and offers direct contact. Data audit script
(`scripts/data_audit_fix.py`) provides a documented, repeatable correction pathway for
pipeline errors. The compliance log in STEWARDSHIP.md creates a durable record of issues
found and corrected.

**Status: Compliant**

---

### Principle 8 — Independence must be protected

**Finding:** No partner or sponsor integrations found. No premium placement or boosted listing
logic in the API or frontend. Sort/filter logic is purely data-driven (score, tier, revenue,
name, state). No affiliate links or sponsored content. FAQ explicitly states: "No organization
can pay to change its tier" and "Any platform that lets organizations pay for a better score
is not using real data."

**Status: Compliant**

---

### Principle 9 — We do not control donor funds

**Finding:** All Give buttons link externally to the organization's own website or the IRS
fallback record. No payment processor (Stripe, PayPal, etc.) integrated anywhere. Multiple
explicit statements in the UI: "MERIT never receives, holds, or processes your money."
The Giving Wallet is a tracker, not a payment system — clearly labeled as such.

**Status: Compliant**

---

### Principle 10 — Decisions should be explainable later

**Finding:** Scoring methodology is documented in `api/merit_scorer_v3_3.py` with inline
comments explaining peer group construction, band thresholds, and scoring logic. The scorer
version is pinned in CLAUDE.md and the scoring history (v1 through v3.3) is preserved for
reference. Tier assignment logic is in `TrustBadge.tsx:getTierFromOrg` and readable without
domain expertise. CLAUDE.md documents all architecture decisions, active vs. legacy files,
and known gotchas for future contributors.

**Gap noted:** No formal changelog or ADR (Architecture Decision Record) directory exists.
Decisions are documented inline but not in a structured log. Recommend creating
`docs/decisions/` if the team grows beyond two people.

**Status: Compliant (with recommendation)**

---

### Principle 11 — AI is a tool, not a replacement for responsibility

**Finding:** AI agent (Claude Code) operates under this stewardship commitment as a
signatory. All code changes are committed with attribution and are reviewable in git history.
The agent does not auto-deploy — changes require explicit human approval and action.
CLAUDE.md specifies that the AI agent must read STEWARDSHIP.md before any work session.
The agent's outputs (code, copy, scripts) are traceable to specific requests and are
reversible.

**Status: Compliant**

---

### Principle 12 — Principles are strengthened, not quietly weakened

**Finding:** STEWARDSHIP.md is version-controlled. CLAUDE.md references it and requires
compliance review for all contributors including AI agents. This review document creates a
dated record of the current state. Any future weakening of a principle would require an
explicit change to STEWARDSHIP.md with a dated entry in the Compliance Log.

**Status: Compliant**

---

## Summary

| Principle | Status |
|---|---|
| 1. Mission before growth | Compliant |
| 2. Privacy is a core principle | Compliant |
| 3. Trust signals must be evidence-based | Compliant |
| 4. Still testing and validating | Compliant |
| 5. Small organizations deserve fairness | Compliant |
| 6. Do not weaponize transparency | Compliant |
| 7. Mistakes must be corrected quickly | Compliant |
| 8. Independence must be protected | Compliant |
| 9. We do not control donor funds | Compliant |
| 10. Decisions should be explainable | Compliant (with recommendation) |
| 11. AI is a tool, not a replacement | Compliant |
| 12. Principles are strengthened | Compliant |

**Overall: Full compliance across all 12 principles.** One recommendation noted for Principle 10.

---

## Issues Resolved During This Review

| Issue | Found | Fixed |
|---|---|---|
| `program_expense_pct` displaying values outside 0–100 range | OrganizationDetail.tsx | Removed from UI; DB values nulled via data_audit_fix.py |
| `months_of_reserve` sentinel values (±999) displayed as data | merit_api.py | CASE expression in SQL + Python clamp; DB recomputed |
| "IRS-verified 501(c)(3)", "Form 990" jargon in public copy | 6 frontend files | Replaced with plain English throughout |
| TrustBadge TIER_MICROCOPY using "IRS recognized 501(c)(3)" | TrustBadge.tsx | Replaced with "registered nonprofit" |

---

*This review was conducted by Claude Code (claude-sonnet-4-6) as a stewardship signatory.*  
*It is subject to human review and challenge per Principle 11.*
