#!/bin/bash
"""
Post-Phase-2 Workflow — Score, Index, and Deploy (Optimized)

Optimizations:
- Monitoring: Only for processes >10 min, checks at 20%/40%/60%/80%/100%
- Parallel: FTS rebuild + research snapshot run in parallel (independent, no conflicts)
- Hardware: GPU for scoring, parallel CPU for FTS batches
- Zero rework: Strict dependency ordering (score → load → {FTS || snapshot} → deploy)

Usage:
    bash scripts/post_phase2_workflow.sh
    bash scripts/post_phase2_workflow.sh --dry-run
    bash scripts/post_phase2_workflow.sh --skip-deploy
"""

set -e

cd /home/akbar/meritgiving
source venv/bin/activate

SCRIPTS=scripts
LOGS=logs
DATA=data

mkdir -p $LOGS $DATA/tmp

LOG_FILE="$LOGS/post_phase2.log"
SCORES_FILE="scores_v4_0_$(date +%Y%m%d_%H%M%S).json"
SKIP_DEPLOY=0
DRY_RUN=0

for arg in "$@"; do
    case "$arg" in
        --skip-deploy) SKIP_DEPLOY=1 ;;
        --dry-run) DRY_RUN=1 ;;
    esac
done

log() {
    msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$msg"
    echo "$msg" >> "$LOG_FILE"
}

# Validation: check scores loaded correctly
validate_scores_loaded() {
    log "  Validating scores..."
    sqlite3 "$DATA/merit_registry.db" <<EOF
.mode line
SELECT
    (SELECT COUNT(*) FROM registry_enriched WHERE merit_score IS NULL) as null_scores,
    (SELECT COUNT(*) FROM registry_enriched WHERE merit_score < 0 OR merit_score > 100) as out_of_range,
    (SELECT COUNT(*) FROM registry_enriched WHERE merit_score IS NOT NULL) as total_scored,
    ROUND(AVG(merit_score), 2) as avg_score,
    ROUND(MIN(merit_score), 2) as min_score,
    ROUND(MAX(merit_score), 2) as max_score;
EOF
}

# Validation: check hidden gems re-flagged correctly
validate_hidden_gems() {
    log "  Validating hidden gems re-flagging..."
    sqlite3 "$DATA/merit_registry.db" <<EOF
.mode line
SELECT
    (SELECT COUNT(*) FROM registry_enriched WHERE is_hidden_gem=1) as total_gems,
    (SELECT COUNT(*) FROM registry_enriched WHERE is_hidden_gem=1 AND merit_score >= 85 AND total_revenue > 0 AND total_revenue < 500000) as valid_gems,
    (SELECT COUNT(*) FROM registry_enriched WHERE is_hidden_gem=1 AND (merit_score < 85 OR total_revenue <= 0 OR total_revenue >= 500000)) as invalid_gems;
EOF
}

# Validation: check specific org (471694019)
validate_org_471694019() {
    log "  Checking org 471694019 (test case)..."
    sqlite3 "$DATA/merit_registry.db" "SELECT EIN, merit_score, total_revenue, is_hidden_gem, CASE WHEN merit_score >= 85 AND total_revenue > 0 AND total_revenue < 500000 THEN 'correct' ELSE 'incorrect' END as status FROM registry_enriched WHERE EIN = '471694019';"
}

# Monitored process: checks at 20%/40%/60%/80%/100%
# Usage: monitor_long_process <name> <log_file> <total_items_or_time>
monitor_progress() {
    local name=$1
    local log_file=$2
    local expected_duration=$3  # in seconds (for scoring: ~7200-10800)

    if [ $expected_duration -lt 600 ]; then
        # Skip monitoring for processes < 10 min
        return 0
    fi

    local check_interval=$((expected_duration / 5))  # 5 checkpoints = 20% each
    local start_time=$(date +%s)

    log "  Monitoring $name (expected ~${expected_duration}s, checking every ${check_interval}s at 20%/40%/60%/80%/100%)"

    for pct in 20 40 60 80 100; do
        target_time=$((start_time + (expected_duration * pct / 100)))
        now=$(date +%s)

        if [ $now -lt $target_time ]; then
            sleep $((target_time - now))
        fi

        last_line=$(tail -1 "$log_file" 2>/dev/null || echo "")
        log "  [$pct%] Last output: ${last_line:0:100}"

        # Check for errors
        if tail -20 "$log_file" 2>/dev/null | grep -qiE "error|exception|traceback|killed"; then
            log "  ❌ DETECTED ERROR — aborting"
            return 1
        fi
    done

    return 0
}

