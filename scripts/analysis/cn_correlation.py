#!/usr/bin/env python3
"""
External Benchmark Correlation
-------------------------------
Compares MERIT scores against two free public benchmarks:

  Tier A (built-in, zero deps):
    - GiveWell Top Charities  — ~20 orgs, highest-confidence effectiveness ratings
    - Forbes Best Charities   — ~100 US orgs, broad recognisable benchmark

  Tier B (optional, needs env vars):
    - Charity Navigator API   — set CN_APP_ID + CN_APP_KEY for ~10K org comparison

Output: data/benchmark_report.csv + printed correlation summary

Usage:
  python3 scripts/analysis/cn_correlation.py
  python3 scripts/analysis/cn_correlation.py --cn    # also fetch CN ratings
  python3 scripts/analysis/cn_correlation.py --verbose
"""

import os, sys, csv, json, argparse, sqlite3
from pathlib import Path

try:
    from scipy.stats import spearmanr
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

BASE   = Path(__file__).parents[2]
DB     = BASE / "data" / "merit_registry.db"
CN_CACHE = BASE / "data" / "cn_ratings.json"
OUT_CSV  = BASE / "data" / "benchmark_report.csv"

# ── GiveWell Top Charities (US entities only — international arms that file with IRS)
# Source: givewell.org/charities/top-charities  (verified EINs from IRS BMF)
GIVEWELL = [
    ("203069450", "Against Malaria Foundation"),
    ("272661601", "GiveDirectly"),
    ("201241274", "Evidence Action"),
    ("134300560", "Helen Keller International"),
    ("300028099", "Innovations for Poverty Action"),
    ("261335563", "Malaria Consortium USA"),
    ("364476738", "New Incentives"),
    ("208413336", "Sightsavers America"),
]

# ── Forbes Best Charities (US, from Forbes annual list — EINs from IRS BMF)
FORBES = [
    ("952097793",  "Direct Relief"),
    ("363673599",  "Feeding America"),
    ("061008595",  "AmeriCares Foundation"),
    ("581623160",  "MAP International"),
    ("581711937",  "Task Force for Global Health"),
    ("256019785",  "Matthew 25: Ministries"),
    ("251302214",  "Brother's Brother Foundation"),
    ("237243215",  "Project CURE"),
    ("133445590",  "Doctors Without Borders USA"),
    ("521689908",  "International Rescue Committee"),
    ("131685039",  "Save the Children Federation"),
    ("237029110",  "Habitat for Humanity International"),
    ("530196605",  "American Red Cross"),
    ("363765823",  "World Vision"),
    ("131635294",  "CARE USA"),
    ("237382161",  "Catholic Relief Services"),
    ("310526972",  "United Way Worldwide"),
    ("521571495",  "Nature Conservancy"),
    ("941305847",  "Sierra Club Foundation"),
    ("133078648",  "Wildlife Conservation Society"),
    ("311812875",  "Wounded Warrior Project"),
    ("593138728",  "St. Jude Children's Research Hospital"),
    ("591036358",  "Children's Miracle Network Hospitals"),
    ("043374567",  "Dana-Farber Cancer Institute"),
    ("042774441",  "Massachusetts General Hospital"),
    ("362167817",  "March of Dimes"),
    ("131624164",  "American Heart Association"),
    ("237303161",  "American Cancer Society"),
    ("131577890",  "American Lung Association"),
    ("530242652",  "National Multiple Sclerosis Society"),
    ("042613474",  "Alzheimer's Association"),
    ("237400892",  "Susan G. Komen"),
    ("133838138",  "Arthritis Foundation"),
    ("952217229",  "City of Hope"),
    ("591337005",  "Shriners Hospitals for Children"),
    ("042103594",  "Brigham and Women's Hospital"),
    ("041564045",  "Children's Hospital Boston"),
    ("953283752",  "Ronald McDonald House Charities"),
    ("590637918",  "Volunteers of America"),
    ("530196688",  "Boys & Girls Clubs of America"),
    ("221457124",  "Big Brothers Big Sisters of America"),
    ("131644147",  "Girl Scouts of the USA"),
    ("221576300",  "Boy Scouts of America"),
    ("131788491",  "YMCA of the USA"),
    ("741109620",  "Goodwill Industries International"),
    ("131788491",  "YMCA"),
    ("042217495",  "Oxfam America"),
    ("131659642",  "PATH"),
    ("200029040",  "Room to Read"),
    ("133441079",  "Population Services International"),
]

