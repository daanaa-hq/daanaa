#!/usr/bin/env python3
"""
Cause IQ archive source scraper.

Uses Archive.org snapshots of Cause IQ organization pages to recover website
URLs for nonprofits whose live directory pages are blocked. Results are staged
in website_discovery_candidates and never written directly to canonical fields.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data/merit_registry.db"
LOG_DIR = ROOT / "logs"
LOG_PATH = LOG_DIR / "causeiq_archive_source_scraper.log"

DEFAULT_LIMIT = 100
DEFAULT_WORKERS = 4
PROFILE_TIMEOUT = 15
TARGET_TIMEOUT = 6
ARCHIVE_API = "https://archive.org/wayback/available"
USER_AGENT = "DaanaaArchiveDiscovery/2026-08-13 (+https://daanaa.org)"

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
    source TEXT NOT NULL DEFAULT 'causeiq_archive',
    notes TEXT,
    checked_at TEXT NOT NULL,
    UNIQUE(run_id, ein, candidate_domain)
);
CREATE INDEX IF NOT EXISTS idx_wdc_ein ON website_discovery_candidates(ein);
CREATE INDEX IF NOT EXISTS idx_wdc_status ON website_discovery_candidates(verification_status);
CREATE INDEX IF NOT EXISTS idx_wdc_confidence ON website_discovery_candidates(confidence DESC);
"""

EXCLUDED_HOST_SUBSTRINGS = (
    "web.archive.org",
    "www.causeiq.com",
    "causeiq.com",
    "google.com",
    "googletagmanager.com",
    "doubleclick.net",
    "cloudfront.net",
    "schema.org",
    "w3.org",
    "creativecommons.org",
    "github.com",
    "archive.org",
)


@dataclass
class CandidateRow:
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
    return logging.getLogger("causeiq_archive_source_scraper")


logger = setup_logging()


