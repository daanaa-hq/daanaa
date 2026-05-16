#!/usr/bin/env python3
"""
Workstream C: IRS Business Master File (BMF) & Publication 78 Verification
Phase 0 — MERIT Data Pipeline

Purpose: 
  1. Download and parse the IRS EO BMF (Business Master File)
  2. Download and parse IRS Publication 78 (deductibility list)
  3. Download IRS Auto-Revocation List
  4. Cross-reference all EINs against revocation status
  5. Build reference tables for subsection/deductibility verification

Sources:
  - IRS BMF: https://www.irs.gov/charities-non-profits/exempt-organizations-business-master-file-extract-eo-bmf
  - Publication 78: https://apps.irs.gov/app/eos/forwardToPub78Download.do
  - Auto-Revocation: https://apps.irs.gov/app/eos/forwardToRevocationDownload.do

Output: 
  - master_orgs_bmf.csv (enrichment data)
  - auto_revocation_flags.csv (revocation status per EIN)
  - ntee_taxonomy.csv (reference table)

Usage:
    python workstream_c_irs_bmf.py --download --parse
"""

import argparse
import csv
import gzip
import hashlib
import json
import logging
import os
import re
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ─── CONFIGURATION ──────────────────────────────────────────────────────────
RAW_DIR = Path("/mnt/agents/output/meritgiving/data/raw/irs_bmf")
CSV_DIR = Path("/mnt/agents/output/meritgiving/data/csv")
LOG_DIR = Path("/mnt/agents/output/meritgiving/data/logs")

# IRS Data URLs
BMF_URLS = {
    "eo1": "https://www.irs.gov/pub/irs-soi/eo1.csv",
    "eo2": "https://www.irs.gov/pub/irs-soi/eo2.csv",
    "eo3": "https://www.irs.gov/pub/irs-soi/eo3.csv",
    "eo4": "https://www.irs.gov/pub/irs-soi/eo4.csv",
}

PUB78_URL = "https://apps.irs.gov/pub/epostcard/ooP78M.txt"
REVOCATION_URL = "https://apps.irs.gov/pub/epostcard/auto-revocation.txt"

# Quality gates
VALID_SUBSECTIONS = {"03"}
VALID_DEDUCTIBILITY = {"PC", "POF"}
SKIP_DEDUCTIBILITY = {"PF"}

# Setup directories
for d in [RAW_DIR, CSV_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ─── LOGGING ────────────────────────────────────────────────────────────────
def setup_logging():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"workstream_c_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger("WorkstreamC")

logger = setup_logging()

# ─── HTTP SESSION ───────────────────────────────────────────────────────────
def create_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry, pool_connections=5, pool_maxsize=10)
    session.mount("https://", adapter)
    session.headers.update({
        "User-Agent": "MERIT-DataPipeline/0.1 (contact@meritgiving.org)"
    })
    return session


# ─── EIN VALIDATION ─────────────────────────────────────────────────────────
def normalize_ein(ein: str) -> Optional[str]:
    if not ein:
        return None
    cleaned = re.sub(r"[^0-9]", "", str(ein))
    if len(cleaned) != 9:
        return None
    return cleaned