log "==============================================="
log "Post-Phase-2 Workflow Started (Optimized)"
log "==============================================="
log "SCORES_FILE: $SCORES_FILE"
log "SKIP_DEPLOY: $SKIP_DEPLOY"
log "DRY_RUN: $DRY_RUN"
log "Hardware: GPU for scoring, parallel CPU for FTS/snapshot"

if [ $DRY_RUN -eq 1 ]; then
    log "DRY-RUN: showing execution plan"
    log ""
    log "1. python3 $SCRIPTS/merit_scorer_v4_0.py --output $SCORES_FILE"
    log "   [Monitor: 20%/40%/60%/80%/100%, ~2-3 hours]"
    log ""
    log "2. python3 $SCRIPTS/load_v4_scores.py $SCORES_FILE"
    log "   [No monitoring, ~5 min]"
    log ""
    log "3. PARALLEL (after stage 2):"
    log "   3a. python3 $SCRIPTS/build_fts_index.py --rebuild"
    log "       [Monitor: 20%/40%/60%/80%/100%, ~10 min]"
    log "   3b. python3 $SCRIPTS/export_research_snapshot.py"
    log "       [No monitoring, ~2 min]"
    log ""
    log "4. bash $SCRIPTS/safe_deploy_droplet.sh"
    log "   [Depends on 3a+3b, ~20 min]"
    log ""
    exit 0
fi

# ────────────────────────────────────────────────────────────────
# Stage 1: Score all orgs with merit_scorer_v4_0
# Expected: ~2-3 hours
# ────────────────────────────────────────────────────────────────
if [ ! -f "$SCORES_FILE" ]; then
    log "Stage 1: Scoring 1.97M orgs with merit_scorer_v4_0 (GPU, ~2-3 hours)"
    SCORER_LOG="$LOGS/scorer_stage1.log"
    python3 "$SCRIPTS/merit_scorer_v4_0.py" --output "$SCORES_FILE" > "$SCORER_LOG" 2>&1 &
    SCORER_PID=$!

    # Monitor: 20%/40%/60%/80%/100% over ~2.5 hours (9000 seconds)
    monitor_progress "Scorer" "$SCORER_LOG" 9000
    if [ $? -ne 0 ]; then
        kill $SCORER_PID 2>/dev/null || true
        log "❌ Scoring failed"
        exit 1
    fi

    wait $SCORER_PID
    if [ $? -ne 0 ]; then
        log "❌ Scorer process exited with error"
        exit 1
    fi

    log "✅ Stage 1 complete: $SCORES_FILE"
else
    log "Stage 1: SKIPPED (scores already exist at $SCORES_FILE)"
fi

# ────────────────────────────────────────────────────────────────
# Stage 2: Load scores into registry_enriched
# Expected: ~5 min (no monitoring needed)
# ────────────────────────────────────────────────────────────────
log "Stage 2: Loading v4.0 scores into registry_enriched (~5 min)"
python3 "$SCRIPTS/load_v4_scores.py" "$SCORES_FILE" 2>&1 | tee -a "$LOG_FILE"
log "✅ Stage 2 complete: scores loaded"

log "Stage 2 QA: Validating score quality..."
VALIDATION=$(validate_scores_loaded)
echo "$VALIDATION" | tee -a "$LOG_FILE"
NULL_SCORES=$(echo "$VALIDATION" | grep "null_scores" | awk '{print $NF}')
OUT_OF_RANGE=$(echo "$VALIDATION" | grep "out_of_range" | awk '{print $NF}')
if [ "$NULL_SCORES" -gt 0 ] || [ "$OUT_OF_RANGE" -gt 0 ]; then
    log "❌ VALIDATION FAILED: $NULL_SCORES null scores, $OUT_OF_RANGE out-of-range scores"
    exit 1
fi
log "✅ Score validation passed"

# ────────────────────────────────────────────────────────────────
# Stage 2b: Re-flag hidden gems with corrected logic
# Expected: ~2 min (after loading new scores)
# ────────────────────────────────────────────────────────────────
log "Stage 2b: Re-flagging hidden gems with corrected definition (total_revenue > 0)"
python3 "$SCRIPTS/flag_hidden_gems.py" --apply 2>&1 | tee -a "$LOG_FILE"
log "✅ Hidden gems re-flagged: corrected to exclude zero-revenue orgs"

log "Stage 2b QA: Validating hidden gems logic..."
GEM_VALIDATION=$(validate_hidden_gems)
echo "$GEM_VALIDATION" | tee -a "$LOG_FILE"
TOTAL_GEMS=$(echo "$GEM_VALIDATION" | grep "total_gems" | awk '{print $NF}')
VALID_GEMS=$(echo "$GEM_VALIDATION" | grep "valid_gems" | awk '{print $NF}')
INVALID_GEMS=$(echo "$GEM_VALIDATION" | grep "invalid_gems" | awk '{print $NF}')
if [ "$INVALID_GEMS" -gt 0 ]; then
    log "❌ VALIDATION FAILED: $INVALID_GEMS hidden gems violate criteria (should be 0)"
    exit 1
