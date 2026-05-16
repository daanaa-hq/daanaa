#!/usr/bin/env python3
"""
AGENT 4: VALIDATOR
Mission: Run all quality gates, produce go/no-go report.
"""
import os, subprocess, sys, json
import pandas as pd
import numpy as np

REPORT = "VALIDATION_REPORT.txt"

try:
    df = pd.read_csv("data/csv/final_profiles.csv", dtype=str)
except Exception as e:
    print(f"[AGENT 4] Cannot load final_profiles.csv: {e}")
    sys.exit(1)

lines = []
lines.append("="*60)
lines.append("  MERITGIVING AGENT SWARM — VALIDATION REPORT")
lines.append(f"  {pd.Timestamp.now()}")
lines.append("="*60)

failures = 0
passes = 0

def gate(name, status, detail=""):
    global failures, passes
    symbol = "PASS" if status else "FAIL"
    if status:
        passes += 1
    else:
        failures += 1
    lines.append(f"\n[{name}] {symbol}")
    if detail:
        lines.append(f"  {detail}")
    return status

total = len(df)
missing_ein = df['EIN'].isnull().sum()
missing_name = df['NAME'].isnull().sum()
gate("1. MASTER INTEGRITY", missing_ein == 0 and missing_name == 0,
     f"Total: {total} | Missing EIN: {missing_ein} | Missing Name: {missing_name}")

df['MERIT_num'] = pd.to_numeric(df['MERIT_score'], errors='coerce')
unique_scores = df['MERIT_num'].nunique()
score_min = df['MERIT_num'].min()
score_max = df['MERIT_num'].max()
score_mean = df['MERIT_num'].mean()
score_std = df['MERIT_num'].std()
gate("2. MERIT SCORE DISTRIBUTION", unique_scores > 100 and score_std > 5,
     f"Unique: {unique_scores} | Range: {score_min:.1f}-{score_max:.1f} | Mean: {score_mean:.1f} | Std: {score_std:.1f}")

all_100 = (df['MERIT_num'] == 100.0).sum()
gate("3. NO 100.0 BUG", all_100 < total * 0.1,
     f"Orgs at exactly 100.0: {all_100}/{total} ({all_100/total*100:.1f}%)")

df['oe_num'] = pd.to_numeric(df['operational_efficiency'], errors='coerce')
oe_count = df['oe_num'].notna().sum()
gate("4. OPERATIONAL EFFICIENCY", oe_count > total * 0.5,
     f"Scored: {oe_count}/{total} ({oe_count/total*100:.1f}%)")

gauges = ['financial_health', 'operational_efficiency', 'sustainability_score', 
          'scale_trajectory', 'compliance_score']
missing_gauges = [g for g in gauges if g not in df.columns]
gate("5. ALL GAUGES PRESENT", len(missing_gauges) == 0,
     f"Missing: {', '.join(missing_gauges) if missing_gauges else 'None'}")

badge_orgs = df['badges'].notna().sum()
unique_badges = df['badges'].str.split('|').explode().nunique()
gate("6. BADGES", badge_orgs > total * 0.9 and unique_badges >= 3,
     f"Orgs with badges: {badge_orgs}/{total} | Unique badge types: {unique_badges}")

ft_count = df['foundation_type'].notna().sum()
gate("7. FOUNDATION TYPE", ft_count > total * 0.5,
     f"Enriched: {ft_count}/{total} ({ft_count/total*100:.1f}%)")

ded_warn = (df['deductibility'] == 'Not Tax-Deductible').sum()
gate("8. DEDUCTIBILITY LABELS", 'deductibility' in df.columns,
     f"Non-deductible flagged: {ded_warn} orgs")

cat_files = [f for f in os.listdir("data/categories") if f.endswith('.json')] if os.path.exists("data/categories") else []
gate("9. CATEGORY JSONS", len(cat_files) >= 10,
     f"Files: {len(cat_files)}")

pp_count = df['propub_mission'].notna().sum() if 'propub_mission' in df.columns else 0
gate("10. PROPUBLICA ENRICHMENT", pp_count > 0,
     f"Orgs with mission: {pp_count}/{total}")

lines.append("\n[11] SERVER SEARCH TEST")
try:
    r = subprocess.run(
        ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 
         'http://127.0.0.1:8081/search?q=education'],
        capture_output=True, text=True, timeout=10
    )
    status = r.stdout.strip()
    if status == "200":
        r2 = subprocess.run(
            ['curl', '-s', 'http://127.0.0.1:8081/search?q=education'],
            capture_output=True, text=True, timeout=10
        )
        try:
            data = json.loads(r2.stdout)
            result_count = len(data.get('results', []))
            gate("11. SERVER SEARCH", result_count > 0,
                 f"Status: 200 | Results: {result_count}")
        except:
            gate("11. SERVER SEARCH", False, "Status: 200 but invalid JSON response")
    else:
        gate("11. SERVER SEARCH", False, f"Status: {status}")
except Exception as e:
    gate("11. SERVER SEARCH", False, f"Server not responding: {e}")

lines.append("\n[12] ORG DETAIL TEST")
sample_ein = df[df['MERIT_num'].notna()].iloc[0]['EIN'] if len(df) > 0 else None
if sample_ein:
    try:
        r = subprocess.run(
            ['curl', '-s', f'http://127.0.0.1:8081/org/{sample_ein}'],
            capture_output=True, text=True, timeout=10
        )
        try:
            data = json.loads(r.stdout)
            has_name = bool(data.get('name'))
            has_score = 'MERIT_score' in data
            gate("12. ORG DETAIL", has_name and has_score,
                 f"EIN: {sample_ein} | Has name: {has_name} | Has score: {has_score}")
        except:
            gate("12. ORG DETAIL", False, "Invalid JSON")
    except Exception as e:
        gate("12. ORG DETAIL", False, f"Error: {e}")
else:
    gate("12. ORG DETAIL", False, "No sample EIN available")

lines.append("\n[13] DISK SPACE")
try:
    stat = os.statvfs('.')
    free_gb = stat.f_bavail * stat.f_frsize / (1024**3)
    gate("13. DISK SPACE", free_gb > 50,
         f"Free: {free_gb:.1f} GB")
except:
    gate("13. DISK SPACE", False, "Cannot check disk")

lines.append(f"\n{'='*60}")
lines.append(f"  RESULTS: {passes} passed, {failures} failed")
lines.append(f"  SCORE: {passes}/{passes+failures} gates")

if failures == 0:
    lines.append("\n  ALL GATES PASS")
    lines.append("  DATA LAYER IS 'ALL SET'")
    lines.append("  Ready for: UI polish -> Public tunnel -> Board review")
    exit_code = 0
elif failures <= 2:
    lines.append("\n  MOSTLY PASS")
    lines.append("  Fix the 2 failures above, then you're ready.")
    exit_code = 0
else:
    lines.append("\n  MULTIPLE FAILURES")
    lines.append("  Do NOT declare 'all set' until these are fixed.")
    exit_code = 1

lines.append(f"\n  Target: Board Confidence 74 -> 83 (Data Fixed)")
lines.append(f"  Current blocker: {'None' if failures == 0 else f'{failures} gates failing'}")
lines.append("="*60)

report_text = '\n'.join(lines)
with open(REPORT, 'w') as f:
    f.write(report_text)

print(report_text)
sys.exit(exit_code)
