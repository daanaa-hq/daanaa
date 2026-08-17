#!/usr/bin/env python3
"""
scripts/ops/fetch_irs_direct_filing.py

Fetches a single org's most recent 990 filing directly from the IRS's own
publishing pipeline (apps.irs.gov), bypassing gt990's ~2-3 month bulk-rebuild
cadence. Built 2026-08-16 after confirming AKF (EIN 521231983) had a real
FY2025 filing (filed 2026-05-15) that gt990's June 4 index didn't have yet --
verified this source has it, and every figure matched CauseIQ exactly
(revenue $106,705,948, expenses $96,147,712, assets $601,887,350,
fundraising $1,445,364, reconciling Part IX breakdown).

IMPORTANT: the IRS's OWN AWS S3 bucket (s3://irs-form-990) was discontinued
December 31, 2021 and is no longer updated. This uses apps.irs.gov's direct
publishing instead (Form 990 series downloads), which IS still active and
updates monthly.

Mechanics:
1. Download the per-submission-year index CSV (index_2025.csv, index_2026.csv,
   etc. -- indexed by when IRS processed/released the filing, NOT the tax
   year it covers) to find the target EIN's most recent ObjectId + XML_BATCH_ID.
2. Download that one monthly batch ZIP (400-700MB, one IRS release covers
   ~50-70K filings across all orgs that submitted that month).
3. Extract just the target EIN's XML, parse revenue/assets/expenses and the
   Part IX functional-expense breakdown.

Scoped to single-org lookups (checking "does this specific org have newer
data than we have") -- NOT a bulk backfill tool. Downloading a ~500MB batch
ZIP per org doesn't scale; for bulk refresh, gt990's consolidated index
(scripts/ops/refresh_stale_orgs_from_gt990.py) remains the right tool.

The index/parse/write building blocks below (iter_990_index_rows,
batch_zip_url, parse_990_xml, write_filing) are also imported by
scripts/ops/refresh_recent_filings_batch.py, the batch-mode version that
downloads each monthly ZIP once and extracts every registry EIN found in it --
built 2026-08-16 once single-org lookups proved this source out. Keep those
functions' signatures stable; the batch script depends on them directly.

Usage:
    python3 scripts/ops/fetch_irs_direct_filing.py 521231983
    python3 scripts/ops/fetch_irs_direct_filing.py 521231983 --apply
"""
import argparse
import csv
import io
import json
import re
import subprocess
import sys
import sqlite3
import tempfile
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from scripts.enrichment.enrich_cause_tags_mission import apply_rules, merge_tags  # noqa: E402
from scripts.enrichment.ingest_990_missions import JUNK as MISSION_JUNK  # noqa: E402

DB_PATH = Path.home() / "meritgiving" / "data" / "merit_registry.db"
NS = "http://www.irs.gov/efile"
INDEX_BASE = "https://apps.irs.gov/pub/epostcard/990/xml"
PARSER_VERSION = "1.5-2026-08-16-mission-junk-filter-v2"

# Schedule O carries dozens of explanations per filing, most of them governance
# boilerplate (conflict-of-interest policy, compensation-review process, etc.)
# or plain financial-line detail that says nothing about what the org does.
# Filter to the lines that answer "what does this org do", calibrated against
# every real FormAndLineReferenceDesc value seen in the 24-filing Phase 1
# sample (docs/990-enrichment/xml-field-inventory.md) -- values are messy in
# practice ("FORM 990, PAGE 2, PART III, LINE 4A", "Pt III, Line 31",
# "FORM 990 - ORGANIZATION'S MISSION", vs. noise like "FORM 990-EZ, PART I,
# LINE 16 - OTHER EXPENSES"). "PART I" was tried and rejected: on a full 990
# it only ever showed up unambiguously as the literal mission string (already
# matched by the "MISSION" keyword below); on a 990-EZ, "PART I" covers the
# combined revenue/expense statement, so every real "Part I" reference in
# the sample was financial noise (other expenses, investment income, grants
# paid) -- EZ's mission field is PrimaryExemptPurposeTxt, extracted
# separately, not this Schedule O path. "PART III" (any spelling/abbreviation:
# "Part III", "PAGE 2, PART III", "Pt III") is always the program
# accomplishments section on both forms -- kept unconditionally.
SCHEDULE_O_LINE_ALLOW = re.compile(r"\bP(?:AR)?T\s+III\b|MISSION", re.IGNORECASE)

