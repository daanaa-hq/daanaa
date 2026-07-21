#!/usr/bin/env bash
#
# merit_safe_sync.sh
#
# Safely sync the merit-build scaffolding from this conversation into your
# existing Claude Code project, WITHOUT overwriting anything you've already
# built. Inventories your work, shows you what's new/different/same, and
# only writes after explicit per-category confirmation.
#
# USAGE:
#   1. Download merit-build.zip from this conversation to your machine
#   2. Put this script next to the zip file
#   3. chmod +x merit_safe_sync.sh
#   4. ./merit_safe_sync.sh /path/to/your/existing/merit-project
#
# EXAMPLE:
#   ./merit_safe_sync.sh /home/akbar/projects/merit
#
# WHAT IT DOES:
#   - Verifies the zip and target directory exist
#   - Creates a timestamped backup of your existing project
#   - Extracts the zip to a staging area (never on top of your work)
#   - Builds three inventories: NEW, IDENTICAL, DIFFERENT
#   - Prints a clear report
#   - Asks before touching anything in your project
#   - Logs every action it takes
#
# WHAT IT WILL NEVER DO:
#   - Overwrite a file without showing you the diff first
#   - Delete anything
#   - Move anything from your existing project
#   - Modify .git/, node_modules/, .env files, or any secret-bearing files
#
# Safe to run multiple times. Idempotent. Re-running just re-inventories.

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly ZIP_FILE="${SCRIPT_DIR}/merit-build.zip"
readonly TARGET="${1:-}"
readonly TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
readonly STAGING_DIR="${SCRIPT_DIR}/.merit-staging-${TIMESTAMP}"
readonly LOG_FILE="${SCRIPT_DIR}/merit-sync-${TIMESTAMP}.log"

# Files we will NEVER touch in your project under any circumstances
readonly PROTECTED_PATTERNS=(
  "*/.git/*"
  "*/.git"
  "*/node_modules/*"
  "*/node_modules"
  "*/.env"
  "*/.env.*"
  "*/.envrc"
  "*/venv/*"
  "*/venv"
  "*/.venv/*"
  "*/.venv"
  "*/__pycache__/*"
  "*/dist/*"
  "*/build/*"
  "*/.next/*"
  "*.duckdb"
  "*.sqlite"
  "*.db"
  "*.key"
  "*.pem"
  "*.crt"
)

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly BOLD='\033[1m'
readonly NC='\033[0m'

# ============================================================================
# Helpers
# ============================================================================

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

info() {
  echo -e "${BLUE}ℹ${NC}  $*" | tee -a "$LOG_FILE"
}

success() {
  echo -e "${GREEN}✓${NC}  $*" | tee -a "$LOG_FILE"
}

warn() {
  echo -e "${YELLOW}⚠${NC}  $*" | tee -a "$LOG_FILE"
}

error() {
  echo -e "${RED}✗${NC}  $*" | tee -a "$LOG_FILE" >&2
}

header() {
  echo "" | tee -a "$LOG_FILE"
  echo -e "${BOLD}━━━ $* ━━━${NC}" | tee -a "$LOG_FILE"
  echo "" | tee -a "$LOG_FILE"
}

confirm() {
  local prompt="$1"
  local response
  echo "" >&2
  read -r -p "$(echo -e "${YELLOW}?${NC} ${prompt} [y/N]: ")" response
  case "$response" in
    [yY]|[yY][eE][sS]) return 0 ;;
    *) return 1 ;;
  esac
}

is_protected() {
  local path="$1"
  for pattern in "${PROTECTED_PATTERNS[@]}"; do
    # shellcheck disable=SC2053
    if [[ "$path" == $pattern ]]; then
      return 0
    fi
  done
  return 1
}

# ============================================================================
# Validation
# ============================================================================

validate_inputs() {
  header "Validating inputs"

  if [[ -z "$TARGET" ]]; then
    error "Usage: $0 <path-to-your-existing-project>"
    error "Example: $0 /home/akbar/projects/merit"
    exit 1
  fi

  if [[ ! -d "$TARGET" ]]; then
    error "Target directory does not exist: $TARGET"
    error "Create it first, or point to your existing Claude Code project root."
    exit 1
  fi

  if [[ ! -f "$ZIP_FILE" ]]; then
    error "Zip file not found: $ZIP_FILE"
    error "Place merit-build.zip in the same directory as this script."
    exit 1
  fi

  if ! command -v unzip >/dev/null 2>&1; then
    error "unzip command not found. Install with: sudo apt install unzip"
    exit 1
  fi

  success "Target: $TARGET"
  success "Zip:    $ZIP_FILE"
  success "Log:    $LOG_FILE"
}

# ============================================================================
# Backup
# ============================================================================

