#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROJECT_NAME="${PROJECT_NAME:-daanaa-visibility}"
BRANCH="${BRANCH:-main}"
DEPLOY="${DEPLOY:-0}"
PUBLIC_DIR="${PUBLIC_DIR:-$ROOT/visibility/cloudflare-public}"

cd "$ROOT"

test -d "$PUBLIC_DIR"
test -f "$PUBLIC_DIR/sitemap-index.xml"
test -f "$PUBLIC_DIR/llms.txt"
test -f "$PUBLIC_DIR/open-data.html"
test -f "$PUBLIC_DIR/data/orgs-manifest.json"

CMD=(npx wrangler pages deploy "$PUBLIC_DIR" --project-name "$PROJECT_NAME" --branch "$BRANCH")

if [[ "$DEPLOY" != "1" ]]; then
  echo "Dry run only. No Cloudflare upload will happen."
  printf 'Would run:'
  printf ' %q' "${CMD[@]}"
  printf '
'
  echo
  echo "To deploy after Cloudflare auth is ready:"
  printf 'DEPLOY=1 PROJECT_NAME=%q BRANCH=%q visibility/scripts/deploy_cloudflare_pages.sh
' "$PROJECT_NAME" "$BRANCH"
  exit 0
fi

"${CMD[@]}"