# Same convention as scripts/enrichment/ingest_990_missions.py's JUNK set --
# grant-purpose fields (Schedule F/I/PF) are frequently a cross-reference
# rather than an actual purpose.
GRANT_PURPOSE_JUNK = {
    "N/A", "NA", "NONE", "SEE ATTACHED", "SEE SCHEDULE O", "SEE SCH O",
    "SEE ATTACHED SCHEDULE", "SAME AS PRIOR YEAR", "NO CHANGE", "SEE PART III", "TBD",
}


def batch_zip_url(batch_id: str) -> str:
    year = batch_id.split("_")[0]
    return f"{INDEX_BASE}/{year}/{batch_id}.zip"


def iter_990_index_rows(
    submission_years: list[int], return_types: frozenset[str] = frozenset({"990"})
) -> Iterator[dict]:
    """Yields raw index rows matching return_types for the given submission
    years -- the year IRS processed/released the filing, not the tax year it
    covers. Shared by single-org lookup and batch discovery so there's one
    place that knows the index CSV's shape.

    Default stays 990-only (unchanged production behavior for the existing
    04:15 nightly cron and the single-org CLI). parse_990_xml() gained
    990-EZ narrative support 2026-08-16 (Phase 3, DECISIONS.md same date),
    but the nightly batch job isn't opted into RETURN_TYPE='990EZ' in this
    change -- that's a separate, reviewable decision (more filings per batch
    = more download/runtime for the existing cron), not silently bundled
    into a schema/parser change. Pass return_types={'990','990EZ'} explicitly
    to opt in for testing."""
    for year in submission_years:
        url = f"{INDEX_BASE}/{year}/index_{year}.csv"
        print(f"Checking {url} ...")
        try:
            resp = requests.get(url, timeout=120)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"  skip ({e})")
            continue
        reader = csv.DictReader(io.StringIO(resp.text))
        for row in reader:
            if row.get("RETURN_TYPE", "").strip() not in return_types:
                continue  # skip other statement shapes (EZ/PF unless opted in above)
            yield row


def find_latest_filing(
    ein: str, submission_years: list[int], return_types: frozenset[str] = frozenset({"990"})
) -> dict | None:
    """Check the given submission-year indices (newest first) for this EIN's
    most recent Form 990 filing. Returns the newest match found."""
    best = None
    for row in iter_990_index_rows(submission_years, return_types):
        if row.get("EIN", "").strip().zfill(9) != ein:
            continue
        tax_period = row.get("TAX_PERIOD", "").strip()
        candidate = {
            "tax_period": tax_period,
            "object_id": row.get("OBJECT_ID", "").strip(),
            "batch_id": row.get("XML_BATCH_ID", "").strip(),
        }
        if best is None or tax_period > best["tax_period"]:
            best = candidate
    return best


# Hardening against a malformed/adversarial filing, per Codex Review B/C
# (2026-08-16): stdlib ET.fromstring() has no application-level cap on text
# length or repeating-group count, so an unusually large or deeply repeated
# filing could drive excessive memory/string-concatenation cost through the
# new narrative-extraction paths. IRS is a trusted upstream in practice (this
# isn't an XXE risk -- ElementTree doesn't resolve external entities), but
# these caps cost nothing on a normal filing and bound the worst case. Real
# filings in the Phase 1 sample topped out at ~5,700 chars for one Schedule O
# explanation and single digits of program/grant rows -- these limits are an
# order of magnitude above that.
MAX_FIELD_TEXT_LEN = 20_000
MAX_LIST_ITEMS = 200


