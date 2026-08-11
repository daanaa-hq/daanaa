# Research Explorer Handoff

**Status:** Complete  
**Owner:** Claude Code  
**Review owner:** Codex  
**Scope:** Public aggregate research exploration only

## Product decision

Build the full explorer at `/research/explorer`. Keep `/research` as the readable research library and add a prominent link to the explorer.

## Data boundary

Use only `frontend/public/research-snapshot.json` through `frontend/src/data/researchSnapshot.ts`. Do not add live raw database queries, private data, donor data, Power BI, or paid analytics services.

## Required views

- V6 evidence states
- Cause areas
- States or regions
- Revenue bands when the snapshot supports the view
- Small organization fairness indicators

## Required behavior

- Search and filter controls
- Recharts visualizations using existing dependencies
- Accessible table alternative for every chart
- CSV download of the visible aggregate rows
- Shareable filter URL
- Snapshot date, denominator, source note, and disclaimer
- What this shows and what this does not show
- Loading, error, empty, keyboard, mobile, and long label states

## Writing rules

Use clear professional prose. Do not use hype, causal claims, moral comparisons, or AI sounding filler. Do not call missing data a weakness. Use “reported,” “observed,” “peer context,” and “available public records.”

## Review gates

- No scoring logic changes
- No database migration
- No production deployment
- No public methodology change outside the approved research brief
- No new external repository or paid service

## Handoff evidence

When complete, provide:

- exact files and branch;
- local route and screenshots;
- snapshot date and denominator;
- tests and build exit codes;
- accessibility check results;
- CSV and share link checks;
- small cell and privacy safeguards;
- known limitations;
- rollback plan.

Implemented:

- `/research/explorer` route backed by `frontend/public/research-snapshot.json`
- prominent `/research` link into the explorer
- accessible chart/table toggle, CSV export, and shareable filter URL

Use:

```text
STATUS=COMPLETE
VERDICT=APPROVED
BLOCKED_BY=NONE
NEXT_ACTION=Archive handoff
UPDATED_AT=<timestamp>
```
