#!/usr/bin/env python3
"""
enrich_cause_tags_mission.py
Extract cause tags from mission statement text.

Runs keyword rules against mission text (richer signals than org names),
then optionally uses Ollama for orgs that rules can't classify.
Additive: never removes existing tags, only adds new ones.

Usage:
    python3 scripts/enrich_cause_tags_mission.py --dry-run
    python3 scripts/enrich_cause_tags_mission.py
    python3 scripts/enrich_cause_tags_mission.py --ollama        # also run Ollama pass
    python3 scripts/enrich_cause_tags_mission.py --limit 500
"""

import sqlite3, json, re, argparse, time, os, requests

DB_PATH = os.path.expanduser("~/meritgiving/data/merit_registry.db")
BATCH   = 10_000
OLLAMA_URL   = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:7b"

# ── Keyword rules on mission text ──────────────────────────────────────────────
# Patterns are matched against full mission text (lower-cased).
# More specific / phrase-level rules than the name-based extractor.

RULES: list[tuple[re.Pattern, list[str]]] = []

def _r(pattern: str, tags: list[str]):
    RULES.append((re.compile(pattern, re.IGNORECASE), tags))

# ── Education ──────────────────────────────────────────────────────────────────
_r(r'\b(after.?school|out.?of.?school time)\b',          ["education", "after-school"])
_r(r'\b(tutoring|academic support|homework help)\b',     ["education", "tutoring"])
_r(r'\b(college.?prep|college.?access|higher.?ed access|first.?generation)\b', ["education", "college access"])
_r(r'\b(early.?childhood|early.?learning|pre.?k|kindergarten readiness)\b',    ["education", "early childhood"])
_r(r'\b(stem education|science education|math education|coding education)\b',  ["education", "STEM"])
_r(r'\b(special.?ed|learning disabilit|dyslexia|iep)\b', ["education", "special education"])
_r(r'\b(vocational|trade.?school|job.?skill|workforce training|apprenticeship)\b', ["education", "vocational training"])
_r(r'\b(scholarships?|financial.?aid|tuition.?assist)\b',["education", "scholarships"])
_r(r'\b(parent.?teacher|pta\b|school.?parent)\b',        ["education", "school support"])
_r(r'\b(literacy|reading program|reading skill|adult.?literacy|ESL|english.?as.?a.?second)\b', ["education", "literacy"])
_r(r'\b(library|book.?access|reading.?room)\b',          ["education", "library"])

# ── Youth & Children ───────────────────────────────────────────────────────────
_r(r'\b(at.?risk youth|underserved youth|youth development|positive youth)\b', ["youth", "youth development"])
_r(r'\b(mentoring youth|youth mentor|big brother|big sister)\b',               ["youth", "mentoring"])
_r(r'\b(summer.?camp|summer.?program|summer.?learning)\b',                     ["youth", "summer programs"])
_r(r'\b(foster.?youth|foster.?care|aging.?out.?of.?foster)\b',                ["youth", "foster care"])
_r(r'\b(juvenile.?justice|youth.?detention|court.?involved)\b',                ["youth", "juvenile justice"])
_r(r'\b(child.?abuse|child.?protect|safe.?children)\b',                        ["youth", "child protection"])
_r(r'\b(childcare|child.?care|affordable.?childcare)\b',                       ["youth", "childcare"])

# ── Food & Hunger ──────────────────────────────────────────────────────────────
_r(r'\b(food.?insecurity|food.?access|hunger.?relief|alleviate.?hunger)\b',   ["food", "hunger relief"])
_r(r'\b(food.?bank|food.?pantry|food.?shelf|emergency.?food)\b',              ["food", "hunger relief"])
_r(r'\b(healthy.?eating|nutritious.?food|nutrition.?education)\b',             ["food", "nutrition"])
_r(r'\b(school.?lunch|school.?meal|free.?meal.?program|feeding.?children)\b', ["food", "school meals"])
_r(r'\b(urban.?agriculture|community.?garden|local.?food|food.?desert)\b',    ["food", "food access"])

# ── Housing & Homelessness ─────────────────────────────────────────────────────
_r(r'\b(affordable.?housing|low.?income.?housing|housing.?stability)\b',       ["housing", "affordable housing"])
_r(r'\b(homeless|unhoused|experiencing.?houselessness)\b',                     ["housing", "homelessness"])
_r(r'\b(transitional.?housing|transitional.?living|rapid.?rehousing)\b',       ["housing", "transitional housing"])
_r(r'\b(eviction.?prevention|prevent.?eviction|housing.?crisis)\b',            ["housing", "eviction prevention"])

