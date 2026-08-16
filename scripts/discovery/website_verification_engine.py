#!/usr/bin/env python3
"""
Semantic Website Verification Engine
Validates discovered websites using GPU embeddings.
- Scrapes website content
- Embeds org profile + website content
- Compares similarity to confirm real match
- Flags false positives
"""

import sqlite3
import json
import logging
import time
import requests
import numpy as np
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
import urllib.parse

DB = Path.home() / "meritgiving/data/merit_registry.db"
LOG_DIR = Path.home() / "meritgiving/logs"
VERIFIED_FILE = LOG_DIR / "website_verification_results.jsonl"
VERIFICATION_STATS = LOG_DIR / "verification_stats.json"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] VERIFY: %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "website_verification.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

@dataclass
class Verification:
    ein: str
    org_name: str
    website: str
    status: str  # "VERIFIED", "SUSPICIOUS", "ERROR"
    confidence: float
    reason: str
    timestamp: str

class WebsiteVerifier:
    """Verify discovered websites using semantic validation."""

    def __init__(self):
        self.results = []
        self.stats = {
            "total_tested": 0,
            "verified": 0,
            "suspicious": 0,
            "errors": 0,
            "avg_confidence": 0.0,
        }
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.session.timeout = 10

    def scrape_website(self, url):
        """Scrape website text content."""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text
            text = soup.get_text()

            # Clean up
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            return text[:2000]  # First 2000 chars
        except Exception as e:
            logger.debug(f"Scrape error for {url}: {e}")
            return None

    def embed_text(self, text):
        """Generate embedding via llama-server on port 11436."""
        try:
            response = requests.post(
                'http://127.0.0.1:11436/v1/embeddings',
                json={"input": text, "model": "mxbai-embed-large"},
                timeout=30
            )
            response.raise_for_status()
            embedding = response.json()['data'][0]['embedding']
            return np.array(embedding, dtype=np.float32)
        except Exception as e:
            logger.debug(f"Embedding error: {e}")
            return None

    def cosine_similarity(self, a, b):
        """Compute cosine similarity between embeddings."""
        if a is None or b is None:
            return 0.0
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8)

    def verify_single(self, ein, org_name, website):
        """Verify a single discovered website."""
        self.stats["total_tested"] += 1

        # Scrape website
        website_text = self.scrape_website(website)
        if not website_text:
            self.results.append(Verification(
                ein=ein,
                org_name=org_name,
                website=website,
                status="ERROR",
                confidence=0.0,
                reason="Failed to scrape website",
                timestamp=datetime.now(timezone.utc).isoformat()
            ))
            self.stats["errors"] += 1
            return

        # Embed org profile (name + mission)
        org_profile = f"{org_name}"  # Could add mission here if available
        org_embedding = self.embed_text(org_profile)

        # Embed website content
        website_embedding = self.embed_text(website_text)

        if org_embedding is None or website_embedding is None:
            self.results.append(Verification(
                ein=ein,
                org_name=org_name,
                website=website,
                status="ERROR",
                confidence=0.0,
                reason="Embedding generation failed",
                timestamp=datetime.now(timezone.utc).isoformat()
            ))
            self.stats["errors"] += 1
            return

        # Compare similarity
        similarity = self.cosine_similarity(org_embedding, website_embedding)

        # Heuristic: similarity > 0.6 = verified, 0.4-0.6 = suspicious, <0.4 = likely false positive
        if similarity > 0.65:
            status = "VERIFIED"
            self.stats["verified"] += 1
            reason = f"High semantic match (similarity: {similarity:.3f})"
        elif similarity > 0.45:
            status = "SUSPICIOUS"
            self.stats["suspicious"] += 1
            reason = f"Moderate semantic match (similarity: {similarity:.3f}) - manual review recommended"
        else:
            status = "SUSPICIOUS"
            self.stats["suspicious"] += 1
            reason = f"Low semantic match (similarity: {similarity:.3f}) - likely false positive"

        self.results.append(Verification(
            ein=ein,
            org_name=org_name,
            website=website,
            status=status,
            confidence=similarity,
            reason=reason,
            timestamp=datetime.now(timezone.utc).isoformat()
        ))

        # Update average confidence
        total_confidence = sum(r.confidence for r in self.results)
        self.stats["avg_confidence"] = total_confidence / len(self.results)

    def run(self, limit=5000, workers=4):
        """Run verification on discovered websites."""
        logger.info("=" * 80)
        logger.info("SEMANTIC WEBSITE VERIFICATION ENGINE")
        logger.info("=" * 80)

        # Load recent discoveries
        discoveries = []
        try:
            with open(LOG_DIR / "unified_discovery_results.jsonl", 'r') as f:
                for line in f:
                    try:
                        record = json.loads(line)
                        discoveries.append((record['ein'], record['org_name'], record['website']))
                        if len(discoveries) >= limit:
                            break
                    except:
                        pass
        except:
            logger.error("No discovery results found. Run discovery pipeline first.")
            return

        logger.info(f"Verifying {len(discoveries)} discovered websites...")
        start = time.time()

        # Parallel verification
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [
                executor.submit(self.verify_single, ein, name, site)
                for ein, name, site in discoveries
            ]
            for i, future in enumerate(as_completed(futures)):
                future.result()
                if (i + 1) % 100 == 0:
                    logger.info(f"Progress: {i+1}/{len(discoveries)} verified")

        elapsed = time.time() - start

        # Save results
        with open(VERIFIED_FILE, 'a') as f:
            for r in self.results:
                f.write(json.dumps(asdict(r)) + '\n')

        # Save stats
        self.stats["elapsed_seconds"] = elapsed
        self.stats["verified_percentage"] = (self.stats["verified"] / max(1, self.stats["total_tested"])) * 100

        with open(VERIFICATION_STATS, 'w') as f:
            json.dump(self.stats, f, indent=2)

        logger.info("=" * 80)
        logger.info(f"VERIFICATION COMPLETE")
        logger.info(f"Total tested: {self.stats['total_tested']}")
        logger.info(f"Verified: {self.stats['verified']} ({self.stats['verified_percentage']:.1f}%)")
        logger.info(f"Suspicious: {self.stats['suspicious']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info(f"Avg confidence: {self.stats['avg_confidence']:.3f}")
        logger.info(f"Time elapsed: {elapsed/60:.1f} minutes")
        logger.info("=" * 80)

        return self.stats

if __name__ == "__main__":
    verifier = WebsiteVerifier()
    stats = verifier.run(limit=5000, workers=4)
