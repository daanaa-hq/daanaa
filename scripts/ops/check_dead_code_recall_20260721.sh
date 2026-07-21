#!/bin/bash
# One-time recall check for archive/dead_code_20260721/ (see that folder's
# README + DECISIONS.md 2026-07-21 for what's in it and why).
#
# 30-day recall window: 2026-07-21 through 2026-08-20. This script does NOT
# delete anything itself — deciding "safe to hard-delete" vs "something needs
# it back" stays a human/session judgment call (STEWARDSHIP.md P10), same
# reasoning as the quarterly refresh script. It only surfaces the decision
# point in TODOS.md, then removes its own one-shot crontab entry so it
# doesn't keep firing every August 20th unreviewed.
set -euo pipefail
cd "$(dirname "$0")/../.."

LOG="logs/graphify_refresh.log"
MARKER="check_dead_code_recall_20260721.sh"

if [ -d "archive/dead_code_20260721" ]; then
  {
    echo ""
    echo "## Recall window closed: archive/dead_code_20260721/ (2026-08-20)"
    echo "30 days have passed with no restore. Decide now:"
    echo "  - If nothing broke: safe to 'rm -rf archive/dead_code_20260721/' and commit."
    echo "  - If something needs a file back: 'git mv archive/dead_code_20260721/<path> <original path>'"
    echo "See archive/dead_code_20260721/README.md for what's in there and why."
    echo ""
  } >> TODOS.md
  echo "$(date '+%Y-%m-%d %H:%M:%S %Z') — recall window closed, reminder logged to TODOS.md" >> "$LOG"
else
  echo "$(date '+%Y-%m-%d %H:%M:%S %Z') — archive/dead_code_20260721/ already resolved, nothing to do" >> "$LOG"
fi

# Self-remove: this is a one-shot check, not a recurring job. Leaving the
# crontab line in place would fire again next August 20th unreviewed.
crontab -l 2>/dev/null | grep -v "$MARKER" | crontab -
echo "$(date '+%Y-%m-%d %H:%M:%S %Z') — self-removed from crontab" >> "$LOG"
