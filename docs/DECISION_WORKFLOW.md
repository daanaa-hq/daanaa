# Decision-Making Workflow

**Adopted:** 2026-07-17 (founder-directed)
**Applies to:** All AI agents and contributors making product, data, or presentation decisions.

---

## The Protocol

Every open question or decision follows four gates, in order:

### Gate 1 — Principles Check
Test the question against `STEWARDSHIP.md` (11 principles) and the Daanaa
Charter (`institution/DAANAA-CHARTER.md`). Write down which principles are
touched and whether any option would violate one. An option that violates a
principle is eliminated here — no data can rescue it.

### Gate 2 — Data Validation
Validate the remaining options with real data before forming an opinion:
- Database queries (registry, link status, coverage numbers)
- Live-site verification (what actually renders, not what the code implies)
- Logs and metrics (what actually happened, not what was intended)

No decision proceeds on assumption. If the data doesn't exist, gathering it
becomes the first action item.

### Gate 3 — Board Simulation (every 12 hours while decisions are open)
Open decisions accumulate in `governance/DECISION_QUEUE.md`. Every 12 hours,
run a board simulation over ALL open items — six perspectives, each in its
own voice, each free to disagree:

| Seat | Lens |
|------|------|
| Legal | Disclosure obligations, liability, terms compliance |
| Accounting/Finance | Data integrity, methodology honesty, financial signals |
| Marketing | Donor experience, differentiation, engagement |
| ED (nonprofit leaders) | Partner sentiment, dignity of listed orgs, mission fit |
| Donor group | What donors actually use and understand |
| Stewardship chair | Principle alignment, long-horizon trust |

Each simulation produces, per decision: consensus level, dissents with
reasons, conditions (if any), and a confidence-to-proceed percentage.
Simulations are saved as `docs/BOARD_SIMULATION_<date>.md` and referenced
from the queue.

### Gate 4 — Resolution or Escalation
- **Consensus ≥ high confidence + principles clean + data clean** → decide,
  log it in `DECISIONS.md`, execute (within existing autonomy rules — frontend
  and spend still gate on founder approval).
- **Unresolved after simulation** (split board, missing data that can't be
  gathered, principle tension with no clean option) → escalate to founder.
  The escalation includes: the question, the data, the board's split, and a
  recommendation.

---

## Cadence & Mechanics

- New questions are appended to `governance/DECISION_QUEUE.md` the moment they
  arise, with status `open`.
- A 12-hour cron check (`scripts/check_decision_queue.sh`) counts open items
  and writes a `.DECISIONS_PENDING` marker + log line when any exist, so any
  active session picks them up.
- Board simulations clear the queue: items move to `resolved` (with the
  decision + simulation link) or `escalated` (waiting on founder).
- Nothing sits open past two simulation cycles (24h) without escalating.

## What This Does NOT Change

- Frontend changes still require founder approval before deploy.
- Spending money still requires founder approval.
- Database schema changes still require founder approval.
- Backend autonomy rules (smoke test + auto-rollback) unchanged.

The workflow governs *how decisions get made and documented* — not who holds
final authority. The founder can override any board-simulation outcome.

## Why (P9 — explainable later)

Every decision this workflow touches leaves a trace: the principles checked,
the data pulled, the six perspectives, and the resolution. A future auditor
can reconstruct not just what was decided but what was considered and
rejected.
