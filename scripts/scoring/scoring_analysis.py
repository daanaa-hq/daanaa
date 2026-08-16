#!/usr/bin/env python3
"""
MERIT Scoring Deep Analysis
Profiles data completeness, identifies correlations, proposes scoring improvements.
"""

import csv, math, json
from collections import Counter, defaultdict
from pathlib import Path
import statistics

BASE = Path.home() / "meritgiving"
MASTER = BASE / "data" / "csv" / "master_orgs.csv"

def safe_float(v):
    if v is None: return None
    try:
        f = float(v)
        if math.isnan(f) or math.isinf(f): return None
        return f
    except: return None

def safe_int(v):
    f = safe_float(v)
    return int(f) if f is not None else None

# Load data
orgs = []
with open(MASTER, "r", encoding="utf-8", errors="ignore") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    for row in reader:
        orgs.append(row)

print("=" * 60)
print("MERIT SCORING DEEP ANALYSIS")
print("=" * 60)
print("Total orgs loaded: " + str(len(orgs)))

# ============================================================
# 1. DATA COMPLETENESS PROFILE
# ============================================================
print("\n" + "=" * 60)
print("1. DATA COMPLETENESS BY FIELD")
print("=" * 60)

completeness = {}
for field in ["REVENUE", "TOTAL_EXPENSES", "PROGRAM_EXPENSES", "ADMIN_EXPENSES",
              "FUNDRAISING", "NET_ASSETS", "TOTAL_ASSETS", "EMPLOYEES", 
              "VOLUNTEERS", "CITY", "NTEE", "MISSION", "LEADERSHIP", "PERCENTILE"]:
    filled = 0
    zero_or_empty = 0
    for org in orgs:
        val = str(org.get(field, "")).strip()
        if val and val.lower() not in ("", "nan", "none", "null", "-", "0", "0.0"):
            filled += 1
        else:
            zero_or_empty += 1
    pct = round(filled / len(orgs) * 100, 1)
    completeness[field] = {"filled": filled, "pct": pct}
    print(field + ": " + str(filled) + "/" + str(len(orgs)) + " (" + str(pct) + "%)")

# ============================================================
# 2. FINANCIAL DISTRIBUTIONS
# ============================================================
print("\n" + "=" * 60)
print("2. FINANCIAL METRIC DISTRIBUTIONS (non-zero values only)")
print("=" * 60)

metrics = {
    "REVENUE": [],
    "TOTAL_EXPENSES": [],
    "PROGRAM_EXPENSES": [],
    "NET_ASSETS": [],
    "TOTAL_ASSETS": [],
    "EMPLOYEES": [],
}

for org in orgs:
    for field in metrics:
        v = safe_float(org.get(field))
        if v and v > 0:
            metrics[field].append(v)

for field, vals in metrics.items():
    if vals:
        vals.sort()
        n = len(vals)
        print("\n" + field + ":")
        print("  Count:    " + str(n))
        print("  Min:      $" + f"{vals[0]:,.0f}")
        print("  Median:   $" + f"{statistics.median(vals):,.0f}")
        print("  Mean:     $" + f"{statistics.mean(vals):,.0f}")
        print("  Max:      $" + f"{vals[-1]:,.0f}")
        print("  P90:      $" + f"{vals[int(n*0.9)]:,.0f}")
        print("  P10:      $" + f"{vals[int(n*0.1)]:,.0f}")

# ============================================================
# 3. CURRENT SCORING ISSUES
# ============================================================
print("\n" + "=" * 60)
print("3. CURRENT SCORING ISSUES")
print("=" * 60)

# Issue 1: Financial Health = 0 because missing net_assets + expenses
fh_zero = 0
fh_reasons = Counter()
for org in orgs:
    expenses = safe_float(org.get("TOTAL_EXPENSES"))
    net_assets = safe_float(org.get("NET_ASSETS"))
    if not expenses or expenses <= 0:
        fh_zero += 1
        fh_reasons["missing_total_expenses"] += 1
    elif not net_assets or net_assets <= 0:
        fh_zero += 1
        fh_reasons["missing_net_assets"] += 1

print("\nFinancial Health = 0 for " + str(fh_zero) + " orgs (" + str(round(fh_zero/len(orgs)*100,1)) + "%)")
for reason, count in fh_reasons.most_common():
    print("  " + reason + ": " + str(count))

