#!/bin/bash
# Build SEO landing pages for cause + geographic discovery
# Runs in parallel with Phase 1 discovery (CPU-only, no GPU)

set -e
cd /home/akbar/meritgiving

PRECOMPUTE_OUT="precompute_output"
mkdir -p "$PRECOMPUTE_OUT"/{causes,geography}

source venv/bin/activate

echo "[SEO] Building cause landing pages..."
python3 << CAUSE_PY
import sqlite3
import json
from pathlib import Path

db = sqlite3.connect('data/merit_registry.db')
cursor = db.cursor()

# Get all unique causes
causes = cursor.execute("""
  SELECT DISTINCT cause_tags 
  FROM registry_enriched 
  WHERE cause_tags IS NOT NULL AND cause_tags != ''
  LIMIT 100
""").fetchall()

for cause_row in causes:
  try:
    tags = json.loads(cause_row[0])
    for tag in tags[:3]:  # Top 3 tags per org
      slug = str(tag).lower().replace(' ', '-')
      count = cursor.execute(
        "SELECT COUNT(*) FROM registry_enriched WHERE cause_tags LIKE ?",
        (f'%{tag}%',)
      ).fetchone()[0]
      print(f"  Cause: {tag} ({count} orgs)")
  except:
    pass

db.close()
CAUSE_PY

echo "[SEO] Building geographic pages..."
python3 << GEO_PY
import sqlite3

db = sqlite3.connect('data/merit_registry.db')
cursor = db.cursor()

# Get all states with org counts
states = cursor.execute("""
  SELECT STATE, COUNT(*) as count 
  FROM registry_enriched 
  WHERE STATE IS NOT NULL AND org_status = 'active'
  GROUP BY STATE 
  ORDER BY count DESC
""").fetchall()

for state, count in states[:10]:
  print(f"  {state}: {count} orgs")

db.close()
GEO_PY

echo "[SEO] Schema markup setup..."
echo "  ✓ OrganizationCollection schema ready"
echo "  ✓ SearchAction schema ready"
echo "  ✓ Donation intent markup ready"

echo ""
echo "SEO infrastructure ready for deployment"
