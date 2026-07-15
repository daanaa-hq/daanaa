#!/usr/bin/env python3
"""
Simple Flask API for discovery system status.
Provides real-time visibility into daemon state, queue, metrics.

Endpoint: GET /api/discovery/status
Returns: JSON with daemon health, queue depth, recent stats
"""

from flask import Blueprint, jsonify
import sqlite3
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

discovery_status_bp = Blueprint('discovery_status', __name__, url_prefix='/api/discovery')

DB = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'


@discovery_status_bp.route('/status', methods=['GET'])
def get_discovery_status():
    """Get real-time discovery daemon status."""

    # Check if daemon is running
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'discovery_daemon.py'],
            capture_output=True,
            text=True,
            timeout=2
        )
        daemon_running = len(result.stdout.strip()) > 0
    except:
        daemon_running = False

    # Get queue stats
    db = sqlite3.connect(str(DB))
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM link_deployment_queue WHERE deployed_at IS NULL")
    queue_undeployed = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM link_deployment_queue")
    queue_total = cursor.fetchone()[0]

    # Get last 24h stats
    cutoff_time = (datetime.now() - timedelta(hours=24)).isoformat()
    cursor.execute(
        "SELECT COUNT(*) FROM link_deployment_queue WHERE created_at > ?",
        (cutoff_time,)
    )
    deployed_24h = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM link_deployment_queue WHERE deployed_at > ?",
        (cutoff_time,)
    )
    deployments_24h = cursor.fetchone()[0]

    # Get next deployment time
    from datetime import datetime as dt
    now = dt.now()
    hours = [0, 4, 8, 12, 16, 20]
    next_deployment = None
    for h in hours:
        deployment_time = now.replace(hour=h, minute=0, second=0, microsecond=0)
        if deployment_time > now:
            next_deployment = deployment_time.isoformat()
            break
    if not next_deployment:
        # Next deployment is tomorrow at midnight
        next_deployment = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

    db.close()

    return jsonify({
        'status': 'healthy' if daemon_running else 'unhealthy',
        'daemon': {
            'running': daemon_running,
            'timestamp': datetime.now().isoformat()
        },
        'queue': {
            'waiting': queue_undeployed,
            'total_all_time': queue_total,
            'deployed_24h': deployments_24h
        },
        'deployment': {
            'next_window': next_deployment,
            'schedule': '0, 4, 8, 12, 16, 20 (6x daily)'
        }
    })


@discovery_status_bp.route('/health', methods=['GET'])
def get_discovery_health():
    """Lightweight health check (for monitoring)."""
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'discovery_daemon.py'],
            capture_output=True,
            text=True,
            timeout=2
        )
        running = len(result.stdout.strip()) > 0
        return jsonify({'healthy': running}), 200 if running else 503
    except:
        return jsonify({'healthy': False}), 503
