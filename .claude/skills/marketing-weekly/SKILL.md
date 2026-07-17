---
name: marketing-weekly
version: 1.0.0
description: Run Daanaa's weekly marketing sprint — carousel post, outreach queue check, Plausible analytics snapshot, and next-week prep. (Daanaa)
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
triggers:
  - weekly marketing
  - marketing sprint
  - do marketing
  - run marketing
  - weekly post
---

## When to invoke this skill

Use at the start of each week to run the full Daanaa marketing sprint.
Covers: LinkedIn carousel post → outreach queue → analytics check → next week prep.
Takes about 10 minutes of your time per week.

---

## Step 0 — Weekly context check

```bash
# What day is it, what was last posted
date
ls -lt /home/akbar/meritgiving/scripts/linkedin/output/*.pdf 2>/dev/null | head -3

# Check Plausible analytics (last 7 days)
curl -s "https://plausible.io/api/v1/stats/summary?site_id=daanaa.org&period=7d" \
  -H "Authorization: Bearer ${PLAUSIBLE_API_KEY}" 2>/dev/null | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    r = d.get('results', {})
    print(f\"Visitors (7d): {r.get('visitors',{}).get('value','?')}\")
    print(f\"Pageviews (7d): {r.get('pageviews',{}).get('value','?')}\")
    print(f\"Bounce rate: {r.get('bounce_rate',{}).get('value','?')}%\")
except: print('Plausible: no data (check PLAUSIBLE_API_KEY)')
"

# Check if LinkedIn session is still valid
ls /home/akbar/meritgiving/scripts/linkedin/.session/state.json 2>/dev/null && echo "LinkedIn session: present" || echo "LinkedIn session: MISSING — run --setup"
```

---

## Step 1 — LinkedIn carousel (Monday post)

Determine which carousel type to run based on the content calendar rotation:
- If no carousel posted this week → run `hidden_gems` (default) OR check `docs/marketing/` for the planned type
- If already posted this week → skip to Step 2

```bash
cd /home/akbar/meritgiving && source venv/bin/activate
python3 scripts/linkedin/post_carousel.py --type hidden_gems
```

Report: PDF filename, whether it posted successfully.

If posting failed (session expired, etc.) — generate with `--dry-run` and give the user the PDF path to upload manually.

---

## Step 2 — Outreach queue

```bash
# Check for queued outreach drafts
ls /home/akbar/meritgiving/docs/outreach/ 2>/dev/null
```

Remind the user of queued targets from memory:
- **Leslie Chandler** — follow-up pending
- **Candid data partnership** — draft ready
- **LinkedIn 250 invites** — are this month's invites sent? (check if follower count moved)

Ask: "Any of these ready to send today?"

---

## Step 3 — Thursday text post (prep for later in week)

Generate one short LinkedIn text post (under 150 words) based on fresh data:

```bash
cd /home/akbar/meritgiving && source venv/bin/activate
python3 - <<'EOF'
import sqlite3, random
db = sqlite3.connect('data/merit_registry.db')
db.row_factory = sqlite3.Row

# Pull a surprising stat for the text post
low_reserve = db.execute("""
    SELECT ntee1_label, COUNT(*) as total,
           SUM(CASE WHEN merit_health_signal_v5 = 'CAUTION' THEN 1 ELSE 0 END) as caution
    FROM registry_enriched
    WHERE org_status='active' AND ntee1_label IS NOT NULL AND merit_health_signal_v5 IS NOT NULL
    GROUP BY ntee1_label HAVING total > 500
    ORDER BY CAST(caution AS FLOAT)/total DESC LIMIT 5
""").fetchall()
for r in low_reserve:
    pct = round(r['caution']/r['total']*100)
    print(f"{r['ntee1_label']}: {pct}% showing limited reserves ({r['total']:,} orgs)")
db.close()
EOF
```

Use the output to write a specific, data-grounded text post. Format:

```
[Surprising stat or observation]

[One sentence of context — why this matters]

[One sentence on what Daanaa shows about this]

daanaa.org
#nonprofits #philanthropy [relevant sector hashtag]
```

---

## Scheduler (optional — runs posting automatically)

If you'd rather not run manually each Monday, the scheduler can handle it:

```bash
cd /home/akbar/meritgiving && source venv/bin/activate

# Show what's scheduled and when it next fires
python3 scripts/linkedin/schedule_posts.py --next

# Start the scheduler (blocks — run in a tmux pane or as a systemd service)
python3 scripts/linkedin/schedule_posts.py

# Trigger the Monday carousel right now (bypasses schedule)
python3 scripts/linkedin/schedule_posts.py --run-now
```

Cadence: Monday 09:00 → carousel (rotates hidden_gems / sector_insight / myth_bust). Thursday 09:00 → prints a data-backed text post to stdout for manual copy-paste.

---

## Step 4 — Next week prep

Suggest what to queue for next week based on the content calendar rotation:
- Which carousel type is next
- Any specific angle based on current data or news
- Whether to run `marketing-content` to plan the full month if calendar isn't set

---

## Step 5 — Weekly summary

Print a clean summary:
```
DAANAA WEEKLY MARKETING — [date]

LinkedIn:
  ✓ Carousel posted: [filename or "pending manual upload"]
  · Followers: [if visible]

Outreach:
  · [status of queued items]

Analytics (7d):
  · Visitors: [N]
  · Pageviews: [N]

Next up (Thursday):
  · [text post draft or "see above"]

Next Monday:
  · [carousel type] — [angle]
```
