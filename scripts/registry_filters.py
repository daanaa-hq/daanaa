#!/usr/bin/env python3
"""
Canonical registry filters — the SINGLE source of truth for which organizations
count as "public / user-facing" anywhere a number is shown to a user.

Every count, stat, snapshot, and aggregate that reaches the site MUST derive
from DEDUCTIBLE_FILTER. Do not re-spell this predicate inline anywhere else —
import it. If the public definition ever changes, change it HERE and the change
flows to precompute_content.py, export_research_snapshot.py, the overnight
data-quality gate, and the consistency check in one move.

Why this exists (the learning we keep losing):
  - 2026-06-14: the homepage stat drifted to 2.06M because one copy of this
    predicate lacked the revoked exclusion.
  - 2026-06-29: the deployed homepage.json.gz was a stale 1.87M after the
    revoked-status sync dropped the true count to 1,729,314 — nothing
    regenerated or redeployed it.
Centralizing the predicate here, plus check_number_consistency.py + the nightly
refresh_public_numbers.sh, prevents both failure modes.

Mirrors daanaa_api.py / droplet_api.py _DEDUCTIBILITY_FILTER.
"""

# The active, tax-deductible 501(c)(3) set: the same population browse/search
# returns and the only number to put in front of users.
DEDUCTIBLE_FILTER = (
    "subsection = '3' AND deductibility = '1' "
    "AND COALESCE(irs_revoked, 0) != 1 "
    "AND COALESCE(org_status, '') != 'revoked'"
)


def canonical_active_count(conn):
    """Return the canonical public org count from an open sqlite3 connection."""
    return conn.execute(
        f"SELECT COUNT(*) FROM registry_enriched WHERE {DEDUCTIBLE_FILTER}"
    ).fetchone()[0]
