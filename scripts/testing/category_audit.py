#!/usr/bin/env python3
"""
Category audit — finds orgs that appear miscategorised based on name keywords.
No LLM or API calls. Runs entirely against merit_registry.db.

Usage:
  python3 scripts/category_audit.py              # full report
  python3 scripts/category_audit.py --ntee X     # single top-level category
  python3 scripts/category_audit.py --csv        # save to audit_report.csv
"""

import sqlite3, argparse, csv, sys, re
from collections import defaultdict
from pathlib import Path

DB = Path(__file__).parent.parent / 'data' / 'merit_registry.db'

# ---------------------------------------------------------------------------
# Keyword rules: each entry = (pattern, expected_ntee1, note)
# pattern matches against lowercase org name
# ---------------------------------------------------------------------------
KEYWORD_RULES = [
    # Faith (X) — wrong-code detection
    (r'\b(hindu|hinduism|mandir|temple of india|vedic|sanatan|gita|yoga ashram|ashram)\b', 'X', 'likely Hindu — check if coded X60 or X70'),
    (r'\b(sikh|gurdwara|gurudwara|khalsa|waheguru)\b',          'X', 'likely Sikh — check if coded X70 or X99'),
    (r'\b(jain|jainism|digambar|shvetambar)\b',                  'X', 'likely Jain — check if coded X70 or X99'),
    (r'\b(buddhis[tm]|dharma center|zen center|tibetan|buddha|sangha|vihara)\b', 'X', 'likely Buddhist — should be X50'),
    (r'\b(mosque|masjid|islamic center|muslim|quran|quranic)\b', 'X', 'likely Islamic — should be X40'),
    (r'\b(synagogue|jewish|hebrew|shul|torah|chabad|jewish federation)\b', 'X', 'likely Jewish — should be X30'),

    # Education (B) — possible miscodes
    (r'\b(charter school|public school|elementary school|high school|school district)\b', 'B', 'school-like name in non-B category'),
    (r'\b(university|college|community college)\b', 'B', 'university-like name — should be B4x'),
    (r'\b(library|public library)\b', 'B', 'library — should be B70 or B72'),

    # Health (E) — possible miscodes
    (r'\b(hospital|medical center|health system|healthcare)\b', 'E', 'hospital-like name'),
    (r'\b(hospice|palliative care)\b', 'E', 'hospice — should be E9x'),
    (r'\b(mental health|behavioral health|psychiatric|counseling center)\b', 'F', 'mental health — should be NTEE F'),

    # Environment (C/D)
    (r'\b(wildlife refuge|animal sanctuary|humane society|spca|animal shelter)\b', 'D', 'animal org — should be NTEE D'),
    (r'\b(environmental|conservation|nature preserve|watershed)\b', 'C', 'environment org — should be NTEE C'),

    # Human Services (P)
    (r'\b(food bank|food pantry|soup kitchen|food shelf)\b', 'K', 'food org — should be NTEE K'),
    (r'\b(homeless shelter|shelter for|transitional housing)\b', 'L', 'housing org — should be NTEE L'),

    # Arts (A)
    (r'\b(symphony|philharmonic|orchestra|opera company)\b', 'A', 'performing arts — should be A6x'),
    (r'\b(museum|art museum|history museum|science museum)\b', 'A', 'museum — should be A5x'),
]

# Subcategory labels from categories.ts (for display)
SUBCATEGORY_LABELS = {
    'X20': 'Christian', 'X21': 'Protestant', 'X22': 'Catholic',
    'X30': 'Jewish', 'X40': 'Islamic', 'X50': 'Buddhist',
    'X60': 'Hindu', 'X70': 'Other Faiths', 'X80': 'Other Religious',
    'X90': 'Other', 'X99': 'Other Religious NEC',
    'B20': 'Elementary/Secondary Ed', 'B40': 'Higher Ed',
    'B70': 'Libraries', 'E20': 'Hospitals', 'E30': 'Clinics',
}

def get_label(nteecc):
    if not nteecc:
        return '(no NTEECC)'
    for prefix_len in (4, 3, 2):
        lbl = SUBCATEGORY_LABELS.get(nteecc[:prefix_len])
        if lbl:
            return f'{nteecc} — {lbl}'
    return nteecc


