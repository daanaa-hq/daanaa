#!/usr/bin/env python3
"""
Populate financial health data (Phase 11)
Autonomous data pipeline: compute health signals, stress tests, peer benchmarks
"""
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "merit_registry.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def compute_financial_health():
    """Compute health signals for all orgs with financial data."""
    db = get_db()

    # Get all orgs with revenue and expense data
    orgs = db.execute("""
        SELECT EIN, organization_name, total_revenue, total_expenses,
               total_assets, total_liabilities
        FROM registry_enriched
        WHERE total_revenue > 0 AND total_expenses > 0
        LIMIT 100  -- Start with sample; scale up later
    """).fetchall()

    now = datetime.now(timezone.utc).isoformat(timespec='seconds')

    for org in orgs:
        ein = org['EIN']
        revenue = org['total_revenue']
        expenses = org['total_expenses']

        # Skip if missing key metrics
        if not revenue or not expenses:
            continue

        # Calculate simple metrics
        operating_margin = (revenue - expenses) / revenue if revenue > 0 else 0
        reserves_months = (revenue - expenses) * 12 / expenses if expenses > 0 else 0

        # Determine health signal (simple heuristic)
        if reserves_months >= 6 and operating_margin > 0.05:
            signal = 'HEALTHY'
            confidence = 0.85
        elif reserves_months >= 3 or operating_margin >= 0.02:
            signal = 'STABLE'
            confidence = 0.75
        elif reserves_months < 1 or operating_margin < -0.05:
            signal = 'CRISIS'
            confidence = 0.65
        else:
            signal = 'CAUTION'
            confidence = 0.70

        # Insert health record
        try:
            db.execute("""
                INSERT OR REPLACE INTO nonprofit_financial_health
                (ein, assessment_date, reserve_ratio, reserve_months_ideal,
                 health_signal, signal_confidence)
                VALUES (?, ?, ?, 6.0, ?, ?)
            """, (ein, now, reserves_months, signal, confidence))
        except Exception as e:
            print(f"Error inserting health for {ein}: {e}")

    db.commit()
    db.close()

    print(f"✅ Populated financial health for {len(orgs)} organizations")

def compute_peer_benchmarks():
    """Compute peer benchmarks by cause area and size."""
    db = get_db()

    # Get all cause areas
    causes = db.execute("SELECT DISTINCT NTEE1 FROM registry_enriched WHERE NTEE1 IS NOT NULL").fetchall()

    now = datetime.now(timezone.utc).isoformat(timespec='seconds')

    for cause_row in causes:
        cause = cause_row[0]

        # Get orgs in this cause with health data
        orgs = db.execute("""
            SELECT eh.ein, eh.reserve_ratio, re.merit_band_v5_label
            FROM nonprofit_financial_health eh
            JOIN registry_enriched re ON re.EIN = eh.ein
            WHERE re.NTEE1 = ? AND eh.reserve_ratio IS NOT NULL
        """, (cause,)).fetchall()

        if len(orgs) < 5:
            continue  # Skip small peer groups

        reserves = sorted([o[1] for o in orgs if o[1]])
        if not reserves:
            continue

        median = reserves[len(reserves)//2]
        percentile_25 = reserves[len(reserves)//4] if len(reserves) > 3 else reserves[0]
        percentile_75 = reserves[3*len(reserves)//4] if len(reserves) > 3 else reserves[-1]

        # Insert benchmark
        try:
            db.execute("""
                INSERT OR REPLACE INTO peer_benchmarking
                (ein, peer_group, metric_type, your_value, peer_median,
                 peer_25th_percentile, peer_75th_percentile, your_rank,
                 peer_total, interpretation, benchmarked_at)
                VALUES (?, ?, 'reserve_ratio', NULL, ?, ?, ?, NULL, ?, ?, ?)
            """, (cause, f"{cause}_all", median, percentile_25, percentile_75, len(orgs),
                  f"Industry median for {cause}: {median:.1f} months reserves", now))
        except Exception as e:
            print(f"Error benchmarking {cause}: {e}")

    db.commit()
    db.close()

    print(f"✅ Computed peer benchmarks for {len(causes)} cause areas")

def seed_impact_templates():
    """Seed outcome measurement templates (Phase 13)."""
    db = get_db()

    templates = [
        ('A0', 'direct_service', 'People Served', 'Track number of individuals reached by direct service programs',
         '["participant_count", "hours_served", "people_engaged"]',
         '["program_records", "survey", "admin_data"]', 'easy'),

        ('A0', 'policy', 'Policy Change', 'Track policy changes influenced or implemented',
         '["policies_enacted", "jurisdictions_reached", "people_affected"]',
         '["government_records", "partner_attestation", "research"]', 'difficult'),

        ('B0', 'direct_service', 'Students Served', 'Track student participation and learning gains',
         '["students_served", "test_score_improvement", "graduation_rate"]',
         '["school_records", "assessments", "surveys"]', 'moderate'),

        ('C0', 'direct_service', 'People Housed', 'Track housing placements and stability',
         '["units_provided", "occupancy_retention", "people_stable_housing"]',
         '["program_data", "partner_records", "follow_up_survey"]', 'moderate'),
    ]

    now = datetime.now(timezone.utc).isoformat(timespec='seconds')

    for cause, prog_type, framework, desc, metrics, methods, difficulty in templates:
        try:
            db.execute("""
                INSERT OR IGNORE INTO cause_outcome_templates
                (cause_area, program_type, outcome_framework, description,
                 key_metrics, measurement_methods, difficulty_to_measure, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (cause, prog_type, framework, desc, metrics, methods, difficulty, now))
        except Exception as e:
            print(f"Error seeding template {framework}: {e}")

    db.commit()
    db.close()

    print(f"✅ Seeded {len(templates)} outcome measurement templates")

def main():
    print("=== Phase 11-13 Data Pipeline Population ===\n")

    try:
        compute_financial_health()
        compute_peer_benchmarks()
        seed_impact_templates()
        print("\n✅ All data pipelines populated successfully")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
