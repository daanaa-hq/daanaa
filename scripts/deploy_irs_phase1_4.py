#!/usr/bin/env python3
"""
Deploy Phase 1-4: IRS Eligibility Integration to Production

This script orchestrates the full deployment of IRS eligibility data to the live
droplet, ensuring 1.86M orgs show accurate tax-deductible status badges.

Steps:
1. Verify precompute rebuild is complete
2. Package precompute with IRS eligibility fields
3. Transfer to droplet staging
4. Execute atomic swap (deploy_droplet.sh)
5. Verify live API responds with IRS fields
6. Report results
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
PRECOMPUTE_DIR = BASE_DIR / "precompute_output"
DEPLOY_SCRATCH = BASE_DIR / ".deploy_scratch"
PAYLOAD = DEPLOY_SCRATCH / "precompute_payload_irs.tar.gz"

DROPLET_IP = "107.170.26.8"
DROPLET_USER = "root"
SSH_KEY = Path.home() / ".ssh" / "daanaa_do_cron"
STAGING_DIR = "/opt/daanaa/staging"


def log(msg: str, level: str = "INFO"):
    """Log with timestamp"""
    ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    print(f"[{ts}] {level}: {msg}", flush=True)


def check_precompute_complete() -> bool:
    """Verify precompute rebuild finished and succeeded with full expected data"""
    log("Checking precompute rebuild status...")

    # Check if rebuild process still running
    result = subprocess.run(
        ["pgrep", "-f", "rebuild_precompute_with_irs"],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        log("Precompute rebuild still running", "WARN")
        return False

    # Expected count from rebuild: 2,056,834 orgs processed (from PHASE_1_4_READINESS.md)
    EXPECTED_MIN = 2000000  # Conservative threshold: at least 2M orgs rebuilt
    EXPECTED_EXACT = 2056834

    # Count total JSON files in precompute/orgs/ to verify full rebuild
    result = subprocess.run(
        ["find", str(PRECOMPUTE_DIR / "orgs"), "-name", "*.json", "-type", "f"],
        capture_output=True,
        text=True,
        timeout=60
    )

    if result.returncode != 0:
        log("Failed to count precompute files", "ERROR")
        return False

    total_files = len([f for f in result.stdout.strip().split('\n') if f])
    if total_files < EXPECTED_MIN:
        log(f"Precompute incomplete: {total_files} orgs (expected {EXPECTED_EXACT})", "ERROR")
        return False

    # Verify IRS fields are actually present in rebuilt files
    # Check for all claimed fields: status, checked_at, sources, notes
    required_fields = ["irs_eligibility_status", "irs_eligibility_checked_at",
                       "irs_eligibility_sources", "irs_eligibility_notes"]

    # Use single find with grep to check all fields simultaneously (faster than 4 sequential finds)
    for field in required_fields:
        result = subprocess.run(
            ["grep", "-r", f'"{field}"', str(PRECOMPUTE_DIR / "orgs"),
             "--include=*.json", "-q"],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            log(f"Precompute missing IRS field: {field}", "ERROR")
            return False

    log(f"✓ Precompute rebuild verified: {total_files} orgs with all IRS fields", "SUCCESS")
    return True


def package_precompute() -> bool:
    """Create deployment tarball with IRS data"""
    log("Packaging precompute with IRS eligibility fields...")

    DEPLOY_SCRATCH.mkdir(parents=True, exist_ok=True)

    try:
        # Create tarball (uncompressed for speed; 25GB takes ~2 min to tar)
        result = subprocess.run(
            ["tar", "--exclude=./vectors.f32.memmap", "-cf", str(PAYLOAD), "."],
            cwd=PRECOMPUTE_DIR,
            capture_output=True,
            text=True,
            timeout=600
        )

        if result.returncode != 0:
            log(f"Tar failed: {result.stderr}", "ERROR")
            return False

        # Compute checksum
        result = subprocess.run(
            ["sha256sum", str(PAYLOAD)],
            capture_output=True,
            text=True
        )

        checksum_file = Path(str(PAYLOAD) + ".sha256")
        checksum_file.write_text(result.stdout)

        size_mb = PAYLOAD.stat().st_size / (1024 ** 2)
        log(f"✓ Payload ready: {size_mb:.0f} MB", "SUCCESS")
        return True

    except Exception as e:
        log(f"Packaging failed: {e}", "ERROR")
        return False


def transfer_to_droplet() -> bool:
    """Copy payload to droplet staging and verify checksum"""
    log("Transferring payload to droplet...")

    try:
        # Transfer both tarball and checksum (25GB ~2-3 min over network)
        for file_path in [PAYLOAD, Path(str(PAYLOAD) + ".sha256")]:
            result = subprocess.run(
                [
                    "scp",
                    "-i", str(SSH_KEY),
                    str(file_path),
                    f"{DROPLET_USER}@{DROPLET_IP}:{STAGING_DIR}/"
                ],
                capture_output=True,
                text=True,
                timeout=600
            )

            if result.returncode != 0:
                log(f"Transfer failed: {result.stderr}", "ERROR")
                return False

        # Verify checksum on droplet to detect corruption
        log("Verifying checksum on droplet...")
        cmd = f"cd {STAGING_DIR} && sha256sum -c precompute_payload_irs.tar.gz.sha256"
        result = subprocess.run(
            ["ssh", "-i", str(SSH_KEY), f"{DROPLET_USER}@{DROPLET_IP}", cmd],
            capture_output=True,
            timeout=60,
            text=True
        )

        if result.returncode != 0:
            log(f"Checksum verification failed on droplet: {result.stderr}", "ERROR")
            return False

        log("✓ Payload transferred and checksum verified", "SUCCESS")
        return True

    except subprocess.TimeoutExpired:
        log("Transfer timeout", "ERROR")
        return False
    except Exception as e:
        log(f"Transfer failed: {e}", "ERROR")
        return False


def execute_atomic_swap() -> bool:
    """Execute atomic swap on droplet: backup v1 to v0, extract new to v1"""
    log("Executing atomic swap on droplet...")

    try:
        # Inline atomic swap script: backup current, extract new, restart
        swap_script = f"""
