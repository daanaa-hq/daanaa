#!/usr/bin/env bash
# privacy_check.sh — enforce the machine-checkable invariants in PRIVACY-INVARIANTS.md.
# Exit non-zero on any violation. Wire as a pre-commit hook or CI step.
set -u
cd "$(dirname "$0")/.." || exit 2
FE="frontend/src"
fail=0
note(){ echo "  PRIVACY VIOLATION: $1"; fail=1; }

echo "== privacy_check =="

# 1. No third-party trackers / analytics in the frontend.
TRACKERS='google-analytics|googletagmanager|gtag\(|\bfbq\(|connect\.facebook|segment\.com|mixpanel|hotjar|posthog|sentry\.io|fullstory|amplitude'
if grep -rqniE "$TRACKERS" "$FE" frontend/index.html 2>/dev/null; then
  note "third-party tracker/analytics reference found:"
  grep -rniE "$TRACKERS" "$FE" frontend/index.html 2>/dev/null | sed 's/^/    /'
fi

# 2. Giving/wallet data must never be POSTed to a server.
if grep -rniE "fetch\(|axios|XMLHttpRequest" "$FE" 2>/dev/null | grep -iE "merit_wallet|wallet_donations|wallet_volunteer" >/dev/null; then
  note "wallet data appears in a network call (must stay localStorage-only)"
fi

# 3. Access log must not contain the client IP token %(h).
if grep -rqnE "access-logformat" restart_api.sh 2>/dev/null; then
  if grep -E "access-logformat" restart_api.sh | grep -q '%(h)s'; then
    note "restart_api.sh access-logformat includes client IP %(h)s"
  fi
fi

# 4. CSP must stay strict — no unsafe-eval, no wildcard script/connect-src.
if grep -nE "Content-Security-Policy|script-src|connect-src" daanaa_api.py | grep -qE "unsafe-eval|script-src[^;]*\*|connect-src[^;]*\*"; then
  note "CSP weakened (unsafe-eval or wildcard in script-src/connect-src)"
fi

# 5. Tier 2 entity firewall (GATE 8): org_claims/waitlist/wallet/feedback data never in prospecting, outreach, or EcoMargins paths.
echo "GATE 8: Tier 2 Entity Firewall"
TIER2_TABLES='org_claims|waitlist|wallet|feedback|call_records'
ECOMARGINS_PATHS='ecomargins|prospecting|outreach|lead_scoring|marketing|consulting'

# Check 1: No Tier 2 table references in EcoMargins/prospecting code
if find . -name "*.py" -path "*/scripts/*" -o -name "*.py" -path "*/api/*" 2>/dev/null | \
   xargs grep -l "$ECOMARGINS_PATHS" 2>/dev/null | \
   xargs grep -l "$TIER2_TABLES" 2>/dev/null | grep -v privacy_check; then
  note "Tier 2 table reference found in prospecting/EcoMargins code path"
fi

# Check 2: No external AI service calls with Tier 2 data (only local inference allowed)
EXTERNAL_AI='openai|anthropic|groq|replicate|cohere|huggingface|api\.together'
if grep -rn "$EXTERNAL_AI" daanaa_api.py scripts/*.py 2>/dev/null | grep -vE "comment|#"; then
  # Allow only if it's clearly for Tier 0/1 data (public/published)
  if grep -rn "$EXTERNAL_AI" daanaa_api.py scripts/*.py 2>/dev/null | grep -qE "registry_enriched|mission.*public|tier.*0|tier.*1"; then
    :  # OK if clearly gated to Tier 0/1
  else
    # Flag as potential violation; requires human review
    echo "  ⚠ MANUAL REVIEW: external AI service reference found (should be local inference only for Tier 2)"
  fi
fi

# Check 3: Tier 2 exports and deletions are possible
if ! grep -q "export.*org_claims\|DELETE.*org_claims" daanaa_api.py; then
  echo "  ⚠ MANUAL REVIEW: Tier 2 data export/delete endpoints may be missing"
fi

if [ "$fail" -eq 0 ]; then
  echo "  OK — all machine-checkable privacy invariants hold."
else
  echo "== privacy_check FAILED — see PRIVACY-INVARIANTS.md =="
fi
exit "$fail"