# ─── BMF DOWNLOADER ─────────────────────────────────────────────────────────
def download_file(session: requests.Session, url: str, local_path: Path, chunk_size: int = 8192) -> bool:
    """Download a file with progress tracking."""
    if local_path.exists():
        logger.info(f"Already downloaded: {local_path.name}")
        return True
    
    logger.info(f"Downloading: {url}")
    try:
        response = session.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0
        
        with open(local_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0 and downloaded % (1024 * 1024) == 0:
                        pct = 100 * downloaded / total_size
                        logger.info(f"  {local_path.name}: {pct:.1f}% ({downloaded//1024//1024}MB / {total_size//1024//1024}MB)")
        
        logger.info(f"Downloaded: {local_path.name} ({downloaded//1024//1024}MB)")
        return True
    
    except Exception as e:
        logger.error(f"Download failed for {url}: {e}")
        if local_path.exists():
            local_path.unlink()
        return False


# ─── BMF PARSER ─────────────────────────────────────────────────────────────
def parse_bmf_file(filepath: Path) -> List[Dict]:
    """
    Parse IRS EO BMF CSV file.
    Returns list of organization records.
    
    BMF Columns (standard IRS format):
    EIN, NAME, ICO, STREET, CITY, STATE, ZIP, GROUP, SUBSECTION, 
    AFFILIATION, CLASSIFICATION, RULING, DEDUCTIBILITY, FOUNDATION,
    ACTIVITY, ORGANIZATION, STATUS, TAX_PERIOD, ASSET_CD, INCOME_CD,
    FILING_REQ_CD, PF_FILING_REQ_CD, ACCT_PD, ASSET_AMT, INCOME_AMT,
    REVENUE_AMT, NTEE_CD, SORT_NAME
    """
    records = []
    
    try:
        open_func = gzip.open if str(filepath).endswith(".gz") else open
        
        with open_func(filepath, "rt", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                ein = normalize_ein(row.get("EIN", ""))
                if not ein:
                    continue
                
                subsection = str(row.get("SUBSECTION", "")).strip()
                if subsection not in VALID_SUBSECTIONS:
                    continue
                
                deductibility = str(row.get("DEDUCTIBILITY", "")).strip()
                if deductibility in SKIP_DEDUCTIBILITY:
                    continue
                
                # Parse asset/income/revenue codes and amounts
                def parse_int(val):
                    if not val:
                        return None
                    try:
                        return int(str(val).replace(",", "").replace("$", "").strip())
                    except (ValueError, TypeError):
                        return None
                
                # Map asset/income/revenue codes to ranges (in cents)
                def code_to_cents(code_val, amount_val):
                    amount = parse_int(amount_val)
                    if amount is not None:
                        return amount * 100  # Convert to cents
                    # Use code ranges if amount not available
                    code_map = {
                        "1": 0, "2": 500_000, "3": 2_500_000,
                        "4": 10_000_000, "5": 50_000_000, "6": 100_000_000,
                        "7": 500_000_000, "8": 1_000_000_000, "9": 5_000_000_000
                    }
                    code = str(code_val).strip() if code_val else ""
                    return code_map.get(code, None)
                
                records.append({
                    "ein": ein,
                    "name": row.get("NAME", "").strip(),
                    "careof_name": row.get("ICO", "").strip(),
                    "street": row.get("STREET", "").strip(),
                    "city": row.get("CITY", "").strip(),
                    "state": row.get("STATE", "").strip(),
                    "zip": row.get("ZIP", "").strip(),
                    "group_exemption": row.get("GROUP", "").strip(),
                    "subsection": subsection,
                    "affiliation_code": row.get("AFFILIATION", "").strip(),
                    "classification_codes": row.get("CLASSIFICATION", "").strip(),
                    "ruling_date": row.get("RULING", "").strip(),
                    "deductibility_code": deductibility,
                    "foundation_code": row.get("FOUNDATION", "").strip(),
                    "activity_codes": row.get("ACTIVITY", "").strip(),
                    "organization_code": row.get("ORGANIZATION", "").strip(),
                    "exempt_status_code": row.get("STATUS", "").strip(),
                    "tax_period": row.get("TAX_PERIOD", "").strip(),
                    "asset_code": row.get("ASSET_CD", "").strip(),
                    "income_code": row.get("INCOME_CD", "").strip(),
                    "filing_requirement_code": row.get("FILING_REQ_CD", "").strip(),
                    "pf_filing_requirement": row.get("PF_FILING_REQ_CD", "").strip(),
                    "accounting_period": row.get("ACCT_PD", "").strip(),
                    "asset_amt_cents": code_to_cents(row.get("ASSET_CD"), row.get("ASSET_AMT")),
                    "income_amt_cents": code_to_cents(row.get("INCOME_CD"), row.get("INCOME_AMT")),
                    "revenue_amt_cents": code_to_cents(row.get("INCOME_CD"), row.get("REVENUE_AMT")),
                    "ntee_code": row.get("NTEE_CD", "").strip(),
                    "sort_name": row.get("SORT_NAME", "").strip(),
                    "organization_type": "PC" if deductibility == "PC" else "POF",
                    "source_provenance": "IRS_BMF",
                    "raw_extracted_at": datetime.now().isoformat()
                })
    
    except Exception as e:
        logger.error(f"Error parsing BMF file {filepath}: {e}")
    
    return records


# ─── PUBLICATION 78 PARSER ──────────────────────────────────────────────────
def download_and_parse_pub78(session: requests.Session) -> Dict[str, Dict]:
    """
    Download and parse Publication 78 (deductibility database).
    Returns dict mapping EIN -> deductibility info.
    """
    local_path = RAW_DIR / "pub78.txt"
    
    if not local_path.exists():
        if not download_file(session, PUB78_URL, local_path):
            return {}
    
    logger.info("Parsing Publication 78...")
    pub78_data = {}
    
    try:
        with open(local_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("EIN"):
                    continue
                
                parts = line.split("|")
                if len(parts) < 4:
                    continue
                
                ein = normalize_ein(parts[0])
                if not ein:
                    continue
                
                name = parts[1].strip() if len(parts) > 1 else ""
                city = parts[2].strip() if len(parts) > 2 else ""
                state = parts[3].strip() if len(parts) > 3 else ""
                deductibility = parts[4].strip() if len(parts) > 4 else ""
                subsection = parts[5].strip() if len(parts) > 5 else ""
                
                if subsection not in VALID_SUBSECTIONS:
                    continue
                if deductibility in SKIP_DEDUCTIBILITY:
                    continue
                
                pub78_data[ein] = {
                    "ein": ein,
                    "name": name,
                    "city": city,
                    "state": state,
                    "deductibility_code": deductibility,
                    "subsection": subsection,
                    "source_provenance": "IRS_BMF",
                    "list_type": "Publication78"
                }
        
        logger.info(f"Publication 78 parsed: {len(pub78_data)} records")
    
    except Exception as e:
        logger.error(f"Error parsing Publication 78: {e}")
    
    return pub78_data


# ─── REVOCATION LIST PARSER ─────────────────────────────────────────────────
def download_and_parse_revocation(session: requests.Session) -> Dict[str, Dict]:
    """
    Download and parse IRS Auto-Revocation List.
    Returns dict mapping EIN -> revocation details.
    
    Quality Gate 4: Cross-check against IRS Auto-Revocation List.
    """
    local_path = RAW_DIR / "auto_revocation.txt"
    
    if not local_path.exists():
        if not download_file(session, REVOCATION_URL, local_path):
            return {}
    
    logger.info("Parsing Auto-Revocation List...")
    revocation_data = {}
    
    try:
        with open(local_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("EIN"):
                    continue
                
                parts = line.split("|")
                if len(parts) < 6:
                    continue
                
                ein = normalize_ein(parts[0])
                if not ein:
                    continue
                
                name = parts[1].strip() if len(parts) > 1 else ""
                state = parts[2].strip() if len(parts) > 2 else ""
                city = parts[3].strip() if len(parts) > 3 else ""
                zipcode = parts[4].strip() if len(parts) > 4 else ""
                revocation_date = parts[5].strip() if len(parts) > 5 else ""
                subsection = parts[6].strip() if len(parts) > 6 else ""
                
                if subsection and subsection not in VALID_SUBSECTIONS:
                    continue
                
                revocation_data[ein] = {
                    "ein": ein,
                    "name": name,
                    "state": state,
                    "city": city,
                    "zipcode": zipcode,
                    "revocation_date": revocation_date,
                    "subsection": subsection,
                    "is_revoked": True,
                    "revocation_source": "IRS_Auto_Revocation",
                    "source_provenance": "IRS_BMF",
                    "extracted_at": datetime.now().isoformat()
                }
        
        logger.info(f"Revocation list parsed: {len(revocation_data)} revoked organizations")
    
    except Exception as e:
        logger.error(f"Error parsing revocation list: {e}")
    
    return revocation_data


# ─── NTEE TAXONOMY BUILDER ──────────────────────────────────────────────────
def build_ntee_taxonomy() -> List[Dict]:
    """
    Build NTEE taxonomy reference table.
    Source: NTEE Classification System (National Taxonomy of Exempt Entities)
    """
    # Major NTEE groups (letter codes)
    ntee_major_groups = [
        {"code": "A", "name": "Arts, Culture & Humanities", "description": "Museums, performing arts, humanities organizations"},
        {"code": "B", "name": "Education", "description": "K-12 schools, universities, educational services"},
        {"code": "C", "name": "Environment", "description": "Environmental protection, beautification"},
        {"code": "D", "name": "Animal-Related", "description": "Animal protection, wildlife preservation"},
        {"code": "E", "name": "Health Care", "description": "Hospitals, clinics, health services"},
        {"code": "F", "name": "Mental Health & Crisis Intervention", "description": "Mental health services, crisis hotlines"},
        {"code": "G", "name": "Voluntary Health Associations", "description": "Disease-specific organizations, medical research"},
        {"code": "H", "name": "Medical Research", "description": "Medical research organizations"},
        {"code": "I", "name": "Crime & Legal-Related", "description": "Legal aid, crime prevention, rehabilitation"},
        {"code": "J", "name": "Employment", "description": "Job training, vocational rehabilitation"},
        {"code": "K", "name": "Food, Agriculture & Nutrition", "description": "Food banks, agricultural programs"},
        {"code": "L", "name": "Housing & Shelter", "description": "Affordable housing, homeless shelters"},
        {"code": "M", "name": "Public Safety & Disaster Preparedness", "description": "Fire prevention, disaster relief"},
        {"code": "N", "name": "Recreation & Sports", "description": "Community centers, sports leagues"},
        {"code": "O", "name": "Youth Development", "description": "Youth organizations, scouting, mentoring"},
        {"code": "P", "name": "Human Services", "description": "Social services, family support"},
        {"code": "Q", "name": "International & Foreign Affairs", "description": "International development, exchange programs"},
        {"code": "R", "name": "Civil Rights & Advocacy", "description": "Civil liberties, advocacy organizations"},
        {"code": "S", "name": "Community Improvement", "description": "Community foundations, neighborhood associations"},
        {"code": "T", "name": "Philanthropy & Voluntarism", "description": "Foundations, grantmaking organizations"},
        {"code": "U", "name": "Science & Technology", "description": "Scientific research, technology programs"},
        {"code": "V", "name": "Social Science", "description": "Social science research organizations"},
        {"code": "W", "name": "Public & Societal Benefit", "description": "Public policy, leadership development"},
        {"code": "X", "name": "Religion-Related", "description": "Religious organizations, interfaith groups"},
        {"code": "Y", "name": "Mutual & Membership Benefit", "description": "Civic associations, credit unions"},
        {"code": "Z", "name": "Unknown/Unclassified", "description": "Organizations not yet classified"},
    ]
    
    # Common NTEE subcategories (major common ones)
    ntee_subcategories = [
        # Education
        {"code": "B21", "parent_code": "B", "name": "Kindergarten/Preschool", "description": "Early childhood education"},
        {"code": "B25", "parent_code": "B", "name": "Elementary/Secondary Schools", "description": "K-12 private schools"},
        {"code": "B28", "parent_code": "B", "name": "Special Education", "description": "Schools for students with disabilities"},
        {"code": "B40", "parent_code": "B", "name": "Higher Education", "description": "Colleges, universities"},
        {"code": "B60", "parent_code": "B", "name": "Adult Education", "description": "Continuing education, literacy"},
        {"code": "B80", "parent_code": "B", "name": "Student Services", "description": "Scholarships, student organizations"},
        {"code": "B90", "parent_code": "B", "name": "Educational Services", "description": "Libraries, educational resources"},
        # Health
        {"code": "E21", "parent_code": "E", "name": "Community Health Centers", "description": "Primary care clinics"},
        {"code": "E24", "parent_code": "E", "name": "Hospitals", "description": "General and specialty hospitals"},
        {"code": "E30", "parent_code": "E", "name": "Health Treatment Facilities", "description": "Treatment centers, hospices"},
        {"code": "E32", "parent_code": "E", "name": "Ambulance & Emergency Medical", "description": "EMS services"},
        {"code": "E50", "parent_code": "E", "name": "Rehabilitative Medical Services", "description": "Physical therapy, rehabilitation"},
        {"code": "E60", "parent_code": "E", "name": "Health Support Services", "description": "Health education, advocacy"},
        {"code": "E70", "parent_code": "E", "name": "Public Health Programs", "description": "Public health initiatives"},
        {"code": "E80", "parent_code": "E", "name": "Health Insurance Providers", "description": "Health insurance organizations"},
        {"code": "E86", "parent_code": "E", "name": "Patient & Family Support", "description": "Patient support services"},
        {"code": "E90", "parent_code": "E", "name": "Nursing Facilities", "description": "Nursing homes, assisted living"},
        # Human Services
        {"code": "P20", "parent_code": "P", "name": "Human Service Organizations", "description": "Multi-service agencies"},
        {"code": "P30", "parent_code": "P", "name": "Children & Youth Services", "description": "Child welfare, foster care"},
        {"code": "P32", "parent_code": "P", "name": "Foster Care", "description": "Foster care programs"},
        {"code": "P40", "parent_code": "P", "name": "Family Services", "description": "Family counseling, support"},
        {"code": "P42", "parent_code": "P", "name": "Single Parent Agencies", "description": "Services for single parents"},
        {"code": "P43", "parent_code": "P", "name": "Family Violence Shelters", "description": "Domestic violence shelters"},
        {"code": "P44", "parent_code": "P", "name": "Runaway & Homeless Youth", "description": "Youth shelters"},
        {"code": "P46", "parent_code": "P", "name": "Emergency Assistance", "description": "Crisis assistance programs"},
        {"code": "P50", "parent_code": "P", "name": "Personal Social Services", "description": "Day care, transportation"},
        {"code": "P51", "parent_code": "P", "name": "Financial Counseling", "description": "Credit counseling, financial literacy"},
        {"code": "P52", "parent_code": "P", "name": "Transportation Assistance", "description": "Medical transport, paratransit"},
        {"code": "P58", "parent_code": "P", "name": "Gift Distribution", "description": "Holiday gift programs"},
        {"code": "P60", "parent_code": "P", "name": "Emergency Assistance (Food, Clothing, Cash)", "description": "Emergency financial aid"},
        {"code": "P70", "parent_code": "P", "name": "Residential Care & Adult Day Programs", "description": "Group homes, adult day care"},
        {"code": "P73", "parent_code": "P", "name": "Group Homes", "description": "Residential group homes"},
        {"code": "P80", "parent_code": "P", "name": "Centers to Support Independent Living", "description": "Independent living centers"},
        {"code": "P81", "parent_code": "P", "name": "Senior Centers", "description": "Senior services programs"},
        {"code": "P84", "parent_code": "P", "name": "Ethnic & Immigrant Centers", "description": "Immigrant services"},
        {"code": "P85", "parent_code": "P", "name": "Homeless Centers", "description": "Homeless services"},
        {"code": "P86", "parent_code": "P", "name": "Developmentally Disabled Centers", "description": "DD services"},
        {"code": "P87", "parent_code": "P", "name": "Deaf & Hearing Impaired Centers", "description": "Services for deaf/hard of hearing"},
        {"code": "P88", "parent_code": "P", "name": "Blind & Visually Impaired Centers", "description": "Services for blind/visually impaired"},
        {"code": "P99", "parent_code": "P", "name": "Human Services (Not Elsewhere Classified)", "description": "Other human services"},
        # Community Improvement
        {"code": "S20", "parent_code": "S", "name": "Community & Neighborhood Development", "description": "Community development"},
        {"code": "S21", "parent_code": "S", "name": "Community Coalitions", "description": "Community partnerships"},
        {"code": "S22", "parent_code": "S", "name": "Neighborhood Associations", "description": "Neighborhood groups"},
        {"code": "S30", "parent_code": "S", "name": "Economic Development", "description": "Business development"},
        {"code": "S31", "parent_code": "S", "name": "Urban & Community Economic Development", "description": "Urban development"},
        {"code": "S32", "parent_code": "S", "name": "Rural Development", "description": "Rural economic development"},
        {"code": "S40", "parent_code": "S", "name": "Business & Industry Promotion", "description": "Chambers of commerce"},
        {"code": "S41", "parent_code": "S", "name": "Promotion of Business", "description": "Business promotion"},
        {"code": "S43", "parent_code": "S", "name": "Small Business Development", "description": "Small business support"},
        {"code": "S50", "parent_code": "S", "name": "Nonprofit Management", "description": "Nonprofit support organizations"},
        {"code": "S80", "parent_code": "S", "name": "Community Service Clubs", "description": "Service clubs"},
        {"code": "S81", "parent_code": "S", "name": "Women's Service Clubs", "description": "Women's service organizations"},
        {"code": "S82", "parent_code": "S", "name": "Men's Service Clubs", "description": "Men's service organizations"},
        # Philanthropy
        {"code": "T20", "parent_code": "T", "name": "Private Grantmaking Foundations", "description": "Private foundations"},
        {"code": "T21", "parent_code": "T", "name": "Corporate Foundations", "description": "Corporate giving programs"},
        {"code": "T22", "parent_code": "T", "name": "Community Foundations", "description": "Community foundations"},
        {"code": "T30", "parent_code": "T", "name": "Public Foundations", "description": "Public charities"},
        {"code": "T31", "parent_code": "T", "name": "Community Foundations", "description": "Community foundations"},
        {"code": "T40", "parent_code": "T", "name": "Voluntarism Promotion", "description": "Volunteer coordination"},
        {"code": "T50", "parent_code": "T", "name": "Philanthropy & Charity Organizations", "description": "Philanthropic organizations"},
        {"code": "T70", "parent_code": "T", "name": "Fund Raising & Fund Distribution", "description": "Fundraising organizations"},
        {"code": "T90", "parent_code": "T", "name": "Charitable Trusts", "description": "Charitable trusts"},
        {"code": "T99", "parent_code": "T", "name": "Philanthropy (Not Elsewhere Classified)", "description": "Other philanthropic activities"},
    ]
    
    # Combine into flat reference table
    all_records = []
    
    for group in ntee_major_groups:
        all_records.append({
            "ntee_code": group["code"],
            "ntee_parent": None,
            "ntee_level": 1,
            "ntee_name": group["name"],
            "ntee_description": group["description"],
            "source": "IRS_NTEE_Major_Group"
        })
    
    for sub in ntee_subcategories:
        all_records.append({
            "ntee_code": sub["code"],
            "ntee_parent": sub["parent_code"],
            "ntee_level": 2,
            "ntee_name": sub["name"],
            "ntee_description": sub["description"],
            "source": "IRS_NTEE_Subcategory"
        })
    
    return all_records


# ─── CSV OUTPUT WRITERS ─────────────────────────────────────────────────────
class BMF_CSVWriter:
    def __init__(self):
        self.bmf_org_file = CSV_DIR / "master_orgs_bmf.csv"
        self.revocation_file = CSV_DIR / "auto_revocation_flags.csv"
        self.ntee_file = CSV_DIR / "ntee_taxonomy.csv"
        self.bmf_fh = None
        self.rev_fh = None
        self.ntee_fh = None
    
    def open(self):
        CSV_DIR.mkdir(parents=True, exist_ok=True)
        
        # BMF organizations
        bmf_exists = self.bmf_org_file.exists()
        self.bmf_fh = open(self.bmf_org_file, "a", newline="", encoding="utf-8")
        self.bmf_writer = csv.DictWriter(
            self.bmf_fh,
            fieldnames=[
                "ein", "name", "careof_name", "street", "city", "state", "zip",
                "group_exemption", "subsection", "affiliation_code", "classification_codes",
                "ruling_date", "deductibility_code", "foundation_code", "activity_codes",
                "organization_code", "exempt_status_code", "tax_period",
                "asset_code", "income_code", "filing_requirement_code", "pf_filing_requirement",
                "accounting_period", "asset_amt_cents", "income_amt_cents", "revenue_amt_cents",
                "ntee_code", "sort_name", "organization_type",
                "source_provenance", "raw_extracted_at"
            ]
        )
        if not bmf_exists:
            self.bmf_writer.writeheader()
        
        # Revocation flags
        rev_exists = self.revocation_file.exists()
        self.rev_fh = open(self.revocation_file, "a", newline="", encoding="utf-8")
        self.rev_writer = csv.DictWriter(
            self.rev_fh,
            fieldnames=[
                "ein", "name", "state", "city", "zipcode",
                "revocation_date", "subsection", "is_revoked",
                "revocation_source", "source_provenance", "extracted_at"
            ]
        )
        if not rev_exists:
            self.rev_writer.writeheader()
        
        # NTEE taxonomy
        ntee_exists = self.ntee_file.exists()
        self.ntee_fh = open(self.ntee_file, "a", newline="", encoding="utf-8")
        self.ntee_writer = csv.DictWriter(
            self.ntee_fh,
            fieldnames=[
                "ntee_code", "ntee_parent", "ntee_level",
                "ntee_name", "ntee_description", "source"
            ]
        )
        if not ntee_exists:
            self.ntee_writer.writeheader()
    
    def write_bmf_org(self, record: Dict):
        self.bmf_writer.writerow(record)
    
    def write_revocation(self, record: Dict):
        self.rev_writer.writerow(record)
    
    def write_ntee(self, records: List[Dict]):
        for r in records:
            self.ntee_writer.writerow(r)
    
    def flush(self):
        self.bmf_fh.flush()
        self.rev_fh.flush()
        self.ntee_fh.flush()
    
    def close(self):
        for fh in [self.bmf_fh, self.rev_fh, self.ntee_fh]:
            if fh:
                fh.close()


# ─── MAIN PROCESSING ────────────────────────────────────────────────────────
def run_workstream_c(download: bool = True, parse: bool = True):
    """Execute Workstream C: IRS BMF processing."""
    session = create_session()
    writer = BMF_CSVWriter()
    writer.open()
    
    all_bmf_records = []
    pub78_data = {}
    revocation_data = {}
    
    try:
        # Step 1: Download and parse BMF files
        if download:
            logger.info("=" * 60)
            logger.info("Step 1: Downloading BMF files")
            logger.info("=" * 60)
            
            for name, url in BMF_URLS.items():
                local_path = RAW_DIR / f"{name}.csv"
                
                if download_file(session, url, local_path):
                    if parse:
                        logger.info(f"Parsing {name}...")
                        records = parse_bmf_file(local_path)
                        logger.info(f"  {name}: {len(records)} 501(c)(3) PC/POF records")
                        all_bmf_records.extend(records)
                        
                        # Write in batches
                        for r in records:
                            writer.write_bmf_org(r)
                        
                        if len(all_bmf_records) % 10000 == 0:
                            writer.flush()
        
        # Step 2: Download and parse Publication 78
        if download:
            logger.info("=" * 60)
            logger.info("Step 2: Processing Publication 78")
            logger.info("=" * 60)
            pub78_data = download_and_parse_pub78(session)
        
        # Step 3: Download and parse Revocation List
        if download:
            logger.info("=" * 60)
            logger.info("Step 3: Processing Auto-Revocation List")
            logger.info("=" * 60)
            revocation_data = download_and_parse_revocation(session)
            
            # Write revocation records
            for ein, record in revocation_data.items():
                writer.write_revocation(record)
        
        # Step 4: Build NTEE taxonomy
        logger.info("=" * 60)
        logger.info("Step 4: Building NTEE Taxonomy")
        logger.info("=" * 60)
        ntee_records = build_ntee_taxonomy()
        writer.write_ntee(ntee_records)
        logger.info(f"NTEE taxonomy: {len(ntee_records)} codes written")
        
        writer.flush()
        
        # Summary
        logger.info("=" * 60)
        logger.info("Workstream C Complete")
        logger.info(f"BMF records: {len(all_bmf_records)}")
        logger.info(f"Publication 78 records: {len(pub78_data)}")
        logger.info(f"Revocation records: {len(revocation_data)}")
        logger.info(f"NTEE taxonomy codes: {len(ntee_records)}")
        logger.info("=" * 60)
    
    except KeyboardInterrupt:
        logger.info("Interrupted, saving progress...")
    finally:
        writer.close()


# ─── CLI ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Workstream C: IRS BMF & Publication 78 Processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download and parse everything
  python workstream_c_irs_bmf.py --download --parse
  
  # Parse only (files already downloaded)
  python workstream_c_irs_bmf.py --parse-only
        """
    )
    parser.add_argument("--download", action="store_true", help="Download source files")
    parser.add_argument("--parse", action="store_true", help="Parse downloaded files")
    parser.add_argument("--parse-only", action="store_true", help="Parse existing files without downloading")
    
    args = parser.parse_args()
    
    download = args.download or (not args.parse_only)
    parse = args.parse or args.parse_only or args.download
    
    if not download and not parse:
        parser.print_help()
        return
    
    logger.info("=" * 60)
    logger.info("Workstream C: IRS BMF & Publication 78")
    logger.info(f"Download: {download} | Parse: {parse}")
    logger.info("=" * 60)
    
    run_workstream_c(download=download, parse=parse)


if __name__ == "__main__":
    main()
