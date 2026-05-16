#!/usr/bin/env python3
"""
MERIT Daily Update Daemon
==========================
Scaffold for your daily data update pipeline.

Integrate this with your existing merit_daemon.py or run via cron:

    crontab -e
    # Run daily at 3:00 AM
    0 3 * * * cd /home/meritgiving && python flask_integration/update_daemon.py >> logs/daily_update.log 2>&1

What this does:
1. Logs the update start
2. Fetches new/updated nonprofit data from your sources
3. Validates records before writing
4. Upserts into the database
5. Logs errors for manual review
6. Records completion status
"""

import os
import sys
import json
import logging
from datetime import datetime
from sqlalchemy import create_engine, text

# Setup paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, 'logs')
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

DATABASE_URL = os.environ.get('DATABASE_URL', f'sqlite:///{DATA_DIR}/merit.db')
engine = create_engine(DATABASE_URL)

# Logging
log_file = os.path.join(LOG_DIR, f'update_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('merit_daemon')

# Error log (human-readable, for review)
ERROR_LOG = os.path.join(BASE_DIR, 'MERIT_ERROR_LOG.md')


def log_error(source, record_id, field, issue, severity='warning'):
    """Log a validation error to both DB and markdown file."""
    # Write to DB
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO validation_log (source, record_id, field, issue, severity)
            VALUES (:source, :record_id, :field, :issue, :severity)
        """), {
            "source": source,
            "record_id": str(record_id),
            "field": field,
            "issue": issue,
            "severity": severity
        })
        conn.commit()

    # Append to markdown error log
    with open(ERROR_LOG, 'a') as f:
        f.write(f"\n## {datetime.now().isoformat()}\n")
        f.write(f"- **Source:** {source}\n")
        f.write(f"- **Record:** {record_id}\n")
        f.write(f"- **Field:** {field}\n")
        f.write(f"- **Issue:** {issue}\n")
        f.write(f"- **Severity:** {severity}\n")

    logger.warning(f"[{severity}] {source}/{record_id}: {field} — {issue}")


def validate_record(org):
    """Validate a nonprofit record before database write.
    Returns (is_valid, errors_list)."""
    errors = []

    # Required fields
    if not org.get('name') or len(org['name'].strip()) < 2:
        errors.append(('name', 'Name is required and must be at least 2 characters'))

    if not org.get('ein') or len(org['ein'].replace('-', '')) != 9:
        errors.append(('ein', 'EIN must be 9 digits'))

    # Score range validation
    score = org.get('merit_score', 0)
    if not (0 <= score <= 100):
        errors.append(('merit_score', f'Score {score} out of range 0-100'))

    # Financial sanity checks
    revenue = org.get('revenue', 0)
    if revenue < 0:
        errors.append(('revenue', f'Revenue cannot be negative: {revenue}'))
    if revenue > 1e13:  # $10T sanity limit
        errors.append(('revenue', f'Revenue seems too high: {revenue}'))

    assets = org.get('assets', 0)
    if assets < 0:
        errors.append(('assets', f'Assets cannot be negative: {assets}'))

    # Program efficiency should be 0-100
    eff = org.get('program_efficiency', 0)
    if not (0 <= eff <= 100):
        errors.append(('program_efficiency', f'Efficiency {eff} out of range 0-100'))

    # Transparency score should be 0-100
    trans = org.get('transparency_score', 0)
    if not (0 <= trans <= 100):
        errors.append(('transparency_score', f'Transparency {trans} out of range 0-100'))

    return len(errors) == 0, errors


def fetch_new_data():
    """
    TODO: Integrate with your existing data sources.

    Replace this stub with your actual data fetching logic:
    - IRS EO BMF downloads
    - ProPublica Nonprofit Explorer API
    - IRSx library for 990 parsing
    - Manual data entry API

    Should return a list of organization dicts.
    """
    logger.info("Fetching new data...")

    # EXAMPLE: Load from a staging file your existing pipeline produces
    staging_file = os.path.join(DATA_DIR, 'staging', 'new_orgs.json')
    if os.path.exists(staging_file):
        with open(staging_file) as f:
            return json.load(f)

    # EXAMPLE: Call your existing API
    # import requests
    # resp = requests.get('https://your-internal-api/orgs/updated', timeout=60)
    # return resp.json()

    logger.info("No new data to process")
    return []


def upsert_organizations(organizations):
    """Insert or update organizations in the database."""
    inserted = 0
    updated = 0
    errors = 0

    with engine.connect() as conn:
        for org in organizations:
            try:
                # Validate
                is_valid, val_errors = validate_record(org)
                if not is_valid:
                    for field, issue in val_errors:
                        log_error('daily_update', org.get('id', 'unknown'), field, issue, 'error')
                    errors += 1
                    continue

                # Check if exists
                existing = conn.execute(
                    text("SELECT id FROM organizations WHERE id = :id OR ein = :ein"),
                    {"id": org.get('id', ''), "ein": org.get('ein', '')}
                ).fetchone()

                # Upsert
                conn.execute(text("""
                    INSERT OR REPLACE INTO organizations
                    (id, name, ein, city, state, category, subcategory, merit_score,
                     revenue, assets, employees, founded, mission, programs, leadership,
                     board_size, revenue_trend, program_efficiency, fundraising_ratio,
                     operating_reserve, transparency_score, created_at, updated_at)
                    VALUES (:id, :name, :ein, :city, :state, :category, :subcategory,
                            :merit_score, :revenue, :assets, :employees, :founded,
                            :mission, :programs, :leadership, :board_size, :revenue_trend,
                            :program_efficiency, :fundraising_ratio, :operating_reserve,
                            :transparency_score,
                            COALESCE((SELECT created_at FROM organizations WHERE id = :id), CURRENT_TIMESTAMP),
                            CURRENT_TIMESTAMP)
                """), {
                    "id": org.get('id'),
                    "name": org.get('name', ''),
                    "ein": org.get('ein', ''),
                    "city": org.get('city', ''),
                    "state": org.get('state', ''),
                    "category": org.get('category', ''),
                    "subcategory": org.get('subcategory', ''),
                    "merit_score": org.get('merit_score', 0),
                    "revenue": org.get('revenue', 0),
                    "assets": org.get('assets', 0),
                    "employees": org.get('employees', 0),
                    "founded": org.get('founded', 0),
                    "mission": org.get('mission', ''),
                    "programs": json.dumps(org.get('programs', [])) if isinstance(org.get('programs'), list) else org.get('programs', '[]'),
                    "leadership": json.dumps(org.get('leadership', [])) if isinstance(org.get('leadership'), list) else org.get('leadership', '[]'),
                    "board_size": org.get('board_size', 0),
                    "revenue_trend": json.dumps(org.get('revenue_trend', [])) if isinstance(org.get('revenue_trend'), list) else org.get('revenue_trend', '[]'),
                    "program_efficiency": org.get('program_efficiency', 0),
                    "fundraising_ratio": org.get('fundraising_ratio', 0),
                    "operating_reserve": org.get('operating_reserve', 0),
                    "transparency_score": org.get('transparency_score', 0),
                })

                if existing:
                    updated += 1
                else:
                    inserted += 1

            except Exception as e:
                log_error('daily_update', org.get('id', 'unknown'), 'general', str(e), 'error')
                errors += 1

        conn.commit()

    return inserted, updated, errors


def run_update():
    """Main update pipeline."""
    logger.info("=" * 60)
    logger.info("MERIT Daily Update Starting")
    logger.info(f"Log file: {log_file}")

    # Record start
    with engine.connect() as conn:
        result = conn.execute(text("""
            INSERT INTO update_history (started_at, status)
            VALUES (CURRENT_TIMESTAMP, 'running')
            RETURNING id
        """))
        update_id = result.scalar()
        conn.commit()

    try:
        # 1. Fetch new data
        organizations = fetch_new_data()
        total = len(organizations)
        logger.info(f"Fetched {total} records")

        if total == 0:
            logger.info("No records to process. Done.")
            # Mark complete
            with engine.connect() as conn:
                conn.execute(text("""
                    UPDATE update_history
                    SET completed_at = CURRENT_TIMESTAMP, status = 'completed',
                        records_processed = 0
                    WHERE id = :id
                """), {"id": update_id})
                conn.commit()
            return

        # 2. Validate and upsert
        inserted, updated, errors = upsert_organizations(organizations)

        # 3. Record completion
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE update_history
                SET completed_at = CURRENT_TIMESTAMP, status = 'completed',
                    records_processed = :total, records_inserted = :inserted,
                    records_updated = :updated, errors = :errors,
                    log_file = :log_file
                WHERE id = :id
            """), {
                "id": update_id,
                "total": total,
                "inserted": inserted,
                "updated": updated,
                "errors": errors,
                "log_file": log_file
            })
            conn.commit()

        logger.info(f"Update complete: {inserted} inserted, {updated} updated, {errors} errors")
        logger.info(f"Total processed: {total}")

        if errors > 0:
            logger.warning(f"{errors} validation errors logged to {ERROR_LOG}")

    except Exception as e:
        logger.error(f"Update failed: {e}", exc_info=True)
        # Mark failed
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE update_history
                SET completed_at = CURRENT_TIMESTAMP, status = 'failed',
                    log_file = :log_file
                WHERE id = :id
            """), {"id": update_id, "log_file": log_file})
            conn.commit()
        raise


if __name__ == '__main__':
    run_update()
