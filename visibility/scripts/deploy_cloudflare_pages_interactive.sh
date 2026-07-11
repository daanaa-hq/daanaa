#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [[ -z "${CLOUDFLARE_API_TOKEN:-}" ]]; then
  if [[ -t 0 ]]; then
    read -rs -p "Cloudflare API token: " CLOUDFLARE_API_TOKEN
    printf '\n'
    export CLOUDFLARE_API_TOKEN
  else
    echo "CLOUDFLARE_API_TOKEN is not set and stdin is not interactive." >&2
    exit 1
  fi
fi

export DEPLOY=1
export PROJECT_NAME="${PROJECT_NAME:-daanaa-visibility}"
export BRANCH="${BRANCH:-main}"
exec "$ROOT/visibility/scripts/deploy_cloudflare_pages.sh"
