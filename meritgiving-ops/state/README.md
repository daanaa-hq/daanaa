# State Directory

**Volatile state. Agents write here. Read this for context.**

This directory holds files that agents update frequently — current snapshots, last-session continuity, queue states, etc. Unlike `strategy/` or `decision-log/`, files here can be overwritten.

## Files

- `last-session.md` — what was happening at end of last Claude Code session (auto-updated)
- `tomorrow.md` — tomorrow's plan from `/plan-tomorrow` (overwritten daily)
- `today.md` — today's priorities from `/plan-today` (overwritten daily)
- `global-status.json` — system-wide status (green/yellow/red) updated by ops-lead daily
- `current-gate.json` — current Phase 0 gate progress
- `infra-snapshot.json` — latest infrastructure health from infra-health-monitor
- `backup-catalog.json` — index of all backups by date
- `approvals-queue.json` — items awaiting CEO approval

## Sample `last-session.md`

```markdown
# Last Session — 2026-05-19 (Night)

## What happened
- Generated Day 1 action plan
- Created org chart and operating rhythm docs
- Created all 10 department charters
- Created risk register with 28 risks
- Created Q2-Q3 OKRs
- Started Claude Code configuration

## What's next
- Generate remaining worker agents
- Generate dashboard scaffolds
- Generate strategic dialogue starter
- Package everything for CEO download

## Open questions
- (None blocking)

## Approvals waiting
- (None — early bootstrap phase)
```

## Sample `global-status.json`

```json
{
  "overall": "green",
  "lastUpdated": "2026-05-19T22:00:00-05:00",
  "departments": {
    "01-product-eng": { "status": "green", "note": "scaffolding phase" },
    "02-data-research": { "status": "green", "note": "scaffolding phase" },
    "03-growth-comms": { "status": "green", "note": "scaffolding phase" },
    "04-operations": { "status": "green", "note": "no incidents" },
    "05-finance": { "status": "green", "note": "books not yet active" },
    "06-legal-compliance": { "status": "yellow", "note": "LLC formation pending" },
    "07-people-partnerships": { "status": "green", "note": "pipeline empty (early)" },
    "08-intelligence": { "status": "green", "note": "morning brief pending wire-up" },
    "09-strategy": { "status": "green", "note": "OKRs set" },
    "10-nonprofit-success": { "status": "green", "note": "Phase 0 autoresponder ready" }
  }
}
```

## Sample `current-gate.json`

```json
{
  "gate": 1,
  "name": "Legal Foundation",
  "weekTarget": 2,
  "weekCurrent": 1,
  "status": "in_progress",
  "criteria": [
    { "item": "LLC formation paperwork submitted", "done": false },
    { "item": "EIN applied for", "done": false },
    { "item": "DBA filed (if needed)", "done": false },
    { "item": "Business bank account opened", "done": false },
    { "item": "Mission lock language drafted", "done": false },
    { "item": "Attorney intro call completed", "done": false },
    { "item": "CPA intro call completed", "done": false }
  ]
}
```

## Updating discipline

- Agents update their relevant files on every run
- Don't pile up stale state — agents own freshness
- If a file gets stale (>7 days), it likely indicates a broken workflow; surface to ops-lead
