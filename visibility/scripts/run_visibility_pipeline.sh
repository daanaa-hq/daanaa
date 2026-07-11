#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEPLOY="${DEPLOY:-0}"
CHECK_LIVE="${CHECK_LIVE:-1}"

cd "$ROOT"

printf '\n[1/8] Build overlay from local data\n'
python3 visibility/scripts/build_overlay.py

printf '\n[2/8] Run content stewardship check\n'
python3 visibility/scripts/check_content_stewardship.py

printf '\n[3/8] Build growth opportunity report\n'
# Non-fatal by founder decision (2026-07-10): this step crashed with a transient
# "sqlite3.DatabaseError: malformed database schema (Beacon)" when it opened the
# registry while a concurrent FTS rebuild / nightly search deploy was rewriting the
# schema (logged pitfall: fts-rebuild-lock-contention; PRAGMA quick_check passes,
# no real corruption). Under `set -euo pipefail` that one report crash blocked
# steps 4-8 including the sitemap deploy. Reports are advisory; sitemaps are not —
# so a failure here warns and continues instead of killing the pipeline.
python3 visibility/scripts/build_growth_opportunity_report.py \
  || printf 'WARNING: growth opportunity report failed (transient DB schema contention?) — continuing.\n'

printf '\n[4/8] Build content and backlink targets\n'
python3 visibility/scripts/build_content_targets.py

printf '\n[5/8] Build improvement loop report\n'
python3 visibility/scripts/build_improvement_loop.py

printf '\n[6/8] Prepare Cloudflare Pages-safe assets\n'
python3 visibility/scripts/prepare_cloudflare_pages.py
python3 visibility/scripts/prepare_indexnow.py

printf '\n[7/8] Package overlay archive\n'
visibility/scripts/package_overlay.sh

if [[ "$DEPLOY" == "1" ]]; then
  printf '\n[8/8] Deploy to Cloudflare Pages\n'
  ./visibility/scripts/deploy_cloudflare_pages.sh
else
  printf '\n[8/8] Deploy skipped. Set DEPLOY=1 to upload to Cloudflare Pages.\n'
  ./visibility/scripts/deploy_cloudflare_pages.sh
fi

if [[ "$CHECK_LIVE" == "1" ]]; then
  printf '\n[extra] Live endpoint smoke checks\n'
  for url in \
    https://data.daanaa.org/open-data \
    https://data.daanaa.org/sitemap-index.xml \
    https://data.daanaa.org/llms.txt \
    https://data.daanaa.org/ai.txt \
    https://data.daanaa.org/data/orgs-manifest.json \
    https://data.daanaa.org/claim-nonprofit-page \
    https://data.daanaa.org/nonprofit-vendor-discounts
  do
    code="$(curl -L -s -o /dev/null -w '%{http_code}' "$url" || true)"
    printf '%s %s\n' "$code" "$url"
  done
fi
