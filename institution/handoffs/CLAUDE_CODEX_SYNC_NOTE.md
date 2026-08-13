# Claude ↔ Codex Sync Note

**Date:** 2026-08-13  
**Purpose:** Minimal shared coordination note for Claude Code and Codex.

## Source Of Truth

- Task record:
  - `institution/tasks/T-2026-08-13-002-charter-safe-product-roadmap.md`
- Behavioral brief:
  - `docs/BEHAVIORAL_SCIENCE_OPPORTUNITIES_BRIEF_20260813.md`
- Verified website handoff:
  - `institution/handoffs/CODEX_VERIFIED_WEBSITES_FOR_CLAUDE_20260813.md`

## Current Codex Scope

- Batch 1 product work remains active
- Website discovery engine has been fixed and run in staging-first mode

## Current Progress

Completed by Codex:
- Homepage discovery pass in `frontend/src/pages/Home.tsx`
- Directory orientation pass in `frontend/src/pages/Directory.tsx`
- Domain guessing engine rewritten into staging-first workflow in `scripts/continuous_discovery/domain_guess_engine.py`
- Verified website queue prepared for Claude in `institution/handoffs/CODEX_VERIFIED_WEBSITES_FOR_CLAUDE_20260813.md`

Website discovery status:
- sample run completed cleanly
- `candidate_verified` rows available
- `candidate_needs_review` rows separated from verified queue
- no canonical website writes performed by Codex during this run

## Next Codex Focus

1. let larger staged website run continue / harvest results
2. continue product work on org-page decision structure
3. opportunities + retention spec refinement
4. accessibility and performance follow-through on priority routes

## Hard Gates

Do not do these without explicit founder approval:

1. deploy
2. migrate
3. ranking / visibility logic changes
4. scoring / badge / evaluative methodology changes
5. restricted-purpose opportunity launch
6. private nonprofit data expansion beyond current stewardship boundaries

## Working Rule

- Claude can consume the verified website queue from the handoff file.
- Codex keeps discovery staging-first unless explicitly asked to promote canonical website fields.
- Update repo-visible files instead of relying on chat/plugin assumptions.
