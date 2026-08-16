#!/usr/bin/env python3
"""
MERIT Worker D — GPU NTEE Classifier via Ollama
Classifies missing NTEE codes using local LLM on RX 7900 XTX.
"""
import sqlite3, requests, time
from pathlib import Path
from datetime import datetime

BASE = Path.home() / "meritgiving"
DATA = BASE / "data"
LOGS = BASE / "logs"
LOGS.mkdir(parents=True, exist_ok=True)

STATE_DB = DATA / "merit_state.db"
OLLAMA_URL = "http://localhost:11434/api/generate"

PROMPT = """Classify this nonprofit into ONE IRS NTEE major group letter (A-Z).
Respond with ONLY the single uppercase letter. No punctuation.

Name: {name}
City: {city}
State: {state}
Letter:"""

def log(msg):
    ts = datetime.now().isoformat()
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOGS / "worker_d.log", "a") as f:
        f.write(line + "\n")

def get_missing_ntee(limit=500):
    conn = sqlite3.connect(STATE_DB)
    c = conn.cursor()
    c.execute("""
        SELECT ein, name, city, state FROM orgs 
        WHERE (ntee_code IS NULL OR ntee_code = '') 
        AND sources LIKE '%propublica%' AND name IS NOT NULL
        LIMIT ?
    """, (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

def classify(name, city, state, model="mistral"):
    try:
        r = requests.post(OLLAMA_URL, json={
            "model": model, "prompt": PROMPT.format(name=name, city=city, state=state),
            "stream": False, "options": {"temperature": 0.1, "num_predict": 3}
        }, timeout=30)
        if r.status_code == 200:
            resp = r.json().get("response", "").strip().upper()
            for ch in resp:
                if 'A' <= ch <= 'Z':
                    return ch
        return None
    except Exception as e:
        log(f"Ollama error: {e}")
        return None

def update_ntee(ein, letter):
    conn = sqlite3.connect(STATE_DB)
    c = conn.cursor()
    c.execute("UPDATE orgs SET ntee_code = ? WHERE ein = ?", (letter, ein))
    conn.commit()
    conn.close()

def main():
    log("=== Worker D: GPU Classifier Started ===")
    
    # Check Ollama
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        models = [m.get("name","") for m in r.json().get("models",[])]
        log(f"Ollama models: {models}")
    except Exception as e:
        log(f"Ollama unreachable: {e}")
        return
    
    total = 0
    while True:
        rows = get_missing_ntee(limit=500)
        if not rows:
            break
        log(f"Batch: {len(rows)} orgs to classify...")
        batch_ok = 0
        for ein, name, city, state in rows:
            letter = classify(name, city, state)
            if letter:
                update_ntee(ein, letter)
                batch_ok += 1
            time.sleep(0.02)
        total += batch_ok
        log(f"Classified {batch_ok}/{len(rows)}. Total: {total}")
        if len(rows) < 500:
            break
    
    log(f"=== Worker D: Finished. Total classified: {total} ===")

if __name__ == "__main__":
    main()
