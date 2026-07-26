#!/bin/bash
# lint_type_scale.sh — Keep the type scale authoritative on EVERY Daanaa surface.
#
# The scale lives in frontend/public/tokens.css. Tailwind references it, and
# standalone pages link it directly. Two ways to bypass it, both checked here:
#
#   1. React/TSX      raw `text-[Npx]` utilities
#   2. Standalone HTML  raw `font-size: Npx` declarations
#
# This is not theoretical. 2,038 hand-rolled sizes across 24 distinct values
# accumulated in the app, and open-data.html separately hand-copied the whole
# palette into its own :root. Both drifted one locally-reasonable edit at a time.
#
# Usage: bash scripts/lint_type_scale.sh
# Exit 0 = clean, 1 = violations.

set -uo pipefail

cd "$(dirname "$0")/.."
FAIL=0

# ── 1. React source: raw text-[Npx] ──────────────────────────────────────────
TSX_HITS=$(grep -rn "text-\[[0-9]*px\]" frontend/src 2>/dev/null || true)

if [ -n "$TSX_HITS" ]; then
  echo "✗ Raw pixel text sizes in frontend/src — use a scale token:"
  printf '%s\n' "$TSX_HITS"
  echo ""
  FAIL=1
fi

# ── 2. Standalone HTML: raw font-size: Npx ───────────────────────────────────
# tokens.css itself is the definition, so it is excluded.
HTML_HITS=$(grep -rn "font-size: *[0-9]" \
  frontend/public/*.html 2>/dev/null || true)

if [ -n "$HTML_HITS" ]; then
  echo "✗ Raw font-size in standalone HTML — use var(--text-*) from tokens.css:"
  printf '%s\n' "$HTML_HITS"
  echo ""
  FAIL=1
fi

# ── 3. Standalone HTML must link the shared tokens ───────────────────────────
for f in frontend/public/*.html; do
  [ -e "$f" ] || continue
  if grep -q "font-size\|:root" "$f" 2>/dev/null; then
    if ! grep -q "tokens.css" "$f" 2>/dev/null; then
      echo "✗ $f styles text but does not link /tokens.css"
      echo "  Add: <link rel=\"stylesheet\" href=\"/tokens.css\">"
      echo ""
      FAIL=1
    fi
  fi
done

if [ "$FAIL" = "0" ]; then
  echo "✓ type scale clean — app and standalone pages both on tokens.css"
  exit 0
fi

echo "Tokens (frontend/public/tokens.css):"
echo "  micro 10   label 11    caption 12   small 13"
echo "  body 14    body-lg 15  lead 16      title-sm 18"
echo "  title 20   title-lg 24 headline 28  headline-lg 32   display 40"
echo ""
echo "In TSX use the Tailwind class:  text-body"
echo "In standalone HTML use the var: font-size: var(--text-body);"
echo "For fluid page headings prefer h1/h2/h3-display, or var(--text-fluid-h1)."
exit 1
