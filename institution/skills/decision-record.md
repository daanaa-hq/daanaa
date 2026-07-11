# Decision Record Skill

## Document Control

| Field | Value |
|---|---|
| Purpose | Preserve evidence, alternatives, reasoning, outcome, and review trigger for material decisions. |
| Responsible role | Stewardship Systems Agent. |
| Authority level | Skill specification subordinate to `DECISION_LOG.md`. |
| Review trigger | Material decision, reversal, or completed operating cycle. |
| Editable status | Editable by ordinary agents through append-only updates and superseding records. |
| Dependencies | `institution/DECISION_LOG.md`, `institution/HYPOTHESES.md`, `institution/RISK_REGISTER.md`. |
| Retirement condition | Retire when a versioned decision database replaces the markdown log. |

## Trigger

Any decision that changes process, affects risk, or informs future reversals.

## Inputs

- Issue
- Evidence
- Options
- Recommendation
- Review trigger

## Permissions

Append to local institutional records.

## Method

Capture why the decision was made, not only what was chosen, then link expected and actual outcomes.

## Output

Decision record with sources, risks accepted, and follow-up trigger.

## Tests

Records remain traceable and reversals reference prior reasoning.

## Failure Behavior

If evidence is weak, record the uncertainty and downgrade authority.

## Cost Awareness

Record cost assumptions and whether spending approval is needed.

## Human Approval Gates

Required where the decision itself needs founder or specialist authorization.

## Revision History

- 2026-07-10: Initial minimum skill spec.

## Retirement Condition

Retire when an auditable decision system replaces the markdown log.
