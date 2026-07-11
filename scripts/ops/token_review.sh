#!/usr/bin/env bash
# Weekly token-usage review (founder request 2026-07-11). Runs locally on the
# home server; analyzes Claude Code transcript sizes + gstack skill analytics,
# then asks the local Qwen server (if up) for optimization recommendations.
# Report: ~/meritgiving/logs/token_review/YYYY-MM-DD.md — read the latest at
# session start when optimizing behavior.
set -u
OUT_DIR="$HOME/meritgiving/logs/token_review"; mkdir -p "$OUT_DIR"
OUT="$OUT_DIR/$(date +%F).md"
PROJ="$HOME/.claude/projects/-home-akbar-meritgiving"
{
echo "# Token Review — week ending $(date +%F)"
echo
echo "## Transcript volume (bytes ≈ tokens x ~4)"
find "$PROJ" -maxdepth 1 -name "*.jsonl" -mtime -7 -printf "%s %f\n" 2>/dev/null | sort -rn | head -10 \
  | awk '{printf "- %.1f MB  %s\n", $1/1048576, $2}'
echo "- WEEK TOTAL: $(find "$PROJ" -maxdepth 1 -name '*.jsonl' -mtime -7 -printf '%s\n' 2>/dev/null | awk '{s+=$1} END {printf "%.0f MB (~%.1fM tokens)", s/1048576, s/4194304}')"
echo
echo "## Skill invocations (7d) — each carries a 5-10K-token preamble"
tail -400 "$HOME/.gstack/analytics/skill-usage.jsonl" 2>/dev/null \
  | python3 -c "
import sys,json,datetime,collections
cut=(datetime.datetime.utcnow()-datetime.timedelta(days=7)).isoformat()
c=collections.Counter()
for l in sys.stdin:
    try: d=json.loads(l)
    except: continue
    if d.get('ts','9')>=cut: c[d.get('skill','?')]+=1
for k,v in c.most_common(12): print(f'- {k}: {v}')"
echo
echo "## Subagent runs (7d, ~50K+ tokens each, cold start)"
ls -la /tmp/claude-1000/-home-akbar-meritgiving/*/tasks/*.output 2>/dev/null | awk -v d="$(date -d '7 days ago' +%s)" '{print}' | wc -l | awk '{print "- output files present: "$1}'
} > "$OUT"
# Local-LLM recommendations (free, home server) if Qwen is up
if curl -s -m 3 http://localhost:11437/health 2>/dev/null | grep -q ok; then
  python3 - "$OUT" <<'PY' >> "$OUT" 2>/dev/null
import sys, json, requests
stats = open(sys.argv[1]).read()[:6000]
r = requests.post("http://localhost:11437/v1/chat/completions", json={
  "messages":[{"role":"user","content":"You review AI-assistant token usage for a solo founder. Stats:\n"+stats+"\nGive 3-5 terse, concrete recommendations to cut token spend next week (e.g., which skills to invoke less, when to use fresh sessions, agent usage). Markdown bullets only."}],
  "max_tokens":400}, timeout=120)
print("\n## Recommendations (local Qwen)\n"+r.json()["choices"][0]["message"]["content"])
PY
fi
# prune reports older than 6 months
find "$OUT_DIR" -name "*.md" -mtime +180 -delete 2>/dev/null
echo "written: $OUT"
