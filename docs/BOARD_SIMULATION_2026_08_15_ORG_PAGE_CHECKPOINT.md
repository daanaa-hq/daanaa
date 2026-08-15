# Board Simulation — Org Page Checkpoint & Donor Trust Recommendations

**Date:** 2026-08-15
**Convened by:** Founder ("review recommendations with codex plug and simulate a board meeting and then make sure that we are following our charter and stewardship guidelines")
**Authority:** Advisory. Resolutions marked FOUNDER become binding only on founder approval.
**Governing documents:** `institution/DAANAA-CHARTER.md`, `STEWARDSHIP.md`, `PRIVACY-INVARIANTS.md`, `DESIGN.md`
**Continuity note:** This session's org-page work directly overlaps `docs/BOARD_SIMULATION_2026_07_25.md` (org profile redesign). That simulation's resolutions R1-R8 were never formally closed — R2 (EIN as universal giving path) and R3 (payload budget for the decision view) in particular are still open. This checkpoint reconciles tonight's work against those open resolutions rather than treating the org page as a fresh topic.

---

## Part 1 — Compliance review of tonight's changes

A parallel, more rigorous compliance audit is running via Codex (`/tmp/daanaa_compliance_audit_20260815.md`, not yet returned as of this writing) — this section is the board's own pass, to be reconciled against that audit once it lands, not a substitute for it.

| Change | Principle | Finding |
|---|---|---|
| ProvenanceLayers removed (100% duplicate content) | P3, R1 (July 25) | **PASS.** Every fact it showed already existed elsewhere on the page in a more readable form (pills vs. raw NTEE code). Directly advances R1 ("everything earns its place against the giving decision or moves behind disclosure") |
| 1:1 contrast bug fixed | Accessibility, not a named principle but a WCAG AA obligation DESIGN.md commits to | **PASS.** Measured before/after: ~1.0-1.2:1 → normal legible contrast. This was a real defect, not a judgment call |
| Empty financial-section wrappers gated on actual data | P4 (small/data-sparse orgs) | **PASS, and directly on-topic for R7** ("small organizations are not penalized by new fields") — a blank bordered gap on a small org's page read as broken, which is its own form of penalizing smallness |
| "At-risk" → "Need support", red → neutral | P5 (no shame framing), DESIGN.md's "No Shame Rule" | **PASS on intent. Needs a vocabulary check** — DESIGN.md documents the canonical health-signal vocabulary as HEALTHY/STABLE/MAY_NEED_SUPPORT (three terms, from `merit_health_signal_v5`). Tonight's fix introduced "Need support" as a *fourth*, separately-sourced label (`org_stability_signal`, a different composite field) on a different component. Two vocabularies for a similar concept is exactly the kind of terminology drift the 2026-07-17 glossary resolution was meant to prevent. **Flagged for Codex's audit to confirm precisely; not waved through here.** |
| V6.1 scorer: Tier 3 threshold 5→3 peers | P3 (evidence-based), P2 (privacy) | **CONDITIONAL — highest-scrutiny item tonight.** A percentile computed against only 3 peer orgs is a much thinner statistical basis than 25+, and a smaller peer group is closer to identifying an individual org's position relative to named-adjacent orgs. The confidence label (LOW/MEDIUM/HIGH) is displayed, which is the right instinct — but "does a 3-peer comparison group risk indirectly exposing something about one of those 3 specific orgs" is a privacy question this board has not rigorously worked through. **Sent to Codex's audit explicitly; treat as open until that returns.** |

---

## Part 2 — Evidence pack