# ── Health ─────────────────────────────────────────────────────────────────────
_r(r'\b(primary.?care|preventive.?care|health.?equity|health.?disparit)\b',   ["health", "health equity"])
_r(r'\b(chronic.?disease|diabetes|hypertension|cardiovascular)\b',             ["health", "chronic disease"])
_r(r'\b(cancer|oncology|tumor|chemotherapy|radiation.?therapy)\b',             ["health", "cancer"])
_r(r'\b(maternal.?health|prenatal.?care|infant.?mortality|birth.?outcome)\b', ["health", "maternal health"])
_r(r'\b(rural.?health|underserved.?communit|medically.?underserved)\b',        ["health", "health equity"])
_r(r'\b(HIV|AIDS|sexual.?health|reproductive.?health)\b',                      ["health", "sexual health"])
_r(r'\b(telehealth|community.?health.?worker|health.?navigator)\b',            ["health", "community health"])
_r(r'\b(free.?clinic|charitable.?clinic|safety.?net.?clinic)\b',              ["health", "free clinic"])

# ── Mental Health ──────────────────────────────────────────────────────────────
_r(r'\b(trauma.?informed|trauma.?recovery|trauma.?survivor)\b',                ["mental health", "trauma"])
_r(r'\b(suicide.?prevention|suicidal|crisis.?intervention)\b',                 ["mental health", "crisis support"])
_r(r'\b(grief|bereavement|loss.?support)\b',                                   ["mental health", "grief support"])
_r(r'\b(depression|anxiety|PTSD|post.?traumatic)\b',                           ["mental health"])
_r(r'\b(substance.?use|substance.?abuse|addiction.?recovery|opioid|alcohol.?misuse)\b', ["mental health", "substance abuse", "recovery"])
_r(r'\b(domestic.?violence|intimate.?partner|abuse.?survivor|battered)\b',    ["mental health", "domestic violence"])

# ── Racial & Social Equity ────────────────────────────────────────────────────
_r(r'\b(racial.?equity|racial.?justice|anti.?racism|systemic.?racism)\b',     ["civil rights", "racial equity"])
_r(r'\b(people.?of.?color|BIPOC|Black.?communit|Latino.?communit|Latinx)\b',  ["civil rights", "racial equity"])
_r(r'\b(economic.?mobility|economic.?opportunity|wealth.?gap|income.?inequal)\b', ["civil rights", "economic equity"])
_r(r'\b(voting.?right|civic.?participation|voter.?access|civic.?engagement)\b', ["civil rights", "voting rights"])

# ── Immigration ────────────────────────────────────────────────────────────────
_r(r'\b(immigrant|immigration|undocumented|DACA|naturalization)\b',            ["immigration"])
_r(r'\b(refugee|asylum.?seeker|resettlement|newly.?arrived)\b',                ["immigration", "refugee services"])

# ── Employment & Economic Dev ──────────────────────────────────────────────────
_r(r'\b(job.?placement|job.?training|employment.?training|workforce.?development)\b', ["employment", "job training"])
_r(r'\b(small.?business|entrepreneurship|micro.?enterprise|startup.?support)\b',      ["employment", "entrepreneurship"])
_r(r'\b(financial.?literacy|financial.?capability|asset.?building)\b',               ["employment", "financial literacy"])
_r(r'\b(living.?wage|poverty.?alleviation|economic.?empowerment)\b',                 ["employment", "economic empowerment"])

# ── Environment ───────────────────────────────────────────────────────────────
_r(r'\b(climate.?change|greenhouse.?gas|carbon.?emission|clean.?energy)\b',   ["environment", "climate"])
_r(r'\b(clean.?water|water.?quality|water.?access|watershed.?protect)\b',     ["environment", "water"])
_r(r'\b(air.?quality|air.?pollution|clean.?air)\b',                            ["environment", "air quality"])
_r(r'\b(land.?conservation|open.?space|habitat.?protect|biodiversity)\b',     ["environment", "conservation"])
_r(r'\b(environmental.?justice|frontline.?communit|pollution.?burden)\b',     ["environment", "environmental justice"])

