"""End-to-end tests for the canonical volunteer hours system (2026-07-22 audit).

Covers every requirement from the volunteer-hours audit:
  - Event submission creates exactly one pending volunteer_hours record
  - Double-submit does not create duplicates
  - Approval creates exactly one aggregate impact record (idempotent bridge)
  - Rejection creates no aggregate record; approve-then-reject withdraws it
  - Status endpoint returns service date + status, never volunteer identity
  - Unauthorized nonprofits cannot read or act on another org's records
  - Public aggregate endpoint exposes no volunteer identity
  - IP addresses are never persisted (submitted_ip stays NULL, audit log clean)
  - Legacy paths return 410 and cannot create records
  - Full QR -> submit -> wallet status link -> approve -> public aggregate flow
"""
import json
import os
import sqlite3

import pytest

import daanaa_api as api


DB_PATH = os.environ['DB_PATH']

ORG_EIN = '331234567'
OTHER_EIN = '339876543'
OWNER_UID = 'uid-owner-org1'
INTRUDER_UID = 'uid-owner-org2'
SHORT_ID = 'evt-test-01'
EVENT_DATE = '2026-07-18'


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


@pytest.fixture(scope='module', autouse=True)
def seed_schema():
    """Create the volunteer tables exactly as they exist in production
    (they were created ad-hoc historically, not by migrations) and seed
    two claimed orgs plus one event."""
    c = _conn()
    c.executescript(f"""
        CREATE TABLE IF NOT EXISTS volunteer_hours (
            id TEXT PRIMARY KEY,
            nonprofit_ein TEXT NOT NULL,
            volunteer_name TEXT NOT NULL,
            volunteer_email TEXT NOT NULL,
            hours REAL NOT NULL,
            service_date TEXT NOT NULL,
            activity_description TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            approval_notes TEXT, approved_by TEXT, approved_at TEXT,
            rejection_reason TEXT, rejected_by TEXT, rejected_at TEXT,
            submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            event_id INTEGER, submitted_via TEXT DEFAULT 'nonprofit_entry',
            edit_count INTEGER DEFAULT 0, locked_at TEXT,
            submitted_ip TEXT, task_type TEXT
        );
        CREATE TABLE IF NOT EXISTS impact_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_ein TEXT NOT NULL,
            impact_type TEXT NOT NULL,
            amount FLOAT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            source TEXT, verified BOOLEAN DEFAULT 0, notes TEXT,
            ein TEXT, type TEXT, hours REAL, log_date TEXT
        );
        CREATE TABLE IF NOT EXISTS volunteer_notification_jobs (job_id TEXT PRIMARY KEY, hour_id TEXT NOT NULL, notification_type TEXT NOT NULL, recipient_email TEXT NOT NULL, recipient_type TEXT NOT NULL, subject TEXT NOT NULL, status TEXT DEFAULT 'pending', attempts INTEGER DEFAULT 0, max_attempts INTEGER DEFAULT 3, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, sent_at TIMESTAMP, next_retry_at TIMESTAMP, error_message TEXT, is_test_run BOOLEAN DEFAULT 0, UNIQUE(hour_id, notification_type));
        DELETE FROM volunteer_hours;
        DELETE FROM impact_logs;
        DELETE FROM volunteer_notification_jobs;
        DELETE FROM volunteer_hours_audit_log;
        DELETE FROM nonprofit_yearly_impact_cache;
        DELETE FROM volunteer_events;
        DELETE FROM org_claims WHERE ein IN ('{ORG_EIN}', '{OTHER_EIN}');
    """)
    c.execute(
        """INSERT INTO org_claims (ein, email, irs_address, pin, pin_expires_at,
                                   claim_status, firebase_uid)
           VALUES (?, 'a@org1.org', 'addr', '0000', '2030-01-01', 'verified', ?)""",
        (ORG_EIN, OWNER_UID))
    c.execute(
        """INSERT INTO org_claims (ein, email, irs_address, pin, pin_expires_at,
                                   claim_status, firebase_uid)
           VALUES (?, 'a@org2.org', 'addr', '0000', '2030-01-01', 'verified', ?)""",
        (OTHER_EIN, INTRUDER_UID))
    c.execute(
        """INSERT OR IGNORE INTO registry_enriched (EIN, organization_name)
           VALUES (?, 'Test Org One')""", (ORG_EIN,))
    c.execute(
        """INSERT INTO volunteer_events (ein, title, event_date, short_id, status)
           VALUES (?, 'Beach Cleanup', ?, ?, 'active')""",
        (ORG_EIN, EVENT_DATE, SHORT_ID))
    c.commit()
    c.close()


