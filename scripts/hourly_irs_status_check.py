#!/usr/bin/env python3
"""
Hourly IRS status check — delegates to sync_irs_revocations --check.

Kept at hourly cadence for cron hygiene; the --check path is fast (no download,
just a count query) so the overhead is negligible.
"""
import subprocess
import sys
from pathlib import Path

script = Path(__file__).parent / 'sync_irs_revocations.py'
result = subprocess.run([sys.executable, str(script), '--check'], timeout=30)
sys.exit(result.returncode)
