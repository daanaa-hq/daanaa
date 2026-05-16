#!/usr/bin/env python3
"""
Workstream B: IRS AWS S3 XML Form 990 Parsing (2019-2023 Priority)
Phase 0 — MERIT Data Pipeline

Purpose: Download and parse Form 990 XML filings from the IRS AWS S3 bucket.
         Priority on 2019-2023 (most recent, most complete).

Data Source: s3://irs-form-990/
AWS Region: us-east-1
Public bucket — no credentials required

Output: Parsed financials in CSV + raw XML caching
Target: 200,000+ unique EINs with at least 1 year of financial data

Usage:
    python workstream_b_irs_s3.py --years 2019,2020,2021,2022,2023 --max-files 50000
"""

import argparse
import csv
import gzip
import json
import logging
import os
import shutil
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
import zipfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

# ─── CONFIGURATION ──────────────────────────────────────────────────────────
RAW_DIR = Path("/mnt/agents/output/meritgiving/data/raw/irs_990_xml")
CSV_DIR = Path("/mnt/agents/output/meritgiving/data/csv")
LOG_DIR = Path("/mnt/agents/output/meritgiving/data/logs")
CHECKPOINT_DIR = Path("/mnt/agents/output/meritgiving/data/raw/irs_990_xml/.checkpoint")

BUCKET_NAME = "irs-form-990"
AWS_REGION = "us-east-1"

# Quality gates
VALID_SUBSECTIONS = {"03"}
VALID_DEDUCTIBILITY = {"PC", "POF"}
SKIP_DEDUCTIBILITY = {"PF"}

# XML namespace used in IRS 990 filings
IRS_NS = {
    "efile": "http://www.irs.gov/efile",
    "irs": "http://www.irs.gov/efile",
    "": "http://www.irs.gov/efile"  # default namespace
}

# Priority years (most recent first)
DEFAULT_YEARS = [2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015]

# Logging setup
def setup_logging():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"workstream_b_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger("WorkstreamB")

logger = setup_logging()

# ─── S3 CLIENT ──────────────────────────────────────────────────────────────
def get_s3_client():
    """Create S3 client for public IRS bucket (no credentials needed)."""
    config = Config(
        retries={"max_attempts": 5, "mode": "adaptive"},
        max_pool_connections=25
    )
    return boto3.client(
        "s3",
        region_name=AWS_REGION,
        config=config,
        # No credentials — public bucket
    )


# ─── S3 LISTING ─────────────────────────────────────────────────────────────
def list_index_files(s3_client, prefix: str = "") -> List[str]:
    """List all index CSV files in the bucket."""
    index_files = []
    paginator = s3_client.get_paginator("list_objects_v2")
    
    for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith("_index.csv") or key.endswith("_index.csv.gz"):
                index_files.append(key)
    
    return sorted(index_files)


def download_index(s3_client, key: str, local_dir: Path) -> Path:
    """Download an index file from S3."""
    local_path = local_dir / Path(key).name
    
    if local_path.exists():
        logger.debug(f"Index already cached: {key}")
        return local_path
    
    local_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        s3_client.download_file(BUCKET_NAME, key, str(local_path))
        logger.info(f"Downloaded index: {key}")
        return local_path
    except ClientError as e:
        logger.error(f"Failed to download index {key}: {e}")
        return None


