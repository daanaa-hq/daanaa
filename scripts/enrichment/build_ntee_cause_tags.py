#!/usr/bin/env python3
"""
build_ntee_cause_tags.py
Populates cause_tags for orgs that have none, using NTEE code as the source.
Deterministic — no LLM, no API calls. Runs entirely on the server.

Only writes to rows where cause_tags IS NULL or empty.
Existing LLM-generated tags are left untouched.

Usage:
    python3 scripts/build_ntee_cause_tags.py            # live run
    python3 scripts/build_ntee_cause_tags.py --dry-run  # count only, no writes
    python3 scripts/build_ntee_cause_tags.py --batch 50000
"""

import sqlite3, json, argparse, sys, time, os

DB_PATH = os.path.expanduser("~/meritgiving/data/merit_registry.db")
BATCH_SIZE = 10_000

# ── NTEE1 broad tags (always applied) ─────────────────────────────────────
NTEE1_TAGS: dict[str, list[str]] = {
    "A": ["arts", "culture", "humanities"],
    "B": ["education"],
    "C": ["environment", "conservation"],
    "D": ["animals", "wildlife"],
    "E": ["health", "healthcare"],
    "F": ["mental health", "crisis support"],
    "G": ["health advocacy", "disease awareness"],
    "H": ["medical research"],
    "I": ["crime prevention", "legal aid", "justice"],
    "J": ["employment", "job training", "workforce"],
    "K": ["food", "nutrition", "hunger relief"],
    "L": ["housing", "shelter", "homelessness"],
    "M": ["public safety", "disaster relief", "emergency services"],
    "N": ["recreation", "sports", "athletics"],
    "O": ["youth development", "children", "youth"],
    "P": ["human services", "social services", "community support"],
    "Q": ["international", "global aid", "development"],
    "R": ["civil rights", "advocacy", "social justice"],
    "S": ["community development", "neighborhood"],
    "T": ["philanthropy", "grantmaking", "voluntarism"],
    "U": ["science", "technology", "research"],
    "V": ["social science", "research"],
    "W": ["civic", "public benefit", "government"],
    "X": ["religion", "faith", "spiritual"],
    "Y": ["mutual aid", "membership"],
    "Z": [],
}

