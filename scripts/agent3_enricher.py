#!/usr/bin/env python3
import os, json, pandas as pd

print("[AGENT 3] Loading scored orgs...")
df = pd.read_csv("data/csv/scored_orgs.csv", dtype=str)
df["EIN"] = df["EIN"].astype(str).str.replace(".0", "").str.strip()
print(f"[AGENT 3] Loaded {len(df)} orgs")

BMF_PATH = "data/irs_bmf.csv"
if os.path.exists(BMF_PATH):
    print("[AGENT 3] Loading BMF...")
    bmf = pd.read_csv(BMF_PATH, dtype=str, low_memory=False)
    bmf_ein_col = None
    for c in ["EIN", "ein", "EIN2"]:
n        if c in bmf.columns:
n            bmf_ein_col = c
n            break
    if bmf_ein_col:
n        bmf[bmf_ein_col] = bmf[bmf_ein_col].astype(str).str.replace(".0", "").str.strip()
n        bmf_cols = {}
n        for target, candidates in {
n            "SUBSECTION": ["SUBSECTION", "SUBSECCD"],
            "FOUNDATION": ["FOUNDATION", "FOUNDATIONCD"],
            "RULING_DATE": ["RULING_DT", "RULING_DATE"],
            "DEDUCTIBILITY": ["DEDUCTIBILITY", "DEDUCTCD"],
            "NTEE_CD": ["NTEE_CD", "NTEE"],
            "CITY": ["CITY", "CITY_NAME"],
            "STATE": ["STATE", "STATE_NAME"]
        }.items():
n            for c in candidates:
n                if c in bmf.columns:
                    bmf_cols[target] = c
                    break
        merge_cols = [bmf_ein_col] + list(bmf_cols.values())
        bmf_subset = bmf[merge_cols].rename(columns={v: k for k, v in bmf_cols.items()})
        bmf_subset.rename(columns={bmf_ein_col: "EIN"}, inplace=True)
        df = df.merge(bmf_subset, on="EIN", how="left", suffixes=("", "_bmf"))
        
        foundation_map = {"PC": "Public Charity", "PF": "Private Foundation", "CO": "Operating Foundation", "BO": "Broadly Supported", "09": "Public Charity", "03": "Private Foundation"}
        df["foundation_type"] = df["FOUNDATION"].map(foundation_map).fillna("Public Charity") if "FOUNDATION" in df.columns else "Public Charity"
        df["deductibility"] = "Tax-Deductible"
        if "DEDUCTIBILITY" in df.columns:
            df["deductibility"] = df["DEDUCTIBILITY"].apply(lambda x: "Not Tax-Deductible" if str(x) == "2" else "Tax-Deductible")
        if "RULING_DATE" in df.columns:
            df["tax_exempt_since"] = df["RULING_DATE"].astype(str).str[:4].replace("nan", "")
        else:
            df["tax_exempt_since"] = ""
        print(f"[AGENT 3] BMF merged")
    else:
        print("[AGENT 3] BMF EIN not found")
        df["foundation_type"] = "Public Charity"
        df["deductibility"] = "Tax-Deductible"
        df["tax_exempt_since"] = ""
else:
    print("[AGENT 3] BMF not found")
    df["foundation_type"] = "Public Charity"
    df["deductibility"] = "Tax-Deductible"
    df["tax_exempt_since"] = ""

if "SUBSECTION" in df.columns:
    df.loc[df["SUBSECTION"].astype(str) == "04", "deductibility"] = "Not Tax-Deductible"
    df.loc[df["SUBSECTION"].astype(str) == "04", "deductibility_warning"] = "This is a 501(c)(4). Donations are NOT tax-deductible."

