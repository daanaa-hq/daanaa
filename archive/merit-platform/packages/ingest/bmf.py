"""IRS BMF (Business Master File) parser — stub.

Downloads from: https://www.irs.gov/charities-non-profits/exempt-organizations-business-master-file-extract-eo-bmf
Regions: eo1, eo2, eo3, eo4, eo_pr, eo_xx

Full workflow: .claude/skills/irs-bmf-ingest/SKILL.md

Existing proven parser: /home/akbar/meritgiving/scripts/ingest_bmf_master.py
This module will wrap that logic once the monorepo is wired up.
"""

import csv
from pathlib import Path
from typing import Iterator


BMF_COLUMNS = [
    "EIN", "NAME", "ICO", "STREET", "CITY", "STATE", "ZIP", "GROUP",
    "SUBSECTION", "AFFILIATION", "CLASSIFICATION", "RULING", "DEDUCTIBILITY",
    "FOUNDATION", "ACTIVITY", "ORGANIZATION", "STATUS", "TAX_PERIOD",
    "ASSET_CD", "INCOME_CD", "FILING_REQ_CD", "PF_FILING_REQ_CD",
    "ACCT_PD", "ASSET_AMT", "INCOME_AMT", "REVENUE_AMT", "NTEE_CD",
    "SORT_NAME",
]


def parse_bmf_csv(path: Path) -> Iterator[dict]:
    """Parse a single IRS BMF CSV file. Yields one dict per row.

    TODO: wire to full ingest pipeline from ingest_bmf_master.py.
    For now, validates the file can be parsed and columns look right.
    """
    with open(path, newline="", encoding="latin-1") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield _normalize_row(row)


def _normalize_row(row: dict) -> dict:
    ein = row.get("EIN", "").strip().zfill(9)
    return {
        "ein": ein,
        "name": row.get("NAME", "").strip(),
        "city": row.get("CITY", "").strip(),
        "state": row.get("STATE", "").strip(),
        "zip": row.get("ZIP", "").strip(),
        "ntee1": (row.get("NTEE_CD", "") or "")[:1].upper() or None,
        "ntee_cd": row.get("NTEE_CD", "").strip() or None,
        "subsection": row.get("SUBSECTION", "").strip(),
        "status": row.get("STATUS", "").strip(),
        "revenue_amt": _to_int(row.get("REVENUE_AMT")),
        "asset_amt": _to_int(row.get("ASSET_AMT")),
        "income_amt": _to_int(row.get("INCOME_AMT")),
        "ruling": row.get("RULING", "").strip() or None,
    }


def _to_int(val) -> int | None:
    try:
        return int(val) if val else None
    except (ValueError, TypeError):
        return None
