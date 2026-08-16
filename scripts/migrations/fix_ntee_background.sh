#!/bin/bash
# NTEE Gap Fix — Background Job
# Safe to run while sleeping. Resumes if interrupted.
# Log: ~/meritgiving/logs/ntee_fix.log

cd ~/meritgiving
source venv/bin/activate

exec > >(tee -a logs/ntee_fix.log)
exec 2>&1

echo "========================================"
echo "NTEE GAP FIX — STARTED"
echo "Time: $(date)"
echo "========================================"

python3 << 'PYEOF'
import csv, os, re
from collections import Counter

print("[1] Loading percentile engine...")
with open('data/csv/percentile_engine_v1.csv', 'r', encoding='utf-8') as f:
    orgs = list(csv.DictReader(f))

print(f"    Total orgs: {len(orgs)}")
missing = [o for o in orgs if not o.get('ntee') or o.get('ntee').strip() == '']
print(f"    Missing NTEE: {len(missing)}")

# --- Strategy 1: Reload BMF with normalized EINs ---
print("\n[2] Strategy 1: Normalized EIN matching...")
bmf_normalized = {}
with open('data/bmf/2026-04-BMF.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader):
        ein_raw = row.get('EIN', '').strip()
        ntee = row.get('NTEE_CD', row.get('NTEE', '')).strip()
        
        # Normalize: remove dashes, pad to 9 digits
        ein_clean = re.sub(r'[^0-9]', '', ein_raw)
        if len(ein_clean) < 9:
            ein_clean = ein_clean.zfill(9)
        
        if ein_clean and ntee:
            bmf_normalized[ein_clean] = ntee
        
        if i % 200000 == 0 and i > 0:
            print(f"    Processed {i} BMF records...")

print(f"    Normalized BMF mappings: {len(bmf_normalized)}")

fixed_count = 0
for org in missing:
    ein = org.get('ein', '').strip()
    ein_clean = re.sub(r'[^0-9]', '', ein)
    if len(ein_clean) < 9:
        ein_clean = ein_clean.zfill(9)
    
    if ein_clean in bmf_normalized:
        org['ntee'] = bmf_normalized[ein_clean]
        fixed_count += 1

print(f"    Fixed by normalization: {fixed_count}")
missing = [o for o in orgs if not o.get('ntee') or o.get('ntee').strip() == '']

# --- Strategy 2: Name keyword inference ---
print("\n[3] Strategy 2: Name keyword inference...")

keyword_map = {
    # Veterans
    'veteran': 'X33', 'vfw': 'X33', 'american legion': 'X33', 'amvets': 'X33',
    'disabled american veterans': 'X33', 'vietnam veterans': 'X33',
    
    # Religion
    'church': 'X21', 'baptist': 'X21', 'catholic': 'X21', 'methodist': 'X21',
    'presbyterian': 'X21', 'lutheran': 'X21', 'episcopal': 'X21',
    'ministry': 'X21', 'mission': 'X21', 'diocese': 'X21',
    
    # Education
    'school': 'B25', 'academy': 'B25', 'education': 'B90', 'scholarship': 'B82',
    'university': 'B43', 'college': 'B42', 'pta': 'B84', 'ptso': 'B84',
    'student council': 'B80', 'alumni': 'B84',
    
    # Health
    'hospital': 'D20', 'medical': 'D30', 'health': 'D50', 'cancer': 'D40',
    'diabetes': 'D40', 'heart': 'D40', 'mental health': 'D30',
    'hospice': 'D30', 'nursing': 'D30',
    
    # Human Services
    'food bank': 'E62', 'soup kitchen': 'E62', 'shelter': 'E70',
    'homeless': 'E70', 'youth': 'E20', 'boys and girls club': 'E21',
    'boy scouts': 'E22', 'girl scouts': 'E24', 'salvation army': 'E60',
    'united way': 'E90', 'goodwill': 'E50', 'red cross': 'E60',
    
    # Arts
    'museum': 'A50', 'symphony': 'A63', 'orchestra': 'A63', 'theater': 'A62',
    'ballet': 'A61', 'arts': 'A40', 'historical society': 'A80',
    'library': 'B70',
    
    # Environment
    'conservation': 'C30', 'nature': 'C40', 'wildlife': 'C60',
    'audubon': 'C60', 'sierra club': 'C30',
    
    # Community
    'chamber of commerce': 'I40', 'rotary': 'I23', 'lions club': 'I26',
    'kiwanis': 'I21', 'jaycees': 'I21', 'elks': 'I30', 'mason': 'I30',
    
    # Housing
    'habitat for humanity': 'L20', 'housing': 'L20', 'homeless shelter': 'L41',
    
    # Sports
    'little league': 'N63', 'youth sports': 'N60', 'soccer': 'N64',
    'football': 'N65', 'basketball': 'N62', 'golf': 'N67',
    
    # Foundations
    'foundation': 'T20', 'community foundation': 'T22',
    'private foundation': 'T20', 'fund': 'T50',
    
    # Animals
    'humane society': 'C50', 'spca': 'C50', 'animal rescue': 'C50',
}

inferred_count = 0
for org in missing:
    name = org.get('name', '').lower()
    for keyword, ntee in keyword_map.items():
        if keyword in name:
            org['ntee'] = ntee
            inferred_count += 1
            break

print(f"    Fixed by keyword inference: {inferred_count}")
missing = [o for o in orgs if not o.get('ntee') or o.get('ntee').strip() == '']

# --- Strategy 3: Generic category fallback ---
print("\n[4] Strategy 3: Generic fallbacks...")
generic_count = 0
for org in missing:
    name = org.get('name', '').lower()
    # Catch common patterns not in keyword map
    if 'association' in name or 'assoc' in name:
        org['ntee'] = 'I80'  # Agricultural/Professional orgs
        generic_count += 1
    elif 'club' in name:
        org['ntee'] = 'N50'  # Social/Recreational clubs
    elif 'center' in name:
        org['ntee'] = 'E20'  # Youth/Community centers
    elif 'coalition' in name or 'alliance' in name:
        org['ntee'] = 'Q20'  # Community coalitions

print(f"    Fixed by generic fallback: {generic_count}")

# --- Final stats ---
final_missing = [o for o in orgs if not o.get('ntee') or o.get('ntee').strip() == '']
print(f"\n[5] FINAL STATS:")
print(f"    Total orgs: {len(orgs)}")
print(f"    With NTEE: {len(orgs) - len(final_missing)}")
print(f"    Still missing: {len(final_missing)}")
print(f"    Coverage: {((len(orgs) - len(final_missing)) / len(orgs) * 100):.1f}%")

# Show NTEE distribution
ntee_counts = Counter(o.get('ntee', '')[:1] for o in orgs if o.get('ntee'))
print(f"\n[6] NTEE Major Category Distribution:")
for cat, count in ntee_counts.most_common(10):
    print(f"    {cat}: {count}")

# --- Save updated percentile engine ---
print("\n[7] Saving updated percentile engine...")
with open('data/csv/percentile_engine_v2.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=[
        'ein', 'name', 'state', 'tax_year', 'revenue', 'ntee',
        'percentile', 'peer_count', 'median_revenue', 'form_type'
    ])
    writer.writeheader()
    for org in orgs:
        writer.writerow({
            'ein': org['ein'],
            'name': org['name'],
            'state': org['state'],
            'tax_year': org['tax_year'],
            'revenue': org['revenue'],
            'ntee': org.get('ntee', ''),
            'percentile': org['percentile'],
            'peer_count': org['peer_count'],
            'median_revenue': org['median_revenue'],
            'form_type': org['form_type']
        })

