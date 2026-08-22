-- 030_v6_scoring_audit_trail.sql
--
-- Correction to the initial Phase B V6 audit-trail migration (2026-08-21;
-- see DECISIONS.md and institution/TEAM_LOG.md). That version mistakenly
-- created scoring_run_log, duplicating the pre-existing live scoring_runs
-- table. scoring_runs already has 47 real v4/v5 records and is read by the
-- API and historical loaders, so it is the one authoritative run ledger.
-- scoring_run_log was empty and is removed here rather than retained as a
-- second, misleading source of truth.
--
-- scoring_runs.completed_at is NOT NULL. SQLite cannot relax that constraint
-- without rebuilding this live-consumer table, so the v6 scorer follows the
-- established load_v5_scores_delta.py convention: it inserts one completed
-- scoring_runs row at the end of the run, when both timestamps are known.
-- The three nullable provenance columns added below therefore remain NULL for
-- historical v4/v5 rows, as they do not apply retroactively.
--
-- Delta history is captured by trg_scoring_history_delta. Because the final
-- scoring_runs row cannot exist while per-organization UPDATEs fire that
-- trigger, scoring_run_current is a deliberately tiny single-row pointer to
-- the run currently in flight. It is not a second run ledger: it contains
-- only the run ID and start time needed for trigger attribution, and the
-- scorer clears it after recording its completed scoring_runs row. This
-- preserves correct run_id attribution without changing the live table's
-- NOT NULL constraint or using a structurally impossible "running" row.
--
-- Known deliberate limitation: delta-only scoring_history proves WHEN a
-- value changed, not that an unchanged organization was re-evaluated on a
-- particular night. row_counts_json records aggregate coverage; full
-- snapshots would be unsustainable at 2.07M organizations x nightly runs.
--
-- This correction drops the prior trigger before recreating it because
-- SQLite has no CREATE TRIGGER OR REPLACE. The ALTER TABLE statements are
-- intentionally one-time migration steps; do not re-run this file after it
-- has been recorded as applied.

DROP TRIGGER IF EXISTS trg_scoring_history_delta;
DROP TABLE IF EXISTS scoring_run_log;

ALTER TABLE scoring_runs ADD COLUMN git_commit TEXT;
ALTER TABLE scoring_runs ADD COLUMN row_counts_json TEXT;
ALTER TABLE scoring_runs ADD COLUMN source_data_date TEXT;

CREATE TABLE IF NOT EXISTS scoring_run_current (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    run_id TEXT NOT NULL,
    started_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS scoring_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    old_scoring_tier TEXT,
    new_scoring_tier TEXT,
    old_merit_percentile_v6 INTEGER,
    new_merit_percentile_v6 INTEGER,
    run_id TEXT
);

CREATE TRIGGER trg_scoring_history_delta
AFTER UPDATE ON registry_enriched
WHEN NEW.scoring_tier IS NOT OLD.scoring_tier
  OR NEW.merit_percentile_v6 IS NOT OLD.merit_percentile_v6
BEGIN
    INSERT INTO scoring_history (
        ein,
        old_scoring_tier,
        new_scoring_tier,
        old_merit_percentile_v6,
        new_merit_percentile_v6,
        run_id
    ) VALUES (
        NEW.EIN,
        OLD.scoring_tier,
        NEW.scoring_tier,
        OLD.merit_percentile_v6,
        NEW.merit_percentile_v6,
        (SELECT run_id FROM scoring_run_current WHERE id = 1)
    );
END;
