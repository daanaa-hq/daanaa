# Decision Queue

Open questions awaiting the 12-hour board-simulation cycle.
Protocol: `docs/DECISION_WORKFLOW.md`. Append new items as they arise.

Format:
```
## [open|resolved|escalated] <short title>
- Raised: <date> by <who/what>
- Principles touched: <P#s>
- Data gathered: <yes/no + pointer>
- Simulation: <link or pending>
- Resolution: <decision + DECISIONS.md date, or blank>
```

---

## [resolved] Retire lamp tier from donor-facing profiles
- Raised: 2026-07-17 by founder ("is visibility tier even important on the profile anymore")
- Principles touched: P3, P4, P5
- Data gathered: yes — tier facts duplicated by plainer page elements
- Simulation: docs/BOARD_SIMULATION_2026_07_17.md (context)
- Resolution: retired from profiles, kept for claim flow. Shipped eaca6663de6.

## [resolved] Remove Score History table + v4 ScoreBreakdown
- Raised: 2026-07-17 during profile redundancy audit
- Principles touched: P3 (percentile deltas reflect our re-scoring, not org trajectory), P9
- Data gathered: yes — snapshot deltas driven by pipeline refreshes; <5% breakdown engagement (est.)
- Simulation: docs/BOARD_SIMULATION_2026_07_17.md (95% / 75% confidence)
- Resolution: both removed, founder-approved ("none are claimed, make the change"). Shipped 37b64f758ce.

## [resolved] Audit Q: Is Plausible active in production?
- Raised: 2026-07-17 by third-party system audit
- Principles touched: P2 (privacy-respecting analytics)
- Data gathered: yes — live homepage serves plausible.io script tag (verified 2026-07-17)
- Resolution: ACTIVE in production. Not residual. STEWARDSHIP P2 note already documents it.

## [resolved] Audit Q: Volunteer workflow scope
- Raised: 2026-07-17 by third-party system audit
- Principles touched: P8 (hand-off model)
- Data gathered: yes — droplet has org-side volunteer-event endpoints (GET/POST/PATCH);
  donor-side has NO in-platform signup (UI shows "Open to volunteers — Soon")
- Resolution: describe as "discovery-only for volunteers; claimed orgs may list
  events; signup always happens on the org's own channel." Matches hand-off model.

## [resolved] Audit Q: Which backend is canonical?
- Raised: 2026-07-17 by third-party system audit
- Data gathered: yes — CLAUDE.md + memory already answer this
- Resolution: daanaa_api.py is the canonical FULL API (local, port 5000).
  scripts/droplet_api.py is the canonical PRODUCTION EDGE (serves precompute
  static files; never SQLite). Both canonical for their tier; the drift risk
  between them is real and tracked as the open contract-guard item below.

## [resolved] Audit finding: "No confirmed in-platform payment flow"
- Raised: 2026-07-17 by third-party system audit (flagged as high-severity gap)
- Principles touched: P8
- Resolution: NOT a gap — it is a charter invariant. Daanaa never handles funds
  (STEWARDSHIP P8, "Never handle funds" non-negotiable). The audit's framing is
  corrected here for the record; no payment flow will ever be added.

## [open] Donor-facing terminology glossary (audit: vocabulary drift, High)
- Raised: 2026-07-17 by third-party system audit
- Principles touched: P3 (honest signals), P5 (careful language), P9
- Data gathered: partial — audit documents drift across score/context/ranking terms
- Simulation: pending next cycle; founder approval needed on final term list
- Resolution: —

## [open] AI-output human-review policy (which outputs need review pre-publication)
- Raised: 2026-07-17 by third-party system audit
- Principles touched: P3, P10
- Data gathered: partial — current practice: missions/cause tags batch-reviewed;
  AI-discovered links labeled "found by AI, not yet confirmed" at serve time
- Simulation: pending next cycle
- Resolution: —

## [open] Full-backend vs droplet contract drift guard (audit: High)
- Raised: 2026-07-17 by third-party system audit
- Principles touched: P9; ops reliability
- Data gathered: yes — drift is real (2026-07-05 outage was this class of failure)
- Proposed: contract test asserting droplet_api routes/headers match daanaa_api
  for the shared surface; wire into principle test suite + terminology lint (audit's
  recommended Codex task)
- Simulation: pending next cycle
- Resolution: —

## [open] Charity Navigator fallback — implement live API checks?
- Raised: 2026-07-17 by founder (verify low-confidence links legally, without getting blocked)
- Principles touched: P3 (evidence-based links), P7 (disclosed source), legal/ToS compliance
- Data gathered: partial — CN fallback pool = 500 high-revenue orgs without donate links; CN ToS review NOT yet done
- Simulation: pending next cycle
- Resolution: —

## [open] web_finder success rate — is 14% acceptable or does strategy need rework?
- Raised: 2026-07-17 from orchestrator test run (14 verified / 100 attempted)
- Principles touched: P3 (only verified sites go live), resource stewardship
- Data gathered: partial — need breakdown of failure reasons (no domain exists vs. verification too strict)
- Simulation: pending next cycle
- Resolution: —