def audit(ntee_filter=None):
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row

    findings = []  # (ntee1, nteecc, org_name, matched_rule, note)

    for pattern, expected_ntee1, note in KEYWORD_RULES:
        rx = re.compile(pattern, re.IGNORECASE)

        where_ntee = f"AND NTEE1 = '{expected_ntee1}'" if ntee_filter is None else \
                     (f"AND NTEE1 = '{ntee_filter}'" if ntee_filter else '')

        # Orgs where name matches the keyword but NTEECC may be wrong
        rows = db.execute(f"""
            SELECT EIN, organization_name, NTEE1, NTEECC
            FROM registry_enriched
            WHERE LOWER(organization_name) REGEXP ?
            {where_ntee if ntee_filter is None else ''}
            LIMIT 500
        """, (pattern,)).fetchall() if False else []  # SQLite has no REGEXP by default

        # Use Python-side regex instead
        if ntee_filter and ntee_filter != expected_ntee1:
            continue

        sample = db.execute(f"""
            SELECT EIN, organization_name, NTEE1, NTEECC
            FROM registry_enriched
            WHERE NTEE1 = ?
            LIMIT 50000
        """, (expected_ntee1,)).fetchall()

        for row in sample:
            name = row['organization_name'] or ''
            if rx.search(name):
                findings.append({
                    'ntee1': row['NTEE1'],
                    'nteecc': row['NTEECC'] or '',
                    'nteecc_label': get_label(row['NTEECC']),
                    'organization_name': name,
                    'ein': row['EIN'],
                    'keyword_match': pattern,
                    'note': note,
                })

    db.close()
    return findings


def count_by_subcategory(findings):
    counts = defaultdict(lambda: defaultdict(int))
    for f in findings:
        counts[f['ntee1']][f['nteecc_label']] += 1
    return counts


def print_report(findings):
    if not findings:
        print('No issues found.')
        return

    by_ntee = defaultdict(list)
    for f in findings:
        by_ntee[f['ntee1']].append(f)

    total = 0
    for ntee1 in sorted(by_ntee):
        group = by_ntee[ntee1]
        by_code = defaultdict(list)
        for f in group:
            by_code[f['nteecc_label']].append(f)

        print(f'\n{"="*60}')
        print(f'NTEE {ntee1} — {len(group)} flagged orgs')
        print(f'{"="*60}')

        for code_label in sorted(by_code):
            orgs = by_code[code_label]
            print(f'\n  [{code_label}] — {len(orgs)} orgs')
            # Group by note
            by_note = defaultdict(list)
            for o in orgs:
                by_note[o['note']].append(o)
            for note, note_orgs in by_note.items():
                print(f'    Issue: {note}')
                print(f'    Count: {len(note_orgs)}')
                print(f'    Sample orgs:')
                for o in note_orgs[:5]:
                    print(f'      {o["ein"]}  {o["organization_name"][:60]}')

        total += len(group)

    print(f'\n{"="*60}')
    print(f'TOTAL FLAGGED: {total} orgs')
    print(f'{"="*60}')
    print('\nNote: flags are keyword-heuristic only. Many matches are correct')
    print('classifications. Use this as a triage list, not a definitive audit.')


def save_csv(findings, path='audit_report.csv'):
    if not findings:
        print('Nothing to save.')
        return
    fields = ['ntee1', 'nteecc', 'nteecc_label', 'ein', 'organization_name', 'note', 'keyword_match']
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(findings)
    print(f'Saved {len(findings)} rows to {path}')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--ntee', default=None, help='Filter to single NTEE1 letter (e.g. X)')
    ap.add_argument('--csv', action='store_true', help='Save results to audit_report.csv')
    args = ap.parse_args()

    print(f'Running category audit against {DB}...')
    if args.ntee:
        print(f'Filtering to NTEE1={args.ntee}')

    findings = audit(ntee_filter=args.ntee)

    print_report(findings)

    if args.csv:
        save_csv(findings)


if __name__ == '__main__':
    main()
