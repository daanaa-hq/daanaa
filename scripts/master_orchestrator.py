#!/usr/bin/env python3
"""
Master Orchestrator v1: Unified pipeline coordinator for Daanaa
Replaces 30+ scattered cron jobs with a single, dependency-aware orchestration layer.

Phases:
  1. IRS Ingest — pull new filings from IRS
  2. Scoring — recompute financial health scores
  3. Enrichment — ProPublica data, website discovery, donation links
  4. Embeddings — rebuild search vectors
  5. Sync — push updates to droplet
  6. Reporting — generate morning brief, snapshots

Run via: 0 2 * * * master_orchestrator.py --mode full
Or individually: master_orchestrator.py --phase irs_ingest
"""

import sys
import sqlite3
import subprocess
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional, List
import argparse
import json

# Setup
HOME = Path.home()
PROJECT = HOME / 'meritgiving'
VENV = PROJECT / 'venv' / 'bin' / 'python3'
DB = PROJECT / 'data' / 'merit_registry.db'
LOGS = PROJECT / 'logs'
LOGS.mkdir(exist_ok=True)

LOG_FILE = LOGS / f'master_orchestrator_{datetime.now().strftime("%Y%m%d")}.log'
logger = logging.getLogger('orchestrator')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler(LOG_FILE)
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)


@dataclass
class Phase:
    """Pipeline phase definition."""
    name: str
    script: Path
    timeout_sec: int = 3600
    required: bool = True  # If False, failures don't block downstream
    skip_if_recent: Optional[int] = None  # Skip if run <N seconds ago
    env_vars: dict = None

    def __post_init__(self):
        if self.env_vars is None:
            self.env_vars = {}


# Pipeline phases in execution order
PHASES = [
    Phase(
        name='irs_ingest',
        script=PROJECT / 'scripts' / 'auto_ingest.py',
        timeout_sec=1800,
        env_vars={'INGEST_BATCH': '100', 'REBALANCE_THRESHOLD': '10000'}
    ),
    Phase(
        name='scoring',
        script=PROJECT / 'scripts' / 'monthly_rescore_agent.py',
        timeout_sec=3600,
        required=False,  # Optional: may not run every day
    ),
    Phase(
        name='enrichment',
        script=PROJECT / 'scripts' / 'overnight_pipeline.py',
        timeout_sec=7200,
        required=False,
    ),
    Phase(
        name='embeddings',
        script=PROJECT / 'scripts' / 'build_embeddings.py',
        timeout_sec=7200,
        required=False,
        skip_if_recent=21600,  # Skip if run <6 hours ago (GPU intensive)
    ),
    Phase(
        name='sync_droplet',
        script=PROJECT / 'scripts' / 'sync_db_to_droplet.sh',
        timeout_sec=600,
    ),
    Phase(
        name='reporting',
        script=PROJECT / 'scripts' / 'morning_briefing_agent.py',
        timeout_sec=300,
        required=False,
    ),
]


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(str(DB))
    conn.row_factory = sqlite3.Row
    return conn


def get_phase_state(phase_name: str) -> dict:
    """Get the last run state of a phase from database."""
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('''
            SELECT * FROM orchestrator_state
            WHERE phase_name = ? AND run_date = date('now')
            ORDER BY run_time DESC LIMIT 1
        ''', (phase_name,))
        row = c.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        conn.close()