| Fact | Value |
|---|---|
| Org page sections removed tonight | 1 full section (ProvenanceLayers), ~350px of dead space fixed (2 components) |
| V6 percentile coverage | 29.5% → 76.4% (554.9K → 1.434M orgs), confidence split: 58.9% HIGH / 17.5% MEDIUM / 23.6% LOW |
| Search latency (measured this session, informal) | ~645ms — far better than the 9.2s the July 25 board flagged as the top-priority blocker (R5), though not independently re-verified under the same load conditions as that measurement |
| R2 (EIN as universal giving path) | **Still not implemented.** EIN is one of four small stat items in a horizontal row (Founded/Revenue/Employees/EIN), not promoted as a first-class DAF-grant path per the board's prior framing |
| R3 (payload budget for decision view) | **Not formally implemented as a budget**, but tonight's cuts (removing ProvenanceLayers, gating empty sections) move the page in that direction without a stated target number |
| DonorVoice.tsx copy | "X supporters have shared notes" — confirmed by Codex's research pass to be device-local data displayed with copy that could be misread as cross-donor social proof |
| Research brief "don't build" list | Streaks, scarcity messaging, live donor counters, leaderboards — all explicitly rejected with citations, none proposed for implementation |

---

## Part 3 — Deliberation

**Participants (simulated):** legal counsel (nonprofit regulatory); DAF program officer; donor archetypes (small-dollar spontaneous, diligence-driven major donor); nonprofit sector researcher; AI/ML engineer; privacy engineer; small nonprofit executive director.

### Finding A — Tonight's work is real progress on R1, but R2 and R3 are still open and shouldn't be forgotten

**Donor (small-dollar):** The duplicate section coming out is good — I remember scrolling past what felt like the same facts twice and wondering if the page was broken. But I still don't see the EIN presented as *my* way to give if I'm giving through a donor-advised fund.

**DAF program officer:** Confirmed — nothing changed on my ask from three weeks ago. The EIN is still buried in a small stat row, formatted the same as "Founded" or "Employees." For DAF-routed money, that's backwards.

**Board consensus:** Tonight's fixes are consistent with R1's spirit and should be logged as partial progress, not treated as closing the July 25 findings. R2 and R3 remain open and should stay visible in the decision queue, not quietly dropped because a different session touched the same file.

### Finding B — The "Need support" vocabulary question is small but real

**Researcher:** Two different composite fields (`merit_health_signal_v5` and `org_stability_signal`) computing similar-sounding "how healthy is this org" signals, with different label sets, is a maintenance and trust risk even before it's a donor-facing confusion risk — which label does a donor see, and do the two ever disagree on the same org?

**AI/ML engineer:** Worth noting `org_stability_signal` isn't in production yet (`droplet_api.py` doesn't have it) — this is a pre-ship catch, which is the right time to catch it, but it should be resolved before it ships, not after.

**Board consensus:** Do not ship `org_stability_signal` to production until it's reconciled with the existing three-term vocabulary — either by unifying the underlying computation or by clearly differentiating what each one measures in its own copy. Codex's compliance audit is checking this precisely; this board defers to that finding rather than guessing.

### Finding C — The V6.1 threshold-lowering is the one item that needs real privacy scrutiny, not a rubber stamp

**Privacy engineer:** I want to be direct about what "3 scoreable peers" means. If a donor — or worse, a competitor, or a disgruntled former employee — can narrow the peer group enough (NTEE2 category × revenue band × region is fairly specific), a "this org ranks in the Nth percentile of 3" could be reverse-engineerable to "which of these 3 named orgs is this." That's not hypothetical; NTEE2×band×region cells can be small in rural areas or niche categories by construction.

**Legal counsel:** The confidence label (LOW at <3 peers) is a real mitigation, but a label is not the same as suppression. Worth asking directly: does LOW confidence also suppress the percentile number itself, or just annotate it?

**AI/ML engineer:** Per this session's own scorer code: the percentile is NULL below 3 peers, and shown with a LOW confidence label between 3-24 peers — it is not suppressed at 3, only below it. So the minimum group that ever gets a visible percentile is exactly 3.

