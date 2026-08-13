#!/usr/bin/env python3
"""Stage exact EIN-matched Habitat affiliate websites from Habitat's locator.

This is intentionally conservative. The locator itself does not expose EINs, so
an affiliate is staged only when its physical address exactly matches one IRS
record that currently lacks a website. It never writes ``registry_enriched``.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

try:
    from directory_identity import DirectoryIdentity, is_exact_address_match
except ModuleNotFoundError:  # Support package imports used by local diagnostics.
    from scripts.continuous_discovery.directory_identity import DirectoryIdentity, is_exact_address_match


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "merit_registry.db"
SOURCE_BASE = "https://www.habitat.org"
SOURCE_PATH = "/local/affiliate-by-state?state={state}"
USER_AGENT = "DaanaaDirectoryVerifier/2026-08-13 (+https://daanaa.org)"
REQUEST_INTERVAL_SECONDS = 2.0
REQUEST_TIMEOUT_SECONDS = 12


@dataclass(frozen=True)
class Affiliate:
    name: str
    website: str
    street_address: str
    city: str
    state: str
    zipcode: str
    source_url: str


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fetch_state(state: str) -> str:
    response = requests.get(
        SOURCE_BASE + SOURCE_PATH.format(state=state),
        headers={"User-Agent": USER_AGENT},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.text


def parse_affiliates(html: str, source_url: str) -> list[Affiliate]:
    soup = BeautifulSoup(html, "html.parser")
    affiliates: list[Affiliate] = []
    for article in soup.select("article.address-listing"):
        name = article.select_one(".address-listing__heading")
        website = article.select_one(".icon--small-website ~ a[href]")
        street = article.select_one(".address-line1")
        city = article.select_one(".locality")
        state = article.select_one(".administrative-area")
        zipcode = article.select_one(".postal-code")
        if not all((name, website, street, city, state, zipcode)):
            continue
        affiliates.append(
            Affiliate(
                name=name.get_text(" ", strip=True),
                website=website["href"],
                street_address=street.get_text(" ", strip=True),
                city=city.get_text(" ", strip=True),
                state=state.get_text(" ", strip=True),
                zipcode=zipcode.get_text(" ", strip=True),
                source_url=source_url,
            )
        )
    return affiliates


def missing_habitat_orgs(conn: sqlite3.Connection, state: str) -> list[sqlite3.Row]:
    conn.row_factory = sqlite3.Row
    return conn.execute(
        """
        SELECT EIN, organization_name, CITY, STATE, zipcode, street_address
        FROM registry_enriched
        WHERE STATE = ?
          AND lower(organization_name) LIKE '%habitat%'
          AND COALESCE(website, '') = ''
          AND COALESCE(org_status, 'active') = 'active'
        """,
        (state,),
    ).fetchall()


def exact_matches(orgs: list[sqlite3.Row], affiliate: Affiliate) -> list[sqlite3.Row]:
    directory_identity = DirectoryIdentity(
        affiliate.state, affiliate.city, affiliate.zipcode, affiliate.street_address
    )
    return [
        org
        for org in orgs
        if is_exact_address_match(
            DirectoryIdentity(org["STATE"], org["CITY"], org["zipcode"], org["street_address"]),
            directory_identity,
        )
    ]


def stage(conn: sqlite3.Connection, run_id: str, org: sqlite3.Row, affiliate: Affiliate) -> None:
    parsed = urlparse(affiliate.website)
    domain = parsed.netloc.lower().removeprefix("www.")
    notes = json.dumps(
        {
            "source_url": affiliate.source_url,
            "directory_name": affiliate.name,
            "directory_physical_address": {
                "street": affiliate.street_address,
                "city": affiliate.city,
                "state": affiliate.state,
                "zip": affiliate.zipcode,
            },
            "match_rule": "exact_state_city_zip_street",
        },
        sort_keys=True,
    )
    conn.execute(
        """
        INSERT OR REPLACE INTO website_discovery_candidates (
            run_id, ein, organization_name, city, state, candidate_domain, final_url,
            verification_status, confidence, nonprofit_signal_count, identity_match_score,
            identity_match_level, title, description, content_preview, source, notes, checked_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'candidate_verified', 98, 2, 1.0, 'exact', ?, ?, ?, 'habitat_official_directory', ?, ?)
        """,
        (
            run_id, org["EIN"], org["organization_name"], org["CITY"], org["STATE"], domain,
            affiliate.website, affiliate.name, "Official Habitat affiliate directory",
            "Exact IRS physical-address match", notes, now_iso(),
        ),
    )

def run(states: list[str], dry_run: bool) -> dict[str, object]:
    run_id = "habitat_official_directory_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    totals: dict[str, object] = {
        "run_id": run_id,
        "states_requested": len(states),
        "states_completed": 0,
        "affiliates": 0,
        "exact_matches": 0,
        "staged": 0,
        "failed_states": [],
        "state_results": [],
    }
    with sqlite3.connect(DB_PATH) as conn:
        for index, state in enumerate(states):
            if index:
                time.sleep(REQUEST_INTERVAL_SECONDS)
            source_url = SOURCE_BASE + SOURCE_PATH.format(state=state)
            try:
                affiliates = parse_affiliates(fetch_state(state), source_url)
            except requests.RequestException as exc:
                totals["failed_states"].append({"state": state, "error": str(exc)[:160]})
                continue
            orgs = missing_habitat_orgs(conn, state)
            state_matches = 0
            totals["states_completed"] += 1
            totals["affiliates"] += len(affiliates)
            for affiliate in affiliates:
                matches = exact_matches(orgs, affiliate)
                if len(matches) != 1:
                    continue
                state_matches += 1
                totals["exact_matches"] += 1
                if not dry_run:
                    stage(conn, run_id, matches[0], affiliate)
                    totals["staged"] += 1
            totals["state_results"].append(
                {"state": state, "affiliates": len(affiliates), "exact_matches": state_matches}
            )
        if not dry_run:
            conn.commit()
    return totals
    return totals


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--states", default="NC", help="Comma-separated USPS states; defaults to NC")
    parser.add_argument("--dry-run", action="store_true", help="Fetch and match without staging candidates")
    args = parser.parse_args()
    states = [state.strip().upper() for state in args.states.split(",") if state.strip()]
    print(json.dumps(run(states, args.dry_run), sort_keys=True))


if __name__ == "__main__":
    main()
