#!/bin/bash
# Design system compliance checker
# Ensures no raw Tailwind colors, proper Button usage, etc.

set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"
FRONTEND="$REPO_ROOT/frontend"
SRC="$FRONTEND/src"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

violations=0

echo "🎨 Daanaa Design System Compliance Check"
echo "========================================"

# Check 1: Raw Tailwind color utilities (bg-red-600, text-green-700, etc.)
# Note: slate/gray colors are acceptable for neutral/info states
echo -n "Checking for raw Tailwind colors... "
raw_colors=$(grep -r "className=\"[^\"]*\(bg-\|text-\|border-\)\(red\|green\|blue\|amber\|cyan\|violet\|pink\|orange\)-[0-9]\+" "$SRC" --include="*.tsx" --include="*.ts" 2>/dev/null | grep -v "node_modules" || true)
if [ -n "$raw_colors" ]; then
  echo -e "${RED}❌ Found${NC}"
  echo "$raw_colors" | head -5
  echo "    Use semantic tokens instead: bg-red-600 → bg-destructive, bg-green-600 → bg-success-green"
  violations=$((violations + 1))
else
  echo -e "${GREEN}✅${NC}"
fi

# Check 2: Inline <button> with className (should use <Button> component)
echo -n "Checking for inline button elements... "
inline_buttons=$(grep -r "<button[^>]*className=" "$SRC" --include="*.tsx" 2>/dev/null | grep -v "aria-label.*Close\|p-1.5\|rounded-full" | grep -v "node_modules" || true)
if [ -n "$inline_buttons" ]; then
  echo -e "${YELLOW}⚠${NC} Found (may be intentional for icon buttons)"
  echo "$inline_buttons" | wc -l | xargs echo "   Count:"
else
  echo -e "${GREEN}✅${NC}"
fi

# Check 3: Emoji in functional UI (should be removed)
echo -n "Checking for emoji in className or text... "
emoji=$(grep -r "[😀-🙏❤💯🎲✅❌🤝📄🔗]" "$SRC" --include="*.tsx" 2>/dev/null | grep -v "node_modules" | grep -v "// emoji\|Emoji disabled" || true)
if [ -n "$emoji" ]; then
  echo -e "${RED}❌ Found${NC}"
  echo "$emoji" | head -3
  violations=$((violations + 1))
else
  echo -e "${GREEN}✅${NC}"
fi

# Check 4: Missing Button import in pages that use <Button>
echo -n "Checking Button component imports... "
button_usage=$(grep -r "<Button " "$SRC/pages" --include="*.tsx" 2>/dev/null | grep -v "node_modules" | cut -d: -f1 | sort -u || true)
missing_imports=0
while IFS= read -r file; do
  if [ -n "$file" ]; then
    if ! grep -q "from.*Button\|import.*Button" "$file"; then
      echo "   Missing Button import: $file"
      missing_imports=$((missing_imports + 1))
    fi
  fi
done <<< "$button_usage"
if [ $missing_imports -gt 0 ]; then
  echo -e "${RED}❌ Found $missing_imports files${NC}"
  violations=$((violations + 1))
else
  echo -e "${GREEN}✅${NC}"
fi

# Check 5: Type scale compliance (app + standalone pages)
# The scale lives in frontend/public/tokens.css. Raw sizes bypass it, which is
# how 2,038 hand-rolled `text-[Npx]` accumulated across 24 distinct values.
echo -n "Checking type scale compliance... "
if bash "$REPO_ROOT/scripts/lint_type_scale.sh" >/tmp/.type-scale-lint 2>&1; then
  echo -e "${GREEN}✅${NC}"
else
  echo -e "${RED}❌ Found${NC}"
  sed 's/^/   /' /tmp/.type-scale-lint | head -20
  violations=$((violations + 1))
fi
rm -f /tmp/.type-scale-lint

# Check 6: Nav height magic numbers
# The nav height was declared once in Navigation.tsx and copied into 37 page
# files as pt-[72px]. Changing the nav would have slid content under the header
# on every one of them, silently. Tokens live in public/tokens.css.
echo -n "Checking nav offset tokens... "
nav_magic=$(grep -rnE "(pt|mt|scroll-mt)-\[(72|88|108)px\]|h-\[72px\]" "$SRC" 2>/dev/null || true)
if [ -n "$nav_magic" ]; then
  echo -e "${RED}❌ Found${NC}"
  echo "$nav_magic" | head -5 | sed 's/^/   /'
  echo "    Use tokens: pt-nav (72), pt-nav-lg (108), scroll-mt-anchor (88), h-nav"
  violations=$((violations + 1))
else
  echo -e "${GREEN}✅${NC}"
fi

# Check 7: Inline scripts in index.html
# Production sends `script-src 'self'` with no 'unsafe-inline' and no hash, so
# any inline <script> is silently blocked on daanaa.org while working fine in
# local preview (which sends no CSP). That exact gap meant the theme init
# script never ran in production and light mode never survived a page load.
echo -n "Checking for CSP-blocked inline scripts... "
inline_js=$(awk '/<script(>| [^>]*[^\/])>/{ if ($0 !~ /src=/) print FILENAME": "NR": "$0 }' \
  "$FRONTEND/index.html" 2>/dev/null || true)
if [ -n "$inline_js" ]; then
  echo -e "${RED}❌ Found${NC}"
  echo "$inline_js" | head -3 | sed 's/^/   /'
  echo "    Production CSP blocks inline scripts. Move it to public/ and load"
  echo "    with <script src=\"/your-file.js\"></script> ('self' permits it)."
  violations=$((violations + 1))
else
  echo -e "${GREEN}✅${NC}"
fi

echo ""
echo "========================================"
if [ $violations -eq 0 ]; then
  echo -e "${GREEN}✅ All design checks passed!${NC}"
  exit 0
else
  echo -e "${RED}❌ $violations check(s) failed${NC}"
  echo ""
  echo "See DESIGN.md for guidance: $REPO_ROOT/DESIGN.md"
  exit 1
fi