# Issue 2: Operational Efficiency = 0 because missing program_expenses
oe_zero = 0
for org in orgs:
    prog = safe_float(org.get("PROGRAM_EXPENSES"))
    if not prog or prog <= 0:
        oe_zero += 1
print("\nOperational Efficiency = 0 for " + str(oe_zero) + " orgs (" + str(round(oe_zero/len(orgs)*100,1)) + "%)")

# Issue 3: Sector Position = 0 because missing percentile
sp_zero = 0
for org in orgs:
    pct = safe_float(org.get("PERCENTILE"))
    if not pct or pct <= 0:
        sp_zero += 1
print("\nSector Position = 0 for " + str(sp_zero) + " orgs (" + str(round(sp_zero/len(orgs)*100,1)) + "%)")

# ============================================================
# 4. CORRELATION ANALYSIS
# ============================================================
print("\n" + "=" * 60)
print("4. CORRELATIONS (Pearson, among orgs with both fields)")
print("=" * 60)

def pearson(x, y):
    n = len(x)
    if n < 10: return None
    mx = statistics.mean(x)
    my = statistics.mean(y)
    num = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    denx = math.sqrt(sum((xi - mx)**2 for xi in x))
    deny = math.sqrt(sum((yi - my)**2 for yi in y))
    if denx == 0 or deny == 0: return None
    return num / (denx * deny)

pairs = [
    ("REVENUE", "TOTAL_EXPENSES"),
    ("REVENUE", "TOTAL_ASSETS"),
    ("TOTAL_EXPENSES", "PROGRAM_EXPENSES"),
    ("NET_ASSETS", "TOTAL_ASSETS"),
    ("REVENUE", "EMPLOYEES"),
]

for f1, f2 in pairs:
    vals1, vals2 = [], []
    for org in orgs:
        v1 = safe_float(org.get(f1))
        v2 = safe_float(org.get(f2))
        if v1 and v1 > 0 and v2 and v2 > 0:
            vals1.append(v1)
            vals2.append(v2)
    r = pearson(vals1, vals2)
    if r is not None:
        print(f1 + " vs " + f2 + ": r=" + str(round(r, 3)) + " (n=" + str(len(vals1)) + ")")

# ============================================================
# 5. SCORING IMPROVEMENT PROPOSALS
# ============================================================
print("\n" + "=" * 60)
print("5. SCORING IMPROVEMENT PROPOSALS (DATA-BACKED)")
print("=" * 60)

proposals = []

# Proposal 1: Use assets/revenue ratio as Financial Health fallback
assets_rev_orgs = []
for org in orgs:
    rev = safe_float(org.get("REVENUE"))
    assets = safe_float(org.get("TOTAL_ASSETS"))
    if rev and rev > 0 and assets and assets > 0:
        assets_rev_orgs.append(assets / rev)

if assets_rev_orgs:
    proposals.append({
        "id": 1,
        "gauge": "Financial Health",
        "problem": str(fh_zero) + " orgs have 0 because missing expenses/assets",
        "solution": "Add fallback: assets/revenue ratio when runway unavailable",
        "data": "assets/revenue ratio available for " + str(len(assets_rev_orgs)) + " orgs",
        "MERIT": "Would reduce Financial Health=0 from " + str(round(fh_zero/len(orgs)*100,1)) + "% to ~" + str(round((fh_zero-len(assets_rev_orgs))/len(orgs)*100,1)) + "%"
    })

# Proposal 2: Use revenue tier for Operational Efficiency fallback
rev_orgs = sum(1 for o in orgs if safe_float(o.get("REVENUE")) and safe_float(o.get("REVENUE")) > 0)
if rev_orgs:
    proposals.append({
        "id": 2,
        "gauge": "Operational Efficiency",
        "problem": str(oe_zero) + " orgs have 0 because missing program_expenses",
        "solution": "Estimate program ratio from revenue tier: small orgs (<$500K) typically 70-85%",
        "data": "Revenue available for " + str(rev_orgs) + " orgs",
        "MERIT": "Would set default 75% for orgs with revenue but no program_expenses"
    })

# Proposal 3: Use revenue percentile for Sector Position when direct percentile missing
rev_pct_orgs = []
for org in orgs:
    rev = safe_float(org.get("REVENUE"))
    if rev and rev > 0:
        rev_pct_orgs.append(rev)

