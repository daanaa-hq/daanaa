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
