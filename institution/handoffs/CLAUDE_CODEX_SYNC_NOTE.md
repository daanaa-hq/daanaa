# Claude ↔ Codex Sync Note

**Date:** 2026-08-13  
**Purpose:** Minimal shared coordination note for Claude Code and Codex.

## Source Of Truth

- Task record:
  - `institution/tasks/T-2026-08-13-002-charter-safe-product-roadmap.md`
- Handoff:
  - `institution/handoffs/2026-08-13-charter-safe-product-roadmap.md`
- Behavioral brief:
  - `docs/BEHAVIORAL_SCIENCE_OPPORTUNITIES_BRIEF_20260813.md`

## Current Codex Scope

- Batch 1: homepage, directory, search/discovery UX, accessibility, and performance hardening
- Product scope explicitly includes:
  - opportunities
  - donor retention
  - volunteer / skills / in-kind action paths

## Current Progress

Completed by Codex:
- Homepage discovery pass in `frontend/src/pages/Home.tsx`
  - hero copy tightened around give / volunteer / research
  - generic path cards replaced with clearer intent-led entry structure
  - on-page guardrail copy added: no sponsored rankings, no platform checkout, no pressure loops
- Directory orientation pass in `frontend/src/pages/Directory.tsx`
  - header copy now reflects nearby organizations and verified giving paths
  - lightweight intent links added: Give / Volunteer / Research / Near me
  - top-of-page instructions clarified for search narrowing without losing public-record context

Validation:
- `cd frontend && npm run build` passed after homepage changes
- `cd frontend && npm run build` passed after directory changes

## Next Codex Focus

1. deeper directory pass
2. org-page decision structure
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

- Claude can implement Track A work.
- Codex reviews for stewardship, provenance, quality, and user-journey coherence.
- Update repo-visible files instead of relying on chat/plugin assumptions.

## If You Need To Sync Fast

Append:
- what changed
- files touched
- what still needs review
- whether a founder gate was reached
