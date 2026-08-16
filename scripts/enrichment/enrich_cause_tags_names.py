#!/usr/bin/env python3
"""
enrich_cause_tags_names.py
Fast keyword-based cause_tags enrichment using org names.
Zero GPU, zero API — runs in seconds on the full dataset.

Targets orgs where cause_tags IS NULL/empty AND NTEE1 IS NULL/empty
(the 593K that the NTEE mapper couldn't tag).

Usage:
    python3 scripts/enrich_cause_tags_names.py
    python3 scripts/enrich_cause_tags_names.py --dry-run
"""

import sqlite3, json, re, argparse, time, os

DB_PATH = os.path.expanduser("~/meritgiving/data/merit_registry.db")
BATCH   = 50_000

# ── Keyword rules ──────────────────────────────────────────────────────────
# Each rule: (regex_pattern, tags_to_assign)
# Rules are applied in order; all matching rules contribute tags.
# Use word-boundary aware patterns (\b) to avoid partial matches.

RULES: list[tuple[re.Pattern, list[str]]] = []

def _r(pattern: str, tags: list[str]):
    RULES.append((re.compile(pattern, re.IGNORECASE), tags))

# Religion (most common no-NTEE category)
_r(r'\b(church|churches|chapel|cathedral|parish|diocese)\b',
   ["religion", "faith"])
_r(r'\b(synagogue|shul)\b',
   ["religion", "faith", "jewish"])
_r(r'\b(temple|congregation)\b',
   ["religion", "faith"])
_r(r'\b(mosque|masjid|islamic center|muslim)\b',
   ["religion", "faith", "islamic"])
_r(r'\b(ministry|ministries|mission|missions|missionary)\b',
   ["religion", "faith"])
_r(r'\b(fellowship|congregation|worship|gospel|bible|biblical)\b',
   ["religion", "faith"])
_r(r'\b(calvary|trinity|bethel|bethlehem|cornerstone|emmanuel|immanuel|zion)\b',
   ["religion", "faith"])
_r(r'\b(christian|christ|salvation|holy|blessed|sacred|saint|apostolic|pentecostal)\b',
   ["religion", "faith"])
_r(r'\b(catholic|protestant|baptist|lutheran|methodist|presbyterian|episcopal|adventist)\b',
   ["religion", "faith"])
_r(r'\b(latter.?day.?saints|lds|mormo)\b',
   ["religion", "faith"])
_r(r'\b(jewish|judaism|jewish|hebrew|torah|talmud|rabbi)\b',
   ["religion", "faith", "jewish"])
_r(r'\b(buddhist|buddhism|dharma|sangha|zen)\b',
   ["religion", "faith"])
_r(r'\b(hindu|hinduism|vedic|mandir)\b',
   ["religion", "faith"])

# Education
_r(r'\b(school|academy|academies|learning|educational|education)\b',
   ["education"])
_r(r'\b(literacy|literate|tutoring|tutors?|mentoring|mentor)\b',
   ["education", "literacy"])
_r(r'\b(scholarship|scholarships|grant.?in.?aid)\b',
   ["education", "scholarships"])
_r(r'\b(college|university|institute|seminary)\b',
   ["education", "higher education"])
_r(r'\b(preschool|pre.?school|kindergarten|daycare|day.?care|childcare)\b',
   ["education", "early childhood"])
_r(r'\b(library|libraries)\b',
   ["education", "library"])
_r(r'\bpta\b|\bptsa\b|\bparent.?teacher\b',
   ["education", "school support"])

# Health & Medical
_r(r'\b(health|healthcare|medical|medicine|hospital|clinic|clinics)\b',
   ["health", "healthcare"])
_r(r'\b(hospice|palliative|nursing home|convalescent)\b',
   ["health", "hospice"])
_r(r'\b(dental|dentistry|oral health)\b',
   ["health", "dental"])
_r(r'\b(vision|optometry|ophthalmology|eye care|eyecare)\b',
   ["health", "vision"])
_r(r'\b(ambulance|ems|emergency medical|paramedic)\b',
   ["health", "emergency services"])

# Mental Health
_r(r'\b(mental health|behavioral health|psychiatric|psychology|counseling|counselor)\b',
   ["mental health", "counseling"])
_r(r'\b(substance abuse|drug abuse|alcohol abuse|addiction|recovery|rehab|sobriety)\b',
   ["mental health", "substance abuse", "recovery"])
_r(r'\b(suicide prevention|crisis hotline|crisis line|crisis center)\b',
   ["mental health", "crisis support"])
_r(r'\b(domestic violence|battered|abuse shelter|safe house)\b',
   ["mental health", "domestic violence", "crisis support"])

# Food & Hunger
_r(r'\b(food bank|food pantry|food shelf|food kitchen|soup kitchen|food closet)\b',
   ["food", "hunger relief"])
_r(r'\b(hunger|hungry|starving|starvation|malnutrition|famine)\b',
   ["food", "hunger relief"])
_r(r'\b(meals on wheels|congregate meals|hot meals|meal delivery)\b',
   ["food", "senior meals"])