@pytest.fixture
def client(monkeypatch):
    import volunteer_hours_events_api as vh
    api.app.config['TESTING'] = True
    monkeypatch.setattr(api, '_require_firebase_user', lambda: OWNER_UID)
    vh._submission_rate_limit.clear()  # tests share one client IP
    with api.app.test_client() as c:
        yield c


@pytest.fixture
def intruder_client(monkeypatch):
    api.app.config['TESTING'] = True
    monkeypatch.setattr(api, '_require_firebase_user', lambda: INTRUDER_UID)
    with api.app.test_client() as c:
        yield c


def _submit(client, email='vol@example.com', name='Pat Volunteer', hours=4.0):
    return client.post(f'/api/events/{SHORT_ID}/log-hours', json={
        'volunteer_name': name,
        'volunteer_email': email,
        'orgs': [{'ein': ORG_EIN, 'hours': hours, 'task_type': 'cleanup'}],
    })


class TestSubmission:
    def test_creates_one_pending_record_with_event_service_date(self, client):
        r = _submit(client, email='one@example.com')
        assert r.status_code == 201
        body = r.get_json()
        assert body['event_date'] == EVENT_DATE
        assert len(body['submissions']) == 1
        sub = body['submissions'][0]
        assert sub['status'] == 'pending'

        c = _conn()
        rows = c.execute(
            "SELECT * FROM volunteer_hours WHERE volunteer_email='one@example.com'"
        ).fetchall()
        c.close()
        assert len(rows) == 1
        assert rows[0]['status'] == 'pending'
        assert rows[0]['service_date'] == EVENT_DATE  # event date, not today
        assert rows[0]['submitted_via'] == 'self_qr'

    def test_double_submit_returns_existing_record(self, client):
        r1 = _submit(client, email='dupe@example.com')
        r2 = _submit(client, email='dupe@example.com')
        assert r1.status_code == 201
        assert r2.status_code == 200
        assert r2.get_json()['submissions'][0]['already_submitted'] is True

        c = _conn()
        n = c.execute(
            "SELECT COUNT(*) FROM volunteer_hours WHERE volunteer_email='dupe@example.com'"
        ).fetchone()[0]
        c.close()
        assert n == 1

    def test_submission_creates_no_impact_record(self, client):
        """Pending hours must not appear in public aggregates — only approval
        bridges (and the wallet never syncs server-linked submissions)."""
        _submit(client, email='noimpact@example.com')
        c = _conn()
        n = c.execute('SELECT COUNT(*) FROM impact_logs').fetchone()[0]
        c.close()
        assert n == 0

    def test_ip_never_persisted(self, client):
        _submit(client, email='ipcheck@example.com')
        c = _conn()
        row = c.execute(
            "SELECT submitted_ip FROM volunteer_hours WHERE volunteer_email='ipcheck@example.com'"
        ).fetchone()
        audit_cols = {r[1] for r in c.execute(
            'PRAGMA table_info(volunteer_hours_audit_log)').fetchall()}
        ip_values = []
        if 'ip_address' in audit_cols:
            ip_values = [r[0] for r in c.execute(
                'SELECT ip_address FROM volunteer_hours_audit_log '
                'WHERE ip_address IS NOT NULL').fetchall()]
        c.close()
        assert row['submitted_ip'] is None  # PRIVACY-INVARIANT #3
        assert ip_values == []


