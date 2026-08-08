"""Compare old vs new mission prompt quality on 10 orgs."""
import sqlite3, requests, json, re, sys

DB      = str(__import__('pathlib').Path.home() / 'meritgiving/data/merit_registry.db')
GEN_URL = 'http://127.0.0.1:8080/v1/chat/completions'
MODEL   = 'deepseek-r1-distill-qwen-14b'

NTEE_LABELS = {
    'A':'arts, culture, and humanities','B':'education','C':'environment',
    'D':'animal welfare','E':'health care','F':'mental health',
    'G':'disease research and prevention','H':'medical research',
    'I':'crime and legal services','J':'employment','K':'food and agriculture',
    'L':'housing and shelter','M':'public safety and disaster relief',
    'N':'recreation, sports, and leisure','O':'youth development',
    'P':'human services','Q':'international affairs','R':'civil rights',
    'S':'community development','T':'philanthropy and grantmaking',
    'U':'science and technology','V':'social science','W':'public benefit',
    'X':'religion','Y':'mutual benefit and membership','Z':'unknown',
}

FEW_SHOT = """\
Examples of good mission sentences — the org NAME is the primary clue; sector confirms it:

name="Springfield Meals on Wheels" sector="human services" location="Springfield, IL"
→ Delivers hot meals to homebound elderly and disabled residents across Springfield.

name="Boys & Girls Club of Greater Milwaukee" sector="youth development" location="Milwaukee, WI"
→ Provides after-school programs, mentorship, and safe spaces for young people in Milwaukee.

name="Trout Unlimited — Rocky Mountain Chapter" sector="environment" location="Denver, CO"
→ Protects and restores cold-water fisheries and trout habitat across the Rocky Mountain region.

name="St. Vincent de Paul Society of Omaha" sector="human services" location="Omaha, NE"
→ Operates food pantries, clothing assistance, and emergency financial aid for people in need in Omaha.

name="Rotary Club of San Jose Foundation" sector="philanthropy and grantmaking" location="San Jose, CA"
→ Awards community grants and supports international development projects through the Rotary Club network.

Rules:
- Read the NAME first — it usually says what the org does.
- Sector confirms the category; use it when the name is ambiguous.
- One sentence, present tense.
- Do NOT repeat the full org name in the mission.
- Do NOT use: "is dedicated to", "strives to", "committed to", "passionate about".
- Do NOT invent specific statistics, dollar amounts, or named programs.
- If the name is just a person's name or acronym, infer from sector + location.
"""

def org_line(org):
    ntee = NTEE_LABELS.get(org.get('NTEE1') or 'Z', 'general nonprofit')
    rev  = org.get('total_revenue')
    size = f"${rev:,.0f} annual revenue" if rev else "small community"
    return (f'  {{"ein": "{org["EIN"]}", "name": "{org["organization_name"]}", '
            f'"sector": "{ntee}", "location": "{org.get("CITY","")}, {org.get("STATE","")}", '
            f'"size": "{size}"}}')

def build_old(batch):
    orgs = "[\n" + ",\n".join(org_line(o) for o in batch) + "\n]"
    return (
        "You write factual, neutral one-sentence descriptions of US nonprofit organizations "
        "based on their name, sector, and location. "
        "Do not invent specific programs, claims, or statistics. "
        "Do not use words like dedicated, committed, passionate, or strives. "
        "Write in present tense. Be specific to the sector and name where possible.\n\n"
        "For each organization below, write one sentence describing what it likely does. "
        'Return ONLY a JSON array: [{"ein": "...", "mission": "..."}]\n\n'
        "Organizations:\n" + orgs
    )

def build_new(batch):
    orgs = "[\n" + ",\n".join(org_line(o) for o in batch) + "\n]"
    return (
        FEW_SHOT + "\n"
        "Now write mission sentences for these organizations. "
        'Return ONLY a JSON array: [{"ein": "...", "mission": "..."}]\n\n'
        "Organizations:\n" + orgs
    )

def call_llm(prompt_text, batch_size):
    payload = {
        'model': MODEL,
        'messages': [
            {'role': 'system', 'content': 'You output only raw JSON arrays. No markdown, no explanation, no code blocks.'},
            {'role': 'user',   'content': prompt_text},
        ],
        'temperature': 0.1,
        'max_tokens': max(1200, 100 * batch_size),
    }
    r = requests.post(GEN_URL, json=payload, timeout=240)
    msg     = r.json()['choices'][0]['message']
    content = msg.get('content') or msg.get('reasoning_content') or ''
    m = re.search(r'\[.*\]', content, re.DOTALL)
    if not m:
        return {}
    try:
        items = json.loads(m.group())
        return {i['ein']: i['mission'] for i in items if 'ein' in i and 'mission' in i}
    except Exception:
        return {}

def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute("""
        SELECT EIN, organization_name, NTEE1, CITY, STATE, total_revenue
        FROM registry_enriched
        WHERE mission_source = 'ai_ntee' AND merit_score IS NOT NULL
        ORDER BY RANDOM() LIMIT 10
    """)]

    print("=== TEST SET ===")
    for o in rows:
        print(f"  {o['organization_name']} ({o['CITY']}, {o['STATE']}) NTEE={o['NTEE1']}")

    print("\n=== OLD PROMPT ===")
    old = call_llm(build_old(rows), len(rows))
    for o in rows:
        print(f"\n  [{o['organization_name']}]")
        print(f"    {old.get(o['EIN'], '(no result)')}")

    print("\n\n=== NEW PROMPT ===")
    new = call_llm(build_new(rows), len(rows))
    for o in rows:
        print(f"\n  [{o['organization_name']}]")
        print(f"    {new.get(o['EIN'], '(no result)')}")

if __name__ == '__main__':
    main()
