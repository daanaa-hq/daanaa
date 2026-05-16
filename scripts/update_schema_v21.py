import sqlite3
from pathlib import Path
import pandas as pd

DB_PATH = Path.home() / 'meritgiving' / 'data' / 'meritgiving.db'
conn = sqlite3.connect(str(DB_PATH))
c = conn.cursor()

print('=' * 60)
print('MeritGiving Schema Update v2.1')
print('=' * 60)

c.execute('PRAGMA table_info(registry)')
registry_cols = [col[1] for col in c.fetchall()]

new_cols = {
    'last_updated': 'TEXT',
    'data_source': 'TEXT',
    'first_seen_date': 'TEXT',
    'last_verified_date': 'TEXT',
    'propublica_object_id': 'TEXT',
    'propublica_filing_date': 'TEXT',
    'propublica_tax_year': 'INTEGER',
    'propublica_pdf_url': 'TEXT',
    'charity_navigator_rating': 'REAL',
    'charity_navigator_score': 'REAL',
    'compliance_status': 'TEXT DEFAULT active',
    'compliance_flag_date': 'TEXT',
    'notes': 'TEXT',
}

for col, dtype in new_cols.items():
    if col not in registry_cols:
        c.execute('ALTER TABLE registry_enriched ADD COLUMN ' + col + ' ' + dtype)
        print('Added: ' + col)
    else:
        print('Exists: ' + col)

c.execute('PRAGMA table_info(scores)')
scores_cols = [col[1] for col in c.fetchall()]

new_score_cols = {
    'scored_at': 'TEXT',
    'score_version': 'TEXT DEFAULT 2.1',
    'model_weights': 'TEXT',
}

for col, dtype in new_score_cols.items():
    if col not in scores_cols:
        c.execute('ALTER TABLE scores ADD COLUMN ' + col + ' ' + dtype)
        print('Added: ' + col)
    else:
        print('Exists: ' + col)

c.execute('CREATE TABLE IF NOT EXISTS enrichment_log (id INTEGER PRIMARY KEY AUTOINCREMENT, ein TEXT, source TEXT, field_name TEXT, old_value TEXT, new_value TEXT, changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, changed_by TEXT DEFAULT system)')
print('Table: enrichment_log')

c.execute('CREATE TABLE IF NOT EXISTS data_freshness (table_name TEXT PRIMARY KEY, last_full_refresh TIMESTAMP, last_incremental_update TIMESTAMP, row_count INTEGER, source_file TEXT, notes TEXT)')
print('Table: data_freshness')

reg_count = len(pd.read_sql('SELECT EIN FROM registry_enriched', conn))
c.execute('INSERT OR REPLACE INTO data_freshness VALUES (?, datetime(now), NULL, ?, ?, ?)', ('registry', reg_count, 'bmf_master.csv', 'Initial load'))

conn.commit()
conn.close()
print('Schema update complete.')
