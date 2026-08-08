#!/bin/bash
# Daily sync: export lean web DB from local → DigitalOcean droplet
# Runs after nightly pipeline. Drops ML/pipeline-only tables before sync.
set -e
LOG="[$(date '+%Y-%m-%d %H:%M:%S')]"
LEAN_DB="/tmp/daanaa_web_sync.db"
SRC_DB="/home/akbar/meritgiving/data/merit_registry.db"
# Dropped from the synced catalog: ML/pipeline-only tables PLUS all user-write
# tables (those live in daanaa_live.db on the droplet and must never be
# overwritten by the catalog sync — see daanaa_api.py LIVE_DB_PATH split).
DROP_TABLES="org_embeddings propublica_financials donate_work_queue nccs_core_2019 page_cache donation_link_evidence human_review_queue release_batches agent_job_log scoring_runs waitlist link_feedback donate_handoffs org_interest org_claims feedback analytics_daily analytics_search visit_counter"
LIVE_BACKUP_DIR="/home/akbar/meritgiving/backups"

echo "$LOG Starting lean DB export..."
rm -f "$LEAN_DB"

# Back up the droplet's live DB (user-generated data) BEFORE touching the catalog.
mkdir -p "$LIVE_BACKUP_DIR"
rsync -az -e "ssh -i /home/akbar/.ssh/daanaa_do_cron -o StrictHostKeyChecking=no" \
    root@107.170.26.8:/opt/daanaa/data/daanaa_live.db \
    "$LIVE_BACKUP_DIR/daanaa_live_$(date +%Y%m%d).db" 2>/dev/null \
    && echo "$LOG Live DB backed up to $LIVE_BACKUP_DIR" \
    || echo "$LOG WARN: live DB backup failed (continuing)"
# Keep only the last 14 daily backups
ls -1t "$LIVE_BACKUP_DIR"/daanaa_live_*.db 2>/dev/null | tail -n +15 | xargs -r rm -f

# Export lean copy
python3 -c "
import sqlite3, sys
src = sqlite3.connect('$SRC_DB')
dst = sqlite3.connect('$LEAN_DB')
src.backup(dst, pages=2000)
dst.close(); src.close()
"

# Drop large tables + vacuum
python3 -c "
import sqlite3
conn = sqlite3.connect('$LEAN_DB')
for t in '$DROP_TABLES'.split():
    conn.execute(f'DROP TABLE IF EXISTS [{t}]')
conn.execute('VACUUM')
conn.close()
"

echo "$LOG Lean DB ready. Syncing to droplet..."
rsync -az -e "ssh -i /home/akbar/.ssh/daanaa_do_cron -o StrictHostKeyChecking=no" \
    "$LEAN_DB" root@107.170.26.8:/opt/daanaa/data/merit_registry.db

echo "$LOG Restarting cloud service..."
ssh -i /home/akbar/.ssh/daanaa_do_cron root@107.170.26.8 "systemctl restart daanaa"

echo "$LOG Sync complete."
rm -f "$LEAN_DB"
