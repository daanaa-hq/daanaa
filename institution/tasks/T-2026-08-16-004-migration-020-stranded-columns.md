# T-2026-08-16-004 — `volunteer_hours` is missing 3 columns migration 020 was supposed to add

| Field | Value |
|---|---|
| Owner | Unassigned — found by Codex review, not yet triaged |
| Scope | `volunteer_hours` table is missing `submitted_via`, `edit_count`, `locked_at` — migration 020 (`020_volunteer_hours_events_impact.sql`) is logged as "run" but never actually added them |
| Affected paths | `data/merit_registry.db` (schema), any code reading/writing those 3 columns on `volunteer_hours` (not yet audited — check `scripts/`, `daanaa_api.py` volunteer-hours endpoints) |
| Authority constraints | Schema change (repair migration) — requires founder approval per CLAUDE.md's approval gates |
| Status | **LIVE BROKEN — confirmed active SQL error, not just a missing feature** |
| Found | 2026-08-16, Codex review pass while checking a related migration-runner bug (see `LESSONS.md` and `DECISIONS.md` same date) |
| Severity | High — `daanaa_api.py:10019` runs `SELECT hours, service_date, status, locked_at FROM volunteer_hours ...`; `locked_at` does not exist on the live table, so this query errors every time it runs. Likely broken since 2026-07-22 (migration 020's logged run date), unnoticed for ~a month. |

---

## What's confirmed

`_run_migrations()`'s old code (fixed same day, see `LESSONS.md` 2026-08-16)
marked a migration "run" even if individual statements failed. Migration
020's three `ALTER TABLE volunteer_hours ADD COLUMN ...` statements
(`submitted_via`, `edit_count`, `locked_at`) are absent from the live
`volunteer_hours` schema, but `_migration_log` shows `020_volunteer_hours_events_impact.sql`
already logged as run (2026-07-22). The fixed migration-runner does **not**
retroactively repair this — it only prevents the same class of silent
failure for migrations not yet logged.

## What's NOT yet known

- Whether any live feature actually depends on these 3 columns and is
  currently degraded (e.g., volunteer-hours edit tracking, submission-source
  attribution, or hour-locking after admin verification) — not checked.
- Whether other ALTER statements across the other flagged files (004, 019)
  have the same gap — only 020 was concretely verified missing columns;
  004 and 019 were flagged as having the same inline-comment-semicolon
  pattern but not individually checked for missing columns.
- The right fix: likely a new, small repair migration
  (`025_repair_volunteer_hours_columns.sql` or similar) that adds the 3
  columns with `IF NOT EXISTS`-safe semantics, rather than trying to force
  a retry of the original file.

## Before executing

1. Check whether any current code path reads/writes `submitted_via`,
   `edit_count`, or `locked_at` on `volunteer_hours` — if so, determine
   whether it's been silently failing/erroring since 2026-07-22, or
   gracefully degrading.
2. Write a small, additive repair migration (not a retry of 020).
3. Audit 004 and 019 the same way before assuming they're fine.
4. Founder approval before applying, same as any schema change.
