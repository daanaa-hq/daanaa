#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DRY_RUN="${DRY_RUN:-1}"
S3_URI="${S3_URI:-}"

if [[ -z "$S3_URI" ]]; then
  cat >&2 <<'EOF'
Missing S3_URI.

Example dry run:
  S3_URI=s3://your-bucket/daanaa-visibility DRY_RUN=1 visibility/scripts/backup_to_s3.sh

Real upload, after review:
  S3_URI=s3://your-bucket/daanaa-visibility DRY_RUN=0 visibility/scripts/backup_to_s3.sh
EOF
  exit 2
fi

cd "$ROOT"
test -d visibility/public
test -d visibility/reports

ARGS=(s3 sync visibility/public "$S3_URI/public" --delete)
if [[ "$DRY_RUN" != "0" ]]; then
  ARGS+=(--dryrun)
fi

printf 'Running: aws %q ' "${ARGS[@]}"
printf '\n'
aws "${ARGS[@]}"

REPORT_ARGS=(s3 sync visibility/reports "$S3_URI/reports" --delete)
if [[ "$DRY_RUN" != "0" ]]; then
  REPORT_ARGS+=(--dryrun)
fi

printf 'Running: aws %q ' "${REPORT_ARGS[@]}"
printf '\n'
aws "${REPORT_ARGS[@]}"

