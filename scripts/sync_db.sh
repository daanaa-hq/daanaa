#!/bin/bash
# Daily sync: export lean web DB from local → DigitalOcean droplet
# Runs after nightly pipeline. Drops ML/pipeline-only tables before sync.
set -e
LOG="[$(date '+%Y-%m-%d %H:%M:%S')]"
LEAN_DB="/tmp/daanaa_web_sync.db"
SRC_DB="/home/akbar/meritgiving/data/merit_registry.db"
DROP_TABLES="org_embeddings propublica_financials donate_work_queue nccs_core_2019 page_cache donation_link_evidence human_review_queue release_batches agent_job_log link_feedback scoring_runs"

echo "$LOG Starting lean DB export..."
rm -f "$LEAN_DB"

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
rsync -az -e "ssh -i /home/akbar/.ssh/daanaa_do -o StrictHostKeyChecking=no" \
    "$LEAN_DB" root@162.243.97.179:/opt/daanaa/data/merit_registry.db

echo "$LOG Restarting cloud service..."
ssh -i /home/akbar/.ssh/daanaa_do root@162.243.97.179 "systemctl restart daanaa"

echo "$LOG Sync complete."
rm -f "$LEAN_DB"
