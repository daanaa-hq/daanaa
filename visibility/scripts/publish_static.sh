#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DRY_RUN="${DRY_RUN:-1}"
TARGET="${TARGET:-}"

if [[ -z "$TARGET" ]]; then
  cat >&2 <<'EOF'
Missing TARGET.

This script publishes the overlay to a separate static target, never to the app.

Example dry run to local staging folder:
  TARGET=/tmp/daanaa-visibility-public DRY_RUN=1 visibility/scripts/publish_static.sh

Real local copy, after review:
  TARGET=/tmp/daanaa-visibility-public DRY_RUN=0 visibility/scripts/publish_static.sh
EOF
  exit 2
fi

cd "$ROOT"
test -d visibility/public

if [[ "$TARGET" == "$ROOT"* ]]; then
  echo "Refusing to publish into the project tree: $TARGET" >&2
  exit 3
fi

if [[ "$DRY_RUN" != "0" ]]; then
  rsync -avnc --delete visibility/public/ "$TARGET/"
else
  mkdir -p "$TARGET"
  rsync -avc --delete visibility/public/ "$TARGET/"
fi

