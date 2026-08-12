#!/usr/bin/env python3
"""
Deploy Phase 1-4: IRS Eligibility Integration to Production

This script orchestrates the full deployment of IRS eligibility data to the live
droplet, ensuring 1.86M orgs show accurate tax-deductible status badges.

Steps:
1. Verify precompute rebuild is complete (sharded orgs/<ein[:3]>/<ein>.json.gz tree)
2. Package precompute with IRS eligibility fields
3. Transfer to droplet staging (rsync)
4. Execute atomic swap (inline SSH script: extract, mv-swap v1<->v0, restart daanaa-api)
5. Verify live API responds with IRS fields (eligible + revoked)
6. Report results
"""

import gzip
import json
import random
import sqlite3
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

    # Check if rebuild process still running. Pattern requires the .py suffix
    # so this doesn't self-match shells/monitors that merely mention the
    # script name in their own command text (e.g. `while pgrep -f
    # rebuild_precompute_with_irs; do ...`) without invoking it directly —
    # hit this exact false positive during tonight's deploy.
    result = subprocess.run(
        ["pgrep", "-f", r"rebuild_precompute_with_irs\.py"],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        log("Precompute rebuild still running", "WARN")
        return False
    if result.returncode != 1:
        log(f"Failed to check precompute rebuild status (rc={result.returncode}): {result.stderr.strip() or 'no stderr'}", "ERROR")
        return False


    # The live API reads sharded orgs/<ein[:3]>/<ein>.json.gz files (see
    # LESSONS.md 2026-08-12) — verify against that tree, not the flat
    # orgs/<ein>.json files (which nothing in production reads).
    # Coverage is ~99% for eligible orgs, ~40% for revoked (orgs without an
    # existing sharded file are skipped by the rebuild and fall back to
    # search.db — a separate known gap). Threshold reflects that, not 2.06M.
    EXPECTED_SHARDED_MIN = 1_900_000

    result = subprocess.run(
        ["find", str(PRECOMPUTE_DIR / "orgs"), "-mindepth", "2", "-name", "*.json.gz", "-type", "f"],
        capture_output=True,
        text=True,
        timeout=120
    )

    if result.returncode != 0:
        log("Failed to count sharded precompute files", "ERROR")
        return False

    total_files = len([f for f in result.stdout.strip().split('\n') if f])
    if total_files < EXPECTED_SHARDED_MIN:
        log(f"Sharded precompute tree too small: {total_files} files (expected >= {EXPECTED_SHARDED_MIN:,})", "ERROR")
        return False

    # Verify IRS fields actually landed in the sharded (gzip) files. An
    # exhaustive zgrep/find across ~1.9M small gzip files is too slow for any
    # reasonable timeout (measured: still running past 180s). This only needs
    # to be a confidence check — the rebuild script's own stdout already
    # reported an exact updated count — so sample N random files directly via
    # Python's gzip module instead of shelling out to search the whole tree.
    all_files = [f for f in result.stdout.strip().split('\n') if f]
    sample_size = min(2000, len(all_files))
    sample = random.sample(all_files, sample_size)

    hits = 0
    read_errors = 0
    for path in sample:
        try:
            with gzip.open(path, 'rt', encoding='utf-8') as f:
                data = json.load(f)
            if data.get('irs_eligibility_status') is not None:
                hits += 1
        except Exception:
            read_errors += 1

    hit_rate = hits / sample_size if sample_size else 0
    if read_errors > sample_size * 0.05:
        log(f"Too many unreadable sharded files in sample: {read_errors}/{sample_size}", "ERROR")
        return False
    if hit_rate < 0.90:
        log(f"Sharded files missing IRS fields: only {hits}/{sample_size} sampled files ({hit_rate:.0%}) contain irs_eligibility_status", "ERROR")
        return False

    log(f"✓ Precompute rebuild verified: {hits}/{sample_size} sampled sharded files have IRS fields ({hit_rate:.0%}), {total_files:,} total files", "SUCCESS")
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

        # Compute checksum (with just filename, not full path, so it works on droplet)
        result = subprocess.run(
            ["sha256sum", PAYLOAD.name],
            cwd=DEPLOY_SCRATCH,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            log(f"Checksum generation failed: {result.stderr}", "ERROR")
            return False

        checksum_file = Path(str(PAYLOAD) + ".sha256")
        checksum_file.write_text(result.stdout)

        size_mb = PAYLOAD.stat().st_size / (1024 ** 2)
        log(f"✓ Payload ready: {size_mb:.0f} MB", "SUCCESS")
        return True

    except Exception as e:
        log(f"Packaging failed: {e}", "ERROR")
        return False


def transfer_to_droplet() -> bool:
    """Copy payload to droplet staging using rsync (14GB ~30-40 min, resumable)"""
    log("Transferring payload to droplet (14GB ~30-40 min, resumable via rsync)...")

    try:
        # Use rsync for resumable transfer (14GB ~30-40 min over network)
        log("Using rsync for resumable transfer...")
        result = subprocess.run(
            [
                "rsync",
                "-avz",
                "-e", f"ssh -i {SSH_KEY}",
                str(PAYLOAD),
                f"{DROPLET_USER}@{DROPLET_IP}:{STAGING_DIR}/"
            ],
            capture_output=True,
            text=True,
            timeout=3000  # 50 minutes
        )

        if result.returncode != 0:
            log(f"Tarball transfer failed: {result.stderr}", "ERROR")
            return False

        # Transfer checksum file
        checksum_file = Path(str(PAYLOAD) + ".sha256")
        result = subprocess.run(
            [
                "rsync",
                "-v",
                "-e", f"ssh -i {SSH_KEY}",
                str(checksum_file),
                f"{DROPLET_USER}@{DROPLET_IP}:{STAGING_DIR}/"
            ],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            log(f"Checksum transfer failed: {result.stderr}", "ERROR")
            return False

        # Verify checksum on droplet to detect corruption (can take 2-3 min for 14GB)
        log("Verifying checksum on droplet...")
        cmd = f"cd {STAGING_DIR} && sha256sum -c precompute_payload_irs.tar.gz.sha256"
        result = subprocess.run(
            ["ssh", "-i", str(SSH_KEY), f"{DROPLET_USER}@{DROPLET_IP}", cmd],
            capture_output=True,
            timeout=300,
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
        # Inline atomic swap script: extract to fresh dir, then rename-swap (no data
        # duplication — mv is instant and free on the same filesystem, unlike cp -r
        # which doubled disk usage and contributed to the earlier disk-full failure).
        # Service name is daanaa-api (verified via systemctl list-units), not "gunicorn".
        swap_script = f"""
set -e
PAYLOAD="{STAGING_DIR}/precompute_payload_irs.tar.gz"
PRECOMPUTE_DIR="/data/precompute"
SERVICE="daanaa-api"

echo "Extracting payload to temporary directory..."
TEMP_DIR=$(mktemp -d -p "$PRECOMPUTE_DIR")
cd "$TEMP_DIR"
tar -xf "$PAYLOAD"

# Validate structure: must have orgs/ directory with org JSON files
if [ ! -d "$TEMP_DIR/orgs" ] || [ ! -f "$(find "$TEMP_DIR/orgs" -name "*.json" -type f | head -1)" ]; then
  echo "ERROR: Invalid payload structure (missing orgs/)" >&2
  rm -rf "$TEMP_DIR"
  exit 1
fi

# Free the tar payload now that extraction succeeded (14GB reclaimed before swap)
rm -f "$PAYLOAD" "$PAYLOAD.sha256"

echo "Swapping v1 -> v0 (rename, no duplication) and staging new version into v1..."
rm -rf "$PRECOMPUTE_DIR/v0"
mv "$PRECOMPUTE_DIR/v1" "$PRECOMPUTE_DIR/v0"
mv "$TEMP_DIR" "$PRECOMPUTE_DIR/v1"
chmod -R 755 "$PRECOMPUTE_DIR/v1"

echo "Restarting $SERVICE..."
systemctl restart "$SERVICE"
sleep 3

if systemctl is-active "$SERVICE" >/dev/null 2>&1; then
  echo "✓ Atomic swap complete"
  exit 0
else
  echo "ERROR: $SERVICE failed to start, rolling back..." >&2
  rm -rf "$PRECOMPUTE_DIR/v1"
  mv "$PRECOMPUTE_DIR/v0" "$PRECOMPUTE_DIR/v1"
  systemctl restart "$SERVICE"
  exit 1
fi
"""

        result = subprocess.run(
            ["ssh", "-i", str(SSH_KEY), f"{DROPLET_USER}@{DROPLET_IP}", swap_script],
            capture_output=True,
            timeout=900,  # 15 min for tar extraction + validation + restart
            text=True
        )

        if result.returncode != 0:
            log(f"Atomic swap failed: {result.stderr}", "ERROR")
            if result.stdout:
                for line in result.stdout.split('\n')[-10:]:
                    if line.strip():
                        log(f"  {line}")
            return False

        # Log output only after the command has succeeded.
        if result.stdout:
            for line in result.stdout.split('\n')[-10:]:
                if line.strip():
                    log(f"  {line}")

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
            log(f"  ✗ {ein}: curl failed (rc={result.returncode})", "WARN")
            return {}
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            log(f"  ✗ {ein}: invalid JSON response from API", "WARN")
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

        # Query the DB directly rather than grepping the precompute tree: the
        # live API reads sharded orgs/<ein[:3]>/<ein>.json.gz files (gzip-
        # compressed, so a text grep can't match their contents anyway), and
        # not every EIN with an IRS status has one (see rebuild_precompute_
        # with_irs.py's skipped_no_file count — coverage is ~99% for eligible,
        # ~40% for revoked). We need an EIN that both has the status AND has
        # a sharded file, or the smoke test targets data that was never
        # rebuilt and fails for the wrong reason.
        DB_PATH = BASE_DIR / "data" / "merit_registry.db"
        test_eins = {"eligible": None, "revoked": None}

        db = sqlite3.connect(str(DB_PATH))
        db.row_factory = sqlite3.Row
        for status_type in ["eligible", "revoked"]:
            cur = db.execute(
                "SELECT EIN FROM registry_enriched WHERE irs_eligibility_status = ? ORDER BY EIN",
                (status_type,)
            )
            for row in cur:
                ein = row["EIN"]
                if (PRECOMPUTE_DIR / "orgs" / ein[:3] / f"{ein}.json.gz").exists():
                    test_eins[status_type] = ein
                    break
        db.close()

        # Verify we found test cases
        if not test_eins["eligible"]:
            log("No eligible org with a sharded precompute file found for testing", "ERROR")
            return False
        if not test_eins["revoked"]:
            log("No revoked org with a sharded precompute file found for testing", "ERROR")
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
