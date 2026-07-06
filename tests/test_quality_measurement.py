"""Tests for quality measurement module (Task 5).

Tests measure enrichment accuracy, validity, and logging to quality_log table.
All assertions use real, hand-computed expected values.
"""
import sqlite3
import pytest
from datetime import date


def test_measure_tag_accuracy_known_input(test_db):
    """Test cause tag accuracy with known inputs where expected value is hand-computable.

    Setup:
    - enrichment_run has 2 orgs with cause_tags
      - EIN 611234567: generated = "Community Development, Education, Health Services"
      - EIN 621345678: generated = "Animal Welfare, Community Services"
    - corrections:
      - 611234567: "Community Development, Education" (2 out of 3 match = 2/3 ≈ 0.667)
      - 621345678: "Animal Welfare, Food Services" (1 out of 2 match = 1/2 = 0.5)
    - Expected overall accuracy: (0.667 + 0.5) / 2 ≈ 0.583
    """
    from scripts.quality_measurement import QualityMeasurement

    cursor = test_db.cursor()
    run_date = "2026-07-06"

    # Insert test enrichment data
    cursor.execute(
        """INSERT INTO enrichment_run
           (run_date, org_ein, enrichment_type, generated_value, confidence_score, prompt_version)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (run_date, "611234567", "cause_tags", "Community Development, Education, Health Services", 0.95, "v1.0")
    )
    cursor.execute(
        """INSERT INTO enrichment_run
           (run_date, org_ein, enrichment_type, generated_value, confidence_score, prompt_version)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (run_date, "621345678", "cause_tags", "Animal Welfare, Community Services", 0.88, "v1.0")
    )
    test_db.commit()

    # Define corrections
    corrections = {
        "611234567": "Community Development, Education",
        "621345678": "Animal Welfare, Food Services"
    }

    # Measure
    qm = QualityMeasurement(test_db)
    accuracy = qm._calculate_tag_accuracy(run_date, corrections)

    # Expected: (2/3 + 1/2) / 2 = (0.6667 + 0.5) / 2 = 0.5833
    expected = (2.0/3.0 + 0.5) / 2.0
    assert abs(accuracy - expected) < 0.01, f"Expected ~{expected:.3f}, got {accuracy:.3f}"


def test_measure_tag_accuracy_no_matches(test_db):
    """Test cause tag accuracy when no generated tags match corrections.

    Setup:
    - enrichment_run: generated = "Education, Health Services"
    - corrections: "Arts & Culture, Environment"
    - Expected accuracy: 0.0 (no overlap)
    """
    from scripts.quality_measurement import QualityMeasurement

    cursor = test_db.cursor()
    run_date = "2026-07-06"

    cursor.execute(
        """INSERT INTO enrichment_run
           (run_date, org_ein, enrichment_type, generated_value, confidence_score, prompt_version)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (run_date, "611234567", "cause_tags", "Education, Health Services", 0.85, "v1.0")
    )
    test_db.commit()

    corrections = {"611234567": "Arts & Culture, Environment"}

    qm = QualityMeasurement(test_db)
    accuracy = qm._calculate_tag_accuracy(run_date, corrections)

    assert accuracy == 0.0, f"Expected 0.0, got {accuracy}"


def test_tag_accuracy_ignores_comma_spacing_differences(test_db):
    """Regression test: tag matching must not be understated by whitespace
    differences in comma-separated tag strings.

    Setup:
    - generated: "Education, Community" (space after comma -> splits to
      ['education', ' community'] before the fix)
    - correction: "education,community" (no space -> splits to
      ['education', 'community'])
    Before the .strip() fix, ' community' != 'community' as set members, so
    only 1 of 2 tags would match (0.5 accuracy) despite being semantically
    identical. After the fix, both match (1.0 accuracy).
    """
    from scripts.quality_measurement import QualityMeasurement

    cursor = test_db.cursor()
    run_date = "2026-07-06"

    cursor.execute(
        """INSERT INTO enrichment_run
           (run_date, org_ein, enrichment_type, generated_value, confidence_score, prompt_version)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (run_date, "611234567", "cause_tags", "Education, Community", 0.9, "v1.0")
    )
    test_db.commit()

    corrections = {"611234567": "education,community"}

    qm = QualityMeasurement(test_db)
    accuracy = qm._calculate_tag_accuracy(run_date, corrections)

    assert accuracy == 1.0, (
        f"Expected 1.0 (full match once whitespace is stripped), got {accuracy} - "
        "comma-spacing differences must not understate real tag accuracy"
    )


