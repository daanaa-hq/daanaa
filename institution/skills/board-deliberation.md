# Board Deliberation Skill

## Document Control

| Field | Value |
|---|---|
| Purpose | Structure dissent-aware consideration of material decisions. |
| Responsible role | Governance Steward. |
| Authority level | Skill specification subordinate to `GOVERNANCE.md`. |
| Review trigger | Material decision with meaningful tradeoffs or uncertainty. |
| Editable status | Editable by ordinary agents with preserved dissent and evidence rules. |
| Dependencies | `institution/GOVERNANCE.md`, `institution/DECISION_LOG.md`. |
| Retirement condition | Retire when a better recorded deliberation process exists. |

## Trigger

Material decision needing structured options, disagreement, and recommendation.

## Inputs

- Decision question
- Evidence
- Assumptions
- Stakeholders
- Options

## Permissions

Local document synthesis only.

## Method

Simulate mission, user, finance, security, legal, product, ethics, and continuity perspectives; preserve real disagreement.

## Output

Arguments for and against each option, minority view, recommendation, and confidence.

## Tests

At least one perspective can dissent when evidence supports disagreement.

## Failure Behavior

If evidence is thin, say so and lower confidence rather than manufacturing consensus.

## Cost Awareness

Always include a lowest-cost option and an explicit reversibility view.

## Human Approval Gates

Required when the recommendation crosses approval thresholds in `GOVERNANCE.md`.

## Revision History

- 2026-07-10: Initial minimum skill spec.

## Retirement Condition

Retire when superseded by a maintained deliberation system.