def record_phase_state(phase_name: str, status: str, duration_sec: float, error: Optional[str] = None):
    """Record phase execution state."""
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO orchestrator_state
            (phase_name, run_date, run_time, status, duration_sec, error_msg)
            VALUES (?, date('now'), time('now'), ?, ?, ?)
        ''', (phase_name, status, duration_sec, error))
        conn.commit()
    except sqlite3.OperationalError:
        # Table doesn't exist yet, create it
        c.execute('''
            CREATE TABLE IF NOT EXISTS orchestrator_state (
                id INTEGER PRIMARY KEY,
                phase_name TEXT NOT NULL,
                run_date DATE NOT NULL,
                run_time TIME NOT NULL,
                status TEXT NOT NULL,
                duration_sec REAL NOT NULL,
                error_msg TEXT
            )
        ''')
        c.execute('''
            INSERT INTO orchestrator_state
            (phase_name, run_date, run_time, status, duration_sec, error_msg)
            VALUES (?, date('now'), time('now'), ?, ?, ?)
        ''', (phase_name, status, duration_sec, error))
        conn.commit()
    finally:
        conn.close()


def run_phase(phase: Phase) -> tuple[bool, float, Optional[str]]:
    """
    Execute a single phase.
    Returns: (success: bool, duration: float, error_msg: Optional[str])
    """
    logger.info(f'Starting phase: {phase.name}')
    start = time.time()

    # Check skip condition
    if phase.skip_if_recent:
        state = get_phase_state(phase.name)
        if state and state['status'] == 'success':
            last_run = datetime.fromisoformat(f"{state['run_date']} {state['run_time']}")
            elapsed = (datetime.now() - last_run).total_seconds()
            if elapsed < phase.skip_if_recent:
                logger.info(f'Skipping {phase.name} (last run {int(elapsed/60)}m ago)')
                return True, 0, None

    # Build command
    if phase.script.name.endswith('.py'):
        cmd = [str(VENV), str(phase.script)]
    else:
        cmd = ['bash', str(phase.script)]

    # Run with timeout
    try:
        env = {**subprocess.os.environ}
        env.update(phase.env_vars)
        result = subprocess.run(
            cmd,
            timeout=phase.timeout_sec,
            capture_output=True,
            text=True,
            env=env,
            cwd=str(PROJECT),
        )
        duration = time.time() - start

        if result.returncode == 0:
            logger.info(f'{phase.name} completed in {duration:.1f}s')
            record_phase_state(phase.name, 'success', duration)
            return True, duration, None
        else:
            error_msg = f"Exit code {result.returncode}: {result.stderr[-500:]}"
            logger.error(f'{phase.name} FAILED: {error_msg}')
            record_phase_state(phase.name, 'failed', duration, error_msg)
            return False, duration, error_msg

    except subprocess.TimeoutExpired:
        duration = time.time() - start
        error_msg = f"Timeout after {duration:.1f}s"
        logger.error(f'{phase.name} TIMEOUT: {error_msg}')
        record_phase_state(phase.name, 'timeout', duration, error_msg)
        return False, duration, error_msg

    except Exception as e:
        duration = time.time() - start
        error_msg = str(e)
        logger.error(f'{phase.name} ERROR: {error_msg}')
        record_phase_state(phase.name, 'error', duration, error_msg)
        return False, duration, error_msg


def run_full_pipeline() -> bool:
    """
    Execute the full pipeline in sequence.
    Returns: True if all required phases succeeded, False otherwise.
    """
    logger.info('=' * 70)
    logger.info('MASTER ORCHESTRATOR: Full Pipeline Start')
    logger.info('=' * 70)

    all_success = True
    phase_results = []

    for phase in PHASES:
        success, duration, error = run_phase(phase)
        phase_results.append({
            'phase': phase.name,
            'success': success,
            'duration_sec': duration,
            'error': error,
        })

        if not success:
            if phase.required:
                logger.error(f'BLOCKING: {phase.name} failed (required phase)')
                all_success = False
                break
            else:
                logger.warning(f'OPTIONAL: {phase.name} failed (non-blocking)')

    # Summary
    logger.info('=' * 70)
    logger.info('SUMMARY:')
    for r in phase_results:
        status_str = '✅' if r['success'] else '❌'
        logger.info(f"  {status_str} {r['phase']:<20} {r['duration_sec']:6.1f}s {r['error'] or ''}")
    logger.info('=' * 70)
    logger.info(f'Pipeline: {"SUCCESS" if all_success else "FAILED"}')
    logger.info('=' * 70)

    return all_success


def run_phase_only(phase_name: str) -> bool:
    """Run a single phase by name."""
    phase = next((p for p in PHASES if p.name == phase_name), None)
    if not phase:
        logger.error(f'Unknown phase: {phase_name}')
        return False

    logger.info(f'Running single phase: {phase_name}')
    success, duration, error = run_phase(phase)
    return success


def status_report() -> dict:
    """Generate a status report of all phases."""
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('''
            SELECT phase_name, MAX(run_time) as last_run, status, duration_sec
            FROM orchestrator_state
            WHERE run_date = date('now')
            GROUP BY phase_name
            ORDER BY run_time DESC
        ''')
        rows = c.fetchall()
        return {row['phase_name']: dict(row) for row in rows}
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description='Master Orchestrator for Daanaa Pipeline')
    parser.add_argument('--mode', choices=['full', 'dry-run', 'status'], default='full',
                        help='Execution mode')
    parser.add_argument('--phase', help='Run single phase by name')
    args = parser.parse_args()

    if args.phase:
        success = run_phase_only(args.phase)
        sys.exit(0 if success else 1)

    if args.mode == 'status':
        report = status_report()
        print(json.dumps(report, indent=2, default=str))
        return

    if args.mode == 'dry-run':
        logger.info('DRY RUN: Would execute the following phases:')
        for phase in PHASES:
            logger.info(f'  - {phase.name} (timeout: {phase.timeout_sec}s, required: {phase.required})')
        return

    # Full pipeline
    success = run_full_pipeline()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