def test_measure_website_validity(test_db):
    """Test website validity measurement from validation results.

    Setup:
    - validations: 3 websites valid, 2 invalid
    - Expected validity: 3/5 = 0.6
    """
    from scripts.quality_measurement import QualityMeasurement

    cursor = test_db.cursor()
    run_date = "2026-07-06"

    # Insert website enrichment data (not used in validity calc, but good to have)
    cursor.execute(
        """INSERT INTO enrichment_run
           (run_date, org_ein, enrichment_type, generated_value, confidence_score, prompt_version)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (run_date, "611234567", "website", "techforgood.org", 0.92, "v1.0")
    )
    test_db.commit()

    validations = {
        "ein1": True,
        "ein2": True,
        "ein3": True,
        "ein4": False,
        "ein5": False,
    }

    qm = QualityMeasurement(test_db)
    validity = qm._calculate_website_validity(run_date, validations)

    expected = 3.0 / 5.0  # 0.6
    assert abs(validity - expected) < 0.01, f"Expected {expected}, got {validity}"


def test_log_metric_writes_to_quality_log(test_db):
    """Test that _log_metric writes a row to quality_log table with exact values.

    Verifies:
    - Row is inserted
    - All columns have correct values
    - Can be queried back
    """
    from scripts.quality_measurement import QualityMeasurement

    qm = QualityMeasurement(test_db)

    date_val = "2026-07-06"
    metric_type = "cause_tag_accuracy"
    value = 0.75
    cohort = "All"
    prompt_version = "v1.0"
    notes = "Test measurement from 10 corrections"

    qm._log_metric(
        date=date_val,
        metric_type=metric_type,
        value=value,
        cohort=cohort,
        prompt_version=prompt_version,
        notes=notes
    )

    # Query back to verify
    cursor = test_db.cursor()
    cursor.execute(
        """SELECT date, metric_type, value, cohort, prompt_version, notes
           FROM quality_log
           WHERE date = ? AND metric_type = ? AND cohort = ? AND prompt_version = ?""",
        (date_val, metric_type, cohort, prompt_version)
    )
    row = cursor.fetchone()

    assert row is not None, "Row not found in quality_log"
    assert row[0] == date_val, f"Date mismatch: expected {date_val}, got {row[0]}"
    assert row[1] == metric_type, f"metric_type mismatch"
    assert abs(row[2] - value) < 0.001, f"Value mismatch: expected {value}, got {row[2]}"
    assert row[3] == cohort, f"cohort mismatch"
    assert row[4] == prompt_version, f"prompt_version mismatch"
    assert row[5] == notes, f"notes mismatch: expected '{notes}', got '{row[5]}'"


def test_log_metric_upsert_behavior(test_db):
    """Test that calling _log_metric twice with same (date, metric_type, cohort, prompt_version)
    overwrites the first row (UPSERT behavior via IntegrityError catch).

    Verifies:
    - First call inserts row with value=0.5
    - Second call with same key but value=0.75 updates the existing row
    - Only one row exists after both calls
    - Final value is 0.75
    """
    from scripts.quality_measurement import QualityMeasurement

    qm = QualityMeasurement(test_db)

    date_val = "2026-07-06"
    metric_type = "website_validity"
    cohort = "All"
    prompt_version = "v1.0"

    # First call
    qm._log_metric(
        date=date_val,
        metric_type=metric_type,
        value=0.5,
        cohort=cohort,
        prompt_version=prompt_version,
        notes="First attempt"
    )

    # Second call with same key, different value
    qm._log_metric(
        date=date_val,
        metric_type=metric_type,
        value=0.75,
        cohort=cohort,
        prompt_version=prompt_version,
        notes="Updated value"
    )

    # Query to verify UPSERT
    cursor = test_db.cursor()
    cursor.execute(
        """SELECT COUNT(*) FROM quality_log
           WHERE date = ? AND metric_type = ? AND cohort = ? AND prompt_version = ?""",
        (date_val, metric_type, cohort, prompt_version)
    )
    count = cursor.fetchone()[0]
    assert count == 1, f"Expected 1 row after UPSERT, got {count}"

    cursor.execute(
        """SELECT value, notes FROM quality_log
           WHERE date = ? AND metric_type = ? AND cohort = ? AND prompt_version = ?""",
        (date_val, metric_type, cohort, prompt_version)
    )
    row = cursor.fetchone()
    assert abs(row[0] - 0.75) < 0.001, f"Expected value 0.75, got {row[0]}"
    assert row[1] == "Updated value", f"Expected notes 'Updated value', got '{row[1]}'"


def test_measure_daily_quality_integration(test_db):
    """Integration test: measure_daily_quality orchestrates tag accuracy and website validity.

    Verifies:
    - Returns dict with 'All' key
    - 'All' dict has both 'cause_tag_accuracy' and 'website_validity' when both inputs provided
    - Both metrics logged to quality_log
    """
    from scripts.quality_measurement import QualityMeasurement

    cursor = test_db.cursor()
    run_date = "2026-07-06"

    # Insert enrichment data
    cursor.execute(
        """INSERT INTO enrichment_run
           (run_date, org_ein, enrichment_type, generated_value, confidence_score, prompt_version)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (run_date, "611234567", "cause_tags", "Education, Health", 0.9, "v1.0")
    )
    cursor.execute(
        """INSERT INTO enrichment_run
           (run_date, org_ein, enrichment_type, generated_value, confidence_score, prompt_version)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (run_date, "621345678", "website", "testorg.org", 0.88, "v1.0")
    )
    test_db.commit()

    tag_corrections = {"611234567": "Education, Health"}  # 2/2 = 1.0
    website_validations = {"ein1": True, "ein2": False}  # 1/2 = 0.5

    qm = QualityMeasurement(test_db)
    results = qm.measure_daily_quality(
        run_date=run_date,
        tag_corrections=tag_corrections,
        website_validations=website_validations
    )

    # Check results structure
    assert "All" in results, "Missing 'All' key in results"
    assert "cause_tag_accuracy" in results["All"], "Missing cause_tag_accuracy"
    assert "website_validity" in results["All"], "Missing website_validity"

    # Check accuracy value (2 tags match / 2 total = 1.0)
    assert abs(results["All"]["cause_tag_accuracy"] - 1.0) < 0.01, \
        f"Expected accuracy 1.0, got {results['All']['cause_tag_accuracy']}"

    # Check validity value (1 valid / 2 total = 0.5)
    assert abs(results["All"]["website_validity"] - 0.5) < 0.01, \
        f"Expected validity 0.5, got {results['All']['website_validity']}"

    # Verify both metrics were logged
    cursor.execute("SELECT COUNT(*) FROM quality_log WHERE date = ?", (run_date,))
    logged_count = cursor.fetchone()[0]
    assert logged_count == 2, f"Expected 2 metrics logged, got {logged_count}"