# ── Veterans ───────────────────────────────────────────────────────────────────
_r(r'\b(veteran|military.?service.?member|service.?member|active.?duty)\b',   ["veterans"])
_r(r'\b(PTSD.*(veteran|military)|veteran.*PTSD)\b',                            ["veterans", "mental health", "PTSD"])
_r(r'\b(veteran.*homeless|homeless.*veteran)\b',                               ["veterans", "homelessness"])
_r(r'\b(military.?famil|gold.?star.?famil)\b',                                 ["veterans", "military families"])

# ── Disability ─────────────────────────────────────────────────────────────────
_r(r'\b(disability|disabled.?person|people.?with.?disabilit)\b',              ["disability services"])
_r(r'\b(autism|autistic|ASD)\b',                                               ["disability services", "autism"])
_r(r'\b(intellectual.?disabilit|developmental.?disabilit|down.?syndrome)\b',  ["disability services"])
_r(r'\b(mental.?health.*(workforce|employment)|supported.?employment)\b',     ["disability services", "employment"])
_r(r'\b(independent.?living|disability.?rights|ADA.?advocacy)\b',             ["disability services", "advocacy"])

# ── Seniors ────────────────────────────────────────────────────────────────────
_r(r'\b(older.?adult|senior.?citizen|aging.?in.?place|aging.?population)\b',  ["senior services"])
_r(r'\b(alzheimer|dementia|memory.?care|cognitive.?decline)\b',               ["senior services", "dementia"])
_r(r'\b(elder.?care|eldercare|caregiver.?support|family.?caregiver)\b',       ["senior services", "caregiving"])

# ── Arts & Culture ─────────────────────────────────────────────────────────────
_r(r'\b(arts.?education|teach.*art|art.*school|creative.?youth)\b',           ["arts", "arts education"])
_r(r'\b(public.?art|community.?mural|street.?art)\b',                         ["arts", "public art"])
_r(r'\b(cultural.?heritage|ethnic.?heritage|cultural.?preservation)\b',       ["arts", "culture"])
_r(r'\b(performing.?arts|theater.?program|dance.?program|music.?program)\b',  ["arts", "performing arts"])

# ── Animals & Wildlife ─────────────────────────────────────────────────────────
_r(r'\b(animal.?welfare|animal.?rescue|animal.?shelter|cruelty.?prevention)\b', ["animals", "animal welfare"])
_r(r'\b(wildlife.?rehabilitation|wildlife.?conservation|endangered.?species)\b', ["animals", "wildlife"])
_r(r'\b(spay.?neuter|trap.?neuter.?return|feral.?cat)\b',                      ["animals", "animal welfare"])

# ── International ─────────────────────────────────────────────────────────────
_r(r'\b(global.?health|international.?development|developing.?countr)\b',     ["international"])
_r(r'\b(disaster.?relief|emergency.?relief|humanitarian.?crisis)\b',          ["international", "disaster relief"])
_r(r'\b(humanitarian.?aid.*(global|international|overseas|abroad)|international.*humanitarian.?aid)\b', ["international", "disaster relief"])
_r(r'\b(clean.?water.*(Africa|Asia|Haiti|global)|global.*clean.?water)\b',    ["international", "water"])

# ── Human Trafficking ─────────────────────────────────────────────────────────
_r(r'\b(human.?trafficking|sex.?trafficking|labor.?trafficking|modern.?slavery|exploitation.*(women|youth|child))\b', ["civil rights", "human trafficking", "crisis support"])
_r(r'\b(survivor.?support|trafficking.?survivor|trafficking.?victim)\b',      ["civil rights", "human trafficking"])

# ── Public Safety ─────────────────────────────────────────────────────────────
_r(r'\b(violence.?prevention|community.?safety|gun.?violence|shootings?)\b',  ["public safety", "violence prevention"])
_r(r'\b(reentry|formerly.?incarcerated|second.?chance|prison.?reform)\b',     ["public safety", "reentry"])
_r(r'\b(restorative.?justice|alternatives.?to.?incarceration)\b',             ["public safety", "restorative justice"])

# ── Faith ─────────────────────────────────────────────────────────────────────
_r(r'\b(faith.?based|ministering|spiritual.?care|pastoral.?care)\b',          ["religion", "faith"])
_r(r'\b(serve.*(poor|needy|marginalized).*faith|faith.*serve.*(poor|needy))\b', ["religion", "faith-based services"])