class TestApprovalAndRejection:
    def _pending_id(self, client, email):
        r = _submit(client, email=email)
        return r.get_json()['submissions'][0]['submission_id']

    def test_approval_creates_exactly_one_impact_record(self, client):
        hid = self._pending_id(client, 'approve-once@example.com')
        r = client.post(f'/api/nonprofit/{ORG_EIN}/volunteer/{hid}/approve')
        assert r.status_code == 200

        c = _conn()
        n = c.execute(
            'SELECT COUNT(*) FROM impact_logs WHERE notes=?', (f'volhours:{hid}',)
        ).fetchone()[0]
        row = c.execute('SELECT log_date, ein, type FROM impact_logs WHERE notes=?',
                        (f'volhours:{hid}',)).fetchone()
        c.close()
        assert n == 1
        assert row['log_date'] == EVENT_DATE
        assert row['ein'] == ORG_EIN

    def test_double_approve_is_idempotent(self, client):
        hid = self._pending_id(client, 'approve-twice@example.com')
        r1 = client.post(f'/api/nonprofit/{ORG_EIN}/volunteer/{hid}/approve')
        r2 = client.post(f'/api/nonprofit/{ORG_EIN}/volunteer/{hid}/approve')
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r2.get_json().get('already_approved') is True

        c = _conn()
        n = c.execute('SELECT COUNT(*) FROM impact_logs WHERE notes=?',
                      (f'volhours:{hid}',)).fetchone()[0]
        c.close()
        assert n == 1

    def test_rejection_creates_no_impact_record(self, client):
        hid = self._pending_id(client, 'reject@example.com')
        r = client.post(f'/api/nonprofit/{ORG_EIN}/volunteer/{hid}/reject',
                        json={'reason': 'Not at this event'})
        assert r.status_code == 200
        c = _conn()
        n = c.execute('SELECT COUNT(*) FROM impact_logs WHERE notes=?',
                      (f'volhours:{hid}',)).fetchone()[0]
        c.close()
        assert n == 0

    def test_approve_then_reject_withdraws_impact_record(self, client):
        hid = self._pending_id(client, 'flipflop@example.com')
        client.post(f'/api/nonprofit/{ORG_EIN}/volunteer/{hid}/approve')
        client.post(f'/api/nonprofit/{ORG_EIN}/volunteer/{hid}/reject',
                    json={'reason': 'Approved in error'})
        c = _conn()
        n = c.execute('SELECT COUNT(*) FROM impact_logs WHERE notes=?',
                      (f'volhours:{hid}',)).fetchone()[0]
        c.close()
        assert n == 0

    def test_reject_missing_record_404(self, client):
        r = client.post(f'/api/nonprofit/{ORG_EIN}/volunteer/EVT-DOESNOTEXIST00/reject',
                        json={'reason': 'x'})
        assert r.status_code == 404


class TestAuthorization:
    def test_intruder_cannot_list_other_orgs_records(self, intruder_client):
        r = intruder_client.get(f'/api/nonprofit/{ORG_EIN}/volunteer/list')
        assert r.status_code == 403

    def test_intruder_cannot_approve_other_orgs_records(self, client, intruder_client):
        hid = _submit(client, email='authz@example.com').get_json()['submissions'][0]['submission_id']
        r = intruder_client.post(f'/api/nonprofit/{ORG_EIN}/volunteer/{hid}/approve')
        assert r.status_code == 403
        c = _conn()
        status = c.execute('SELECT status FROM volunteer_hours WHERE id=?', (hid,)).fetchone()[0]
        c.close()
        assert status == 'pending'


class TestStatusEndpoint:
    def test_returns_status_and_service_date_never_identity(self, client):
        hid = _submit(client, email='status@example.com').get_json()['submissions'][0]['submission_id']
        r = client.get(f'/api/volunteer/submissions/status?ids={hid}')
        assert r.status_code == 200
        subs = r.get_json()['submissions']
        assert len(subs) == 1
        assert subs[0]['status'] == 'pending'
        assert subs[0]['service_date'] == EVENT_DATE
        raw = json.dumps(r.get_json())
        assert 'status@example.com' not in raw
        assert 'Pat Volunteer' not in raw

    def test_invalid_ids_rejected(self, client):
        r = client.get('/api/volunteer/submissions/status?ids=DROP TABLE;--')
        assert r.status_code == 400


class TestPublicAggregate:
    def test_private_by_default_then_opt_in_aggregate_only(self, client):
        hid = _submit(client, email='aggregate@example.com').get_json()['submissions'][0]['submission_id']
        client.post(f'/api/nonprofit/{ORG_EIN}/volunteer/{hid}/approve')

        # Private by default
        r = client.get(f'/api/public/nonprofit/{ORG_EIN}/volunteer-impact?year=2026')
        assert r.status_code == 404

        # Build the yearly cache, then opt in
        client.get(f'/api/nonprofit/{ORG_EIN}/volunteer/impact/2026')
        client.post(f'/api/nonprofit/{ORG_EIN}/volunteer/impact/2026/visibility',
                    json={'is_public': True})

        r = client.get(f'/api/public/nonprofit/{ORG_EIN}/volunteer-impact?year=2026')
        assert r.status_code == 200
        body = r.get_json()
        assert body['total_hours_approved'] > 0
        assert 'labor_value_note' in body  # illustrative-only labeling
        raw = json.dumps(body)
        assert 'aggregate@example.com' not in raw
        assert 'Pat Volunteer' not in raw


