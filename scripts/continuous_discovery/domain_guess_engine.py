#!/usr/bin/env python3
"""
Domain Guessing Engine — staging-first website discovery.

This script generates likely nonprofit website domains, verifies them
conservatively, and writes the best candidate per EIN into a staging table.
It does not write to canonical website fields unless explicitly invoked with
--write-canonical, and even then only for the strongest matches.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sqlite3
import socket
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data/merit_registry.db"
LOG_DIR = ROOT / "logs"
LOG_PATH = LOG_DIR / "domain_guess_engine.log"

DEFAULT_LIMIT = 100
DEFAULT_WORKERS = 8
TIMEOUT = 5

NONPROFIT_SIGNALS = [
    "nonprofit", "charity", "donate", "donation", "mission", "501c3", "501(c)(3)",
    "tax-deductible", "give", "volunteer", "community service", "charitable",
    "foundation", "trust", "endowment", "grant", "philanthrop", "social impact",
    "cause", "services", "help", "support us", "fund", "initiative",
]

PARKED_SIGNALS = [
    "parked", "for sale", "coming soon", "under construction", "godaddy",
    "registrar", "domain for sale", "buy this domain",
]

GENERIC_NAME_WORDS = {
    "the", "and", "of", "for", "inc", "incorporated", "llc", "ltd", "foundation",
    "association", "society", "center", "centre", "organization", "org", "group",
    "friends", "club", "committee", "community", "services", "ministries",
}

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS website_discovery_candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    ein TEXT NOT NULL,
    organization_name TEXT,
    city TEXT,
    state TEXT,
    candidate_domain TEXT NOT NULL,
    final_url TEXT,
    verification_status TEXT NOT NULL,
    confidence INTEGER NOT NULL DEFAULT 0,
    nonprofit_signal_count INTEGER NOT NULL DEFAULT 0,
    identity_match_score REAL NOT NULL DEFAULT 0,
    identity_match_level TEXT NOT NULL DEFAULT 'none',
    title TEXT,
    description TEXT,
    content_preview TEXT,
    source TEXT NOT NULL DEFAULT 'domain_guess',
    notes TEXT,
    checked_at TEXT NOT NULL,
    UNIQUE(run_id, ein, candidate_domain)
);
CREATE INDEX IF NOT EXISTS idx_wdc_ein ON website_discovery_candidates(ein);
CREATE INDEX IF NOT EXISTS idx_wdc_status ON website_discovery_candidates(verification_status);
CREATE INDEX IF NOT EXISTS idx_wdc_confidence ON website_discovery_candidates(confidence DESC);
"""


@dataclass
class CandidateResult:
    ein: str
    organization_name: str
    city: str
    state: str
    candidate_domain: str
    final_url: Optional[str]
    verification_status: str
    confidence: int
    nonprofit_signal_count: int
    identity_match_score: float
    identity_match_level: str
    title: Optional[str]
    description: Optional[str]
    content_preview: Optional[str]
    notes: list[str]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def setup_logging() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler()],
    )
    return logging.getLogger("domain_guess_engine")


logger = setup_logging()


