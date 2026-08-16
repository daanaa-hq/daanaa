#!/bin/bash
# Consolidate 30+ scattered cron jobs into master_orchestrator.py
# Usage: bash scripts/consolidate_cron.sh --dry-run (to preview changes)

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$PROJECT_DIR/venv/bin/python3"
DB="$PROJECT_DIR/data/merit_registry.db"
BACKUP_CRON="/tmp/crontab_backup_$(date +%s).txt"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Daanaa Cron Consolidation${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Step 1: Create orchestrator_state table if needed
echo -e "${YELLOW}Step 1: Initialize orchestrator_state table${NC}"
$VENV -c "
import sqlite3
from pathlib import Path

db = Path('$DB')
conn = sqlite3.connect(str(db))
c = conn.cursor()

c.execute('''
    CREATE TABLE IF NOT EXISTS orchestrator_state (
        id INTEGER PRIMARY KEY,
        phase_name TEXT NOT NULL,
        run_date DATE NOT NULL,
        run_time TIME NOT NULL,
        status TEXT NOT NULL,
        duration_sec REAL NOT NULL,
        error_msg TEXT,
        UNIQUE(phase_name, run_date)
    )
''')

c.execute('CREATE INDEX IF NOT EXISTS idx_orchestrator_phase ON orchestrator_state(phase_name)')
c.execute('CREATE INDEX IF NOT EXISTS idx_orchestrator_date ON orchestrator_state(run_date)')

conn.commit()
conn.close()
print('✅ orchestrator_state table created')
" || echo -e "${RED}❌ Failed to create table${NC}"

echo ""
echo -e "${YELLOW}Step 2: Backup current crontab${NC}"
crontab -l > "$BACKUP_CRON" 2>/dev/null || true
echo "✅ Backup saved to: $BACKUP_CRON"

echo ""
echo -e "${YELLOW}Step 3: Show new cron schedule${NC}"
echo ""
cat << 'EOF'
# NEW SCHEDULE (after consolidation)
# Master orchestrator coordinates all phases
0 2 * * * cd /home/akbar/meritgiving && source venv/bin/activate && python3 scripts/master_orchestrator.py --mode full >> logs/master_orchestrator.log 2>&1

# KEEP: High-frequency monitors (not in master_orchestrator)
*/5 * * * * /home/akbar/meritgiving/scripts/log_gpu_temp.sh
*/4 * * * * /home/akbar/meritgiving/venv/bin/python3 /home/akbar/meritgiving/scripts/gpu_queue_manager.py --run >> /home/akbar/meritgiving/logs/cron.log 2>&1
*/10 * * * * source /home/akbar/meritgiving/venv/bin/activate && python3 /home/akbar/meritgiving/scripts/surge_detection_agent.py >> /home/akbar/meritgiving/logs/surge_agent.log 2>&1
*/30 * * * * /home/akbar/meritgiving/venv/bin/python3 /home/akbar/meritgiving/scripts/feedback_ingestion_agent.py >> /home/akbar/meritgiving/logs/cron.log 2>&1
0 * * * * cd /home/akbar/meritgiving && source venv/bin/activate && python3 scripts/hourly_irs_status_check.py
0 * * * * /usr/bin/python3 /home/akbar/procurement_stack/python_scripts/albert_etl.py >> /home/akbar/procurement_stack/albert_autonomous.log 2>&1

# KEEP: Email triage (independent)
30 7 * * * cd /home/akbar/meritgiving && /home/akbar/meritgiving/venv/bin/python3 -m scripts.email_agent.run --limit 50 --query 'newer_than:2d -label:daanaa/triaged' >> /home/akbar/meritgiving/logs/email_agent.log 2>&1

# KEEP: GPU night mode (separate)
0 22 * * * /home/akbar/meritgiving/scripts/gpu_night.sh start >> /home/akbar/meritgiving/logs/gpu_night.log 2>&1
0 9 * * * /home/akbar/meritgiving/scripts/gpu_night.sh stop >> /home/akbar/meritgiving/logs/gpu_night.log 2>&1

# KEEP: Weekly tasks (not suitable for daily master_orchestrator)
15 4 * * 0 /home/akbar/meritgiving/scripts/weekly_maintenance.sh
0 5 * * 1 venv/bin/python3 scripts/impact_snapshot.py >> logs/impact.log 2>&1

# RETIRE (consolidated into master_orchestrator):
# ❌ auto_ingest.py (0 */2) — now run by master_orchestrator --phase irs_ingest
# ❌ overnight_pipeline.py (orphaned) — now run by master_orchestrator --phase enrichment
# ❌ morning_brief.py (0 7) — duplicate of morning_briefing_agent.py
# ❌ morning_briefing_agent.py (0 11) — moved to master_orchestrator --phase reporting
# ❌ monthly_rescore_agent.py (0 6 1) — now run by master_orchestrator --phase scoring
# ❌ agent_outcome_analyzer.py (15 3) — optional, move to weekly
# ❌ agent_nightly_audit.md (0 3) — deprecated OpenClaw syntax, use master_orchestrator
# ❌ agent_quality.py (15 2) — optional, keep if needed separately
# ❌ agent_cause_tags.py (35 2) — optional, keep if needed separately
# ❌ Various weekly jobs: link_health, enrichment agents — run via master_orchestrator
# ❌ db_sync_from_droplet.sh (0 2) — optional, keep if needed separately
# ❌ Various GPU jobs at 9 AM (stop_embed_server conflict) — resolved via gpu_night.sh

# Optional: Keep agent jobs separate for fine-grained control:
# 15 2 * * * cd ~/meritgiving && source venv/bin/activate && python3 scripts/run_agents.py --agent quality >> logs/agent_quality.log 2>&1
# 35 2 * * * cd ~/meritgiving && source venv/bin/activate && python3 scripts/run_agents.py --agent cause_tags >> logs/agent_cause_tags.log 2>&1

EOF

echo ""
echo -e "${YELLOW}Step 4: Review and apply changes${NC}"
echo ""

if [[ "$1" == "--dry-run" ]]; then
    echo -e "${YELLOW}Dry run mode: no changes made${NC}"
    echo "To apply: bash scripts/consolidate_cron.sh --apply"
    exit 0
fi

if [[ "$1" == "--apply" ]]; then
    echo -e "${RED}⚠️  This will modify your crontab!${NC}"
    echo "Backup saved to: $BACKUP_CRON"
    echo ""
    read -p "Continue? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Applying new crontab..."
        # TODO: Use crontab -e with a temp file
        echo -e "${GREEN}✅ Manual step: Edit crontab with 'crontab -e' and apply the schedule above${NC}"
    else
        echo "Cancelled."
        exit 1
    fi
else
    echo -e "${YELLOW}Usage:${NC}"
    echo "  bash scripts/consolidate_cron.sh --dry-run    # Preview changes"
    echo "  bash scripts/consolidate_cron.sh --apply      # Apply changes (manual crontab edit)"
    exit 1
fi
