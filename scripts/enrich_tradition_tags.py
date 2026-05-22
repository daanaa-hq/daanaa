#!/usr/bin/env python3
"""
Enrich cause_tags for Hindu, Sikh, Jain, Buddhist, Islamic, Jewish orgs
that currently have only generic tags ("religion", "faith") or no tags.

Phase 1: Deterministic regex — instant, no model.
Phase 2: Ollama qwen2.5:14b for orgs with no tags and no clear name match.

Usage:
  python3 scripts/enrich_tradition_tags.py             # dry run
  python3 scripts/enrich_tradition_tags.py --write     # commit to DB
  python3 scripts/enrich_tradition_tags.py --write --phase2   # also run Ollama
"""

import sqlite3, json, re, argparse, requests
from pathlib import Path

DB = Path(__file__).parent.parent / 'data' / 'merit_registry.db'
OLLAMA_URL = 'http://localhost:11434/api/generate'
OLLAMA_MODEL = 'qwen2.5:14b'

# ---------------------------------------------------------------------------
# Deterministic tradition rules — applied purely from org name
# ---------------------------------------------------------------------------
TRADITION_RULES = [
    ('Hindu',    r'\b(hindu|hinduism|mandir|vedic|sanatan|gita|shakti|krishna|vishnu|shiva|devi|rama|hanuman|ganesh|durga|lakshmi|ashram|veda|yoga ashram|arya samaj)\b'),
    ('Sikh',     r'\b(sikh|sikhism|gurdwara|gurudwara|khalsa|waheguru|guru nanak|guru granth|akali|punjabi sikh)\b'),
    ('Jain',     r'\b(jain|jainism|digambar|shvetambar|tirth|mahavir|jaina)\b'),
    ('Buddhist', r'\b(buddhis[tm]|zen |tibetan buddhist|buddha |sangha|vihara|dharma center|dharma temple|wat |theravada|mahayana|vajrayana)\b'),
    ('Islamic',  r'\b(islamic|masjid|mosque|muslim|quran|quranic|islamic center|halal|ummah|hijab|salat)\b'),
    ('Jewish',   r'\b(jewish|judaism|synagogue|shul|torah|chabad|talmud|hebrew school|yeshiva|rabbi|jewish federation|jewish community)\b'),
]

GENERIC_TAGS = {'religion', 'faith', 'spiritual', 'religious services', 'worship',
                'church', 'religious activities', 'religious community', 'religion promotion',
                'religious organization', 'religion awareness', 'faith community'}


TRADITION_TAG_NAMES = {t.lower() for t, _ in TRADITION_RULES}


def is_generic(tags: list) -> bool:
    if not tags:
        return True
    lower = {t.lower() for t in tags}
    return lower.issubset(GENERIC_TAGS)


def has_wrong_tradition(tags: list, correct_tradition: str) -> bool:
    """True if tags contain a tradition tag that doesn't match the detected tradition."""
    lower = {t.lower() for t in tags}
    wrong = TRADITION_TAG_NAMES - {correct_tradition.lower()}
    return bool(lower & wrong)


def detect_tradition(name: str) -> str | None:
    for tradition, pattern in TRADITION_RULES:
        if re.search(pattern, name, re.IGNORECASE):
            return tradition
    return None


def merge_tags(existing: list, new_tradition: str) -> list:
    # Strip generic tags AND any wrong-tradition tags
    wrong = TRADITION_TAG_NAMES - {new_tradition.lower()}
    keep = [t for t in existing if t.lower() not in GENERIC_TAGS and t.lower() not in wrong]
    tradition_tag = new_tradition.lower()
    if tradition_tag not in [t.lower() for t in keep]:
        keep = [new_tradition] + keep
    # Always include Religion
    if 'Religion' not in keep and 'religion' not in [t.lower() for t in keep]:
        keep.append('Religion')
    return keep[:6]


def ollama_tag(name: str, mission: str | None) -> list | None:
    text = name
    if mission:
        text += f'. {mission[:300]}'
    prompt = f"""You are tagging nonprofit organizations for a donor discovery platform.

Org: {text}

Return ONLY a JSON array of 3-5 specific cause tags describing this organization's religious tradition and work.
Be specific: use "Sikh", "Hindu", "Jain", "Buddhist", "Islamic", "Jewish" etc rather than just "religion".
Example: ["Sikh", "Community Services", "Religion"]

Tags:"""
    try:
        r = requests.post(OLLAMA_URL, json={
            'model': OLLAMA_MODEL,
            'prompt': prompt,
            'stream': False,
            'options': {'temperature': 0.1, 'num_predict': 80}
        }, timeout=60)
        text = r.json().get('response', '').strip()
        match = re.search(r'\[.*?\]', text, re.DOTALL)
        if match:
            tags = json.loads(match.group())
            return [str(t).strip() for t in tags if t][:6]
    except Exception as e:
        print(f'  ollama error: {e}')
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true', help='Commit changes to DB')
    ap.add_argument('--phase2', action='store_true', help='Use Ollama for no-match orgs')
    ap.add_argument('--limit', type=int, default=0, help='Max orgs to process')
    args = ap.parse_args()

    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row

    rows = db.execute("""
        SELECT EIN, organization_name, cause_tags, mission
        FROM registry_enriched
    """).fetchall()

    updates = []
    skipped_already_specific = 0
    phase1_hits = 0
    phase1_corrections = 0
    phase2_hits = 0
    no_match = 0

    for row in rows:
        if args.limit and len(updates) >= args.limit:
            break

        name = row['organization_name'] or ''
        raw = row['cause_tags']
        existing = json.loads(raw) if raw and raw not in ('[]', 'null') else []

        tradition = detect_tradition(name)

        # Skip if already has correct specific tradition tag and no wrong ones
        if not is_generic(existing) and not (tradition and has_wrong_tradition(existing, tradition)):
            skipped_already_specific += 1
            continue

        if tradition:
            new_tags = merge_tags(existing, tradition)
            updates.append((json.dumps(new_tags), row['EIN']))
            is_correction = has_wrong_tradition(existing, tradition)
            if is_correction:
                phase1_corrections += 1
            else:
                phase1_hits += 1
            if args.limit and (phase1_hits + phase1_corrections) <= 5:
                label = '[fix]' if is_correction else '[new]'
                print(f'  {label} {name[:52]:52} {existing} → {new_tags}')

        elif args.phase2:
            tags = ollama_tag(name, row['mission'])
            if tags:
                updates.append((json.dumps(tags), row['EIN']))
                phase2_hits += 1
                print(f'  [ollama] {name[:55]:55} → {tags}')
            else:
                no_match += 1
        else:
            no_match += 1

    print(f'\nResults:')
    print(f'  Already specific (skipped):  {skipped_already_specific}')
    print(f'  Phase 1 new tags:            {phase1_hits}')
    print(f'  Phase 1 corrections:         {phase1_corrections}')
    print(f'  Phase 2 Ollama hits:         {phase2_hits}')
    print(f'  No match / unprocessed:      {no_match}')
    print(f'  Total updates queued:        {len(updates)}')

    if args.write and updates:
        db.executemany('UPDATE registry_enriched SET cause_tags = ? WHERE EIN = ?', updates)
        db.commit()
        print(f'  Written to DB: {len(updates)} orgs updated')
    elif updates:
        print(f'  Dry run — pass --write to commit')

    db.close()


if __name__ == '__main__':
    main()
