#!/usr/bin/env python3
"""
Alert manager for Daanaa infrastructure.

Monitors metrics and sends email alerts for critical conditions.
Deduplicates alerts (don't spam the same alert every minute).
Summarizes alerts in a daily digest.

Usage:
  - Run every minute via cron (metrics_collector → alert_manager)
  - Daily digest sent at 9 AM
"""

import json
import os
import smtplib
import sqlite3
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

METRICS_FILE = "/tmp/daanaa_metrics.json"
ALERTS_DB = "data/alert_log.db"
ALERT_EMAIL = os.environ.get("ALERT_EMAIL", "akbar.khowaja@gmail.com")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


def init_alert_db():
    """Create alert log table."""
    conn = sqlite3.connect(ALERTS_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY,
            timestamp TEXT,
            level TEXT,
            message TEXT,
            sent BOOLEAN DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def log_alert(level: str, message: str):
    """Log an alert. Returns True if this is a new alert (not duplicate)."""
    conn = sqlite3.connect(ALERTS_DB)

    # Check if identical alert was logged in last 30 minutes
    cutoff = (datetime.utcnow() - timedelta(minutes=30)).isoformat()
    existing = conn.execute(
        "SELECT id FROM alerts WHERE level=? AND message=? AND timestamp > ?",
        (level, message, cutoff)
    ).fetchone()

    if existing:
        conn.close()
        return False  # Duplicate, don't spam

    # Log new alert
    conn.execute(
        "INSERT INTO alerts (timestamp, level, message) VALUES (?, ?, ?)",
        (datetime.utcnow().isoformat(), level, message)
    )
    conn.commit()
    conn.close()
    return True


def send_alert_email(level: str, message: str):
    """Send immediate alert email."""
    try:
        msg = MIMEMultipart()
        msg["Subject"] = f"[{level}] Daanaa Alert: {message[:60]}"
        msg["From"] = "alerts@daanaa.org"
        msg["To"] = ALERT_EMAIL

        body = f"""
{level} Alert from Daanaa Infrastructure Monitoring

{message}

Time: {datetime.utcnow().isoformat()}Z

---
Dashboard: https://daanaa.org/admin/monitoring (when available)
Docs: docs/INFRASTRUCTURE_MONITORING.md
        """

        msg.attach(MIMEText(body, "plain"))

        # In production, use actual SMTP credentials from env
        # For now, log to file instead of failing
        with open("/tmp/daanaa_alerts.log", "a") as f:
            f.write(f"{datetime.utcnow().isoformat()} [{level}] {message}\n")

        return True
    except Exception as e:
        print(f"Error sending alert: {e}")
        return False


def process_metrics():
    """Read metrics and send alerts for new conditions."""
    if not Path(METRICS_FILE).exists():
        return

    try:
        with open(METRICS_FILE) as f:
            metrics = json.load(f)
    except:
        return

    init_alert_db()

    # Process alerts from metrics
    for alert_msg in metrics.get("alerts", []):
        if "CRITICAL" in alert_msg:
            level = "CRITICAL"
        elif "WARNING" in alert_msg:
            level = "WARNING"
        else:
            level = "INFO"

        is_new = log_alert(level, alert_msg)
        if is_new and level == "CRITICAL":
            send_alert_email(level, alert_msg)


def send_daily_digest():
    """Send daily summary of all alerts."""
    conn = sqlite3.connect(ALERTS_DB)

    # Alerts from last 24 hours
    cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()
    rows = conn.execute(
        "SELECT level, message, timestamp FROM alerts WHERE timestamp > ? ORDER BY timestamp DESC",
        (cutoff,)
    ).fetchall()

    conn.close()

    if not rows:
        return  # No alerts in last 24h

    # Summarize by level
    summary = {"CRITICAL": [], "WARNING": [], "INFO": []}
    for level, msg, ts in rows:
        summary[level].append((msg, ts))

    # Format email
    msg = MIMEMultipart()
    msg["Subject"] = f"Daanaa Daily Alert Digest — {len(rows)} events"
    msg["From"] = "alerts@daanaa.org"
    msg["To"] = ALERT_EMAIL

    body = f"""
Daanaa Infrastructure Alert Digest
Last 24 Hours

CRITICAL: {len(summary['CRITICAL'])} events
"""
    for msg_text, ts in summary["CRITICAL"]:
        body += f"\n  • {ts[:16]}Z: {msg_text}"

    body += f"""

WARNING: {len(summary['WARNING'])} events
"""
    for msg_text, ts in summary["WARNING"][:5]:  # Limit to 5
        body += f"\n  • {ts[:16]}Z: {msg_text}"

    if len(summary["WARNING"]) > 5:
        body += f"\n  ... and {len(summary['WARNING']) - 5} more"

    body += """

---
Review full logs: /tmp/daanaa_alerts.log
Dashboard: https://daanaa.org/admin/monitoring
Docs: docs/INFRASTRUCTURE_MONITORING.md
"""

    msg.attach(MIMEText(body, "plain"))

    # Log instead of send (for now)
    with open("/tmp/daanaa_alerts.log", "a") as f:
        f.write(f"\n=== DAILY DIGEST ===\n{body}\n")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "digest":
        send_daily_digest()
    else:
        process_metrics()
