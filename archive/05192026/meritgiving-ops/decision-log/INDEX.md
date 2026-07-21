# Decision Log Index

**Every important decision lives here as a numbered ADR.**

Append to this list every time `/log-decision` runs.

---

## Active ADRs

| # | Date | Title | Status | Departments | Reversibility |
|---|---|---|---|---|---|
| 001 | 2026-05-19 | Operate MERIT as DBA under EcoMargins LLC until MeritGiving LLC forms | Accepted | finance, legal, strategy | Easy |
| 002 | 2026-05-19 | Phase 0 has no payment rails on-platform; donate buttons link out to nonprofit-owned pages | Accepted | eng, legal, strategy | Hard |
| 003 | 2026-05-19 | Use Claude Code with monorepo + skills + agents architecture instead of self-hosted service stack | Accepted | eng, ops, strategy | Hard |
| 004 | 2026-05-19 | Operating rhythm: 3 sessions/day, 17–21 hrs/week, gates protect phase transitions | Accepted | strategy, all | Easy |
| 005 | 2026-05-19 | 10-department org structure with department-head agents and worker agents | Accepted | strategy, all | Easy |

---

## Conventions

- ADRs are numbered sequentially with leading zeros (001, 002, ...)
- Filename: `ADR-NNN-[short-slug].md`
- Status: Proposed → Accepted → Superseded → Deprecated
- Reversibility: Easy / Hard / Permanent
- Every ADR references related risks, issues, and prior ADRs

## When to write an ADR

Write one for:
- Architecture choices (stack, tools, services)
- Mission/strategy commitments
- Legal/compliance interpretations
- Operating policies
- Major partnerships
- Pricing/funding decisions
- Anything you'd want a successor to know

Don't write one for:
- Minor implementation details
- Style choices
- Day-to-day operational decisions
- Things that change frequently

## How to use

When in doubt about a past decision: search this file by keyword, then open the relevant ADR. The reasoning at the time of the decision is preserved, including alternatives considered. This is how the org keeps its memory.
