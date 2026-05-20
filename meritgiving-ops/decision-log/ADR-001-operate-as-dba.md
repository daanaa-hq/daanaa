# ADR-001: Operate MERIT as DBA under EcoMargins LLC until MeritGiving LLC forms

## Status
Accepted

## Date
2026-05-19

## Departments affected
finance, legal, strategy

## Context

MERIT needs to launch operations (account signups, infrastructure, vendor relationships) immediately. Forming a new LLC takes 1–4 weeks depending on path (DIY Texas SOS, service-assisted, or attorney-assisted). Waiting for the LLC blocks all parallel execution.

EcoMargins Consulting LLC is an existing Texas LLC owned by the founder. It has clean books, a credit card, and the legal capacity to operate businesses. Adding a DBA ("Doing Business As") for MERIT is a low-friction option.

## Decision

Operate MERIT as a DBA under EcoMargins Consulting LLC during Phase 0 setup. All MERIT expenses charged to EcoMargins credit card. All MERIT income (e.g., tips) flows to EcoMargins. Track all MERIT transactions with class/location code "MERIT" in QuickBooks.

When MeritGiving LLC formation is complete (target: Gate 1, Week 2):
1. Document inter-entity capital contribution (attorney-drafted)
2. Reimburse EcoMargins for accumulated MERIT expenses
3. Transfer DBA filing
4. Future expenses on MeritGiving card; future income to MeritGiving

## Consequences

- **What gets easier:** Immediate execution of parallel tracks (account signups, credit applications, infrastructure). No blocking on LLC paperwork.
- **What gets harder:** Bookkeeping discipline becomes critical — must keep clean class/location tagging in QBO. CPA must verify proper transfer at LLC transition.
- **What we'll measure:** Clean books at monthly close. CPA sign-off at quarterly review. Successful inter-entity transfer documentation when MeritGiving LLC funds.

## Alternatives considered

- **Option A: Wait for MeritGiving LLC formation before starting**
  - Pros: cleanest accounting from day one
  - Cons: blocks 2–4 weeks of parallel execution; momentum loss
  - Why not: speed matters; LLC paperwork is mechanical

- **Option B: Operate entirely under EcoMargins (no DBA) forever**
  - Pros: simplest legal structure
  - Cons: brand confusion; mixed liability; mission lock harder to enforce in consulting LLC
  - Why not: mission lock requires dedicated entity

- **Option C: Use a third-party fiscal sponsor (Code for America, etc.)**
  - Pros: 501(c)(3) status immediately
  - Cons: governance overhead; less direct control
  - Why not: premature; revisit at Gate 10 (Month 15)

## Reversibility

**Easy.** DBA can be canceled when MeritGiving LLC formation completes. Inter-entity accounting cleanup is mechanical with CPA support.

## Related

- ADRs: ADR-005 (org structure)
- Risks: R-001 (claim fraud — requires legal entity clarity in claim comms)
- Strategy: `funding-strategy.md` (EcoMargins → MeritGiving funding flow)
