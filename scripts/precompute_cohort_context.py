#!/usr/bin/env python3
"""
Precompute cause-cohort financial context for UNSCORED organizations.

For the ~79% of orgs we have no 990 financials for, we still know their NTEE
code. This script rolls up the SCORED population by NTEE subcategory (NTEECC,
e.g. "S21") and by broad NTEE1 (e.g. "S"), so an unscored org can be shown the
*typical* financial shape of organizations in its cause area — clearly framed
as "about this cause area, not this org" (Stewardship P3/P4).

Output: precompute_output/cohort_context.json
  {
    "by_nteecc": { "S21": {median_reserve, p25, p75, healthy_rate, n}, ... },
    "by_ntee1":  { "S":   {median_reserve, p25, p75, healthy_rate, n}, ... },
    "generated": "<iso>", "source_scored_orgs": <int>, "min_sample": 30
  }

Stewardship guardrails enforced HERE (not just in UI):
  - MIN_SAMPLE: buckets with fewer than this many scored orgs are dropped, so we
    never quote a "typical" that rests on a handful of orgs (no false precision).
  - Reserves are summarized with robust percentiles (median/P25/P75), never a
    mean, so a few huge-endowment outliers can't distort the "typical".
  - We publish the sample size N so the UI can always show what the number rests on.

Run nightly via the existing pipeline. Pure read of the registry; writes one
small JSON (a few hundred keys).
"""

import json
import sqlite3
import statistics
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path('data/merit_registry.db')
OUT_PATH = Path('precompute_output/cohort_context.json')

# Below this many scored orgs in a bucket, we do not publish a "typical" for it.
MIN_SAMPLE = 30

# Reserves above this (months) are real but rare (large endowments). Percentiles
# already resist them; we keep raw values and let P25/median/P75 do the work.


def _summarize(reserves, signals):
    """Robust summary of one bucket. reserves: list[float], signals: list[str]."""
    n = len(reserves)
    reserves_sorted = sorted(reserves)
    # statistics.quantiles needs n>=2; guard small (already gated by MIN_SAMPLE).
    qs = statistics.quantiles(reserves_sorted, n=4)  # [P25, P50, P75]
    healthy = sum(1 for s in signals if s == 'HEALTHY')
    return {
        'median_reserve': round(qs[1], 1),
        'p25': round(qs[0], 1),
        'p75': round(qs[2], 1),
        'healthy_rate': round(100.0 * healthy / n, 1),
        'n': n,
    }


def build():
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute(
        """
        SELECT NTEECC, NTEE1, months_of_reserve, merit_health_signal_v5
        FROM registry_enriched
        WHERE merit_archetype_v5 IS NOT NULL
          AND months_of_reserve IS NOT NULL
          AND months_of_reserve >= 0
        """
    )

    by_cc = {}   # NTEECC -> {reserves: [], signals: []}
    by_b1 = {}   # NTEE1  -> {reserves: [], signals: []}
    total = 0

    for nteecc, ntee1, reserve, signal in cur:
        total += 1
        signal = signal or ''
        try:
            reserve = float(reserve)
        except (TypeError, ValueError):
            continue
        if nteecc:
            b = by_cc.setdefault(nteecc, {'reserves': [], 'signals': []})
            b['reserves'].append(reserve)
            b['signals'].append(signal)
        if ntee1:
            b = by_b1.setdefault(ntee1, {'reserves': [], 'signals': []})
            b['reserves'].append(reserve)
            b['signals'].append(signal)

    conn.close()

    out_cc = {
        cc: _summarize(b['reserves'], b['signals'])
        for cc, b in by_cc.items()
        if len(b['reserves']) >= MIN_SAMPLE
    }
    out_b1 = {
        b1: _summarize(b['reserves'], b['signals'])
        for b1, b in by_b1.items()
        if len(b['reserves']) >= MIN_SAMPLE
    }

    result = {
        'by_nteecc': out_cc,
        'by_ntee1': out_b1,
        'generated': datetime.now(timezone.utc).isoformat(),
        'source_scored_orgs': total,
        'min_sample': MIN_SAMPLE,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2))

    print(f"✓ cohort_context.json written")
    print(f"  scored orgs aggregated: {total:,}")
    print(f"  NTEECC buckets (N>={MIN_SAMPLE}): {len(out_cc)}")
    print(f"  NTEE1  buckets (N>={MIN_SAMPLE}): {len(out_b1)}")
    # Show a couple samples for sanity
    for cc in list(out_cc)[:3]:
        print(f"  {cc}: {out_cc[cc]}")


if __name__ == '__main__':
    build()
