"""Deterministic identity checks for public nonprofit directory entries.

Directory websites often omit EINs.  This module keeps a conservative bridge to
IRS records: a record is eligible for automatic staging only when state, city,
ZIP, and a normalized street address all agree.  It never writes canonical data.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


ABBREVIATIONS = {
    "AVE": "AVENUE",
    "BLVD": "BOULEVARD",
    "CTR": "CENTER",
    "CT": "COURT",
    "DR": "DRIVE",
    "HWY": "HIGHWAY",
    "LN": "LANE",
    "PKWY": "PARKWAY",
    "PL": "PLACE",
    "RD": "ROAD",
    "SQ": "SQUARE",
    "ST": "STREET",
    "STE": "SUITE",
}


def normalize_text(value: str | None) -> str:
    """Return an uppercase comparison key without punctuation noise."""
    value = (value or "").upper()
    value = re.sub(r"\b([A-Z])\.\s*([A-Z])\.", r"\1\2", value)
    return re.sub(r"[^A-Z0-9 ]+", " ", value).strip()

def normalize_address(value: str | None) -> str:
    """Normalize common USPS-style abbreviations while preserving street number."""
    tokens = normalize_text(value).split()
    normalized = " ".join(ABBREVIATIONS.get(token, token) for token in tokens)
    # IRS exports can order state-route numbers before HIGHWAY ("NC 5 HWY").
    return re.sub(r"\b([A-Z]{2}) (\d+) HIGHWAY\b", r"\1 HIGHWAY \2", normalized)


def zip5(value: str | None) -> str:
    match = re.search(r"\d{5}", value or "")
    return match.group(0) if match else ""


@dataclass(frozen=True)
class DirectoryIdentity:
    state: str | None
    city: str | None
    zipcode: str | None
    street_address: str | None


def is_exact_address_match(irs: DirectoryIdentity, directory: DirectoryIdentity) -> bool:
    """Require every non-name IRS identity field to agree before auto-staging."""
    return (
        normalize_text(irs.state) == normalize_text(directory.state)
        and bool(normalize_text(irs.city))
        and normalize_text(irs.city) == normalize_text(directory.city)
        and bool(zip5(irs.zipcode))
        and zip5(irs.zipcode) == zip5(directory.zipcode)
        and bool(normalize_address(irs.street_address))
        and normalize_address(irs.street_address) == normalize_address(directory.street_address)
    )
