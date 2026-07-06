"""Tests for batch monitoring module (Task 9).

Tests the monitoring script's core logic for checking enrichment batch health
and quality trends. Uses check_batch_health() function for testability
(separate from main() which handles printing).
"""
import sqlite3
import pytest
from datetime import date, timedelta


def test_check_batch_health_batch_ran_yesterday(test_db):
    """Test check_batch_health when yesterday's enrichment batch succeeded.

    Setup:
    - enrichment_run has 5 cause_tag results from yesterday
    - quality_log has 1 quality metric from yesterday: 0.92
    - Expected: batch_ran=True, enrichment_count=5, quality_avg=0.92, trend="→"
    """
    from scripts.monitor_batch import check_batch_health

    cursor = test_db.cursor()
    yesterday = str(date.today() - timedelta(days=1))

    # Insert 5 enrichment results from yesterday
    for i in range(5):
        cursor.execute(
            """INSERT INTO enrichment_run
               (run_date, org_ein, enrichment_type, generated_value, confidence_score, prompt_version)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (yesterday, f"61123456{i}", "cause_tags", "Education, Health", 0.85, "v1.0")
        )

    # Insert 1 quality metric from yesterday (avg will be just this value)
    cursor.execute(
        """INSERT INTO quality_log
           (date, metric_type, value, cohort, prompt_version)
           VALUES (?, ?, ?, ?, ?)""",
        (yesterday, "cause_tag_accuracy", 0.92, "All", "v1.0")
    )
    test_db.commit()

    health = check_batch_health(test_db, check_date=yesterday)

    assert health['batch_ran'] is True
    assert health['enrichment_count'] == 5
    assert health['checked_date'] == yesterday
    assert abs(health['quality_avg'] - 0.92) < 0.001
    assert health['quality_trend'] == '→'  # Single value, no trend


def test_check_batch_health_batch_missing(test_db):
    """Test check_batch_health when yesterday's batch did NOT run.

    Setup:
    - No enrichment_run rows for yesterday
    - No quality_log rows for yesterday
    - Expected: batch_ran=False, enrichment_count=0, quality_avg=None, trend=None
    """
    from scripts.monitor_batch import check_batch_health

    yesterday = str(date.today() - timedelta(days=1))

    health = check_batch_health(test_db, check_date=yesterday)

    assert health['batch_ran'] is False
    assert health['enrichment_count'] == 0
    assert health['checked_date'] == yesterday
    assert health['quality_avg'] is None
    assert health['quality_trend'] is None


def test_check_batch_health_quality_trend_increasing(test_db):
    """Test quality trend detection: increasing accuracy over 3 recent dates.

    Setup:
    - 3 quality_log entries with increasing values:
      - 3 days ago: 0.75
      - 2 days ago: 0.82
      - 1 day ago: 0.90
    - Expected average: (0.75 + 0.82 + 0.90) / 3 ≈ 0.823
    - Expected trend: '↑' (0.90 > 0.75)
    """
    from scripts.monitor_batch import check_batch_health

    cursor = test_db.cursor()
    today = date.today()

    # Insert 3 quality metrics with increasing trend
    dates = [
        str(today - timedelta(days=3)),
        str(today - timedelta(days=2)),
        str(today - timedelta(days=1))
    ]
    values = [0.75, 0.82, 0.90]

    for d, v in zip(dates, values):
        cursor.execute(
            """INSERT INTO quality_log
               (date, metric_type, value, cohort, prompt_version)
               VALUES (?, ?, ?, ?, ?)""",
            (d, "cause_tag_accuracy", v, "All", "v1.0")
        )
    test_db.commit()

    check_date = str(today - timedelta(days=1))
    health = check_batch_health(test_db, check_date=check_date)

    # Average of [0.75, 0.82, 0.90]
    expected_avg = (0.75 + 0.82 + 0.90) / 3.0
    assert abs(health['quality_avg'] - expected_avg) < 0.001
    assert health['quality_trend'] == '↑'


def test_check_batch_health_quality_trend_decreasing(test_db):
    """Test quality trend detection: decreasing accuracy over 3 recent dates.

    Setup:
    - 3 quality_log entries with decreasing values:
      - 3 days ago: 0.95
      - 2 days ago: 0.87
      - 1 day ago: 0.76
    - Expected average: (0.95 + 0.87 + 0.76) / 3 ≈ 0.863
    - Expected trend: '↓' (0.76 < 0.95)
    """
    from scripts.monitor_batch import check_batch_health

    cursor = test_db.cursor()
    today = date.today()

    # Insert 3 quality metrics with decreasing trend
    dates = [
        str(today - timedelta(days=3)),
        str(today - timedelta(days=2)),
        str(today - timedelta(days=1))
    ]
    values = [0.95, 0.87, 0.76]

    for d, v in zip(dates, values):
        cursor.execute(
            """INSERT INTO quality_log
               (date, metric_type, value, cohort, prompt_version)
               VALUES (?, ?, ?, ?, ?)""",
            (d, "cause_tag_accuracy", v, "All", "v1.0")
        )
    test_db.commit()

    check_date = str(today - timedelta(days=1))
    health = check_batch_health(test_db, check_date=check_date)

    # Average of [0.95, 0.87, 0.76]
    expected_avg = (0.95 + 0.87 + 0.76) / 3.0
    assert abs(health['quality_avg'] - expected_avg) < 0.001
    assert health['quality_trend'] == '↓'


def test_check_batch_health_quality_trend_flat(test_db):
    """Test quality trend detection: flat accuracy (same value across dates).

    Setup:
    - 3 quality_log entries with flat values:
      - 3 days ago: 0.85
      - 2 days ago: 0.85
      - 1 day ago: 0.85
    - Expected average: 0.85
    - Expected trend: '→' (0.85 == 0.85)
    """
    from scripts.monitor_batch import check_batch_health

    cursor = test_db.cursor()
    today = date.today()

    # Insert 3 quality metrics with flat trend
    dates = [
        str(today - timedelta(days=3)),
        str(today - timedelta(days=2)),
        str(today - timedelta(days=1))
    ]
    value = 0.85

    for d in dates:
        cursor.execute(
            """INSERT INTO quality_log
               (date, metric_type, value, cohort, prompt_version)
               VALUES (?, ?, ?, ?, ?)""",
            (d, "cause_tag_accuracy", value, "All", "v1.0")
        )
    test_db.commit()

    check_date = str(today - timedelta(days=1))
    health = check_batch_health(test_db, check_date=check_date)

    assert abs(health['quality_avg'] - 0.85) < 0.001
    assert health['quality_trend'] == '→'


def test_check_batch_health_mixed_enrichment_types(test_db):
    """Test check_batch_health counts all enrichment_run rows regardless of type.

    Setup:
    - 3 cause_tags + 2 website results from yesterday
    - Expected enrichment_count: 5 (all types counted)
    """
    from scripts.monitor_batch import check_batch_health

    cursor = test_db.cursor()
    yesterday = str(date.today() - timedelta(days=1))

    # Insert 3 cause_tags
    for i in range(3):
        cursor.execute(
            """INSERT INTO enrichment_run
               (run_date, org_ein, enrichment_type, generated_value, confidence_score, prompt_version)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (yesterday, f"61123456{i}", "cause_tags", "Education, Health", 0.85, "v1.0")
        )

    # Insert 2 websites
    for i in range(3, 5):
        cursor.execute(
            """INSERT INTO enrichment_run
               (run_date, org_ein, enrichment_type, generated_value, confidence_score, prompt_version)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (yesterday, f"61123456{i}", "website", "myorg.org", 0.75, "v1.0")
        )
    test_db.commit()

    health = check_batch_health(test_db, check_date=yesterday)

    assert health['batch_ran'] is True
    assert health['enrichment_count'] == 5
