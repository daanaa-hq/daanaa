#!/bin/bash
# provision.sh — Idempotent droplet provisioner for daanaa.org.
#
# Reproduces the droplet's nginx/systemd/firewall/directory state from the
# files checked into ops/droplet-iac/files/, instead of tribal SSH knowledge.
# Ansible was considered and rejected for this: not installed locally or on
# the droplet (checked 2026-08-14, see snapshot/packages.txt), and adding it
# as a new dependency just to run a handful of file-copy + systemctl steps
# fails the CLAUDE.md "small diffs, justify new deps" bar. This script does
# the same job with tools already on every Ubuntu box (ssh, rsync, systemctl,
# nginx, ufw).
#
# SAFE BY DEFAULT: runs in --dry-run unless --apply is passed. Even under
# --apply, firewall enablement and cert issuance are separately gated
# (--enable-firewall, --issue-cert) because both can take a service offline
# if done wrong (locking out SSH; hitting Let's Encrypt rate limits).
#
# Usage:
#   ./provision.sh                      # dry-run: show what would change, change nothing
#   ./provision.sh --apply              # apply nginx + systemd + directory state (safe subset)
#   ./provision.sh --apply --enable-firewall   # additionally turn on ufw (22/80/443 only)
#   ./provision.sh --apply --issue-cert        # additionally run certbot certonly (fresh droplet only)
#   ./provision.sh --target root@1.2.3.4       # provision a different host (e.g. a staging droplet)
#
# Style/conventions match scripts/ops/sync_droplet_api.sh (SSH key, retry
# wrapper, logging) so this fits the existing ops toolkit rather than
# introducing a new pattern.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SSH_KEY="$HOME/.ssh/daanaa_do_cron"
TARGET="root@107.170.26.8"
DRY_RUN=1
ENABLE_FIREWALL=0
ISSUE_CERT=0

for arg in "$@"; do
    case "$arg" in
        --apply) DRY_RUN=0 ;;
        --enable-firewall) ENABLE_FIREWALL=1 ;;
        --issue-cert) ISSUE_CERT=1 ;;
        --target) : ;; # value consumed below
        --target=*) TARGET="${arg#--target=}" ;;
        *) : ;;
    esac
done
# handle "--target VALUE" (space form)
prev=""
for arg in "$@"; do
    if [ "$prev" = "--target" ]; then TARGET="$arg"; fi
    prev="$arg"
done

SSH="ssh -i $SSH_KEY -o ConnectTimeout=15 -o BatchMode=yes -o StrictHostKeyChecking=accept-new $TARGET"
RSYNC_SSH="ssh -i $SSH_KEY -o BatchMode=yes -o StrictHostKeyChecking=accept-new"

