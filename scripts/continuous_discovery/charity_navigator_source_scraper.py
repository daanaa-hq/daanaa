#!/usr/bin/env python3
"""
Charity Navigator source scraper — stage nonprofit websites by EIN.

This script uses Charity Navigator's public EIN profile pages as a
source-attributed discovery lane. It stages findings in
website_discovery_candidates and does not write canonical website fields.
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
from urllib.robotparser import RobotFileParser

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data/merit_registry.db"
LOG_DIR = ROOT / "logs"
LOG_PATH = LOG_DIR / "charity_navigator_source_scraper.log"

DEFAULT_LIMIT = 100
DEFAULT_WORKERS = 4
PROFILE_TIMEOUT = 12
TARGET_TIMEOUT = 6
USER_AGENT = "DaanaaSourceScraper/2026-08-13 (+https://daanaa.org)"
CN_BASE = "https://www.charitynavigator.org"
ARCHIVE_API = "https://archive.org/wayback/available"

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
    source TEXT NOT NULL DEFAULT 'charity_navigator',
    notes TEXT,
    checked_at TEXT NOT NULL,
    UNIQUE(run_id, ein, candidate_domain)
);
CREATE INDEX IF NOT EXISTS idx_wdc_ein ON website_discovery_candidates(ein);
CREATE INDEX IF NOT EXISTS idx_wdc_status ON website_discovery_candidates(verification_status);
CREATE INDEX IF NOT EXISTS idx_wdc_confidence ON website_discovery_candidates(confidence DESC);
"""

WEBSITE_PATTERNS = [
    re.compile(r'"website"\s*:\s*"(?P<url>https?:\\/\\/[^"]+)"', re.IGNORECASE),
    re.compile(r'"url"\s*:\s*\{\s*"url"\s*:\s*"(?P<url>https?:\\/\\/[^"]+)"', re.IGNORECASE),
    re.compile(r'<a\s+href="(?P<url>https?://[^"]+)"[^>]*aria-label="[^"]*nonprofit website', re.IGNORECASE),
    re.compile(r'href="(?P<url>https?://[^"]+)"[^>]*aria-label="Visit nonprofit website"', re.IGNORECASE),
]


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
    return logging.getLogger("charity_navigator_source_scraper")


logger = setup_logging()


