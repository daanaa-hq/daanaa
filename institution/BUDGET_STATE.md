# Budget State

## Document Control

| Field | Value |
|---|---|
| Purpose | Track known, unknown, and requested financial stewardship inputs. |
| Responsible role | Finance Steward; Stewardship Systems Agent maintains unknowns. |
| Authority level | Evidence snapshot; not accounting record. |
| Review trigger | Weekly review, new service, billing change, funding opportunity, or founder update. |
| Editable status | Editable by ordinary agents when values are sourced; unknowns must stay unknown. |
| Dependencies | `FOUNDER_REQUESTS.md`, `FUNDING_PIPELINE.md`, repo deployment docs. |
| Retirement condition | Retire when replaced by official accounting/budget system. |

## Scenario Default

Recommended scenario while cash information is missing: survival.

## Known From Repository Evidence

| Item | Value | Source | Confidence |
|---|---:|---|---|
| Canonical local data store size | `data/merit_registry.db` about 11G | `ls -lh data` | High |
| Local data artifacts total | `data/` about 124G | `ls -lh data` | High |
| DigitalOcean droplet cost | Documentation states resize from $8/mo to $16/mo on 2026-07-06 | `LESSONS.md` | Medium; billing not verified |
| New spending approved in this bootstrap | $0 | Current work | High |

## Unknown Required Inputs

- Available cash.
- Monthly burn.
- Annual committed recurring cost.
- Cloud provider billing.
- API/model spend.
- Domain/email/workspace spend.
- Active paid services and trial end dates.
- Expected revenue.
- Probability-weighted funding pipeline.

## Spending Controls

- No new recurring paid service without founder approval and documentation of purpose, cost, benefit, alternatives, switching/cancellation path, data implications, vendor dependence, and approval.
- Prefer existing hardware, existing data, local models, cached results, batch jobs, and open-source tools.
- Treat any missing financial value as unknown, not zero.

