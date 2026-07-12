# AI Operational Memory — Curated Institutional Knowledge

**Purpose:** Preserve institutional knowledge, decisions, and lessons learned through AI sessions without exposing credentials, personal data, or transient artifacts.

**Authority:** Founder Ruling 2026-07-11, item 2 (Operational Decisions)

**Status:** Migration in progress (started 2026-07-11)

---

## What This Contains

This directory holds curated institutional memory extracted from AI session records. It is structured for:
- Successor discovery (can a next steward find this?)
- Long-term durability (no credentials, no proprietary formats)
- Constitutional clarity (decisions linked to principles)
- Operational resilience (standing constraints, incident patterns)

## What This Does NOT Contain

Raw conversational history, credentials, tokens, personal nonprofit information, machine-specific paths, transient session material, or vendor-specific artifacts are **not** here.

See `migration/exclusions.md` for the full inventory of what was reviewed and why it was excluded.

---

## Files in This Directory

| File | Purpose |
|------|---------|
| `DECISIONS.md` | Significant architectural, governance, and operational decisions with reasoning |
| `STANDING_CONSTRAINTS.md` | Institutional rules and gotchas that recur every session (e.g., "droplet holds no authoritative data") |
| `INCIDENTS.md` | Significant incidents: symptoms, root cause, resolution, prevention rule |
| `LESSONS_LEARNED.md` | Patterns discovered, validated, and worth remembering (opposite of one-off fixes) |
| `OPEN_QUESTIONS.md` | Unresolved questions worth picking up later (with context and prior reasoning) |
| `MEMORY_MANIFEST.md` | Summary: how many memories, when migrated, total size, next review date |
| `migration/` | Migration documentation (source inventory, exclusions, log) |

---

## How a Successor Uses This

1. Read STANDING_CONSTRAINTS.md first (recurring gotchas)
2. Read INCIDENTS.md to understand operational risks
3. Read DECISIONS.md to understand *why* the system is designed this way
4. Check OPEN_QUESTIONS.md for starting points on future work
5. Run `git log -- institution/ai-memory/` to see evolution of memory

If a successor needs the full conversational history for a specific incident or decision, they should be able to trace back to:
- A commit in DECISIONS.md or INCIDENTS.md
- A git blame showing when the memory was recorded
- A cross-reference to the relevant code or institutional document

---

## Sources and Traceability

Each memory item includes:
- **Date:** When it was first recorded
- **Source:** Where it came from (incident post-mortem, code review, etc.) without exposing raw conversational material
- **Evidence:** Concrete examples or links to code/tests that prove the point
- **Status:** Live (currently applies), closed (resolved), or historical (for context)

---

## Next Review

Scheduled for quarterly review under Amendment 1's continuous self-review duty.

- Q3 2026: Verify memories remain accurate and add new patterns
- Q4 2026: Reconcile with LESSONS.md and DECISIONS.md in root; promote repeatable patterns to formal policy

---

**The work continues. This memory is meant to make the institution wiser for future stewards.**