def _text(el) -> str | None:
    if el is None or not el.text:
        return None
    value = " ".join(el.text.split())[:MAX_FIELD_TEXT_LEN]
    return value or None


def _is_grant_junk(value: str) -> bool:
    return value.upper().rstrip(".") in GRANT_PURPOSE_JUNK


# Bug found 2026-08-16, after a real production backfill run: 76 of 16,057
# missions written by this session's pipeline were literal cross-reference
# boilerplate ("SEE PART III, LINE 1.") rather than an actual mission --
# common when a lazy e-filer leaves Part I's mission field pointing at Part
# III instead of restating it. scripts/enrichment/ingest_990_missions.py
# (the older NCCS-based mission pipeline) already guards against exactly
# this with its JUNK set and a startswith-prefix check; this file's mission
# extraction never inherited that guard. Reusing the same JUNK set (imported,
# not duplicated) rather than maintaining two junk-detection lists.
def _is_mission_junk(value: str) -> bool:
    upper = value.upper().rstrip(".")
    if upper in MISSION_JUNK:
        return True
    # Deliberately specific prefixes, not a bare "starts with SEE" check --
    # verified against real production data (2026-08-16) that a blanket rule
    # would wrongly reject genuine mission text starting with the word "See"
    # as an imperative (e.g. "SEE GOD'S CHILDREN AND CHOSEN DELIVERED...").
    # Second batch added same day after the first pass left 231 real
    # cross-reference variants uncaught (SEE PAGE/SUMMARY/MISSION STATEMENT/
    # FORM 990/990) -- all unambiguous filing cross-references, not real
    # prose openings.
    #
    # Third batch added 2026-08-17 after a Codex review of the GT990
    # historical backfill's freshly written missions (177K new rows) found
    # this filter still missed real, repeated cross-reference variants:
    # "REFER TO SCHEDULE O", "SEE STATEMENT...", "SEE DESCRIPTION...",
    # "SEE ORGANIZATION'S...", "SEE SUPPLEMENT...", "NOT APPLICABLE" (a
    # spelled-out N/A the exact-match JUNK set didn't cover). Quantified
    # against the live database at the time: 223 rows across the full
    # irs_990-sourced population matched one of these missed prefixes (182
    # under 100 chars, near-certain junk), out of roughly 595K total --
    # a narrow, bounded defect, not a systemic corruption of the backfill
    # (the review's 60-row random sample was otherwise clean).
    return upper.startswith((
        "SEE SCHEDULE", "SEE SCH", "SEE PART", "SEE ATTACH",
        "SEE PAGE", "SEE SUMMARY", "SEE MISSION STATEMENT",
        "SEE FORM 990", "SEE 990",
        "REFER TO", "SEE STATEMENT", "SEE DESCRIPTION",
        "SEE ORGANIZATION", "SEE SUPPLEMENT", "NOT APPLICABLE",
    ))


def _extract_schedule_o(root) -> list[dict]:
    """Schedule O explanations, filtered to the lines that describe what the
    org does (mission/Part III) rather than governance boilerplate. Present
    on both 990 and 990-EZ filings under the same tag names."""
    out = []
    for detail in root.findall(f".//{{{NS}}}IRS990ScheduleO/{{{NS}}}SupplementalInformationDetail")[:MAX_LIST_ITEMS]:
        line_ref = _text(detail.find(f"{{{NS}}}FormAndLineReferenceDesc")) or ""
        explanation = _text(detail.find(f"{{{NS}}}ExplanationTxt"))
        if not explanation or not SCHEDULE_O_LINE_ALLOW.search(line_ref):
            continue
        out.append({"line_reference": line_ref, "explanation": explanation})
    return out