if rev_pct_orgs:
    proposals.append({
        "id": 3,
        "gauge": "Sector Position",
        "problem": str(sp_zero) + " orgs have 0 because missing peer percentile",
        "solution": "Use national revenue percentile within NTEE major as proxy",
        "data": "Revenue available for " + str(len(rev_pct_orgs)) + " orgs",
        "MERIT": "Would reduce Sector Position=0 from " + str(round(sp_zero/len(orgs)*100,1)) + "% to ~" + str(round((sp_zero-len(rev_pct_orgs))/len(orgs)*100,1)) + "%"
    })

# Proposal 4: Add Fundraising Efficiency gauge
fundraising_orgs = []
for org in orgs:
    rev = safe_float(org.get("REVENUE"))
    fund = safe_float(org.get("FUNDRAISING"))
    if rev and rev > 0 and fund and fund > 0:
        fundraising_orgs.append(fund / rev)

if fundraising_orgs:
    proposals.append({
        "id": 4,
        "gauge": "NEW: Fundraising Efficiency",
        "problem": "No measure of how efficiently org raises money",
        "solution": "fundraising_costs / revenue — lower is better",
        "data": "Available for " + str(len(fundraising_orgs)) + " orgs",
        "MERIT": "New 6th gauge, weight 10%, reduces Compliance to 5%"
    })

# Proposal 5: Add Administrative Overhead gauge
admin_orgs = []
for org in orgs:
    admin = safe_float(org.get("ADMIN_EXPENSES"))
    expenses = safe_float(org.get("TOTAL_EXPENSES"))
    if admin and admin > 0 and expenses and expenses > 0:
        admin_orgs.append(admin / expenses)

if admin_orgs:
    proposals.append({
        "id": 5,
        "gauge": "NEW: Administrative Overhead",
        "problem": "No visibility into admin bloat",
        "solution": "admin_expenses / total_expenses — lower is better",
        "data": "Available for " + str(len(admin_orgs)) + " orgs",
        "MERIT": "New 6th gauge, shows donors how much goes to overhead"
    })

for p in proposals:
    print("\nProposal #" + str(p["id"]) + ": " + p["gauge"])
    print("  Problem:  " + p["problem"])
    print("  Solution: " + p["solution"])
    print("  Data:     " + p["data"])
    print("  Impact:   " + p["MERIT"])

# ============================================================
# 6. REVISED WEIGHTS
# ============================================================
print("\n" + "=" * 60)
print("6. REVISED SCORING WEIGHTS (PROPOSED)")
print("=" * 60)

print("""
Current weights:
  Financial Health      25%
  Operational Eff.      25%
  Scale Trajectory      20%
  Sector Position       20%
  Compliance            10%

Proposed weights (v2.1):
  Financial Health      20%  (reduced — many orgs have fallback only)
  Operational Eff.      20%  (reduced — some estimated)
  Scale Trajectory      15%  (reduced — revenue alone is weak signal)
  Sector Position       20%  (kept — peer comparison is core value)
  Compliance            10%  (kept)
  Fundraising Eff.      10%  (NEW — if data available, else 0)
  Admin Overhead         5%  (NEW — if data available, else 0)
""")

# ============================================================
# 7. OUTPUT SUMMARY JSON
# ============================================================
summary = {
    "total_orgs": len(orgs),
    "completeness": completeness,
    "scoring_issues": {
        "financial_health_zero": {"count": fh_zero, "pct": round(fh_zero/len(orgs)*100, 1)},
        "operational_efficiency_zero": {"count": oe_zero, "pct": round(oe_zero/len(orgs)*100, 1)},
        "sector_position_zero": {"count": sp_zero, "pct": round(sp_zero/len(orgs)*100, 1)},
    },
    "proposals": proposals,
    "revised_weights": {
        "financial_health": 0.20,
        "operational_efficiency": 0.20,
        "scale_trajectory": 0.15,
        "sector_position": 0.20,
        "compliance": 0.10,
        "fundraising_efficiency": 0.10,
        "admin_overhead": 0.05,
    }
}

with open(BASE / "data" / "scoring_analysis.json", "w") as f:
    json.dump(summary, f, indent=2)

print("\n" + "=" * 60)
print("Analysis complete. Saved to: data/scoring_analysis.json")
print("=" * 60)