create_backup() {
  header "Creating safety backup"

  local backup_dir="${TARGET}.backup-${TIMESTAMP}"

  info "Backing up your existing project before any changes..."
  info "Source: $TARGET"
  info "Backup: $backup_dir"

  if ! confirm "Proceed with backup? (Required to continue)"; then
    error "Backup declined. Cannot proceed safely. Exiting."
    exit 1
  fi

  # Backup via cp + find, excluding protected/heavy directories
  mkdir -p "$backup_dir"
  (cd "$TARGET" && find . \
    -not -path '*/.git*' \
    -not -path '*/node_modules*' \
    -not -path '*/venv*' \
    -not -path '*/.venv*' \
    -not -path '*/__pycache__*' \
    -not -path '*/dist/*' \
    -not -path '*/build/*' \
    -not -path '*/.next/*' \
    -not -name '*.duckdb' \
    -not -name '*.sqlite' \
    -print0 | while IFS= read -r -d '' item; do
      if [[ -d "$item" ]]; then
        mkdir -p "$backup_dir/$item"
      elif [[ -f "$item" ]]; then
        mkdir -p "$backup_dir/$(dirname "$item")"
        cp -p "$item" "$backup_dir/$item"
      fi
    done)

  success "Backup created at: $backup_dir"
  echo "$backup_dir" > "${SCRIPT_DIR}/.last-backup-${TIMESTAMP}"
}

# ============================================================================
# Extract to staging
# ============================================================================

extract_to_staging() {
  header "Extracting zip to staging (NOT touching your project)"

  mkdir -p "$STAGING_DIR"
  info "Staging dir: $STAGING_DIR"

  unzip -q "$ZIP_FILE" -d "$STAGING_DIR"

  # Find the actual root inside the zip (it's "merit-build/")
  local extracted_root
  extracted_root="$(find "$STAGING_DIR" -mindepth 1 -maxdepth 1 -type d | head -1)"

  if [[ -z "$extracted_root" ]]; then
    error "Could not find extracted contents in $STAGING_DIR"
    exit 1
  fi

  success "Extracted to: $extracted_root"
  echo "$extracted_root"
}

# ============================================================================
# Build inventory
# ============================================================================

build_inventory() {
  local staging_root="$1"

  header "Inventorying files (no changes yet)"

  local new_files=()
  local identical_files=()
  local different_files=()
  local protected_skipped=()

  # Walk every file in the staging area
  while IFS= read -r staging_file; do
    # Relative path inside the bundle
    local rel_path="${staging_file#$staging_root/}"
    local target_file="$TARGET/$rel_path"

    # Skip protected patterns
    if is_protected "$target_file"; then
      protected_skipped+=("$rel_path")
      continue
    fi

    if [[ ! -e "$target_file" ]]; then
      new_files+=("$rel_path")
    elif cmp -s "$staging_file" "$target_file"; then
      identical_files+=("$rel_path")
    else
      different_files+=("$rel_path")
    fi
  done < <(find "$staging_root" -type f)

  # Write inventories to files for processing
  printf '%s\n' "${new_files[@]:-}"        > "${SCRIPT_DIR}/.inventory-new-${TIMESTAMP}.txt"
  printf '%s\n' "${identical_files[@]:-}"  > "${SCRIPT_DIR}/.inventory-same-${TIMESTAMP}.txt"
  printf '%s\n' "${different_files[@]:-}"  > "${SCRIPT_DIR}/.inventory-diff-${TIMESTAMP}.txt"
  printf '%s\n' "${protected_skipped[@]:-}" > "${SCRIPT_DIR}/.inventory-skip-${TIMESTAMP}.txt"

  # Report
  echo ""
  echo -e "${BOLD}Inventory results:${NC}"
  echo -e "  ${GREEN}NEW${NC}        (safe to add):       ${#new_files[@]} files"
  echo -e "  ${BLUE}IDENTICAL${NC}  (skip, already match): ${#identical_files[@]} files"
  echo -e "  ${YELLOW}DIFFERENT${NC}  (need your review):   ${#different_files[@]} files"
  echo -e "  ${RED}PROTECTED${NC}  (never touched):       ${#protected_skipped[@]} files"
  echo ""

  log "Inventory: NEW=${#new_files[@]} SAME=${#identical_files[@]} DIFF=${#different_files[@]} SKIP=${#protected_skipped[@]}"
}

# ============================================================================
# Process NEW files (safe to add)
# ============================================================================

process_new_files() {
  local staging_root="$1"
  local new_list="${SCRIPT_DIR}/.inventory-new-${TIMESTAMP}.txt"

  if [[ ! -s "$new_list" ]]; then
    info "No new files to add."
    return 0
  fi

  header "NEW files (would be added to your project)"

  echo -e "${BOLD}First 30 files preview:${NC}"
  head -30 "$new_list" | sed 's/^/  + /'

  local total
  total=$(wc -l < "$new_list" | tr -d ' ')
  if (( total > 30 )); then
    echo "  ... and $(( total - 30 )) more (see $new_list)"
  fi

  echo ""
  info "Full list saved to: $new_list"
  echo ""

  if confirm "Add these ${total} NEW files to your project?"; then
    local count=0
    while IFS= read -r rel_path; do
      [[ -z "$rel_path" ]] && continue
      local src="$staging_root/$rel_path"
      local dst="$TARGET/$rel_path"
      mkdir -p "$(dirname "$dst")"
      cp "$src" "$dst"
      count=$((count + 1))
    done < "$new_list"
    success "Added $count new files"
  else
    warn "Skipped adding new files (your choice)"
  fi
}