fi
log "✅ Hidden gems validation passed: $TOTAL_GEMS gems, all meet criteria"

log "Stage 2b spot-check: Org 471694019..."
validate_org_471694019 | tee -a "$LOG_FILE"

# ────────────────────────────────────────────────────────────────
# Stage 3: PARALLEL — FTS rebuild + Research snapshot
# FTS: ~10 min, monitor at 20%/40%/60%/80%/100%
# Snapshot: ~2 min, no monitoring
# ────────────────────────────────────────────────────────────────
log "Stage 3: PARALLEL execution"
log "  3a. Building FTS5 search index (~10 min, CPU)"
log "  3b. Exporting research snapshot (~2 min, light)"

FTS_LOG="$LOGS/fts_stage3a.log"
SNAP_LOG="$LOGS/snapshot_stage3b.log"

# Start FTS rebuild in background
python3 "$SCRIPTS/build_fts_index.py" --rebuild > "$FTS_LOG" 2>&1 &
FTS_PID=$!

# Start snapshot export in background (will finish first)
MERIT_DB_PATH="$DATA/merit_registry.db" python3 "$SCRIPTS/export_research_snapshot.py" > "$SNAP_LOG" 2>&1 &
SNAP_PID=$!

# Monitor FTS: 20%/40%/60%/80%/100% over ~600 seconds (10 min)
log "  Monitoring FTS (expected ~600s, checking at 20%/40%/60%/80%/100%)"
monitor_progress "FTS Index" "$FTS_LOG" 600
if [ $? -ne 0 ]; then
    kill $FTS_PID $SNAP_PID 2>/dev/null || true
    log "❌ FTS rebuild failed"
    exit 1
fi

# Wait for both to complete
log "  Waiting for FTS and snapshot to complete..."
wait $FTS_PID
FTS_EXIT=$?

wait $SNAP_PID
SNAP_EXIT=$?

if [ $FTS_EXIT -ne 0 ]; then
    log "❌ FTS rebuild failed"
    exit 1
fi

if [ $SNAP_EXIT -ne 0 ]; then
    log "❌ Snapshot export failed"
    exit 1
fi

log "✅ Stage 3 complete: FTS rebuilt + snapshot exported"

# ────────────────────────────────────────────────────────────────
# Stage 4: Deploy to droplet (depends on stage 3 completion)
# Expected: ~20 min
# ────────────────────────────────────────────────────────────────
if [ $SKIP_DEPLOY -eq 0 ]; then
    log "Stage 4: Deploying to droplet (sandboxed, ~20 min)"
    bash "$SCRIPTS/safe_deploy_droplet.sh" 2>&1 | tee -a "$LOG_FILE"
    if [ $? -ne 0 ]; then
        log "❌ Deploy failed"
        exit 1
    fi
    log "✅ Stage 4 complete: droplet deployed"

    log "Stage 4 QA: Verifying droplet API..."
    sleep 5  # Give droplet a moment to stabilize

    # Test /api/stats endpoint
    STATS=$(curl -s http://192.168.1.73:5000/api/stats 2>/dev/null || echo "FAILED")
    if echo "$STATS" | grep -q "total_orgs"; then
        ORG_COUNT=$(echo "$STATS" | grep -o '"total_orgs":[0-9]*' | cut -d: -f2)
        log "✅ Droplet API responding: $ORG_COUNT orgs"
        echo "$STATS" | head -20 | tee -a "$LOG_FILE"
    else
        log "⚠️  Droplet API not responding yet (may need a moment)"
    fi

    log "Spot-check droplet org 471694019..."
    ORG_DATA=$(curl -s "http://192.168.1.73:5000/api/org/471694019" 2>/dev/null || echo "FAILED")
    if echo "$ORG_DATA" | grep -q "merit_score"; then
        SCORE=$(echo "$ORG_DATA" | grep -o '"merit_score":[0-9.]*' | cut -d: -f2)
        GEM=$(echo "$ORG_DATA" | grep -o '"is_hidden_gem":[a-z]*' | cut -d: -f2)
        log "✅ Org 471694019: score=$SCORE, hidden_gem=$GEM"
    else
        log "⚠️  Org API endpoint not yet available"
    fi
else
    log "Stage 4: SKIPPED (--skip-deploy)"
fi

log "==============================================="
log "✅ Post-Phase-2 Workflow Complete"
log "==============================================="
log "Verify daanaa.org shows updated data:"
log "  curl http://localhost:5000/api/stats"
log "  curl https://daanaa.org/api/stats"
log "==============================================="
