# Codex Agent Guide

## Document Control

| Field | Value |
|---|---|
| Purpose | Root guidance for Codex agents working in this repository. |
| Responsible role | Stewardship Systems Agent, accountable to the Chief Steward. |
| Authority level | Operating guidance; subordinate to protected constitutional rules and explicit founder instructions. |
| Review trigger | Any material governance, privacy, deployment, data, payment, or agent-autonomy change. |
| Editable status | Editable by ordinary agents for clarity; protected rules referenced here are not editable by ordinary agents. |
| Dependencies | `CLAUDE.md`, `STEWARDSHIP.md`, `PRIVACY-INVARIANTS.md`, `institution/`. |
| Retirement condition | Retire only if replaced by a clearer root agent guide with equivalent protections. |

## Required Reading

Before changing code or institutional files, read:

1. `CLAUDE.md`
2. `STEWARDSHIP.md`
3. `PRIVACY-INVARIANTS.md`
4. `DECISIONS.md`
5. `LESSONS.md`
6. `institution/README.md`
7. `institution/CONSTITUTION.md`
8. `institution/AUTHORITY.md`
9. `institution/CURRENT_STATE.md`
10. `institution/state.json`

## Operating Rules

- Preserve the existing product. Prefer additive, reversible changes.
- Do not deploy, migrate databases, publish content, spend money, send external communications, alter authentication, or change public scoring/peer methodology without explicit founder approval.
- Keep nonprofit discovery and access to core public IRS information free.
- Payment must not affect public visibility, ranking, search treatment, or Peer Financial Context.
- Separate public records, nonprofit-provided information, and AI inference.
- Treat private nonprofit information as owned and controlled by the nonprofit; do not sell it.
- AI conclusions must show sources, assumptions, confidence, and uncertainty where material.
- Daanaa is not an attorney, CPA, auditor, investment adviser, lender, charity-rating agency, or regulated financial institution.
- Use local, existing, cached, and open-source resources before paid services.
- Never store secrets in the repo or print secrets into reports.

When repo instructions conflict, use the narrower stewardship protection and surface the conflict in `institution/RISK_REGISTER.md` or `institution/FOUNDER_REQUESTS.md`.

## Authority Order

Follow the authority order defined in `institution/AUTHORITY.md`.
Lower layers may clarify but may not override higher layers.
