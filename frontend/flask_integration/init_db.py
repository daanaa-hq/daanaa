#!/usr/bin/env python3
"""
MERIT Database Initialization
=============================
Run this once to create the database tables.

    python flask_integration/init_db.py

Supports SQLite, PostgreSQL, and MySQL via SQLAlchemy.
"""

import os
import sys
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///data/merit.db')

def init_database():
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        # Organizations table — the core entity
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS organizations (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                ein TEXT UNIQUE,
                city TEXT,
                state TEXT,
                category TEXT,
                subcategory TEXT,
                merit_score INTEGER DEFAULT 0,
                revenue BIGINT DEFAULT 0,
                assets BIGINT DEFAULT 0,
                employees INTEGER DEFAULT 0,
                founded INTEGER,
                mission TEXT,
                programs TEXT DEFAULT '[]',        -- JSON array
                leadership TEXT DEFAULT '[]',      -- JSON array
                board_size INTEGER DEFAULT 0,
                revenue_trend TEXT DEFAULT '[]',   -- JSON array of {year, amount}
                program_efficiency INTEGER DEFAULT 0,
                fundraising_ratio INTEGER DEFAULT 0,
                operating_reserve REAL DEFAULT 0,
                transparency_score INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Create useful indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_org_category ON organizations(category)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_org_state ON organizations(state)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_org_merit_score ON organizations(merit_score)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_org_name ON organizations(name)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_org_search ON organizations(name, city, ein)
        """))

        # Data validation log — tracks import errors
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS validation_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT,
                record_id TEXT,
                field TEXT,
                issue TEXT,
                severity TEXT DEFAULT 'warning',  -- 'error' or 'warning'
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Update history — tracks daily update runs
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS update_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                records_processed INTEGER DEFAULT 0,
                records_inserted INTEGER DEFAULT 0,
                records_updated INTEGER DEFAULT 0,
                errors INTEGER DEFAULT 0,
                status TEXT DEFAULT 'running',  -- 'running', 'completed', 'failed'
                log_file TEXT
            )
        """))

        conn.commit()

    print(f"Database initialized: {DATABASE_URL}")
    print("Tables created: organizations, validation_log, update_history")
    print("Indexes created: category, state, merit_score, name")

if __name__ == '__main__':
    init_database()
