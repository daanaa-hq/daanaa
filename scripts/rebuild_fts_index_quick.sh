#!/bin/bash
# Quick FTS index rebuild — safe and resumable
# Does NOT rebuild the entire precompute; only touches the search index

set -euo pipefail

BASE_DIR="$HOME/meritgiving"
DB_PATH="$BASE_DIR/data/merit_registry.db"
LOG_FILE="$BASE_DIR/logs/fts_rebuild.log"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log "FTS Index Rebuild"
log "================================================================"

if [ ! -f "$DB_PATH" ]; then
  log "ERROR: Database not found at $DB_PATH"
  exit 1
fi

log "Starting FTS rebuild (this may take 30-60 seconds)..."

# Rebuild the FTS index — drop and recreate it
cd "$BASE_DIR"
python3 -c "
import sqlite3
from pathlib import Path

db_path = Path('$DB_PATH')
if not db_path.exists():
    print(f'ERROR: {db_path} not found')
    exit(1)

conn = sqlite3.connect(db_path, timeout=10)
cursor = conn.cursor()

# Get before-state
cursor.execute('SELECT COUNT(*) FROM registry_enriched')
total_orgs = cursor.fetchone()[0]
print(f'Total orgs in registry: {total_orgs:,}')

cursor.execute('SELECT COUNT(*) FROM org_fts')
fts_before = cursor.fetchone()[0]
print(f'FTS entries before: {fts_before:,}')

# Rebuild FTS index
print('Dropping and recreating org_fts...')
cursor.execute('DROP TABLE IF EXISTS org_fts')
cursor.execute('DROP TRIGGER IF EXISTS org_ai')
cursor.execute('DROP TRIGGER IF EXISTS org_ad')
cursor.execute('DROP TRIGGER IF EXISTS org_au')

# Recreate the FTS virtual table with all content
cursor.execute('''
  CREATE VIRTUAL TABLE org_fts USING fts5(
    ein, organization_name, city, state, mission, cause_tags,
    content=registry_enriched, content_rowid=rowid
  )
''')

# Populate the FTS index from registry_enriched
cursor.execute('''
  INSERT INTO org_fts(rowid, ein, organization_name, city, state, mission, cause_tags)
  SELECT rowid, ein, organization_name, city, state, mission, cause_tags
  FROM registry_enriched
''')

# Create triggers to keep FTS in sync
cursor.execute('''
  CREATE TRIGGER org_ai AFTER INSERT ON registry_enriched BEGIN
    INSERT INTO org_fts(rowid, ein, organization_name, city, state, mission, cause_tags)
    VALUES (new.rowid, new.ein, new.organization_name, new.city, new.state, new.mission, new.cause_tags);
  END
''')

cursor.execute('''
  CREATE TRIGGER org_ad AFTER DELETE ON registry_enriched BEGIN
    DELETE FROM org_fts WHERE rowid = old.rowid;
  END
''')

cursor.execute('''
  CREATE TRIGGER org_au AFTER UPDATE ON registry_enriched BEGIN
    DELETE FROM org_fts WHERE rowid = old.rowid;
    INSERT INTO org_fts(rowid, ein, organization_name, city, state, mission, cause_tags)
    VALUES (new.rowid, new.ein, new.organization_name, new.city, new.state, new.mission, new.cause_tags);
  END
''')

conn.commit()

# Verify
cursor.execute('SELECT COUNT(*) FROM org_fts')
fts_after = cursor.fetchone()[0]
print(f'FTS entries after: {fts_after:,}')

if fts_after == total_orgs:
    print(f'✓ FTS fully rebuilt and in sync ({fts_after:,} orgs)')
else:
    print(f'WARN: FTS has {fts_after:,} entries but registry has {total_orgs:,}')

conn.close()
" 2>&1 | tee -a "$LOG_FILE"

log "================================================================"
log "✓ FTS rebuild complete"
log "Run: bash scripts/ops/sync_droplet_api.sh"
log "Then: bash scripts/health_check.sh"
