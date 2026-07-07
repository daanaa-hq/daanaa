#!/usr/bin/env python3
"""
Database migration for enrichment pipeline.
Creates enrichment_run and quality_log tables.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "meritgiving" / "data" / "merit_registry.db"

def migrate(con=None):
    """Create enrichment tables if they don't exist."""
    owns_connection = con is None
    if owns_connection:
        con = sqlite3.connect(str(DB_PATH), timeout=180)

    cursor = con.cursor()

    # enrichment_run: stores every enrichment result with context
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS enrichment_run (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_date DATE NOT NULL,
            org_ein TEXT NOT NULL,
            enrichment_type TEXT NOT NULL CHECK(enrichment_type IN ('cause_tags', 'website')),
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