class CauseIQArchiveSourceScraper:
    def __init__(self, db_path: Path = DB_PATH, workers: int = DEFAULT_WORKERS):
        self.db_path = db_path
        self.workers = workers
        self.run_id = f"causeiq_archive_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        self.session = self._create_session()
        self._archive_lock = threading.Lock()
        self._last_archive_request = 0.0
        self.results = {
            "run_id": self.run_id,
            "orgs_requested": 0,
            "orgs_processed": 0,
            "snapshots_found": 0,
            "candidates_stored": 0,
            "verified_candidates": 0,
            "needs_review_candidates": 0,
            "rejected_candidates": 0,
            "errors": 0,
        }

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        retry_strategy = Retry(
            total=2,
            backoff_factor=0.4,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({"User-Agent": USER_AGENT})
        return session

    def init_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(SCHEMA_SQL)
            conn.commit()

    def archive_pause(self) -> None:
        with self._archive_lock:
            wait = 1.0 - (time.time() - self._last_archive_request)
            if wait > 0:
                time.sleep(wait)
            self._last_archive_request = time.time()

    def slugify_for_causeiq(self, text: str) -> str:
        text = (text or "").lower().strip()
        text = text.encode("ascii", "ignore").decode("ascii")
        text = text.replace("&", " and ")
        text = re.sub(r"[^a-z0-9]+", "-", text)
        text = re.sub(r"-{2,}", "-", text).strip("-")
        return text

    def org_url(self, org_name: str, ein: str) -> str:
        slug = self.slugify_for_causeiq(org_name)
        ein_digits = re.sub(r"\D", "", ein or "")
        return f"https://www.causeiq.com/organizations/{slug},{ein_digits}/"

    def get_orgs_without_website(self, limit: int) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT EIN, organization_name, CITY, STATE, COALESCE(total_revenue, 0) AS total_revenue
                FROM registry_enriched
                WHERE COALESCE(website, '') = ''
                  AND COALESCE(org_status, 'active') = 'active'
                  AND COALESCE(total_revenue, 0) >= 100000
                  AND EIN NOT IN (
                      SELECT DISTINCT ein
                      FROM website_discovery_candidates
                      WHERE source = 'causeiq_archive'
                  )
                ORDER BY total_revenue DESC, EIN
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            {
                "ein": str(row["EIN"]),
                "organization_name": row["organization_name"] or "",
                "city": row["CITY"] or "",
                "state": row["STATE"] or "",
            }
            for row in rows
        ]

    def fetch_archive_snapshot_url(self, org_url: str) -> tuple[Optional[str], list[str]]:
        self.archive_pause()
        try:
            resp = self.session.get(ARCHIVE_API, params={"url": org_url}, timeout=PROFILE_TIMEOUT)
            if resp.status_code >= 400:
                return None, [f"archive_api_http_{resp.status_code}"]
            payload = resp.json()
            closest = payload.get("archived_snapshots", {}).get("closest")
            if not closest or closest.get("available") is not True:
                return None, ["no_archive_snapshot"]
            self.results["snapshots_found"] += 1
            return closest.get("url"), [f"archive_timestamp:{closest.get('timestamp', '')}"]
        except Exception as exc:  # noqa: BLE001
            return None, [f"archive_api_error:{str(exc)[:120]}"]

    def fetch_snapshot_html(self, snapshot_url: str) -> tuple[Optional[str], list[str]]:
        try:
            resp = self.session.get(snapshot_url, timeout=PROFILE_TIMEOUT)
            if resp.status_code >= 400:
                return None, [f"snapshot_http_{resp.status_code}"]
            return resp.text, []
        except Exception as exc:  # noqa: BLE001
            return None, [f"snapshot_fetch_error:{str(exc)[:120]}"]

    def extract_title(self, html: str) -> Optional[str]:
        match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def extract_description(self, html: str) -> Optional[str]:
        match = re.search(r'<meta\s+name="description"\s+content="([^"]+)"', html, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def extract_external_candidates(self, html: str) -> list[str]:
        urls = re.findall(r'https?://[^"\'<>\s]+', html)
        cleaned: list[str] = []
        seen: set[str] = set()
        for raw_url in urls:
            url = raw_url.rstrip("\\").rstrip("/")
            parsed = urlparse(url)
            host = parsed.netloc.lower().replace("www.", "")
            if not host or any(part in host for part in EXCLUDED_HOST_SUBSTRINGS):
                continue
            if url in seen:
                continue
            seen.add(url)
            cleaned.append(url)
        return cleaned

    def org_tokens(self, org_name: str) -> list[str]:
        tokens = re.findall(r"[a-z0-9]+", (org_name or "").lower())
        stop = {"the", "of", "and", "for", "inc", "foundation", "association", "church", "center", "centre", "organization"}
        return [t for t in tokens if len(t) >= 3 and t not in stop]

    def score_candidate(self, org_name: str, url: str) -> tuple[int, float, str]:
        host = urlparse(url).netloc.lower().replace("www.", "")
        tokens = self.org_tokens(org_name)
        score = 0
        matched = 0
        for token in tokens:
            if token in host:
                matched += 1
                score += 25
        acronym = "".join(word[0] for word in re.findall(r"[A-Za-z0-9]+", org_name) if word)
        if len(acronym) >= 3 and acronym.lower() in host:
            score += 30
        ratio = matched / max(1, len(tokens))
        if ratio >= 0.75 or score >= 50:
            level = "strong"
        elif ratio >= 0.4 or score >= 25:
            level = "moderate"
        elif score > 0:
            level = "weak"
        else:
            level = "none"
        return min(100, score), ratio, level

    def verify_target(self, url: str) -> tuple[Optional[str], list[str]]:
        notes: list[str] = []
        try:
            head = self.session.head(url, timeout=TARGET_TIMEOUT, allow_redirects=True)
            if head.status_code < 400:
                return head.url, notes
            notes.append(f"target_head_{head.status_code}")
        except Exception as exc:  # noqa: BLE001
            notes.append(f"target_head_error:{str(exc)[:80]}")
        try:
            get_resp = self.session.get(url, timeout=TARGET_TIMEOUT, allow_redirects=True)
            if get_resp.status_code < 400:
                return get_resp.url, notes
            notes.append(f"target_get_{get_resp.status_code}")
        except Exception as exc:  # noqa: BLE001
            notes.append(f"target_get_error:{str(exc)[:80]}")
        return None, notes

    def build_candidate(self, org: dict) -> CandidateRow:
        ein = org["ein"]
        name = org["organization_name"]
        city = org["city"]
        state = org["state"]
        org_url = self.org_url(name, ein)

        snapshot_url, notes = self.fetch_archive_snapshot_url(org_url)
        if not snapshot_url:
            return CandidateRow(
                ein=ein,
                organization_name=name,
                city=city,
                state=state,
                candidate_domain="causeiq_archive_unavailable",
                final_url=None,
                verification_status="candidate_rejected",
                confidence=0,
                nonprofit_signal_count=0,
                identity_match_score=0.0,
                identity_match_level="none",
                title=None,
                description=None,
                content_preview=None,
                notes=notes + [f"source_url:{org_url}"],
            )

        html, html_notes = self.fetch_snapshot_html(snapshot_url)
        if not html:
            return CandidateRow(
                ein=ein,
                organization_name=name,
                city=city,
                state=state,
                candidate_domain="causeiq_archive_fetch_failed",
                final_url=None,
                verification_status="candidate_rejected",
                confidence=0,
                nonprofit_signal_count=0,
                identity_match_score=0.0,
                identity_match_level="none",
                title=None,
                description=None,
                content_preview=None,
                notes=notes + html_notes + [f"source_url:{org_url}", f"snapshot_url:{snapshot_url}"],
            )

        title = self.extract_title(html)
        description = self.extract_description(html)
        preview = re.sub(r"\s+", " ", html[:700])
        urls = self.extract_external_candidates(html)
        if not urls:
            return CandidateRow(
                ein=ein,
                organization_name=name,
                city=city,
                state=state,
                candidate_domain="causeiq_archive_no_external_url",
                final_url=None,
                verification_status="candidate_rejected",
                confidence=10,
                nonprofit_signal_count=0,
                identity_match_score=0.0,
                identity_match_level="none",
                title=title,
                description=description,
                content_preview=preview,
                notes=notes + html_notes + [f"source_url:{org_url}", f"snapshot_url:{snapshot_url}", "no_external_candidate_url"],
            )

        scored = []
        for url in urls:
            score, ratio, level = self.score_candidate(name, url)
            scored.append((score, ratio, level, url))
        scored.sort(reverse=True)
        best_score, best_ratio, best_level, best_url = scored[0]

        final_url, verify_notes = self.verify_target(best_url)
        all_notes = notes + html_notes + verify_notes + [
            f"source_url:{org_url}",
            f"snapshot_url:{snapshot_url}",
            "source:causeiq_archive",
        ]
        candidate_domain = urlparse(final_url or best_url).netloc.lower().replace("www.", "") or best_url

        if final_url and best_level in {"strong", "moderate"}:
            status = "candidate_verified"
            confidence = min(96, 55 + best_score)
        elif final_url:
            status = "candidate_needs_review"
            confidence = 60
        else:
            status = "candidate_needs_review" if best_level != "none" else "candidate_rejected"
            confidence = 45 if best_level != "none" else 15

        return CandidateRow(
            ein=ein,
            organization_name=name,
            city=city,
            state=state,
            candidate_domain=candidate_domain,
            final_url=final_url or best_url,
            verification_status=status,
            confidence=confidence,
            nonprofit_signal_count=1,
            identity_match_score=best_ratio,
            identity_match_level=best_level,
            title=title,
            description=description,
            content_preview=preview,
            notes=all_notes,
        )

    def store_candidate(self, conn: sqlite3.Connection, candidate: CandidateRow) -> None:
        conn.execute(
            """
            INSERT OR REPLACE INTO website_discovery_candidates (
                run_id, ein, organization_name, city, state, candidate_domain, final_url,
                verification_status, confidence, nonprofit_signal_count, identity_match_score,
                identity_match_level, title, description, content_preview, source, notes, checked_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'causeiq_archive', ?, ?)
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

    def run(self, limit: int) -> dict:
        self.init_schema()
        orgs = self.get_orgs_without_website(limit)
        self.results["orgs_requested"] = len(orgs)
        logger.info("run_id=%s orgs=%s workers=%s", self.run_id, len(orgs), self.workers)
        if not orgs:
            logger.warning("No candidate orgs found")
            return self.results

        candidates: list[CandidateRow] = []
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self.build_candidate, org): org for org in orgs}
            for future in as_completed(futures):
                try:
                    candidate = future.result()
                    candidates.append(candidate)
                    self.results["orgs_processed"] += 1
                except Exception as exc:  # noqa: BLE001
                    self.results["errors"] += 1
                    logger.error("worker error: %s", str(exc)[:160])

        with sqlite3.connect(self.db_path) as conn:
            for candidate in candidates:
                self.store_candidate(conn, candidate)
                self.results["candidates_stored"] += 1
                if candidate.verification_status == "candidate_verified":
                    self.results["verified_candidates"] += 1
                elif candidate.verification_status == "candidate_needs_review":
                    self.results["needs_review_candidates"] += 1
                else:
                    self.results["rejected_candidates"] += 1
            conn.commit()

        return self.results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage websites from archived Cause IQ organization pages")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help=f"Number of orgs to process (default: {DEFAULT_LIMIT})")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help=f"Concurrent workers (default: {DEFAULT_WORKERS})")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    scraper = CauseIQArchiveSourceScraper(workers=args.workers)
    results = scraper.run(limit=args.limit)
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
