-- 029_drop_dead_v6_ledger.sql
--
-- Phase A of the V6 corrected plan (DECISIONS.md, TEAM_LOG.md, 2026-08-21).
-- v6_scoring_runs, v6_peer_context_assignments (9.36M rows), and
-- v6_conditional_band_context (52.8K rows) were an abandoned 2026-07-26/27/28
-- prototype ledger design. Confirmed via grep + cron/pipeline check: zero
-- scheduled consumers. The live system (scripts/scoring/daanaa_scorer.py +
-- scripts/scoring/peer_group.py) writes scoring_tier/merit_percentile_v6/etc
-- directly to registry_enriched, bypassing this ledger entirely -- these
-- tables never fed anything donors actually see.
--
-- Codex's independent recommendation (asked directly, not assumed): drop
-- after a verified backup, since retaining 2.8GB+ of dead prototype state
-- increases the exact "which table is real" ambiguity that cost real
-- investigation time today.
--
-- Backup taken and verified before this ran (gzip -9, integrity-checked,
-- INSERT count matched exactly against the live table): local scratch dir,
-- not committed to git (too large, and this is dev-machine housekeeping,
-- not a droplet asset). If this migration needs to run against another
-- environment (e.g. the droplet, once this whole change is approved to
-- ship there), take the equivalent backup there first:
--   sqlite3 <db> ".dump v6_scoring_runs" | gzip -9 > backup.sql.gz
--   sqlite3 <db> ".dump v6_peer_context_assignments" | gzip -9 > backup.sql.gz
--   sqlite3 <db> ".dump v6_conditional_band_context" | gzip -9 > backup.sql.gz
--
-- registry_enriched_v6_backup_2026_07_26 is a real, separate snapshot table
-- (not ledger machinery) and is intentionally NOT touched by this migration.

DROP TABLE IF EXISTS v6_scoring_runs;
DROP TABLE IF EXISTS v6_peer_context_assignments;
DROP TABLE IF EXISTS v6_conditional_band_context;
