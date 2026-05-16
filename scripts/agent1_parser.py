#!/usr/bin/env python3
"""
AGENT 1: DEEP XML PARSER
Mission: Extract every relevant field from all 990/990-EZ XMLs in storage.
"""
import os, csv, glob, re, sys
import xml.etree.ElementTree as ET

OUT = "data/csv/extracted_financials.csv"
os.makedirs("data/csv", exist_ok=True)

def get_text(root, xpath, ns=None):
    if ns:
        el = root.find(xpath, ns)
        if el is not None and el.text:
            return el.text.strip()
    xpath_no_ns = re.sub(r'[a-zA-Z0-9]+:', '', xpath)
    el = root.find(xpath_no_ns)
    if el is not None and el.text:
        return el.text.strip()
    return None

def safe_float(val):
    if val is None:
        return None
    val = str(val).replace(',', '').replace('$', '').strip()
    try:
        return float(val)
    except:
        return None

def parse_xml(xml_path):
    try:
        with open(xml_path, 'rb') as f:
            raw = f.read()
        raw = raw.replace(b'\x00', b'')
        root = ET.fromstring(raw)
    except Exception as e:
        return None

    ns = None
    if root.tag.startswith('{'):
        nsurl = root.tag.split('}')[0][1:]
        ns = {'ns': nsurl}

    def g(xpath):
        return get_text(root, xpath, ns)

    ein = g("ns:ReturnHeader/ns:Filer/ns:EIN") or g("ReturnHeader/Filer/EIN")
    tax_year = g("ns:ReturnHeader/ns:TaxYr") or g("ReturnHeader/TaxYr")
    org_name = (g("ns:ReturnHeader/ns:Filer/ns:BusinessName/ns:BusinessNameLine1Txt") or 
                g("ReturnHeader/Filer/BusinessName/BusinessNameLine1"))
    
    employees = g("ns:ReturnData/ns:IRS990/ns:TotalEmployeeCnt") or g("ReturnData/IRS990/TotalEmployeeCnt")
    volunteers = g("ns:ReturnData/ns:IRS990/ns:TotalVolunteersCnt") or g("ReturnData/IRS990/TotalVolunteersCnt")
    
    mission = (g("ns:ReturnData/ns:IRS990/ns:ActivityOrMissionDesc") or 
               g("ReturnData/IRS990/ActivityOrMissionDesc"))
    
    prog_descs = []
    for pattern in [
        "ns:ReturnData/ns:IRS990/ns:ProgramSrvcAccomplishmentGrp/ns:Desc",
        "ns:ReturnData/ns:IRS990/ns:ProgramServiceAccomplishment/ns:Description",
        "ReturnData/IRS990/ProgramSrvcAccomplishmentGrp/Desc",
        "ReturnData/IRS990/ProgramServiceAccomplishment/Description"
    ]:
        found = root.findall(pattern, ns) if ns else root.findall(pattern)
        for f in found:
            if f.text and len(f.text.strip()) > 10:
                prog_descs.append(f.text.strip())
    program_accomplishments = " | ".join(prog_descs[:3]) if prog_descs else None
    
    officers = []
    officer_patterns = [
        "ns:ReturnData/ns:IRS990/ns:OfficerDirectorTrusteeEmplGrp",
        "ns:ReturnData/ns:IRS990/ns:OfficerDirectorTrusteeEmployee",
        "ReturnData/IRS990/OfficerDirectorTrusteeEmplGrp",
        "ReturnData/IRS990/OfficerDirectorTrusteeEmployee"
    ]
    for pattern in officer_patterns:
        found = root.findall(pattern, ns) if ns else root.findall(pattern)
        for person in found[:5]:
            name = (get_text(person, "ns:PersonNm", ns) or 
                    get_text(person, "PersonName", None))
            title = get_text(person, "ns:TitleTxt", ns) or get_text(person, "Title", None)
            comp = get_text(person, "ns:CompensationAmt", ns) or get_text(person, "Compensation", None)
            if name:
                officers.append(f"{name} ({title or 'Unknown'}): ${comp or '0'}")
    top_officers = " | ".join(officers) if officers else None
    
    total_exp = (g("ns:ReturnData/ns:IRS990/ns:FunctionalExpenses/ns:TotalFunctionalExpensesAmt") or
                 g("ReturnData/IRS990/FunctionalExpenses/TotalFunctionalExpensesAmt"))
    program_exp = (g("ns:ReturnData/ns:IRS990/ns:FunctionalExpenses/ns:ProgramServicesAmt") or
                   g("ReturnData/IRS990/FunctionalExpenses/ProgramServicesAmt"))
    mgmt_exp = (g("ns:ReturnData/ns:IRS990/ns:FunctionalExpenses/ns:ManagementAndGeneralAmt") or
                g("ReturnData/IRS990/FunctionalExpenses/ManagementAndGeneralAmt"))
    fund_exp = (g("ns:ReturnData/ns:IRS990/ns:FunctionalExpenses/ns:FundraisingAmt") or
                g("ReturnData/IRS990/FunctionalExpenses/FundraisingAmt"))
    
    total_assets = (g("ns:ReturnData/ns:IRS990/ns:TotalAssetsEOYAmt") or
                    g("ReturnData/IRS990/TotalAssetsEOYAmt"))
    net_assets = (g("ns:ReturnData/ns:IRS990/ns:NetAssetsOrFundBalancesEOYAmt") or
                  g("ReturnData/IRS990/NetAssetsOrFundBalancesEOYAmt"))
    
    total_revenue = (g("ns:ReturnData/ns:IRS990/ns:CYTotalRevenueAmt") or
                     g("ReturnData/IRS990/CYTotalRevenueAmt"))
    contributions = (g("ns:ReturnData/ns:IRS990/ns:CYContributionsGrantsAmt") or
                       g("ReturnData/IRS990/CYContributionsGrantsAmt"))
    
    schedule_o = []
    so_patterns = [
        "ns:ReturnData/ns:IRS990ScheduleO/ns:SupplementalInformationDetail/ns:ExplanationTxt",
        "ReturnData/IRS990ScheduleO/SupplementalInformationDetail/ExplanationTxt"
    ]
    for pattern in so_patterns:
        found = root.findall(pattern, ns) if ns else root.findall(pattern)
        for f in found:
            if f.text and len(f.text.strip()) > 20:
                schedule_o.append(f.text.strip())
    schedule_o_text = " | ".join(schedule_o[:2]) if schedule_o else None
    
    if not ein:
        return None
        
    return {
        'ein': str(ein).replace('.0', '').strip(),
        'tax_year': tax_year,
        'name': org_name,
        'total_revenue': safe_float(total_revenue),
        'contributions': safe_float(contributions),
        'total_expenses': safe_float(total_exp),
        'program_expenses': safe_float(program_exp),
        'mgmt_expenses': safe_float(mgmt_exp),
        'fundraising_expenses': safe_float(fund_exp),
        'total_assets': safe_float(total_assets),
        'net_assets': safe_float(net_assets),
        'employees': employees,
        'volunteers': volunteers,
        'mission': mission,
        'program_accomplishments': program_accomplishments,
        'top_officers': top_officers,
        'schedule_o': schedule_o_text,
        'source_file': os.path.basename(xml_path)
    }

print("[AGENT 1] Scanning for XML files...")
xml_files = glob.glob("data/xml/**/*.xml", recursive=True)
print(f"[AGENT 1] Found {len(xml_files)} XML files")

if len(xml_files) == 0:
    print("[AGENT 1] No XML files found. Check data/xml_filings/")
    sys.exit(1)

records = []
errors = 0
for i, f in enumerate(xml_files):
    if i % 1000 == 0 and i > 0:
        print(f"[AGENT 1] Parsed {i}/{len(xml_files)} | Good: {len(records)} | Errors: {errors}")
    rec = parse_xml(f)
    if rec:
        records.append(rec)
    else:
        errors += 1

print(f"[AGENT 1] Complete. Good: {len(records)} | Errors: {errors}")

if records:
    keys = records[0].keys()
    with open(OUT, 'w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=keys)
        writer.writeheader()
        writer.writerows(records)
    print(f"[AGENT 1] Wrote {len(records)} records to {OUT}")
else:
    print("[AGENT 1] No records extracted")
    sys.exit(1)
