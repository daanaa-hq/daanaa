"""Volunteer Hours Fraud Detection — Flag suspicious patterns.

Privacy-first approach (P2, P5 from STEWARDSHIP.md):
  - No student names/emails in scores
  - Only data-driven patterns, no human judgement
  - Flags for review, doesn't auto-reject
  - Transparent scoring (admins can see why flagged)

Stewardship alignment:
  - P5: Don't weaponize transparency (respectful language, no shame)
  - P10: Human in command (flagged items require admin review)
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Optional


class SubmissionFlag:
    """Represents a flagged submission with reason and risk score."""

    def __init__(self, hour_id: str, nonprofit_ein: str, risk_score: float,
                 reason: str, severity: str = 'medium', details: Dict = None):
        self.hour_id = hour_id
        self.nonprofit_ein = nonprofit_ein
        self.risk_score = risk_score  # 0-100
        self.reason = reason
        self.severity = severity  # 'low', 'medium', 'high', 'critical'
        self.details = details or {}


class VolunteerFraudDetector:
    """Detect suspicious volunteer submission patterns."""

    def __init__(self, db_path: str = 'data/merit_registry.db'):
        self.db_path = db_path

    def _get_db(self) -> sqlite3.Connection:
        """Get database connection."""
        db = sqlite3.connect(self.db_path)
        db.row_factory = sqlite3.Row
        return db

    def analyze_submission(self, hour_id: str) -> Optional[SubmissionFlag]:
        """
        Analyze a single submission for fraud indicators.

        Returns SubmissionFlag if suspicious, None if clean.
        """
        db = self._get_db()
        try:
            # Get submission details
            submission = db.execute(
                'SELECT * FROM volunteer_hours WHERE id=?', (hour_id,)
            ).fetchone()

            if not submission:
                return None

            flags = []

            # Check for duplicate submissions (same student + org + date)
            duplicate_flag = self._check_duplicate_submission(
                db, submission['volunteer_email'], submission['nonprofit_ein'],
                submission['service_date']
            )
            if duplicate_flag:
                flags.append(duplicate_flag)

            # Check for anomalous hours (too high, too frequent)
            anomaly_flag = self._check_anomalous_hours(
                db, submission['volunteer_email'], submission['hours'],
                submission['service_date']
            )
            if anomaly_flag:
                flags.append(anomaly_flag)

            # Check for impossible schedule (multiple overlapping submissions)
            schedule_flag = self._check_impossible_schedule(
                db, submission['volunteer_email'], submission['service_date'],
                submission['hours']
            )
            if schedule_flag:
                flags.append(schedule_flag)

            # Check for rapid organization-switching
            org_switch_flag = self._check_rapid_org_switching(
                db, submission['volunteer_email'], submission['nonprofit_ein'],
                submission['submitted_at']
            )
            if org_switch_flag:
                flags.append(org_switch_flag)

            # No flags = clean submission
            if not flags:
                return None

            # Aggregate flags into single flag with composite score
            combined_score = min(100, sum(f.risk_score for f in flags) / len(flags) * 1.5)
            reasons = ' | '.join(f.reason for f in flags)
            severity = self._calculate_severity(combined_score)

            return SubmissionFlag(
                hour_id=hour_id,
                nonprofit_ein=submission['nonprofit_ein'],
                risk_score=combined_score,
                reason=f"Multiple concerns: {reasons}",
                severity=severity,
                details={'individual_flags': len(flags), 'pattern_count': len(flags)}
            )

        finally:
            db.close()

    def _check_duplicate_submission(self, db: sqlite3.Connection,
                                     volunteer_email: str, nonprofit_ein: str,
                                     service_date: str) -> Optional[SubmissionFlag]:
        """Check for duplicate submissions (same volunteer + org + date)."""
        # Query for other non-rejected submissions on same date
        count = db.execute('''
            SELECT COUNT(*) as cnt FROM volunteer_hours
            WHERE volunteer_email=? AND nonprofit_ein=? AND service_date=?
              AND status != 'rejected'
        ''', (volunteer_email, nonprofit_ein, service_date)).fetchone()

        if count and count['cnt'] > 1:
            return SubmissionFlag(
                hour_id='',  # Will be set by caller
                nonprofit_ein=nonprofit_ein,
                risk_score=45,
                reason='Duplicate submission for same org on same date',
                severity='high'
            )

        return None

    def _check_anomalous_hours(self, db: sqlite3.Connection,
                                volunteer_email: str, claimed_hours: float,
                                service_date: str) -> Optional[SubmissionFlag]:
        """Check for unusually high hours or suspicious patterns."""
        # Get volunteer's historical stats
        stats = db.execute('''
            SELECT
                AVG(hours) as avg_hours,
                MAX(hours) as max_hours,
                COUNT(*) as submission_count
            FROM volunteer_hours
            WHERE volunteer_email=? AND status='approved'
        ''', (volunteer_email,)).fetchone()

        if not stats or stats['submission_count'] < 3:
            # Not enough history to detect anomalies
            return None

        avg = stats['avg_hours'] or 0
        max_seen = stats['max_hours'] or 0

        # Flag if claimed hours are 3x+ the average or exceed max by 50%
        if claimed_hours > max_seen * 1.5:
            risk = min(80, (claimed_hours / (max_seen or 1) - 1) * 20)
            return SubmissionFlag(
                hour_id='',
                nonprofit_ein='',
                risk_score=risk,
                reason=f'Hours ({claimed_hours}h) significantly exceed volunteer history (avg: {avg:.1f}h, max: {max_seen:.1f}h)',
                severity='high' if risk > 60 else 'medium'
            )

        if claimed_hours > avg * 3:
            risk = min(70, (claimed_hours / (avg or 1) - 1) * 15)
            return SubmissionFlag(
                hour_id='',
                nonprofit_ein='',
                risk_score=risk,
                reason=f'Hours ({claimed_hours}h) are 3x+ volunteer average ({avg:.1f}h)',
                severity='medium'
            )

        return None

    def _check_impossible_schedule(self, db: sqlite3.Connection,
                                    volunteer_email: str, service_date: str,
                                    claimed_hours: float) -> Optional[SubmissionFlag]:
        """Check for overlapping submissions (impossible to volunteer >24h/day)."""
        overlapping = db.execute('''
            SELECT SUM(hours) as total FROM volunteer_hours
            WHERE volunteer_email=? AND service_date=? AND status != 'rejected'
        ''', (volunteer_email, service_date)).fetchone()

        if overlapping and overlapping['total']:
            total = overlapping['total'] + claimed_hours
            if total > 24:
                risk = min(90, (total - 24) * 5)
                return SubmissionFlag(
                    hour_id='',
                    nonprofit_ein='',
                    risk_score=risk,
                    reason=f'Total hours on {service_date} would be {total}h (physical impossibility)',
                    severity='critical' if risk > 80 else 'high'
                )

        return None

    def _check_rapid_org_switching(self, db: sqlite3.Connection,
                                    volunteer_email: str, nonprofit_ein: str,
                                    submitted_at: str) -> Optional[SubmissionFlag]:
        """Check for suspicious pattern of switching between many orgs."""
        # Count unique orgs in last 30 days
        window_start = (datetime.fromisoformat(submitted_at) - timedelta(days=30)).isoformat()

        org_count = db.execute('''
            SELECT COUNT(DISTINCT nonprofit_ein) as org_count
            FROM volunteer_hours
            WHERE volunteer_email=? AND submitted_at >= ?
        ''', (volunteer_email, window_start)).fetchone()

        if org_count and org_count['org_count'] > 15:
            # More than 15 different orgs in 30 days is suspicious
            risk = min(65, (org_count['org_count'] - 15) * 3)
            return SubmissionFlag(
                hour_id='',
                nonprofit_ein=nonprofit_ein,
                risk_score=risk,
                reason=f'Volunteer has submitted to {org_count["org_count"]} different organizations in 30 days',
                severity='medium'
            )

        return None

    def _calculate_severity(self, risk_score: float) -> str:
        """Calculate severity level from risk score."""
        if risk_score >= 80:
            return 'critical'
        elif risk_score >= 60:
            return 'high'
        elif risk_score >= 40:
            return 'medium'
        else:
            return 'low'

    def flag_submissions_batch(self, nonprofit_ein: str = None,
                               days_back: int = 7) -> List[SubmissionFlag]:
        """
        Scan recent submissions for fraud indicators.

        Args:
            nonprofit_ein: If provided, scan only this org's submissions
            days_back: Scan submissions from last N days

        Returns: List of flagged submissions
        """
        db = self._get_db()
        try:
            # Get recent submissions
            query = '''
                SELECT id FROM volunteer_hours
                WHERE status = 'pending' AND submitted_at >= datetime('now', ?)
            '''
            params = [f'-{days_back} days']

            if nonprofit_ein:
                query += ' AND nonprofit_ein = ?'
                params.append(nonprofit_ein)

            submissions = db.execute(query, params).fetchall()

            flags = []
            for sub in submissions:
                flag = self.analyze_submission(sub['id'])
                if flag:
                    flags.append(flag)

            return flags

        finally:
            db.close()

    def store_flag(self, flag: SubmissionFlag, admin_notes: str = '') -> bool:
        """Store flagged submission in database for review."""
        db = self._get_db()
        try:
            import secrets
            flag_id = 'flag_' + secrets.token_hex(8)

            db.execute('''
                INSERT OR REPLACE INTO volunteer_fraud_flags
                (flag_id, hour_id, nonprofit_ein, risk_score, reason, severity,
                 admin_notes, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'pending_review', datetime('now'))
            ''', (flag_id, flag.hour_id, flag.nonprofit_ein, flag.risk_score,
                  flag.reason, flag.severity, admin_notes))

            db.commit()
            return True

        except Exception as e:
            print(f"Error storing flag: {e}")
            return False
        finally:
            db.close()

    def get_pending_flags(self, nonprofit_ein: str = None) -> List[Dict]:
        """Get all pending fraud flags for review."""
        db = self._get_db()
        try:
            query = '''
                SELECT * FROM volunteer_fraud_flags
                WHERE status = 'pending_review'
            '''
            params = []

            if nonprofit_ein:
                query += ' AND nonprofit_ein = ?'
                params.append(nonprofit_ein)

            query += ' ORDER BY risk_score DESC'

            return [dict(row) for row in db.execute(query, params).fetchall()]

        finally:
            db.close()
