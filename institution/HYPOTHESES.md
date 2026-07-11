# Hypotheses

## Document Control

| Field | Value |
|---|---|
| Purpose | Track important assumptions through the evidence ladder. |
| Responsible role | Stewardship Systems Agent. |
| Authority level | Hypothesis registry; not policy. |
| Review trigger | Weekly review, experiment completion, or material decision. |
| Editable status | Editable by ordinary agents with evidence. |
| Dependencies | `STEWARDSHIP.md`, `CURRENT_STATE.md`, `USER_INSIGHTS.md`. |
| Retirement condition | Retire when replaced by a database-backed experiment registry. |

## Registry

| ID | Assumption | Why it matters | Evidence for | Evidence against | Confidence | Test | Test cost | Success criteria | Result | Next action |
|---|---|---|---|---|---|---|---|---|---|---|
| H-001 | A concise institutional directory will reduce agent confusion. | Conflicting docs and duplicate systems increase operational risk. | Many docs and recent lessons document wrong-file and stale-doc failures. | Unknown whether agents will read new files. | Medium | Use this directory for two operating cycles and compare founder interruptions/errors. | Low | Fewer repeated context questions and no added filler docs. | Not tested. | Run weekly review manually. |
| H-002 | Manual weekly review should precede scheduled automation. | Prevents low-value scheduled reports and founder burden. | Existing repo has duplicate cron/scheduler lessons. | Manual process may be skipped. | High | Run two manual reviews before adding cron. | Low | Each review yields one clear constraint and no invented activity. | First run pending. | Run `scripts/institution_weekly_review.py`. |
| H-003 | Routine synthesis can use local repo data without external APIs. | Controls cost and privacy. | Bootstrap discovery produced useful state from local files and DB. | Funding/current-service verification needs external authoritative sources. | Medium | Track which sections require external verification. | Low | Most weekly state comes from local evidence; external checks are explicit. | In progress. | Keep unknowns explicit. |
| H-004 | Nonprofit-facing operational tools should first be used internally. | Prevents throwaway internal systems and improves product quality. | User directive and existing internal dashboards support this path. | Actual nonprofit value not yet measured here. | Medium | Use founder brief, budget state, and risk register internally for two cycles. | Low | Founder finds at least one decision clarified per cycle. | Not tested. | Request feedback after first brief. |
| H-005 | Public peer financial context helps small nonprofits if language avoids shame. | Core mission depends on useful, dignified transparency. | Stewardship docs and product components emphasize peer context. | User evidence from small nonprofits not verified in this bootstrap. | Medium-low | Interview or observe representative small nonprofits using org pages. | Medium | Users report improved understanding without feeling judged. | Not tested. | Add to user research queue. |

