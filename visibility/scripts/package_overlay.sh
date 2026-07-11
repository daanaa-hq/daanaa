#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT_DIR="$ROOT/visibility/artifacts"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
ARCHIVE="$OUT_DIR/daanaa-visibility-overlay-$STAMP.tar.gz"

cd "$ROOT"

test -d visibility/public
mkdir -p "$OUT_DIR"

tar -czf "$ARCHIVE" -C visibility public reports README.md

BYTES="$(wc -c < "$ARCHIVE" | tr -d ' ')"
SHA256="$(sha256sum "$ARCHIVE" | awk '{print $1}')"

cat > "$ARCHIVE.sha256" <<EOF
$SHA256  $(basename "$ARCHIVE")
EOF

printf 'Created %s\n' "$ARCHIVE"
printf 'Bytes: %s\n' "$BYTES"
printf 'SHA256: %s\n' "$SHA256"