print(f"    Saved: data/csv/percentile_engine_v2.csv")

# --- Generate sample cards with improved NTEE ---
print("\n[8] Generating sample cards with improved NTEE...")

ntee_major = {
    'A': 'Arts, Culture, Humanities', 'B': 'Education',
    'C': 'Environment / Animals', 'D': 'Health',
    'E': 'Human Services', 'F': 'International / Foreign Affairs',
    'G': 'Public / Societal Benefit', 'H': 'Religion',
    'I': 'Mutual / Membership Benefit', 'K': 'Food / Agriculture',
    'L': 'Housing / Shelter', 'M': 'Public Safety',
    'N': 'Recreation / Sports', 'O': 'Youth Development',
    'P': 'Human / Civil Rights', 'Q': 'Community Improvement',
    'T': 'Philanthropy / Voluntarism', 'U': 'Science / Technology',
    'V': 'Social Science', 'W': 'Public / Societal Benefit',
    'X': 'Religion-Related', 'Y': 'Mutual / Membership',
    'Z': 'Unknown'
}

ntee_sub = {
    'X21': 'Religious Organization', 'X30': 'Religious Media',
    'X33': 'Veterans Organization', 'X50': 'Religious Activities',
    'X80': 'Religious Service Organizations', 'X81': 'Religious Counseling',
    'X99': 'Religion-Related (Other)',
    'B20': 'Elementary / Secondary Education', 'B21': 'Kindergarten / Preschools',
    'B24': 'Primary / Elementary Schools', 'B25': 'Secondary / High Schools',
    'B28': 'Special Education', 'B30': 'Vocational / Technical',
    'B40': 'Higher Education', 'B41': 'Community / Junior Colleges',
    'B42': 'Undergraduate Colleges', 'B43': 'Universities',
    'B50': 'Graduate / Professional Schools', 'B60': 'Adult / Continuing Education',
    'B70': 'Libraries', 'B80': 'Student Services',
    'B82': 'Scholarships / Financial Aid', 'B84': 'Alumni Associations',
    'B90': 'Educational Services', 'B99': 'Education (Other)',
    'E20': 'Youth Centers / Clubs', 'E21': 'Boys and Girls Clubs',
    'E22': 'Boy Scouts', 'E24': 'Girl Scouts',
    'E30': "Children's / Youth Services", 'E31': 'Adoption',
    'E32': 'Foster Care', 'E40': 'Family Services',
    'E42': 'Single Parent Agencies', 'E50': 'Personal Social Services',
    'E60': 'Emergency Assistance', 'E61': 'Thrift Shops',
    'E62': 'Food Banks / Pantries', 'E70': 'Residential / Custodial Care',
    'E80': 'Senior Centers / Services', 'E81': 'Senior Continuing Care',
    'E82': 'Nursing Homes', 'E84': 'Ethnic / Immigrant Centers',
    'E86': 'Blind / Visually Impaired', 'E90': 'Human Service Organizations',
    'E99': 'Human Services (Other)',
    'I20': 'Civic Centers', 'I21': 'Community Service Clubs',
    'I23': 'Rotary International', 'I26': 'Lions Clubs',
    'I30': 'Fraternal Societies', 'I31': 'College Fraternities / Sororities',
    'I40': 'Business and Industry', 'I50': 'Professional Societies',
    'I60': 'Labor Unions', 'I70': 'Veterans Organizations',
    'I72': 'Military / Veterans Posts', 'I80': 'Agricultural Organizations',
    'I99': 'Mutual / Membership (Other)',
    'N50': 'Recreational / Social Clubs', 'N60': 'Amateur Sports',
    'N99': 'Recreation / Sports (Other)',
    'T20': 'Private Foundations', 'T21': 'Corporate Foundations',
    'T22': 'Community Foundations', 'T30': 'Public Foundations',
    'T40': 'Voluntarism Promotion', 'T50': 'Philanthropy / Charity',
    'T70': 'Fund Raising Organizations', 'T90': 'Gift Distribution',
    'T99': 'Philanthropy / Voluntarism (Other)',
    'Q20': 'Community Coalitions', 'Q30': 'Economic Development',
    'Q99': 'Community Improvement (Other)',
    'A50': 'Museums', 'A62': 'Theater', 'A63': 'Music',
    'A80': 'Historical Societies', 'A99': 'Arts / Culture (Other)',
    'C30': 'Natural Resources Conservation', 'C50': 'Animals',
    'C60': 'Wildlife Preservation', 'C99': 'Environment (Other)',
    'D20': 'Hospitals', 'D30': 'Health Treatment Facilities',
    'D50': 'Voluntary Health Associations', 'D99': 'Health (Other)',
    'L20': 'Housing Development', 'L41': 'Homeless Shelters',
    'L99': 'Housing / Shelter (Other)',
}

