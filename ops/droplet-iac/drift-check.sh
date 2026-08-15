#!/bin/bash
# drift-check.sh — Read-only comparison of live droplet config against the
# checked-in IaC in ops/droplet-iac/files/. Never modifies the droplet or
# the repo. Exit code 0 = no drift, 1 = drift found (safe for cron/alerting).
#
# This is the "diff, don't apply" tool the task asked for. Run it:
#   - before any manual SSH session that's about to touch nginx/systemd/ufw
#     (know what's already different before you add a third variable)
#   - after any deploy that touches droplet config
#   - on a schedule (weekly cron is enough — this config doesn't change often)
#
# Style matches scripts/ops/sync_droplet_api.sh (SSH key, retry, logging).

set -uo pipefail  # no -e: we want to keep checking after individual diffs fail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SSH_KEY="$HOME/.ssh/daanaa_do_cron"
TARGET="root@107.170.26.8"
for arg in "$@"; do
    case "$arg" in
        --target=*) TARGET="${arg#--target=}" ;;
    esac
done
prev=""
for arg in "$@"; do
    if [ "$prev" = "--target" ]; then TARGET="$arg"; fi
    prev="$arg"
done

SSH="ssh -i $SSH_KEY -o ConnectTimeout=15 -o BatchMode=yes -o StrictHostKeyChecking=accept-new $TARGET"

DRIFT_FOUND=0
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

check() {
    # check <label> <local_file> <remote_fetch_command>
    local label="$1" local_file="$2" remote_cmd="$3"
    local remote_out="$TMP/$(basename "$local_file").remote"
    if ! $SSH "$remote_cmd" > "$remote_out" 2>/dev/null; then
        echo ""
        echo "=== $label ==="
        echo "  COULD NOT FETCH from droplet (SSH or file-not-found) — treating as drift."
        DRIFT_FOUND=1
        return
    fi
    if ! diff -q "$local_file" "$remote_out" >/dev/null 2>&1; then
        echo ""
        echo "=== $label: DRIFT DETECTED ==="
        diff -u "$local_file" "$remote_out" | head -60
        DRIFT_FOUND=1
    else
        echo "=== $label: OK (matches checked-in IaC) ==="
    fi
}

log "Checking $TARGET against ops/droplet-iac/files/ ..."
log "NOTE: files/ includes explanatory comments the live droplet's minimal configs don't have -- expect comment-only lines in every diff below even when the functional config matches. Read past the comment hunks for the lines that actually change directives/values."
if ! $SSH "whoami" >/dev/null 2>&1; then
    log "FATAL: cannot reach $TARGET over SSH. Cannot check drift."
    exit 2
fi

check "nginx: sites-available/daanaa" \
    "$SCRIPT_DIR/files/nginx/daanaa.conf" \
    "cat /etc/nginx/sites-available/daanaa"

check "nginx: sites-available/daanaa-ssl" \
    "$SCRIPT_DIR/files/nginx/daanaa-ssl.conf" \
    "cat /etc/nginx/sites-available/daanaa-ssl"

check "systemd: daanaa-api.service" \
    "$SCRIPT_DIR/files/systemd/daanaa-api.service" \
    "cat /etc/systemd/system/daanaa-api.service"

check "systemd: env-override.conf" \
    "$SCRIPT_DIR/files/systemd/env-override.conf" \
    "cat /etc/systemd/system/daanaa-api.service.d/env-override.conf"

# --- Structural checks (not simple file diffs) ---

echo ""
echo "=== Structural check: duplicate ssl_certificate directives ==="
DUP=$($SSH "grep -rl ssl_certificate /etc/nginx/sites-enabled/ 2>/dev/null | grep -vE '/(daanaa-ssl)\$'")
if [ -n "$DUP" ]; then
    echo "  DRIFT: unexpected ssl_certificate directive(s) found outside daanaa-ssl:"
    echo "$DUP" | sed 's/^/    /'
    DRIFT_FOUND=1
else
    echo "  OK: only daanaa-ssl declares ssl_certificate."
fi

echo ""
echo "=== Structural check: DAANAA_PROD not blanked by drop-in ==="
BAD_ENV=$($SSH "grep -E '^Environment=\"DAANAA_PROD=\"?\"?\$' /etc/systemd/system/daanaa-api.service.d/*.conf 2>/dev/null")
if [ -n "$BAD_ENV" ]; then
    echo "  DRIFT (matches the 2026-08-14 live incident, see snapshot finding #1):"
    echo "$BAD_ENV" | sed 's/^/    /'
    DRIFT_FOUND=1
else
    echo "  OK: no drop-in sets DAANAA_PROD to an empty value."
fi

echo ""
echo "=== Structural check: PRECOMPUTE_DIR points at a directory that exists ==="
PC_DIR=$($SSH "grep -hoP '(?<=PRECOMPUTE_DIR=)[^\"]*' /etc/systemd/system/daanaa-api.service.d/*.conf /etc/systemd/system/daanaa-api.service 2>/dev/null | tail -1")
if [ -n "$PC_DIR" ]; then
    if $SSH "test -d '$PC_DIR'"; then
        echo "  OK: $PC_DIR exists."
    else
        echo "  DRIFT: PRECOMPUTE_DIR=$PC_DIR does not exist on disk. Service would fail to serve data on next restart."
        DRIFT_FOUND=1
    fi
fi

echo ""
echo "=== Structural check: ufw status ==="
UFW=$($SSH "ufw status | head -1")
echo "  Live: $UFW"
if echo "$UFW" | grep -q "inactive"; then
    echo "  NOTE: ufw inactive — known gap (snapshot finding #3), not newly-introduced drift. Not counted as drift by this check since files/ufw/rules.txt is opt-in (provision.sh --enable-firewall), but flagging every run until fixed."
fi

echo ""
echo "=== Structural check: gunicorn bind list (0.0.0.0:8880 exposure) ==="
BIND8880=$($SSH "ss -tlnp 2>/dev/null | grep ':8880 ' || true")
if [ -n "$BIND8880" ]; then
    echo "  NOTE: gunicorn still bound to 0.0.0.0:8880 (snapshot finding #3). The checked-in canonical systemd unit removes this bind — live droplet hasn't had that applied yet. Not counted as new drift (known, tracked), but surfaced every run as a reminder."
fi

echo ""
log "Drift check complete."
if [ "$DRIFT_FOUND" = 1 ]; then
    log "RESULT: DRIFT FOUND. Review diffs above before making further manual changes."
    exit 1
else
    log "RESULT: no file-level drift from checked-in IaC."
    exit 0
fi