# ── NTEECC subcategory tags (merged in on top of NTEE1 tags) ──────────────
# Key = NTEECC code (uppercase). Value = extra tags to append.
NTEECC_EXTRA: dict[str, list[str]] = {
    # Arts (A)
    "A23": ["cultural awareness", "ethnic heritage"],
    "A25": ["art education"],
    "A27": ["community events", "festivals"],
    "A31": ["film", "video"],
    "A40": ["visual arts"],
    "A41": ["photography"],
    "A44": ["drawing", "painting"],
    "A50": ["museum"],
    "A51": ["art museum"],
    "A52": ["children's museum"],
    "A54": ["history museum"],
    "A57": ["science museum"],
    "A60": ["performing arts"],
    "A62": ["dance"],
    "A63": ["ballet"],
    "A65": ["theater"],
    "A68": ["music"],
    "A69": ["orchestra", "symphony"],
    "A6A": ["opera"],
    "A6B": ["choir", "choral"],
    "A6C": ["music ensemble", "band"],
    "A71": ["history"],
    "A72": ["language", "linguistics"],
    "A73": ["literature"],
    "A74": ["writing"],
    "A80": ["historic preservation"],
    "A82": ["historical society"],
    "A83": ["historic preservation"],

    # Education (B)
    "B20": ["k-12 education", "elementary", "secondary"],
    "B21": ["preschool", "early childhood"],
    "B24": ["elementary school", "primary education"],
    "B25": ["high school", "secondary education"],
    "B29": ["charter school"],
    "B30": ["vocational", "technical education"],
    "B40": ["higher education", "college", "university"],
    "B41": ["community college"],
    "B42": ["college"],
    "B43": ["university"],
    "B60": ["adult education", "continuing education"],
    "B70": ["library"],
    "B82": ["scholarships", "student financial aid"],
    "B83": ["student organizations", "greek life"],
    "B84": ["alumni association"],
    "B92": ["literacy", "reading"],
    "B94": ["parent teacher", "school support"],

    # Environment (C)
    "C20": ["pollution control", "environmental cleanup"],
    "C27": ["recycling"],
    "C30": ["land conservation", "natural resources"],
    "C32": ["wetlands", "water conservation"],
    "C34": ["land preservation"],
    "C36": ["forest conservation"],
    "C41": ["botanical garden", "arboretum"],
    "C42": ["horticulture", "gardening"],
    "C60": ["environmental education", "outdoor education"],

    # Animals (D)
    "D20": ["animal welfare", "animal protection"],
    "D30": ["wildlife preservation"],
    "D31": ["endangered species"],
    "D32": ["bird sanctuary"],
    "D33": ["marine life", "ocean conservation"],
    "D34": ["wildlife refuge", "wildlife sanctuary"],
    "D40": ["veterinary services"],
    "D50": ["zoo"],

    # Health (E)
    "E20": ["primary care", "community health"],
    "E21": ["community health"],
    "E22": ["health clinic"],
    "E40": ["reproductive health"],
    "E41": ["family planning"],
    "E61": ["blood bank"],
    "E62": ["ambulance", "emergency medical"],
    "E65": ["organ donation"],
    "E70": ["public health"],
    "E86": ["patient support"],
    "E91": ["nursing home"],
    "E92": ["home health care"],

    # Mental Health (F)
    "F20": ["substance abuse", "addiction"],
    "F21": ["substance abuse prevention"],
    "F22": ["recovery", "rehabilitation"],
    "F30": ["mental health treatment"],
    "F31": ["psychiatric care"],
    "F32": ["mental health center"],
    "F40": ["crisis hotline", "crisis intervention"],
    "F42": ["rape crisis", "sexual assault"],
    "F43": ["domestic violence shelter", "domestic violence"],
    "F60": ["counseling", "support groups"],

    # Voluntary Health (G)
    "G30": ["cancer"],
    "G41": ["vision", "blindness"],
    "G43": ["heart disease"],
    "G44": ["kidney disease"],
    "G45": ["lung disease"],
    "G48": ["brain disorders", "neurological"],
    "G51": ["arthritis"],
    "G54": ["epilepsy"],
    "G61": ["asthma"],
    "G81": ["HIV/AIDS"],
    "G82": ["alzheimer's"],
    "G83": ["autism"],
    "G84": ["cystic fibrosis"],
    "G85": ["diabetes"],
    "G86": ["learning disabilities"],
    "G87": ["multiple sclerosis"],

    # Medical Research (H)
    "H30": ["cancer research"],
    "H41": ["eye research"],
    "H43": ["heart research"],
    "H45": ["lung research"],
    "H81": ["HIV/AIDS research"],
    "H83": ["autism research"],
    "H85": ["diabetes research"],

    # Crime & Legal (I)
    "I20": ["crime prevention"],
    "I21": ["youth violence prevention"],
    "I30": ["corrections", "prison"],
    "I31": ["halfway house", "reentry"],
    "I40": ["rehabilitation", "reentry"],
    "I50": ["courts", "justice system"],
    "I51": ["mediation", "arbitration"],
    "I60": ["law enforcement"],
    "I71": ["domestic violence"],
    "I72": ["child abuse prevention"],
    "I73": ["sexual abuse prevention"],
    "I80": ["legal services"],
    "I83": ["public interest law"],

    # Employment (J)
    "J20": ["job placement", "career services"],
    "J22": ["job training", "workforce development"],
    "J30": ["vocational rehabilitation"],
    "J32": ["sheltered workshop", "supported employment"],
    "J40": ["labor union"],

    # Food (K)
    "K20": ["agriculture", "farming"],
    "K25": ["farmland preservation"],
    "K30": ["food programs", "food assistance"],
    "K31": ["food bank", "food pantry"],
    "K34": ["congregate meals", "senior meals"],
    "K35": ["meals on wheels"],
    "K36": ["food distribution"],
    "K40": ["nutrition education"],

    # Housing (L)
    "L20": ["affordable housing", "housing development"],
    "L21": ["public housing"],
    "L22": ["temporary housing", "transitional housing"],
    "L25": ["affordable housing"],
    "L30": ["housing assistance"],
    "L33": ["homeownership"],
    "L40": ["homeless shelter"],
    "L41": ["emergency shelter"],
    "L81": ["home repair", "home improvement"],

    # Public Safety (M)
    "M20": ["disaster relief", "emergency preparedness"],
    "M23": ["search and rescue"],
    "M24": ["fire prevention", "fire department"],
    "M40": ["safety education"],
    "M41": ["first aid"],

    # Recreation (N)
    "N20": ["recreational sports"],
    "N30": ["fitness", "wellness"],
    "N50": ["recreational clubs"],
    "N52": ["country club"],
    "N60": ["amateur sports"],
    "N63": ["baseball", "softball"],
    "N64": ["football"],
    "N65": ["soccer"],
    "N66": ["basketball"],
    "N67": ["swimming"],
    "N69": ["winter sports", "skiing"],

    # Youth (O)
    "O20": ["youth centers", "youth clubs"],
    "O21": ["boys and girls club"],
    "O30": ["youth athletics"],
    "O40": ["scouting"],
    "O41": ["boy scouts"],
    "O42": ["girl scouts"],
    "O50": ["youth programs"],
    "O55": ["4-H", "youth agriculture"],

    # Human Services (P)
    "P20": ["social services"],
    "P27": ["YMCA", "YWCA"],
    "P28": ["neighborhood center"],
    "P29": ["thrift shop"],
    "P30": ["children's services"],
    "P31": ["adoption"],
    "P32": ["foster care"],
    "P33": ["child care", "daycare"],
    "P40": ["family services"],
    "P42": ["domestic violence", "family violence shelter"],
    "P43": ["family counseling"],
    "P46": ["parenting education"],
    "P51": ["financial counseling"],
    "P52": ["financial assistance"],
    "P54": ["transportation assistance"],
    "P60": ["emergency assistance", "basic needs"],
    "P62": ["victim services"],
    "P70": ["residential care"],
    "P71": ["adult day care"],
    "P72": ["developmental disabilities"],
    "P73": ["group home"],
    "P75": ["senior living", "assisted living"],
    "P81": ["senior services", "senior center"],
    "P82": ["refugee services", "immigrant services"],
    "P84": ["deaf services", "hearing impaired"],
    "P86": ["disability services"],
    "P87": ["poverty relief", "low income support"],
    "P88": ["veterans", "military families"],

    # International (Q)
    "Q20": ["international exchange"],
    "Q21": ["cultural exchange"],
    "Q22": ["student exchange"],
    "Q30": ["international development"],
    "Q31": ["agricultural development"],
    "Q32": ["economic development"],
    "Q33": ["international relief", "disaster relief"],
    "Q35": ["democracy", "civil society"],
    "Q40": ["international peace"],
    "Q50": ["human rights"],

    # Civil Rights (R)
    "R20": ["civil rights"],
    "R22": ["minority rights"],
    "R23": ["disability rights"],
    "R24": ["women's rights", "gender equity"],
    "R25": ["senior rights"],
    "R26": ["LGBTQ rights"],
    "R30": ["race relations", "diversity"],
    "R40": ["voter registration", "civic engagement"],
    "R61": ["reproductive rights"],
    "R63": ["religious freedom"],

    # Community (S)
    "S20": ["neighborhood development"],
    "S21": ["community coalition"],
    "S22": ["neighborhood association"],
    "S30": ["economic development"],
    "S31": ["urban development"],
    "S32": ["rural development"],
    "S40": ["business development"],
    "S41": ["chamber of commerce", "business association"],
    "S43": ["small business"],
    "S80": ["service club", "community club"],
    "S81": ["women's service club"],
    "S82": ["men's service club"],

    # Philanthropy (T)
    "T20": ["private foundation", "grantmaking"],
    "T21": ["corporate foundation"],
    "T22": ["private foundation"],
    "T23": ["donor advised fund"],
    "T30": ["public foundation"],
    "T31": ["community foundation"],
    "T40": ["voluntarism"],

    # Science (U)
    "U21": ["marine science", "oceanography"],
    "U31": ["astronomy"],
    "U33": ["chemistry"],
    "U34": ["mathematics"],
    "U36": ["geology"],
    "U41": ["computer science"],
    "U42": ["engineering"],
    "U50": ["biology", "life sciences"],

    # Social Science (V)
    "V21": ["anthropology", "sociology"],
    "V22": ["economics"],
    "V23": ["behavioral science"],
    "V24": ["political science"],

    # Public Benefit (W)
    "W30": ["military", "government"],
    "W61": ["credit union"],
    "W70": ["leadership development"],
    "W80": ["public transportation"],
    "W90": ["consumer protection"],

    # Religion (X)
    "X20": ["christian", "christianity"],
    "X21": ["protestant"],
    "X22": ["catholic"],
    "X30": ["jewish", "judaism"],
    "X40": ["islamic", "muslim"],
    "X50": ["buddhist", "buddhism"],
    "X60": ["hindu", "hinduism"],
}


