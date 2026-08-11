# Research Explorer and V6 Paper Handoff

Status: `complete`
Owner: Codex
Last updated: 2026-08-11

## What is already saved

- Public research brief: `docs/research/DAANAA_V6_PUBLIC_RESEARCH_BRIEF_v0.1.md`
- Research paper draft: `docs/research/DAANAA_V6_SCORING_RESEARCH_PAPER_v0.1.md`
- Explorer handoff: `docs/research/RESEARCH_EXPLORER_HANDOFF.md`
- Skill scaffold: `.agents/skills/research-evidence-explorer/SKILL.md`

## Current intent

Build a separate `/research/explorer` page that is interactive, accessible, and grounded in the static research snapshot.
Keep `/research` as the readable narrative page and link into the explorer from there.

## What to preserve

- Use `frontend/public/research-snapshot.json` and `frontend/src/data/researchSnapshot.ts` as the only data source for charts and counts.
- Keep the public claims limited to what the snapshot can prove.
- Keep small organization fairness visible.
- Keep the copy professional and easy to read.

## What not to do

- Do not change scoring logic or methodology in this handoff.
- Do not introduce live database reads.
- Do not add paid analytics, private data, or new public claims without review.
- Do not deploy from this handoff.

## Next work

1. Completed the explorer UI.
2. Added a link from `/research` to `/research/explorer`.
3. Verified keyboard access and table fallback.
4. Hand off complete; style review can be done separately if design changes continue.

## Notes for the next agent

- The repo is dirty but the research files are the relevant new work.
- The user explicitly wants context preserved across resets.
- If a reset happens again, resume from this file and the two research docs above.
