#!/bin/bash
# RETIRED 2026-06-09 — DO NOT USE.
# This script gzipped the LIVE WAL-mode SQLite DB and shipped it to the droplet.
# It caused: (1) DB corruption (torn snapshot of an open WAL DB, 2026-06-06), and
# (2) a 100%-full droplet lockup (2026-06-09) — the droplet serves precompute files
# and never uses merit_registry.db.
# Replacement: scripts/safe_deploy_droplet.sh (snapshot + integrity gate + link gate
# + disk guard + atomic swap). See DECISIONS.md 2026-06-09.
echo "RETIRED: use scripts/safe_deploy_droplet.sh instead. See DECISIONS.md 2026-06-09." >&2
exit 1
