#!/usr/bin/env python3
"""
Workstream D: Data Cleaning, Deduplication, and Master Merge
Phase 0 — MERIT Data Pipeline

Purpose:
  1. Load all CSV outputs from Workstreams A, B, and C
  2. Deduplicate organizations (one row per EIN)
  3. Merge financials across sources (one row per EIN per tax year)
  4. Apply all quality gates
  5. Cross-check against revocation list
  6. Output clean master files

Input:
  - csv/master_orgs_propublica.csv (from Workstream A)
  - csv/master_orgs_irs_s3.csv (from Workstream B)
  - csv/master_orgs_bmf.csv (from Workstream C)
  - csv/financials_annual_propublica.csv (from Workstream A)
  - csv/financials_annual_irs_s3.csv (from Workstream B)
  - csv/auto_revocation_flags.csv (from Workstream C)
  - csv/ntee_taxonomy.csv (from Workstream C)

Output:
  - csv/master_orgs.csv (deduplicated, one row per EIN)
  - csv/financials_annual.csv (deduplicated, one row per EIN per year)
  - csv/ntee_taxonomy.csv (reference table)
  - csv/data_quality_report.csv (quality metrics)
  - logs/workstream_d_*.log

Usage:
    python workstream_d_master_merge.py --validate --output
"""

import argparse
import csv
import gzip
import json
import logging
import os
import re
import shutil
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# ─── CONFIGURATION ──────────────────────────────────────────────────────────
CSV_DIR = Path("/home/akbar/meritgiving/data/reports/meritgiving/data/csv")
LOG_DIR = Path("/home/akbar/meritgiving/data/reports/meritgiving/data/logs")

# Quality gate thresholds
MIN_REVENUE_YEAR = 2011
MAX_REVENUE_YEAR = 2023

# Quality gates
VALID_SUBSECTIONS = {"03"}
VALID_DEDUCTIBILITY = {"PC", "POF"}
SKIP_DEDUCTIBILITY = {"PF"}

