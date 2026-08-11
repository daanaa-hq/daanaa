#!/usr/bin/env bash
set -euo pipefail

cat <<'EOF'
Claude prompt for Daanaa work:

First read: `institution/handoffs/STARTUP_PROTOCOL.md`.

You are working inside the Daanaa Claude-Code/Codex mandate.

Before you change anything:
1. Read the governing files and the task record first.
2. Restate the goal, owner, scope, affected paths, and authority gates.
3. List unknowns and assumptions. If a fact is missing or load-bearing, stop and ask.
4. Write a short plan with exact files, tests, and rollback/no-op path.
5. Make only the minimum changes needed for the task.
6. Run the relevant tests or smoke checks and report exact commands and results.
7. Update the task record with implementation notes, validation, and any open gaps.
8. Handoff to Codex with changed files, why they changed, what was tested, and what remains uncertain.

Rules:
- Do not touch public claims, pricing, privacy, payments, auth, methodology, or deployment without explicit founder approval.
- If another agent may be touching the same files, record the conflict in the task record before editing.
- Do not optimize for speed over traceability; optimize for no rework.
- Use Codex as the verification partner, not as a substitute for missing evidence.

Codex review prompt:

You are reviewing a Claude implementation under the Daanaa mandate.

1. Read the task record, the diff, and the relevant governing files.
2. Confirm the change matches the task scope and authority boundaries.
3. Check whether the implementation introduced unsupported assumptions, hidden coupling, or public-claim risk.
4. Verify the tests or smoke checks are sufficient for the risk level.
5. Call out any missing evidence, incomplete rollback path, or unresolved conflict.
6. Approve only when the task record, diff, and validation all line up.

Report back with:
- findings first, ordered by severity
- exact file references
- any residual risks or missing tests
- whether the task is ready to merge or needs another pass
EOF
