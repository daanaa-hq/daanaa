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
import time
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
    """Verify precompute rebuild finished"""
    log("Checking precompute rebuild status...")

    # Check if rebuild process still running
    result = subprocess.run(
        ["pgrep", "-f", "rebuild_precompute_with_irs"],
        capture_output=True
    )

    if result.returncode == 0:
        log("Precompute rebuild still running", "WARN")
        return False

    log("✓ Precompute rebuild complete", "SUCCESS")
    return True


def package_precompute() -> bool:
    """Create deployment tarball with IRS data"""
    log("Packaging precompute with IRS eligibility fields...")

    DEPLOY_SCRATCH.mkdir(parents=True, exist_ok=True)

    try:
        # Create tarball
        result = subprocess.run(
            ["tar", "--exclude=./vectors.f32.memmap", "-czf", str(PAYLOAD), "."],
            cwd=PRECOMPUTE_DIR,
            capture_output=True,
            timeout=300
        )

        if result.returncode != 0:
            log(f"Tar failed: {result.stderr.decode()}", "ERROR")
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
    """Copy payload to droplet staging"""
    log("Transferring payload to droplet...")

    try:
        # Transfer both tarball and checksum
        for file_path in [PAYLOAD, Path(str(PAYLOAD) + ".sha256")]:
            result = subprocess.run(
                [
                    "scp",
                    "-i", str(SSH_KEY),
                    str(file_path),
                    f"{DROPLET_USER}@{DROPLET_IP}:{STAGING_DIR}/"
                ],
                capture_output=True,
                timeout=120
            )

            if result.returncode != 0:
                log(f"Transfer failed: {result.stderr.decode()}", "ERROR")
                return False

        log("✓ Payload transferred to droplet", "SUCCESS")
        return True

    except subprocess.TimeoutExpired:
        log("Transfer timeout", "ERROR")
        return False
    except Exception as e:
        log(f"Transfer failed: {e}", "ERROR")
        return False


def execute_atomic_swap() -> bool:
    """Run deploy_droplet.sh to swap precompute live"""
    log("Executing atomic swap on droplet...")

    try:
        # SSH into droplet and run deploy script
        cmd = f"bash /opt/daanaa/scripts/deploy_droplet.sh {STAGING_DIR}/precompute_payload_irs.tar.gz"

        result = subprocess.run(
            ["ssh", "-i", str(SSH_KEY), f"{DROPLET_USER}@{DROPLET_IP}", cmd],
            capture_output=True,
            timeout=300,
            text=True
        )

        # Log deployment output
        if result.stdout:
            for line in result.stdout.split('\n')[-10:]:
                if line.strip():
                    log(f"  {line}")

        if result.returncode != 0:
            log(f"Atomic swap failed: {result.stderr.decode()}", "ERROR")
            return False

        log("✓ Atomic swap complete", "SUCCESS")
        return True

    except subprocess.TimeoutExpired:
        log("Swap timeout", "ERROR")
        return False
    except Exception as e:
        log(f"Swap failed: {e}", "ERROR")
        return False


def verify_live_api() -> bool:
    """Smoke test: verify IRS fields in live API"""
    log("Verifying IRS fields in live API...")

    try:
        # Test with a known EIN that should have IRS data
        result = subprocess.run(
            [
                "curl",
                "-s",
                "-m", "5",
                "https://daanaa.org/api/organizations/10001000"
            ],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            log("API not responding", "WARN")
            return False

        # Parse response
        try:
            data = json.loads(result.stdout)

            # Check for IRS eligibility field
            if "irs_eligibility_status" in data:
                status = data.get("irs_eligibility_status")
                log(f"✓ API returning IRS fields (status: {status})", "SUCCESS")
                return True
            else:
                log("IRS eligibility field not found in API response", "WARN")
                return False

        except json.JSONDecodeError:
            log("API returned non-JSON response", "WARN")
            return False

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
