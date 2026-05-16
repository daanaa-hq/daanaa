import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path.home() / "meritgiving" / "data" / "meritgiving.db"
conn = sqlite3.connect(str(DB_PATH))

print("=" * 70)
print("PERCENTILE REFRAME")
print("=" * 70)
print("Convert raw scores to peer-relative percentiles")
print()

df = pd.read_sql("SELECT r.EIN, r.NTEE1, s.revenue_band, s.merit_score FROM registry_enriched r JOIN scores s ON r.EIN = s.EIN", conn)
df["ntee_major"] = df["NTEE1"].astype(str).str[:1]

# Compute percentile within each NTEE + revenue band
df["peer_percentile"] = df.groupby(["ntee_major", "revenue_band"])["merit_score"].rank(pct=True) * 100
df["peer_percentile"] = df["peer_percentile"].round(0).astype(int)

# Also compute national percentile
df["national_percentile"] = df["merit_score"].rank(pct=True) * 100
df["national_percentile"] = df["national_percentile"].round(0).astype(int)

# Tier badges
def tier(pct):
    if pct >= 90: return "Flagship"
    elif pct >= 75: return "High-Impact"
    elif pct >= 50: return "Established"
    elif pct >= 25: return "Emerging"
    else: return "Developing"

df["tier"] = df["peer_percentile"].apply(tier)

# Save to database
c = conn.cursor()
c.execute("DROP TABLE IF EXISTS percentiles")
c.execute("CREATE TABLE percentiles (EIN TEXT PRIMARY KEY, peer_percentile INTEGER, national_percentile INTEGER, tier TEXT)")
rows = df[["EIN", "peer_percentile", "national_percentile", "tier"]].values.tolist()
c.executemany("INSERT INTO percentiles VALUES (?,?,?,?)", rows)
conn.commit()

print("Percentiles computed for " + str(len(df)) + " orgs")
print("\nSample output:")
print("  EIN              | NTEE | Band   | Raw | Peer %ile | National %ile | Tier")
print("  " + "-" * 75)
sample = df.sample(15)[["EIN", "ntee_major", "revenue_band", "merit_score", "peer_percentile", "national_percentile", "tier"]]
for _, row in sample.iterrows():
    print("  " + row["EIN"] + " | " + row["ntee_major"] + "    | " + row["revenue_band"].ljust(6) + " | " + str(row["merit_score"]).ljust(5) + " | " + str(int(row["peer_percentile"])).rjust(3) + "th      | " + str(int(row["national_percentile"])).rjust(3) + "th        | " + row["tier"])

print("\nTier distribution:")
tier_counts = df["tier"].value_counts()
for tier_name, count in tier_counts.items():
    pct = round(count / len(df) * 100, 1)
    print("  " + tier_name + ": " + str(count) + " orgs (" + str(pct) + "%)")

# Show the bias fix
print("\n" + "=" * 70)
print("BIAS FIX DEMONSTRATION")
print("=" * 70)
print("\nBefore (raw scores): Health median = 59.1, Arts median = 47.5")
print("After (peer percentiles): Both can be 'top 20%' within their sector")
print("\nExample — same raw score, different context:")
example = df[df["merit_score"].between(45, 50)].sample(5)[["NAME", "ntee_major", "merit_score", "peer_percentile", "tier"]]
for _, row in example.iterrows():
    print("  " + row["NAME"][:40] + " (" + row["ntee_major"] + ") | raw=" + str(row["merit_score"]) + " | peer=" + str(int(row["peer_percentile"])) + "th | " + row["tier"])

conn.close()
print("\nDone. Table 'percentiles' created.")
