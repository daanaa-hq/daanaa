#!/usr/bin/env bash
# Deploy the org sitemaps (richness-first) to the droplet.
#
# Flow: scripts/generate_visibility_exports.py -> dist/sitemaps/* + dist/sitemap-index.xml
#       -> rsync to droplet /opt/daanaa/visibility/ -> public verify on daanaa.org.
#
# The droplet serves these via dedicated nginx locations (= /sitemap-index.xml and
# /sitemaps/) added 2026-07-10. Files live OUTSIDE /opt/daanaa/frontend/dist on
# purpose: deploy_morning.sh rsyncs that dir with --delete and would wipe them.
#
# The static-pages sitemap at daanaa.org/sitemap.xml is a different file
# (frontend/public/sitemap.xml) and is not touched here.
#
# Safe to run from cron. Fails loudly and leaves the previous live sitemaps in
# place if generation fails (rsync only runs after a successful generate).

set -euo pipefail

REPO="/home/akbar/meritgiving"
DROPLET="root@107.170.26.8"
SSH_KEY="$HOME/.ssh/daanaa_do_cron"
REMOTE_DIR="/opt/daanaa/visibility"

cd "$REPO"
source venv/bin/activate

echo "[1/3] Generating exports (richness-first order)..."
python3 scripts/generate_visibility_exports.py

test -s dist/sitemap-index.xml
FILE_COUNT=$(ls dist/sitemaps/orgs-*.xml | wc -l)
if [[ "$FILE_COUNT" -lt 30 ]]; then
  echo "ERROR: only $FILE_COUNT sitemap files generated (expected ~35) — refusing to ship." >&2
  exit 1
fi

echo "[2/3] Shipping $FILE_COUNT sitemap files to droplet..."
rsync -az -e "ssh -i $SSH_KEY" --delete dist/sitemaps/ "$DROPLET:$REMOTE_DIR/sitemaps/"
rsync -az -e "ssh -i $SSH_KEY" dist/sitemap-index.xml "$DROPLET:$REMOTE_DIR/sitemap-index.xml"

echo "[3/3] Public smoke test..."
for url in \
  https://daanaa.org/ \
  https://daanaa.org/sitemap-index.xml \
  https://daanaa.org/sitemaps/orgs-0001.xml \
  https://daanaa.org/sitemap.xml
do
  code=$(curl -s -o /dev/null -w '%{http_code}' "$url")
  echo "$code $url"
  if [[ "$code" != "200" ]]; then
    echo "ERROR: smoke test failed for $url" >&2
    exit 1
  fi
done

echo "Org sitemaps deployed and verified."
