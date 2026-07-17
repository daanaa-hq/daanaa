---
name: marketing-content
version: 1.0.0
description: Plan Daanaa's LinkedIn content calendar — generate a month of post ideas, assign types, and queue them in order. (Daanaa)
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
triggers:
  - content calendar
  - plan content
  - what should we post
  - content ideas
  - plan next month
  - content plan
---

## When to invoke this skill

Use when asked to plan Daanaa's LinkedIn content — monthly calendar, post ideas, or what to post next.
Produces a prioritized queue of carousel and text post ideas, with types and suggested timing.

---

## Step 0 — Pull current context

```bash
# Check what was posted recently (output folder timestamps)
ls -lt /home/akbar/meritgiving/scripts/linkedin/output/*.pdf 2>/dev/null | head -5

# Pull fresh sector data for content ideas
cd /home/akbar/meritgiving && source venv/bin/activate
python3 - <<'EOF'
import sqlite3, json
db = sqlite3.connect('data/merit_registry.db')
db.row_factory = sqlite3.Row
# Top sectors by org count
sectors = db.execute("""
    SELECT ntee1_label, COUNT(*) as cnt,
           AVG(CASE WHEN merit_score_v5 IS NOT NULL THEN merit_score_v5 END) as avg_score
    FROM registry_enriched
    WHERE org_status = 'active' AND ntee1_label IS NOT NULL
    GROUP BY ntee1_label ORDER BY cnt DESC LIMIT 10
""").fetchall()
for s in sectors:
    print(f"{s['ntee1_label']}: {s['cnt']:,} orgs, avg score {s['avg_score']:.0f}" if s['avg_score'] else f"{s['ntee1_label']}: {s['cnt']:,} orgs")
db.close()
EOF
```

---

## Step 1 — Generate the calendar

Build a 4-week content calendar using this cadence:

**Week structure (2 posts per week is the right pace for a new page):**
- **Monday**: Carousel post (high-effort, high-reach)
- **Thursday**: Short text post or single stat (low-effort, keeps the page active)

**Monthly mix:**
| Week | Monday Carousel | Thursday Text |
|---|---|---|
| Week 1 | `hidden_gems` | Stat from the database |
| Week 2 | `sector_insight` | Quote or observation |
| Week 3 | `how_it_works` OR `myth_bust` | Question to the audience |
| Week 4 | `feature_launch` OR `hidden_gems` | Behind-the-scenes |

For each carousel, suggest:
- Type
- Specific angle or context (e.g., "sector_insight focused on Food & Hunger")
- Suggested caption hook (first line only)

For each text post, write the full post (under 150 words).

---

## Step 2 — Pull content ideas from the data

Use the sector data pulled in Step 0 to make carousel angles specific:
- Largest sector → sector_insight angle
- Most hidden gems in a cause area → hidden_gems angle
- Surprising stat (high low-reserve %, small avg score in a big sector) → myth_bust or text post

---

## Step 3 — Output format

Present the calendar as a clean table:

```
DAANAA LINKEDIN — [Month] Content Calendar

Week 1
  Mon [date]: CAROUSEL — hidden_gems
              Angle: "The food pantries no one knows about"
              Context flag: --type hidden_gems --context "food pantries under $200K"
  Thu [date]: TEXT POST
              "97% of U.S. nonprofits have no national name recognition.
               That doesn't mean they're not doing important work.
               It means they need a different kind of visibility.
               daanaa.org"

Week 2
  ...
```

Then ask: "Want me to generate the Week 1 carousel now?"

---

## Step 4 — Optionally save the calendar

```bash
# Save to docs/marketing/
mkdir -p /home/akbar/meritgiving/docs/marketing
# Write calendar to docs/marketing/YYYY-MM-content-calendar.md
```
