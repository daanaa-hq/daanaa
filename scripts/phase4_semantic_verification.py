#!/usr/bin/env python3
"""
Phase 4: Semantic Verification — GPU-accelerated embedding-based verification
of web candidates against known nonprofit embeddings.

Strategy:
1. Load reference embeddings from registry_enriched orgs that have websites
2. For each org missing a website (and revenue > $100K):
   a. Generate 5-10 domain candidates via heuristics
   b. Fetch homepage text (HTTP GET, respecting robots.txt)
   c. Compute embedding of fetched text
   d. Compute cosine similarity against nonprofit reference embeddings
   e. Mark as semantic_match=1 if similarity > 0.75
3. Batch-save results; log progress to /tmp/phase4_progress.log

GPU: mxbai-embed-large on port 11436 (Vulkan)
Run in background with checkpoint resumption.

Usage:
    python3 scripts/phase4_semantic_verification.py --limit 50000 --workers 16
    python3 scripts/phase4_semantic_verification.py --limit 10000 --workers 8 --dry-run
"""

import sqlite3
import requests
import re
import argparse
import json
import time
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import threading

DB_PATH = Path.home() / "meritgiving/data/merit_registry.db"
CHECKPOINT_PATH = Path.home() / "meritgiving/logs/phase4_checkpoint.json"
PROGRESS_LOG = Path("/tmp/phase4_progress.log")
EMBED_URL = "http://127.0.0.1:11436/embedding"  # GPU-accelerated llama-server endpoint
EMBED_MODEL = "mxbai-embed-large"

UA = ("Mozilla/5.0 (compatible; DaanaaWebFinder/1.0; "
      "+https://daanaa.org) semantic-verification")

FETCH_TIMEOUT = 8
SIMILARITY_THRESHOLD = 0.75
BATCH_SIZE = 100

_robots_cache: dict[str, RobotFileParser] = {}
_stats_lock = threading.Lock()
_stats = {
    "processed": 0,
    "verified": 0,
    "fetched": 0,
    "embed_errors": 0,
    "timestamp": datetime.now(timezone.utc).isoformat()
}

def log(msg: str, to_progress=True):
    """Log to stdout and optionally to progress file."""
    ts = datetime.now(timezone.utc).isoformat()
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    if to_progress:
        with open(PROGRESS_LOG, "a") as f:
            f.write(line + "\n")

def load_checkpoint() -> dict:
    """Load resume checkpoint if exists."""
    if CHECKPOINT_PATH.exists():
        try:
            with open(CHECKPOINT_PATH) as f:
                return json.load(f)
        except Exception as e:
            log(f"Checkpoint read error: {e}", to_progress=False)
    return {"processed_eins": set(), "start_time": datetime.now(timezone.utc).isoformat()}

def save_checkpoint(checkpoint: dict):
    """Persist checkpoint."""
    checkpoint["processed_eins"] = list(checkpoint["processed_eins"])
    checkpoint["timestamp"] = datetime.now(timezone.utc).isoformat()
    with open(CHECKPOINT_PATH, "w") as f:
        json.dump(checkpoint, f, indent=2)

def can_fetch(url: str) -> bool:
    """Check robots.txt. Fail closed."""
    try:
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
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
        return False