# ============================================================================
# Process DIFFERENT files (need human review)
# ============================================================================

process_different_files() {
  local staging_root="$1"
  local diff_list="${SCRIPT_DIR}/.inventory-diff-${TIMESTAMP}.txt"

  if [[ ! -s "$diff_list" ]]; then
    info "No files differ from yours. Nothing to review."
    return 0
  fi

  header "DIFFERENT files (your work conflicts with the bundle)"

  echo -e "${BOLD}These files exist in BOTH places with different content.${NC}"
  echo -e "${BOLD}I will NOT overwrite any of these automatically.${NC}"
  echo ""

  local diffs_dir="${SCRIPT_DIR}/merit-diffs-${TIMESTAMP}"
  mkdir -p "$diffs_dir"

  echo -e "${BOLD}Generating side-by-side diffs to: $diffs_dir${NC}"
  echo ""

  local count=0
  while IFS= read -r rel_path; do
    [[ -z "$rel_path" ]] && continue
    local src="$staging_root/$rel_path"
    local dst="$TARGET/$rel_path"
    # Generate diff
    local diff_file="$diffs_dir/${rel_path//\//__}.diff"
    mkdir -p "$(dirname "$diff_file")"
    diff -u "$dst" "$src" > "$diff_file" 2>/dev/null || true
    echo "  ≠ $rel_path"
    count=$((count + 1))
  done < "$diff_list"

  echo ""
  success "Generated $count diff files in: $diffs_dir"
  echo ""
  info "Review each diff and decide manually:"
  info "  - Keep your version: do nothing"
  info "  - Take bundle version: cp from staging to your project"
  info "  - Merge: edit your file using bundle as reference"
  echo ""
  info "Staging area kept for reference at: $staging_root"
  info "(Delete it when done: rm -rf $STAGING_DIR)"
}

# ============================================================================
# Summary
# ============================================================================

print_summary() {
  header "Sync summary"

  local backup_path
  backup_path="$(cat "${SCRIPT_DIR}/.last-backup-${TIMESTAMP}" 2>/dev/null || echo "(none)")"

  echo "Backup of your original project: $backup_path"
  echo "Staging area (bundle contents):  $STAGING_DIR"
  echo "Full log of this run:            $LOG_FILE"
  echo ""
  echo "Inventories:"
  echo "  New files added:     ${SCRIPT_DIR}/.inventory-new-${TIMESTAMP}.txt"
  echo "  Identical (skipped): ${SCRIPT_DIR}/.inventory-same-${TIMESTAMP}.txt"
  echo "  Different (review):  ${SCRIPT_DIR}/.inventory-diff-${TIMESTAMP}.txt"
  echo "  Protected (skipped): ${SCRIPT_DIR}/.inventory-skip-${TIMESTAMP}.txt"
  echo ""

  if [[ -d "${SCRIPT_DIR}/merit-diffs-${TIMESTAMP}" ]]; then
    echo "Diffs for conflicting files: ${SCRIPT_DIR}/merit-diffs-${TIMESTAMP}/"
    echo ""
  fi

  success "Done. Nothing was overwritten without your explicit yes."
  echo ""
  echo "Next steps:"
  echo "  1. Review the diff files for any DIFFERENT entries"
  echo "  2. Manually merge anything worth keeping from the bundle"
  echo "  3. When confident, delete the staging dir and backup"
  echo "  4. git status / git diff in your project to see what changed"
}

# ============================================================================
# Main
# ============================================================================

main() {
  echo ""
  echo -e "${BOLD}MERIT Safe Sync${NC}"
  echo "================"
  echo ""
  echo "This script will NEVER:"
  echo "  - Overwrite a file you've already written"
  echo "  - Touch .git, node_modules, venv, .env, or secrets"
  echo "  - Delete anything"
  echo "  - Skip the backup step"
  echo ""

  validate_inputs
  create_backup

  local staging_root
  staging_root="$(extract_to_staging | tail -1)"

  build_inventory "$staging_root"

  echo ""
  if confirm "Proceed to add NEW files and generate diffs for DIFFERENT files?"; then
    process_new_files "$staging_root"
    process_different_files "$staging_root"
    print_summary
  else
    warn "Sync cancelled. Nothing was changed."
    info "Staging area kept for reference: $staging_root"
    info "Backup kept just in case: $(cat "${SCRIPT_DIR}/.last-backup-${TIMESTAMP}" 2>/dev/null || echo unknown)"
  fi
}

main "$@"
