#!/usr/bin/env bash
  set -Eeuo pipefail

  APP_DIR="/home/akbar/meritgiving"
  DROPLET="root@107.170.26.8"
  REMOTE_DIR="/opt/daanaa"
  DB="/opt/daanaa/merit_registry.db"
  EIN="${EIN:-000019818}"
  APPROVE_BACKEND_DEPLOY="${APPROVE_BACKEND_DEPLOY:-false}"

  cd "$APP_DIR"

  echo "== Local release gates =="

  git diff --check
  python3 -m py_compile droplet_api.py scripts/v6_financial_context_api.py

  cd frontend
  npm run build
  npm test -- --runInBand
  cd ..

  echo "Review exact files:"
  git status --short
  git diff -- droplet_api.py frontend/src/pages/OrganizationDetail.tsx

  if [[ "$APPROVE_BACKEND_DEPLOY" != "true" ]]; then
    echo
    echo "Validation complete. Deployment intentionally not performed."
    echo "Before deployment, confirm:"
    echo "  1. All tests pass or failures are formally approved."
    echo "  2. DigitalOcean snapshot is complete."
    echo "  3. Production SQLite backup is verified."
    echo "  4. The backend diff is approved."
    exit 0
  fi

  echo "== Droplet preflight =="

  ssh "$DROPLET" "
    set -Eeuo pipefail
    systemctl is-active --quiet nginx
    systemctl is-active --quiet daanaa
    test -f '$DB'
    df -h /
    free -h
    sqlite3 '$DB' 'PRAGMA integrity_check;'
    sqlite3 '$DB' \"SELECT name FROM sqlite_master WHERE type='table' AND
    name='v6_peer_context_assignments';\"
  "

  echo "== Creating verified production database backup =="

  STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
  REMOTE_BACKUP="/opt/daanaa/backups/pre-v6-route-${STAMP}.db"

  ssh "$DROPLET" "
    set -Eeuo pipefail
    mkdir -p /opt/daanaa/backups
    sqlite3 '$DB' \".backup '$REMOTE_BACKUP'\"
    sqlite3 '$REMOTE_BACKUP' 'PRAGMA integrity_check;' | grep -qx ok
    echo \"Verified backup: $REMOTE_BACKUP\"
  "

  echo "== Saving current backend for rollback =="

  ssh "$DROPLET" "
    set -Eeuo pipefail
    cp '$REMOTE_DIR/droplet_api.py' '$REMOTE_DIR/droplet_api.py.pre-v6-${STAMP}'
  "

  echo "== Deploying backend only =="

  scp "$APP_DIR/droplet_api.py" "$DROPLET:$REMOTE_DIR/droplet_api.py"

  ssh "$DROPLET" "
    set -Eeuo pipefail
    python3 -m py_compile '$REMOTE_DIR/droplet_api.py'
    systemctl restart daanaa
    sleep 12
    systemctl is-active --quiet daanaa
    curl -fsS --max-time 20 http://127.0.0.1:5000/health
  "

  echo "== Local droplet API gate =="

  ssh "$DROPLET" "
    set -Eeuo pipefail
    RESPONSE=\$(curl -fsS --max-time 30 \
      -H 'Accept: application/json' \
      'http://127.0.0.1:5000/api/organizations/$EIN/financial-context')

    python3 -c '
  import json, sys
  data = json.loads(sys.stdin.read())
  required = [
      \"status\",
      \"selected_tier\",
      \"peer_reference_label\",
      \"data_limitations\"
  ]
  missing = [key for key in required if key not in data]
  if missing:
      raise SystemExit(\"Missing fields: \" + \", \".join(missing))
  print(\"Local v6 API JSON gate passed\")
  ' <<< \"\$RESPONSE\"
  "

  echo "== Public API gate =="

  CONTENT_TYPE="$(curl -fsSI --max-time 30 \
    "https://daanaa.org/api/organizations/${EIN}/financial-context" \
    | awk -F': ' 'tolower($1) == "content-type" {print tolower($2)}' \
    | tr -d '\r')"

  [[ "$CONTENT_TYPE" == application/json* ]] || {
    echo "FAIL: Public v6 endpoint is not returning JSON."
    echo "Content-Type: $CONTENT_TYPE"
    exit 1
  }

  curl -fsS --max-time 30 \
    -H "Accept: application/json" \
    "https://daanaa.org/api/organizations/${EIN}/financial-context" \
    | python3 -m json.tool >/dev/null

  echo
  echo "Backend deployment passed."
  echo "Frontend deployment remains paused until browser QA is complete."
  echo "Rollback file: $REMOTE_DIR/droplet_api.py.pre-v6-${STAMP}"
  echo "Database backup: $REMOTE_BACKUP"