def _extract_990_programs(irs990) -> list[dict]:
    """Structured Part III program records for a full Form 990: the primary
    program (reported as direct IRS990 children, not a repeating group in
    this schema version) plus each additional program in the repeating
    ProgSrvcAccomActyOtherGrp. Verified against real 2026 filings -- see
    docs/990-enrichment/xml-field-inventory.md; the schema this project's
    audit assumed (ProgramServiceAccomplishmentGrp/DescriptionProgramServiceAccomTxt)
    does not exist in current filings and never matched."""
    programs = []
    primary_desc = _text(irs990.find(f"{{{NS}}}Desc"))
    if primary_desc:
        def amt(tag):
            el = irs990.find(f"{{{NS}}}{tag}")
            if el is None or not el.text:
                return None
            try:
                return float(el.text)
            except ValueError:
                return None
        programs.append({
            "description": primary_desc,
            "expense_amt": amt("ExpenseAmt"),
            "revenue_amt": amt("RevenueAmt"),
            "grant_amt": amt("GrantAmt"),
        })
    for grp in irs990.findall(f"{{{NS}}}ProgSrvcAccomActyOtherGrp")[:MAX_LIST_ITEMS]:
        desc = _text(grp.find(f"{{{NS}}}Desc"))
        if not desc:
            continue
        def gamt(tag, node=grp):
            el = node.find(f"{{{NS}}}{tag}")
            if el is None or not el.text:
                return None
            try:
                return float(el.text)
            except ValueError:
                return None
        programs.append({
            "description": desc,
            "expense_amt": gamt("ExpenseAmt"),
            "revenue_amt": gamt("RevenueAmt"),
            "grant_amt": gamt("GrantAmt"),
        })
    return programs


def _extract_990ez_programs(irs990ez) -> list[dict]:
    """990-EZ's Part III equivalent: a real repeating group (unlike full
    990's flatter primary+OtherGrp shape)."""
    programs = []
    for grp in irs990ez.findall(f"{{{NS}}}ProgramSrvcAccomplishmentGrp")[:MAX_LIST_ITEMS]:
        desc = _text(grp.find(f"{{{NS}}}DescriptionProgramSrvcAccomTxt"))
        if not desc:
            continue
        expense_el = grp.find(f"{{{NS}}}ProgramServiceExpensesAmt")
        expense_amt = None
        if expense_el is not None and expense_el.text:
            try:
                expense_amt = float(expense_el.text)
            except ValueError:
                pass
        programs.append({"description": desc, "expense_amt": expense_amt,
                          "revenue_amt": None, "grant_amt": None})
    return programs


def _extract_grant_purposes(root) -> list[str]:
    """Grant purposes from Schedule I (domestic) and Schedule F (foreign),
    junk-filtered. Schedule F's RegionTxt is appended when present -- it's
    the closest deterministic signal to 'geographic areas served' for
    grantmaking orgs. Schedule PF deliberately excluded here: Phase 1
    sampling found the vast majority of PF grant-purpose text is literally
    'SEE ATTACHED' (25/39 sampled rows) -- not useful signal, would just add
    noise to cause_tags."""
    purposes = []
    for row in root.findall(f".//{{{NS}}}IRS990ScheduleI/{{{NS}}}RecipientTable")[:MAX_LIST_ITEMS]:
        purpose = _text(row.find(f"{{{NS}}}PurposeOfGrantTxt"))
        if purpose and not _is_grant_junk(purpose):
            purposes.append(purpose)
    for row in root.findall(f".//{{{NS}}}IRS990ScheduleF/{{{NS}}}GrantsToOrgOutsideUSGrp")[:MAX_LIST_ITEMS]:
        purpose = _text(row.find(f"{{{NS}}}PurposeOfGrantTxt"))
        region = _text(row.find(f"{{{NS}}}RegionTxt"))
        if purpose and not _is_grant_junk(purpose):
            purposes.append(f"{purpose} ({region})" if region else purpose)
    return purposes[:MAX_LIST_ITEMS]