class CharityNavigatorSourceScraper:
    def __init__(self, db_path: Path = DB_PATH, workers: int = DEFAULT_WORKERS):
        self.db_path = db_path
        self.workers = workers
        self.run_id = f"charity_navigator_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        self.session = self._create_session()
        self._robots = RobotFileParser()
        self._robots_loaded = False
        self._rate_lock = threading.Lock()
        self._last_cn_request = 0.0
        self._archive_lock = threading.Lock()
        self._last_archive_request = 0.0
        self._archive_lock = threading.Lock()
        self._last_archive_request = 0.0
        self.results = {
            "run_id": self.run_id,
            "orgs_requested": 0,
            "orgs_processed": 0,
            "candidate_profiles_fetched": 0,
            "archive_profiles_fetched": 0,
            "archive_profiles_fetched": 0,
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

    def load_robots(self) -> None:
        if self._robots_loaded:
            return
        try:
            self._robots.set_url(f"{CN_BASE}/robots.txt")
            self._robots.read()
        except Exception as exc:  # noqa: BLE001
            logger.warning("robots.txt read failed, failing open: %s", str(exc)[:120])
        self._robots_loaded = True

    def can_fetch_profile(self, ein: str) -> bool:
        self.load_robots()
        path = f"{CN_BASE}/ein/{ein}"
        try:
            return self._robots.can_fetch(USER_AGENT, path)
        except Exception:  # noqa: BLE001
            return True

    def cn_pause(self) -> None:
        with self._rate_lock:
            wait = 1.2 - (time.time() - self._last_cn_request)
            if wait > 0:
                time.sleep(wait)
            self._last_cn_request = time.time()

    def archive_pause(self) -> None:
        with self._archive_lock:
            wait = 1.0 - (time.time() - self._last_archive_request)
            if wait > 0:
                time.sleep(wait)
            self._last_archive_request = time.time()

    def fetch_archive_profile(self, ein: str) -> tuple[Optional[str], list[str]]:
        """Recover an EIN-keyed profile from Internet Archive when live CN is unavailable."""
        profile_url = f"{CN_BASE}/ein/{ein}"
        self.archive_pause()
        try:
            lookup = self.session.get(ARCHIVE_API, params={"url": profile_url}, timeout=PROFILE_TIMEOUT)
            if lookup.status_code >= 400:
                return None, [f"archive_api_http_{lookup.status_code}"]
            closest = lookup.json().get("archived_snapshots", {}).get("closest")
            if not closest or closest.get("available") is not True:
                return None, ["no_archive_snapshot"]
            snapshot_url = closest.get("url")
            if not snapshot_url:
                return None, ["archive_snapshot_url_missing"]
            snapshot_url = snapshot_url.replace("http://web.archive.org", "https://web.archive.org")
            snapshot_url = re.sub(r"/web/(\d+)(?:[a-z_]+)?/", r"/web/\1id_/", snapshot_url)
            response = self.session.get(snapshot_url, timeout=PROFILE_TIMEOUT)
            self.results["archive_profiles_fetched"] += 1
            if response.status_code >= 400:
                return None, [f"archive_snapshot_http_{response.status_code}"]
            return response.text, [f"archive_timestamp:{closest.get("timestamp", "")}", f"archive_snapshot:{snapshot_url}"]
        except Exception as exc:  # noqa: BLE001
            return None, [f"archive_fetch_error:{str(exc)[:120]}"]

    def get_orgs_without_website(self, limit: int) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT EIN, organization_name, CITY, STATE
                FROM registry_enriched
                WHERE COALESCE(website, '') = ''
                  AND COALESCE(org_status, 'active') = 'active'
                  AND COALESCE(subsection, '3') = '3'
                  AND COALESCE(NTEE1, '') NOT IN ('E', 'Y')
                  AND COALESCE(total_revenue, 0) BETWEEN 100000 AND 500000000
                  AND EIN NOT IN (
                      SELECT DISTINCT ein
                      FROM website_discovery_candidates
                      WHERE source = 'charity_navigator'
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

    def fetch_profile(self, ein: str) -> tuple[Optional[str], list[str]]:
        if not self.can_fetch_profile(ein):
            return None, ["robots_disallow"]

        self.cn_pause()
        url = f"{CN_BASE}/ein/{ein}"
        notes: list[str] = []
        try:
            resp = self.session.get(url, timeout=PROFILE_TIMEOUT)
            self.results["candidate_profiles_fetched"] += 1
            if resp.status_code == 404:
                return None, ["profile_not_found"]
            if resp.status_code >= 400:
                return None, [f"profile_http_{resp.status_code}"]
            return resp.text, notes
        except Exception as exc:  # noqa: BLE001
            return None, [f"profile_fetch_error:{str(exc)[:120]}"]

    def extract_website(self, html: str) -> Optional[str]:
        for pattern in WEBSITE_PATTERNS:
            match = pattern.search(html)
            if match:
                return match.group("url").replace("\\/", "/")
        return None

    def extract_title(self, html: str) -> Optional[str]:
        match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def extract_description(self, html: str) -> Optional[str]:
        match = re.search(
            r'<meta\s+name="description"\s+content="([^"]+)"',
            html,
            re.IGNORECASE,
        )
        return match.group(1).strip() if match else None

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

        html, notes = self.fetch_profile(ein)
        source_label = "charity_navigator_public_profile"
        if not html or not self.extract_website(html):
            archive_html, archive_notes = self.fetch_archive_profile(ein)
            if archive_html:
                html = archive_html
                notes = notes + archive_notes
                source_label = "charity_navigator_archive"
            else:
                notes = notes + archive_notes
        if not html:
            return CandidateRow(
                ein=ein,
                organization_name=name,
                city=city,
                state=state,
                candidate_domain=f"charitynavigator.org/ein/{ein}",
                final_url=None,
                verification_status="candidate_rejected",
                confidence=0,
                nonprofit_signal_count=0,
                identity_match_score=0.0,
                identity_match_level="none",
                title=None,
                description=None,
                content_preview=None,
                notes=notes,
            )

        title = self.extract_title(html)
        description = self.extract_description(html)
        website = self.extract_website(html)
        preview = re.sub(r"\s+", " ", html[:700])

        if not website:
            return CandidateRow(
                ein=ein,
                organization_name=name,
                city=city,
                state=state,
                candidate_domain=f"charitynavigator.org/ein/{ein}",
                final_url=None,
                verification_status="candidate_rejected",
                confidence=15,
                nonprofit_signal_count=1,
                identity_match_score=0.0,
                identity_match_level="none",
                title=title,
                description=description,
                content_preview=preview,
                notes=notes + ["profile_has_no_website"],
            )

        final_url, target_notes = self.verify_target(website)
        all_notes = notes + target_notes + [f"source:{source_label}", "attribution:IRS_Form_990_via_Charity_Navigator"]
        parsed = urlparse(final_url or website)
        candidate_domain = parsed.netloc.lower().replace("www.", "") or website

        if final_url:
            status = "candidate_verified"
            confidence = 96
            identity_score = 1.0
            identity_level = "strong"
            nonprofit_signal_count = 2
        else:
            status = "candidate_needs_review"
            confidence = 60
            identity_score = 0.9
            identity_level = "strong"
            nonprofit_signal_count = 1

        return CandidateRow(
            ein=ein,
            organization_name=name,
            city=city,
            state=state,
            candidate_domain=candidate_domain,
            final_url=final_url or website,
            verification_status=status,
            confidence=confidence,
            nonprofit_signal_count=nonprofit_signal_count,
            identity_match_score=identity_score,
            identity_match_level=identity_level,
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
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'charity_navigator', ?, ?)
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
    parser = argparse.ArgumentParser(description="Stage websites from Charity Navigator public EIN profiles")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help=f"Number of orgs to process (default: {DEFAULT_LIMIT})")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help=f"Concurrent workers (default: {DEFAULT_WORKERS})")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    scraper = CharityNavigatorSourceScraper(workers=args.workers)
    results = scraper.run(limit=args.limit)
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
