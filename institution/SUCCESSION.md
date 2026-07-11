# Succession And Continuity

## Document Control

| Field | Value |
|---|---|
| Purpose | Reduce unhealthy dependence on the founder, current developers, current models, vendors, and stack. |
| Responsible role | Chief Steward; Continuity Steward when appointed. |
| Authority level | Continuity plan; protected by `CONSTITUTION.md` where mission is involved. |
| Review trigger | Weekly review, new single point of failure, vendor change, key-person dependency, incident, or funding change. |
| Editable status | Editable by ordinary agents for proposed improvements; authority changes require founder approval. |
| Dependencies | `GOVERNANCE.md`, `CURRENT_STATE.md`, `RISK_REGISTER.md`, `BUDGET_STATE.md`. |
| Retirement condition | Retire when replaced by board-approved succession and continuity plan. |

## Current Single Points Of Failure

- Founder approval and provider-console access for finance, billing, credentials, and legal decisions.
- Local server and SQLite data store.
- DigitalOcean droplet production path.
- Large local data artifacts and backups.
- Local model services for enrichment/search assistance.
- Repository institutional memory spread across many docs.

## Continuity Direction

- Keep core public discovery useful without paid access.
- Preserve data provenance and decision rationale.
- Make recovery, deployment, backup, and review procedures executable by a qualified successor.
- Keep secrets out of repo and document where authority lives without exposing credentials.
- Prefer open formats and exportable data.
- Avoid vendor lock-in unless measurable benefit justifies it and an exit path is recorded.

## Near-Term Continuity Actions

1. Verify offsite backups and restoration.
2. Reconcile deployment source-of-truth for droplet API.
3. Record monthly spend and service ownership.
4. Keep founder requests small, explicit, and batched.
5. Move repeated decisions into documented workflows only after evidence.