def parse_990_xml(content: bytes) -> dict | None:
    """Parses a single 990 or 990-EZ XML: revenue/assets/expenses (990 only --
    990-EZ's financial field names are unverified against real filings, so
    this deliberately does not guess at them; narrative extraction is
    990-EZ's only supported output for now), Part IX functional-expense
    breakdown, organization-authored mission text, structured Part III
    program records, Schedule O explanations, and grant purposes.
    Returns None if the filing is neither a parseable IRS990 nor IRS990EZ
    return (e.g. 990-PF, 990-T -- not this function's shape).

    Mission text added 2026-08-16 (Track B/C consolidation, see DECISIONS.md
    same date). Narrative fields (Schedule O, structured programs, grant
    purposes, 990-EZ support) added 2026-08-16 (990 Narrative Enrichment
    project, DECISIONS.md same date "reuse existing tables/scripts") --
    same single XML download, same parse pass, no extra network round trip."""
    root = ET.fromstring(content)
    irs990 = root.find(f".//{{{NS}}}IRS990")
    irs990ez = root.find(f".//{{{NS}}}IRS990EZ") if irs990 is None else None
    if irs990 is None and irs990ez is None:
        return None

    schedule_o = _extract_schedule_o(root)
    grant_purposes = _extract_grant_purposes(root)

    if irs990ez is not None:
        # 990-EZ: narrative only. Financials intentionally left None -- see
        # docstring. write_filing() must not let None financials overwrite
        # an EIN's existing revenue/assets.
        mission_text = _text(irs990ez.find(f"{{{NS}}}PrimaryExemptPurposeTxt"))
        if mission_text and _is_mission_junk(mission_text):
            mission_text = None
        programs = _extract_990ez_programs(irs990ez)
        return {
            "total_revenue": None, "total_assets": None, "total_expenses": None,
            "program_services_amt": None, "management_general_amt": None,
            "fundraising_amt": None,
            "mission_text": mission_text,
            "programs": programs,
            "schedule_o": schedule_o,
            "grant_purposes": grant_purposes,
            "significant_new_program": None,
            "significant_change": None,
        }

    grp = irs990.find(f".//{{{NS}}}TotalFunctionalExpensesGrp")

    def amt(tag, node=irs990):
        el = node.find(f".//{{{NS}}}{tag}")
        if el is None or not el.text:
            return None
        try:
            return float(el.text)
        except ValueError:
            return None

    # Part I is the organization's explicit short mission statement -- prefer
    # it. Part III's MissionDesc is the org's longer mission narrative (a
    # distinct field, not a duplicate); use it as the second choice. Last
    # resort: join the structured program descriptions themselves. (The
    # previous fallback here referenced ProgramServiceAccomplishmentGrp/
    # DescriptionProgramServiceAccomTxt, a field name that does not exist in
    # current-year filings -- verified against 8 real sampled 990s, never
    # matched. Replaced with the real schema, see xml-field-inventory.md.)
    programs = _extract_990_programs(irs990)

    def _mission_candidate(text_value):
        """None if empty or junk -- lets the caller fall through to the
        next candidate instead of accepting a cross-reference as a mission."""
        if not text_value or _is_mission_junk(text_value):
            return None
        return text_value

    # Second bug found in the same review pass (2026-08-16): the two direct
    # candidates above were junk-filtered, but this third fallback -- joining
    # every Part III program description -- was not. A junk individual
    # description ("SEE SCHEDULE O") joined ahead of a real one produced
    # mission text like "SEE SCHEDULE O\n\nOUR Y IS COMMITTED TO..." (a real,
    # observed production case). Filter each program description the same
    # way before joining, and drop the whole candidate if nothing real
    # survives, rather than joining unfiltered.
    non_junk_program_descriptions = [
        p["description"] for p in programs
        if p.get("description") and not _is_mission_junk(p["description"])
    ]

    mission_text = (
        _mission_candidate(_text(irs990.find(f"{{{NS}}}ActivityOrMissionDesc")))
        or _mission_candidate(_text(irs990.find(f"{{{NS}}}MissionDesc")))
        or ("\n\n".join(non_junk_program_descriptions) or None)
    )

    def bool_ind(tag):
        el = irs990.find(f"{{{NS}}}{tag}")
        if el is None or not el.text:
            return None
        return el.text.strip().lower() in ("true", "x", "1")

    return {
        "total_revenue": amt("CYTotalRevenueAmt"),
        "total_assets": amt("TotalAssetsEOYAmt"),
        "total_expenses": amt("TotalAmt", grp) if grp is not None else None,
        "program_services_amt": amt("ProgramServicesAmt", grp) if grp is not None else None,
        "management_general_amt": amt("ManagementAndGeneralAmt", grp) if grp is not None else None,
        "fundraising_amt": amt("FundraisingAmt", grp) if grp is not None else None,
        "mission_text": mission_text,
        "programs": programs,
        "schedule_o": schedule_o,
        "grant_purposes": grant_purposes,
        "significant_new_program": bool_ind("SignificantNewProgramSrvcInd"),
        "significant_change": bool_ind("SignificantChangeInd"),
    }