def embed_text(text: str) -> np.ndarray | None:
    """Get embedding via GPU-accelerated llama-server endpoint."""
    try:
        resp = requests.post(
            EMBED_URL,
            json={"content": text},
            timeout=30
        )
        if resp.status_code == 200:
            data = resp.json()
            # llama-server format: [{"index": 0, "embedding": [[1024-dim vector]]}]
            if isinstance(data, list) and len(data) > 0:
                item = data[0]
                if "embedding" in item and len(item["embedding"]) > 0:
                    emb = item["embedding"][0]  # Extract from nested list
                    return np.array(emb, dtype=np.float32)
        with _stats_lock:
            _stats["embed_errors"] += 1
    except Exception as e:
        with _stats_lock:
            _stats["embed_errors"] += 1
    return None

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity, safe."""
    if a is None or b is None:
        return 0.0
    a_norm = np.linalg.norm(a)
    b_norm = np.linalg.norm(b)
    if a_norm == 0 or b_norm == 0:
        return 0.0
    return float(np.dot(a, b) / (a_norm * b_norm))

def fetch_homepage_text(domain: str) -> str | None:
    """Fetch homepage and extract text."""
    try:
        if not domain.startswith(('http://', 'https://')):
            url = f"https://{domain}"
        else:
            url = domain

        if not can_fetch(url):
            return None

        resp = requests.get(url, timeout=FETCH_TIMEOUT, allow_redirects=True,
                           headers={"User-Agent": UA, "Accept": "text/html,*/*"})
        if resp.status_code == 200:
            text = resp.text.lower()
            # Strip script/style
            text = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', text, flags=re.DOTALL)
            # Strip tags
            text = re.sub(r'<[^>]+>', ' ', text)
            # Normalize whitespace
            text = ' '.join(text.split())
            return text[:1200]
    except Exception:
        pass
    return None

def generate_candidates(org_name: str, city: str = "") -> list[str]:
    """Generate 5-10 domain candidates."""
    candidates = []
    name = org_name.strip().lower()
    city = (city or "").strip().lower()

    # Remove common suffixes
    core = name
    for suffix in [' inc', ' llc', ' ltd', ' foundation', ' association', ' group',
                   ' partners', ' healthcare', ' hospital', ' university', ' college',
                   ' school', ' center', ' centre', ' institute', ' corp', ' co.']:
        if core.endswith(suffix):
            core = core[:-len(suffix)].strip()

    # Pattern 1: Full name
    clean = ''.join(core.split())
    candidates.extend([f"{clean}.org", f"{clean}.com"])

    # Pattern 2: Initials
    initials = ''.join(w[0] for w in core.split() if w)
    if len(initials) > 1:
        candidates.extend([f"{initials}.org", f"{initials}.com"])

    # Pattern 3: First + Last word
    words = core.split()
    if len(words) >= 2:
        first_last = words[0] + words[-1]
        candidates.extend([f"{first_last}.org", f"{first_last}.com"])

    # Pattern 4: City + name
    if city and len(city) > 2:
        city_org = city + clean
        candidates.append(f"{city_org}.org")

    # Pattern 5: First word
    if words:
        first = words[0]
        candidates.extend([f"{first}.org", f"{first}.com"])

    return list(dict.fromkeys(candidates))[:10]

def verify_candidate(
    ein: str, org_name: str, city: str,
    reference_embeddings: list[np.ndarray]
) -> tuple[bool, float]:
    """
    Verify a single org's candidates against reference nonprofit embeddings.
    Returns (verified, best_similarity).
    """
    candidates = generate_candidates(org_name, city)
    best_similarity = 0.0

    for candidate in candidates:
        text = fetch_homepage_text(candidate)
        if text is None:
            continue

        with _stats_lock:
            _stats["fetched"] += 1

        # Compute embedding
        emb = embed_text(text)
        if emb is None:
            continue

        # Compute max similarity against all reference embeddings
        similarities = [cosine_similarity(emb, ref) for ref in reference_embeddings]
        max_sim = max(similarities) if similarities else 0.0

        if max_sim > best_similarity:
            best_similarity = max_sim

        if max_sim >= SIMILARITY_THRESHOLD:
            return True, max_sim

    return False, best_similarity

def process_batch(batch: list, reference_embeddings: list[np.ndarray]) -> list[dict]:
    """Process a batch of orgs."""
    results = []
    for ein, org_name, city in batch:
        try:
            verified, similarity = verify_candidate(ein, org_name, city, reference_embeddings)
            results.append({
                "ein": ein,
                "verified": verified,
                "similarity": similarity
            })
            with _stats_lock:
                _stats["processed"] += 1
                if verified:
                    _stats["verified"] += 1
        except Exception as e:
            log(f"Error processing {ein}: {e}", to_progress=False)
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=10000)
    parser.add_argument('--workers', type=int, default=8)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    log("=" * 70)
    log(f"Phase 4 Semantic Verification — Limit: {args.limit}, Workers: {args.workers}")

    # Load checkpoint
    checkpoint = load_checkpoint()
    processed_eins = set(checkpoint.get("processed_eins", []))
    log(f"Resuming from checkpoint: {len(processed_eins)} already processed")

    conn = sqlite3.connect(DB_PATH, timeout=30)
    c = conn.cursor()

    # Load reference embeddings from orgs that have websites
    log("Loading reference embeddings...")
    c.execute("""
        SELECT org_embeddings.EIN, org_embeddings.vector
        FROM org_embeddings
        JOIN registry_enriched ON org_embeddings.EIN = registry_enriched.EIN
        WHERE registry_enriched.website IS NOT NULL
          AND registry_enriched.website != ''
          AND registry_enriched.deductibility = '1'
        LIMIT 10000
    """)

    reference_embeddings = []
    ref_count = 0
    for ein, vec_blob in c.fetchall():
        try:
            emb_array = np.frombuffer(vec_blob, dtype=np.float32)
            reference_embeddings.append(emb_array)
            ref_count += 1
        except Exception:
            pass

    log(f"Loaded {ref_count} reference nonprofit embeddings")

    if not reference_embeddings:
        log("ERROR: No reference embeddings found. Ensure org_embeddings table is populated.")
        return

    # Query orgs needing verification
    log("Querying orgs to verify...")
    c.execute("""
        SELECT EIN, organization_name, CITY
        FROM registry_enriched
        WHERE deductibility = '1'
          AND total_revenue > 100000
          AND (website IS NULL OR website = '')
          AND (website_checked_at IS NULL
               OR website_checked_at < datetime('now', '-90 days'))
        ORDER BY total_revenue DESC
        LIMIT ?
    """, (args.limit,))

    rows = c.fetchall()
    to_process = [row for row in rows if row[0] not in processed_eins]
    log(f"Found {len(rows)} candidates; {len(to_process)} new after checkpoint")

    if args.dry_run:
        log("DRY RUN — not saving results")

    # Process in batches
    batch_results = []
    for i in range(0, len(to_process), BATCH_SIZE):
        batch = to_process[i:i+BATCH_SIZE]
        results = process_batch(batch, reference_embeddings)
        batch_results.extend(results)

        # Update checkpoint every batch
        checkpoint["processed_eins"] = list(processed_eins) + [r["ein"] for r in batch_results]
        save_checkpoint(checkpoint)

        # Batch update if not dry-run
        if not args.dry_run and batch_results:
            for result in batch_results:
                if result["verified"]:
                    c.execute("""
                        UPDATE registry_enriched
                        SET website_status = 'beta', website_checked_at = datetime('now')
                        WHERE EIN = ?
                    """, (result["ein"],))
            conn.commit()
            batch_results = []

        # Log progress
        with _stats_lock:
            elapsed = (datetime.now(timezone.utc).isoformat() - _stats["timestamp"])
            log(f"Progress: {_stats['processed']}/{len(to_process)} "
                f"(verified: {_stats['verified']}, fetched: {_stats['fetched']}, "
                f"embed_errors: {_stats['embed_errors']})")

    conn.close()

    # Final stats
    log("=" * 70)
    with _stats_lock:
        log(f"Phase 4 Complete")
        log(f"  Processed: {_stats['processed']}")
        log(f"  Verified: {_stats['verified']} (gain: +{_stats['verified']} websites)")
        log(f"  Fetched: {_stats['fetched']} candidates")
        log(f"  Embed errors: {_stats['embed_errors']}")

if __name__ == "__main__":
    main()
