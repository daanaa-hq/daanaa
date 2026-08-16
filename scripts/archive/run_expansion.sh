#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# MERIT Worker E: e-Postcard Expansion — Bash Wrapper
# ═══════════════════════════════════════════════════════════════════════════════
# 
# Purpose:
#   Orchestrates the e-Postcard (990-N) expansion pipeline by running the
#   Python expansion script with proper environment setup and logging.
#
# Usage:
#   chmod +x scripts/run_expansion.sh
#   ./scripts/run_expansion.sh
#
# Output:
#   - Appends ~20,000–50,000 stub records to master_orgs_clean.csv
#   - Generates report: data/reports/epostcard_expansion_YYYY-MM-DD.csv
#   - Saves execution log: data/reports/epostcard_expansion_YYYY-MM-DD.log
# ═══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

# ── Configuration ───────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$PROJECT_DIR/data"
REPORTS_DIR="$DATA_DIR/reports"
PYTHON_SCRIPT="$SCRIPT_DIR/expand_epostcard.py"

# Required data files
INDEX_2020="$DATA_DIR/index_2020.json"
INDEX_2022="$DATA_DIR/index_2022.json"
BMF_FILE="$DATA_DIR/bmf.csv"
MASTER_FILE="$DATA_DIR/master_orgs_clean.csv"

# Timestamp for this run
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
RUN_LOG="$REPORTS_DIR/expansion_run_$TIMESTAMP.log"

# ── ANSI Colors ─────────────────────────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ── Helper Functions ────────────────────────────────────────────────────────

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$RUN_LOG"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1" | tee -a "$RUN_LOG"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$RUN_LOG"
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1" | tee -a "$RUN_LOG"
}

log_header() {
    echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}${BOLD}  $1${NC}"
    echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════════════════════${NC}"
}

# ── Pre-flight Checks ───────────────────────────────────────────────────────

check_file() {
    local file="$1"
    local label="$2"
    if [[ -f "$file" ]]; then
        local size
        size=$(du -h "$file" | cut -f1)
        log_success "$label found ($size): $file"
        return 0
    else
        log_warn "$label NOT found: $file"
        return 1
    fi
}

check_python() {
    if command -v python3 &> /dev/null; then
        local version
        version=$(python3 --version)
        log_success "Python available: $version"
        return 0
    elif command -v python &> /dev/null; then
        local version
        version=$(python --version)
        log_success "Python available: $version"
        return 0
    else
        log_error "Python 3 is required but not installed"
        exit 1
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════════

mkdir -p "$REPORTS_DIR"

echo -e "\n" > "$RUN_LOG"

log_header "MERIT Worker E: e-Postcard (990-N) Expansion"
echo -e "${BOLD}Started:${NC} $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$RUN_LOG"
echo "" | tee -a "$RUN_LOG"

# ── Step 1: Environment Checks ──────────────────────────────────────────────

log_header "STEP 1: Pre-flight Checks"

check_python

log_info "Project directory: $PROJECT_DIR"
log_info "Data directory:    $DATA_DIR"
log_info "Reports directory: $REPORTS_DIR"

echo "" | tee -a "$RUN_LOG"

# Check required source files
MISSING=0

check_file "$INDEX_2020" "Index 2020" || ((MISSING++))
check_file "$INDEX_2022" "Index 2022" || ((MISSING++))
check_file "$BMF_FILE"   "BMF CSV"    || ((MISSING++))

# Master file may not exist yet (first run)
if [[ -f "$MASTER_FILE" ]]; then
    check_file "$MASTER_FILE" "Master orgs file"
else
    log_warn "Master orgs file not found (will be created): $MASTER_FILE"
fi

# Check Python script
check_file "$PYTHON_SCRIPT" "Expansion script"

echo "" | tee -a "$RUN_LOG"

if [[ $MISSING -gt 0 ]]; then
    log_warn "$MISSING required source file(s) missing. Continuing anyway..."
    log_warn "The script will process whatever data is available."
    echo "" | tee -a "$RUN_LOG"
fi

# ── Step 2: Backup Existing Master ──────────────────────────────────────────

log_header "STEP 2: Backup"

if [[ -f "$MASTER_FILE" ]]; then
    BACKUP_FILE="$DATA_DIR/master_orgs_clean_backup_$TIMESTAMP.csv"
    cp "$MASTER_FILE" "$BACKUP_FILE"
    log_success "Master file backed up to: $BACKUP_FILE"
else
    log_info "No existing master file to backup"
fi

echo "" | tee -a "$RUN_LOG"

# ── Step 3: Run Expansion ───────────────────────────────────────────────────

log_header "STEP 3: Running e-Postcard Expansion"

log_info "Executing: $PYTHON_SCRIPT"
log_info "Log file:  $RUN_LOG"
echo "" | tee -a "$RUN_LOG"

# Run the Python script and capture output
if python3 "$PYTHON_SCRIPT" 2>&1 | tee -a "$RUN_LOG"; then
    EXIT_CODE=${PIPESTATUS[0]}
else
    EXIT_CODE=${PIPESTATUS[0]}
fi

echo "" | tee -a "$RUN_LOG"

# ── Step 4: Results ─────────────────────────────────────────────────────────

log_header "STEP 4: Results"

if [[ $EXIT_CODE -eq 0 ]]; then
    log_success "Expansion completed successfully (exit code: $EXIT_CODE)"
    
    # Show generated files
    echo "" | tee -a "$RUN_LOG"
    log_info "Generated files:"
    
    # Find today's report files
    TODAY=$(date +%Y-%m-%d)
    REPORT_COUNT=0
    
    for f in "$REPORTS_DIR"/epostcard_expansion_*"$TODAY"*; do
        if [[ -f "$f" ]]; then
            local size
            size=$(du -h "$f" | cut -f1)
            echo -e "  ${GREEN}✓${NC} $(basename "$f") ($size)" | tee -a "$RUN_LOG"
            ((REPORT_COUNT++))
        fi
    done
    
    if [[ -f "$MASTER_FILE" ]]; then
        local master_size master_lines
        master_size=$(du -h "$MASTER_FILE" | cut -f1)
        master_lines=$(wc -l < "$MASTER_FILE" | tr -d ' ')
        echo -e "  ${GREEN}✓${NC} $(basename "$MASTER_FILE") ($master_size, $master_lines lines)" | tee -a "$RUN_LOG"
    fi
    
    echo "" | tee -a "$RUN_LOG"
    log_success "e-Postcard expansion pipeline finished at $(date '+%H:%M:%S')"
    
else
    log_error "Expansion failed (exit code: $EXIT_CODE)"
    log_error "Check the log file for details: $RUN_LOG"
    exit $EXIT_CODE
fi

# ── Step 5: Summary ─────────────────────────────────────────────────────────

log_header "SUMMARY"
echo -e "${BOLD}Started:${NC}  $TIMESTAMP" | tee -a "$RUN_LOG"
echo -e "${BOLD}Finished:${NC} $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$RUN_LOG"
echo -e "${BOLD}Log file:${NC} $RUN_LOG" | tee -a "$RUN_LOG"
echo "" | tee -a "$RUN_LOG"
log_info "Next steps:"
echo -e "  1. Review the expansion report in $REPORTS_DIR" | tee -a "$RUN_LOG"
echo -e "  2. Validate the updated master_orgs_clean.csv" | tee -a "$RUN_LOG"
echo -e "  3. Proceed to Worker F (Financial Data Enrichment) if applicable" | tee -a "$RUN_LOG"
echo "" | tee -a "$RUN_LOG"

exit 0
