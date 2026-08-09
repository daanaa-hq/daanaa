# Phase 4C Sprint Status — Quality-Gated Approach (Not Timelines)

**Status:** 🚀 **SPRINT ACTIVE** — Measurement-first, quality-gated approach locked in

---

## Executive Summary

**Phase 3** (AtAGlance component) is built & deployed. **Phase 4C** is now running a quality-gated hybrid approach:

**Workstream 1** (Mission Capital pipeline): **BLOCKED** — public API not accessible; pivoting to measurement-first approach.
**Workstream 2** (Measurement infrastructure): **COMPLETE** — Plausible setup guide ready, tracking configured, ready for gate-driven measurement.

**Key principle:** We measure until **quality gates pass**, not calendars. Measure until Gate A.1 (reliability) is solid, then iterate through A.2 (significance), A.3 (understanding), A.4 (confidence). Only then decide Phase 4 path. This de-risks the external data decision and forces us to prove value with data quality, not speed.

---

## Workstream 1: Mission Capital Pipeline

**Status:** ⚠️ **BLOCKED** (Day 1)

**What happened:**
```
Test run: 100 sample orgs ($150K-$50M revenue)
MC API endpoint: 0% match rate (0/100 orgs found)
Conclusion: API either requires auth or endpoint structure different
```

**Options considered:**
- A: Fix MC API integration (requires ToS review + potential auth)
- B: Switch to ProPublica enrichment (proven API, 156K orgs)
- C: Defer external data entirely until Phase 3 measurement complete
- **D: Hybrid** — Run measurement Week 1 with NO external data, then decide on source Week 2

**Decision:** **Option D (Hybrid)**

**Rationale:**
- Phase 3 measurement doesn't require external data — it tests display improvements
- Force ourselves to prove Phase 3 value FIRST with existing data
- Week 2: Decide on data source (ProPublica, Candid, or none) based on Phase 3 metrics
- If Phase 3 CTR +30%+: ship ANY data source. If flat: pivot strategy entirely.

**Approach revision (Quality-gated, not timeline-driven):**
- **Phase A (Measurement):** Measure until Gate A.4 passes (reliability → significance → understanding → confidence)
- **Phase B (Data source decision):** If A.4 passes, evaluate data sources through 4 quality gates
- **Phase C (Launch):** Build + ship when Phase B gates pass, not on a predetermined date

---

## Workstream 2: Measurement Infrastructure

**Status:** ✅ **COMPLETE** (Day 1)

**Deliverables:**
- ✅ `scripts/phase3_measurement_setup.py` — Plausible integration orchestrator
- ✅ `docs/PLAUSIBLE_SETUP_GUIDE.txt` — 7-step setup guide (copy-paste ready)
- ✅ `docs/.phase3_measurement_tracking.json` — Tracking config + success criteria
- ✅ `docs/PHASE3_MEASUREMENT_PLAN.md` — Query templates + success gates

**What's next (3 steps):**
1. Update `frontend/src/utils/analytics.ts` (add 3 event tracking functions)
2. Integrate tracking into 3 components (AtAGlance, WalletHeartButton, Directory)
3. Configure Plausible dashboard (custom properties + 3 goals)

**Timeline:**
- Aug 9-10: Frontend integration + Plausible config
- Aug 9 (today): Capture baseline metrics (Aug 2-8 CTR data)
- Aug 10-16: Live measurement (daily pulse checks)
- Aug 16: Generate decision report

---

## The Measurement Strategy (Gates A.1–A.4)

**Primary metric: Small org CTR** (clicks to org detail page for revenue_band='Micro')
- **Baseline:** ~40% of large org CTR (pre-Aug 9)
- **Target:** 80% parity (+100% relative improvement)
- **Gate A.2 threshold:** +30% over baseline = "Phase 3 Wins" path; ±5%–+30% = investigate further; <-5% = rollback signal