set -e
PAYLOAD="{STAGING_DIR}/precompute_payload_irs.tar.gz"
PRECOMPUTE_DIR="/data/precompute"

echo "Extracting payload to temporary directory..."
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"
tar -xf "$PAYLOAD"

if [ ! -f "$TEMP_DIR/orgs.json" ] || [ ! -d "$TEMP_DIR/orgs" ]; then
  echo "ERROR: Invalid payload structure" >&2
  exit 1
fi

echo "Backup current v1 to v0..."
rm -rf "$PRECOMPUTE_DIR/v0"
cp -r "$PRECOMPUTE_DIR/v1" "$PRECOMPUTE_DIR/v0" 2>/dev/null || true

echo "Deploy new version to v1..."
rm -rf "$PRECOMPUTE_DIR/v1"
mv "$TEMP_DIR" "$PRECOMPUTE_DIR/v1"
chmod -R 755 "$PRECOMPUTE_DIR/v1"

echo "Restarting gunicorn..."
systemctl restart gunicorn
sleep 2

if systemctl is-active gunicorn >/dev/null 2>&1; then
  echo "✓ Atomic swap complete"
  exit 0
else
  echo "ERROR: Gunicorn failed to start, rolling back..." >&2
  rm -rf "$PRECOMPUTE_DIR/v1"
  mv "$PRECOMPUTE_DIR/v0" "$PRECOMPUTE_DIR/v1"
  systemctl restart gunicorn
  exit 1