_r(r'\b(gleaning|gleaners|harvest|food rescue|food recovery)\b',
   ["food", "hunger relief"])

# Housing
_r(r'\b(habitat for humanity|habitat humanity)\b',
   ["housing", "affordable housing"])
_r(r'\b(housing|affordable housing|homeownership)\b',
   ["housing"])
_r(r'\b(homeless|homelessness|shelter|transitional living|transitional housing)\b',
   ["housing", "homelessness"])

# Animals
_r(r'\b(humane society|animal shelter|animal rescue|spca|aspca|rspca)\b',
   ["animals", "animal welfare"])
_r(r'\b(animal|animals|pet rescue|pet adoption|dog rescue|cat rescue|feline|canine)\b',
   ["animals"])
_r(r'\b(wildlife|wild.?life|nature preserve|nature sanctuary|bird sanctuary)\b',
   ["animals", "wildlife"])
_r(r'\b(zoo|aquarium|wildlife park|safari)\b',
   ["animals", "wildlife"])

# Environment
_r(r'\b(environment|environmental|conservation|conservancy|ecology|ecological)\b',
   ["environment", "conservation"])
_r(r'\b(green|sustainability|sustainable|climate|clean energy|renewable)\b',
   ["environment", "sustainability"])
_r(r'\b(land trust|nature conservancy|trail|watershed|river|lake|ocean)\b',
   ["environment", "conservation"])
_r(r'\b(garden club|gardening|horticultural|botanical)\b',
   ["environment", "horticulture"])
_r(r'\b(recycling|recycle|zero waste|composting)\b',
   ["environment", "recycling"])

# Youth
_r(r'\b(youth|young people|teenagers|teen|adolescent)\b',
   ["youth", "youth development"])
_r(r'\b(children|child|kids|infant|toddler|juvenile)\b',
   ["youth", "children"])
_r(r'\b(boy scouts?|cub scouts?|girl scouts?|scouting|4-h|four.?h)\b',
   ["youth", "scouting"])
_r(r'\b(ymca|ywca|young men.?s|young women.?s|boys? and girls? club)\b',
   ["youth", "recreation"])
_r(r'\b(after.?school|summer camp|summer program)\b',
   ["youth", "youth programs"])

# Veterans & Military
_r(r'\b(veteran|veterans?|vfw|american legion|purple heart|gold star|military family|military families)\b',
   ["veterans", "military"])
_r(r'\b(armed forces|army|navy|marine|air force|coast guard|national guard)\b',
   ["veterans", "military"])

# Arts & Culture (exclude martial arts — handled under Recreation)
_r(r'\b(arts?|artistic|artisan|fine arts|visual arts)\b(?!.*martial)',
   ["arts"])
_r(r'\b(museum|gallery|galleries|exhibit)\b',
   ["arts", "museum"])
_r(r'\b(theater|theatre|drama|performing arts|playhouse|opera)\b',
   ["arts", "theater"])
_r(r'\b(music|musical|orchestra|symphony|philharmonic|choir|chorus|choral|band|ensemble)\b',
   ["arts", "music"])
_r(r'\b(dance|ballet|contemporary dance|folk dance)\b',
   ["arts", "dance"])
_r(r'\b(cultural|heritage|ethnic|folklore|folk art)\b',
   ["arts", "culture"])
_r(r'\b(historic|historical|history|heritage|preservation)\b',
   ["arts", "historic preservation"])
_r(r'\b(library|libraries|literary|literature|poetry|writing)\b',
   ["arts", "literature"])

# Recreation & Sports
_r(r'\b(sports?|athletic|athletics|recreation|recreational)\b',
   ["recreation", "sports"])
_r(r'\b(baseball|softball|little league)\b',
   ["recreation", "baseball"])
_r(r'\b(soccer|football|gridiron)\b',
   ["recreation", "sports"])
_r(r'\b(basketball|hoops)\b',
   ["recreation", "basketball"])
_r(r'\b(swimming|swim club|aquatics|water polo)\b',
   ["recreation", "swimming"])
_r(r'\b(golf|tennis|lacrosse|volleyball|wrestling|gymnastics|rowing|cycling|running|marathon)\b',
   ["recreation", "sports"])
_r(r'\b(hockey|ice skating|figure skating|skiing|snowboard)\b',
   ["recreation", "sports"])

# Senior
_r(r'\b(senior|seniors?|elderly|elder|aging|gerontology|retirement|aged)\b',
   ["senior services"])
_r(r'\b(alzheimer|dementia|memory care)\b',
   ["senior services", "dementia"])

# Disability
_r(r'\b(disability|disabled|handicap|special needs|developmental disabilities|autism|autistic)\b',
   ["disability services"])
_r(r'\b(blind|visually impaired|deaf|hearing impaired|hearing loss)\b',
   ["disability services"])
_r(r'\b(cerebral palsy|down syndrome|intellectual disability|developmental delay)\b',
   ["disability services"])

