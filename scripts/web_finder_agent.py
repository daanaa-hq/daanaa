#!/usr/bin/env python3
"""
Web Finder Agent — discover org websites by domain-pattern guessing,
verified with name-token matching + GPU embeddings.

Strategy (no search engine involved):
1. Query orgs with revenue data but missing websites, revenue DESC
2. Guess candidate domains from the org name (orgname.org, firstword.org, ...)
3. Fetch each candidate (robots.txt respected, identified UA) and verify
   ownership: ≥70% of org-name tokens on page + embedding similarity ≥ 0.5
4. Verified finds saved as website_status='beta' (disclosure policy);
   misses marked 'no_website_found' (re-eligible after 90 days)

GPU: mxbai-embed-large on port 11436 (Vulkan)
CPU: candidate fetching, HTML stripping, name-token matching

Run:
    python3 scripts/web_finder_agent.py --limit 100 --dry-run
    python3 scripts/web_finder_agent.py --limit 1000
"""

import sqlite3
import requests
import re
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np

from website_normalize import normalize_website

DB_PATH = Path.home() / "meritgiving/data/merit_registry.db"
LOG_PATH = Path.home() / "meritgiving/logs/web_finder_50k.log"
EMBED_URL = "http://127.0.0.1:11436/v1/embeddings"
EMBED_MODEL = "mxbai-embed-large"
LLM_URL = "http://127.0.0.1:11437/v1/chat/completions"
LLM_MODEL = "local"

UA = ("Mozilla/5.0 (compatible; DaanaaWebFinder/1.0; "
      "+https://daanaa.org/about) website-discovery")

FETCH_TIMEOUT = 8
MIN_CONFIDENCE = 0.5   # embedding floor; primary gate is the name-token check (≥70%)
LLM_TIMEOUT = 15   # LLM domain guessing timeout

# robots.txt cache, one parser per scheme://host (modeled on donation_link_pipeline)
_robots_cache: dict[str, RobotFileParser] = {}

def can_fetch(url: str) -> bool:
    """Returns False if robots.txt disallows path. Fails open (True) on error."""
    try:
        parsed = urlparse(url)
        base   = f"{parsed.scheme}://{parsed.netloc}"
        if base not in _robots_cache:
            rp = RobotFileParser()
            rp.set_url(base + "/robots.txt")
            try:
                rp.read()
            except Exception:
                pass
            _robots_cache[base] = rp
        return _robots_cache[base].can_fetch(UA, url)
    except Exception:
        return False  # fail closed — can't confirm permission, don't scrape

def log(msg: str):
    ts = datetime.now(timezone.utc).isoformat()
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")

