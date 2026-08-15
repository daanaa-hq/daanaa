# Droplet IaC — daanaa.org (107.170.26.8)

This directory turns "what does the droplet actually look like" from tribal
SSH knowledge into checked-in, diffable files. It was written after three
config-drift incidents this month (DNS pointed wrong three times, a
duplicate `ssl_certificate` directive broke nginx, and systemd env vars
silently drifted from what `droplet_api.py` expects). See "How this would
have prevented each incident" below.

**Ansible was checked first and rejected** — not installed locally or on the
droplet (`which ansible-playbook` → not found, both places, checked
2026-08-14). Adding it as a new dependency to run a handful of file-copy +
`systemctl` steps doesn't clear the CLAUDE.md bar ("prefer mature libraries...
justify each new dependency") when dependency-free bash does the same job
with tools every Ubuntu box already has. If the droplet fleet grows past one
host, revisit this.

## What's here

```
ops/droplet-iac/
  README.md              this file
  snapshot/               recon captured 2026-08-14 — what the droplet ACTUALLY has right now
    SNAPSHOT_2026-08-14.md   findings, ordered by severity
    nginx-T.txt              full `nginx -T` dump
    systemd-unit.txt          all daanaa-api.service* files found (live + 2 stale .bak)
    systemd-env-override.txt  the live drop-in (contains a live bug, see below)
    ufw-status.txt
    packages.txt
    listening-ports.txt
    directory-tree.txt
  files/                  canonical config — what SHOULD be deployed
    nginx/daanaa.conf         port 80: ACME challenge + proxy to :5000
    nginx/daanaa-ssl.conf     port 443: TLS + proxy to :5000
    systemd/daanaa-api.service
    systemd/env-override.conf
    ufw/rules.txt
  provision.sh            idempotent apply script (dry-run by default)
  drift-check.sh          read-only diff: live droplet vs files/ (never applies anything)
```

## How to run it

**Always dry-run first.** `provision.sh` defaults to `--dry-run`; nothing is
written to the droplet unless you pass `--apply`.

```bash
cd ops/droplet-iac

# 1. See what's different right now (safe — read-only, always)
./drift-check.sh

# 2. See what provisioning WOULD change (safe — dry run, default)
./provision.sh

# 3. Review the [PLAN] output above line by line. Then, if it looks right:
./provision.sh --apply

# Firewall and cert issuance are separately gated (see below) — neither
# runs even under --apply unless you ask for them explicitly:
./provision.sh --apply --enable-firewall     # only after confirming SSH rule lands first
./provision.sh --apply --issue-cert          # fresh droplet only — NOT the live one, it already has a cert
```

`provision.sh` does **not** restart nginx or `daanaa-api` automatically,
even under `--apply`. It writes config, validates it (`nginx -t`,
`systemctl daemon-reload`), and stops — the actual reload/restart is a
separate, deliberate command you run after reviewing the diff, following
the same pattern `scripts/ops/sync_droplet_api.sh` uses for its own restart
+ smoke test + auto-rollback.

## Drift detection (ongoing, not one-time)

`drift-check.sh` is read-only and safe to run any time, including on a
cron schedule. It exits `0` if the live droplet matches `files/`, `1` if
there's drift (so it can gate an alert). It checks:

