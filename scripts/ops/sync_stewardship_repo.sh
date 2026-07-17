#!/bin/bash
# sync_stewardship_repo.sh — mirror governance corpus + custom skills to the
# private daanaa-hq/daanaa-ai-stewardship archive, sanitized.
#
# Called by the post-commit hook when governance/ or .claude/skills/ changed,
# or run manually. Idempotent; no-op when nothing differs.
#
# Sanitization rule (set at archive creation, 2026-07-16): droplet IP never
# leaves the main repo — replaced with YOUR_DROPLET_IP.

set -euo pipefail

MAIN="/home/akbar/meritgiving"
ARCHIVE="/home/akbar/daanaa-ai-stewardship"
LOG="$MAIN/logs/stewardship_sync.log"

ts() { date '+%Y-%m-%d %H:%M:%S'; }
log() { echo "[$(ts)] $*" >> "$LOG"; }

[ -d "$ARCHIVE/.git" ] || { log "archive clone missing at $ARCHIVE — skipping"; exit 0; }

# Mirror governance docs + skills (delete removed files in target dirs)
rsync -a --delete "$MAIN/governance/" "$ARCHIVE/governance/" 2>/dev/null || true
# Core governance docs living at main-repo root
for f in STEWARDSHIP.md PRIVACY-INVARIANTS.md; do
  [ -f "$MAIN/$f" ] && cp "$MAIN/$f" "$ARCHIVE/governance/$f"
done
rsync -a --delete "$MAIN/.claude/skills/" "$ARCHIVE/skills/" 2>/dev/null || true
[ -d "$MAIN/.agents/skills/daanaa-system-audit" ] && \
  rsync -a "$MAIN/.agents/skills/daanaa-system-audit/" "$ARCHIVE/skills/daanaa-system-audit/"

# Sanitize (never let infra details into the shareable archive)
grep -rl "162\.243\.97\.179" "$ARCHIVE/skills" "$ARCHIVE/governance" 2>/dev/null | while read -r f; do
  sed -i 's/162\.243\.97\.179/YOUR_DROPLET_IP/g' "$f"
done

cd "$ARCHIVE"
if git status --porcelain | grep -q .; then
  git add -A
  git commit -m "Auto-sync from main repo $(cd "$MAIN" && git rev-parse --short HEAD) — $(ts)" >> "$LOG" 2>&1
  git push origin main >> "$LOG" 2>&1 \
    && log "synced + pushed (main @ $(cd "$MAIN" && git rev-parse --short HEAD))" \
    || log "PUSH FAILED — commit is local, will push on next sync"
else
  log "no changes to sync"
fi
