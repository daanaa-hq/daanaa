# Daanaa Audit Framework

This directory holds the audit of Daanaa against mission constraints, security, privacy, data credibility, and performance. Use the prompt in `/home/akbar/meritgiving/AUDIT_PROMPT_FABLE5.md` with Claude Fable 5 for the full audit.

## How to use

1. Copy the full content of `AUDIT_PROMPT_FABLE5.md` into Claude Fable 5 (claude.ai or Fable 5 CLI).
2. Run **PHASE 0** first (structure map). Review, ask questions.
3. Run remaining phases sequentially. Each phase ends with a report file and **STOPS**. Type "continue" to move to the next phase.
4. All progress persists in this directory. If interrupted, the next session reads the completed phases and picks up where you left off.
5. At the end, PHASE 6 (synthesis) produces `MASTER_REPORT.md` with a fix sequence for future Claude Code sessions.

## What the prompt covers

### Phases
- **PHASE 0:** Stack map (routes, frontend pages, database schema)
- **PHASE 1:** Backend security + mission (SQL injection, hardcoded secrets, ranking by revenue, Claude API boundaries)
- **PHASE 2:** Frontend + UX + accessibility (XSS, mixed content, error handling, tier explanations, keyboard nav)
- **PHASE 3:** Data credibility (BMF ingest validation, data freshness visibility, tier assignment logic, revocations)
- **PHASE 4:** Performance (droplet slowness diagnosis: CPU, memory, query, embedding server, caching)
- **PHASE 5:** Stewardship reconciliation (each of 12 principles + 7 privacy invariants → enforced in code? gaps?)
- **PHASE 6:** Synthesis (top 5 CRITICAL/HIGH fixes, quick wins, fix sequence for future sessions)

### Constraints enforced
- **Mission before growth:** No ranking by revenue/size by default.
- **Privacy architectural:** Giving Wallet = localStorage only, no IP retention, minimal PII.
- **Public data → Claude API only:** Donor/volunteer data → local Llama only.
- **Four-tier labels honest:** Must explain DATA_INCOMPLETE / VERIFIED_HEALTHY / FINANCIAL_NOTE / NOT_ASSESSED.
- **No paid placement:** Zero revenue from ranking, no sponsored results.

### Token discipline
- Never read whole files; use `rg`/`grep` to locate + read only matches (max 40 lines).
- Each phase produces one report file and stops.
- Findings go into `FINDINGS.md` (one line per issue).
- Summaries capped at 15 lines.

## Output files (created during audit)

- `00_structure.md` — Stack map, API routes, frontend pages, DB schema
- `01_backend.md` — SQL injection, secrets, ranking, input validation, Claude API boundaries
- `02_frontend.md` — XSS, mixed content, error handling, tier explanations, accessibility
- `03_data.md` — BMF validation, data freshness visibility, tier assignment, revocations
- `04_performance.md` — Baseline measurements, bottleneck diagnosis (query, embed, cache, or system)
- `05_stewardship.md` — Principle-gap table, conflicts between principles
- `FINDINGS.md` — Consolidated findings in format: `[CRITICAL|HIGH|MED|LOW] [area] file:line — issue — fix`
- `MASTER_REPORT.md` — Top 5 fixes (mission risk × user impact ÷ effort), quick wins, fix sequence

## Known issues (for context)

- **Droplet slowness:** Root cause TBD (PHASE 4 will diagnose).
- **Data freshness:** "As of <date>" not shown to users (credibility violation, HIGH priority).
- **Tier label honesty:** Are four-tier labels explained in UI, or just unexplained icons? (PHASE 2).
- **Claude API boundary:** Are any private/donor fields being sent to Anthropic? (PHASE 1).

## Running with Fable 5

The prompt is tuned for Fable 5's higher reasoning capability. It:
- Expects tighter validation logic (can reason about boundary cases).
- Uses sharper search patterns (rg regex, not naive grep).
- Proposes higher-confidence fixes with effort estimates.
- Generates a runnable fix sequence for future Claude Code sessions.

**Start with PHASE 0.** The full audit typically takes 2–3 Fable 5 sessions (one per 2–3 phases, then a final synthesis).
