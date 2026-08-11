# Shared Claude Code / Codex Handoffs

This directory is the shared file-backed coordination space for the two agents.

## Tag protocol

1. The active agent writes a handoff note before stopping.
2. The note names the exact files changed, tests run, failures, and next owner.
3. The next agent reads the note, confirms the working tree, and claims the next phase.
4. Only one agent may edit a file at a time.
5. A `ready-for-review` state is not a deployment approval.
6. Deployment requires a separate founder-approved release record with verified backup,
   rollback, health, API, and browser gates.

## Status values

- `in-progress`: owner is actively editing or testing.
- `blocked`: work cannot continue without a specific decision or external change.
- `ready-for-review`: local work is complete, evidence is attached, human review remains.
- `approved-for-deploy`: explicit approval exists for the exact reviewed diff only.
- `deployed`: public smoke tests passed after deployment.

## Current rule

The current v6 work remains local-only. No droplet writes, database migrations, manual
Gunicorn processes, or production restarts are permitted from this handoff directory.
## Shared Skill Hint

Generated handoff packets should include `institution/skills/quality-design-operating-model.md` when the work needs the common quality / design / innovation / continuity model.

## Startup Protocol

Begin each new Claude or Codex window with `STARTUP_PROTOCOL.md` before reading chat history.

