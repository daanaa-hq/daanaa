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

if [ "$fail" -eq 0 ]; then
  echo "  OK — all machine-checkable privacy invariants hold."
else
  echo "== privacy_check FAILED — see PRIVACY-INVARIANTS.md =="
fi
exit "$fail"