# Civil Rights & Advocacy
_r(r'\b(civil rights|voting rights|voter registration|civic engagement)\b',
   ["civil rights", "advocacy"])
_r(r'\b(immigration|immigrant|refugee|asylum|undocumented)\b',
   ["immigration", "refugee services"])
_r(r'\b(lgbtq|lgbt|gay|lesbian|transgender|queer|pride)\b',
   ["civil rights", "LGBTQ"])
_r(r'\b(womens?|feminist|gender equity|gender equality)\b',
   ["civil rights", "women's rights"])

# International
_r(r'\b(international|global|worldwide|overseas|africa|asia|latin america|developing world)\b',
   ["international"])
_r(r'\b(relief|humanitarian|aid organization|disaster relief)\b',
   ["international", "disaster relief"])

# Community & Civic
_r(r'\b(rotary|lions club|kiwanis|elks lodge|moose lodge|eagles|vfw post)\b',
   ["community", "civic"])
_r(r'\b(community foundation|united way|community fund)\b',
   ["philanthropy", "community"])
_r(r'\b(fire department|fire company|volunteer fire|fire station|rescue squad)\b',
   ["public safety", "fire"])
_r(r'\b(public safety|emergency management|disaster preparedness)\b',
   ["public safety", "emergency services"])

# Employment
_r(r'\b(workforce|job training|vocational|employment|career)\b',
   ["employment", "job training"])

# Martial arts (before generic arts rule fires)
_r(r'\b(martial arts?|karate|taekwondo|judo|jiu.?jitsu|boxing|wrestling|mma)\b',
   ["recreation", "sports", "martial arts"])

# Research
_r(r'\b(research institute|research foundation|research center)\b',
   ["research"])

# STEM / Science
_r(r'\b(stem|science|technology|engineering|mathematics|coding|robotics)\b',
   ["education", "science"])

# Philanthropy / Foundations
_r(r'\b(family foundation|charitable foundation|private foundation|community foundation|united way)\b',
   ["philanthropy"])

# Additional religion signals
_r(r'\b(divine|sacred|blessed|holy spirit|holy ghost|lord jesus|our savior|redeemer)\b',
   ["religion", "faith"])
_r(r'\b(kehilla|kehillas|shul|yeshiva|mikvah|chabad|lubavitch|beth israel|beit)\b',
   ["religion", "faith", "jewish"])
_r(r'\b(alumnae|alumni association|alma mater)\b',
   ["education"])
_r(r'\b(redevelopment|urban renewal|revitalization|corridor)\b',
   ["community development"])
_r(r'\b(hospice|palliative care|end.?of.?life)\b',
   ["health", "hospice"])


def apply_rules(name: str) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for pattern, tags in RULES:
        if pattern.search(name):
            for t in tags:
                if t not in seen:
                    seen.add(t)
                    result.append(t)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    todo = db.execute("""
        SELECT COUNT(*) FROM registry_enriched
        WHERE (cause_tags IS NULL OR cause_tags = '')
          AND (NTEE1 IS NULL OR NTEE1 = '')
    """).fetchone()[0]
    print(f"Orgs with no NTEE and no tags: {todo:,}")

    if args.dry_run:
        rows = db.execute("""
            SELECT organization_name FROM registry_enriched
            WHERE (cause_tags IS NULL OR cause_tags = '')
              AND (NTEE1 IS NULL OR NTEE1 = '')
            ORDER BY RANDOM() LIMIT 20
        """).fetchall()
        matched = sum(1 for r in rows if apply_rules(r[0]))
        print(f"\nSample (20 random):  {matched}/20 would get tags\n")
        for r in rows:
            tags = apply_rules(r[0])
            print(f"  {'✓' if tags else '·'} {r[0][:60]:<60}  →  {tags}")
        db.close()
        return

    start = time.time()
    offset = 0
    written = 0
    skipped = 0

    while True:
        rows = db.execute("""
            SELECT EIN, organization_name FROM registry_enriched
            WHERE (cause_tags IS NULL OR cause_tags = '')
              AND (NTEE1 IS NULL OR NTEE1 = '')
            LIMIT ? OFFSET ?
        """, (BATCH, offset)).fetchall()
        if not rows:
            break

        updates = []
        for r in rows:
            tags = apply_rules(r["organization_name"] or "")
            if tags:
                updates.append((json.dumps(tags), r["EIN"]))
            else:
                skipped += 1

        if updates:
            db.executemany(
                "UPDATE registry_enriched SET cause_tags = ? WHERE EIN = ?",
                updates,
            )
            db.commit()
            written += len(updates)

        offset += BATCH
        print(f"  {written:>8,} tagged | {skipped:>8,} unmatched | {offset:>9,} processed", end="\r")

    elapsed = time.time() - start
    match_rate = written / todo * 100 if todo else 0
    print(f"\n\nDone in {elapsed:.1f}s")
    print(f"  Tagged:      {written:,}  ({match_rate:.1f}% of target)")
    print(f"  Unmatched:   {skipped:,}  (still need Ollama)")
    db.close()


if __name__ == "__main__":
    main()
