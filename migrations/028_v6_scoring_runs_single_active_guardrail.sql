-- 028_v6_scoring_runs_single_active_guardrail.sql
--
-- Phase 0 of the V6 scoring reconciliation (see DECISIONS.md 2026-08-21,
-- institution/TEAM_LOG.md same date). v6_scoring_runs had a row
-- (v6_foundation_candidate_20260728_revised) with status='active' while its
-- own notes said "Candidate only; not active API/frontend output" -- a
-- self-contradictory record that made it impossible to trace what the live
-- serving columns actually came from. This migration:
--
--   1. Corrects that one row's status to 'candidate' (matches the value
--      scripts/scoring/v6_financial_context_api.py already queries for via
--      `WHERE r.status IN ('candidate', 'active')`, so this doesn't break
--      that read path -- it stops the row from falsely claiming promotion).
--   2. Adds a partial unique index so status='active' can only ever match
--      one row, enforced by SQLite itself. This is the guardrail: the
--      failure mode here was structural (nothing prevented two rows from
--      both claiming active), not a one-off mistake, so the fix is
--      structural too, not a note to remember next time.
--
-- Idempotent: safe to run more than once (UPDATE has a status='active'
-- guard so it's a no-op the second time; CREATE UNIQUE INDEX IF NOT EXISTS).
--
-- Verified before writing this: inserted a test row with status='active',
-- then tried to set a second row to status='active' -- the second update
-- failed with "UNIQUE constraint failed: v6_scoring_runs.status", proving
-- the guardrail actually blocks the failure mode it's meant to prevent, not
-- just declaring intent to. Test row removed after verification.

UPDATE v6_scoring_runs
SET status = 'candidate'
WHERE run_id = 'v6_foundation_candidate_20260728_revised' AND status = 'active';

CREATE UNIQUE INDEX IF NOT EXISTS idx_v6_scoring_runs_single_active
ON v6_scoring_runs(status) WHERE status = 'active';
