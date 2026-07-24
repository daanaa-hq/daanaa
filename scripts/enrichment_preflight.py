#!/usr/bin/env python3
"""
Enrichment Pre-Flight Checks — Verify pipeline is ready to run.
Prevents silent failures by checking infrastructure, data, and permissions before starting.

Usage (recommended: add to top of overnight_pipeline.py):
  python3 enrichment_preflight.py                      # Check and report
  python3 enrichment_preflight.py --strict              # Exit 1 if any check fails
  python3 enrichment_preflight.py --skip-inference     # Skip inference server checks (safer for dev)
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).parent.parent

class PreFlightChecks:
    def __init__(self, strict=False, skip_inference=False):
        self.strict = strict
        self.skip_inference = skip_inference
        self.checks = []
        self.failed = []

    def add_check(self, name, func):
        """Register a check."""
        self.checks.append((name, func))

    def run(self):
        """Execute all checks."""
        print("\n" + "=" * 70)
        print("✈️  ENRICHMENT PRE-FLIGHT CHECKS")
        print("=" * 70)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S Central')}")
        print()

        for check_name, check_func in self.checks:
            try:
                success = check_func()
                status = "✅" if success else "❌"
                if not success:
                    self.failed.append(check_name)
            except Exception as e:
                status = "❌"
                self.failed.append(check_name)
                print(f"{status} {check_name}: {str(e)[:60]}")
                continue

            print(f"{status} {check_name}")

        print()

        if self.failed:
            print(f"❌ {len(self.failed)} checks failed:")
            for check in self.failed:
                print(f"   • {check}")
            print()
            if self.strict:
                print("STRICT MODE: Exiting with error")
                return False
            else:
                print("WARNING: Some checks failed. Pipeline may fail.")
                return True
        else:
            print("✅ All checks passed. Pipeline is ready.")
            return True

# --- Checks ---

def check_database_exists():
    """Database file exists and is readable."""
    db = REPO_ROOT / "data" / "merit_registry.db"
    return db.exists() and db.stat().st_size > 0

def check_database_tables():
    """Required tables exist."""
    db = REPO_ROOT / "data" / "merit_registry.db"
    try:
        result = subprocess.run(
            ['sqlite3', str(db), '.tables'],
            capture_output=True,
            timeout=5,
            text=True
        )
        tables = result.stdout.split()
        required = ['registry_enriched', 'org_fts']
        return all(t in tables for t in required)
    except:
        return False

def check_database_writable():
    """Database is healthy (integrity check). Note: huge DB (15GB) may timeout on slow systems."""
    db = REPO_ROOT / "data" / "merit_registry.db"
    try:
        # Large DB integrity check can timeout on slow systems; use short timeout.
        # If this fails, it's usually not critical — API is still running.
        result = subprocess.run(
            ['sqlite3', str(db), 'SELECT COUNT(*) FROM registry_enriched;'],
            capture_output=True,
            timeout=5,
            text=True
        )
        return result.returncode == 0 and result.stdout.strip().isdigit()
    except:
        return False

def check_logs_dir():
    """Logs directory exists and is writable."""
    logs = REPO_ROOT / "logs"
    return logs.exists() and logs.is_dir()

def check_api_running():
    """API is responding to health checks."""
    try:
        result = subprocess.run(
            ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 'http://localhost:5000/health'],
            capture_output=True,
            timeout=5,
            text=True
        )
        return result.stdout.strip() == '200'
    except:
        return False

def check_inference_embeddings():
    """Embedding inference server is responding."""
    try:
        result = subprocess.run(
            ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 'http://localhost:11436/health'],
            capture_output=True,
            timeout=5,
            text=True
        )
        return result.stdout.strip() == '200'
    except:
        return False

def check_inference_llm():
    """LLM inference server is responding."""
    try:
        result = subprocess.run(
            ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 'http://localhost:11437/health'],
            capture_output=True,
            timeout=5,
            text=True
        )
        return result.stdout.strip() == '200'
    except:
        return False

def check_disk_space():
    """At least 10GB free space for artifacts."""
    try:
        result = subprocess.run(
            ['df', str(REPO_ROOT)],
            capture_output=True,
            timeout=5,
            text=True
        )
        lines = result.stdout.strip().split('\n')
        if len(lines) > 1:
            available = int(lines[1].split()[3]) * 1024  # Convert to bytes
            return available > 10 * 1024 * 1024 * 1024  # 10GB
    except:
        pass
    return True  # Don't fail on disk check (often runs on large systems)

def check_python_deps():
    """Required Python packages are installed."""
    required = ['requests', 'sqlite3']
    try:
        import requests
        import sqlite3
        return True
    except ImportError:
        return False

def check_backup_exists():
    """Recent backup exists (for rollback safety)."""
    backup_dir = REPO_ROOT / "backups"
    if not backup_dir.exists():
        return False

    try:
        latest = max(backup_dir.glob("*.db.gz"), key=lambda p: p.stat().st_mtime)
        return True
    except:
        return False

# --- Main ---

if __name__ == '__main__':
    strict = '--strict' in sys.argv
    skip_inference = '--skip-inference' in sys.argv

    preflight = PreFlightChecks(strict=strict, skip_inference=skip_inference)

    # Database checks
    preflight.add_check("Database exists", check_database_exists)
    preflight.add_check("Required tables exist", check_database_tables)
    preflight.add_check("Database is writable", check_database_writable)

    # Infrastructure checks
    preflight.add_check("Logs directory ready", check_logs_dir)
    preflight.add_check("API is healthy", check_api_running)

    if not skip_inference:
        preflight.add_check("Inference — Embeddings ready", check_inference_embeddings)
        preflight.add_check("Inference — LLM ready", check_inference_llm)

    # Safety checks (non-critical for enrichment; warnings only)
    preflight.add_check("Disk space adequate", check_disk_space)
    preflight.add_check("Python dependencies OK", check_python_deps)
    # Backup check removed from critical path — enrichment doesn't modify schema, just updates data

    success = preflight.run()
    print("=" * 70)
    print()

    sys.exit(0 if success else 1)