class TestLegacyPathsDisabled:
    def test_hours_pending_gone(self, client):
        assert client.get('/api/nonprofit/hours-pending').status_code == 410

    def test_verify_hours_gone(self, client):
        r = client.post('/api/nonprofit/verify-hours',
                        json={'record_id': 'x', 'action': 'verify'})
        assert r.status_code == 410

    def test_firestore_verify_hours_gone(self, client):
        r = client.post(f'/api/nonprofit/{ORG_EIN}/verify-hours/some-log-id', json={})
        assert r.status_code == 410

    def test_legacy_paths_created_no_records(self):
        c = _conn()
        tables = {r[0] for r in c.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        n = 0
        if 'volunteer_hour_logs' in tables:
            n = c.execute('SELECT COUNT(*) FROM volunteer_hour_logs').fetchone()[0]
        c.close()
        assert n == 0


class TestDashboardSummary:
    def test_summary_matches_canonical_table(self, client):
        r = client.get('/api/nonprofit/volunteer-hours/summary?period=all')
        assert r.status_code == 200
        body = r.get_json()
        # Shape must satisfy frontend VolunteerInsightsSchema
        for key in ('total_hours_period', 'total_hours_previous_period',
                    'trend_direction', 'trend_percent', 'top_volunteers',
                    'approved_count', 'pending_count', 'rejected_count'):
            assert key in body
        assert body['trend_direction'] in ('up', 'down', 'flat')


class TestEndToEnd:
    def test_full_flow_qr_to_public_aggregate(self, client):
        """QR -> submission -> wallet link -> approval -> wallet status update
        -> public aggregate."""
        # 1. Volunteer scans QR, loads the event info page
        r = client.get(f'/api/events/{SHORT_ID}/log-hours-info')
        assert r.status_code == 200
        assert r.get_json()['event_date'] == EVENT_DATE

        # 2. Submits hours -> one pending record, wallet gets the linkage
        r = _submit(client, email='e2e@example.com', name='Casey E2E', hours=6.0)
        assert r.status_code == 201
        body = r.get_json()
        hid = body['submissions'][0]['submission_id']
        assert body['event_date'] == EVENT_DATE  # wallet stores service date

        # 3. Wallet checks status: submitted, not approved
        r = client.get(f'/api/volunteer/submissions/status?ids={hid}')
        assert r.get_json()['submissions'][0]['status'] == 'pending'

        # 4. Nonprofit sees it in the approval dashboard and approves
        r = client.get(f'/api/nonprofit/{ORG_EIN}/volunteer/list?status=pending')
        assert any(rec['id'] == hid for rec in r.get_json()['records'])
        assert client.post(
            f'/api/nonprofit/{ORG_EIN}/volunteer/{hid}/approve').status_code == 200

        # 5. Wallet refresh now sees approved (identity never in response)
        r = client.get(f'/api/volunteer/submissions/status?ids={hid}')
        sub = r.get_json()['submissions'][0]
        assert sub['status'] == 'approved'
        assert 'e2e@example.com' not in json.dumps(r.get_json())

        # 6. Exactly one aggregate impact record exists for this submission
        c = _conn()
        n = c.execute('SELECT COUNT(*) FROM impact_logs WHERE notes=?',
                      (f'volhours:{hid}',)).fetchone()[0]
        c.close()
        assert n == 1

        # 7. Org opts in -> public aggregate includes the hours, no identity
        client.get(f'/api/nonprofit/{ORG_EIN}/volunteer/impact/2026')
        client.post(f'/api/nonprofit/{ORG_EIN}/volunteer/impact/2026/visibility',
                    json={'is_public': True})
        r = client.get(f'/api/public/nonprofit/{ORG_EIN}/volunteer-impact?year=2026')
        assert r.status_code == 200
        assert r.get_json()['total_hours_approved'] >= 6.0
        assert 'Casey' not in json.dumps(r.get_json())
