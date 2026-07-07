"""Task 6 fix: regression tests for the enrichment_run CHECK constraint
migration.

Context: db_enrich_migration.py originally widened enrichment_run's
enrichment_type CHECK constraint from ('cause_tags', 'website') to include
'mission', 'volunteer_url', 'donate_url', 'donate_url_review' - but did so
via `CREATE TABLE IF NOT EXISTS`, which is a no-op against a table that
already exists. On any production DB created before this widening, the old
narrower constraint would survive migrate() forever, and the first insert
of one of the new enrichment types would raise sqlite3.IntegrityError from
_write_results() in enrich_batch.py - outside any per-org try/except,
killing the entire nightly batch.

These tests build an in-memory DB with the OLD (pre-widening) schema by
hand, run migrate() against it, and confirm the constraint is actually
widened - not just present on a fresh table.
"""
import sqlite3
import pytest


def _create_old_schema_enrichment_run(con):
    """Recreate the exact pre-Task-6 enrichment_run schema (only
    'cause_tags'/'website' allowed), matching what shipped in commit
    a9a01ee2f4d before the Task 6 widening."""
    cursor = con.cursor()
    cursor.execute("""
        CREATE TABLE enrichment_run (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_date DATE NOT NULL,
            org_ein TEXT NOT NULL,
            enrichment_type TEXT NOT NULL CHECK(enrichment_type IN ('cause_tags', 'website')),
            generated_value TEXT NOT NULL,
            confidence_score REAL CHECK(confidence_score >= 0.0 AND confidence_score <= 1.0),
            context_used TEXT,
            prompt_version TEXT NOT NULL DEFAULT 'v1.0',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(run_date, org_ein, enrichment_type)
        )
    """)
    con.commit()


def test_migrate_widens_old_constraint_so_new_types_insert_cleanly():
    """The core regression: on a DB with the pre-Task-6 constraint, migrate()
    must widen it so inserting a 'mission' row (one of the new enrichment
    types) succeeds instead of raising IntegrityError."""
    con = sqlite3.connect(':memory:')
    _create_old_schema_enrichment_run(con)

    from scripts.db_enrich_migration import migrate
    migrate(con)

    cursor = con.cursor()
    # Would raise sqlite3.IntegrityError before the fix, since the old
    # ('cause_tags', 'website') constraint would still be in force.
    cursor.execute(
        """INSERT INTO enrichment_run
           (run_date, org_ein, enrichment_type, generated_value, confidence_score, prompt_version)
           VALUES ('2026-07-07', '123456789', 'mission', 'A test mission.', 0.85, 'v1.0')"""
    )
    con.commit()

    cursor.execute("SELECT enrichment_type FROM enrichment_run WHERE org_ein = '123456789'")
    assert cursor.fetchone()[0] == 'mission'
    con.close()


@pytest.mark.parametrize(
    "enrichment_type",
    ["volunteer_url", "donate_url", "donate_url_review"],
)
def test_migrate_widens_constraint_for_all_new_enrichment_types(enrichment_type):
    """Every new enrichment type Task 6 introduced must insert cleanly after
    migrate() runs against an old-schema DB, not just 'mission'."""
    con = sqlite3.connect(':memory:')
    _create_old_schema_enrichment_run(con)

    from scripts.db_enrich_migration import migrate
    migrate(con)

    cursor = con.cursor()
    cursor.execute(
        """INSERT INTO enrichment_run
           (run_date, org_ein, enrichment_type, generated_value, confidence_score, prompt_version)
           VALUES ('2026-07-07', '123456789', ?, 'some value', 0.85, 'v1.0')""",
        (enrichment_type,)
    )
    con.commit()

    cursor.execute("SELECT COUNT(*) FROM enrichment_run WHERE enrichment_type = ?", (enrichment_type,))
    assert cursor.fetchone()[0] == 1
    con.close()


def test_migrate_preserves_existing_rows_through_constraint_widening():
    """The rename/create/copy/drop migration pattern must not lose any
    pre-existing enrichment_run rows written under the old constraint."""
    con = sqlite3.connect(':memory:')
    _create_old_schema_enrichment_run(con)

    cursor = con.cursor()
    cursor.execute(
        """INSERT INTO enrichment_run
           (run_date, org_ein, enrichment_type, generated_value, confidence_score, prompt_version)
           VALUES ('2026-07-01', '999999999', 'cause_tags', 'Education, Health', 0.7, 'v1.0')"""
    )
    cursor.execute(
        """INSERT INTO enrichment_run
           (run_date, org_ein, enrichment_type, generated_value, confidence_score, prompt_version)
           VALUES ('2026-07-01', '999999999', 'website', 'https://example.org', 0.9, 'v1.0')"""
    )
    con.commit()

    from scripts.db_enrich_migration import migrate
    migrate(con)

    cursor.execute("SELECT COUNT(*) FROM enrichment_run WHERE org_ein = '999999999'")
    assert cursor.fetchone()[0] == 2, "Pre-existing rows must survive the constraint migration"
    con.close()


def test_migrate_is_idempotent_on_already_widened_schema():
    """Running migrate() twice (e.g. two nightly cron invocations, or a
    fresh DB that already has the widened constraint) must not raise or
    duplicate/lose data - the migration must detect it's already applied
    and skip the rename/create/copy/drop entirely."""
    con = sqlite3.connect(':memory:')

    from scripts.db_enrich_migration import migrate
    migrate(con)  # first run: creates the table fresh with the widened constraint
    migrate(con)  # second run: must be a clean no-op, not an error

    cursor = con.cursor()
    cursor.execute(
        """INSERT INTO enrichment_run
           (run_date, org_ein, enrichment_type, generated_value, confidence_score, prompt_version)
           VALUES ('2026-07-07', '111222333', 'donate_url', 'https://example.org/give', 0.9, 'v1.0')"""
    )
    con.commit()

    cursor.execute("SELECT COUNT(*) FROM enrichment_run")
    assert cursor.fetchone()[0] == 1
    con.close()


def test_migrate_on_fresh_db_creates_widened_constraint_directly():
    """A brand-new DB (no enrichment_run table at all) must get the widened
    constraint straight away via the CREATE TABLE IF NOT EXISTS path - no
    migration needed since there's no old table to widen."""
    con = sqlite3.connect(':memory:')

    from scripts.db_enrich_migration import migrate
    migrate(con)

    cursor = con.cursor()
    cursor.execute(
        """INSERT INTO enrichment_run
           (run_date, org_ein, enrichment_type, generated_value, confidence_score, prompt_version)
           VALUES ('2026-07-07', '444555666', 'volunteer_url', 'https://example.org/volunteer', 0.9, 'v1.0')"""
    )
    con.commit()
    cursor.execute("SELECT COUNT(*) FROM enrichment_run")
    assert cursor.fetchone()[0] == 1
    con.close()


def test_old_constraint_actually_rejects_new_types_before_migration():
    """Sanity check that _create_old_schema_enrichment_run really reproduces
    the old, narrower constraint (i.e. this test file would have caught the
    original bug) - without this, the other tests above could be passing
    for the wrong reason."""
    con = sqlite3.connect(':memory:')
    _create_old_schema_enrichment_run(con)

    cursor = con.cursor()
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            """INSERT INTO enrichment_run
               (run_date, org_ein, enrichment_type, generated_value, confidence_score, prompt_version)
               VALUES ('2026-07-07', '123456789', 'mission', 'A test mission.', 0.85, 'v1.0')"""
        )
    con.close()