def build_tags(ntee1: str, nteecc: str) -> list[str]:
    """Return a deduplicated list of tags for an org."""
    code1 = (ntee1 or "").strip().upper()[:1]
    code2 = (nteecc or "").strip().upper()[:4]

    tags: list[str] = []
    tags.extend(NTEE1_TAGS.get(code1, []))
    if code2 and code2 != code1:
        tags.extend(NTEECC_EXTRA.get(code2, []))

    # Deduplicate preserving order
    seen: set[str] = set()
    result: list[str] = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            result.append(t)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Count affected rows without writing")
    parser.add_argument("--batch", type=int, default=BATCH_SIZE,
                        help=f"Rows per commit (default {BATCH_SIZE})")
    args = parser.parse_args()

    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    # Count how many need tags
    todo = db.execute("""
        SELECT COUNT(*) FROM registry_enriched
        WHERE cause_tags IS NULL OR cause_tags = ''
    """).fetchone()[0]
    total_all = db.execute("SELECT COUNT(*) FROM registry_enriched").fetchone()[0]

    print(f"Total orgs: {total_all:,}")
    print(f"Need cause_tags: {todo:,}  ({todo/total_all*100:.1f}%)")

    if args.dry_run:
        # Sample preview
        rows = db.execute("""
            SELECT EIN, NTEE1, NTEECC FROM registry_enriched
            WHERE cause_tags IS NULL OR cause_tags = ''
            LIMIT 10
        """).fetchall()
        print("\nSample output (dry run):")
        for r in rows:
            tags = build_tags(r["NTEE1"], r["NTEECC"])
            print(f"  {r['EIN']} | {r['NTEE1']}/{r['NTEECC']} → {tags}")
        print("\nDry run complete — no changes written.")
        db.close()
        return

    print(f"\nProcessing in batches of {args.batch:,}...")
    start = time.time()
    offset = 0  # kept for progress display only
    written = 0
    skipped_empty = 0  # orgs with no NTEE code at all

    while True:
        # Always read from OFFSET 0 — tagged rows drop out of the WHERE clause
        # so the next batch automatically advances to the next untagged rows.
        rows = db.execute("""
            SELECT EIN, NTEE1, NTEECC FROM registry_enriched
            WHERE cause_tags IS NULL OR cause_tags = ''
            LIMIT ?
        """, (args.batch,)).fetchall()

        if not rows:
            break

        updates = []
        for r in rows:
            tags = build_tags(r["NTEE1"], r["NTEECC"])
            if tags:
                updates.append((json.dumps(tags), r["EIN"]))
            else:
                skipped_empty += 1

        if updates:
            db.executemany(
                "UPDATE registry_enriched SET cause_tags = ? WHERE EIN = ?",
                updates,
            )
            db.commit()
            written += len(updates)
        elif not updates:
            # All rows in this batch have no NTEE — advance past them by tagging
            # with a sentinel so they don't loop forever, then let Ollama clean up.
            db.executemany(
                "UPDATE registry_enriched SET cause_tags = ? WHERE EIN = ?",
                [("[]", r["EIN"]) for r in rows],
            )
            db.commit()

        offset += args.batch
        elapsed = time.time() - start
        rate = written / elapsed if elapsed > 0 else 0
        remaining = max(todo - written - skipped_empty, 0) / rate if rate > 0 else 0
        print(
            f"  {written:>9,} written | {skipped_empty:>9,} no-NTEE | "
            f"{rate:,.0f}/s | ~{remaining/60:.1f} min remaining",
            end="\r",
        )

    elapsed = time.time() - start
    print(f"\n\nDone in {elapsed:.1f}s")
    print(f"  Written:              {written:,}")
    print(f"  Skipped (no NTEE):    {skipped_empty:,}")
    db.close()


if __name__ == "__main__":
    main()
