import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
import numpy as np

DB_PATH = Path.home() / "meritgiving" / "data" / "meritgiving.db"

print("=" * 70)
print("MeritGiving Deep Data Quality Analysis v2.0")
print("=" * 70)

conn = sqlite3.connect(str(DB_PATH))
reg = pd.read_sql("SELECT * FROM registry_enriched", conn)
scores = pd.read_sql("SELECT * FROM scores", conn)
df = reg.merge(scores, on="EIN", how="left")

print("\n[OVERVIEW]")
print("  Total orgs:      " + str(len(df)))
print("  Revenue range:   $" + str(round(df["REVENUE_AMT"].min(), 0)) + " - $" + str(round(df["REVENUE_AMT"].max(), 0)))
print("  Median revenue:  $" + str(round(df["REVENUE_AMT"].median(), 0)))
print("  Score range:     " + str(df["merit_score"].min()) + " - " + str(df["merit_score"].max()))
print("  Score std dev:   " + str(round(df["merit_score"].std(), 2)))
print("  Unique scores:   " + str(df["merit_score"].nunique()))

print("\n" + "=" * 70)
print("[SCORE DISTRIBUTION - CHECKING FOR SKEWS]")
print("=" * 70)

print("\nScore percentiles:")
for p in [1, 5, 10, 25, 50, 75, 90, 95, 99]:
    val = df["merit_score"].quantile(p/100)
    print("  P" + str(p) + ": " + str(round(val, 1)))

score_counts = df["merit_score"].value_counts().head(10)
print("\nMost common scores:")
for score, count in score_counts.items():
    pct = round(count / len(df) * 100, 2)
    print("  Score " + str(score) + ": " + str(count) + " orgs (" + str(pct) + "%)")

print("\n" + "=" * 70)
print("[REVENUE vs SCORE CORRELATION]")
print("=" * 70)

corr = df["REVENUE_AMT"].corr(df["merit_score"])
print("\nPearson correlation (revenue vs score): " + str(round(corr, 3)))
if corr > 0.8:
    print("  WARNING: Strong positive correlation - score is mostly revenue-driven")
elif corr > 0.5:
    print("  WARNING: Moderate correlation - revenue dominates scoring")
else:
    print("  OK: Weak correlation - score considers other factors")

print("\nScore by revenue band:")
for band in ["small", "medium", "large", "major", "mega"]:
    subset = df[df["revenue_band"] == band]
    if len(subset) > 0:
        print("  " + band + ": " + str(len(subset)) + " orgs | score " + str(round(subset["merit_score"].min(), 1)) + "-" + str(round(subset["merit_score"].max(), 1)) + " | median " + str(round(subset["merit_score"].median(), 1)))

print("\n" + "=" * 70)
print("[NTEE DEEP DIVE]")
print("=" * 70)

print("\nNTEE major groups:")
df["ntee_major"] = df["NTEE1"].astype(str).str[:1]
ntee_major = df["ntee_major"].value_counts().sort_index()
for major, count in ntee_major.items():
    pct = round(count / len(df) * 100, 1)
    subset = df[df["ntee_major"] == major]
    median_rev = round(subset["REVENUE_AMT"].median(), 0)
    median_score = round(subset["merit_score"].median(), 1)
    print("  " + major + ": " + str(count) + " orgs (" + str(pct) + "%) | median rev $" + str(median_rev) + " | median score " + str(median_score))

bad_ntee = df[df["NTEE1"].isin(["UNDEFINED", "INVALID", "nan", "None"])]
print("\nRemaining bad NTEE: " + str(len(bad_ntee)) + " orgs")

print("\n" + "=" * 70)
print("[STATE DEEP DIVE]")
print("=" * 70)

state_stats = []
for state in df["STATE"].dropna().unique():
    subset = df[df["STATE"] == state]
    state_stats.append({
        "state": state,
        "count": len(subset),
        "median_rev": subset["REVENUE_AMT"].median(),
        "median_score": subset["merit_score"].median(),
        "score_std": subset["merit_score"].std(),
    })

state_df = pd.DataFrame(state_stats).sort_values("count", ascending=False)
print("\nTop 15 states (with score spread):")
for _, row in state_df.head(15).iterrows():
    print("  " + row["state"] + ": " + str(row["count"]) + " orgs | median rev $" + str(round(row["median_rev"], 0)) + " | median score " + str(round(row["median_score"], 1)) + " | std " + str(round(row["score_std"], 1)))

low_variation = state_df[state_df["score_std"] < 3]
if len(low_variation) > 0:
    print("\nWARNING: States with low score variation (std < 3):")
    for _, row in low_variation.iterrows():
        print("  " + row["state"] + ": std=" + str(round(row["score_std"], 2)))

print("\n" + "=" * 70)
print("[TOP/BOTTOM ORGS SANITY CHECK]")
print("=" * 70)

print("\nTop 10 by score:")
top = df.nlargest(10, "merit_score")[["NAME", "STATE", "NTEE1", "REVENUE_AMT", "merit_score"]]
for _, row in top.iterrows():
    print("  " + str(row["NAME"])[:45] + " | " + row["STATE"] + " | " + str(row["NTEE1"]) + " | $" + str(round(row["REVENUE_AMT"], 0)) + " | " + str(row["merit_score"]))

print("\nBottom 10 by score:")
bottom = df.nsmallest(10, "merit_score")[["NAME", "STATE", "NTEE1", "REVENUE_AMT", "merit_score"]]
for _, row in bottom.iterrows():
    print("  " + str(row["NAME"])[:45] + " | " + row["STATE"] + " | " + str(row["NTEE1"]) + " | $" + str(round(row["REVENUE_AMT"], 0)) + " | " + str(row["merit_score"]))

print("\n" + "=" * 70)
print("[REVENUE ANOMALIES]")
print("=" * 70)

zero_rev = len(df[df["REVENUE_AMT"] == 0])
negative_rev = len(df[df["REVENUE_AMT"] < 0])
very_low = len(df[df["REVENUE_AMT"] < 50000])
very_high = len(df[df["REVENUE_AMT"] > 100000000])

print("\n  Zero revenue:     " + str(zero_rev) + " orgs")
print("  Negative revenue: " + str(negative_rev) + " orgs")
print("  Below $50K:       " + str(very_low) + " orgs")
print("  Above $100M:      " + str(very_high) + " orgs")

print("\n" + "=" * 70)
print("[FINAL VERDICT]")
print("=" * 70)

issues = []
if corr > 0.7:
    issues.append("HIGH: Score is heavily revenue-correlated (" + str(round(corr, 2)) + ")")
if df["merit_score"].std() < 10:
    issues.append("HIGH: Score variation too low (std=" + str(round(df["merit_score"].std(), 2)) + ")")
if len(bad_ntee) > 0:
    issues.append("MED: " + str(len(bad_ntee)) + " orgs still have bad NTEE codes")
if zero_rev > 0:
    issues.append("MED: " + str(zero_rev) + " orgs have zero revenue")
if very_low > 0 or very_high > 0:
    issues.append("MED: Revenue filter leaks detected")

if not issues:
    print("  PASS: Data looks clean and ready for public serving.")
else:
    for issue in issues:
        print("  " + issue)

conn.close()
print("\nAnalysis complete.")