class DomainGuessEngine:
    def __init__(self, db_path: Path = DB_PATH, workers: int = DEFAULT_WORKERS):
        self.db_path = db_path
        self.workers = workers
        self.run_id = f"domain_guess_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        self.session = self._create_session()
        self.results = {
            "run_id": self.run_id,
            "orgs_requested": 0,
            "orgs_processed": 0,
            "orgs_with_candidates": 0,
            "candidate_domains_checked": 0,
            "candidates_stored": 0,
            "canonical_writes": 0,
            "errors": 0,
        }

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        retry_strategy = Retry(
            total=2,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({"User-Agent": "DaanaaDomainGuess/2026-08-13 (+https://daanaa.org)"})
        return session

    def init_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(SCHEMA_SQL)
            conn.commit()

    def slugify(self, text: str) -> str:
        text = (text or "").lower().strip()
        text = text.encode("ascii", "ignore").decode("ascii")
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"[-\s]+", "", text)
        return text[:50]

    def extract_acronym(self, org_name: str) -> Optional[str]:
        words = [w for w in re.split(r"\s+", org_name or "") if w]
        if len(words) <= 1:
            return None
        acronym = "".join(w[0].lower() for w in words)
        return acronym if len(acronym) >= 2 else None

    def generate_domain_variants(self, org_name: str, city: str, acronym: Optional[str]) -> list[str]:
        slug_name = self.slugify(org_name)
        slug_city = self.slugify(city) if city else None
        variants: list[str] = []

        if slug_name:
            variants.extend([f"{slug_name}.org", f"{slug_name}.com"])

        if acronym:
            slug_acronym = self.slugify(acronym)
            if slug_acronym:
                variants.extend([f"{slug_acronym}.org", f"{slug_acronym}.com"])

        if slug_city and slug_name and slug_city != slug_name:
            variants.extend([
                f"{slug_city}{slug_name}.org",
                f"{slug_city}{slug_name}.com",
            ])

        words = [self.slugify(w) for w in re.split(r"\s+", org_name or "") if self.slugify(w)]
        if len(words) >= 2:
            variants.extend([
                f"{words[0]}{words[-1]}.org",
                f"{words[0]}{words[-1]}.com",
            ])

        return list(dict.fromkeys(v for v in variants if v))[:10]

    def dns_lookup(self, domain: str) -> bool:
        try:
            socket.gethostbyname(domain)
            return True
        except (socket.gaierror, socket.error):
            return False

    def fetch_page(self, domain: str) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str], list[str]]:
        notes: list[str] = []
        for url in (f"https://{domain}", f"http://{domain}"):
            try:
                head = self.session.head(url, timeout=TIMEOUT, allow_redirects=True)
                if head.status_code not in (200, 301, 302, 303):
                    notes.append(f"HEAD {url} -> {head.status_code}")
                    continue
                final_url = head.url
                get_resp = self.session.get(final_url, timeout=TIMEOUT, allow_redirects=True)
                if get_resp.status_code >= 400:
                    notes.append(f"GET {final_url} -> {get_resp.status_code}")
                    continue
                html = get_resp.text
                title_match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
                title = title_match.group(1).strip() if title_match else None
                desc_match = re.search(
                    r"<meta\s+name=[\"']description[\"']\s+content=[\"']([^\"']+)[\"']",
                    html,
                    re.IGNORECASE,
                )
                description = desc_match.group(1).strip() if desc_match else None
                body_match = re.search(r"<body[^>]*>(.*?)</body>", html, re.IGNORECASE | re.DOTALL)
                content = body_match.group(1) if body_match else html
                content = re.sub(r"<[^>]+>", " ", content)
                content = re.sub(r"\s+", " ", content).strip()[:700]
                return final_url, title, description, content, notes
            except Exception as exc:  # noqa: BLE001
                notes.append(f"fetch_error {url}: {str(exc)[:80]}")
        return None, None, None, None, notes

    def score_nonprofit_signals(self, text: str) -> int:
        combined = (text or "").lower()
        return sum(1 for signal in NONPROFIT_SIGNALS if signal in combined)

    def extract_name_tokens(self, org_name: str) -> list[str]:
        tokens = re.findall(r"[a-z0-9]+", (org_name or "").lower())
        return [t for t in tokens if len(t) >= 3 and t not in GENERIC_NAME_WORDS]

    def score_identity(self, org_name: str, domain_or_url: str, title: str, description: str, content: str) -> tuple[float, str]:
        domain_host = urlparse(domain_or_url if domain_or_url.startswith("http") else f"https://{domain_or_url}").netloc.lower()
        domain_host = domain_host.replace("www.", "")
        domain_text = re.sub(r"\.(org|com|net|us)$", "", domain_host)
        combined = " ".join(part for part in [title or "", description or "", content or ""] if part).lower()
        tokens = self.extract_name_tokens(org_name)
        if not tokens:
            ratio = SequenceMatcher(None, self.slugify(org_name), domain_text).ratio()
            level = "strong" if ratio >= 0.8 else "weak" if ratio >= 0.6 else "none"
            return ratio, level

        matched = sum(1 for token in tokens if token in combined or token in domain_text)
        token_ratio = matched / max(1, len(tokens))
        seq_ratio = SequenceMatcher(None, self.slugify(org_name), domain_text).ratio()
        score = max(token_ratio, seq_ratio)
        if token_ratio >= 0.75 or seq_ratio >= 0.88:
            level = "strong"
        elif token_ratio >= 0.5 or seq_ratio >= 0.72:
            level = "moderate"
        elif token_ratio > 0 or seq_ratio >= 0.58:
            level = "weak"
        else:
            level = "none"
        return score, level

    def verify_domain(self, *, ein: str, org_name: str, city: str, state: str, domain: str) -> CandidateResult:
        if not self.dns_lookup(domain):
            return CandidateResult(ein, org_name, city, state, domain, None, "dns_failed", 0, 0, 0.0, "none", None, None, None, ["dns lookup failed"])

        final_url, title, description, content, notes = self.fetch_page(domain)
        if not final_url:
            return CandidateResult(ein, org_name, city, state, domain, None, "http_failed", 0, 0, 0.0, "none", None, None, None, notes)

        combined = " ".join(part for part in [title or "", description or "", content or ""] if part)
        lower_combined = combined.lower()
        if any(sig in lower_combined for sig in PARKED_SIGNALS):
            return CandidateResult(ein, org_name, city, state, domain, final_url, "parked_or_placeholder", 0, 0, 0.0, "none", title, description, content, notes + ["parked or placeholder signals"])

        signal_count = self.score_nonprofit_signals(combined)
        identity_score, identity_level = self.score_identity(org_name, final_url, title or "", description or "", content or "")

        confidence = 0
        if signal_count >= 3:
            confidence += 45
        elif signal_count == 2:
            confidence += 35
        elif signal_count == 1:
            confidence += 20

        if identity_level == "strong":
            confidence += 45
        elif identity_level == "moderate":
            confidence += 30
        elif identity_level == "weak":
            confidence += 10
        confidence = min(100, confidence)

        status = "candidate_rejected"
        if signal_count >= 2 and identity_level in {"strong", "moderate"}:
            status = "candidate_verified"
        elif signal_count >= 1 and identity_level == "strong":
            status = "candidate_verified"
        elif confidence >= 45:
            status = "candidate_needs_review"
        else:
            notes.append("insufficient nonprofit signals or identity match")

        return CandidateResult(
            ein=ein,
            organization_name=org_name,
            city=city,
            state=state,
            candidate_domain=domain,
            final_url=final_url,
            verification_status=status,
            confidence=confidence,
            nonprofit_signal_count=signal_count,
            identity_match_score=identity_score,
            identity_match_level=identity_level,
            title=title,
            description=description,
            content_preview=content,
            notes=notes,
        )

    def get_orgs_without_website(self, limit: int) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT EIN, organization_name, CITY, STATE
                FROM registry_enriched
                WHERE COALESCE(website, '') = ''
                  AND EIN NOT IN (SELECT DISTINCT ein FROM website_discovery_candidates)
                ORDER BY EIN
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            {
                "ein": row["EIN"],
                "organization_name": row["organization_name"] or "",
                "city": row["CITY"] or "",
                "state": row["STATE"] or "",
            }
            for row in rows
        ]

    def store_candidate(self, conn: sqlite3.Connection, candidate: CandidateResult) -> None:
        conn.execute(
            """
            INSERT OR REPLACE INTO website_discovery_candidates (
                run_id, ein, organization_name, city, state, candidate_domain, final_url,
                verification_status, confidence, nonprofit_signal_count, identity_match_score,
                identity_match_level, title, description, content_preview, source, notes, checked_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'domain_guess', ?, ?)
            """,
            (
                self.run_id,
                candidate.ein,
                candidate.organization_name,
                candidate.city,
                candidate.state,
                candidate.candidate_domain,
                candidate.final_url,
                candidate.verification_status,
                candidate.confidence,
                candidate.nonprofit_signal_count,
                candidate.identity_match_score,
                candidate.identity_match_level,
                candidate.title,
                candidate.description,
                candidate.content_preview,
                json.dumps(candidate.notes),
                now_iso(),
            ),
        )

    def maybe_write_canonical(self, conn: sqlite3.Connection, candidate: CandidateResult) -> bool:
        if candidate.verification_status != "candidate_verified":
            return False
        if candidate.confidence < 92 or candidate.identity_match_level != "strong":
            return False
        before = conn.total_changes
        conn.execute(
            """
            UPDATE registry_enriched
            SET website = ?,
                website_status = 'candidate',
                website_source = 'domain_guess',
                website_checked_at = ?,
                website_final_domain = ?,
                website_last_verified = ?
            WHERE EIN = ? AND COALESCE(website, '') = ''
            """,
            (
                candidate.final_url or candidate.candidate_domain,
                now_iso(),
                urlparse(candidate.final_url or f"https://{candidate.candidate_domain}").netloc.lower().replace("www.", ""),
                now_iso(),
                candidate.ein,
            ),
        )
        return conn.total_changes > before

    def run(self, *, limit: int, write_canonical: bool) -> dict:
        self.init_schema()
        orgs = self.get_orgs_without_website(limit)
        self.results["orgs_requested"] = len(orgs)
        logger.info("run_id=%s orgs=%s workers=%s write_canonical=%s", self.run_id, len(orgs), self.workers, write_canonical)
        if not orgs:
            logger.warning("No orgs without websites found")
            return self.results

        with sqlite3.connect(self.db_path) as conn:
            for org in orgs:
                self.results["orgs_processed"] += 1
                domains = self.generate_domain_variants(
                    org_name=org["organization_name"],
                    city=org["city"],
                    acronym=self.extract_acronym(org["organization_name"]),
                )
                candidates: list[CandidateResult] = []
                with ThreadPoolExecutor(max_workers=min(self.workers, max(1, len(domains)))) as executor:
                    futures = [
                        executor.submit(
                            self.verify_domain,
                            ein=org["ein"],
                            org_name=org["organization_name"],
                            city=org["city"],
                            state=org["state"],
                            domain=domain,
                        )
                        for domain in domains
                    ]
                    for future in as_completed(futures):
                        self.results["candidate_domains_checked"] += 1
                        try:
                            candidates.append(future.result())
                        except Exception as exc:  # noqa: BLE001
                            self.results["errors"] += 1
                            logger.warning("candidate verification failed for %s: %s", org["ein"], str(exc)[:120])

                if not candidates:
                    continue

                best = max(
                    candidates,
                    key=lambda c: (
                        c.verification_status == "candidate_verified",
                        c.verification_status == "candidate_needs_review",
                        c.confidence,
                        c.identity_match_score,
                        c.nonprofit_signal_count,
                    ),
                )
                self.store_candidate(conn, best)
                self.results["candidates_stored"] += 1
                if best.verification_status in {"candidate_verified", "candidate_needs_review"}:
                    self.results["orgs_with_candidates"] += 1
                if write_canonical and self.maybe_write_canonical(conn, best):
                    self.results["canonical_writes"] += 1
                conn.commit()

                logger.info(
                    "EIN=%s status=%s confidence=%s domain=%s final=%s",
                    best.ein,
                    best.verification_status,
                    best.confidence,
                    best.candidate_domain,
                    best.final_url,
                )

        return self.results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Staging-first nonprofit website discovery")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="Number of orgs to process")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help="Parallel workers per org")
    parser.add_argument(
        "--write-canonical",
        action="store_true",
        help="Allow explicit canonical website writes for only the strongest matches",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    engine = DomainGuessEngine(workers=args.workers)
    results = engine.run(limit=args.limit, write_canonical=args.write_canonical)
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
