import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime

DB_PATH = Path.home() / "meritgiving" / "data" / "meritgiving.db"

print("=" * 70)
print("MeritGiving Data Quality Analysis")
print("=" * 70)

conn = sqlite3.connect(str(DB_PATH))
reg = pd.read_sql("SELECT * FROM registry_enriched", conn)
scores = pd.read_sql("SELECT * FROM scores", conn)
df = reg.merge(scores, on="EIN", how="left")

print("\n[OVERVIEW]")
print("  Total orgs: " + str(len(df)))
print("  Revenue range: $" + str(df["REVENUE_AMT"].min()) + " - $" + str(df["REVENUE_AMT"].max()))
print("  Median revenue: $" + str(round(df["REVENUE_AMT"].median(), 0)))
print("  Score range: " + str(df["merit_score"].min()) + " - " + str(df["merit_score"].max()))
print("  Score std dev: " + str(round(df["merit_score"].std(), 2)))

print("\n" + "=" * 70)
print("[NTEE CATEGORY ANALYSIS]")
print("=" * 70)

ntee_counts = df["NTEE1"].value_counts().head(20)
print("\nTop 20 NTEE codes:")
for code, count in ntee_counts.items():
    pct = round(count / len(df) * 100, 1)
    median_rev = round(df[df["NTEE1"] == code]["REVENUE_AMT"].median(), 0)
    median_score = round(df[df["NTEE1"] == code]["merit_score"].median(), 1)
    print("  " + str(code) + ": " + str(count) + " orgs (" + str(pct) + "%) | median rev $" + str(median_rev) + " | median score " + str(median_score))

undefined = len(df[df["NTEE1"] == "UNDEFINED"])
invalid = len(df[df["NTEE1"] == "INVALID"])
missing = len(df[df["NTEE1"].isna()])
print("\nNTEE QUALITY FLAGS:")
print("  UNDEFINED: " + str(undefined) + " orgs (" + str(round(undefined/len(df)*100, 1)) + "%)")
print("  INVALID:   " + str(invalid) + " orgs (" + str(round(invalid/len(df)*100, 1)) + "%)")
print("  NULL:      " + str(missing) + " orgs (" + str(round(missing/len(df)*100, 1)) + "%)")
print("  CLEAN:     " + str(len(df) - undefined - invalid - missing) + " orgs (" + str(round((len(df)-undefined-invalid-missing)/len(df)*100, 1)) + "%)")

print("\n" + "=" * 70)
print("[STATE / LOCATION ANALYSIS]")
print("=" * 70)

state_counts = df["STATE"].value_counts().head(15)
print("\nTop 15 states:")
for state, count in state_counts.items():
    pct = round(count / len(df) * 100, 1)
    median_rev = round(df[df["STATE"] == state]["REVENUE_AMT"].median(), 0)
    median_score = round(df[df["STATE"] == state]["merit_score"].median(), 1)
    print("  " + str(state) + ": " + str(count) + " orgs (" + str(pct) + "%) | median rev $" + str(median_rev) + " | median score " + str(median_score))

null_state = len(df[df["STATE"].isna()])
print("\nLOCATION FLAGS:")
print("  NULL state: " + str(null_state) + " orgs")
print("  NULL city:  " + str(df["CITY"].isna().sum()) + " orgs")
print("  NULL zip:   " + str(df["ZIP"].isna().sum()) + " orgs")

print("\n" + "=" * 70)
print("[REVENUE ANOMALIES]")
print("=" * 70)

zero_rev = len(df[df["REVENUE_AMT"] == 0])
negative_rev = len(df[df["REVENUE_AMT"] < 0])
very_low = len(df[df["REVENUE_AMT"] < 50000])
very_high = len(df[df["REVENUE_AMT"] > 100000000])

print("\nRevenue distribution:")
print("  Zero revenue:     " + str(zero_rev) + " orgs")
print("  Negative revenue: " + str(negative_rev) + " orgs")
print("  Below $50K:       " + str(very_low) + " orgs (filter leak?)")
print("  Above $100M:      " + str(very_high) + " orgs (filter leak?)")

print("\nRevenue bands:")
for band, label in [("small", "50K-100K"), ("medium", "100K-500K"), ("large", "500K-1M"), ("major", "1M-5M"), ("mega", "5M-100M")]:
    cnt = len(df[df["revenue_band"] == band])
    pct = round(cnt / len(df) * 100, 1)
    print("  " + label + ": " + str(cnt) + " orgs (" + str(pct) + "%)")

print("\n" + "=" * 70)
print("[SCORE DISTRIBUTION ANALYSIS]")
print("=" * 70)

print("\nOverall score distribution:")
print("  Min:    " + str(df["merit_score"].min()))
print("  Max:    " + str(df["merit_score"].max()))
print("  Mean:   " + str(round(df["merit_score"].mean(), 2)))
print("  Median: " + str(round(df["merit_score"].median(), 2)))
print("  Std:    " + str(round(df["merit_score"].std(), 2)))

print("\nScore by NTEE major group:")
df["ntee_major"] = df["NTEE1"].astype(str).str[:1]
for major in sorted(df["ntee_major"].unique()):
    subset = df[df["ntee_major"] == major]
    if len(subset) > 100:
        print("  " + major + ": " + str(len(subset)) + " orgs | score " + str(round(subset["merit_score"].min(), 1)) + "-" + str(round(subset["merit_score"].max(), 1)) + " | median " + str(round(subset["merit_score"].median(), 1)))

print("\n" + "=" * 70)
print("[DATA QUALITY SUMMARY]")
print("=" * 70)

issues = []
if undefined > len(df) * 0.1:
    issues.append("HIGH: " + str(undefined) + " orgs have UNDEFINED NTEE (>10%)")
if invalid > len(df) * 0.05:
    issues.append("HIGH: " + str(invalid) + " orgs have INVALID NTEE (>5%)")
if df["merit_score"].std() < 5:
    issues.append("HIGH: Score range too narrow (std=" + str(round(df["merit_score"].std(), 2)) + ") — all orgs look identical")
if zero_rev > 0:
    issues.append("MED: " + str(zero_rev) + " orgs have zero revenue")
if negative_rev > 0:
    issues.append("MED: " + str(negative_rev) + " orgs have negative revenue")
if very_low > 0:
    issues.append("MED: " + str(very_low) + " orgs below $50K (filter leak)")
if very_high > 0:
    issues.append("MED: " + str(very_high) + " orgs above $100M (filter leak)")

if not issues:
    print("  No major issues detected.")
else:
    for issue in issues:
        print("  " + issue)

print("\n" + "=" * 70)
print("RECOMMENDATIONS")
print("=" * 70)
print("  1. NTEE cleanup: " + str(undefined + invalid + missing) + " orgs need proper NTEE classification")
print("  2. Score differentiation: Add CorePCF financials for real program expense ratios")
print("  3. Revenue validation: " + str(zero_rev + negative_rev) + " orgs need revenue review")
print("  4. Location enrichment: " + str(null_state) + " orgs missing state data")
print("  5. Consider filtering out UNDEFINED/INVALID NTEE for public-facing search")

conn.close()
print("\nAnalysis complete.")
