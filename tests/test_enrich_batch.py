import sqlite3
import pytest


def test_enrichment_tables_exist():
    """Verify enrichment_run and quality_log tables are created."""
    con = sqlite3.connect(':memory:')
    cursor = con.cursor()

    # Import and run migration
    from scripts.db_enrich_migration import migrate
    migrate(con)

    # Check tables exist
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='enrichment_run'"
    )
    assert cursor.fetchone() is not None, "enrichment_run table not created"

    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='quality_log'"
    )
    assert cursor.fetchone() is not None, "quality_log table not created"

    con.close()


def test_enrichment_run_schema():
    """Verify enrichment_run has all required columns."""
    con = sqlite3.connect(':memory:')
    from scripts.db_enrich_migration import migrate
    migrate(con)

    cursor = con.cursor()
    cursor.execute("PRAGMA table_info(enrichment_run)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}

    required = {
        'run_id': 'INTEGER',
        'run_date': 'DATE',
        'org_ein': 'TEXT',
        'enrichment_type': 'TEXT',
        'generated_value': 'TEXT',
        'confidence_score': 'REAL',
        'context_used': 'TEXT',
        'prompt_version': 'TEXT',
        'created_at': 'TIMESTAMP'
    }

    for col, typ in required.items():
        assert col in columns, f"Column {col} missing from enrichment_run"

    con.close()


def test_quality_log_schema():
    """Verify quality_log has all required columns."""
    con = sqlite3.connect(':memory:')
    from scripts.db_enrich_migration import migrate
    migrate(con)

    cursor = con.cursor()
    cursor.execute("PRAGMA table_info(quality_log)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}

    required = {
        'date': 'DATE',
        'metric_type': 'TEXT',
        'value': 'REAL',
        'cohort': 'TEXT',
        'prompt_version': 'TEXT',
        'notes': 'TEXT'
    }

    for col, typ in required.items():
        assert col in columns, f"Column {col} missing from quality_log"

    con.close()


def test_migrate_adds_volunteer_url_column():
    """volunteer_url must exist on registry_enriched after migrate() runs,
    since Task 2's website_content.py discovers this and Task 6 needs
    somewhere to write it."""
    import sqlite3
    con = sqlite3.connect(':memory:')
    cursor = con.cursor()
    cursor.execute("""
        CREATE TABLE registry_enriched (
            EIN TEXT PRIMARY KEY, organization_name TEXT
        )
    """)
    con.commit()

    from scripts.db_enrich_migration import migrate
    migrate(con)

    cols = {row[1] for row in cursor.execute("PRAGMA table_info(registry_enriched)")}
    assert 'volunteer_url' in cols
    con.close()