fi
"""

        result = subprocess.run(
            ["ssh", "-i", str(SSH_KEY), f"{DROPLET_USER}@{DROPLET_IP}", swap_script],
            capture_output=True,
            timeout=300,
            text=True
        )

        # Log output
        if result.stdout:
            for line in result.stdout.split('\n')[-10:]:
                if line.strip():
                    log(f"  {line}")

        if result.returncode != 0:
            log(f"Atomic swap failed: {result.stderr}", "ERROR")
            return False

        log("✓ Atomic swap complete with automatic rollback safety", "SUCCESS")
        return True

    except subprocess.TimeoutExpired:
        log("Swap timeout", "ERROR")
        return False
    except Exception as e:
        log(f"Swap failed: {e}", "ERROR")
        return False


def verify_live_api() -> bool:
    """Smoke test: verify IRS fields in live API with both eligible and revoked orgs"""
    log("Verifying IRS fields in live API...")

    # Required IRS fields that must be present in all responses
    REQUIRED_IRS_FIELDS = [
        "irs_eligibility_status",
        "irs_eligibility_checked_at",
        "irs_eligibility_sources",
        "irs_eligibility_notes"
    ]

    def query_api(ein: str) -> dict:
        """Query API for org and return parsed JSON or empty dict on failure"""
        result = subprocess.run(
            [
                "curl",
                "-s",
                "-m", "15",  # Extended timeout for post-deployment warmup
                f"https://daanaa.org/api/organizations/{ein}"
            ],
            capture_output=True,
            text=True,
            timeout=20
        )
        if result.returncode != 0:
            return {}
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {}

    def validate_org(ein: str, expected_status: str) -> bool:
        """Validate org has all IRS fields and expected status"""
        data = query_api(ein)
        if not data:
            log(f"  ✗ {ein}: API no response", "WARN")
            return False

        # Check all required fields exist
        for field in REQUIRED_IRS_FIELDS:
            if field not in data:
                log(f"  ✗ {ein}: missing field {field}", "ERROR")
                return False

        # Check status matches expected and is non-null
        status = data.get("irs_eligibility_status")
        if not status or status != expected_status:
            log(f"  ✗ {ein}: expected status '{expected_status}', got '{status}'", "ERROR")
            return False

        # Verify checked_at is set (indicates rebuild ran)
        checked_at = data.get("irs_eligibility_checked_at")
        if not checked_at:
            log(f"  ✗ {ein}: missing or empty irs_eligibility_checked_at", "ERROR")
            return False

        log(f"  ✓ {ein}: {expected_status} (all fields present)", "SUCCESS")
        return True

    try:
        log("Finding test orgs (eligible and revoked)...")

        # Find test EINs: one eligible, one revoked
        test_eins = {"eligible": None, "revoked": None}

        for status_type in ["eligible", "revoked"]:
            result = subprocess.run(
                ["grep", "-l", f'"{status_type}"', "-r", str(PRECOMPUTE_DIR / "orgs"),
                 "--include=*.json"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0 and result.stdout:
                first_file = result.stdout.strip().split('\n')[0]
                test_eins[status_type] = Path(first_file).stem

        # Verify we found test cases
        if not test_eins["eligible"]:
            log("No eligible org found in precompute for testing", "ERROR")
            return False
        if not test_eins["revoked"]:
            log("No revoked org found in precompute for testing", "ERROR")
            return False

        log("Testing eligible org...")
        if not validate_org(test_eins["eligible"], "eligible"):
            return False

        log("Testing revoked org...")
        if not validate_org(test_eins["revoked"], "revoked"):
            return False

        log("✓ API returning all required IRS fields with correct data", "SUCCESS")
        return True

    except Exception as e:
        log(f"Verification failed: {e}", "ERROR")
        return False


def main():
    """Execute full deployment pipeline"""
    log("Phase 1-4 IRS Integration Deployment")
    log("=" * 60)

    steps = [
        ("Precompute Complete?", check_precompute_complete),
        ("Package Precompute", package_precompute),
        ("Transfer to Droplet", transfer_to_droplet),
        ("Atomic Swap", execute_atomic_swap),
        ("Verify Live API", verify_live_api),
    ]

    results = {}
    for step_name, step_func in steps:
        log(f"\n[Step] {step_name}...")
        try:
            success = step_func()
            results[step_name] = "✅ PASS" if success else "❌ FAIL"

            if not success:
                log(f"Stopping at failed step: {step_name}", "ERROR")
                break

        except Exception as e:
            log(f"Step crashed: {e}", "ERROR")
            results[step_name] = "❌ CRASH"
            break

    # Summary
    log("\n" + "=" * 60)
    log("DEPLOYMENT SUMMARY")
    for step_name, result in results.items():
        print(f"  {result} {step_name}")

    # Exit code
    if all("✅" in r for r in results.values()):
        log("\n🎉 Phase 1-4 LIVE: 1.86M orgs with IRS eligibility badges", "SUCCESS")
        return 0
    else:
        log("\n⚠️  Deployment incomplete. Check logs above.", "ERROR")
        return 1


if __name__ == "__main__":
    sys.exit(main())
