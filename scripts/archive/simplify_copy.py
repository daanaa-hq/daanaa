#!/usr/bin/env python3
"""
Copy simplification audit — uses Ollama (qwen2.5:14b) to flag jargon
in all .tsx files and suggest plain-English alternatives.

Output: data/copy_suggestions.json
"""

import json, re, subprocess, time
from pathlib import Path

PAGES_DIR = Path.home() / "meritgiving/frontend/src/pages"
COMPONENTS_DIR = Path.home() / "meritgiving/frontend/src/components"
OUT_PATH = Path.home() / "meritgiving/data/copy_suggestions.json"

# Regex: captures quoted strings that look like real user copy (not CSS/SVG)
TEXT_RE = re.compile(r'(?<![a-zA-Z])>([A-Z][^<{]{8,}[a-z.!?])</|"([A-Z][^"]{8,}[a-z.!?])"')
CSS_SKIP = re.compile(r'font-|text-|flex|grid|border|bg-|rounded|px-|py-|gap-|items-|hidden|block|stroke|fill|viewBox|className|opacity|tracking|leading|shadow|hover|transition|duration|cursor|translate|overflow|absolute|relative|fixed|pointer|animate|aspect|shrink|grow|z-[0-9]')

def extract_strings(tsx_path: Path) -> list[str]:
    content = tsx_path.read_text(errors='ignore')
    seen = set()
    results = []
    for m in TEXT_RE.finditer(content):
        text = (m.group(1) or m.group(2) or '').strip()
        if not text or len(text) < 10 or len(text) > 200:
            continue
        if CSS_SKIP.search(text):
            continue
        if text in seen:
            continue
        seen.add(text)
        results.append(text)
    return results

def ask_ollama(text: str) -> dict:
    prompt = (
        f'Is this phrase jargon or hard to understand for a general audience?\n'
        f'Phrase: "{text}"\n\n'
        f'Reply with JSON only, no explanation:\n'
        f'{{"is_jargon": true/false, "reason": "one sentence", "plain_alternative": "simpler version or null"}}\n'
    )
    try:
        result = subprocess.run(
            ['ollama', 'run', 'qwen2.5:14b', prompt],
            capture_output=True, text=True, timeout=30
        )
        raw = result.stdout.strip()
        # Extract JSON from response
        json_match = re.search(r'\{[^}]+\}', raw, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception:
        pass
    return {"is_jargon": False, "reason": "parse error", "plain_alternative": None}

def main():
    all_strings = {}
    for tsx in list(PAGES_DIR.glob("*.tsx")) + list(COMPONENTS_DIR.glob("*.tsx")):
        strings = extract_strings(tsx)
        if strings:
            all_strings[tsx.name] = strings

    total = sum(len(v) for v in all_strings.values())
    print(f"Found {total} candidate strings across {len(all_strings)} files")

    suggestions = {}
    done = 0
    t0 = time.time()

    for filename, strings in all_strings.items():
        suggestions[filename] = []
        for text in strings:
            result = ask_ollama(text)
            done += 1
            if result.get("is_jargon"):
                suggestions[filename].append({
                    "original": text,
                    "plain": result.get("plain_alternative"),
                    "reason": result.get("reason"),
                })
            if done % 10 == 0:
                elapsed = time.time() - t0
                print(f"  {done}/{total} checked ({elapsed:.0f}s)...")

    # Write output — only files with actual jargon hits
    output = {k: v for k, v in suggestions.items() if v}
    with open(OUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    total_flags = sum(len(v) for v in output.values())
    print(f"\nDone. {total_flags} jargon phrases flagged across {len(output)} files.")
    print(f"Results: {OUT_PATH}")

    # Print summary
    for fname, items in output.items():
        print(f"\n── {fname} ({len(items)} flags) ──")
        for item in items:
            print(f"  ORIGINAL: {item['original']}")
            print(f"  PLAIN:    {item['plain']}")
            print()

if __name__ == "__main__":
    main()