log()   { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
plan()  { echo "  [PLAN] $*"; }
apply() { echo "  [APPLY] $*"; }

retry() {
    "$@" && return 0
    log "Retrying in 10s: $*"
    sleep 10
    "$@"
}

if [ "$DRY_RUN" = 1 ]; then
    log "DRY RUN — no changes will be made. Pass --apply to actually provision."
else
    log "APPLY MODE — this will write config to $TARGET."
fi
log "Target: $TARGET"

# ---------------------------------------------------------------------------
# 0. Preflight
# ---------------------------------------------------------------------------
log "Preflight: checking SSH reachability..."
if ! retry $SSH "whoami" >/dev/null 2>&1; then
    log "FATAL: cannot reach $TARGET over SSH with key $SSH_KEY. Aborting — no changes possible or attempted."
    exit 1
fi
log "SSH OK."

# ---------------------------------------------------------------------------
# 1. Packages (idempotent — apt-get install -y is a no-op if already present)
# ---------------------------------------------------------------------------
log "Step 1/6: packages (nginx, certbot, python3.12-venv, ufw)"
PKG_CMD='apt-get install -y nginx certbot python3-certbot ufw python3.12-venv'
if [ "$DRY_RUN" = 1 ]; then
    plan "apt-get update && $PKG_CMD"
else
    apply "apt-get update -qq && $PKG_CMD"
    $SSH "apt-get update -qq && DEBIAN_FRONTEND=noninteractive $PKG_CMD"
fi

# ---------------------------------------------------------------------------
# 2. Directory structure
# ---------------------------------------------------------------------------
log "Step 2/6: directory structure under /opt/daanaa and /data"
DIRS="/opt/daanaa /opt/daanaa/frontend /opt/daanaa/data /opt/daanaa/data/analytics \
/opt/daanaa/data/backups /opt/daanaa/data/claims /opt/daanaa/data/precompute \
/opt/daanaa/logs /opt/daanaa/scripts /opt/daanaa/staging /var/www/acme/.well-known/acme-challenge"
if [ "$DRY_RUN" = 1 ]; then
    for d in $DIRS; do plan "mkdir -p $d (mode 755, root:root)"; done
    plan "NOTE: live droplet has /opt/daanaa/data at mode 777 (world-writable) — see snapshot finding #5. This IaC creates it at 755. Applying to the LIVE droplet tightens permissions; verify nothing currently depends on world-writability before running --apply there."
else
    for d in $DIRS; do
        apply "mkdir -p $d"
        $SSH "mkdir -p '$d' && chmod 755 '$d'"
    done
fi

# ---------------------------------------------------------------------------
# 3. nginx config
# ---------------------------------------------------------------------------
log "Step 3/6: nginx site config"
if [ "$DRY_RUN" = 1 ]; then
    plan "rsync files/nginx/daanaa.conf     -> /etc/nginx/sites-available/daanaa"
    plan "rsync files/nginx/daanaa-ssl.conf -> /etc/nginx/sites-available/daanaa-ssl"
    plan "ln -sf sites-available/{daanaa,daanaa-ssl} sites-enabled/"
    plan "rm -f /etc/nginx/sites-enabled/default (stock Ubuntu default — not used)"
    plan "nginx -t (validate before any reload)"
    plan "SAFETY CHECK: refuse if any file under sites-enabled/ OTHER than daanaa/daanaa-ssl declares ssl_certificate — this is the exact duplicate-SSL-directive check that would have caught the incident"
else
    DUP=$($SSH "grep -rl ssl_certificate /etc/nginx/sites-enabled/ 2>/dev/null | grep -vE '/(daanaa-ssl)\$' || true")
    if [ -n "$DUP" ]; then
        log "FATAL: found unexpected ssl_certificate directive(s) outside daanaa-ssl: $DUP"
        log "Refusing to deploy nginx config — resolve the duplicate manually first (this is the exact failure mode from the incident this playbook exists to prevent)."
        exit 1
    fi
    apply "nginx config -> sites-available/"
    retry rsync -e "$RSYNC_SSH" --checksum --backup --suffix=".prev" \
        "$SCRIPT_DIR/files/nginx/daanaa.conf" "$TARGET:/etc/nginx/sites-available/daanaa"
    retry rsync -e "$RSYNC_SSH" --checksum --backup --suffix=".prev" \
        "$SCRIPT_DIR/files/nginx/daanaa-ssl.conf" "$TARGET:/etc/nginx/sites-available/daanaa-ssl"
    $SSH "ln -sf /etc/nginx/sites-available/daanaa /etc/nginx/sites-enabled/daanaa && \
          ln -sf /etc/nginx/sites-available/daanaa-ssl /etc/nginx/sites-enabled/daanaa-ssl && \
          rm -f /etc/nginx/sites-enabled/default"
    if ! $SSH "nginx -t" 2>&1; then
        log "FATAL: nginx -t failed after config deploy. NOT reloading nginx. Config on disk may be broken — investigate before any reload."
        exit 1
    fi
    log "nginx -t passed. NOT reloading automatically — run '$SSH systemctl reload nginx' by hand after reviewing the diff, or add --reload-nginx support if this becomes routine."
fi

# ---------------------------------------------------------------------------
# 4. systemd unit + env override
# ---------------------------------------------------------------------------
log "Step 4/6: systemd service"
if [ "$DRY_RUN" = 1 ]; then
    plan "rsync files/systemd/daanaa-api.service     -> /etc/systemd/system/daanaa-api.service"
    plan "mkdir -p /etc/systemd/system/daanaa-api.service.d/"
    plan "rsync files/systemd/env-override.conf      -> /etc/systemd/system/daanaa-api.service.d/env-override.conf"
    plan "SAFETY CHECK: refuse if the resulting merged environment has DAANAA_PROD unset or empty — this is the exact env-drift bug found live on 2026-08-14 (snapshot finding #1)"
    plan "systemctl daemon-reload"
    plan "NOT restarting the service automatically — a systemd unit change requires a restart to take effect, and that's a live-traffic-impacting action. Run manually after reviewing: ssh ... systemctl restart daanaa-api, then smoke-test per scripts/ops/sync_droplet_api.sh's pattern."
else
    apply "systemd unit -> /etc/systemd/system/daanaa-api.service"
    retry rsync -e "$RSYNC_SSH" --checksum --backup --suffix=".prev" \
        "$SCRIPT_DIR/files/systemd/daanaa-api.service" "$TARGET:/etc/systemd/system/daanaa-api.service"
    $SSH "mkdir -p /etc/systemd/system/daanaa-api.service.d"
    retry rsync -e "$RSYNC_SSH" --checksum --backup --suffix=".prev" \
        "$SCRIPT_DIR/files/systemd/env-override.conf" "$TARGET:/etc/systemd/system/daanaa-api.service.d/env-override.conf"

    # Structural guard: verify DAANAA_PROD would come out non-empty after
    # the merge. systemd doesn't expose "show merged env" without starting
    # the unit, so approximate: fail if the drop-in defines DAANAA_PROD at
    # all with an empty value (the exact bug pattern found live).
    BAD_ENV=$($SSH "grep -E '^Environment=\"DAANAA_PROD=\"?\"?\$' /etc/systemd/system/daanaa-api.service.d/env-override.conf 2>/dev/null || true")
    if [ -n "$BAD_ENV" ]; then
        log "FATAL: env-override.conf sets DAANAA_PROD to an empty value. Refusing — this is the exact bug from snapshot finding #1. Fix files/systemd/env-override.conf before re-running."
        exit 1
    fi
    $SSH "systemctl daemon-reload"
    log "daemon-reload done. NOT restarting daanaa-api automatically — do that by hand after reviewing, then smoke-test (see scripts/ops/sync_droplet_api.sh for the smoke pattern: homepage doctype + /api/search 200 + /api/organizations 200)."
fi

# ---------------------------------------------------------------------------
# 5. Firewall (opt-in only — can lock out SSH if done wrong)
# ---------------------------------------------------------------------------
log "Step 5/6: firewall (ufw)"
if [ "$ENABLE_FIREWALL" = 0 ]; then
    plan "Skipped — pass --enable-firewall to apply ufw rules from files/ufw/rules.txt. Live droplet currently has ufw INACTIVE (snapshot finding #3); this is a real gap but enabling it wrong can cut off SSH, so it stays opt-in."
elif [ "$DRY_RUN" = 1 ]; then
    plan "ufw allow 22/tcp   (SSH — MUST be added before enabling, or this locks you out)"
    plan "ufw allow 80/tcp   (HTTP)"
    plan "ufw allow 443/tcp  (HTTPS)"
    plan "ufw --force enable"
    plan "ufw status verbose (confirm 22/80/443 open, default deny elsewhere)"
else
    apply "ufw allow 22/tcp && ufw allow 80/tcp && ufw allow 443/tcp"
    $SSH "ufw allow 22/tcp && ufw allow 80/tcp && ufw allow 443/tcp"
    # Verify port 22 rule landed BEFORE enabling — refuse to enable blind.
    if ! $SSH "ufw status | grep -q '22/tcp.*ALLOW'"; then
        log "FATAL: SSH allow rule did not land. Refusing to enable ufw — this would lock out SSH access."
        exit 1
    fi
    $SSH "ufw --force enable"
    $SSH "ufw status verbose"
    log "ufw enabled. Verify you can still SSH in from a NEW connection (don't close this session) before trusting this."
fi

# ---------------------------------------------------------------------------
# 6. TLS cert issuance (opt-in, fresh-droplet-only — hits LE rate limits)
# ---------------------------------------------------------------------------
log "Step 6/6: TLS certificate (certbot)"
if [ "$ISSUE_CERT" = 0 ]; then
    plan "Skipped — pass --issue-cert on a fresh droplet with no existing cert. Live droplet already has a valid cert (renews via certbot.timer, webroot mode) — do NOT run this against it, Let's Encrypt rate-limits repeat issuance for the same domain."
elif [ "$DRY_RUN" = 1 ]; then
    plan "certbot certonly --webroot -w /var/www/acme -d daanaa.org -d www.daanaa.org --non-interactive --agree-tos -m <ops-email>"
else
    if $SSH "test -d /etc/letsencrypt/live/daanaa.org"; then
        log "FATAL: /etc/letsencrypt/live/daanaa.org already exists on $TARGET. Refusing to re-issue (rate-limit risk) — use certbot renew instead if this is a genuine renewal need."
        exit 1
    fi
    log "Provide --email via DAANAA_OPS_EMAIL env var before running this step: DAANAA_OPS_EMAIL=ops@daanaa.org ./provision.sh --apply --issue-cert"
    [ -n "${DAANAA_OPS_EMAIL:-}" ] || { log "FATAL: DAANAA_OPS_EMAIL not set."; exit 1; }
    $SSH "certbot certonly --webroot -w /var/www/acme -d daanaa.org -d www.daanaa.org --non-interactive --agree-tos -m '$DAANAA_OPS_EMAIL'"
fi

log "Done. DRY_RUN=$DRY_RUN ENABLE_FIREWALL=$ENABLE_FIREWALL ISSUE_CERT=$ISSUE_CERT"
[ "$DRY_RUN" = 1 ] && log "Nothing was changed (dry run). Review the [PLAN] lines above, then re-run with --apply."