def parse_index_file(index_path: Path) -> List[Dict]:
    """Parse index CSV to get filing metadata."""
    records = []
    
    open_func = gzip.open if str(index_path).endswith(".gz") else open
    
    try:
        with open_func(index_path, "rt", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Filter for 501(c)(3) organizations
                subsection = row.get("SUBSECTION", "").strip()
                if subsection not in VALID_SUBSECTIONS:
                    continue
                
                # Filter for PC or POF (skip PF)
                deductibility = row.get("DEDUCTIBILITY", "").strip()
                if deductibility in SKIP_DEDUCTIBILITY:
                    continue
                
                records.append({
                    "ein": row.get("EIN", "").strip().zfill(9),
                    "tax_period": row.get("TAX_PERIOD", "").strip(),
                    "tax_year": row.get("TAX_YEAR", "").strip(),
                    "form_type": row.get("FORM_TYPE", "").strip(),
                    "subsection": subsection,
                    "deductibility": deductibility,
                    "organization_name": row.get("ORGANIZATION_NAME", "").strip(),
                    "return_timestamp": row.get("RETURN_TIMESTAMP", "").strip(),
                    "xml_key": row.get("OBJECT_ID", "").strip() + "_public.xml",
                    "object_id": row.get("OBJECT_ID", "").strip()
                })
    except Exception as e:
        logger.error(f"Error parsing index {index_path}: {e}")
    
    return records


# ─── XML DOWNLOAD & PARSING ─────────────────────────────────────────────────
def download_xml(s3_client, object_id: str, local_dir: Path) -> Optional[Path]:
    """Download a single XML filing from S3."""
    xml_key = f"{object_id}_public.xml"
    local_path = local_dir / xml_key
    
    if local_path.exists():
        return local_path
    
    try:
        s3_client.download_file(BUCKET_NAME, xml_key, str(local_path))
        return local_path
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            # Try alternative path
            alt_key = f"{object_id}_public.xml"
            try:
                s3_client.download_file(BUCKET_NAME, alt_key, str(local_path))
                return local_path
            except ClientError:
                pass
        logger.debug(f"XML not found: {xml_key}")
        return None


def safe_find_text(element, path: str, namespaces: Dict) -> Optional[str]:
    """Safely extract text from XML element."""
    try:
        found = element.find(path, namespaces)
        if found is not None and found.text:
            return found.text.strip()
        return None
    except Exception:
        return None


def parse_990_xml(xml_path: Path) -> Optional[Dict]:
    """
    Parse a Form 990 XML file and extract financial data.
    Returns dict with all financial fields.
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Determine which form type (990, 990EZ, 990PF)
        form_type = "990"
        if root.find(".//irs:ReturnTypeCd", IRS_NS) is not None:
            return_type = root.find(".//irs:ReturnTypeCd", IRS_NS)
            if return_type is not None and return_type.text:
                form_type = return_type.text
        
        # Helper to extract integer values (in cents)
        def extract_cents(xpath: str) -> Optional[int]:
            text = safe_find_text(root, xpath, IRS_NS)
            if text:
                try:
                    # Remove commas, dollar signs
                    clean = text.replace(",", "").replace("$", "").strip()
                    val = float(clean)
                    return int(round(val * 100))
                except (ValueError, TypeError):
                    return None
            return None
        
        # Common paths for different form versions
        financials = {
            "form_type": form_type,
            "revenue_cents": None,
            "expenses_cents": None,
            "assets_eoy_cents": None,
            "assets_boy_cents": None,
            "liabilities_eoy_cents": None,
            "liabilities_boy_cents": None,
            "net_assets_cents": None,
            "contributions_cents": None,
            "program_service_revenue_cents": None,
            "investment_income_cents": None,
            "fundraising_expenses_cents": None,
            "officer_compensation_cents": None,
            "other_salaries_cents": None,
            "grants_paid_cents": None,
            "total_employees": None,
            "total_volunteers": None,
        }
        
        # Form 990 (full)
        if form_type in ("990", "990O"):
            financials["revenue_cents"] = extract_cents(".//irs:CYTotalRevenueAmt") or extract_cents(".//irs:TotalRevenueCurrentYearAmt")
            financials["expenses_cents"] = extract_cents(".//irs:CYTotalExpensesAmt") or extract_cents(".//irs:TotalExpensesCurrentYearAmt")
            financials["assets_eoy_cents"] = extract_cents(".//irs:TotalAssetsEOYAmt") or extract_cents(".//irs:Form990TotalAssetsGrp/irs:EOYAmt")
            financials["assets_boy_cents"] = extract_cents(".//irs:TotalAssetsBOYAmt") or extract_cents(".//irs:Form990TotalAssetsGrp/irs:BOYAmt")
            financials["liabilities_eoy_cents"] = extract_cents(".//irs:TotalLiabilitiesEOYAmt") or extract_cents(".//irs:Form990TotalLiabilitiesGrp/irs:EOYAmt")
            financials["net_assets_cents"] = extract_cents(".//irs:NetAssetsOrFundBalancesEOYAmt") or extract_cents(".//irs:NetAssetsFundBalanceGrp/irs:EOYAmt")
            financials["contributions_cents"] = extract_cents(".//irs:CYContributionsGrantsAmt") or extract_cents(".//irs:ContributionsGrantsCurrentYearAmt")
            financials["program_service_revenue_cents"] = extract_cents(".//irs:CYProgramServiceRevenueAmt")
            financials["investment_income_cents"] = extract_cents(".//irs:CYInvestmentIncomeAmt")
            financials["fundraising_expenses_cents"] = extract_cents(".//irs:TotalFundraisingExpenseAmt") or extract_cents(".//irs:FundraisingAmt")
            financials["officer_compensation_cents"] = extract_cents(".//irs:CompCurrentOfcrDirectorsAmt") or extract_cents(".//irs:CompensationOfOfficersAmt")
            financials["other_salaries_cents"] = extract_cents(".//irs:OtherSalariesAndWagesAmt") or extract_cents(".//irs:SalariesWagesCurrentYearAmt")
            financials["grants_paid_cents"] = extract_cents(".//irs:CYGrantsAndSimilarPaidAmt") or extract_cents(".//irs:GrantsPaidCurrentYearAmt")
            
            # Employee/volunteer counts
            employees = safe_find_text(root, ".//irs:TotalEmployeeCnt", IRS_NS)
            if employees:
                try:
                    financials["total_employees"] = int(employees)
                except ValueError:
                    pass
            
            volunteers = safe_find_text(root, ".//irs:TotalVolunteersCnt", IRS_NS) or safe_find_text(root, ".//irs:TotalVolunteerCnt", IRS_NS)
            if volunteers:
                try:
                    financials["total_volunteers"] = int(volunteers)
                except ValueError:
                    pass
        
        # Form 990-EZ
        elif form_type == "990EZ":
            financials["revenue_cents"] = extract_cents(".//irs:TotalRevenueAmt") or extract_cents(".//irs:TotalRevenue")
            financials["expenses_cents"] = extract_cents(".//irs:TotalExpensesAmt") or extract_cents(".//irs:TotalExpenses")
            financials["assets_eoy_cents"] = extract_cents(".//irs:Form990TotalAssetsGrp/irs:EOYAmt") or extract_cents(".//irs:TotalAssetsEOY")
            financials["net_assets_cents"] = extract_cents(".//irs:NetAssetsOrFundBalancesEOYAmt") or extract_cents(".//irs:NetAssetsEOY")
            financials["contributions_cents"] = extract_cents(".//irs:ContributionsGiftsGrantsAmt") or extract_cents(".//irs:ContributionsGiftsGrants")
            financials["program_service_revenue_cents"] = extract_cents(".//irs:ProgramServiceRevenueAmt")
            financials["investment_income_cents"] = extract_cents(".//irs:InvestmentIncomeAmt")
            financials["officer_compensation_cents"] = extract_cents(".//irs:OfficerDirectorTrusteeCompensationAmt")
            financials["other_salaries_cents"] = extract_cents(".//irs:OtherSalariesWagesAmt")
            financials["grants_paid_cents"] = extract_cents(".//irs:GrantsAndSimilarAmountsPaidAmt")
        
        # Form 990-PF (Private Foundation) — skip if non-operating
        elif form_type == "990PF":
            # Check if it's an operating foundation
            op_fd_check = safe_find_text(root, ".//irs:OperatingFoundationStatusTxt", IRS_NS)
            if op_fd_check and "non-operating" in op_fd_check.lower():
                return None  # Skip non-operating private foundations
            
            financials["revenue_cents"] = extract_cents(".//irs:TotalRevAndExpnssAmt")
            financials["expenses_cents"] = extract_cents(".//irs:TtlOprExpnssPaidAmt") or extract_cents(".//irs:TotalOperatingExpensesPaidAmt")
            financials["assets_eoy_cents"] = extract_cents(".//irs:TotalAssetsEOYAmt")
            financials["net_assets_cents"] = extract_cents(".//irs:NetAssetsEOYAmt")
            financials["contributions_cents"] = extract_cents(".//irs:ContrRcvdRevAndExpnssAmt")
            financials["investment_income_cents"] = extract_cents(".//irs:NetInvstIncmAmt")
            financials["grants_paid_cents"] = extract_cents(".//irs:TtlCharitblCtntnPdAmt") or extract_cents(".//irs:TotalCharitableContributionsPaidAmt")
            financials["officer_compensation_cents"] = extract_cents(".//irs:CompOfcrDirTrstAmt")
        
        return financials
    
    except ET.ParseError as e:
        logger.debug(f"XML parse error in {xml_path}: {e}")
        return None
    except Exception as e:
        logger.debug(f"Error parsing {xml_path}: {e}")
        return None


# ─── CSV WRITER ─────────────────────────────────────────────────────────────
class IRS_CSVWriter:
    def __init__(self):
        self.financial_file = CSV_DIR / "financials_annual_irs_s3.csv"
        self.org_file = CSV_DIR / "master_orgs_irs_s3.csv"
        self.fin_fh = None
        self.org_fh = None
        self.fin_writer = None
        self.org_writer = None
        self.fin_count = 0
        self.org_count = 0
        self._seen_eins = set()
    
    def open(self):
        CSV_DIR.mkdir(parents=True, exist_ok=True)
        
        fin_exists = self.financial_file.exists()
        self.fin_fh = open(self.financial_file, "a", newline="", encoding="utf-8")
        self.fin_writer = csv.DictWriter(
            self.fin_fh,
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
        if not fin_exists:
            self.fin_writer.writeheader()
        
        org_exists = self.org_file.exists()
        self.org_fh = open(self.org_file, "a", newline="", encoding="utf-8")
        self.org_writer = csv.DictWriter(
            self.org_fh,
            fieldnames=[
                "ein", "name", "subsection", "deductibility",
                "organization_type", "source_provenance", "raw_extracted_at"
            ]
        )
        if not org_exists:
            self.org_writer.writeheader()
    
    def write_filing(self, record: Dict, financials: Dict):
        # Write organization record (deduplicated)
        if record["ein"] not in self._seen_eins:
            self.org_writer.writerow({
                "ein": record["ein"],
                "name": record["organization_name"],
                "subsection": record["subsection"],
                "deductibility": record["deductibility"],
                "organization_type": "PC" if record["deductibility"] == "PC" else "POF",
                "source_provenance": "IRS_S3",
                "raw_extracted_at": datetime.now().isoformat()
            })
            self._seen_eins.add(record["ein"])
            self.org_count += 1
        
        # Write financial record
        tax_year = record.get("tax_year", "")
        if not tax_year and record.get("tax_period"):
            tax_year = record["tax_period"][:4]
        
        row = {
            "ein": record["ein"],
            "tax_year": tax_year,
            "tax_period": record.get("tax_period", ""),
            "form_type": financials.get("form_type", record.get("form_type", "")),
            "revenue_cents": financials.get("revenue_cents"),
            "expenses_cents": financials.get("expenses_cents"),
            "assets_eoy_cents": financials.get("assets_eoy_cents"),
            "assets_boy_cents": financials.get("assets_boy_cents"),
            "liabilities_eoy_cents": financials.get("liabilities_eoy_cents"),
            "liabilities_boy_cents": financials.get("liabilities_boy_cents"),
            "net_assets_cents": financials.get("net_assets_cents"),
            "contributions_cents": financials.get("contributions_cents"),
            "program_service_revenue_cents": financials.get("program_service_revenue_cents"),
            "investment_income_cents": financials.get("investment_income_cents"),
            "fundraising_expenses_cents": financials.get("fundraising_expenses_cents"),
            "officer_compensation_cents": financials.get("officer_compensation_cents"),
            "other_salaries_cents": financials.get("other_salaries_cents"),
            "grants_paid_cents": financials.get("grants_paid_cents"),
            "total_employees": financials.get("total_employees"),
            "total_volunteers": financials.get("total_volunteers"),
            "object_id": record.get("object_id", ""),
            "source_provenance": "IRS_S3",
            "extracted_at": datetime.now().isoformat()
        }
        
        self.fin_writer.writerow(row)
        self.fin_count += 1
        
        if self.fin_count % 1000 == 0:
            self.fin_fh.flush()
    
    def close(self):
        if self.fin_fh:
            self.fin_fh.close()
        if self.org_fh:
            self.org_fh.close()


# ─── CHECKPOINT ───────────────────────────────────────────────────────────────
class IRS_Checkpoint:
    def __init__(self):
        CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
        self.file = CHECKPOINT_DIR / "processed_object_ids.json"
        self.processed: Set[str] = set()
        self.load()
    
    def load(self):
        if self.file.exists():
            try:
                with open(self.file, "r") as f:
                    data = json.load(f)
                    self.processed = set(data.get("processed", []))
                logger.info(f"Loaded checkpoint: {len(self.processed)} processed object IDs")
            except Exception as e:
                logger.warning(f"Could not load checkpoint: {e}")
    
    def save(self):
        data = {
            "processed": sorted(list(self.processed)),
            "last_updated": datetime.now().isoformat()
        }
        tmp = self.file.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(data, f)
        tmp.replace(self.file)
    
    def is_processed(self, object_id: str) -> bool:
        return object_id in self.processed
    
    def mark_processed(self, object_id: str):
        self.processed.add(object_id)
        if len(self.processed) % 1000 == 0:
            self.save()


# ─── MAIN PROCESSING LOOP ───────────────────────────────────────────────────
def process_filings_for_year(year: int, max_files: Optional[int] = None, checkpoint: IRS_Checkpoint = None):
    """Process all filings for a given tax year."""
    s3_client = get_s3_client()
    
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    year_dir = RAW_DIR / str(year)
    year_dir.mkdir(exist_ok=True)
    
    # Download index for the year
    # IRS S3 structure: index_YYYY.csv or index_YYYY.csv.gz
    index_key = f"index_{year}.csv.gz"
    index_local = year_dir / f"index_{year}.csv.gz"
    
    if not index_local.exists():
        try:
            s3_client.download_file(BUCKET_NAME, index_key, str(index_local))
            logger.info(f"Downloaded index for {year}")
        except ClientError as e:
            # Try non-gzipped version
            index_key = f"index_{year}.csv"
            try:
                s3_client.download_file(BUCKET_NAME, index_key, str(index_local)[:-3])
            except ClientError:
                logger.error(f"Could not download index for {year}: {e}")
                return
    
    # Parse index
    records = parse_index_file(index_local)
    logger.info(f"Year {year}: {len(records)} 501(c)(3) PC/POF filings found")
    
    if max_files:
        records = records[:max_files]
    
    # Process filings
    csv_writer = IRS_CSVWriter()
    csv_writer.open()
    
    processed = 0
    failed = 0
    skipped = 0
    start_time = time.time()
    
    try:
        for i, record in enumerate(records):
            object_id = record["object_id"]
            
            if checkpoint and checkpoint.is_processed(object_id):
                skipped += 1
                continue
            
            # Download XML
            xml_path = download_xml(s3_client, object_id, year_dir)
            if not xml_path:
                failed += 1
                if checkpoint:
                    checkpoint.mark_processed(object_id)
                continue
            
            # Parse XML
            financials = parse_990_xml(xml_path)
            if not financials:
                failed += 1
                if checkpoint:
                    checkpoint.mark_processed(object_id)
                continue
            
            # Write to CSV
            csv_writer.write_filing(record, financials)
            processed += 1
            
            if checkpoint:
                checkpoint.mark_processed(object_id)
            
            # Progress
            if (i + 1) % 1000 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                logger.info(
                    f"Year {year} | {i+1}/{len(records)} | "
                    f"Processed: {processed} | Failed: {failed} | Skipped: {skipped} | "
                    f"Rate: {rate:.1f} files/sec | Orgs: {csv_writer.org_count} | Financials: {csv_writer.fin_count}"
                )
                checkpoint.save() if checkpoint else None
        
    except KeyboardInterrupt:
        logger.info("Interrupted, saving checkpoint...")
    finally:
        csv_writer.close()
        if checkpoint:
            checkpoint.save()
        
        elapsed = time.time() - start_time
        logger.info("=" * 60)
        logger.info(f"Year {year} Complete")
        logger.info(f"Processed: {processed} | Failed: {failed} | Skipped: {skipped}")
        logger.info(f"Orgs: {csv_writer.org_count} | Financials: {csv_writer.fin_count}")
        logger.info(f"Time: {elapsed/3600:.2f}h | Rate: {len(records)/elapsed:.1f} files/sec")
        logger.info("=" * 60)


# ─── CLI ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Workstream B: IRS AWS S3 Form 990 XML Parsing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process 2019-2023 (priority years)
  python workstream_b_irs_s3.py --years 2019,2020,2021,2022,2023
  
  # Process all available years
  python workstream_b_irs_s3.py --years all
  
  # Process single year with limit
  python workstream_b_irs_s3.py --years 2023 --max-files 10000
  
  # Resume from checkpoint
  python workstream_b_irs_s3.py --years 2023 --resume
        """
    )
    parser.add_argument(
        "--years",
        type=str,
        default="2019,2020,2021,2022,2023",
        help="Comma-separated years or 'all'"
    )
    parser.add_argument("--max-files", type=int, default=None, help="Max files per year")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    
    args = parser.parse_args()
    
    # Parse years
    if args.years.lower() == "all":
        years = DEFAULT_YEARS
    else:
        years = [int(y.strip()) for y in args.years.split(",")]
    
    logger.info("=" * 60)
    logger.info("Workstream B: IRS AWS S3 XML Parsing")
    logger.info(f"Years: {years}")
    logger.info(f"Max files/year: {args.max_files or 'unlimited'}")
    logger.info("=" * 60)
    
    checkpoint = IRS_Checkpoint() if args.resume else IRS_Checkpoint()
    
    for year in years:
        logger.info(f"\n--- Processing year {year} ---")
        process_filings_for_year(year, args.max_files, checkpoint)


if __name__ == "__main__":
    main()
