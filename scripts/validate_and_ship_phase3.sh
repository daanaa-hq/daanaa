#!/usr/bin/env bash
set -euo pipefail

cd /home/akbar/meritgiving

STAGING_URL="${STAGING_URL:-https://staging.daanaa.org}"
ARTIFACT_DIR=".deploy_scratch/precompute/orgs"

echo "=== Waiting for the real precompute builder ==="

if ! pgrep -af '[p]recompute_orgs.py' >/dev/null; then
  echo "ERROR: No precompute_orgs.py process is running."
  echo "Do not deploy until the clean rebuild has actually run."
  exit 1
fi

while pgrep -af '[p]recompute_orgs.py' >/dev/null; do
  date
  pgrep -af '[p]recompute_orgs.py' || true
  sleep 60
done

echo "=== Validating nested artifacts ==="

python3 - "$ARTIFACT_DIR" <<'PY'
import gzip
import json
import os
import sys
from collections import Counter

root = sys.argv[1]
required = {
    "irs_eligibility_status",
    "irs_eligibility_checked_at",
    "irs_eligibility_sources",
    "irs_eligibility_explanation",
}
counts = Counter()
total = errors = 0

for base, _, files in os.walk(root):
    for name in files:
        if not name.endswith(".json.gz"):
            continue

        total += 1
        path = os.path.join(base, name)

        try:
            with gzip.open(path, "rt", encoding="utf-8") as f:
                data = json.load(f)

            if any(data.get(field) is None for field in required):
                counts["missing"] += 1
            else:
                counts[data["irs_eligibility_status"]] += 1

        except Exception as exc:
            errors += 1
            print(f"ERROR: {path}: {exc}", file=sys.stderr)

print({
    "files": total,
    "verified": counts["verified"],
    "unverified": counts["unverified"],
    "revoked": counts["revoked"],
    "unknown": counts["unknown"],
    "exception_possible": counts["exception_possible"],
    "missing_fields": counts["missing"],
    "read_errors": errors,
})

assert total == 1_758_078
assert counts["missing"] == 0
assert errors == 0
assert counts["revoked"] == 0
assert counts["verified"] == 1_250_731
assert counts["unverified"] == 367_993

print("✓ Nested artifact validation passed")
PY

echo "=== Validating v6 scoring tiers ==="

REVOKED_ACTIVE=$(sqlite3 data/merit_registry.db "
SELECT COUNT(*)
FROM v6_peer_context_assignments a
JOIN registry_enriched r ON r.EIN = a.EIN
WHERE a.run_id = (
  SELECT run_id
  FROM v6_scoring_runs
  WHERE status = 'candidate'
  ORDER BY started_at DESC
  LIMIT 1
)
AND a.selected_tier IN (
  '1_direct',
  '2_regional_conditional',
  '3_broader_regional',
  '4_national'
)
AND r.irs_eligibility_status = 'revoked';
")

[ "$REVOKED_ACTIVE" -eq 0 ] || {
  echo "ERROR: $REVOKED_ACTIVE revoked organizations remain in active tiers."
  exit 1
}

echo "✓ v6 scoring-tier check passed"

echo "=== Shipping to staging only ==="

sha256sum .deploy_scratch/precompute_payload.tar.gz \
  > .deploy_scratch/precompute_payload.tar.gz.sha256

bash scripts/safe_deploy_droplet.sh --ship-only

echo "=== Staging smoke tests ==="

curl --fail --silent --show-error "$STAGING_URL/" -o /dev/null
curl --fail --silent --show-error "$STAGING_URL/directory" -o /dev/null
curl --fail --silent --show-error "$STAGING_URL/health" -o /dev/null

curl --fail --silent --show-error \
  "$STAGING_URL/api/organizations/010545734" \
  | python3 -c '
import json, sys
d = json.load(sys.stdin)
required = [
    "irs_eligibility_status",
    "irs_eligibility_checked_at",
    "irs_eligibility_sources",
    "irs_eligibility_explanation",
]
missing = [x for x in required if d.get(x) is None]
if missing:
    raise SystemExit(f"Missing IRS fields: {missing}")
print("✓ API IRS fields present")
'

echo
echo "STAGING DEPLOYED AND AUTOMATED CHECKS PASSED."
echo "Next: manual QA and Impeccable design audit."
echo "Production deployment remains blocked pending explicit approval."
