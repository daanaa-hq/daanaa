#!/bin/bash
# migrate_type_scale.sh — Replace hand-rolled `text-[Npx]` with semantic type
# scale tokens defined in frontend/tailwind.config.js.
#
# Twelve sizes are a pure rename (no visual change). Eleven drift sizes fold
# into their nearest neighbour, which IS a small visual change — those are
# listed separately below so they can be reviewed.
#
# Usage:
#   bash scripts/migrate_type_scale.sh --dry-run   # report only
#   bash scripts/migrate_type_scale.sh             # apply

set -euo pipefail

cd "$(dirname "$0")/.."
SRC="frontend/src"
DRY_RUN=0
[ "${1:-}" = "--dry-run" ] && DRY_RUN=1

# px -> token. Pure renames (size is preserved exactly).
EXACT="
10:micro
11:label
12:caption
13:small
14:body
15:body-lg
16:lead
18:title-sm
20:title
24:title-lg
28:headline
32:headline-lg
40:display
"

# px -> token. Drift sizes; these change rendered size to the nearest token.
DRIFT="
8:micro
9:micro
17:title-sm
19:title
22:title-lg
26:headline
30:headline-lg
34:headline-lg
42:display
48:display
52:display
"

count_for() {
  grep -rho "text-\[$1px\]" "$SRC" 2>/dev/null | wc -l | tr -d ' '
}

apply_for() {
  local px="$1" token="$2"
  # Preserves any variant prefix (md:, hover:, dark: ...) since only the
  # `text-[Npx]` fragment is rewritten.
  grep -rl "text-\[${px}px\]" "$SRC" 2>/dev/null \
    | xargs -r sed -i "s/text-\[${px}px\]/text-${token}/g"
}

total_exact=0
total_drift=0

echo "=== Pure renames (no visual change) ==="
for pair in $EXACT; do
  px="${pair%%:*}"; token="${pair##*:}"
  n=$(count_for "$px")
  [ "$n" = "0" ] && continue
  printf "  %5s  text-[%spx] -> text-%s\n" "$n" "$px" "$token"
  total_exact=$((total_exact + n))
  [ "$DRY_RUN" = "0" ] && apply_for "$px" "$token"
done

echo ""
echo "=== Drift folded to nearest token (small visual change) ==="
for pair in $DRIFT; do
  px="${pair%%:*}"; token="${pair##*:}"
  n=$(count_for "$px")
  [ "$n" = "0" ] && continue
  printf "  %5s  text-[%spx] -> text-%s\n" "$n" "$px" "$token"
  total_drift=$((total_drift + n))
  [ "$DRY_RUN" = "0" ] && apply_for "$px" "$token"
done

echo ""
echo "Pure renames: $total_exact"
echo "Drift folded: $total_drift"
echo "Total:        $((total_exact + total_drift))"

if [ "$DRY_RUN" = "1" ]; then
  echo ""
  echo "(dry run — nothing written)"
else
  remaining=$(grep -rho "text-\[[0-9]*px\]" "$SRC" 2>/dev/null | wc -l | tr -d ' ')
  echo "Remaining raw sizes: $remaining"
fi
