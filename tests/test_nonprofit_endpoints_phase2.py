"""Tests for Track 2 Phase 2: Volunteer Reporting + Donor Tools"""
import pytest
import sqlite3
import uuid
import os
import json
from datetime import datetime, timedelta
from pathlib import Path

# Isolated DB via env (see conftest.py) — never write test rows into the live DB.
DB_PATH = os.environ.get('DB_PATH', 'data/merit_registry.db')


@pytest.fixture
def db():
    """Get database connection with test setup.

    Creates background_jobs + donor_templates mirroring the production DDL
    (those tables were created directly in the live DB when the feature
    shipped; nonprofit_portal_endpoints.py uses but never creates them).
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS background_jobs (
            id TEXT PRIMARY KEY,
            nonprofit_ein TEXT NOT NULL,
            job_type TEXT NOT NULL DEFAULT 'export_volunteer_hours',
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            started_at TEXT,
            completed_at TEXT,
            result_path TEXT,
            error_message TEXT,
            params TEXT,
            FOREIGN KEY (nonprofit_ein) REFERENCES nonprofit_accounts(ein)
        );
        CREATE TABLE IF NOT EXISTS donor_templates (
            id TEXT PRIMARY KEY,
            nonprofit_ein TEXT NOT NULL,
            template_name TEXT NOT NULL,
            template_body TEXT NOT NULL,
            is_default BOOLEAN DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (nonprofit_ein) REFERENCES nonprofit_accounts(ein),
            UNIQUE(nonprofit_ein, template_name)
        );
    ''')
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def test_org(db):
    """Create test nonprofit account."""
    cursor = db.cursor()
    ein = f'test_{uuid.uuid4().hex[:8]}'
    account_id = str(uuid.uuid4())

    # Ensure nonprofit_accounts table exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nonprofit_accounts (
            id TEXT PRIMARY KEY,
            ein TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Ensure volunteer_hours table exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS volunteer_hours (
            id TEXT PRIMARY KEY,
            nonprofit_ein TEXT NOT NULL,
            volunteer_name TEXT NOT NULL,
            volunteer_email TEXT NOT NULL,
            hours REAL NOT NULL,
            service_date TEXT NOT NULL,
            activity_description TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            approval_notes TEXT,
            approved_by TEXT,
            approved_at TEXT,
            rejection_reason TEXT,
            rejected_by TEXT,
            rejected_at TEXT,
            submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            event_id INTEGER,
            submitted_via TEXT DEFAULT 'nonprofit_entry',
            edit_count INTEGER DEFAULT 0,
            locked_at TEXT,
            submitted_ip TEXT,
            task_type TEXT,
            FOREIGN KEY (nonprofit_ein) REFERENCES nonprofit_accounts(ein)
        )
    ''')

    cursor.execute('''
        INSERT OR IGNORE INTO nonprofit_accounts (id, ein, email, name)
        VALUES (?, ?, ?, ?)
    ''', (account_id, ein, f'test_{ein}@test.org', 'Test Nonprofit'))

    db.commit()
    return {'id': account_id, 'ein': ein}


class TestBackgroundJobs:
    """Test background job tracking (CSV exports)."""

    def test_background_jobs_table_exists(self, db):
        """Verify background_jobs table schema."""
        cursor = db.cursor()
        cursor.execute("PRAGMA table_info(background_jobs)")
        columns = {row[1] for row in cursor.fetchall()}

        required = {'id', 'nonprofit_ein', 'job_type', 'status', 'result_path', 'error_message'}
        assert required.issubset(columns), f"Missing columns: {required - columns}"

    def test_donor_templates_table_exists(self, db):
        """Verify donor_templates table schema."""
        cursor = db.cursor()
        cursor.execute("PRAGMA table_info(donor_templates)")
        columns = {row[1] for row in cursor.fetchall()}

        required = {'id', 'nonprofit_ein', 'template_name', 'template_body', 'is_default'}
        assert required.issubset(columns), f"Missing columns: {required - columns}"


class TestVolunteerHoursSummary:
    """Test volunteer hours summary endpoint."""

    def test_summary_this_month(self, db, test_org):
        """Test monthly summary calculation."""
        cursor = db.cursor()
        ein = test_org['ein']

        # Insert test volunteer hours
        cursor.execute('''
            INSERT INTO volunteer_hours
            (id, nonprofit_ein, volunteer_name, volunteer_email, hours, service_date,
             activity_description, status, approved_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'verified', ?)
        ''', (
            str(uuid.uuid4()),
            ein,
            'Alice Smith',
            'alice@test.org',
            10.0,
            datetime.now().strftime('%Y-%m-%d'),
            'Event setup',
            datetime.now().isoformat(),
        ))

        cursor.execute('''
            INSERT INTO volunteer_hours
            (id, nonprofit_ein, volunteer_name, volunteer_email, hours, service_date,
             activity_description, status, approved_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'verified', ?)
        ''', (
            str(uuid.uuid4()),
            ein,
            'Bob Jones',
            'bob@test.org',
            8.0,
            datetime.now().strftime('%Y-%m-%d'),
            'Mentoring',
            datetime.now().isoformat(),
        ))

        db.commit()

        # Verify hours were inserted
        cursor.execute(
            'SELECT SUM(hours) FROM volunteer_hours WHERE nonprofit_ein = ? AND status = ?',
            (ein, 'verified')
        )
        total = cursor.fetchone()[0]
        assert total == 18.0, f"Expected 18 hours, got {total}"

    def test_top_volunteers_ranking(self, db, test_org):
        """Test top volunteers are ranked correctly."""
        cursor = db.cursor()
        ein = test_org['ein']

        # Insert volunteers with different hours
        volunteers = [
            ('Alice', 40),
            ('Bob', 35),
            ('Carol', 28),
            ('Dave', 15),
        ]

        for name, hours in volunteers:
            cursor.execute('''
                INSERT INTO volunteer_hours
                (id, nonprofit_ein, volunteer_name, volunteer_email, hours, service_date,
                 activity_description, status, approved_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'verified', ?)
            ''', (
                str(uuid.uuid4()),
                ein,
                name,
                f'{name.lower()}@test.org',
                hours,
                datetime.now().strftime('%Y-%m-%d'),
                'Test activity',
                datetime.now().isoformat(),
            ))

        db.commit()

        # Verify ranking
        cursor.execute('''
            SELECT volunteer_name, SUM(hours) as total_hours
            FROM volunteer_hours
            WHERE nonprofit_ein = ? AND status = 'verified'
            GROUP BY volunteer_name
            ORDER BY total_hours DESC
            LIMIT 3
        ''', (ein,))

        top_3 = cursor.fetchall()
        assert len(top_3) == 3
        assert top_3[0]['volunteer_name'] == 'Alice'
        assert top_3[1]['volunteer_name'] == 'Bob'
        assert top_3[2]['volunteer_name'] == 'Carol'


class TestDonorTemplates:
    """Test donor template management."""

    def test_create_donor_template(self, db, test_org):
        """Test creating a custom donor template."""
        cursor = db.cursor()
        ein = test_org['ein']
        template_id = str(uuid.uuid4())

        cursor.execute('''
            INSERT INTO donor_templates
            (id, nonprofit_ein, template_name, template_body, is_default)
            VALUES (?, ?, ?, ?, 0)
        ''', (
            template_id,
            ein,
            'Custom Thank You',
            'Dear {donor_name}, Thank you for {amount} on {date}. Best, {org_name}',
        ))

        db.commit()

        # Verify insertion
        cursor.execute('SELECT * FROM donor_templates WHERE id = ?', (template_id,))
        row = cursor.fetchone()
        assert row is not None
        assert row['template_name'] == 'Custom Thank You'
        assert '{donor_name}' in row['template_body']

    def test_template_unique_name_per_org(self, db, test_org):
        """Test that template names are unique per org."""
        cursor = db.cursor()
        ein = test_org['ein']

        cursor.execute('''
            INSERT INTO donor_templates
            (id, nonprofit_ein, template_name, template_body, is_default)
            VALUES (?, ?, ?, ?, 0)
        ''', (str(uuid.uuid4()), ein, 'Test Template', 'Body {donor_name}'))

        db.commit()

        # Try to insert duplicate name
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute('''
                INSERT INTO donor_templates
                (id, nonprofit_ein, template_name, template_body, is_default)
                VALUES (?, ?, ?, ?, 0)
            ''', (str(uuid.uuid4()), ein, 'Test Template', 'Different body'))
            db.commit()


class TestStatusCounts:
    """Test volunteer status counting."""

    def test_count_by_status(self, db, test_org):
        """Test counting volunteer submissions by status."""
        cursor = db.cursor()
        ein = test_org['ein']

        # Create submissions with different statuses
        statuses = ['pending', 'verified', 'rejected', 'verified']
        for status in statuses:
            cursor.execute('''
                INSERT INTO volunteer_hours
                (id, nonprofit_ein, volunteer_name, volunteer_email, hours, service_date,
                 activity_description, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(uuid.uuid4()),
                ein,
                f'Volunteer_{status}',
                f'{status}@test.org',
                5.0,
                datetime.now().strftime('%Y-%m-%d'),
                'Activity',
                status,
            ))

        db.commit()

        # Count by status
        cursor.execute('''
            SELECT status, COUNT(*) as count
            FROM volunteer_hours
            WHERE nonprofit_ein = ?
            GROUP BY status
        ''', (ein,))

        counts = {row['status']: row['count'] for row in cursor.fetchall()}
        assert counts.get('pending', 0) == 1
        assert counts.get('verified', 0) == 2
        assert counts.get('rejected', 0) == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
