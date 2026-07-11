# User Insight Skill

## Document Control

| Field | Value |
|---|---|
| Purpose | Synthesize verified feedback and behavior without exposing private nonprofit information. |
| Responsible role | Nonprofit Success Steward and Product Steward. |
| Authority level | Skill specification subordinate to privacy and dignity protections. |
| Review trigger | Weekly review, repeated confusion, new feedback source, or product experiment. |
| Editable status | Editable by ordinary agents with privacy-preserving evidence. |
| Dependencies | `institution/USER_INSIGHTS.md`, `PRIVACY-INVARIANTS.md`, `institution/state.json`. |
| Retirement condition | Retire when a maintained privacy-preserving insights pipeline replaces this spec. |

## Trigger

Need to summarize user friction, claims activity, search behavior, or support signals.

## Inputs

- Aggregate analytics
- Feedback tables
- Claim and interest activity
- Task and issue notes

## Permissions

Read aggregate local signals; do not export or expose private operational data.

## Method

Favor aggregate patterns, repeated confusion, and mission-relevant burden; separate verified evidence from inference.

## Output

User-friction summary, uncertainty notes, and suggested validation steps.

## Tests

No new personal data collection is introduced without explicit documentation.

## Failure Behavior

If data is sparse, state that clearly and avoid overgeneralization.

## Cost Awareness

Prefer existing first-party signals and manual synthesis over new tooling.

## Human Approval Gates

Required for new personal-data collection or external sharing of user-related data.

## Revision History

- 2026-07-10: Initial minimum skill spec.

## Retirement Condition

Retire when a better privacy-preserving user-insight system exists.
