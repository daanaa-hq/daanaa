#!/usr/bin/env python3
import sqlite3
import requests
import time
import sys
from pathlib import Path
from datetime import datetime

DB = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'
LOG = Path.home() / 'meritgiving' / 'logs' / 'overnight.log'

def log(msg):
    t = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    s = '[' + t + '] ' + msg
    print(s)
    sys.stdout.flush()
    with open(LOG, 'a') as f:
        f.write(s + chr(10))

def get_db():
    return sqlite3.connect(str(DB))

def enrich_batch(size=1000):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT EIN FROM registry_enriched WHERE propublica_object_id IS NULL LIMIT ?', (size,))
    eins = [r[0] for r in c.fetchall()]
    if not eins:
        log('All orgs enriched.')
        conn.close()
        return 0, 0
    log('Enriching ' + str(len(eins)) + ' orgs...')
    updated = 0
    errors = 0
    for i, ein in enumerate(eins):
        try:
            url = 'https://projects.propublica.org/nonprofits/api/v2/organizations/' + ein + '.json'
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                org = data.get('organization', {})
                filings = data.get('filings_with_data', [])
                obj_id = org.get('id', '')
                pdf = ''
                fdate = ''
                fyear = 0
                if filings and len(filings) > 0:
                    latest = filings[0]
                    pdf = latest.get('pdf_url', '')
                    fdate = latest.get('date_submitted', '')
                    fyear = latest.get('tax_prd_yr', 0)
                c.execute('UPDATE registry SET propublica_object_id = ?, propublica_pdf_url = ?, propublica_filing_date = ?, propublica_tax_year = ?, last_updated = datetime(\'now\') WHERE EIN = ?', (obj_id, pdf, fdate, fyear, ein))
                updated += 1
            elif resp.status_code == 429:
                log('Rate limited. Waiting 60s...')
                time.sleep(60)
                continue
            else:
                errors += 1
        except Exception as e:
            errors += 1
            if i % 50 == 0:
                log('Error for ' + ein + ': ' + str(e)[:60])
        time.sleep(0.6)
        if updated % 100 == 0 and updated > 0:
            conn.commit()
            log(str(updated) + '/' + str(len(eins)) + ' done, ' + str(errors) + ' errors')
    conn.commit()
    conn.close()
    log('Batch: ' + str(updated) + ' updated, ' + str(errors) + ' errors')
    return updated, errors

def main():
    log('=' * 60)
    log('Overnight Pipeline Started')
    log('=' * 60)
    total = 0
    errs = 0
    batches = 0
    while batches < 50:
        u, e = enrich_batch(1000)
        total += u
        errs += e
        batches += 1
        if u == 0:
            log('Done. All orgs enriched.')
            break
        if batches % 5 == 0:
            log('Progress: ' + str(total) + ' enriched, ' + str(errs) + ' errors')
    log('=' * 60)
    log('Complete: ' + str(total) + ' enriched, ' + str(errs) + ' errors')
    log('=' * 60)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log('FATAL: ' + str(e))
        sys.exit(1)
