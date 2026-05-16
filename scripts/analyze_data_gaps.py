#!/usr/bin/env python3
"""
MeritGiving Data Gap Analysis
Scans what you HAVE vs what you NEED for scoring.

Run after ingest_bmf_master.py:
    python3 scripts/analyze_data_gaps.py
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path.home() / "meritgiving" / "data" / "meritgiving.db"
REPORT_PATH = Path.home() / "meritgiving" / "data" / "gap_analysis.json"

print("=" * 60)
print("MeritGiving Data Gap Analysis")
print("=" * 60)

conn = sqlite3.connect(str(DB_PATH))
c = conn.cursor()

# Check what tables exist
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in c.fetchall()]
print(f"\nExisting tables: {tables}")

# Check registry size
c.execute("SELECT COUNT(*) FROM registry_enriched")
registry_size = c.fetchone()[0]
print(f"Registry size: {registry_size:,} orgs")

# ============================================================================
# GAP 1: DETAILED FINANCIALS
# ============================================================================
print("\n[GAP 1] Detailed Financials (Program Expenses, Fundraising Costs)")
print("  Status: ❌ MISSING")
print("  BMF has: REVENUE_AMT, ASSET_AMT, INCOME_AMT (top-line only)")
print("  Need from: NCCS CorePCF 2019-2022 OR IRS 990 XML 2023-2024")
print("  Impact: Cannot compute program_expense_ratio, fundraising_efficiency")
print("  Action: Download CorePCF files from nccs-data.urban.org")

# ============================================================================
# GAP 2: FILING RECENCY
# ============================================================================
print("\n[GAP 2] Filing Recency (last 990 filed date)")
print("  Status: ❌ MISSING")
print("  BMF has: No filing date field")
print("  Need from: ProPublica API OR IRS index files")
print("  Impact: Cannot flag stale filings (org may be dormant)")
print("  Action: Async ProPublica enrichment worker")

# ============================================================================
# GAP 3: MISSION TEXT / SCHEDULE O
# ============================================================================
print("\n[GAP 3] Mission Text / Narrative Descriptions")
print("  Status: ❌ MISSING")
print("  BMF has: NTEE1 code only")
print("  Need from: 990 XML Schedule O OR ProPublica")
print("  Impact: Cannot validate NTEE against mission, NLP categorization")
print("  Action: Extract Schedule O from 990 XML for top 10K orgs")

# ============================================================================
# GAP 4: GOVERNANCE DATA
# ============================================================================
print("\n[GAP 4] Governance (board size, independence, policies)")
print("  Status: ❌ MISSING")
print("  BMF has: None")
print("  Need from: 990 XML Part VI")
print("  Impact: Cannot score governance dimension")
print("  Action: Extract from 990 XML (only available on full 990, not EZ)")

# ============================================================================
# GAP 5: EXTERNAL VALIDATION
# ============================================================================
print("\n[GAP 5] External Validation (Charity Navigator, etc.)")
print("  Status: ❌ MISSING")
print("  Need from: Charity Navigator API, GreatNonprofits")
print("  Impact: No crowd/expert trust signals")
print("  Action: API enrichment (low priority until base data is solid)")

# ============================================================================
# GAP 6: HISTORICAL PANEL
# ============================================================================
print("\n[GAP 6] Multi-Year Financial History")
print("  Status: ❌ MISSING")
print("  BMF has: Single snapshot (latest monthly)")
print("  Need from: CorePCF 2019-2022 (5-year panel)")
print("  Impact: Cannot compute growth trends, volatility")
print("  Action: Download CorePCF panel")

# ============================================================================
# WHAT YOU HAVE (Strengths)
# ============================================================================
print("\n" + "=" * 60)
print("WHAT YOU HAVE (Use These Now)")
print("=" * 60)
print("  ✓ Master registry: 1.8M+ orgs with EIN, name, address")
print("  ✓ NTEE codes: Primary + NCCS major group mappings")
print("  ✓ Geocoded addresses: bmf_master_geocoded.csv")
print("  ✓ Monthly snapshots: Track changes over time")
print("  ✓ Revocation data: bmf_rev files")
print("  ✓ Ruling dates: Calculate org age")
print("  ✓ Foundation codes: Filter public vs private charities")
print("  ✓ Status codes: Active vs inactive")

# ============================================================================
# PRIORITY ROADMAP
# ============================================================================
print("\n" + "=" * 60)
print("RECOMMENDED EXECUTION ORDER")
print("=" * 60)
print("""
WEEK 1 (This week):
  1. Run ingest_bmf_master.py → Build filtered registry (~400K orgs)
  2. Run track_bmf_changes.py → Lifecycle tables
  3. Download NCCS CorePCF 2019-2022:
     → https://nccs-data.urban.org/data/core/YYYY/corepcfYYYY.csv
     → If URLs fail, email nccs@urban.org for direct links

WEEK 2:
  4. Load CorePCF into SQLite, join on EIN to registry
  5. Compute scoring dimensions (program ratio, efficiency, liquidity)
  6. Build percentile tables by NTEE + state

WEEK 3:
  7. Download IRS index_2023.csv, index_2024.csv
  8. Filter to EINs in your registry
  9. Selective XML download (only ~50K files, not 2M)
  10. Parse 2023-2024 financials, append to database

WEEK 4:
  11. ProPublica API enrichment (async, 1 req/sec)
  12. Charity Navigator API (free key, ~10K orgs)
  13. Build FastAPI endpoints to serve the data
  14. Public dashboard MVP
""")

# Save report
gap_report = {
    "analysis_date": datetime.now().isoformat(),
    "registry_size": registry_size,
    "existing_tables": tables,
    "gaps": [
        {"name": "Detailed Financials", "status": "missing", "source": "CorePCF or 990 XML", "priority": "critical"},
        {"name": "Filing Recency", "status": "missing", "source": "ProPublica API", "priority": "high"},
        {"name": "Mission Text", "status": "missing", "source": "990 XML Schedule O", "priority": "medium"},
        {"name": "Governance Data", "status": "missing", "source": "990 XML Part VI", "priority": "medium"},
        {"name": "External Validation", "status": "missing", "source": "Charity Navigator", "priority": "low"},
        {"name": "Historical Panel", "status": "missing", "source": "CorePCF 2019-2022", "priority": "critical"},
    ],
    "strengths": [
        "Master registry with 1.8M+ orgs",
        "NTEE codes and NCCS major groups",
        "Geocoded addresses",
        "Monthly change tracking",
        "Revocation flags",
        "Org age from ruling dates",
        "Public/private charity filter"
    ]
}

with open(REPORT_PATH, 'w') as f:
    json.dump(gap_report, f, indent=2)

print(f"\nGap report saved: {REPORT_PATH}")
conn.close()
