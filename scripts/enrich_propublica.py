import sqlite3
import requests
import time
from pathlib import Path
from datetime import datetime

DB_PATH = Path.home() / 'meritgiving' / 'data' / 'meritgiving.db'
conn = sqlite3.connect(str(DB_PATH))
c = conn.cursor()

print('=' * 60)
print('ProPublica Enrichment')
print('=' * 60)

c.execute("SELECT EIN FROM registry_enriched WHERE propublica_object_id IS NULL OR propublica_object_id = '' LIMIT 1000")
eins = [row[0] for row in c.fetchall()]
print('Orgs to enrich: ' + str(len(eins)))

updated = 0
errors = 0

for ein in eins:
    try:
        url = 'https://projects.propublica.org/nonprofits/api/v2/organizations/' + ein + '.json'
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            org = data.get('organization', {})
            filings = data.get('filings_with_data', [])
            object_id = org.get('id', '')
            pdf_url = ''
            filing_date = ''
            tax_year = 0
            if filings and len(filings) > 0:
                latest = filings[0]
                pdf_url = latest.get('pdf_url', '')
                filing_date = latest.get('date_submitted', '')
                tax_year = latest.get('tax_prd_yr', 0)
            c.execute("UPDATE registry SET propublica_object_id = ?, propublica_pdf_url = ?, propublica_filing_date = ?, propublica_tax_year = ?, last_updated = datetime('now') WHERE EIN = ?", (object_id, pdf_url, filing_date, tax_year, ein))
            updated += 1
        else:
            errors += 1
    except Exception as e:
        errors += 1
    time.sleep(0.5)
    if updated % 100 == 0:
        print('Progress: ' + str(updated) + ' updated, ' + str(errors) + ' errors')
        conn.commit()

conn.commit()
conn.close()
print('=' * 60)
print('Complete: ' + str(updated) + ' updated, ' + str(errors) + ' errors')
print('=' * 60)