# Setup directories
for d in [CSV_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ─── LOGGING ────────────────────────────────────────────────────────────────
def setup_logging():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"workstream_d_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger("WorkstreamD")

logger = setup_logging()


# ─── DATA LOADERS ───────────────────────────────────────────────────────────
def load_csv(filepath: Path) -> List[Dict]:
    """Load a CSV file into a list of dictionaries."""
    records = []
    
    if not filepath.exists():
        logger.warning(f"File not found: {filepath}")
        return records
    
    try:
        open_func = gzip.open if str(filepath).endswith(".gz") else open
        
        with open_func(filepath, "rt", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(dict(row))
        
        logger.info(f"Loaded {len(records)} records from {filepath.name}")
    except Exception as e:
        logger.error(f"Error loading {filepath}: {e}")
    
    return records


def load_all_sources() -> Dict[str, List[Dict]]:
    """Load all source CSV files."""
    sources = {}
    
    # Organization sources
    sources["orgs_propublica"] = load_csv(CSV_DIR / "master_orgs_propublica.csv")
    sources["orgs_irs_s3"] = load_csv(CSV_DIR / "master_orgs_irs_s3.csv")
    sources["orgs_bmf"] = load_csv(CSV_DIR / "master_orgs_bmf.csv")
    
    # Financial sources
    sources["fins_propublica"] = load_csv(CSV_DIR / "financials_annual_propublica.csv")
    sources["fins_irs_s3"] = load_csv(CSV_DIR / "financials_annual_irs_s3.csv")
    
    # Reference data
    sources["revocations"] = load_csv(CSV_DIR / "auto_revocation_flags.csv")
    sources["ntee"] = load_csv(CSV_DIR / "ntee_taxonomy.csv")
    
    return sources


# ─── QUALITY GATES ──────────────────────────────────────────────────────────
class QualityGate:
    """Implements all quality gates for the pipeline."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.stats = defaultdict(int)
    
    # Gate 1: EIN must be 9 digits, zero-padded, no hyphens
    def validate_ein(self, ein: str) -> Optional[str]:
        if not ein:
            self.stats["ein_empty"] += 1
            return None
        
        cleaned = re.sub(r"[^0-9]", "", str(ein))
        if len(cleaned) != 9:
            self.stats[f"ein_invalid_length_{len(cleaned)}"] += 1
            return None
        
        return cleaned
    
    # Gate 2: Subsection code must be "03" (501(c)(3))
    def validate_subsection(self, subsection: str) -> bool:
        if not subsection:
            self.stats["subsection_empty"] += 1
            return False
        
        subsection = str(subsection).strip()
        if subsection not in VALID_SUBSECTIONS:
            self.stats[f"subsection_invalid_{subsection}"] += 1
            return False
        
        return True
    
    # Gate 3: Deductibility code must be PC or POF (skip PF)
    def validate_deductibility(self, deductibility: str) -> Tuple[bool, str]:
        if not deductibility:
            self.stats["deductibility_empty"] += 1
            return True, ""  # Empty is acceptable, we'll flag it
        
        deductibility = str(deductibility).strip().upper()
        if deductibility in SKIP_DEDUCTIBILITY:
            self.stats["deductibility_pf_skipped"] += 1
            return False, "PF"
        
        return True, deductibility
    
    # Gate 5: Revenue/Expense/Assets must be integers (cents)
    def validate_cents(self, value: Any, field_name: str) -> Optional[int]:
        if value is None or value == "":
            return None
        
        try:
            if isinstance(value, int):
                return value
            if isinstance(value, str):
                # Already in cents from upstream
                clean = value.replace(",", "").replace("$", "").replace(".", "").strip()
                return int(clean) if clean else None
            if isinstance(value, float):
                # Should not happen but handle gracefully
                return int(round(value * 100))
            return None
        except (ValueError, TypeError):
            self.stats[f"cents_invalid_{field_name}"] += 1
            return None
    
    # Gate 6: Source provenance tracking
    def validate_provenance(self, source: str) -> str:
        valid_sources = {"ProPublica", "IRS_S3", "IRS_BMF", "Candid"}
        if source in valid_sources:
            return source
        return "UNKNOWN"


# ─── DEDUPLICATION ──────────────────────────────────────────────────────────
class DeduplicationEngine:
    """Handles deduplication across all sources."""
    
    def __init__(self, quality_gate: QualityGate):
        self.qg = quality_gate
        self.master_orgs: Dict[str, Dict] = {}  # ein -> best record
        self.financials: Dict[str, Dict] = {}  # ein|year -> best record
        self.source_counts = defaultdict(int)
    
    def _merge_org_records(self, existing: Dict, new: Dict) -> Dict:
        """Merge two organization records, preferring non-empty fields."""
        merged = dict(existing)
        
        # Prefer records with more complete data
        for key, value in new.items():
            if key in ["raw_extracted_at", "extracted_at"]:
                continue
            
            if value and not merged.get(key):
                merged[key] = value
            elif value and key in ["name"] and len(str(value)) > len(str(merged.get(key, ""))):
                # Prefer longer, more descriptive names
                merged[key] = value
        
        # Track all sources
        existing_sources = set(merged.get("_sources", []))
        existing_sources.add(new.get("source_provenance", "UNKNOWN"))
        merged["_sources"] = sorted(existing_sources)
        merged["source_provenance"] = "|".join(sorted(existing_sources))
        
        return merged
    
    def add_org(self, record: Dict) -> bool:
        """Add an organization record, handling deduplication."""
        ein = self.qg.validate_ein(record.get("ein", ""))
        if not ein:
            return False
        
        subsection = record.get("subsection", "")
        if not self.qg.validate_subsection(subsection):
            return False
        
        deductibility = record.get("deductibility", record.get("deductibility_code", ""))
        is_valid, ded_code = self.qg.validate_deductibility(deductibility)
        if not is_valid:
            return False
        
        # Normalize record
        clean_record = {
            "ein": ein,
            "name": record.get("name", record.get("organization_name", "")).strip(),
            "address": record.get("address", record.get("street", "")).strip(),
            "city": record.get("city", "").strip(),
            "state": record.get("state", "").strip(),
            "zipcode": record.get("zipcode", record.get("zip", "")).strip(),
            "subsection": subsection,
            "deductibility_code": ded_code,
            "ntee_code": record.get("ntee_code", "").strip(),
            "ntee_description": record.get("ntee_description", "").strip(),
            "organization_type": record.get("organization_type", "PC" if ded_code == "PC" else "POF"),
            "foundation_status": record.get("foundation_status", "").strip(),
            "activity_codes": record.get("activity_codes", "").strip(),
            "classification_codes": record.get("classification_codes", "").strip(),
            "ruling_date": record.get("ruling_date", "").strip(),
            "affiliation_code": record.get("affiliation_code", "").strip(),
            "source_provenance": record.get("source_provenance", "UNKNOWN"),
            "raw_extracted_at": record.get("raw_extracted_at", datetime.now().isoformat()),
        }
        
        # Merge with existing
        if ein in self.master_orgs:
            self.master_orgs[ein] = self._merge_org_records(self.master_orgs[ein], clean_record)
            self.source_counts["merged"] += 1
        else:
            clean_record["_sources"] = [clean_record["source_provenance"]]
            self.master_orgs[ein] = clean_record
            self.source_counts["new"] += 1
        
        return True
    
    def add_financial(self, record: Dict) -> bool:
        """Add a financial record, handling deduplication by EIN + tax year."""
        ein = self.qg.validate_ein(record.get("ein", ""))
        if not ein:
            return False
        
        tax_year = record.get("tax_year", "")
        if not tax_year:
            tax_period = record.get("tax_period", "")
            if tax_period and len(str(tax_period)) >= 4:
                tax_year = str(tax_period)[:4]
            else:
                return False
        
        # Validate year range
        try:
            year_int = int(tax_year)
            if year_int < MIN_REVENUE_YEAR or year_int > MAX_REVENUE_YEAR:
                return False
        except (ValueError, TypeError):
            return False
        
        key = f"{ein}|{tax_year}"
        
        # Validate cents fields
        def get_cents(field: str) -> Optional[int]:
            return self.qg.validate_cents(record.get(field), field)
        
        clean_record = {
            "ein": ein,
            "tax_year": tax_year,
            "tax_period": record.get("tax_period", ""),
            "form_type": record.get("form_type", ""),
            "revenue_cents": get_cents("revenue_cents"),
            "expenses_cents": get_cents("expenses_cents"),
            "assets_eoy_cents": get_cents("assets_eoy_cents"),
            "assets_boy_cents": get_cents("assets_boy_cents"),
            "liabilities_eoy_cents": get_cents("liabilities_eoy_cents"),
            "liabilities_boy_cents": get_cents("liabilities_boy_cents"),
            "net_assets_cents": get_cents("net_assets_cents"),
            "contributions_cents": get_cents("contributions_cents"),
            "program_service_revenue_cents": get_cents("program_service_revenue_cents"),
            "investment_income_cents": get_cents("investment_income_cents"),
            "fundraising_expenses_cents": get_cents("fundraising_expenses_cents"),
            "officer_compensation_cents": get_cents("officer_compensation_cents"),
            "other_salaries_cents": get_cents("other_salaries_cents"),
            "grants_paid_cents": get_cents("grants_paid_cents"),
            "total_employees": record.get("total_employees", None),
            "total_volunteers": record.get("total_volunteers", None),
            "object_id": record.get("object_id", ""),
            "source_provenance": record.get("source_provenance", "UNKNOWN"),
            "extracted_at": record.get("extracted_at", datetime.now().isoformat()),
        }
        
        # Merge strategy: prefer records with more financial data
        if key in self.financials:
            existing = self.financials[key]
            existing_data_count = sum(1 for v in [
                existing.get("revenue_cents"), existing.get("expenses_cents"),
                existing.get("assets_eoy_cents")
            ] if v is not None)
            new_data_count = sum(1 for v in [
                clean_record.get("revenue_cents"), clean_record.get("expenses_cents"),
                clean_record.get("assets_eoy_cents")
            ] if v is not None)
            
            if new_data_count > existing_data_count:
                # Keep sources from both
                sources = set(existing.get("source_provenance", "").split("|"))
                sources.add(clean_record.get("source_provenance", ""))
                clean_record["source_provenance"] = "|".join(sorted(sources - {"", "UNKNOWN"}))
                self.financials[key] = clean_record
                self.source_counts["fin_merged_better"] += 1
            else:
                self.source_counts["fin_kept_existing"] += 1
        else:
            self.financials[key] = clean_record
            self.source_counts["fin_new"] += 1
        
        return True
    
    def apply_revocation_flags(self, revocations: List[Dict]):
        """Apply revocation flags to master organizations."""
        revoked_count = 0
        
        for rev in revocations:
            ein = self.qg.validate_ein(rev.get("ein", ""))
            if not ein or ein not in self.master_orgs:
                continue
            
            is_revoked = str(rev.get("is_revoked", "")).lower() in ("true", "1", "yes")
            if is_revoked:
                self.master_orgs[ein]["is_revoked"] = True
                self.master_orgs[ein]["revocation_date"] = rev.get("revocation_date", "")
                self.master_orgs[ein]["revocation_source"] = rev.get("revocation_source", "")
                revoked_count += 1
        
        logger.info(f"Applied revocation flags: {revoked_count} organizations flagged")
        self.source_counts["revoked"] = revoked_count


# ─── STATISTICS ─────────────────────────────────────────────────────────────
def compute_statistics(engine: DeduplicationEngine) -> Dict:
    """Compute summary statistics for the merged dataset."""
    stats = {
        "total_unique_organizations": len(engine.master_orgs),
        "total_unique_financial_records": len(engine.financials),
        "organizations_by_state": defaultdict(int),
        "organizations_by_type": defaultdict(int),
        "organizations_by_ntee_major": defaultdict(int),
        "financial_records_by_year": defaultdict(int),
        "financial_records_with_revenue": 0,
        "financial_records_with_expenses": 0,
        "financial_records_with_assets": 0,
        "revoked_organizations": 0,
        "source_breakdown": defaultdict(int),
    }
    
    # Org stats
    for ein, org in engine.master_orgs.items():
        stats["organizations_by_state"][org.get("state", "UNKNOWN")] += 1
        stats["organizations_by_type"][org.get("organization_type", "UNKNOWN")] += 1
        
        ntee = org.get("ntee_code", "")
        if ntee:
            major = ntee[0] if len(ntee) >= 1 else "Z"
            stats["organizations_by_ntee_major"][major] += 1
        
        if org.get("is_revoked"):
            stats["revoked_organizations"] += 1
        
        source = org.get("source_provenance", "UNKNOWN")
        stats["source_breakdown"][source] += 1
    
    # Financial stats
    for key, fin in engine.financials.items():
        year = fin.get("tax_year", "UNKNOWN")
        stats["financial_records_by_year"][year] += 1
        
        if fin.get("revenue_cents") is not None:
            stats["financial_records_with_revenue"] += 1
        if fin.get("expenses_cents") is not None:
            stats["financial_records_with_expenses"] += 1
        if fin.get("assets_eoy_cents") is not None:
            stats["financial_records_with_assets"] += 1
    
    return stats


# ─── CSV OUTPUT ─────────────────────────────────────────────────────────────
class MasterWriter:
    """Writes the final master CSV files."""
    
    def __init__(self):
        self.master_org_file = CSV_DIR / "master_orgs.csv"
        self.master_fin_file = CSV_DIR / "financials_annual.csv"
        self.quality_report_file = CSV_DIR / "data_quality_report.csv"
    
    def write_master_orgs(self, orgs: Dict[str, Dict]):
        """Write deduplicated master organizations file."""
        with open(self.master_org_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "ein", "name", "address", "city", "state", "zipcode",
                    "subsection", "deductibility_code", "ntee_code", "ntee_description",
                    "organization_type", "foundation_status", "activity_codes",
                    "classification_codes", "ruling_date", "affiliation_code",
                    "is_revoked", "revocation_date", "revocation_source",
                    "source_provenance", "raw_extracted_at"
                ]
            )
            writer.writeheader()
            
            for ein in sorted(orgs.keys()):
                org = orgs[ein]
                # Remove internal tracking fields
                row = {k: v for k, v in org.items() if not k.startswith("_")}
                writer.writerow(row)
        
        logger.info(f"Wrote {len(orgs)} organizations to {self.master_org_file.name}")
    
    def write_master_financials(self, financials: Dict[str, Dict]):
        """Write deduplicated master financials file."""
        with open(self.master_fin_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "ein", "tax_year", "tax_period", "form_type",
                    "revenue_cents", "expenses_cents", "assets_eoy_cents",
                    "assets_boy_cents", "liabilities_eoy_cents", "liabilities_boy_cents",
                    "net_assets_cents", "contributions_cents", "program_service_revenue_cents",
                    "investment_income_cents", "fundraising_expenses_cents",
                    "officer_compensation_cents", "other_salaries_cents", "grants_paid_cents",
                    "total_employees", "total_volunteers",
                    "object_id", "source_provenance", "extracted_at"
                ]
            )
            writer.writeheader()
            
            # Sort by EIN, then tax year
            sorted_keys = sorted(financials.keys(), key=lambda k: (k.split("|")[0], k.split("|")[1]))
            
            for key in sorted_keys:
                fin = financials[key]
                row = {k: v for k, v in fin.items() if not k.startswith("_")}
                writer.writerow(row)
        
        logger.info(f"Wrote {len(financials)} financial records to {self.master_fin_file.name}")
    
    def write_quality_report(self, stats: Dict, qg: QualityGate, engine: DeduplicationEngine):
        """Write data quality report."""
        with open(self.quality_report_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["metric_category", "metric_name", "value"])
            
            # High-level stats
            writer.writerow(["overview", "total_unique_organizations", stats["total_unique_organizations"]])
            writer.writerow(["overview", "total_unique_financial_records", stats["total_unique_financial_records"]])
            writer.writerow(["overview", "revoked_organizations", stats["revoked_organizations"]])
            
            # Quality gate stats
            for key, value in sorted(qg.stats.items()):
                writer.writerow(["quality_gate", key, value])
            
            # Deduplication stats
            for key, value in sorted(engine.source_counts.items()):
                writer.writerow(["deduplication", key, value])
            
            # Org distribution
            for state, count in sorted(stats["organizations_by_state"].items(), key=lambda x: -x[1])[:20]:
                writer.writerow(["org_distribution_state", state, count])
            
            for org_type, count in sorted(stats["organizations_by_type"].items(), key=lambda x: -x[1]):
                writer.writerow(["org_distribution_type", org_type, count])
            
            for ntee, count in sorted(stats["organizations_by_ntee_major"].items(), key=lambda x: -x[1]):
                writer.writerow(["org_distribution_ntee", ntee, count])
            
            # Financial distribution
            for year, count in sorted(stats["financial_records_by_year"].items()):
                writer.writerow(["financial_by_year", year, count])
            
            writer.writerow(["financial_completeness", "records_with_revenue", stats["financial_records_with_revenue"]])
            writer.writerow(["financial_completeness", "records_with_expenses", stats["financial_records_with_expenses"]])
            writer.writerow(["financial_completeness", "records_with_assets", stats["financial_records_with_assets"]])
            
            # Source breakdown
            for source, count in sorted(stats["source_breakdown"].items(), key=lambda x: -x[1]):
                writer.writerow(["source_breakdown", source, count])
        
        logger.info(f"Wrote quality report to {self.quality_report_file.name}")


# ─── MAIN WORKFLOW ──────────────────────────────────────────────────────────
def run_workstream_d(validate: bool = True, output: bool = True):
    """Execute Workstream D: Data cleaning and master merge."""
    logger.info("=" * 60)
    logger.info("Workstream D: Data Cleaning, Deduplication & Master Merge")
    logger.info("=" * 60)
    
    start_time = time.time()
    
    # Step 1: Load all sources
    logger.info("\n[Step 1] Loading all source files...")
    sources = load_all_sources()
    
    # Step 2: Initialize quality gates and deduplication engine
    logger.info("\n[Step 2] Initializing quality gates and deduplication engine...")
    qg = QualityGate()
    engine = DeduplicationEngine(qg)
    
    # Step 3: Process organization records
    logger.info("\n[Step 3] Processing organization records...")
    
    org_sources = [
        ("ProPublica", sources["orgs_propublica"]),
        ("IRS_S3", sources["orgs_irs_s3"]),
        ("IRS_BMF", sources["orgs_bmf"]),
    ]
    
    for source_name, records in org_sources:
        added = 0
        for record in records:
            if engine.add_org(record):
                added += 1
        logger.info(f"  {source_name}: {len(records)} loaded, {added} added/merged")
    
    logger.info(f"Total unique organizations after dedup: {len(engine.master_orgs)}")
    
    # Step 4: Process financial records
    logger.info("\n[Step 4] Processing financial records...")
    
    fin_sources = [
        ("ProPublica", sources["fins_propublica"]),
        ("IRS_S3", sources["fins_irs_s3"]),
    ]
    
    for source_name, records in fin_sources:
        added = 0
        for record in records:
            if engine.add_financial(record):
                added += 1
        logger.info(f"  {source_name}: {len(records)} loaded, {added} added/merged")
    
    logger.info(f"Total unique financial records after dedup: {len(engine.financials)}")
    
    # Step 5: Apply revocation flags
    logger.info("\n[Step 5] Applying revocation flags...")
    engine.apply_revocation_flags(sources["revocations"])
    
    # Step 6: Compute statistics
    logger.info("\n[Step 6] Computing statistics...")
    stats = compute_statistics(engine)
    
    # Step 7: Write output
    if output:
        logger.info("\n[Step 7] Writing master files...")
        writer = MasterWriter()
        writer.write_master_orgs(engine.master_orgs)
        writer.write_master_financials(engine.financials)
        writer.write_quality_report(stats, qg, engine)
    
    # Summary
    elapsed = time.time() - start_time
    logger.info("\n" + "=" * 60)
    logger.info("Workstream D Complete")
    logger.info(f"Unique organizations: {stats['total_unique_organizations']}")
    logger.info(f"Unique financial records: {stats['total_unique_financial_records']}")
    logger.info(f"Revoked organizations: {stats['revoked_organizations']}")
    logger.info(f"Orgs by type: {dict(stats['organizations_by_type'])}")
    logger.info(f"Top 5 states: {dict(sorted(stats['organizations_by_state'].items(), key=lambda x: -x[1])[:5])}")
    logger.info(f"Financial records with revenue: {stats['financial_records_with_revenue']}")
    logger.info(f"Financial records with expenses: {stats['financial_records_with_expenses']}")
    logger.info(f"Financial records with assets: {stats['financial_records_with_assets']}")
    logger.info(f"Elapsed time: {elapsed:.1f}s")
    logger.info("=" * 60)


# ─── CLI ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Workstream D: Data Cleaning, Deduplication & Master Merge",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full pipeline: validate and output
  python workstream_d_master_merge.py --validate --output
  
  # Validate only (no output)
  python workstream_d_master_merge.py --validate
  
  # Output only (skip validation)
  python workstream_d_master_merge.py --output
        """
    )
    parser.add_argument("--validate", action="store_true", help="Run validation")
    parser.add_argument("--output", action="store_true", help="Write output files")
    
    args = parser.parse_args()
    
    if not args.validate and not args.output:
        args.validate = True
        args.output = True
    
    logger.info("=" * 60)
    logger.info("Workstream D: Master Merge")
    logger.info(f"Validate: {args.validate} | Output: {args.output}")
    logger.info("=" * 60)
    
    run_workstream_d(validate=args.validate, output=args.output)


if __name__ == "__main__":
    main()
