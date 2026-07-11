# Cost And Infrastructure Skill

## Document Control

| Field | Value |
|---|---|
| Purpose | Review local hardware, cloud dependencies, model routing, storage, recurring costs, and avoidable waste. |
| Responsible role | Finance Steward and Technology Steward. |
| Authority level | Skill specification subordinate to spending controls and privacy protections. |
| Review trigger | Weekly review, new infrastructure proposal, new model path, or spending request. |
| Editable status | Editable by ordinary agents with sourced evidence. |
| Dependencies | `institution/BUDGET_STATE.md`, `institution/CURRENT_STATE.md`, `institution/state.json`. |
| Retirement condition | Retire when a maintained cost and infrastructure dashboard exists. |

## Trigger

Need to assess local-vs-cloud execution, active services, spend controls, or infrastructure waste.

## Inputs

- Budget state
- Process inventory
- Local model availability
- Storage and data footprint
- Founder-provided billing data when available

## Permissions

Read local process and repository evidence; no provider-console access without approval.

## Method

Prefer deterministic code, then local models, then justified cloud use; mark missing billing data as unknown.

## Output

Model-routing recommendation, cost-risk notes, unknowns, and spending controls.

## Tests

No spending is authorized; unknown values stay unknown.

## Failure Behavior

If usage telemetry is absent, report the gap and keep the survival posture.

## Cost Awareness

This skill exists to reduce unnecessary recurring cost and vendor dependence.

## Human Approval Gates

Required for paid services, infrastructure upgrades, or external data processing of sensitive information.

## Revision History

- 2026-07-10: Initial minimum skill spec.

## Retirement Condition

Retire when a maintained cost/infrastructure system replaces this spec.
