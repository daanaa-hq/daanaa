#!/usr/bin/env python3
import os, csv, json, time, xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict

BASE = Path.home() / "meritgiving"
XML_DIR = BASE / "data" / "xml"
MASTER_CSV = BASE / "data" / "csv" / "master_orgs.csv"
PROGRESS_FILE = BASE / "data" / "xml_parse_progress.json"
EXTRACTED_FILE = BASE / "data" / "xml_extracted.json"

def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"completed_files": [], "errors": 0, "total_orgs": 0}

def save_progress(progress):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f)

def load_extracted():
    if EXTRACTED_FILE.exists():
        with open(EXTRACTED_FILE) as f:
            return json.load(f)
    return {}

def save_extracted(data):
    with open(EXTRACTED_FILE, "w") as f:
        json.dump(data, f)

def find_text(root, *tags):
    for tag in tags:
        for e in root.iter():
            if e.tag.endswith(tag) or e.tag == tag:
                if e.text and e.text.strip():
                    return e.text.strip()
    return None

def parse_xml_file(filepath):
    try:
        tree = ET.parse(str(filepath))
        root = tree.getroot()
        filename = filepath.name
        ein_from_file = filename.split("_")[0]
        
        data = {}
        data["EIN"] = find_text(root, "EIN") or ein_from_file
        data["NAME"] = find_text(root, "BusinessNameLine1Txt", "BusinessNameLine1", "Name")
        data["CITY"] = find_text(root, "CityNm", "City")
        data["STATE"] = find_text(root, "StateAbbreviationCd", "State")
        data["NTEE"] = find_text(root, "NTEECd", "NTEECode")
        data["YEAR"] = find_text(root, "TaxYr", "TaxYear", "ReturnTs")
        data["REVENUE"] = find_text(root, "CYTotalRevenueAmt", "TotalRevenueCurrentYear", "TotalRevenue")
        data["TOTAL_EXPENSES"] = find_text(root, "CYTotalExpensesAmt", "TotalExpensesCurrentYear", "TotalExpenses")
        data["PROGRAM_EXPENSES"] = find_text(root, "TotalProgramServiceExpenses", "CYProgramServiceRevenueAmt", "ProgramServicesExpenses")
        data["NET_ASSETS"] = find_text(root, "NetAssetsOrFundBalancesEOYAmt", "NetAssetsOrFundBalancesEOY")
        data["TOTAL_ASSETS"] = find_text(root, "TotalAssetsEOYAmt", "TotalAssetsEOY")
        data["EMPLOYEES"] = find_text(root, "TotalEmployeeCnt", "EmployeeCnt")
        data["VOLUNTEERS"] = find_text(root, "TotalVolunteersCnt", "VolunteersCnt")
        data["MISSION"] = find_text(root, "MissionDesc", "MissionStatement")
        data["PROGRAM_ACCOMPLISHMENTS"] = find_text(root, "ProgramServiceAccomplishment/Desc", "ProgramServiceAccomplishmentDesc")
        
        leaders = []
        for e in root.iter():
            if e.tag.endswith("NamePerson") or e.tag.endswith("PersonNm"):
                if e.text and e.text.strip():
                    leaders.append(e.text.strip())
            if len(leaders) >= 3:
                break
        if leaders:
            data["LEADERSHIP"] = ", ".join(leaders)
        
        return {k: v for k, v in data.items() if v is not None and v != ""}
    except Exception as e:
        return None

def update_master_csv(extracted_data):
    rows = []
    with open(MASTER_CSV, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames)
        for row in reader:
            rows.append(row)
    
    all_keys = set(fieldnames)
    for d in extracted_data.values():
        all_keys.update(d.keys())
    
    for k in all_keys:
        if k not in fieldnames:
            fieldnames.append(k)
    
    updated = 0
    for row in rows:
        ein = str(row.get("EIN", "")).strip()
        if ein in extracted_data:
            for key, val in extracted_data[ein].items():
                if val and str(val).strip().lower() not in ("", "nan", "none", "null", "-"):
                    row[key] = str(val)
            updated += 1
    
    for row in rows:
        for k in fieldnames:
            if k not in row:
                row[k] = ""
    
    output_csv = MASTER_CSV.with_suffix(".csv.enriched")
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    backup = MASTER_CSV.with_suffix(".csv.backup_xml")
    os.rename(MASTER_CSV, backup)
    os.rename(output_csv, MASTER_CSV)
    return updated

def main(batch_limit=50000):
    progress = load_progress()
    completed = set(progress["completed_files"])
    extracted = load_extracted()
    
    xml_files = []
    for year_dir in sorted(XML_DIR.iterdir()):
        if year_dir.is_dir():
            for xml_file in year_dir.glob("*.xml"):
                if str(xml_file) not in completed:
                    xml_files.append(xml_file)
    
    total = len(xml_files)
    print("Total XML files: " + str(total))
    print("Already done: " + str(len(completed)))
    print("Will process: " + str(min(batch_limit, total)))
    print("")
    
    parsed = 0
    start_time = time.time()
    
    for i, xml_file in enumerate(xml_files[:batch_limit]):
        if i % 100 == 0 and i > 0:
            elapsed = time.time() - start_time
            rate = (i / elapsed * 60) if elapsed > 0 else 0
            print("[" + str(i) + "/" + str(min(batch_limit, total)) + "] Parsed " + str(parsed) + " orgs | " + str(int(rate)) + " files/min")
            save_extracted(extracted)
            save_progress(progress)
        
        result = parse_xml_file(xml_file)
        if result and result.get("EIN"):
            ein = result["EIN"]
            if ein not in extracted:
                extracted[ein] = result
            else:
                for k, v in result.items():
                    if v and str(v).strip():
                        extracted[ein][k] = v
            parsed += 1
        else:
            progress["errors"] += 1
        
        completed.add(str(xml_file))
        progress["completed_files"] = list(completed)
    
    save_extracted(extracted)
    save_progress(progress)
    
    print("")
    print("Done! Parsed " + str(parsed) + " orgs from " + str(min(batch_limit, total)) + " files.")
    print("Errors: " + str(progress["errors"]))
    print("")
    print("Updating master_orgs.csv...")
    updated = update_master_csv(extracted)
    print("Updated " + str(updated) + " rows")
    print("")
    print("Restart server: pkill -f uvicorn; sleep 2; cd ~/meritgiving && nohup python3 -m uvicorn app:app --host 0.0.0.0 --port 8081 --workers 1 > server.log 2>&1 &")

if __name__ == "__main__":
    limit = int(os.environ.get("XML_BATCH_LIMIT", "50000"))
    main(limit)