**Board consensus:** This needs a specific answer, not an assumption, before it's considered settled: for the smallest peer groups (3-5 orgs), is a percentile alone — without revealing the other orgs' identities or exact values — actually a privacy exposure, or is it structurally safe because percentile rank doesn't reveal magnitude? The board's initial read is that percentile rank (not raw revenue) is a weaker signal than an exact number, which is a meaningful mitigation — but this deserves Codex's audit finding, not the board's intuition, as the final word.

### Finding D — The research brief's recommendations are low-risk and mostly already-compliant-pattern extensions

**Legal counsel:** I reviewed the 8 recommendations against the Charter directly. Recommendation 3 (explicitly *not* building a donor counter) is the most important one on the list — it closes off a real risk before anyone builds it, and it's correctly framed as a decision record, not a feature.

**Researcher:** Recommendation 7 (DonorVoice copy fix) is the only one that's a genuine bug, not an enhancement. It should be treated with more urgency than the others — an unintentional misleading trust signal is exactly what P3 exists to catch fast, per P6 ("mistakes must be corrected quickly").

**Board consensus:** Recommendations 1, 2, 4, 5, 6, 7, 8 are approved for implementation as a low-risk batch — copy and disclosure additions, no new judgment calls, each individually checked against Stewardship in the brief itself. Recommendation 3 (don't build) is adopted as a standing decision record.

### Dissents recorded

- **DAF program officer dissents** from treating R2 as lower priority than tonight's other fixes: "the EIN-as-primary-path finding is three weeks old and still hasn't moved. That's the biggest single donor-facing gap on this page, bigger than a duplicate section."
- **Privacy engineer dissents** from approving the V6.1 threshold change as fully resolved pending only Codex's audit: "I want this board to see the actual answer, not just be told an audit is coming. If the audit comes back CONDITIONAL, this board should reconvene before the 76.4% coverage number is used publicly anywhere."

---

## Part 4 — Resolutions

**R9 — Reconcile the "Need support" vocabulary with the existing HEALTHY/STABLE/MAY_NEED_SUPPORT terms before `org_stability_signal` ships to production.** Do not deploy this feature to `droplet_api.py` until resolved. **Engineering, autonomous — proceed, gates deploy only**

**R10 — V6.1's lowered peer-group threshold (3-peer minimum) is CONDITIONAL pending Codex's compliance audit finding on re-identification risk.** If the audit returns PASS with clear reasoning, this resolves automatically. If CONDITIONAL or FAIL, this board reconvenes before the 76.4% coverage figure is cited in any founder-facing or public materials. **FOUNDER — do not treat as settled until the audit lands**

**R11 — Implement the research brief's low-risk batch (Recommendations 1, 2, 4, 5, 6, 7, 8).** Recommendation 7 (DonorVoice copy) gets priority treatment as a live bug, not a backlog enhancement. **Backend/copy, autonomous — proceed**

**R12 — Recommendation 3 (do not build donor-activity counters) is adopted as a standing decision.** Logged in `DECISIONS.md` so it is not re-proposed without this context. **Complete**

**R13 — R2 (EIN as universal giving path) and R3 (payload budget) from the July 25 simulation remain open and are re-affirmed as priorities, not superseded by tonight's smaller fixes.** **FOUNDER — carried forward, unresolved**

**R14 — Tonight's dedup and empty-state fixes are approved as consistent with R1 and R7.** Already shipped; no further action needed. **Complete**

---

## Part 5 — Awaiting founder

R10 is provisional pending the Codex compliance audit — this board does not consider the V6.1 coverage number safe to cite publicly until that returns and is reviewed. R13 asks the founder to confirm R2/R3 are still the intended next major org-page work, or to explicitly reprioritize. R2 in particular has now been open for three weeks across two separate board sessions without a founder decision either way — the board notes this as a pattern worth naming, not just resolving once: open FOUNDER-gated items should get a yes/no/not-now within a bounded window, or they silently rot in the queue the way R2 has.

This checkpoint will be updated with the Codex compliance audit's findings once it returns, and R10 will be closed out explicitly rather than left ambiguous.
