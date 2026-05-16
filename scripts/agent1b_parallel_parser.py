#!/usr/bin/env python3
import os, csv, glob, re, sys
import xml.etree.ElementTree as ET
from multiprocessing import Pool, cpu_count

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
    if val is None: return None
    val = str(val).replace(',', '').replace('$', '').strip()
    try: return float(val)
    except: return None

def parse_single_xml(xml_path):
    try:
        with open(xml_path, 'rb') as f:
            raw = f.read()
        raw = raw.replace(b'\x00', b'')
        root = ET.fromstring(raw)
    except:
        return None

    ns = None
    if root.tag.startswith('{'):
        nsurl = root.tag.split('}')[0][1:]
        ns = {'ns': nsurl}

    def g(xpath): return get_text(root, xpath, ns)

    ein = g("ns:ReturnHeader/ns:Filer/ns:EIN") or g("ReturnHeader/Filer/EIN")
    if not ein: return None

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
    for pattern in [
        "ns:ReturnData/ns:IRS990/ns:OfficerDirectorTrusteeEmplGrp",
        "ns:ReturnData/ns:IRS990/ns:OfficerDirectorTrusteeEmployee",
        "ReturnData/IRS990/OfficerDirectorTrusteeEmplGrp",
        "ReturnData/IRS990/OfficerDirectorTrusteeEmployee"
    ]:
        found = root.findall(pattern, ns) if ns else root.findall(pattern)
        for person in found[:5]:
            name = (get_text(person, "ns:PersonNm", ns) or get_text(person, "PersonName", None))
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
    for pattern in [
        "ns:ReturnData/ns:IRS990ScheduleO/ns:SupplementalInformationDetail/ns:ExplanationTxt",
        "ReturnData/IRS990ScheduleO/SupplementalInformationDetail/ExplanationTxt"
    ]:
        found = root.findall(pattern, ns) if ns else root.findall(pattern)
        for f in found:
            if f.text and len(f.text.strip()) > 20:
                schedule_o.append(f.text.strip())
    schedule_o_text = " | ".join(schedule_o[:2]) if schedule_o else None
    
    return {
        'ein': str(ein).replace('.0', '').strip(),
        'tax_year': tax_year, 'name': org_name,
        'total_revenue': safe_float(total_revenue),
        'contributions': safe_float(contributions),
        'total_expenses': safe_float(total_exp),
        'program_expenses': safe_float(program_exp),
        'mgmt_expenses': safe_float(mgmt_exp),
        'fundraising_expenses': safe_float(fund_exp),
        'total_assets': safe_float(total_assets),
        'net_assets': safe_float(net_assets),
        'employees': employees, 'volunteers': volunteers,
        'mission': mission,
        'program_accomplishments': program_accomplishments,
        'top_officers': top_officers,
        'schedule_o': schedule_o_text,
        'source_file': os.path.basename(xml_path)
    }

if __name__ == '__main__':
    print(f"[AGENT 1b] CPU cores: {cpu_count()}")
    xml_files = glob.glob("data/xml/**/*.xml", recursive=True)
    print(f"[AGENT 1b] Found {len(xml_files)} XML files")
    if len(xml_files) == 0:
        print("[AGENT 1b] No XML files. Check data/xml/")
        sys.exit(1)
    
    workers = max(1, cpu_count() - 1)
    print(f"[AGENT 1b] Parsing with {workers} workers...")
    
    records = []
    errors = 0
    batch_size = max(1, len(xml_files) // (workers * 4))
    
    with Pool(processes=workers) as pool:
        for i, result in enumerate(pool.imap_unordered(parse_single_xml, xml_files, chunksize=batch_size)):
            if i % 1000 == 0 and i > 0:
                print(f"[AGENT 1b] {i}/{len(xml_files)} | Good:{len(records)} | Err:{errors}")
            if result:
                records.append(result)
            else:
                errors += 1
    
    print(f"[AGENT 1b] Done. Good:{len(records)} | Err:{errors}")
    if records:
        keys = records[0].keys()
        with open(OUT, 'w', newline='', encoding='utf-8') as fh:
            writer = csv.DictWriter(fh, fieldnames=keys)
            writer.writeheader()
            writer.writerows(records)
        print(f"[AGENT 1b] Wrote {len(records)} to {OUT}")
    else:
        sys.exit(1)
