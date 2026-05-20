#!/usr/bin/env bash
# Waits for ntee_tagger screen to exit, then launches Phase 2 jobs.
# Run in its own screen session: screen -dmS phase2_watch scripts/phase2_launcher.sh

LOGDIR="$HOME/meritgiving/logs"
log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOGDIR/phase2_launcher.log"; }

log "Phase 2 launcher started — waiting for ntee_tagger to finish..."

# Poll until ntee_tagger screen session is gone
while screen -ls 2>/dev/null | grep -q "ntee_tagger"; do
    sleep 60
done

log "ntee_tagger finished. Launching Phase 2 jobs..."

cd "$HOME/meritgiving" || exit 1
source venv/bin/activate

# 2a. Merit scoring + percentile rebuild
screen -dmS merit_scorer bash -c "
  source $HOME/meritgiving/venv/bin/activate &&
  cd $HOME/meritgiving &&
  python3 -u api/merit_scorer_v3_3.py \
    --output data/scoring_run_\$(date +%Y%m%d).csv \
    >> $LOGDIR/merit_scorer.log 2>&1 &&
  python3 -u scripts/build_percentiles.py \
    >> $LOGDIR/build_percentiles.log 2>&1
  echo '[merit_scorer done]' >> $LOGDIR/merit_scorer.log
"
log "merit_scorer screen launched"

# 2b. Cause tags (picks up new missions pp_backfill has added)
screen -dmS agent_cause_tags bash -c "
  source $HOME/meritgiving/venv/bin/activate &&
  cd $HOME/meritgiving &&
  python3 -u scripts/run_agents.py --agent cause_tags --force \
    >> $LOGDIR/agent_cause_tags.log 2>&1
  echo '[cause_tags done]' >> $LOGDIR/agent_cause_tags.log
"
log "cause_tags screen launched"

# 2c. Quality report
screen -dmS agent_quality bash -c "
  source $HOME/meritgiving/venv/bin/activate &&
  cd $HOME/meritgiving &&
  python3 -u scripts/run_agents.py --agent quality --force \
    >> $LOGDIR/agent_quality.log 2>&1
  echo '[quality done]' >> $LOGDIR/agent_quality.log
"
log "quality screen launched"

log "Phase 2 launch complete. Current screens:"
screen -ls | tee -a "$LOGDIR/phase2_launcher.log"