def apply_rules(mission: str) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for pattern, tags in RULES:
        if pattern.search(mission):
            for t in tags:
                if t not in seen:
                    seen.add(t)
                    result.append(t)
    return result


def merge_tags(existing: list[str], new: list[str]) -> list[str]:
    existing_lower = {t.lower() for t in existing}
    added = [t for t in new if t.lower() not in existing_lower]
    return existing + added


def ollama_tag(name: str, mission: str) -> list[str] | None:
    text = f"{name}. {mission[:400]}"
    prompt = f"""Tag this nonprofit for a donor discovery platform.

Org: {text}

Return ONLY a JSON array of 3-6 specific cause tags. Use concrete terms like "after-school programs", "food insecurity", "affordable housing", "veterans", "wildlife conservation".
No generic terms like "community" or "support" alone.

Tags:"""
    try:
        r = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 100}
        }, timeout=60)
        text_out = r.json().get("response", "").strip()
        m = re.search(r"\[.*?\]", text_out, re.DOTALL)
        if m:
            tags = json.loads(m.group())
            return [str(t).strip() for t in tags if t][:6]
    except Exception as e:
        print(f"  ollama error: {e}")
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--ollama", action="store_true", help="Run Ollama pass on unmatched orgs")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    # Orgs with mission text
    total_with_mission = db.execute(
        "SELECT COUNT(*) FROM registry_enriched WHERE mission IS NOT NULL AND mission != ''"
    ).fetchone()[0]
    print(f"Orgs with mission text: {total_with_mission:,}")

    # Dry-run sample
    if args.dry_run:
        rows = db.execute("""
            SELECT EIN, organization_name, mission, cause_tags
            FROM registry_enriched
            WHERE mission IS NOT NULL AND mission != ''
            ORDER BY total_revenue DESC NULLS LAST
            LIMIT 30
        """).fetchall()
        matched = 0
        for r in rows:
            existing = json.loads(r["cause_tags"]) if r["cause_tags"] and r["cause_tags"] not in ("[]", "null") else []
            new_tags = apply_rules(r["mission"])
            merged = merge_tags(existing, new_tags)
            added = [t for t in merged if t not in existing]
            if added:
                matched += 1
            print(f"  {'✓' if added else '·'} {r['organization_name'][:50]:<50} +{added}")
        print(f"\nSample: {matched}/30 got new tags from mission")
        db.close()
        return

    offset = 0
    written = 0
    skipped = 0
    ollama_hits = 0
    start = time.time()

    while True:
        rows = db.execute("""
            SELECT EIN, organization_name, mission, cause_tags
            FROM registry_enriched
            WHERE mission IS NOT NULL AND mission != ''
            LIMIT ? OFFSET ?
        """, (BATCH, offset)).fetchall()
        if not rows:
            break
        if args.limit and written + skipped >= args.limit:
            break

        updates = []
        for r in rows:
            if args.limit and written + skipped + len(updates) >= args.limit:
                break

            existing = json.loads(r["cause_tags"]) if r["cause_tags"] and r["cause_tags"] not in ("[]", "null") else []
            new_tags = apply_rules(r["mission"])

            if not new_tags and args.ollama:
                new_tags = ollama_tag(r["organization_name"] or "", r["mission"]) or []
                if new_tags:
                    ollama_hits += 1

            merged = merge_tags(existing, new_tags)
            added = [t for t in merged if t not in existing]

            if added:
                updates.append((json.dumps(merged), r["EIN"]))
            else:
                skipped += 1

        if updates:
            db.executemany(
                "UPDATE registry_enriched SET cause_tags = ? WHERE EIN = ?",
                updates
            )
            db.commit()
            written += len(updates)

        offset += BATCH
        elapsed = time.time() - start
        print(f"  {written:>7,} enriched | {skipped:>7,} unchanged | {offset:>8,} processed | {elapsed:.0f}s", end="\r")

    print(f"\n\nDone in {time.time() - start:.1f}s")
    print(f"  Enriched:  {written:,}")
    print(f"  Unchanged: {skipped:,}")
    if args.ollama:
        print(f"  Ollama:    {ollama_hits:,}")
    db.close()


if __name__ == "__main__":
    main()
