#!/usr/bin/env python3
"""
Helper function to enrich org responses with v5.0 scoring data.

Adds to any org dict:
- archetype_v5: Financial operating model
- band_v5: Revenue size band
- peer_benchmarks_v5: P25, P50, P75 for reserves + health rate
- donor_context_v5: Explanatory copy for donors
"""

import json
import sqlite3
from pathlib import Path

DB = Path.home() / "meritgiving/data/merit_registry.db"
COHORT_PATH = Path.home() / "meritgiving/precompute_output/cohort_context.json"

# Loaded once, cached in-process. Small file (a few hundred keys).
_COHORT_CACHE = None


def _load_cohort():
    global _COHORT_CACHE
    if _COHORT_CACHE is None:
        try:
            _COHORT_CACHE = json.loads(COHORT_PATH.read_text())
        except Exception:
            _COHORT_CACHE = {'by_nteecc': {}, 'by_ntee1': {}}
    return _COHORT_CACHE


def get_cohort_context(nteecc: str | None, ntee1: str | None) -> dict | None:
    """
    Cause-cohort financial context for an UNSCORED org.

    Returns the *typical* financial shape of organizations in this org's cause
    area, drawn from the scored population — explicitly NOT a statement about
    this org's own finances. Caller must only attach this when the org has no
    v5_context (no real financials of its own).

    Prefers the narrow NTEE subcategory (NTEECC); falls back to the broad NTEE1
    bucket; returns None if neither has a large enough sample (suppressed in the
    precompute step). The returned dict carries `n` so the UI can always show
    what the typical rests on, and `level` so the UI can word it honestly.
    """
    data = _load_cohort()
    if nteecc:
        b = data.get('by_nteecc', {}).get(nteecc)
        if b:
            return {**b, 'level': 'subcategory', 'ntee_code': nteecc}
    if ntee1:
        b = data.get('by_ntee1', {}).get(ntee1)
        if b:
            return {**b, 'level': 'broad', 'ntee_code': ntee1}
    return None

BENCHMARKS = {
    ('donation_funded', 'micro'): {
        'reserves_p25': 6.2, 'reserves_p50': 19.2, 'reserves_p75': 61.8,
        'healthy_rate': 49.0,
    },
    ('donation_funded', 'professional'): {
        'reserves_p25': 4.7, 'reserves_p50': 12.9, 'reserves_p75': 32.8,
        'healthy_rate': 54.6,
    },
    ('donation_funded', 'established'): {
        'reserves_p25': 4.5, 'reserves_p50': 11.4, 'reserves_p75': 26.4,
        'healthy_rate': 51.2,
    },
    ('fee_for_service', 'micro'): {
        'reserves_p25': 8.0, 'reserves_p50': 21.0, 'reserves_p75': 40.0,
        'healthy_rate': 50.0,
    },
    ('fee_for_service', 'professional'): {
        'reserves_p25': 5.0, 'reserves_p50': 10.0, 'reserves_p75': 20.0,
        'healthy_rate': 45.0,
    },
    ('fee_for_service', 'established'): {
        'reserves_p25': 4.0, 'reserves_p50': 8.8, 'reserves_p75': 18.0,
        'healthy_rate': 42.0,
    },
    ('endowment', 'micro'): {
        'reserves_p25': 120.0, 'reserves_p50': 120.0, 'reserves_p75': 120.0,
        'healthy_rate': 98.0,
    },
    ('endowment', 'professional'): {
        'reserves_p25': 120.0, 'reserves_p50': 120.0, 'reserves_p75': 120.0,
        'healthy_rate': 99.0,
    },
    ('endowment', 'established'): {
        'reserves_p25': 120.0, 'reserves_p50': 120.0, 'reserves_p75': 120.0,
        'healthy_rate': 99.0,
    },
}

def get_v5_context(ein: str) -> dict | None:
    """
    Retrieve v5.0 scoring context for an org.
    Returns a dict with archetype, band, benchmarks, and donor copy.
    """
    conn = sqlite3.connect(str(DB))
    c = conn.cursor()

    c.execute("""
        SELECT
            merit_archetype_v5,
            merit_archetype_v5_label,
            merit_band_v5,
            merit_band_v5_label,
            merit_score_v5,
            merit_health_signal_v5,
            merit_peer_group_v5,
            merit_peer_count_v5,
            months_of_reserve
        FROM registry_enriched
        WHERE EIN = ? AND merit_archetype_v5 IS NOT NULL
    """, (ein,))

    row = c.fetchone()
    conn.close()

    if not row:
        return None

    (archetype_key, archetype_label, band_key, band_label,
     score, health_signal, peer_group, peer_count, reserves_mo) = row

    # Get benchmarks
    bench = BENCHMARKS.get((archetype_key, band_key), {})

    # Build response
    context = {
        'archetype': {
            'key': archetype_key,
            'label': archetype_label,
        },
        'band': {
            'key': band_key,
            'label': band_label,
        },
        'peer_group': {
            'label': peer_group,
            'org_count': peer_count,
        },
        'score': {
            'percentile': int(score),
            'health_signal': health_signal,
        },
        'benchmarks': {
            'reserves_months': {
                'p25': bench.get('reserves_p25', 0),
                'p50': bench.get('reserves_p50', 0),
                'p75': bench.get('reserves_p75', 0),
                'your_value': reserves_mo,
            },
            'healthy_rate_peer': bench.get('healthy_rate', 0),
        },
        'donor_explanation': generate_donor_copy(
            archetype_label, band_label, health_signal,
            reserves_mo, bench.get('reserves_p50', 0), peer_count
        ),
    }

    return context

def generate_donor_copy(archetype: str, band: str, health: str,
                        reserves_mo: float, p50: float, peer_count: int) -> str:
    """Generate donor-facing explanation of org's financial position."""
    if not reserves_mo:
        return "Financial data not available from IRS Form 990."

    # Determine health explanation
    if health == 'HEALTHY':
        health_desc = f"Above the typical level for similar organizations, suggesting solid financial stability."
    elif health == 'STABLE':
        health_desc = f"Close to the typical level for similar organizations, showing steady financial management."
    else:  # CAUTION
        health_desc = f"Below the typical level for similar organizations. This organization may be in a growth phase or operating lean by design."

    return (
        f"This organization is a {archetype} nonprofit with a budget in the {band} range. "
        f"Looking at its financial reserves: Organizations like this one typically keep about {int(p50)} months "
        f"of operating costs in reserve. This one has {reserves_mo:.1f} months. {health_desc} "
        f"This comparison is based on public IRS 990 data from {peer_count:,} similar organizations."
    )

if __name__ == '__main__':
    # Test
    import json
    context = get_v5_context('391214392')  # LAKESHORE CAP INC
    if context:
        print(json.dumps(context, indent=2))
    else:
        print("No v5 context found")
