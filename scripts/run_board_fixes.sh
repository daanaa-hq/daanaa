#!/bin/bash
set -e
echo "=========================================="
echo "MERIT Board Review — Automated Fixes"
echo "=========================================="
if [ ! -f "app.py" ] && [ ! -f "merit_app.py" ]; then
    echo "ERROR: Run this from ~/meritgiving/ directory"
    exit 1
fi
mkdir -p logs

echo ""
echo "[1/4] Running dedupe & data quality audit..."
echo "------------------------------------------"
if [ -f "scripts/merit_dedupe_audit.py" ]; then
    python3 scripts/merit_dedupe_audit.py | tee logs/audit_$(date +%Y%m%d_%H%M%S).log
else
    echo "  ⚠️  merit_dedupe_audit.py not found."
fi

echo ""
echo "[2/4] Applying P0 automated fixes..."
echo "------------------------------------------"
if [ -f "scripts/merit_p0_board_fixes.py" ]; then
    python3 scripts/merit_p0_board_fixes.py | tee logs/fixes_$(date +%Y%m%d_%H%M%S).log
else
    echo "  ⚠️  merit_p0_board_fixes.py not found."
fi

echo ""
echo "[3/4] Testing MERIT score engine..."
echo "------------------------------------------"
if [ -f "scripts/merit_scorer.py" ] && [ -f "data/index/sample_2023_2000.json" ]; then
    python3 scripts/merit_scorer.py --input data/index/sample_2023_2000.json --output data/scored_sample_test.json | tee logs/scorer_$(date +%Y%m%d_%H%M%S).log
    echo ""
    echo "  Score distribution preview:"
    python3 -c "
import json
from collections import Counter
with open('data/scored_sample_test.json') as f: data = json.load(f)
bands = Counter(); scores = []
for o in data:
    m = o.get('_merit', {})
    bands[m.get('merit_band', 'Unknown')] += 1
    if m.get('merit_score') is not None: scores.append(m['merit_score'])
print('  Bands:', dict(bands))
if scores: print(f'  Range: {min(scores)}-{max(scores)}, Mean: {sum(scores)/len(scores):.1f}')
"
else
    echo "  ⚠️  Skipping score test."
fi

echo ""
echo "[4/4] Manual fixes checklist"
echo "------------------------------------------"
cat << 'CHECKLIST'

AUTOMATED FIXES COMPLETE. MANUAL FIXES STILL NEEDED:

Webflow / CMS:
  ☐ Rename collection field "Impact Score" -> "MERIT Score"
  ☐ Update template: {{impact_score}} -> {{merit_score}}
  ☐ Homepage tagline: "peer-ranked MERIT scores"
  ☐ Hide "Uncategorized" from browse grid (or move to bottom)
  ☐ Replace/remove "Featured Organizations" section
  ☐ Add footer: About | Methodology | Contact | Privacy | Terms
  ☐ Add "Report incorrect data" link on org pages
  ☐ Add data freshness timestamp on org cards

Airtable:
  ☐ Rename "Impact" column -> "MERIT"
  ☐ Update formula fields

n8n:
  ☐ Relabel "Impact" nodes -> "MERIT"

Content / Docs:
  ☐ Whitepaper: global find/replace "Impact" -> "MERIT"
  ☐ /merit/docs/MERIT-CONTEXT.md: update references
  ☐ GitHub READMEs: rename

Data (next batch):
  ☐ Fix mission parsing from 990 Schedule O
  ☐ Fix NTEE for known orgs (Houston Symphony = A69)
  ☐ Unify "last filing year" source of truth
  ☐ Replace hardcoded org counts with real SELECT COUNT(*)

SEO / Distribution:
  ☐ Per-org URLs: /o/{ein}/{slug}
  ☐ OG tags for social sharing
  ☐ Generate sitemap.xml
  ☐ Schema.org JSON-LD markup

CHECKLIST

echo ""
echo "=========================================="
echo "Done. Review logs/ directory for details."
echo "=========================================="
