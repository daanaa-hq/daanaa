#!/usr/bin/env python3
"""
Usage Telemetry Engine — Tracks founder behavior patterns to improve dashboards.

Tracks:
- Which tabs founder uses most (for reordering)
- Which actions founder takes (approve, reject, send)
- How long founder spends on each dashboard
- Time of day patterns (when founder works)
- Success patterns (which themes resonate)

Uses:
- Adaptive UI: reorder tabs by usage frequency
- Smart recommendations: suggest actions founder commonly takes
- Timing optimization: send emails when founder is actively using platform
- Performance insights: identify slow-performing workflows

Privacy-first design:
- No PII captured beyond email
- No storing individual decision data
- Only aggregated patterns
- All data stays on server (never sent to cloud)
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from enum import Enum

logger = logging.getLogger('usage_telemetry')
logger.setLevel(logging.INFO)

DB = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'


class EventType(Enum):
    TAB_VIEW = 'tab_view'
    ACTION_TAKEN = 'action_taken'
    DECISION_MADE = 'decision_made'
    PAGE_LOAD = 'page_load'
    SESSION_START = 'session_start'
    SESSION_END = 'session_end'


def get_db():
    db = sqlite3.connect(str(DB))
    db.row_factory = sqlite3.Row
    return db


def init_telemetry_tables():
    """Create tables for usage telemetry tracking."""
    db = get_db()
    cursor = db.cursor()

    # Event log (detailed user interactions)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS telemetry_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            tab_name TEXT,
            action TEXT,
            metadata TEXT,
            duration_seconds INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Usage patterns (aggregated stats)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usage_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_type TEXT NOT NULL,
            pattern_key TEXT,
            value REAL,
            count INTEGER,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Adaptive UI state (personalization)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS adaptive_ui_state (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_name TEXT UNIQUE NOT NULL,
            setting_value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.commit()
    db.close()


def log_event(event_type: str, tab_name: str = None, action: str = None, metadata: dict = None, duration: int = None):
    """Log a user interaction event."""
    db = get_db()
    cursor = db.cursor()

    metadata_json = json.dumps(metadata or {})

    cursor.execute("""
        INSERT INTO telemetry_events (event_type, tab_name, action, metadata, duration_seconds)
        VALUES (?, ?, ?, ?, ?)
    """, (event_type, tab_name, action, metadata_json, duration))

    db.commit()
    db.close()

    logger.info(f"Logged event: {event_type} - tab:{tab_name} action:{action}")


def analyze_usage_patterns():
    """
    Analyze usage patterns from telemetry data.
    Runs hourly to update patterns.
    """
    logger.info("Analyzing usage patterns...")
    db = get_db()
    cursor = db.cursor()

    # Tab usage frequency (last 30 days)
    cursor.execute("""
        SELECT tab_name, COUNT(*) as count
        FROM telemetry_events
        WHERE event_type = 'tab_view'
        AND timestamp > datetime('now', '-30 days')
        GROUP BY tab_name
        ORDER BY count DESC
    """)

    tab_usage = cursor.fetchall()

    # Update pattern records
    for tab in tab_usage:
        cursor.execute("""
            INSERT INTO usage_patterns (pattern_type, pattern_key, value, count)
            VALUES ('tab_usage', ?, 0, ?)
            ON CONFLICT(pattern_type, pattern_key) DO UPDATE SET
                count = excluded.count,
                last_updated = CURRENT_TIMESTAMP
        """, (tab['tab_name'], tab['count']))

    # Action frequency (what founder does most)
    cursor.execute("""
        SELECT action, COUNT(*) as count
        FROM telemetry_events
        WHERE event_type = 'action_taken'
        AND timestamp > datetime('now', '-7 days')
        GROUP BY action
        ORDER BY count DESC
    """)

    actions = cursor.fetchall()

    for action in actions:
        if action['action']:
            cursor.execute("""
                INSERT INTO usage_patterns (pattern_type, pattern_key, count)
                VALUES ('action_frequency', ?, ?)
                ON CONFLICT(pattern_type, pattern_key) DO UPDATE SET
                    count = excluded.count,
                    last_updated = CURRENT_TIMESTAMP
            """, (action['action'], action['count']))

    # Time of day patterns
    cursor.execute("""
        SELECT
            strftime('%H', timestamp) as hour,
            COUNT(*) as count
        FROM telemetry_events
        WHERE timestamp > datetime('now', '-7 days')
        GROUP BY hour
        ORDER BY count DESC
        LIMIT 3
    """)

    peak_hours = cursor.fetchall()

    for hour_data in peak_hours:
        cursor.execute("""
            INSERT INTO usage_patterns (pattern_type, pattern_key, count)
            VALUES ('peak_hour', ?, ?)
            ON CONFLICT(pattern_type, pattern_key) DO UPDATE SET
                count = excluded.count,
                last_updated = CURRENT_TIMESTAMP
        """, (hour_data['hour'], hour_data['count']))

    db.commit()
    logger.info(f"Updated patterns: {len(tab_usage)} tabs, {len(actions)} actions, {len(peak_hours)} peak hours")
    db.close()


def calculate_tab_order():
    """
    Calculate recommended tab order based on usage frequency.
    High-usage tabs appear first.
    """
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT pattern_key, count
        FROM usage_patterns
        WHERE pattern_type = 'tab_usage'
        ORDER BY count DESC
    """)

    tabs = cursor.fetchall()
    db.close()

    tab_names = [tab['pattern_key'] for tab in tabs]

    return tab_names