def fetch_and_parse(batch_id: str, object_id: str) -> dict | None:
    zip_url = batch_zip_url(batch_id)
    print(f"Downloading {zip_url} (this is a full monthly batch, ~400-700MB)...")

    xml_name = f"{object_id}_public.xml"
    # Python's zipfile module doesn't support the compression method IRS uses
    # for these archives ("That compression method is not supported") --
    # confirmed the command-line `unzip` handles it fine, so shell out to it
    # instead of fighting zipfile.
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "batch.zip"
        resp = requests.get(zip_url, timeout=600, stream=True)
        resp.raise_for_status()
        with open(zip_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1 << 20):
                f.write(chunk)

        result = subprocess.run(
            ["unzip", "-o", str(zip_path), xml_name, "-d", tmpdir],
            capture_output=True, text=True
        )
        xml_path = Path(tmpdir) / xml_name
        if result.returncode != 0 or not xml_path.exists():
            print(f"  {xml_name} not found in batch (unzip: {result.stderr.strip()})")
            return None
        content = xml_path.read_bytes()

    return parse_990_xml(content)


def write_filing(db: sqlite3.Connection, ein: str, filing: dict, data: dict, now: str) -> bool:
    """Writes one parsed filing to registry_enriched + supporting tables
    using the established safety rules: never downgrade, reconciliation-
    checked expense breakdown, additive-only narrative writes. Returns
    whether the expense breakdown reconciled (True even when there's no
    breakdown to check -- e.g. a 990-EZ narrative-only filing -- since "no
    breakdown" is not a reconciliation failure).
    Shared by the single-org CLI and the batch script -- change write
    behavior here only, not in both places."""
    tax_year = int(filing["tax_period"][:4])
    total = data["total_expenses"]
    program = data["program_services_amt"] or 0
    mgmt = data["management_general_amt"] or 0
    fundraising = data["fundraising_amt"] or 0
    reconciles = True if total is None else abs((program + mgmt + fundraising) - total) <= 1

    # Financial writes: only when this filing actually produced financials.
    # 990-EZ narrative-only filings (parse_990_xml returns total_revenue=None
    # by design -- EZ's financial field names are unverified against real
    # filings) must not fall through to the UPDATE below, which would
    # otherwise silently overwrite an EIN's existing good revenue/assets with
    # NULL. This also fixes a latent bug in the original 2026-08-16 version:
    # a full-990 filing whose revenue somehow failed to parse (None) would
    # have hit the same unconditional UPDATE and clobbered existing data once
    # the tax_year guard passed -- found during Phase 3 narrative-extension
    # review, not previously exercised (every sampled 990 parsed cleanly).
    #
    # Codex Review B/C (2026-08-16) found this guard was still incomplete:
    # it protects total_revenue but not total_assets independently -- a
    # filing with parseable revenue but a missing/invalid assets figure would
    # still write NULL into total_assets on both tables. COALESCE against the
    # existing registry value so a per-field parse failure never clobbers a
    # per-field value that was already known good.
    if data["total_revenue"] is not None:
        db.execute(
            "INSERT OR REPLACE INTO org_revenue_history "
            "(EIN, tax_year, total_revenue, total_assets, total_expenses, form_type, source, extracted_at) "
            "VALUES (?, ?, ?, COALESCE(?, (SELECT total_assets FROM org_revenue_history "
            "  WHERE EIN = ? AND tax_year = ?)), ?, '990', 'irs_direct', ?)",
            (ein, tax_year, data["total_revenue"], data["total_assets"], ein, tax_year,
             data["total_expenses"], now)
        )
        db.execute(
            "UPDATE registry_enriched SET total_revenue = ?, "
            "total_assets = COALESCE(?, total_assets), latest_tax_year = ?, "
            "data_source = 'irs_direct' WHERE EIN = ? AND (latest_tax_year IS NULL OR latest_tax_year < ?)",
            (data["total_revenue"], data["total_assets"], tax_year, ein, tax_year)
        )
    if data["program_services_amt"] is not None:
        db.execute(
            "INSERT OR REPLACE INTO irs_990_functional_expense_filings "
            "(EIN, tax_year, object_id, source_url, total_amt, program_services_amt, "
            "management_general_amt, fundraising_amt, reconciles, validation_status, parser_version, extracted_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (ein, tax_year, filing["object_id"], batch_zip_url(filing["batch_id"]),
             total, program, mgmt, fundraising, int(reconciles),
             "accepted" if reconciles else "rejected", PARSER_VERSION, now)
        )

    # Mission text. Guard clause copied verbatim from
    # scripts/enrichment/ingest_990_missions.py's existing precedence rule:
    # never overwrites a claimed/nonprofit-submitted mission or a
    # scraped-from-website mission. Extended 2026-08-16 (Phase 3 narrative
    # work, DECISIONS.md same date) to also let a NEWER irs_990 filing
    # replace an OLDER one -- the original guard blocked this once
    # mission_source was already 'irs_990', found reviewing Codex's Review A
    # ("does not implement latest IRS mission wins").
    #
    # Codex Review B/C (2026-08-16): mission_last_verified is a TEXT column;
    # a lexical '<' comparison works today because every irs_990 value is a
    # bare 4-digit year, but would silently misorder against a differently
    # shaped value (e.g. an ISO timestamp) if one were ever written to this
    # column under mission_source='irs_990'. CAST both sides to INTEGER so
    # the comparison is well-defined regardless of the stored value's shape
    # (CAST of a non-numeric string is 0 in SQLite, which fails safe: it
    # sorts below any real year, so a malformed existing value would be
    # treated as staler and preferred, never as newer and protected against
    # replacement).
    mission_text = data.get("mission_text")
    if mission_text and len(mission_text.strip()) >= 20:
        db.execute(
            "UPDATE registry_enriched "
            "SET mission = ?, mission_source = 'irs_990', "
            "    mission_last_verified = ? "
            "WHERE EIN = ? "
            "  AND (mission_source IS NULL OR mission_source LIKE 'ai_%' "
            "       OR mission IS NULL OR mission = '' "
            "       OR (mission_source = 'irs_990' "
            "           AND (mission_last_verified IS NULL "
            "                OR CAST(mission_last_verified AS INTEGER) < ?)))",
            (mission_text, str(tax_year), ein, tax_year),
        )

    # Schedule O -> extracted_programs. Existing table, existing producer
    # convention (scripts/enrichment/schedule_o_extraction.py, ProPublica-
    # sourced, never run -- 0 rows): same table, new schedule_o_source value,
    # so any future consumer doesn't need to know which pipeline populated a
    # given row beyond checking that column. One row per filing (allowlisted
    # Schedule O explanations for the same EIN/year are joined, matching the
    # table's PRIMARY KEY (EIN, schedule_o_year)).
    schedule_o = data.get("schedule_o") or []
    if schedule_o:
        joined = "\n\n".join(
            f"[{row['line_reference']}] {row['explanation']}" if row["line_reference"] else row["explanation"]
            for row in schedule_o
        )
        db.execute(
            "INSERT OR REPLACE INTO extracted_programs "
            "(EIN, schedule_o_text, schedule_o_year, schedule_o_source, extraction_confidence, extracted_at) "
            "VALUES (?, ?, ?, 'irs_990_xml', 1.0, ?)",
            (ein, joined, tax_year, now),
        )

    # cause_tags: reuse scripts/enrichment/enrich_cause_tags_mission.py's
    # apply_rules()/merge_tags() verbatim against the richer narrative text
    # (mission + Schedule O + Part III program descriptions + grant
    # purposes), not just the short mission string that script normally
    # reads. Same additive guarantee (merge_tags never removes a tag), same
    # rule set -- this is the highest-leverage searchability win available,
    # since cause_tags already feeds both org_fts (build_fts_index.py) and
    # org_embeddings (build_org_embeddings.py) with zero new search
    # infrastructure needed. DECISIONS.md 2026-08-16.
    programs = data.get("programs") or []
    grant_purposes = data.get("grant_purposes") or []
    narrative_parts = [mission_text or ""]
    narrative_parts += [p["description"] for p in programs if p.get("description")]
    narrative_parts += [row["explanation"] for row in schedule_o]
    narrative_parts += grant_purposes
    narrative_text = "\n".join(part for part in narrative_parts if part)
    if narrative_text.strip():
        new_tags = apply_rules(narrative_text)
        if new_tags:
            row = db.execute(
                "SELECT cause_tags FROM registry_enriched WHERE EIN = ?", (ein,)
            ).fetchone()
            if row is not None:
                try:
                    existing = json.loads(row[0]) if row[0] else []
                except (TypeError, ValueError):
                    existing = []
                merged = merge_tags(existing, new_tags)
                if merged != existing:
                    db.execute(
                        "UPDATE registry_enriched SET cause_tags = ? WHERE EIN = ?",
                        (json.dumps(merged), ein),
                    )

    # programs_available: flip on when this filing actually produced
    # structured program content, so the frontend can decide whether to
    # render a Programs section without re-deriving that from raw text.
    if programs:
        db.execute(
            "UPDATE registry_enriched SET programs_available = 1 WHERE EIN = ?",
            (ein,),
        )

    return reconciles


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ein")
    ap.add_argument("--apply", action="store_true", help="Write to the database (default: print only)")
    ap.add_argument("--include-ez", action="store_true",
                     help="Also check 990-EZ filings (narrative only, no financials -- see write_filing())")
    args = ap.parse_args()

    ein = args.ein.zfill(9)
    return_types = frozenset({"990", "990EZ"}) if args.include_ez else frozenset({"990"})
    current_year = datetime.now().year
    filing = find_latest_filing(ein, [current_year, current_year - 1], return_types)
    if not filing:
        print("No Form 990 filing found in the checked submission years.")
        sys.exit(1)

    print(f"Found: tax_period={filing['tax_period']}, object_id={filing['object_id']}, batch={filing['batch_id']}")
    data = fetch_and_parse(filing["batch_id"], filing["object_id"])
    if not data:
        print("Could not parse the filing.")
        sys.exit(1)

    print(f"\nParsed (tax_year={filing['tax_period'][:4]}):")
    for k, v in data.items():
        print(f"  {k}: {v}")

    if not args.apply:
        total = data["total_expenses"]
        program = data["program_services_amt"] or 0
        mgmt = data["management_general_amt"] or 0
        fundraising = data["fundraising_amt"] or 0
        reconciles = bool(total and abs((program + mgmt + fundraising) - total) <= 1)
        print(f"  reconciles: {reconciles}")
        print("\nDry run -- no changes written. Re-run with --apply to write.")
        return

    db = sqlite3.connect(DB_PATH)
    now = datetime.now(timezone.utc).isoformat()
    reconciles = write_filing(db, ein, filing, data, now)
    db.commit()
    print(f"  reconciles: {reconciles}")
    print("Written.")


if __name__ == "__main__":
    main()
