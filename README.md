# MERIT — How This Works

**Start here.** This is the map of how the MERIT build system is organized.

---

## The two repos

### `meritgiving-ops/` — The organization
The "company" side. Mission, strategy, departments, decisions, briefings, risks, OKRs.
Not deployed anywhere — lives in GitHub for version control.
This is where Claude pulls context from when reasoning about the org.

### `merit-platform/` — The product
The actual MERIT platform code + Claude Code configuration. Deploys to Vercel (web) and Railway/Fly (api).
Contains the dashboards, profile pages, scoring engine, etc.

---

## Daily workflow for Akbar (CEO)

### Morning session (60 min)
1. Open Claude Code in `merit-platform/`
2. Run `/morning-brief` — reads from `meritgiving-ops/` to generate today's brief
3. Strategic block (20 min): the one priority needing CEO judgment today
4. Clear approval queue (20 min): PRs, content, emails Claude prepared
5. Run `/log-decision` for any calls made
6. Run `/plan-today` to confirm lunch + night priorities

### Lunch session (45-60 min)
Either:
- A human conversation (advisor, sponsor, user research call)
- A deep build session with Claude Code

### Night session (45-60 min)
1. Review what shipped today via `/ops` dashboard
2. Build/ship block
3. Run `/plan-tomorrow`
4. Weekly habit (Monday: plan / Friday: retro / etc.)

**Total time:** 2.5–3 hours/day, ~17–21 hours/week.

---

## The 10 departments

Each lives in `meritgiving-ops/departments/[NN-name]/`:

| # | Department | Head agent | Primary responsibility |
|---|---|---|---|
| 01 | Product & Engineering | `eng-lead` | Build the platform |
| 02 | Data & Research | `data-lead` | Source, score, enrich data |
| 03 | Growth & Communications | `growth-lead` | Marketing, content, community |
| 04 | Operations | `ops-lead` | Infra, inbox, incidents |
| 05 | Finance & Accounting | `finance-lead` | Books, runway, credits |
| 06 | Legal & Compliance | `legal-lead` | Filings, risks, ToS |
| 07 | People & Partnerships | `partnerships-lead` | Advisors, sponsors, vendors |
| 08 | Intelligence | `intel-lead` | Briefings, signals, synthesis |
| 09 | Mission & Strategy | `strategy-lead` | OKRs, ADRs, north star |
| 10 | Nonprofit Success | `nonprofit-success-lead` | Claims, onboarding, support |

Each has a `DEPT.md` that defines its mission, KPIs, escalation rules, approval gates, and worker agents.

---

## The agent hierarchy

```
Akbar (CEO)
  └── Claude Code (COO, orchestrator)
       └── 10 Department Head Agents
            └── 25+ Worker Agents
                 └── Tools (MCP servers)
```

**Department heads** read DEPT.md, coordinate workers, escalate per rules.
**Worker agents** execute specific recurring tasks on schedules.
**Compliance agents** review PRs against rules (legal-reviewer).

All agent definitions live in `merit-platform/.claude/agents/`.

---

## The dashboards

Three dashboards in `merit-platform/apps/web/app/(dashboard)/`:

- **`/ceo`** — daily executive view (Akbar only, Clerk-gated)
- **`/ops`** — operational health (Akbar + Claude agents, Clerk-gated)
- **`/mission`** — public impact view (no auth, indexed)

See `SPECIFICATION.md` in that directory.

---

## The gates

Phase 0 has 7 gates over 24 weeks. Each is a pass/fail decision point that protects the next phase.

| Gate | Week | What |
|---|---|---|
| 1 | 2 | Legal Foundation |
| 2 | 4 | Credits & Infrastructure |
| 3 | 8 | Data Foundation |
| 4 | 12 | Halfway Mirror (honest self-eval) |
| 5 | 16 | Trust Foundation |
| 6 | 20 | Pre-Launch Readiness |
| 7 | 24 | Public Launch |

See `meritgiving-ops/strategy/phase-plan.md` for criteria.

---

## The slash commands

In Claude Code (inside `merit-platform/`):

- `/morning-brief` — generates today's brief
- `/weekly-allhands` — Monday status across all departments
- `/weekly-retro` — Friday reflection
- `/monthly` — monthly board-format review
- `/log-decision` — capture a decision as ADR
- `/plan-today` / `/plan-tomorrow` — set priorities
- `/ship-it` — pre-deploy checklist
- `/dept [name]` — full status of one department
- `/escalate [issue]` — surface to CEO immediately
- `/brief [topic]` — deep dive on any topic

---

## The mission lock

Eight non-negotiable principles in `meritgiving-ops/strategy/mission-lock.md`. Encoded in:
- LLC operating agreement (when MeritGiving LLC forms)
- Root `CLAUDE.md` (every Claude session inherits)
- Every DEPT.md
- Public `/about` page

If anything ever feels mission-conflicting, surface immediately. Mission lock overrides convenience.

---

## What to do RIGHT NOW

1. Read `DAY_1_ACTION_PLAN.md` at the root of this build
2. Execute Day 1 (account signups, credit applications) in three sessions today
3. While doing that, Claude continues generating the remaining scaffolding
4. End of Day 1: commit both repos to GitHub
5. Day 2: start the first morning brief, the system begins running

---

## What's intentionally NOT here yet

These will be added as we go, NOT in this initial scaffolding:
- Actual code for IRS BMF ingestion (will use existing Python scoring engine)
- Actual profile page rendering (will build in Week 5-8)
- Skills (SKILL.md files) for specific tasks (will add as needed)
- Compliance subagents for specific PR types (will add when shipping starts)
- Database migrations (will add when schema solidifies)

The scaffolding is the org structure + how decisions get made. Code comes after that's set.

---

## Operating principle for everything

**The system should make the right thing the easy thing.** If at any point Claude is making the wrong call easy or the right call hard, the system has a gap. Surface that and fix the system, not the symptom.