**Secondary metrics (validate via Gate A.3):**
- At a Glance visibility rate (>60% of org detail visitors)
- Micro/Large org bookmark ratio (proxy for decision-making)
- Search filter engagement (are users finding leadership/stability context useful?)

**Decision paths (Gate A.4 determines next steps, not a calendar date):**
```
Gate A.1 PASS: Measurement is stable
  ↓ (move to A.2)
Gate A.2 PASS: CTR signal is clear (+30%+, -5%, or ambiguous-but-trending)
  ↓ (move to A.3)
Gate A.3 PASS: Secondary metrics explain why (scroll, time, bookmarks align)
  ↓ (move to A.4)
Gate A.4 PASS: Confidence is high (can articulate result + next action)
  ↓
  IF "Phase 3 Wins" → Phase B (data source decision)
  IF "Neutral" → Debug via A/B test or UX iteration
  IF "Needs rollback" → Investigate regression + retry
```

---

## Stewardship Alignment

- **P3 (Evidence-Based):** Measuring real impact, not assuming
- **P4 (Small Org Fairness):** Testing if display helps small orgs reach parity
- **P6 (Mistakes Correction):** 1-week measurement window to catch problems fast

---

## Next Steps (Quality-Gated, Not Calendar-Driven)

**Foundation (Today):** ✅ COMPLETE
- ✅ Phase 3 code audit (4 fields verified live on API)
- ✅ Impeccable review (a11y fixes applied + committed)
- ✅ Measurement infrastructure (Plausible guide + tracking config ready)
- ✅ Quality gates framework documented (PHASE4C_QUALITY_GATES.md)

**Phase A.1 — Measurement Reliability (TO DO):**
- [ ] Frontend analytics integration (3 event tracking functions)
- [ ] Plausible dashboard config (custom properties + 3 goals)
- [ ] Baseline metrics capture (Aug 2-8 pre-Phase-3 CTR data)
- [ ] Deploy instrumented frontend to staging
- ✅ Exit: Day-to-day variance <15%, sample size >100 micro org clicks/day

**Phase A.2–A.4 — Iterate Until Gates Pass:**
- Daily pulse checks (measurement reliability trending?)
- Weekly cohort reviews (approaching significance threshold?)
- Root cause analysis if signal is unclear
- Final decision memo when Gate A.4 confidence is high
- ✅ Exit: Can articulate why Phase 3 helped/hurt/was neutral

**Phase B — Data Source Decision (If A.4 passes with "Wins"):**
- Evaluate ProPublica, Candid, Mission Capital through 4 quality gates
- ✅ Exit: Selected source scores ≥7/10, Stewardship P2/P3/P4/P7 pass

**Phase C — Launch (If B.4 passes):**
- Build, stage, smoke test, monitor
- ✅ Exit: Live with rolling alert coverage

---

## Commits So Far (Phase 4C)

1. `0ab90843b99` — Phase 4C foundation (Mission Capital fetch + measurement plan)
2. `0373e8d16d1` — Measurement infrastructure ready (Plausible setup + tracking)

---

## Risk Management

**Risk:** Phase 3 component still not rendering on daanaa.org (Cloudflare cache)
**Mitigation:** Measurement setup doesn't depend on visual rendering — tracks API-level impact
**Plan:** If component never renders, measurement still proves if Phase 3 logic helps (API-level CTR)

**Risk:** Small org CTR shows no improvement
**Mitigation:** Fast pivot to alternative hypotheses (search visibility? trust signals? UI placement?)
**Plan:** Use Week 1 measurement to diagnose root cause

---

## What's Different

**Old approach:** "Build Phase 4 feature A, B, C; ship and hope it works"
**New approach:** "Measure Phase 3 impact; THEN decide what Phase 4 needs"

This forces a test-first, data-driven decision process that aligns with Stewardship P3 (evidence-based) and P6 (mistakes correction).

---

## Status Symbols

- ✅ Complete (ready)
- 🚀 Active (in progress)
- ⚠️ Blocked (needs decision)
- 🤔 Decision pending (Aug 16)
- ❌ Failed (rollback mode)

