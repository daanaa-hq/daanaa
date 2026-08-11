# Quality Design Operating Model Skill

## Document Control

| Field | Value |
|---|---|
| Purpose | Apply the shared quality-and-design operating model for Daanaa work. |
| Responsible role | Stewardship Systems Agent. |
| Authority level | Operating skill subordinate to `institution/HANDOFF_PROTOCOL.md` and `AUTHORITY.md`. |
| Review trigger | Any task with quality, design, safety, coordination, or handoff risk. |
| Editable status | Editable by ordinary agents with evidence. |
| Dependencies | `institution/HANDOFF_PROTOCOL.md`, `institution/tasks/`, `institution/skills/INVENTORY.md`, `scripts/task_handoff_packet.py`. |
| Retirement condition | Retire when replaced by a maintained shared skill registry with equivalent traceability. |

## When To Use

Use for frontend, backend, coordination, or workflow changes where quality matters more than speed.

## Model

- Toyota: stop the line, use standard work, fix root cause, and require evidence before PASS.
- Apple: simplify the experience, prefer coherence, and remove fragmented choices.
- NASA: preflight checklist, explicit abort criteria, checkpoint/resume, no silent failure.
- Tesla: first-principles innovation, reinvention when the stack is wrong, and fast prototype-to-system learning.
- Amazon/Stripe: small increments, clear ownership, written decisions, observable outcomes.
- GitHub: one source of truth, small diffs, easy reverts, clear handoff packets.
- Kaizen: every miss becomes a rule, checklist item, or skill update.

## Operating Rules

- Stop when a load-bearing fact is missing.
- Prefer the smallest reversible change.
- Do not claim PASS without evidence.
- Separate verified facts, assumptions, and open risks.
- Preserve perspective separation: Claude writes the implementer/checkpoint lens; Codex writes the skeptic/reviewer lens.
- Keep one packet for Codex, one checkpoint for resume.
- Design for continuity: document decisions, skills, and checkpoints so the system can outlast the current founders.
- If the task changes a public claim, privacy, money, or methodology, require founder approval.

## Workflow

1. Read the task record and governing files.
2. Restate scope, owner, files, and gates.
3. Run the smallest relevant validation.
4. Record results in the task record.
5. Generate the handoff packet.
6. Hand off the packet to Codex.
7. Capture durable lessons as skills or decision records when a pattern repeats.
8. Resume from the checkpoint, not the chat thread.

## Output

- Clear next action.
- Evidence-backed PASS / CONDITIONAL / FAIL.
- Compact resume hint.
- Codex review packet with mismatches highlighted.
