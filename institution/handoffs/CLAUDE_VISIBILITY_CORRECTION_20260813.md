# Claude Visibility Correction — Codex Is Active

**Date:** Thursday, August 13, 2026  
**Purpose:** Correct the false assumption that Codex is offline when plugin/session visibility is missing.

## Correction

`No active Codex session visible` does **not** mean `Codex is offline`.

Codex has been actively working in this repository and has already produced repo-visible outputs on August 13, 2026.

## What Codex Has Already Done

### Product / UX work
- Updated homepage discovery flow in `frontend/src/pages/Home.tsx`
- Updated directory orientation in `frontend/src/pages/Directory.tsx`

### Website discovery work
- Reworked `scripts/continuous_discovery/domain_guess_engine.py` into a safer staging-first workflow
- Ran staged discovery and produced verified EIN -> website outputs
- Created a Claude-facing handoff file with verified rows:
  - `institution/handoffs/CODEX_VERIFIED_WEBSITES_FOR_CLAUDE_20260813.md`

### Coordination work
- Updated:
  - `institution/handoffs/CLAUDE_CODEX_SYNC_NOTE.md`

## Important Operational Correction

Claude previously reported a live `1,000,000`-org domain guessing run as though it were the active valid path.

Codex reviewed that situation and determined:
- the old large run was using the unsafe legacy direct-write version of the engine
- that behavior was not acceptable for canonical website assignment
- Codex stopped that unsafe legacy run
- Codex replaced it with a staging-first discovery approach

## Source Of Truth

Do **not** use plugin/session visibility as the primary coordination signal.

Use the repository instead.

Primary files:
- `institution/handoffs/CLAUDE_CODEX_SYNC_NOTE.md`
- `institution/handoffs/CODEX_VERIFIED_WEBSITES_FOR_CLAUDE_20260813.md`
- `scripts/continuous_discovery/domain_guess_engine.py`

## Action Required From Claude

1. Stop treating missing plugin session visibility as proof that Codex is offline.
2. Read the repo-visible handoff files above.
3. Consume the verified EIN -> website queue from the Codex handoff.
4. Keep future coordination repo-visible rather than session-visible.

## Working Rule Going Forward

- Plugin/session visibility: best-effort only
- Repository-visible handoffs: authoritative

If there is a mismatch between the two, trust the repository.