def get_badges(row):
    badges = []
    ty = str(row.get("tax_year_ext", ""))
    if ty in ["2022", "2023", "2024", "2025"]:
        badges.append("IRS Active")
    fc = pd.to_numeric(row.get("filing_count"), errors="coerce")
    if pd.notna(fc) and fc >= 3:
        badges.append("Consistent Filer")
    score = pd.to_numeric(row.get("MERIT_score"), errors="coerce")
    if pd.notna(score) and score >= 75:
        badges.append("High Impact")
    pr = pd.to_numeric(row.get("program_ratio"), errors="coerce")
    if pd.notna(pr) and pr >= 0.85:
        badges.append("Highly Efficient")
    if not badges:
        badges.append("Newly Filed")
    return "|".join(badges)

df["badges"] = df.apply(get_badges, axis=1)

print("[AGENT 3] ProPublica enrichment...")
propub_dir = "data/propublica_cache"
propub_hits = 0
if os.path.exists(propub_dir):
    for i, row in df.iterrows():
        ein = str(row["EIN"]).strip()
        cache_file = f"{propub_dir}/{ein}.json"
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                df.at[i, "propub_mission"] = data.get("mission", "")
                df.at[i, "propub_website"] = data.get("website", "")
                df.at[i, "propub_address"] = data.get("address", "")
                propub_hits += 1
            except:
                pass
    print(f"[AGENT 3] ProPublica: {propub_hits}/{len(df)}")

print("[AGENT 3] Rebuilding categories...")
os.makedirs("data/categories", exist_ok=True)
df["ntee_major"] = df["NTEE"].astype(str).str[0].str.upper()
df.loc[df["ntee_major"].isin(["N", "n"]), "ntee_major"] = "Unknown"

NTEE_DESC = {
    "A": "Arts, Culture & Humanities", "B": "Education",
    "C": "Environment & Animals", "D": "Health",
    "E": "Human Services", "F": "International",
    "G": "Public & Societal Benefit", "H": "Religion Related",
    "K": "Food & Agriculture", "L": "Housing & Shelter",
    "M": "Crime & Legal", "N": "Recreation & Sports",
    "O": "Youth Development", "P": "Human & Civil Rights",
    "Q": "Community Improvement", "T": "Philanthropy",
    "U": "Science & Technology", "X": "Religion Related"
}

for major, group in df.groupby("ntee_major"):
    if major in ["", "N"]:
        continue
    group["MERIT_score_num"] = pd.to_numeric(group["MERIT_score"], errors="coerce").fillna(0)
    top = group.sort_values("MERIT_score_num", ascending=False).head(500)
    records = []
    for _, row in top.iterrows():
        records.append({
            "ein": row["EIN"], "name": row["NAME"], "state": row["STATE"],
            "city": row.get("CITY", row.get("CITY_bmf", "")),
            "revenue": row.get("revenue_num", row.get("revenue", "")),
            "MERIT_score": row.get("MERIT_score", ""),
            "financial_health": row.get("financial_health", ""),
            "operational_efficiency": row.get("operational_efficiency", ""),
            "sustainability_score": row.get("sustainability_score", ""),
            "scale_trajectory": row.get("scale_trajectory", ""),
            "compliance_score": row.get("compliance_score", ""),
            "program_ratio": row.get("program_ratio", ""),
            "badges": row.get("badges", ""),
            "foundation_type": row.get("foundation_type", "Public Charity"),
            "deductibility": row.get("deductibility", "Tax-Deductible"),
            "mission": row.get("propub_mission", row.get("mission_ext", "")),
            "confidence": row.get("confidence", "Medium")
        })
    cat_name = NTEE_DESC.get(major, f"Category {major}")
    with open(f"data/categories/{major}.json", "w", encoding="utf-8") as f:
        json.dump({"category_code": major, "category_name": cat_name, "count": len(records), "orgs": records}, f)

print(f"[AGENT 3] Rebuilt {len(df['ntee_major'].unique())} categories")
df.to_csv("data/csv/final_profiles.csv", index=False)
print(f"[AGENT 3] Wrote final_profiles.csv ({len(df)} orgs)")
#!/usr/bin/env python3
import os, json, pandas as pd

