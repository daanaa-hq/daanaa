#!/usr/bin/env python3
import json, requests, time
from pathlib import Path
from collections import defaultdict

BASE = Path.home() / "meritgiving"
OLLAMA_URL = "http://localhost:11434/api/generate"

def ollama_classify(name, city, state, mission=""):
    prompt = f"""You are an IRS NTEE code classifier. Output ONLY the 3-character NTEE code. No explanation. No punctuation. Just 3 letters/numbers.

Examples:
- Houston Symphony Society, Houston, TX -> A69
- United Way of Greater Houston, Houston, TX -> T70
- Houston Food Bank, Houston, TX -> K31
- Houston Museum of Natural Science, Houston, TX -> A50
- Memorial Hermann Hospital, Houston, TX -> E20
- Houston SPCA, Houston, TX -> D60

Organization: {name}
City: {city}
State: {state}
{f'Mission: {mission[:200]}' if mission else ''}

NTEE Code (3 chars only):"""
    
    try:
        r = requests.post(OLLAMA_URL, json={
            "model": "qwen2.5:14b",
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": 10, "temperature": 0.0, "top_p": 0.1}
        }, timeout=30)
        result = r.json().get('response', '').strip()
        clean = ''.join(c for c in result if c.isalnum()).upper()[:3]
        if len(clean) >= 2 and clean[0].isalpha():
            return clean
        return None
    except:
        return None

def main():
    with open(BASE / "data/xml_extracted.json") as f:
        data = json.load(f)
    
    try:
        with open(BASE / "data/ntee_fixes.json") as f:
            existing = json.load(f)
    except:
        existing = {}
    
    pending = []
    for ein, org in data.items():
        ntee = str(org.get('NTEE', '')).strip().upper()
        if (not ntee or ntee in ['NON', 'NONE', '']) and ein not in existing:
            pending.append({
                'ein': ein,
                'name': org.get('NAME', ''),
                'city': org.get('CITY', ''),
                'state': org.get('STATE', ''),
                'mission': org.get('MISSION', '')
            })
    
    print(f"Orgs needing NTEE classification: {len(pending)}")
    if not pending:
        print("Nothing to do!")
        return
    
    batch_size = 100
    results = dict(existing)
    start_time = time.time()
    
    for i, org in enumerate(pending):
        result = ollama_classify(org['name'], org['city'], org['state'], org['mission'])
        if result:
            results[org['ein']] = result
        
        if (i + 1) % batch_size == 0:
            with open(BASE / "data/ntee_fixes.json", "w") as f:
                json.dump(results, f, indent=2)
            
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed * 60
            remaining_hours = (len(pending) - i - 1) / (rate / 60) if rate > 0 else 0
            print(f"  {i+1}/{len(pending)} | {rate:.0f}/min | ETA: {remaining_hours:.1f}h")
    
    with open(BASE / "data/ntee_fixes.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Done. Total fixes: {len(results)}")

if __name__ == "__main__":
    main()
