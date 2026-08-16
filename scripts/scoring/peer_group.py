#!/usr/bin/env python3
"""
scripts/scoring/peer_group.py

Single source of truth for the v6 peer-group definition: revenue bands,
Census regions, and the tier-key construction that decides which orgs count
as "the same peer group" as a given organization.

Extracted 2026-08-16 from scripts/scoring/daanaa_scorer.py (which now
imports these instead of defining its own copy) after finding that
_find_similar_orgs() in both API files and scripts/core/precompute_similar_orgs.py
were each using a DIFFERENT, disagreeing definition of "similar" than what
Financial Context tells donors a given org is being compared against — see
DECISIONS.md 2026-08-16. Fixing that meant giving every caller (the scorer,
both APIs, and the precompute) the exact same function to call, not four
separately-maintained copies that can drift again.

This module only knows about grouping keys (band, region, tier-key). It does
NOT touch scoring/percentile math — that stays in daanaa_scorer.py.
"""

# Revenue band thresholds (IRS-aligned). None/0 revenue -> no band, since an
# org with no revenue on file can't be meaningfully bucketed by size.
def get_revenue_band(revenue):
    if revenue is None or revenue == 0:
        return None
    if revenue < 50000:
        return "Grassroots"
    elif revenue < 200000:
        return "Small"
    elif revenue < 500000:
        return "Mid"
    elif revenue < 5000000:
        return "Established"
    else:
        return "Major"


# Inclusive [min, max) revenue range for each band -- lets a SQL caller build
# a BETWEEN/comparison clause instead of computing get_revenue_band() in SQL.
# max=None means unbounded above (Major).
REVENUE_BAND_RANGES = {
    "Grassroots": (0.01, 50000),
    "Small": (50000, 200000),
    "Mid": (200000, 500000),
    "Established": (500000, 5000000),
    "Major": (5000000, None),
}


# US Census Bureau region mapping (Northeast, Midwest, South, West).
CENSUS_REGIONS = {
    "Northeast": ["CT", "ME", "MA", "NH", "RI", "VT", "NJ", "NY", "PA"],
    "Midwest": ["IL", "IN", "MI", "OH", "WI", "IA", "KS", "MN", "MO", "NE", "ND", "SD"],
    "South": ["DE", "FL", "GA", "MD", "NC", "SC", "VA", "WV", "AL", "KY", "MS", "TN", "AR", "LA", "OK", "TX"],
    "West": ["AZ", "CO", "ID", "MT", "NV", "NM", "UT", "WY", "AK", "CA", "HI", "OR", "WA"],
}

STATE_TO_REGION = {}
for _region, _states in CENSUS_REGIONS.items():
    for _state in _states:
        STATE_TO_REGION[_state] = _region


def get_region(state):
    return STATE_TO_REGION.get(state)


def get_ntee2(nteecc):
    """First two characters of NTEECC (e.g. 'S21' -> 'S2'). None if unavailable."""
    return nteecc[:2] if nteecc else None


def get_ntee1(nteecc):
    """First character of NTEECC (e.g. 'S21' -> 'S'). None if unavailable."""
    return nteecc[:1] if nteecc else None


def peer_group_criteria(scoring_tier, nteecc, state, total_revenue, archetype):
    """
    Return the exact predicate that defines "the same peer group" as this
    org, matching daanaa_scorer.py's tier-key construction exactly. This is
    the org's OWN persisted scoring_tier -- callers should not recompute a
    tier from scratch, since the scorer already picked the most specific
    tier that had enough scoreable peers at scoring time.

    Returns a dict describing the match, or None if the tier/fields don't
    support a criteria (e.g. unrecognized scoring_tier):
      {
        "tier": "1_Full_Context",
        "ntee2": "S2",           # present for tiers 1, 2, 3
        "ntee1": "S",            # present for tier 3b
        "band": "Established",   # present for tiers 1, 2, 3b, 4
        "region": "Midwest",     # present for tier 1 only
        "archetype": "...",      # present for tier 4 only
      }

    Callers turn this into a SQL WHERE clause or an in-memory index lookup;
    this function only owns what the criteria IS, not how it's queried.
    """
    ntee2 = get_ntee2(nteecc)
    ntee1 = get_ntee1(nteecc)
    band = get_revenue_band(total_revenue)
    region = get_region(state)

    if scoring_tier == "1_Full_Context" and ntee2 and band and region:
        return {"tier": scoring_tier, "ntee2": ntee2, "band": band, "region": region}
    if scoring_tier == "2_Regional_Context" and ntee2 and band:
        return {"tier": scoring_tier, "ntee2": ntee2, "band": band}
    if scoring_tier == "3_Broad_Category" and ntee2:
        return {"tier": scoring_tier, "ntee2": ntee2}
    if scoring_tier == "3b_Broad_Category" and ntee1 and band:
        return {"tier": scoring_tier, "ntee1": ntee1, "band": band}
    if scoring_tier == "4_Archetype_Only" and archetype and band:
        return {"tier": scoring_tier, "archetype": archetype, "band": band}
    return None


def sql_predicate(criteria: dict) -> tuple[str, list]:
    """
    Turn a peer_group_criteria() dict into a parameterized SQL WHERE
    fragment (ANDed conditions, no leading "WHERE") plus its params, against
    registry_enriched's actual columns (NTEECC, NTEE1, total_revenue, STATE,
    merit_archetype_v5_label). Shared by both API files' similar-orgs query
    so "same criteria" isn't reimplemented, and re-verified, twice.
    """
    clauses = []
    params: list = []

    if "ntee2" in criteria:
        clauses.append("NTEECC LIKE ?")
        params.append(criteria["ntee2"] + "%")
    if "ntee1" in criteria:
        clauses.append("NTEE1 = ?")
        params.append(criteria["ntee1"])
    if "archetype" in criteria:
        clauses.append("merit_archetype_v5_label = ?")
        params.append(criteria["archetype"])
    if "band" in criteria:
        band_min, band_max = REVENUE_BAND_RANGES[criteria["band"]]
        if band_max is None:
            clauses.append("total_revenue >= ?")
            params.append(band_min)
        else:
            clauses.append("total_revenue >= ? AND total_revenue < ?")
            params.extend([band_min, band_max])
    if "region" in criteria:
        states = CENSUS_REGIONS[criteria["region"]]
        placeholders = ",".join("?" * len(states))
        clauses.append(f"STATE IN ({placeholders})")
        params.extend(states)

    return " AND ".join(clauses), params