print("[AGENT 3] Loading scored orgs...")
df = pd.read_csv("data/csv/scored_orgs.csv", dtype=str)
df["EIN"] = df["EIN"].astype(str).str.replace(".0", "").str.strip()
print(f"[AGENT 3] Loaded {len(df)} orgs")

BMF_PATH = "data/irs_bmf.csv"
if os.path.exists(BMF_PATH):
    print("[AGENT 3] Loading BMF...")
    bmf = pd.read_csv(BMF_PATH, dtype=str, low_memory=False)
    bmf_ein_col = None
    for c in ["EIN", "ein", "EIN2"]:
        if c in bmf.columns:
            bmf_ein_col = c
            break
    if bmf_ein_col:
        bmf[bmf_ein_col] = bmf[bmf_ein_col].astype(str).str.replace(".0", "").str.strip()
        bmf_cols = {}
        for target, candidates in {
            "SUBSECTION": ["SUBSECTION", "SUBSECCD"],
            "FOUNDATION": ["FOUNDATION", "FOUNDATIONCD"],
            "RULING_DATE": ["RULING_DT", "RULING_DATE"],
            "DEDUCTIBILITY": ["DEDUCTIBILITY", "DEDUCTCD"],
            "NTEE_CD": ["NTEE_CD", "NTEE"],
            "CITY": ["CITY", "CITY_NAME"],
            "STATE": ["STATE", "STATE_NAME"]
        }.items():
            for c in candidates:
                if c in bmf.columns:
                    bmf_cols[target] = c
                    break
        merge_cols = [bmf_ein_col] + list(bmf_cols.values())
        bmf_subset = bmf[merge_cols].rename(columns={v: k for k, v in bmf_cols.items()})
        bmf_subset.rename(columns={bmf_ein_col: "EIN"}, inplace=True)
        df = df.merge(bmf_subset, on="EIN", how="left", suffixes=("", "_bmf"))
        
        foundation_map = {"PC": "Public Charity", "PF": "Private Foundation", "CO": "Operating Foundation", "BO": "Broadly Supported", "09": "Public Charity", "03": "Private Foundation"}
        df["foundation_type"] = df["FOUNDATION"].map(foundation_map).fillna("Public Charity") if "FOUNDATION" in df.columns else "Public Charity"
        df["deductibility"] = "Tax-Deductible"
        if "DEDUCTIBILITY" in df.columns:
            df["deductibility"] = df["DEDUCTIBILITY"].apply(lambda x: "Not Tax-Deductible" if str(x) == "2" else "Tax-Deductible")
        if "RULING_DATE" in df.columns:
            df["tax_exempt_since"] = df["RULING_DATE"].astype(str).str[:4].replace("nan", "")
        else:
            df["tax_exempt_since"] = ""
        print("[AGENT 3] BMF merged")
    else:
        print("[AGENT 3] BMF EIN not found")
        df["foundation_type"] = "Public Charity"
        df["deductibility"] = "Tax-Deductible"
        df["tax_exempt_since"] = ""
else:
    print("[AGENT 3] BMF not found")
    df["foundation_type"] = "Public Charity"
    df["deductibility"] = "Tax-Deductible"
    df["tax_exempt_since"] = ""

if "SUBSECTION" in df.columns:
    df.loc[df["SUBSECTION"].astype(str) == "04", "deductibility"] = "Not Tax-Deductible"
    df.loc[df["SUBSECTION"].astype(str) == "04", "deductibility_warning"] = "This is a 501(c)(4). Donations are NOT tax-deductible."

