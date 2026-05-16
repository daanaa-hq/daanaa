import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path.home() / "meritgiving" / "data" / "meritgiving.db"
conn = sqlite3.connect(str(DB_PATH))

print("=" * 70)
print("NTEE SECTOR BENCHMARKING")
print("=" * 70)

df = pd.read_sql("SELECT r.EIN, r.NTEE1, r.REVENUE_AMT, s.merit_score FROM registry_enriched r JOIN scores s ON r.EIN = s.EIN WHERE r.NTEE1 IS NOT NULL AND r.NTEE1 != ''", conn)
df["ntee_major"] = df["NTEE1"].astype(str).str[:1]

ntee_defs = {
    "A": "Arts, Culture", "B": "Education", "C": "Environment",
    "D": "Animal-Related", "E": "Health", "F": "Mental Health",
    "G": "Voluntary Health", "H": "Medical Research", "I": "Crime, Legal",
    "J": "Employment", "K": "Food, Agriculture", "L": "Housing, Shelter",
    "M": "Public Safety", "N": "Recreation, Sports", "O": "Youth Development",
    "P": "Human Services", "Q": "International", "R": "Civil Rights",
    "S": "Community Improvement", "T": "Philanthropy", "U": "Science, Technology",
    "V": "Social Science", "W": "Public Benefit", "X": "Religion, Spiritual",
    "Y": "Mutual, Membership", "Z": "Unknown",
}

print("\nSector Score Variance Analysis:")
print("-" * 70)
print("Sector Name                             Count   Mean    Std     CV      Med Rev")
print("-" * 70)

results = []
for major in sorted(df["ntee_major"].unique()):
    subset = df[df["ntee_major"] == major]
    if len(subset) < 50:
        continue
    mean_score = subset["merit_score"].mean()
    std_score = subset["merit_score"].std()
    cv = std_score / mean_score if mean_score > 0 else 0
    median_rev = subset["REVENUE_AMT"].median()
    name = ntee_defs.get(major, "Unknown")
    flag = " <<< HIGH VARIANCE" if cv > 0.5 else ""
    print(major + " " + name[:38].ljust(40) + str(len(subset)).rjust(6) + " " + str(round(mean_score,1)).rjust(7) + " " + str(round(std_score,1)).rjust(7) + " " + str(round(cv,3)).rjust(7) + " $" + str(round(median_rev,0)).rjust(10) + flag)
    results.append({"sector": major, "name": name, "count": len(subset), "mean_score": mean_score, "std_score": std_score, "cv": cv, "median_revenue": median_rev})

results_df = pd.DataFrame(results).sort_values("mean_score", ascending=False)

print("\n" + "=" * 70)
print("RISK FLAGS:")
print("=" * 70)

high_cv = results_df[results_df["cv"] > 0.5]
if len(high_cv) > 0:
    print("\nHIGH VARIANCE SECTORS (CV > 0.5):")
    for _, row in high_cv.iterrows():
        print("  " + row["sector"] + " (" + row["name"] + "): CV=" + str(round(row["cv"],3)))
else:
    print("\nNo high-variance sectors (all CV < 0.5)")

highest = results_df.iloc[0]
lowest = results_df.iloc[-1]
gap = highest["mean_score"] - lowest["mean_score"]
print("\nSYSTEMATIC BIAS CHECK:")
print("  Highest: " + highest["sector"] + " (" + highest["name"] + ") = " + str(round(highest["mean_score"],1)))
print("  Lowest:  " + lowest["sector"] + " (" + lowest["name"] + ") = " + str(round(lowest["mean_score"],1)))
print("  Gap:     " + str(round(gap,1)) + " points")
if gap > 15:
    print("  WARNING: " + str(round(gap,1)) + "-point gap suggests systematic bias. Consider sector normalization.")
else:
    print("  OK: Gap is manageable")

conn.close()
print("\nDone.")
