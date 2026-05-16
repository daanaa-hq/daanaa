import pandas as pd

FILES = {
    "PC":    "data/corepcf/core_2019_pc.csv",
    "PZ":    "data/corepcf/core_2019_pz.csv",
    "OT_PZ": "data/corepcf/core_2019_ot_pz.csv",
}

for scope, path in FILES.items():
    print(f"\n{'='*50}")
    print(f"=== {scope}: {path} ===")
    
    # Load headers only
    df = pd.read_csv(path, nrows=0)
    cols = list(df.columns)
    print(f"Total columns: {len(cols)}")
    
    # Find revenue-related columns
    rev_keywords = ['REV', 'INCOME', 'CONTR', 'DUES', 'GOVT', 'PROGRAM', 'INVESTMENT', 'SPECIAL', 'GROSS', 'NET']
    rev_cols = [c for c in cols if any(k in c.upper() for k in rev_keywords)]
    print(f"Revenue-related columns ({len(rev_cols)}):")
    for c in rev_cols:
        print(f"  {c}")
    
    # Check specifically for TOTREV
    print(f"'TOTREV' present: {'TOTREV' in cols}")
    
    # Sample first 5 rows of top 5 revenue cols
    if rev_cols:
        sample = pd.read_csv(path, nrows=5, usecols=rev_cols[:5], dtype=str)
        print("\nSample values (first 5 rows):")
        for c in rev_cols[:5]:
            vals = sample[c].tolist()
            print(f"  {c}: {vals}")

