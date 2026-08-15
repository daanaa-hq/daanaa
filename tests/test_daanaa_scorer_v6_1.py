"""
V6.1 scorer unit tests — Tier 3 threshold lowering + fallback tiers.

Covers the change shipped in commit 9f84651e742 (2026-08-14): Tier 3 threshold
lowered from 5 to 3 scoreable peers, plus new Tier 3b (NTEE1 x Band) and
Tier 4 (Archetype x Band) fallback peer groups, aimed at lifting percentile
coverage from 29.5% to 76.4%.

These are pure-function unit tests against compute_revenue_percentiles() and
get_revenue_band()/get_region() — no live database required, so they run in
every CI pass (unlike test_merit_scorer_v5_0.py's opt-in live-data tests).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.scoring.daanaa_scorer import (
    compute_revenue_percentiles,
    get_revenue_band,
    get_region,
)


def make_org(ein, ntee="A20", state="CA", revenue=100000, reserve=6.0, archetype="Donation-Funded"):
    """Build a dict that mimics a sqlite3.Row for registry_enriched columns."""
    return {
        "EIN": ein,
        "NTEECC": ntee,
        "STATE": state,
        "total_revenue": revenue,
        "months_of_reserve": reserve,
        "merit_archetype_v5_label": archetype,
    }


def make_update(scoring_tier, ein, peer_desc="test", size=1, scoreable=1, confidence="moderate"):
    return (scoring_tier, peer_desc, size, scoreable, confidence, ein)


class TestRevenueBandAndRegion:
    def test_band_thresholds_are_irs_aligned(self):
        assert get_revenue_band(49_999) == "Grassroots"
        assert get_revenue_band(50_000) == "Small"
        assert get_revenue_band(199_999) == "Small"
        assert get_revenue_band(200_000) == "Mid"
        assert get_revenue_band(499_999) == "Mid"
        assert get_revenue_band(500_000) == "Established"
        assert get_revenue_band(4_999_999) == "Established"
        assert get_revenue_band(5_000_000) == "Major"

    def test_band_none_for_missing_or_zero_revenue(self):
        assert get_revenue_band(None) is None
        assert get_revenue_band(0) is None

    def test_region_maps_known_state(self):
        assert get_region("CA") == "West"
        assert get_region("NY") == "Northeast"

    def test_region_none_for_unknown_state(self):
        assert get_region("XX") is None
        assert get_region(None) is None


class TestTier3ThresholdLowering:
    """Regression test for the exact change in commit 9f84651e742.

    Before the fix, Tier 3 required >=5 scoreable peers (percentile None for
    3-4 peer groups). After the fix, 3 scoreable peers is enough to get a
    MEDIUM-confidence percentile. This is the failing-first case: with the
    old threshold this test's core assertion (percentile is not None) fails.
    """

    def test_org_with_exactly_3_scoreable_peers_gets_a_percentile(self):
        orgs = [make_org(f"{i}", ntee="B25", revenue=100000 * i) for i in range(1, 4)]  # 3 orgs
        updates = [make_update("3_Broad_Category", org["EIN"]) for org in orgs]

        results = compute_revenue_percentiles(orgs, updates)

        for org in orgs:
            percentile, confidence, peer_count = results[org["EIN"]]
            assert peer_count == 3
            assert percentile is not None, (
                "Tier 3 org with 3 scoreable peers must receive a percentile "
                "(threshold was lowered from 5 to 3 in v6.1)"
            )
            assert confidence == "MEDIUM"

    def test_org_with_only_2_scoreable_peers_stays_null(self):
        """Below the new floor of 3, percentile must remain NULL — the
        threshold was lowered, not removed."""
        orgs = [make_org(f"{i}", ntee="C30", revenue=100000 * i) for i in range(1, 3)]  # 2 orgs
        updates = [make_update("3_Broad_Category", org["EIN"]) for org in orgs]

        results = compute_revenue_percentiles(orgs, updates)

        for org in orgs:
            percentile, confidence, peer_count = results[org["EIN"]]
            assert peer_count == 2
            assert percentile is None, "Below the 3-peer floor, percentile must stay NULL (privacy/honesty)"
            assert confidence == "LOW"


class TestConfidenceTierBoundaries:
    def test_high_confidence_at_25_peers(self):
        orgs = [make_org(f"{i}", ntee="D40", revenue=1000 * i) for i in range(1, 26)]  # 25 orgs
        updates = [make_update("3_Broad_Category", org["EIN"]) for org in orgs]

        results = compute_revenue_percentiles(orgs, updates)
        _, confidence, peer_count = results[orgs[0]["EIN"]]
        assert peer_count == 25
        assert confidence == "HIGH"

    def test_medium_confidence_below_25_peers(self):
        orgs = [make_org(f"{i}", ntee="D40", revenue=1000 * i) for i in range(1, 25)]  # 24 orgs
        updates = [make_update("3_Broad_Category", org["EIN"]) for org in orgs]

        results = compute_revenue_percentiles(orgs, updates)
        _, confidence, peer_count = results[orgs[0]["EIN"]]
        assert peer_count == 24
        assert confidence == "MEDIUM"


class TestTier3bAndTier4Fallbacks:
    """New peer-group fallbacks added in v6.1 for orgs that don't clear the
    Tier 1-3 thresholds (no region, or NTEE2 group too sparse)."""

    def test_tier3b_ntee1_band_peer_key_used_when_tagged(self):
        # All revenues held within the "Mid" band ($200K-$500K) so the 5 orgs
        # actually land in the same (ntee1, band) peer group.
        orgs = [make_org(f"{i}", ntee="E50", revenue=200000 + 10000 * i) for i in range(1, 6)]
        updates = [make_update("3b_Broad_Category", org["EIN"]) for org in orgs]

        results = compute_revenue_percentiles(orgs, updates)

        for org in orgs:
            percentile, confidence, peer_count = results[org["EIN"]]
            assert peer_count == 5
            assert percentile is not None

    def test_tier4_archetype_band_peer_key_used_when_tagged(self):
        # Same-band revenues (see comment above) so all 5 orgs share one
        # (archetype, band) peer group.
        orgs = [
            make_org(f"{i}", ntee=None, revenue=200000 + 10000 * i, archetype="Fee-for-Service")
            for i in range(1, 6)
        ]
        updates = [make_update("4_Archetype_Only", org["EIN"]) for org in orgs]

        results = compute_revenue_percentiles(orgs, updates)

        for org in orgs:
            percentile, confidence, peer_count = results[org["EIN"]]
            assert peer_count == 5
            assert percentile is not None

    def test_orgs_without_a_recognized_tier_get_no_peer_key(self):
        """An org whose scoring_tier isn't one of the five known tiers must
        not silently join some other group's peer list."""
        orgs = [make_org("1", ntee="F60")]
        updates = [make_update("unknown_tier", "1")]

        results = compute_revenue_percentiles(orgs, updates)
        percentile, confidence, peer_count = results["1"]
        assert peer_count == 0
        assert percentile is None


class TestPercentileMath:
    def test_percentile_rank_is_monotonic_with_revenue(self):
        """Higher revenue within the same peer group must never produce a
        lower percentile than a lower-revenue peer."""
        orgs = [make_org(str(i), ntee="G70", revenue=100000 * i) for i in range(1, 11)]  # 10 orgs
        updates = [make_update("3_Broad_Category", org["EIN"]) for org in orgs]

        results = compute_revenue_percentiles(orgs, updates)
        percentiles = [results[org["EIN"]][0] for org in orgs]

        assert percentiles == sorted(percentiles), "Percentile must increase with revenue"
        assert percentiles[-1] == 100, "Top earner in its peer group should rank at the 100th percentile"

    def test_org_missing_revenue_is_excluded_from_percentile(self):
        orgs = [make_org(str(i), ntee="H80", revenue=100000 * i) for i in range(1, 5)]
        orgs.append(make_org("5", ntee="H80", revenue=None))
        updates = [make_update("3_Broad_Category", org["EIN"]) for org in orgs]

        results = compute_revenue_percentiles(orgs, updates)
        percentile, _, _ = results["5"]
        assert percentile is None, "Org with no revenue cannot be ranked, regardless of peer group size"
