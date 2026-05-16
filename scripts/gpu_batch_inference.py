#!/usr/bin/env python3
import json, requests, sys, time
from pathlib import Path
from collections import defaultdict

BASE = Path.home() / "meritgiving"
OLLAMA_URL = "http://localhost:11434/api/generate"

def ollama_generate(prompt, model="qwen2.5:14b", max_tokens=10):
    try:
        r = requests.post(OLLAMA_URL, json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": 0.0, "top_p": 0.1}
        }, timeout=30)
        return r.json().get('response', '').strip()
    except Exception as e:
        return f"ERROR: {e}"

def classify_ntee(org_name, city, state, mission=""):
    prompt = f"""You are an IRS NTEE code classifier. Output ONLY a 3-character NTEE code. No explanation. No punctuation. Just 3 letters/numbers.

Examples:
- Houston Symphony Society, Houston, TX -> A69
- United Way of Greater Houston, Houston, TX -> T70
- Houston Food Bank, Houston, TX -> K31
- Houston Museum of Natural Science, Houston, TX -> A50
- Memorial Hermann Hospital, Houston, TX -> E20
- Houston SPCA, Houston, TX -> D60

Organization: {org_name}
City: {city}
State: {state}
{f'Mission: {mission}' if mission else ''}

NTEE Code (3 chars only):"""
    return prompt

def main():
    # Test with known org first
    test_prompt = classify_ntee("Houston Symphony Society", "Houston", "TX")
    result = ollama_generate(test_prompt)
    print(f"Test: Houston Symphony Society -> {result}")
    if result != "A69":
        print("WARNING: Model not accurate enough. Consider using deepseek-r1:14b for reasoning.")
        print("Available models:")
        r = requests.get("http://localhost:11434/api/tags")
        for m in r.json().get('models', []):
            print(f"  - {m['name']}")
        return
    
    # Load orgs needing NTEE
    print("Loading missing NTEE orgs...")
    with open(BASE / "data/ntee_fixes.json") as f:
        existing_fixes = json.load(f)
    
    # Also load from cache directly
    cache_dir = BASE / "data/propublica_cache"
    pending = []
    for f in cache_dir.glob("*.json"):
        try:
            with open(f) as fh:
                d = json.load(fh)
            org = d.get('organization', {})
            ein = str(org.get('ein', '')).strip()
            ntee = str(org.get('ntee_code', '')).strip().upper()
            if ein and (not ntee or ntee in ['NON', 'NONE', '']) and ein not in existing_fixes:
                pending.append({
                    'ein': ein,
                    'name': org.get('name', ''),
                    'city': org.get('city', ''),
                    'state': org.get('state', ''),
                    'mission': org.get('mission', '')
                })
        except:
            pass
    
    print(f"Pending orgs for GPU classification: {len(pending)}")
    if not pending:
        print("No pending orgs — all done!")
        return
    
    # Batch process
    results = {}
    batch_size = 100  # Process 100, then save checkpoint
    for i, org in enumerate(pending):
        prompt = classify_ntee(org['name'], org['city'], org['state'], org['mission'])
        result = ollama_generate(prompt)
        
        # Clean result — take first 3 alphanumeric chars
        clean = ''.join(c for c in result if c.isalnum()).upper()[:3]
        if len(clean) == 3:
            results[org['ein']] = clean
        
        if (i + 1) % batch_size == 0:
            # Merge with existing and save checkpoint
            existing_fixes.update(results)
            with open(BASE / "data/ntee_fixes.json", "w") as f:
                json.dump(existing_fixes, f, indent=2)
            print(f"  Processed {i+1}/{len(pending)} — checkpoint saved")
            results = {}  # Reset batch buffer
    
    # Final save
    existing_fixes.update(results)
    with open(BASE / "data/ntee_fixes.json", "w") as f:
        json.dump(existing_fixes, f, indent=2)
    
    print(f"Done. Total fixes: {len(existing_fixes)}")

if __name__ == "__main__":
    main()
