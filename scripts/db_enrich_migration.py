#!/usr/bin/env python3
"""
Database migration for enrichment pipeline.
Creates enrichment_run and quality_log tables.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "meritgiving" / "data" / "merit_registry.db"

# Marker value that only appears in the widened enrichment_type CHECK
# constraint (Task 6 added mission/volunteer_url/donate_url/donate_url_review
# on top of the original cause_tags/website). Used to detect whether an
# existing enrichment_run table still has the old, narrower constraint.
_WIDENED_CONSTRAINT_MARKER = "donate_url_review"


def _enrichment_run_needs_constraint_migration(cursor) -> bool:
    """True if enrichment_run already exists but with the OLD CHECK
    constraint (only 'cause_tags'/'website'). CREATE TABLE IF NOT EXISTS is a
    no-op against an existing table, so on any production DB created before
    Task 6, the old narrower constraint would otherwise survive forever -
    and the first insert of a 'mission'/'volunteer_url'/'donate_url'/
    'donate_url_review' row would raise IntegrityError. That raises from
    _write_results() in enrich_batch.py, outside any per-org try/except,
    which would kill the entire nightly batch.
    """
    cursor.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='enrichment_run'"
    )
    row = cursor.fetchone()
    if row is None or row[0] is None:
        return False  # table doesn't exist yet; CREATE TABLE IF NOT EXISTS below handles it
    return _WIDENED_CONSTRAINT_MARKER not in row[0]


def _migrate_enrichment_run_constraint(cursor) -> None:
    """Widen enrichment_run's enrichment_type CHECK constraint on an
    existing DB using SQLite's rename/create/copy/drop pattern (SQLite has
    no ALTER TABLE ... DROP/MODIFY CONSTRAINT). All existing rows are
    preserved. The idx_enrichment_date_ein index is dropped along with the
    old table and recreated further down by the existing
    CREATE INDEX IF NOT EXISTS statement.
    """
    cursor.execute("ALTER TABLE enrichment_run RENAME TO enrichment_run_pre_widen")
    cursor.execute("""
        CREATE TABLE enrichment_run (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_date DATE NOT NULL,
            org_ein TEXT NOT NULL,
            enrichment_type TEXT NOT NULL CHECK(enrichment_type IN (
                'cause_tags', 'website', 'mission', 'volunteer_url',
                'donate_url', 'donate_url_review'
            )),
            generated_value TEXT NOT NULL,
            confidence_score REAL CHECK(confidence_score >= 0.0 AND confidence_score <= 1.0),
            context_used TEXT,  -- JSON: {similar_orgs: [...], semantic_similarity: 0.85, ...}
            prompt_version TEXT NOT NULL DEFAULT 'v1.0',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(run_date, org_ein, enrichment_type)
        )
    """)
    cursor.execute("""
        INSERT INTO enrichment_run
            (run_id, run_date, org_ein, enrichment_type, generated_value,
             confidence_score, context_used, prompt_version, created_at)
        SELECT run_id, run_date, org_ein, enrichment_type, generated_value,
               confidence_score, context_used, prompt_version, created_at
        FROM enrichment_run_pre_widen
    """)
    cursor.execute("DROP TABLE enrichment_run_pre_widen")


def migrate(con=None):
    """Create enrichment tables if they don't exist."""
    owns_connection = con is None
    if owns_connection:
        con = sqlite3.connect(str(DB_PATH), timeout=180)

    cursor = con.cursor()

    # Widen the old CHECK constraint BEFORE the CREATE TABLE IF NOT EXISTS
    # below runs, since that statement no-ops against an already-existing
    # table and would otherwise leave a pre-Task-6 DB stuck on the old,
    # narrower constraint forever. Idempotent: no-op if already widened or
    # if the table doesn't exist yet.
    if _enrichment_run_needs_constraint_migration(cursor):
        _migrate_enrichment_run_constraint(cursor)

    # enrichment_run: stores every enrichment result with context
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS enrichment_run (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_date DATE NOT NULL,
            org_ein TEXT NOT NULL,
            enrichment_type TEXT NOT NULL CHECK(enrichment_type IN (
                'cause_tags', 'website', 'mission', 'volunteer_url',
                'donate_url', 'donate_url_review'
            )),
            generated_value TEXT NOT NULL,
            confidence_score REAL CHECK(confidence_score >= 0.0 AND confidence_score <= 1.0),
            context_used TEXT,  -- JSON: {similar_orgs: [...], semantic_similarity: 0.85, ...}
            prompt_version TEXT NOT NULL DEFAULT 'v1.0',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(run_date, org_ein, enrichment_type)
        )
    """)

    # quality_log: daily quality metrics for trending and auto-improvement
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quality_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            metric_type TEXT NOT NULL CHECK(metric_type IN ('cause_tag_accuracy', 'website_validity')),
            value REAL CHECK(value >= 0.0 AND value <= 1.0),
            cohort TEXT NOT NULL DEFAULT 'All',  -- 'All', 'NTEE_A', 'size_micro', etc.
            prompt_version TEXT NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(date, metric_type, cohort, prompt_version)
        )
    """)

    # Create indexes for fast queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_enrichment_date_ein
        ON enrichment_run(run_date, org_ein)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_quality_date_metric
        ON quality_log(date, metric_type, cohort)
    """)

    # Add volunteer_url to registry_enriched if it exists and is missing the column
    # (idempotent — same pattern donation_link_pipeline.py uses for its own new columns).
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='registry_enriched'"
    )
    if cursor.fetchone():
        existing_cols = {r[1] for r in cursor.execute("PRAGMA table_info(registry_enriched)")}
        if 'volunteer_url' not in existing_cols:
            cursor.execute("ALTER TABLE registry_enriched ADD COLUMN volunteer_url TEXT")

    con.commit()
    print("✓ Enrichment tables created/verified")

    # Only close the connection if migrate() opened it itself (con=None was
    # passed). If the caller passed in their own connection, they own its
    # lifecycle and migrate() must not close it out from under them.
    if owns_connection:
        con.close()

if __name__ == "__main__":
    migrate()
    print("Migration complete")