def embed_text(text: str) -> np.ndarray | None:
    """Get embedding via fast GPU 0 server."""
    try:
        resp = requests.post(
            EMBED_URL,
            json={"model": EMBED_MODEL, "input": text},
            timeout=30   # embed shares the GPU with mission gen; 5s timed out under load
        )
        if resp.status_code == 200:
            emb = resp.json()["data"][0]["embedding"]
            return np.array(emb, dtype=np.float32)
        log(f"  Embedding HTTP {resp.status_code}: {resp.text[:120]}")
    except Exception as e:
        log(f"  Embedding error: {e}")
    return None

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two vectors."""
    if a is None or b is None:
        return 0.0
    a_norm = np.linalg.norm(a)
    b_norm = np.linalg.norm(b)
    if a_norm == 0 or b_norm == 0:
        return 0.0
    return float(np.dot(a, b) / (a_norm * b_norm))

STOPWORDS = {'inc', 'incorporated', 'the', 'of', 'for', 'and', 'a', 'an',
             'foundation', 'fund', 'corp', 'corporation', 'assn', 'association',
             'co', 'ltd', 'llc', 'trust'}


def llm_candidate_domains(org_name: str, city: str, state: str) -> list[str]:
    """Second candidate tier (board decision 2026-07-17): ask the local LLM
    for the domains a real org with this name would plausibly register —
    acronyms, abbreviations, shortened forms the token guesser can't produce
    (e.g. "Vermont Land Trust Inc" → vlt.org). Local Qwen on 11437, zero
    external cost. Verification thresholds downstream stay unchanged."""
    try:
        prompt = (
            f'Nonprofit: "{org_name}" in {city or "?"}, {state or "?"}. '
            'List the 4 most plausible website domains this organization would '
            'register, favoring .org, including acronym forms. Reply with ONLY '
            'the bare domains, one per line, no explanations.')
        resp = requests.post(
            LLM_URL,
            json={"model": "qwen", "max_tokens": 80, "temperature": 0.2,
                  "messages": [{"role": "user", "content": prompt}]},
            timeout=20)
        if resp.status_code != 200:
            return []
        text = resp.json()["choices"][0]["message"]["content"]
        out = []
        for line in text.strip().splitlines():
            d = line.strip().lower().strip('-• ').rstrip('/')
            d = re.sub(r'^https?://', '', d).replace('www.', '')
            if re.fullmatch(r'[a-z0-9][a-z0-9-]{1,60}\.(org|com|net|us)', d):
                out.append(d)
        return out[:4]
    except Exception:
        return []  # LLM down (e.g., outside GPU-night window) → heuristics only


def search_website(org_name: str, city: str, state: str) -> list[str]:
    """
    Search for org website candidates. Prioritize .org over .com (nonprofits ~99% use .org).
    Tier 1: heuristic token patterns. Tier 2: LLM-proposed domains (acronyms,
    abbreviations). Ownership verification downstream is unchanged either way.
    """
    candidates = []  # Use list to preserve order; .org first

    # Pattern 1: Direct domain guesses (most orgs use org_name pattern)
    org_clean = org_name.lower().strip().replace(' ', '').replace('-', '').replace('.', '')
    candidates.append(f"{org_clean}.org")
    candidates.append(f"{org_clean}.com")

    # Pattern 2: First word + .org
    first_word = org_name.split()[0].lower().replace('-', '')
    if len(first_word) > 2:
        candidates.append(f"{first_word}.org")

    # Pattern 3: Acronym of significant words (Vermont Land Trust → vlt.org)
    words = [w for w in re.findall(r"[a-zA-Z]+", org_name.lower()) if w not in STOPWORDS]
    if len(words) >= 2:
        acronym = ''.join(w[0] for w in words)
        if 2 <= len(acronym) <= 8:
            candidates.append(f"{acronym}.org")
    # Pattern 3b: Stopword-stripped name (drops Inc/The/Foundation noise)
    if words:
        stripped = ''.join(words)
        if stripped != org_clean:
            candidates.append(f"{stripped}.org")

    # Pattern 4: City + org pattern (e.g., "bostonchildrensmuseum.org")
    if city:
        city_clean = city.lower().replace(' ', '')
        candidates.append(f"{city_clean}{org_clean}.org")

    # Tier 2: LLM-proposed domains (appended after heuristics; dedupe keeps order)
    candidates.extend(llm_candidate_domains(org_name, city, state))

    # Return top candidates to try (deduped, .org-first)
    return list(dict.fromkeys(candidates))[:9]

def llm_domain_guesses(org_name: str, city: str = '', state: str = '') -> list[str]:
    """
    Use Qwen3-30B to generate smart domain guesses (abbreviations, acronyms, shorthands).
    Falls back to empty list on error — pattern-based guessing still runs.
    """
    try:
        context = f"{org_name}"
        if city:
            context += f" in {city}"
        if state:
            context += f", {state}"

        payload = {
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": "You generate likely nonprofit website domain names. Return only a JSON array of domain guesses (no .org/.com extensions, just the domain part). E.g. [\"redcross\", \"americanredcross\", \"arc\"]"},
                {"role": "user", "content": f"Generate 5 likely website domain names for nonprofit: {context}"},
            ],
            "temperature": 0.3,
            "max_tokens": 100,
        }

        resp = requests.post(LLM_URL, json=payload, timeout=LLM_TIMEOUT)
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"].strip()
            # Parse the JSON array
            guesses = json.loads(content)
            if isinstance(guesses, list):
                # Add .org and .com variants, prioritize .org
                candidates = []
                for guess in guesses[:5]:
                    guess_clean = guess.lower().replace(' ', '').replace('-', '')
                    candidates.append(f"{guess_clean}.org")
                    candidates.append(f"{guess_clean}.com")
                return list(dict.fromkeys(candidates))  # Dedupe, preserve .org-first order
    except Exception as e:
        pass  # fail gracefully; pattern-based search will still run

    return []

def fetch_website_text(url: str) -> str | None:
    """Fetch website homepage and extract text."""
    try:
        # Ensure URL has scheme
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"

        if not can_fetch(url):
            return None  # robots.txt disallows — respect it

        resp = requests.get(url, timeout=FETCH_TIMEOUT, allow_redirects=True,
                            headers={"User-Agent": UA, "Accept": "text/html,*/*"})
        if resp.status_code == 200:
            # Extract text from HTML (basic)
            text = resp.text.lower()
            # Drop script/style bodies — code noise, and it pushed token counts
            # past the embed server's 512-token batch limit (HTTP 500)
            text = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', text, flags=re.DOTALL)
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', ' ', text)
            # Remove extra whitespace
            text = ' '.join(text.split())
            return text[:1200]  # ≤~450 tokens, safely under the embed batch limit
    except Exception as e:
        pass
    return None

def _name_token_ratio(org_name: str, page_text: str) -> float:
    """Share of meaningful org-name words that appear on the page.
    Deterministic and explainable: a real org homepage names the org."""
    stop = {'the', 'inc', 'incorporated', 'corp', 'corporation', 'foundation',
            'fund', 'assn', 'association', 'and', 'for', 'of'}
    tokens = [t for t in re.findall(r'[a-z]+', org_name.lower())
              if len(t) > 2 and t not in stop]
    if not tokens:
        return 0.0
    return sum(1 for t in tokens if t in page_text) / len(tokens)

def llm_verify_website(org_name: str, website_url: str, website_text: str) -> bool:
    """
    Use LLM to verify website ownership. Final gate to catch false positives:
    - Spanish language sites, unrelated orgs with similar names, generic company sites.
    Returns True if LLM confirms this is the org's official website.
    """
    try:
        payload = {
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": "You are a website verification expert. Given an organization name and website content, determine if the website is the official website for that organization. Respond with only 'YES' or 'NO'."},
                {"role": "user", "content": f"Is {website_url} the official website for '{org_name}'? Here is the page content: {website_text[:500]}"},
            ],
            "temperature": 0.0,
            "max_tokens": 5,
        }

        resp = requests.post(LLM_URL, json=payload, timeout=LLM_TIMEOUT)
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"].strip().upper()
            return "YES" in content
    except Exception as e:
        log(f"  LLM verification error: {e}")

    return False  # Fail closed — uncertain, don't verify

def verify_website_ownership(org_record: dict, website_url: str) -> tuple[bool, float]:
    """
    Verify the website belongs to the org. Three gates, all required:
    1. Name-token check: ≥70% of meaningful org-name words appear on the page
    2. Embedding similarity ≥ 0.5 between org identity and page text
    3. LLM confirmation: "Is this the official website?" (catches false positives)
    Returns (is_verified, confidence_score)
    """
    org_name = org_record['organization_name']

    # Fetch page first — cheapest signal
    website_text = fetch_website_text(website_url)
    if website_text is None:
        return False, 0.0

    name_ratio = _name_token_ratio(org_name, website_text)
    if name_ratio < 0.7:
        log(f"    Verified: False (name tokens on page: {name_ratio:.0%})")
        return False, 0.0

    org_address = f"{org_name} {org_record.get('CITY', '')} {org_record.get('STATE', '')}"
    org_emb = embed_text(org_address)
    website_emb = embed_text(website_text)
    similarity = cosine_similarity(org_emb, website_emb)

    if similarity < MIN_CONFIDENCE:
        log(f"    Verified: False (embedding similarity: {similarity:.3f}, below {MIN_CONFIDENCE})")
        return False, 0.0

    # Final gate: LLM verification
    llm_confirmed = llm_verify_website(org_name, website_url, website_text)
    is_verified = llm_confirmed
    log(f"    Verified: {is_verified} (name tokens: {name_ratio:.0%}, similarity: {similarity:.3f}, llm: {llm_confirmed})")
    return is_verified, similarity

def process_org(ein: str, name: str, city: str, state: str, revenue: float, dry_run: bool) -> dict:
    """Process a single org: guess candidates, fetch, verify, save. Returns result dict."""
    result = {'ein': ein, 'name': name, 'verified': False, 'candidate': None, 'error': None}

    try:
        # Get candidates: LLM guesses + pattern-based guesses
        llm_candidates = llm_domain_guesses(name, city or '', state or '')
        pattern_candidates = search_website(name, city or '', state or '')
        candidates = list(dict.fromkeys(llm_candidates + pattern_candidates))  # dedupe, preserve order

        if not candidates:
            result['error'] = 'no candidates'
            return result

        # Try each candidate until we find a verified match
        for candidate in candidates:
            website_text = fetch_website_text(candidate)
            if website_text is None:
                continue

            is_verified, confidence = verify_website_ownership(
                {'EIN': ein, 'organization_name': name, 'CITY': city, 'STATE': state},
                candidate
            )

            if is_verified:
                result['verified'] = True
                result['candidate'] = normalize_website(candidate)
                result['confidence'] = confidence
                return result

    except Exception as e:
        result['error'] = str(e)

    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=100)
    parser.add_argument('--workers', type=int, default=8)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--priority', choices=['high-revenue', 'all'], default='high-revenue')
    args = parser.parse_args()

    log("━" * 70)
    log(f"Web Finder Agent — Priority: {args.priority}, Workers: {args.workers}")

    # isolation_level=None = autocommit; each UPDATE is its own transaction.
    conn = sqlite3.connect(DB_PATH, isolation_level=None, timeout=30)
    c = conn.cursor()

    # Query orgs: have revenue, missing website, ordered by revenue DESC.
    if args.priority == 'high-revenue':
        query = """
            SELECT EIN, organization_name, CITY, STATE, total_revenue
            FROM registry_enriched
            WHERE deductibility = '1'
              AND total_revenue > 100000
              AND (website IS NULL OR website = '')
              AND (website_checked_at IS NULL
                   OR website_checked_at < datetime('now', '-90 days'))
            ORDER BY total_revenue DESC
            LIMIT ?
        """
    else:
        query = """
            SELECT EIN, organization_name, CITY, STATE, total_revenue
            FROM registry_enriched
            WHERE deductibility = '1'
              AND (website IS NULL OR website = '')
              AND (website_checked_at IS NULL
                   OR website_checked_at < datetime('now', '-90 days'))
            ORDER BY total_revenue DESC
            LIMIT ?
        """

    orgs = c.execute(query, (args.limit,)).fetchall()
    log(f"Found {len(orgs)} orgs to process")

    if args.dry_run:
        log("DRY RUN — not saving results")

    verified = 0
    processed = 0

    # Process orgs in parallel
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(process_org, ein, name, city, state, revenue, args.dry_run): (ein, name, revenue)
            for ein, name, city, state, revenue in orgs
        }

        for i, future in enumerate(as_completed(futures), 1):
            ein, name, revenue = futures[future]
            try:
                result = future.result()
                log(f"\n[{i}/{len(orgs)}] {name} (${revenue:,.0f})")

                if result['verified']:
                    log(f"  ✓ Verified! {result['candidate']} (confidence: {result['confidence']:.3f})")
                    if not args.dry_run:
                        c.execute("""
                            UPDATE registry_enriched
                            SET website = ?, website_status = 'beta', website_checked_at = datetime('now')
                            WHERE EIN = ?
                        """, (result['candidate'], ein))
                    verified += 1
                else:
                    log(f"  ✗ No verified website found")
                    if not args.dry_run:
                        c.execute("""
                            UPDATE registry_enriched
                            SET website_status = 'no_website_found', website_checked_at = datetime('now')
                            WHERE EIN = ?
                        """, (ein,))

                processed += 1

            except Exception as e:
                log(f"[{i}/{len(orgs)}] {name}: ERROR - {e}")
                processed += 1

    conn.close()

    log(f"\n━ Summary ━")
    log(f"Processed: {processed}")
    log(f"Verified: {verified}")
    log(f"Coverage gain: +{verified} websites")

if __name__ == "__main__":
    main()