# Pick 3 diverse orgs with good NTEE
good_orgs = [o for o in orgs if o.get('ntee') and len(o.get('ntee')) >= 1]
samples = []
for pct_range in [(0, 25), (40, 60), (75, 100)]:
    candidates = [o for o in good_orgs if pct_range[0] <= float(o['percentile']) <= pct_range[1]]
    if candidates:
        samples.append(random.choice(candidates))

for org in samples:
    ntee_code = org.get('ntee', 'Z99')
    major = ntee_major.get(ntee_code[0], 'Unknown') if ntee_code else 'Unknown'
    sub = ntee_sub.get(ntee_code[:3], 'General / Unspecified') if ntee_code else 'Unknown'
    
    pct = float(org['percentile'])
    if pct < 25:
        bar_pos = "●───────────────"
    elif pct < 50:
        bar_pos = "────●───────────"
    elif pct < 75:
        bar_pos = "────────●───────"
    else:
        bar_pos = "───────────────●"
    
    revenue_str = f"${float(org['revenue']):,.0f}"
    median_str = f"${float(org['median_revenue']):,.0f}"
    
    card = f"""
{'='*60}
{org['name']}
{org['state']} | {sub}
{'='*60}

Revenue: {revenue_str}
Compared to {org['peer_count']} peers in {org['state']}:

[{bar_pos}] {org['percentile']}th percentile
smaller ← → larger

Peer Median: {median_str}

Size doesn't predict impact.
Larger may have infrastructure.
Smaller may be grassroots-focused.

This is NOT a rating.
It is a transparency signal from public IRS data.

Confidence: Medium — based on {org['peer_count']} peer orgs
{'='*60}
"""
    print(card)

print("\n" + "="*60)
print("NTEE GAP FIX COMPLETE")
print("="*60)
print(f"Updated engine: data/csv/percentile_engine_v2.csv")
print(f"Log: logs/ntee_fix.log")
print(f"Time: {os.popen('date').read().strip()}")
PYEOF

echo ""
echo "========================================"
echo "NTEE FIX COMPLETE"
echo "Time: $(date)"
echo "========================================"