# De-duplicate by EIN
FORBES = list({ein: name for ein, name in FORBES}.items())


def load_merit_scores(eins: list[str]) -> dict[str, dict]:
    """Return {ein: {merit_score, merit_tier, org_name, ntee1, total_revenue}} for matching EINs."""
    db = sqlite3.connect(DB)
    placeholders = ",".join("?" * len(eins))
    rows = db.execute(f"""
        SELECT EIN, organization_name, merit_score, merit_tier,
               ntee1_percentile, program_expense_pct, months_of_reserve,
               total_revenue, NTEE1
        FROM registry_enriched
        WHERE EIN IN ({placeholders})
    """, eins).fetchall()
    db.close()
    return {
        r[0]: {
            "org_name": r[1], "merit_score": r[2], "merit_tier": r[3],
            "ntee1_pct": r[4], "program_pct": r[5], "months_reserve": r[6],
            "total_revenue": r[7], "ntee1": r[8],
        }
        for r in rows
    }


def fetch_cn_ratings(eins: list[str]) -> dict[str, float]:
    """Fetch Charity Navigator overall scores for given EINs. Caches in data/cn_ratings.json."""
    import urllib.request, time

    app_id  = os.environ.get("CN_APP_ID", "")
    app_key = os.environ.get("CN_APP_KEY", "")
    if not app_id or not app_key:
        print("  CN_APP_ID / CN_APP_KEY not set — skipping CN tier")
        return {}

    cache: dict[str, float] = {}
    if CN_CACHE.exists():
        try:
            cache = json.loads(CN_CACHE.read_text())
        except Exception:
            pass

    results: dict[str, float] = {}
    to_fetch = [e for e in eins if e not in cache]
    print(f"  Fetching {len(to_fetch)} orgs from CN API ({len(cache)} cached)…")

    for ein in to_fetch:
        url = f"https://api.charitynavigator.org/v2/Organizations/{ein}?app_id={app_id}&app_key={app_key}"
        try:
            with urllib.request.urlopen(url, timeout=8) as resp:
                data = json.loads(resp.read())
                score = data.get("currentRating", {}).get("score")
                cache[ein] = float(score) if score is not None else -1
        except Exception:
            cache[ein] = -1
        time.sleep(0.25)

    CN_CACHE.write_text(json.dumps(cache, indent=2))

    for ein in eins:
        v = cache.get(ein, -1)
        if v >= 0:
            results[ein] = v
    return results


TIER_RANK = {"Beacon": 5, "Lantern": 4, "Flame": 3, "Ember": 2, "Spark": 1, None: 0}


