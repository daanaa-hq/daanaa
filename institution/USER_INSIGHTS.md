# User Insights

## Document Control

| Field | Value |
|---|---|
| Purpose | Track user signals, friction, and evidence of nonprofit/public value. |
| Responsible role | Nonprofit Success Steward and Product Steward. |
| Authority level | Evidence and hypothesis registry; not product roadmap by itself. |
| Review trigger | Weekly review, repeated support issue, analytics change, user interview, or launch step. |
| Editable status | Editable by ordinary agents with privacy-preserving evidence. |
| Dependencies | `CURRENT_STATE.md`, `HYPOTHESES.md`, `PRIVACY-INVARIANTS.md`. |
| Retirement condition | Retire when replaced by privacy-preserving product analytics and support synthesis. |

## Principles

Do not optimize solely for clicks, time on site, or engagement. Prioritize usefulness, comprehension, completion, confidence, reduced administrative burden, mission time saved, trust, accessibility, and dignity.

Do not expose individual nonprofit weaknesses or inferred risks publicly without authorization and context.

## Verified Signal Surfaces

- Search logging route: `/api/log/search`.
- Aggregate analytics route/table surface: `/api/event`, `analytics_*`.
- Feedback route/table: `/api/feedback`, `feedback`.
- Claim flow: `org_claims`.
- Interest and view signals: `org_interest`, `org_view_events`, `org_wallet_saves`.
- Wallet tests and components exist; wallet contents include sensitive giving/volunteer intent and must be protected.

## Friction Register

| ID | Friction | Evidence | Severity | Next action |
|---|---|---|---|---|
| U-001 | Search result counts can confuse users between fused and filtered modes. | `DECISIONS.md` 2026-06-04 entry. | Medium | Product decision and UX copy/test. |
| U-002 | Hardcoded public counts and unsourced vendor claims can reduce trust. | `docs/audit/readiness_check.md`. | Medium | Evidence/copy audit before outreach. |
| U-003 | Missing/unknown revenue data may be misunderstood as poor performance. | Readiness doc says many orgs lack revenue data; user directive prohibits shame. | High | Make no-data language clear and nonjudgmental. |
| U-004 | Docs disagree about wallet storage/auth behavior. | Root `STEWARDSHIP.md`, `PRIVACY-INVARIANTS.md`, frontend code differ in details. | Medium | Reconcile public/privacy language to implementation. |

