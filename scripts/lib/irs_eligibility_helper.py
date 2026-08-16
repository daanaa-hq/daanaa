"""
IRS Eligibility Helper — Phase 2 Integration

Provides consistent eligibility status classification across all public API routes.

Statuses:
- verified: Pub78 + BMF + not revoked (authoritative intersection)
- unverified: BMF-only, not in Pub78 (limited evidence)
- revoked: IRS auto-revocation record found
- unknown: Manifest missing or stale (> 7 days)
- exception_possible: Church/group ruling indicators

CRITICAL: This helper parses IRS source files directly, NOT the database.
The database flags (deductibility='1') are unreliable; the source files are
the single source of truth per IRS Publication 78 and BMF.

Rules:
- Verified: EIN in BOTH Pub78 AND BMF, not in auto-revocation list
- Unverified: EIN in BMF but NOT in Pub78, not in auto-revocation list
- Revoked: EIN in auto-revocation list (regardless of Pub78/BMF status)
- Unknown: Manifest missing/stale or source files unavailable
- Exception Possible: Church/group ruling codes (may not be in Pub78)
"""

import csv
import json
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, Set, Tuple


class IrsEligibilityHelper:
    """Classify organizations by IRS evidence tier.

    Loads Pub78, BMF, and auto-revocation lists at startup.
    All EIN lookups are O(1) set membership checks.
    """

    def __init__(self, db_path: str, manifest_path: str):
        """
        Initialize helper with database and manifest paths.

        Args:
            db_path: Path to merit_registry.db
            manifest_path: Path to eligibility_manifest.json
        """
        self.db_path = db_path
        self.manifest_path = manifest_path
        self._manifest_cache: Optional[Dict] = None

        # Source of truth: loaded from IRS files, not database
        self._pub78_eins: Optional[Set[str]] = None
        self._bmf_eins: Optional[Set[str]] = None
        self._revoked_eins: Optional[Set[str]] = None
        self._registry_eins: Optional[Set[str]] = None

        # Computed at load time
        self._verified_eins: Optional[Set[str]] = None
        self._unverified_eins: Optional[Set[str]] = None
        self._load_error: Optional[str] = None

    def _load_manifest(self) -> Optional[Dict]:
        """Load and cache the eligibility manifest."""
        if self._manifest_cache is not None:
            return self._manifest_cache

        try:
            with open(self.manifest_path, "r") as f:
                self._manifest_cache = json.load(f)
            return self._manifest_cache
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self._load_error = f"Manifest error: {e}"
            return None

    def _get_manifest_age_hours(self) -> Optional[float]:
        """Get age of manifest in hours."""
        manifest = self._load_manifest()
        if not manifest or "generated_at" not in manifest:
            return None

        try:
            generated = datetime.fromisoformat(manifest["generated_at"].replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            return (now - generated).total_seconds() / 3600
        except (ValueError, TypeError):
            return None

    def _is_manifest_fresh(self) -> bool:
        """Check if manifest is less than 7 days old."""
        age = self._get_manifest_age_hours()
        if age is None:
            return False
        return age < 168  # 7 days in hours

    def _load_pub78(self) -> Set[str]:
        """Parse Publication 78 file to get eligible EINs.

        Format: pipe-delimited (|)
        Columns: [0]=EIN [1]=... [5]=DEDUCTIBILITY_CODE ...

        Only include EINs that are:
        - in the registry (EIN exists in registry_enriched)
        - have approved deductibility codes (PC, POF, SC, IND, GOV)
        """
        if self._pub78_eins is not None:
            return self._pub78_eins

        manifest = self._load_manifest()
        if not manifest or "sources" not in manifest:
            return set()

        pub78_source = next((s for s in manifest["sources"] if s["name"] == "pub78"), None)
        if not pub78_source:
            return set()

        pub78_path = pub78_source.get("path")
        if not pub78_path or not Path(pub78_path).exists():
            self._load_error = f"Publication 78 file not found: {pub78_path}"
            return set()

        # Approved deductibility codes from IRS Publication 78
        PUB78_CODES = {"PC", "POF", "SC", "IND", "GOV"}

        # Load registry EINs to filter (only count if in registry)
        registry_eins = self._load_registry_eins()

        eins = set()
        try:
            with open(pub78_path, "r", encoding="utf-8", errors="replace", newline="") as f:
                reader = csv.reader(f, delimiter="|")
                for row in reader:
                    if not row or len(row) < 6:  # Need at least columns 0-5
                        continue
                    ein = row[0].strip()
                    if not ein or len(ein) != 9 or not ein.isdigit():
                        continue
                    # Only count if in registry
                    if ein not in registry_eins:
                        continue
                    # Check deductibility code (column 5, index 5)
                    code = row[5].strip().upper() if len(row) > 5 else ""
                    if code in PUB78_CODES:
                        eins.add(ein)
        except Exception as e:
            self._load_error = f"Failed to parse pub78: {e}"
            return set()

        self._pub78_eins = eins
        return eins

    def _load_bmf(self) -> Set[str]:
        """Parse BMF file to get eligible EINs.

        CSV format from IRS EO Business Master File.
        Column: EIN (first column, 9-digit)
        Filter: subsection 03 (charitable) + deductibility 1
        """
        if self._bmf_eins is not None:
            return self._bmf_eins

        manifest = self._load_manifest()
        if not manifest or "sources" not in manifest:
            return set()

        bmf_source = next((s for s in manifest["sources"] if s["name"] == "eo_bmf"), None)
        if not bmf_source:
            return set()

        bmf_path = bmf_source.get("path")
        if not bmf_path or not Path(bmf_path).exists():
            self._load_error = f"BMF file not found: {bmf_path}"
            return set()

        eins = set()
        try:
            with open(bmf_path, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ein = row.get("EIN", "").strip()
                    subsection = row.get("SUBSECTION", "").strip()
                    deductibility = row.get("DEDUCTIBILITY", "").strip()

                    # Only include charitable (03) with deductibility 1
                    if len(ein) == 9 and ein.isdigit() and subsection == "03" and deductibility == "1":
                        eins.add(ein)
        except Exception as e:
            self._load_error = f"Failed to parse BMF: {e}"
            return set()

        self._bmf_eins = eins
        return eins

    def _load_registry_eins(self) -> Set[str]:
        """Load all EINs from registry to filter revocations (only count revoked if in registry)."""
        if self._registry_eins is not None:
            return self._registry_eins

        eins = set()
        try:
            with sqlite3.connect(self.db_path, timeout=30) as db:
                cursor = db.execute("SELECT DISTINCT EIN FROM registry_enriched")
                eins = {row[0] for row in cursor.fetchall()}
        except sqlite3.Error as e:
            self._load_error = f"Failed to load registry EINs: {e}"

        self._registry_eins = eins
        return eins

    def _load_revocations(self) -> Set[str]:
        """Parse auto-revocation file to get CURRENTLY revoked EINs.

        Format: Pipe-delimited (|), uses csv reader
        Columns: [0]=EIN [1]=NAME [2]=SECONDARY_NAME [3]=ADDRESS [4]=CITY [5]=STATE [6]=ZIP
                 [7]=COUNTRY [8]=SUBSECTION [9]=REVOCATION_DATE [10]=REINSTATEMENT_DATE [11]=...

        Only include orgs that are:
        - in the registry (EIN exists in registry_enriched)
        - currently revoked (empty reinstatement date in column 11, index 11)
        """
        if self._revoked_eins is not None:
            return self._revoked_eins

        manifest = self._load_manifest()
        if not manifest or "sources" not in manifest:
            return set()

        rev_source = next((s for s in manifest["sources"] if s["name"] == "auto_revocation"), None)
        if not rev_source:
            return set()

        rev_path = rev_source.get("path")
        if not rev_path or not Path(rev_path).exists():
            self._load_error = f"Revocation file not found: {rev_path}"
            return set()

        # Load registry EINs to filter (only count revoked if in registry)
        registry_eins = self._load_registry_eins()

        eins = set()
        try:
            with open(rev_path, "r", encoding="utf-8", errors="replace", newline="") as f:
                reader = csv.reader(f, delimiter="|")
                for row in reader:
                    if not row or len(row) < 12:  # Need at least 12 columns (0-11)
                        continue
                    ein = row[0].strip()
                    if not ein or len(ein) != 9 or not ein.isdigit():
                        continue
                    # Only count if in registry
                    if ein not in registry_eins:
                        continue
                    # Reinstatement date is column 11 (index 11)
                    reinstatement = row[11].strip() if len(row) > 11 else ""
                    # Only count as revoked if reinstatement date is empty
                    if not reinstatement:
                        eins.add(ein)
        except Exception as e:
            self._load_error = f"Failed to parse revocations: {e}"
            return set()

        self._revoked_eins = eins
        return eins

    def _compute_eligibility_sets(self):
        """Compute verified and unverified sets from source files."""
        if self._verified_eins is not None:
            return  # Already computed

        pub78 = self._load_pub78()
        bmf = self._load_bmf()
        revoked = self._load_revocations()

        # verified = (Pub78 ∩ BMF) - revoked
        self._verified_eins = (pub78 & bmf) - revoked

        # unverified = (BMF - Pub78) - revoked
        self._unverified_eins = (bmf - pub78) - revoked

    def _get_verified_eins(self) -> Set[str]:
        """Get set of verified eligible EINs (Pub78 + BMF, not revoked)."""
        self._compute_eligibility_sets()
        return self._verified_eins or set()

    def _get_unverified_eins(self) -> Set[str]:
        """Get set of BMF-only (unverified) EINs."""
        self._compute_eligibility_sets()
        return self._unverified_eins or set()

    def _get_revoked_eins(self) -> Set[str]:
        """Get set of revoked EINs."""
        self._load_revocations()
        return self._revoked_eins or set()

    def _check_exception_possible(self, ein: str) -> bool:
        """Check if organization might be a church or group ruling.

        These may not appear in Pub78 but are eligible per RP 2018-32.
        Query database for church/group ruling codes.
        """
        if not ein or len(ein) != 9:
            return False

        try:
            with sqlite3.connect(self.db_path, timeout=30) as db:
                cursor = db.execute(
                    """
                    SELECT ntee1 FROM registry_enriched
                    WHERE EIN=? LIMIT 1
                    """,
                    (ein,),
                )
                row = cursor.fetchone()
                if row and row[0]:
                    ntee = row[0]
                    # Church groups: X20, X25, etc.
                    return ntee.startswith("X") or "group" in ntee.lower()
        except sqlite3.Error:
            pass

        return False

    def should_show_profile_publicly(self, ein: str) -> bool:
        """Determine if organization profile should be shown in search/directory.

        Revoked organizations: hidden from search/directory.
        All other statuses (verified, unverified, unknown): shown.
        """
        if not ein or len(ein) != 9:
            return True  # Assume visible if lookup fails

        status = self.get_eligibility_status(ein)
        return status != "revoked"

    def get_eligibility_status(self, ein: str) -> str:
        """Get eligibility status for a single EIN.

        Returns one of: verified, unverified, revoked, unknown, exception_possible
        """
        if not ein or len(ein) != 9:
            return "unknown"

        # Check manifest freshness first
        if not self._is_manifest_fresh():
            return "unknown"

        revoked = self._get_revoked_eins()
        if ein in revoked:
            return "revoked"

        verified = self._get_verified_eins()
        if ein in verified:
            return "verified"

        unverified = self._get_unverified_eins()
        if ein in unverified:
            return "unverified"

        # Check if exception_possible (church/group ruling)
        if self._check_exception_possible(ein):
            return "exception_possible"

        return "unknown"

    def get_eligibility_fields(self, ein: str) -> Dict:
        """Get full eligibility context for an organization.

        Returns dict with: status, checked_at, sources, explanation
        """
        if not ein or len(ein) != 9:
            return {
                "irs_eligibility_status": "unknown",
                "irs_eligibility_checked_at": None,
                "irs_eligibility_sources": [],
                "irs_eligibility_explanation": "Invalid EIN format",
            }

        status = self.get_eligibility_status(ein)
        manifest = self._load_manifest()
        checked_at = manifest.get("generated_at") if manifest else None

        explanations = {
            "verified": "Current IRS BMF, Publication 78, and revocation records support tax-deductible eligibility.",
            "unverified": "The latest IRS evidence does not include a complete verification. Check the IRS before giving.",
            "revoked": "Do not assume a contribution is tax-deductible without confirming the current IRS status.",
            "unknown": "We do not have complete current IRS evidence for a tax-deductibility statement.",
            "exception_possible": "Some eligible churches and group-ruling subordinates may not appear in Publication 78. Confirm directly with the organization or IRS.",
        }

        sources_map = {
            "verified": ["Publication 78", "BMF subsection 03"],
            "unverified": ["BMF subsection 03"],
            "revoked": ["IRS auto-revocation list"],
            "unknown": [],
            "exception_possible": ["IRS Publication 78", "IRS Group Ruling Database"],
        }

        return {
            "irs_eligibility_status": status,
            "irs_eligibility_checked_at": checked_at,
            "irs_eligibility_sources": sources_map.get(status, []),
            "irs_eligibility_explanation": explanations.get(status, "Unknown status"),
        }

    def get_revocation_metadata(self, ein: str) -> Optional[Dict]:
        """Get revocation details if organization is revoked.

        Returns dict with revocation date/details if available, None otherwise.
        """
        if self.get_eligibility_status(ein) != "revoked":
            return None

        try:
            with sqlite3.connect(self.db_path, timeout=30) as db:
                cursor = db.execute(
                    """
                    SELECT irs_revoked_date, irs_revoked_date_iso
                    FROM registry_enriched
                    WHERE EIN=? LIMIT 1
                    """,
                    (ein,),
                )
                row = cursor.fetchone()
                if row:
                    return {
                        "revoked": True,
                        "revoked_date": row[1] or row[0],  # Prefer ISO format
                    }
        except sqlite3.Error:
            pass

        return None

    def get_badge_text(self, ein: str) -> str:
        """Get short badge text for a status."""
        status = self.get_eligibility_status(ein)
        badges = {
            "verified": "✓ IRS eligibility verified",
            "unverified": "⚠ Tax deductibility not verified",
            "revoked": "✗ IRS revocation record found",
            "unknown": "? Tax status not verified",
            "exception_possible": "ℹ IRS listing may not tell the whole story",
        }
        return badges.get(status, "Status unknown")

    def get_detail_text(self, ein: str) -> str:
        """Get detailed explanation for a status."""
        status = self.get_eligibility_status(ein)
        explanations = {
            "verified": "Current IRS BMF, Publication 78, and revocation records support tax-deductible eligibility.",
            "unverified": "The latest IRS evidence does not include a complete verification. Check the IRS before giving.",
            "revoked": "Do not assume a contribution is tax-deductible without confirming the current IRS status.",
            "unknown": "We do not have complete current IRS evidence for a tax-deductibility statement.",
            "exception_possible": "Some eligible churches and group-ruling subordinates may not appear in Publication 78. Confirm directly with the organization or IRS.",
        }
        return explanations.get(status, "Unknown status")

    def should_show_donate_prompt(self, ein: str) -> bool:
        """Should organization show donate prompt?

        Returns False only for revoked organizations.
        Unknown/unverified show warning but still allow donation.
        """
        status = self.get_eligibility_status(ein)
        return status != "revoked"

    def get_wallet_disclaimer(self, ein: str) -> Optional[str]:
        """Get wallet disclaimer text if needed.

        Returns disclaimer text for historical wallet entries.
        """
        status = self.get_eligibility_status(ein)
        if status == "revoked":
            return "Daanaa recorded this organization as not revoked when you saved it. Status has since changed. Do not assume this contribution is tax-deductible. See IRS Publication 526."
        return None


# Module-level API for Flask integration
_helper: Optional[IrsEligibilityHelper] = None


def initialize_helper(db_path: str, manifest_path: str):
    """Initialize the helper for use across the application."""
    global _helper
    _helper = IrsEligibilityHelper(db_path, manifest_path)


def get_eligibility_status(ein: str) -> str:
    """Get status for an EIN (module level)."""
    if not _helper:
        return "unknown"
    return _helper.get_eligibility_status(ein)


def get_eligibility_fields(ein: str) -> Dict:
    """Get full eligibility context (module level)."""
    if not _helper:
        return {
            "irs_eligibility_status": "unknown",
            "irs_eligibility_checked_at": None,
            "irs_eligibility_sources": [],
            "irs_eligibility_explanation": "Helper not initialized",
        }
    return _helper.get_eligibility_fields(ein)


def should_show_profile_publicly(ein: str) -> bool:
    """Check if profile should be shown in search/directory (module level)."""
    if not _helper:
        return True
    return _helper.should_show_profile_publicly(ein)


def should_show_donate_prompt(ein: str) -> bool:
    """Check if donate prompt should show (module level)."""
    if not _helper:
        return True
    return _helper.should_show_donate_prompt(ein)


def get_revocation_metadata(ein: str) -> Optional[Dict]:
    """Get revocation details if revoked (module level)."""
    if not _helper:
        return None
    return _helper.get_revocation_metadata(ein)


def get_wallet_disclaimer(ein: str) -> Optional[str]:
    """Get wallet disclaimer if needed (module level)."""
    if not _helper:
        return None
    return _helper.get_wallet_disclaimer(ein)