- File-level diff of the two nginx site configs against `files/nginx/`
- File-level diff of the systemd unit and env-override drop-in
- **Structural check**: no file under `sites-enabled/` other than
  `daanaa-ssl` declares `ssl_certificate` (the exact incident #2 pattern)
- **Structural check**: no systemd drop-in sets `DAANAA_PROD` to an empty
  value (the exact incident #3 pattern, and a live bug as of this writing —
  see below)
- **Structural check**: `PRECOMPUTE_DIR` points at a directory that
  actually exists on disk (would have caught the stale `.bak` file
  referencing a nonexistent `v2` precompute directory before anyone
  restored from it)
- ufw status and the `0.0.0.0:8880` gunicorn bind are surfaced every run as
  known, tracked gaps (see snapshot findings #3) — not scored as new
  "drift" since they predate this tool, but they won't go quiet either.

Suggested cadence: run before touching droplet config by hand, after any
deploy that touches nginx/systemd, and weekly via cron for ambient
monitoring — matching the "daemon publishes its own state, watchdog reads
it" pattern in `docs/DAEMON_HEALTH_STANDARD.md` (this is the equivalent for
static infra config rather than a running daemon).

## What recon found on the live droplet (2026-08-14)

Full detail in `snapshot/SNAPSHOT_2026-08-14.md`. Headlines:

1. **A live env-var bug matching the exact incident pattern.**
   `/etc/systemd/system/daanaa-api.service.d/env-override.conf` currently
   sets `DAANAA_PROD=` (empty), silently overriding the base unit's
   `DAANAA_PROD=1` — systemd drop-ins replace same-key `Environment=`
   entries, they don't merge. Per `CLAUDE.md`, `DAANAA_PROD` gates
   HTTPS-only CSP/HSTS headers. Verified live and fixed same day — the
   production CSP header being served to real users included a dev-only
   `connect-src http://localhost:5000` directive and no `Strict-Transport-
   Security` header at all, both traced directly to `is_prod =
   bool(os.environ.get("DAANAA_PROD"))` in `droplet_api.py`. `DAANAA_PROD=`
   removed from the drop-in (base unit's `DAANAA_PROD=1` now applies).
   **Correction to the original recon:** the same drop-in's `DB_PATH` was
   flagged as pointing at a nonexistent file — true at recon time, but a
   V6.1 database rsync landed at that exact path later the same day, and
   `droplet_api.py`'s `/api/organizations/<ein>` route genuinely reads it
   live via SQLite (`get_db()`, not precompute-only as assumed). Confirmed
   via `curl https://daanaa.org/api/organizations/391214392` returning
   `merit_percentile_v6`. **`DB_PATH` is load-bearing — kept, not
   dropped.** `drift-check.sh`'s "DAANAA_PROD not blanked" structural
   check catches a repeat of the actual bug on every run going forward.

   **Second correction, this one from a live incident (2026-08-15):**
   applying the "fixed" env-override with `DAANAA_PROD` restored crashed
   every gunicorn worker and took the site down for ~45s. `droplet_api.py`
   refuses to boot with `DAANAA_PROD` truthy unless `DAANAA_CLAIM_SECRET`
   or `DAANAA_ADMIN_KEY` is also set — neither exists anywhere on this
   droplet. Rolled back immediately to the pre-incident state
   (`DAANAA_PROD=` blank). The CSP/HSTS gap described above is therefore
   **still live** — fixing it for real requires generating and deploying
   an admin/claim secret first, as a separate, independently-verified
   step, before `DAANAA_PROD` can be safely re-enabled. See the sequence
   documented in `files/systemd/env-override.conf`. Not attempted again
   without going through `provision.sh`'s dry-run first — this incident is
   exactly the failure mode the dry-run flag exists to catch, and it
   wasn't used.
2. **Two stale systemd `.bak` files, one pointing at a precompute version
   that doesn't exist** (`v2`; only `v0` and `v1` exist on disk). If ever
   restored from by hand, the service comes up broken.
3. **`ufw` is inactive**, and gunicorn is directly reachable on
   `0.0.0.0:8880` with no TLS, no nginx, and (since ufw is off) no
   firewall in front of it. Real, currently-live gap. Not auto-fixed —
   `provision.sh --enable-firewall` is opt-in, and the canonical systemd
   unit in `files/` drops the `8880` bind, but applying either to the live
   droplet is a live behavior change that needs review first.
4. **The nginx SSL config is currently clean** — no duplicate
   `ssl_certificate` directive today. A `.prev` rollback file next to
   `daanaa-ssl` in `sites-available/` suggests the incident was already
   fixed by hand; this IaC now gives future changes something to diff
   against instead of editing blind.
5. `/opt/daanaa/data/` is world-writable (777) and a few files are owned
   by an orphaned uid (1000, no matching `/etc/passwd` entry) — informational,
   not fixed (permission changes are founder-gated per `CLAUDE.md`).

## How this would have prevented each incident

- **DNS pointed to the wrong IP three times.** Out of scope for this
  directory (DNS is explicitly untouched per the task brief), but the same
  principle applies: the correct IP (`107.170.26.8`) is now the one
  constant hardcoded into `provision.sh`, `drift-check.sh`, and this
  README, all checked into git and reviewable — instead of living only in
  whoever's shell history typed it last. `feedback_droplet_ssh_ip.md` in
  project memory already captures this same fact; this directory doesn't
  replace that, it gives it a second, executable home.
- **Duplicate `ssl_certificate` directive broke nginx (discovered only via
  `journalctl` after 502s).** `provision.sh`'s nginx step refuses to
  deploy if any file under `sites-enabled/` besides `daanaa-ssl` declares
  `ssl_certificate` — checked *before* writing anything, not discovered
  after a restart fails. `drift-check.sh` runs the identical check
  read-only, any time, so "does anything else define SSL" is answerable
  in one command instead of a `grep` archaeology session after the outage
  has already happened.
- **Systemd env vars (`DB_PATH`, `DAANAA_PROD`) silently drifted.** This
  is not hypothetical — recon found it live (finding #1 above), today.
  `drift-check.sh`'s structural check for a blanked `DAANAA_PROD` catches
  exactly this pattern, and `provision.sh` refuses to deploy an
  `env-override.conf` that does it, before `daemon-reload` even runs. The
  canonical `files/systemd/env-override.conf` is also designed so this
  class of bug is structurally harder to introduce: it only sets keys the
  base unit doesn't already set, with a comment explaining why repeating a
  base-unit key is dangerous.
- **SSH timeouts forcing the DO web-console fallback.** Not directly fixed
  by config-as-code, but `provision.sh` and `drift-check.sh` both retry
  once on a failed SSH connection (same pattern as
  `scripts/ops/sync_droplet_api.sh`) and fail loudly with a clear message
  rather than hanging silently — reducing how often an SSH hiccup gets
  misread as "the droplet is broken" versus "the connection is flaky."

## Non-negotiables baked into `provision.sh`

- Defaults to dry-run; `--apply` is required for any write.
- Firewall changes require `--enable-firewall` even under `--apply`, and
  the script verifies the SSH allow-rule landed *before* calling
  `ufw enable`, refusing to proceed if it didn't (won't lock itself out).
- Cert issuance requires `--issue-cert` even under `--apply`, and refuses
  to run if `/etc/letsencrypt/live/daanaa.org` already exists (avoids
  Let's Encrypt rate-limit risk against the live domain — this is for
  fresh droplets only).
- Never restarts `nginx` or `daanaa-api` on its own — config is written
  and validated, the reload/restart is a separate manual step, consistent
  with the smoke-test-then-rollback discipline in
  `scripts/ops/sync_droplet_api.sh`.
- No destructive commands anywhere in either script (no `rm -rf`, no
  `dpkg --purge`, nothing that deletes data).