def run(use_cn: bool = False, verbose: bool = False):
    print("\n" + "=" * 68)
    print("  MERIT EXTERNAL BENCHMARK CORRELATION")
    print("=" * 68)

    all_eins = list({ein for ein, _ in GIVEWELL + FORBES})
    merit = load_merit_scores(all_eins)

    rows = []

    # ── GiveWell analysis ────────────────────────────────────────────────
    print(f"\n── GiveWell Top Charities ({len(GIVEWELL)} orgs) ──")
    gw_found = gw_top2 = 0
    for ein, label in GIVEWELL:
        m = merit.get(ein)
        if m and m["merit_score"] is not None:
            gw_found += 1
            tier = m["merit_tier"]
            if tier in ("Beacon", "Lantern"):
                gw_top2 += 1
            flag = "" if tier in ("Beacon", "Lantern", "Flame") else "⚠ LOW"
            print(f"  {label:<45} {m['merit_score']:>5.0f}  {tier or '—':<8} {flag}")
            rows.append({"EIN": ein, "org_name": m["org_name"] or label,
                         "merit_score": m["merit_score"], "merit_tier": tier,
                         "external_score": None, "source": "GiveWell", "delta": None,
                         "flag": flag.strip()})
        else:
            print(f"  {label:<45}   —    not in MERIT DB")
            rows.append({"EIN": ein, "org_name": label, "merit_score": None,
                         "merit_tier": None, "external_score": None,
                         "source": "GiveWell", "delta": None, "flag": "NOT_IN_DB"})

    if gw_found:
        print(f"\n  Coverage: {gw_found}/{len(GIVEWELL)} orgs in MERIT DB")
        print(f"  In top 2 tiers (Beacon/Lantern): {gw_top2}/{gw_found} ({gw_top2/gw_found*100:.0f}%)")

    # ── Forbes analysis ──────────────────────────────────────────────────
    print(f"\n── Forbes Best Charities ({len(FORBES)} orgs) ──")
    fb_found = fb_top3 = 0
    for ein, label in FORBES:
        m = merit.get(ein)
        if m and m["merit_score"] is not None:
            fb_found += 1
            tier = m["merit_tier"]
            if tier in ("Beacon", "Lantern", "Flame"):
                fb_top3 += 1
            flag = "" if tier in ("Beacon", "Lantern", "Flame") else "⚠ LOW"
            if verbose or flag:
                print(f"  {label:<45} {m['merit_score']:>5.0f}  {tier or '—':<8} {flag}")
            rows.append({"EIN": ein, "org_name": m["org_name"] or label,
                         "merit_score": m["merit_score"], "merit_tier": tier,
                         "external_score": None, "source": "Forbes",
                         "delta": None, "flag": flag.strip()})

    if fb_found:
        print(f"\n  Coverage: {fb_found}/{len(FORBES)} orgs in MERIT DB")
        print(f"  In top 3 tiers (Beacon/Lantern/Flame): {fb_top3}/{fb_found} ({fb_top3/fb_found*100:.0f}%)")
    else:
        print("  None found in MERIT DB yet (need 990 data for these large orgs)")

    # ── Optional CN tier ─────────────────────────────────────────────────
    if use_cn:
        print("\n── Charity Navigator API ──")
        cn_eins = [r["EIN"] for r in rows if r["merit_score"] is not None]
        cn_scores = fetch_cn_ratings(cn_eins)
        if cn_scores and HAS_SCIPY:
            pairs = [(merit[e]["merit_score"], cn_scores[e]) for e in cn_scores if e in merit]
            if len(pairs) >= 5:
                merit_vals, cn_vals = zip(*pairs)
                rho, pval = spearmanr(merit_vals, cn_vals)
                print(f"\n  Spearman ρ = {rho:.3f}  (p = {pval:.4f}, n = {len(pairs)})")
                if rho > 0.5:
                    print("  ✅ Strong positive correlation — MERIT and CN agree")
                elif rho > 0.25:
                    print("  🟡 Moderate correlation — broadly aligned with differences")
                else:
                    print("  ⚠  Weak correlation — investigate divergences")
        for r in rows:
            if r["EIN"] in cn_scores:
                cn = cn_scores[r["EIN"]]
                r["external_score"] = cn
                r["delta"] = round(r["merit_score"] - cn, 1) if r["merit_score"] else None

    # ── Write CSV ────────────────────────────────────────────────────────
    fields = ["EIN", "org_name", "merit_score", "merit_tier",
              "external_score", "source", "delta", "flag"]
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"\n  Report written → {OUT_CSV}")
    print("=" * 68 + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cn",      action="store_true", help="Also fetch Charity Navigator ratings")
    ap.add_argument("--verbose", action="store_true", help="Print all orgs, not just flagged ones")
    args = ap.parse_args()
    run(use_cn=args.cn, verbose=args.verbose)