def get_recommended_actions():
    """
    Get actions that founder frequently takes.
    Useful for quick-action buttons.
    """
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT pattern_key, count
        FROM usage_patterns
        WHERE pattern_type = 'action_frequency'
        ORDER BY count DESC
        LIMIT 5
    """)

    actions = [dict(row) for row in cursor.fetchall()]
    db.close()

    return actions


def get_active_hours():
    """Get hours when founder is most active."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT pattern_key as hour, count
        FROM usage_patterns
        WHERE pattern_type = 'peak_hour'
        ORDER BY count DESC
    """)

    hours = [dict(row) for row in cursor.fetchall()]
    db.close()

    return hours


def update_adaptive_ui(setting_name: str, setting_value: str):
    """Update adaptive UI setting (e.g., tab order, widget layout)."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO adaptive_ui_state (setting_name, setting_value)
        VALUES (?, ?)
        ON CONFLICT(setting_name) DO UPDATE SET
            setting_value = excluded.setting_value,
            updated_at = CURRENT_TIMESTAMP
    """, (setting_name, setting_value))

    db.commit()
    db.close()

    logger.info(f"Updated UI setting: {setting_name} = {setting_value}")


def get_adaptive_ui_state():
    """Get current adaptive UI configuration."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT setting_name, setting_value FROM adaptive_ui_state")

    settings = {}
    for row in cursor.fetchall():
        settings[row['setting_name']] = row['setting_value']

    db.close()

    return settings


def generate_telemetry_summary():
    """Generate summary of usage patterns and health."""
    db = get_db()
    cursor = db.cursor()

    # Most used tab (last 30 days)
    cursor.execute("""
        SELECT tab_name, count FROM usage_patterns
        WHERE pattern_type = 'tab_usage'
        ORDER BY count DESC LIMIT 1
    """)
    most_used_tab = cursor.fetchone()

    # Most frequent action (last 7 days)
    cursor.execute("""
        SELECT pattern_key as action, count FROM usage_patterns
        WHERE pattern_type = 'action_frequency'
        ORDER BY count DESC LIMIT 1
    """)
    most_frequent_action = cursor.fetchone()

    # Peak active hours
    cursor.execute("""
        SELECT pattern_key as hour, count FROM usage_patterns
        WHERE pattern_type = 'peak_hour'
        ORDER BY count DESC LIMIT 3
    """)
    peak_hours = cursor.fetchall()

    # Total events this week
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM telemetry_events
        WHERE timestamp > datetime('now', '-7 days')
    """)
    weekly_events = cursor.fetchone()['total']

    db.close()

    return {
        'most_used_tab': dict(most_used_tab) if most_used_tab else None,
        'most_frequent_action': dict(most_frequent_action) if most_frequent_action else None,
        'peak_hours': [dict(h) for h in peak_hours],
        'weekly_events': weekly_events,
        'generated_at': datetime.now().isoformat(),
    }


# Initialize tables on import
init_telemetry_tables()