def get_badges(row):
    badges = []
    ty = str(row.get("tax_year_ext", ""))
    if ty in ["2022", "2023", "2024", "2025"]:
        badges.append("IRS Active")
    fc = pd.to_numeric(row.get("filing_count"), errors="coerce")
    if pd.notna(fc) and fc >= 3:
        badges.append("Consistent Filer")
    score = pd.to_numeric(row.get("MERIT_score"), errors="coerce")
    if pd.notna(score) and score >= 75:
        badges.append("High Impact")
    pr = pd.to_numeric(row.get("program_ratio"), errors="coerce")
    if pd.notna(pr) and pr >= 0.85:
        badges.append("Highly Efficient")
    if not badges:
        badges.append("Newly Filed")
    return "|".join(badges)

df["badges"] = df.apply(get_badges, axis=1)

print("[AGENT 3] ProPublica enrichment...")
propub_dir = "data/propublica_cache"
propub_hits = 0
if os.path.exists(propub_dir):
    for i, row in df.iterrows():
        ein = str(row["EIN"]).strip()
        cache_file = f"{propub_dir}/{ein}.json"
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                df.at[i, "propub_mission"] = data.get("mission", "")
                df.at[i, "propub_website"] = data.get("website", "")
                df.at[i, "propub_address"] = data.get("address", "")
                propub_hits += 1
            except:
                pass
    print(f"[AGENT 3] ProPublica: {propub_hits}/{len(df)}")

print("[AGENT 3] Rebuilding categories...")
os.makedirs("data/categories", exist_ok=True)
df["ntee_major"] = df["NTEE"].astype(str).str[0].str.upper()
df.loc[df["ntee_major"].isin(["N", "n"]), "ntee_major"] = "Unknown"

NTEE_DESC = {
    "A": "Arts, Culture & Humanities", "B": "Education",
    "C": "Environment & Animals", "D": "Health",
    "E": "Human Services", "F": "International",
    "G": "Public & Societal Benefit", "H": "Religion Related",
    "K": "Food & Agriculture", "L": "Housing & Shelter",
    "M": "Crime & Legal", "N": "Recreation & Sports",
    "O": "Youth Development", "P": "Human & Civil Rights",
    "Q": "Community Improvement", "T": "Philanthropy",
    "U": "Science & Technology", "X": "Religion Related"
}

for major, group in df.groupby("ntee_major"):
    if major in ["", "N"]:
        continue
    group["MERIT_score_num"] = pd.to_numeric(group["MERIT_score"], errors="coerce").fillna(0)
    top = group.sort_values("MERIT_score_num", ascending=False).head(500)
    records = []
    for _, row in top.iterrows():
        records.append({
            "ein": row["EIN"], "name": row["NAME"], "state": row["STATE"],
            "city": row.get("CITY", row.get("CITY_bmf", "")),
            "revenue": row.get("revenue_num", row.get("revenue", "")),
            "MERIT_score": row.get("MERIT_score", ""),
            "financial_health": row.get("financial_health", ""),
            "operational_efficiency": row.get("operational_efficiency", ""),
            "sustainability_score": row.get("sustainability_score", ""),
            "scale_trajectory": row.get("scale_trajectory", ""),
            "compliance_score": row.get("compliance_score", ""),
            "program_ratio": row.get("program_ratio", ""),
            "badges": row.get("badges", ""),
            "foundation_type": row.get("foundation_type", "Public Charity"),
            "deductibility": row.get("deductibility", "Tax-Deductible"),
            "mission": row.get("propub_mission", row.get("mission_ext", "")),
            "confidence": row.get("confidence", "Medium")
        })
    cat_name = NTEE_DESC.get(major, f"Category {major}")
    with open(f"data/categories/{major}.json", "w", encoding="utf-8") as f:
        json.dump({"category_code": major, "category_name": cat_name, "count": len(records), "orgs": records}, f)

print(f"[AGENT 3] Rebuilt {len(df['ntee_major'].unique())} categories")
df.to_csv("data/csv/final_profiles.csv", index=False)
print(f"[AGENT 3] Wrote final_profiles.csv ({len(df)} orgs)")
