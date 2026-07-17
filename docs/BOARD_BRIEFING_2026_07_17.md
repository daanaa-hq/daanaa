# Board Briefing: Profile Trust Signal Decisions
**Date:** 2026-07-17  
**Requestor:** Akbar Khowaja (Founder)  
**Decision Type:** Frontend UX / Trust Signal Presentation (P3, P5)  

---

## Executive Summary

We're refining the org profile page to remove two data visualizations that don't cleanly serve our core mission: helping donors make informed giving decisions. Both removals are rooted in **Stewardship Principle 3 (trust signals = evidence-based)** and have stakeholder implications. We're seeking input from Legal, Accounting/Finance, Marketing, ED, and Donor Group before deciding.

---

## Decision #1: Remove Score History Table
*("How they've tracked over time" — multi-year peer percentile movement)*

### What it shows today
A table of annual snapshots showing an org's percentile rank vs. peers, with year-over-year deltas.

### Why we're considering removal
**Stewardship P3 concern:** The deltas mostly reflect Daanaa's own pipeline re-scoring (methodology updates, data refreshes), not the org's actual performance trajectory. Showing this as "how they've tracked" implies org-level change we can't evidence. It's rank-movement framing, which our v5 financial model moved away from toward health signals (HEALTHY/STABLE/NEED_SUPPORT) instead of position.

### What replaces it
Nothing — the org's financial story is told by:
- Raw financial metrics (revenue, reserves, expenses)
- v5 peer financial context (archetype, band, health signal)
- Multi-year raw 990 data table (already present, unchanged)

### Stakeholder Questions

**Legal:** Does removing the percentile history create any liability or disclosure gap? (It doesn't — percentiles are internal rankings, not fiduciary disclosures.)

**Accounting/Finance:** Are we losing a signal that donors need to assess financial trajectory? (Probably not — raw 990 data is more honest; percentile trends are noisy.)

**Marketing:** Does this hurt donor decision-making? Is percentile history a differentiator vs. competitors? (Unlikely — most donors focus on mission + health, not rank movement.)

**ED:** Is this table something our nonprofit partners expect or rely on? (Feedback welcome.)

**Donor Group:** Does seeing "percentile went from 45th to 52nd" help your giving decision? (We suspect no — it's internal jargon.)

---

## Decision #2: Remove v4 ScoreBreakdown Inline Explainer
*("Score Breakdown" — toggleable deep dive into v4 scoring logic)*

### What it shows today
A detailed breakdown of v4 score components (operating model, financial metrics) when toggled from the accountability strip.

### Why we're considering removal
**Stewardship P3 + P9 concern:** With the lamp tier badge now retired from donor-facing profiles, this explainer is orphaned — it explains a v4 score that no longer appears on the page. The v5 financial context panel is now the canonical story. Two competing scoring narratives on one page = confusion, not clarity.

### What replaces it
- v5 Peer Financial Context section (already present, now the only one)
- Methodology link: "How we assess nonprofits →" (updated from "About this score")

### Stakeholder Questions

**Legal:** Does removing the v4 explainer create any disclosure obligation? (No — methodology is linked, not removed.)

**Accounting/Finance:** Do nonprofits or donors rely on v4 score explanations? (Unlikely — v5 is current. But feedback welcome.)

**Marketing:** Does the v4 breakdown differentiate us or confuse the story? (We think it confuses — it's technical debt.)

**ED:** Should we keep a detailed scoring explanation on every profile? (Or is the link sufficient?)

**Donor Group:** When you see a donor profile, do you want to understand the scoring deeply, or just the result + health signal? (Surface-level assumed, but validate.)

---

## Impact Summary

| Item | Removed | Impact | Recovery |
|------|---------|--------|----------|
| Score History table | 1 data viz (low importance) | Cleaner profile, less confusing deltas | Raw 990 table stays, methodology link added |
| v4 ScoreBreakdown | 1 toggle-able section | Remove technical debt, reduce narrative confusion | v5 context + methodology link stays live |

**Net effect:** Profile becomes simpler, cleaner, more honest about what we actually know.

---

## Timeline & Process

**By EOD 2026-07-18:**  
- Legal: any disclosure concerns?
- Accounting/Finance: any data integrity concerns?
- Marketing: donor impact assessment?
- ED: nonprofit partner feedback?
- Donor Group: what do you actually use?

**2026-07-19:** Founder reviews feedback, decides.

**If approved:** Ship with next deploy (same day).

---

## Principle Alignment

**P3 (Trust signals = evidence-based):** ✅ Both removals reduce noise; percentile deltas are signal-to-noise killer.  
**P5 (No weaponized transparency):** ✅ Removing confusing score details = clearer, more humane framing.  
**P9 (Decisions explainable later):** ✅ This briefing is the record.  
**P10 (AI is tool, not authority):** ✅ Human board + stakeholders decide, not AI.

---

## Questions for Board

1. Do these removals align with your stewardship interpretation?
2. Any stakeholder concerns we haven't surfaced?
3. Should we gather donor feedback before shipping, or after via analytics?

