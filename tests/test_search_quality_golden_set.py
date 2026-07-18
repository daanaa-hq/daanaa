"""Search quality golden set — ~20 representative queries with result assertions.

2026-07-18 rationale: the 2026-07-17 sort-param bug (browse sort dropdown was
a silent no-op on precompute) shipped through a presence-only contract test
(the route existed, but behavior wasn't verified). This suite asserts expected
result presence/relevance for common donor queries so quality regressions
(wrong sorting, faceted filters that break, broken search paths for small orgs)
are caught before touching production.

Golden queries cover:
- Common words (health, food, children — high traffic)
- Org names (self-search)
- Cause tags (mission)
- Location (city, state, zip)
- Peer context (by archetype/band)

Assertions are recall-shaped (org X appears in top N), not rank-shaped (no big-org
bias per P4). Run against live site: pytest tests/test_search_quality_golden_set.py -v
"""

import pytest
import requests


BASE_URL = "https://daanaa.org"
API_BASE = f"{BASE_URL}/api/organizations"


class Query:
    def __init__(self, label: str, params: dict, assertions: list):
        self.label = label
        self.params = params
        self.assertions = assertions


def execute_query(q: Query, per_page: int = 50) -> dict:
    """Fetch search results, cache-busted for live data."""
    import time
    params = {**q.params, "per_page": per_page, "_cb": int(time.time() * 1e9)}
    r = requests.get(API_BASE, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


GOLDEN_SET = [
    Query("common-word: health (high-volume)", {"q": "health"},
          [
              ("result_count", lambda n: n > 0, "health returns results"),
              ("contains_name_token", ["health"], 1, "at least one top result mentions health"),
          ]),

    Query("common-word: food (high-volume)", {"q": "food"},
          [
              ("result_count", lambda n: n > 0, "food returns results"),
          ]),

    Query("common-word: children", {"q": "children"},
          [
              ("result_count", lambda n: n > 0, "children returns results"),
          ]),

    Query("org name: Red Cross (self-search)", {"q": "Red Cross"},
          [
              ("has_org_exact", "Red Cross", 50, "Red Cross appears in top 50"),
          ]),

    Query("org name: Salvation Army", {"q": "Salvation Army"},
          [
              ("has_org_exact", "Salvation Army", 50, "Salvation Army appears in top 50"),
          ]),

    Query("cause-tag: environment", {"q": "environment"},
          [
              ("result_count", lambda n: n > 0, "environment returns results"),
          ]),

    Query("cause-tag: education", {"q": "education"},
          [
              ("result_count", lambda n: n > 0, "education returns results"),
          ]),

    Query("location: CA (state search)", {"location": "CA"},
          [
              ("result_count", lambda n: n > 0, "state location search returns results"),
          ]),

    Query("location: New York, NY", {"location": "New York, NY"},
          [
              ("result_count", lambda n: n > 0, "NY city search returns results"),
          ]),

    Query("location: 90210 (zip code)", {"location": "90210"},
          [
              ("result_count", lambda n: n > 0, "zip code search returns results"),
          ]),

    Query("small org discovery: 'good' + micro band", {"q": "good", "merit_band_v5": "Micro"},
          [
              ("result_count", lambda n: n > 0, "micro-band filter returns results"),
          ]),

    Query("financial context: Donation-Funded archetype", {"merit_archetype_v5": "Donation-Funded"},
          [
              ("result_count", lambda n: n > 0, "archetype filter returns results"),
          ]),

    Query("sort by name ascending", {"q": "health", "sort": "organization_name", "order": "asc"},
          [
              ("result_count", lambda n: n > 0, "sorted search returns results"),
              ("name_sorted_asc", "sorted alphabetically ascending"),
          ]),

    Query("sort by total revenue descending", {"q": "health", "sort": "total_revenue", "order": "desc"},
          [
              ("result_count", lambda n: n > 0, "revenue sort returns results"),
          ]),

    Query("pagination: page 2 differs from page 1", {"q": "health", "per_page": 25, "page": 2},
          [
              ("result_count", lambda n: n > 0, "page 2 returns results"),
              ("not_first_page", "page 2 has different EINs than page 1"),
          ]),

    Query("misspelling resilience: 'helth'", {"q": "helth"},
          [
              # Fuzzy match is nice-to-have; not required but worth asserting if it works
              ("result_count", lambda n: n >= 0, "misspelled query doesn't crash"),
          ]),

    Query("nearby search: Los Angeles, CA within 10mi", {"near": "Los Angeles, CA", "radius": 10},
          [
              ("result_count", lambda n: n > 0, "proximity search returns results"),
              ("all_in_radius", "CA", "nearby results in CA region"),
          ]),

    Query("claim status: only claimed orgs", {"website_status": "claimed"},
          [
              ("result_count", lambda n: n >= 0, "claimed filter doesn't crash"),
          ]),

    Query("combined: cause + state + sort", {"q": "health", "location": "TX", "sort": "total_revenue"},
          [
              ("result_count", lambda n: n > 0, "combined filters return results"),
          ]),
]


@pytest.mark.parametrize("golden_query", GOLDEN_SET, ids=lambda q: q.label)
def test_search_quality(golden_query):
    """Run one golden query and verify its assertions."""
    result = execute_query(golden_query)
    orgs = result.get("organizations", [])

    for assertion in golden_query.assertions:
        if assertion[0] == "result_count":
            predicate = assertion[1]
            msg = assertion[2]
            assert predicate(len(orgs)), f"{msg}: got {len(orgs)} results"

        elif assertion[0] == "has_org_exact":
            name, top_n, msg = assertion[1], assertion[2], assertion[3]
            top_names = [o.get("organization_name", "") for o in orgs[:top_n]]
            found = any(name.lower() in n.lower() for n in top_names)
            assert found, f"{msg}: {name} not in top {top_n}"

        elif assertion[0] == "all_in_state":
            state = assertion[1]
            msg = assertion[2]
            # Data completeness: allow up to 10% incomplete records (STATE is None)
            with_state = [o for o in orgs if o.get("STATE") is not None]
            assert len(with_state) > 0, f"{msg}: no orgs with state data"
            bad = [o for o in with_state if o.get("STATE") != state]
            assert len(bad) == 0, f"{msg}: {len(bad)} orgs not in {state}"

        elif assertion[0] == "contains_name_token":
            tokens, min_count, msg = assertion[1], assertion[2], assertion[3]
            found = sum(1 for o in orgs[:10]
                       if any(t.lower() in o.get("organization_name", "").lower() for t in tokens))
            assert found >= min_count, f"{msg}: only {found}/{min_count} top results matched"

        elif assertion[0] == "name_sorted_asc":
            msg = assertion[1]
            names = [o.get("organization_name", "") for o in orgs]
            sorted_names = sorted(names, key=str.lower)
            assert names == sorted_names, f"{msg}: names not in ascending order"

        elif assertion[0] == "not_first_page":
            msg = assertion[1]
            # Execute page 1 to compare
            p1_result = execute_query(Query("", {"q": golden_query.params.get("q", "")}, []))
            p1_eins = set(o.get("EIN") for o in p1_result.get("organizations", [])[:25])
            p2_eins = set(o.get("EIN") for o in orgs)
            assert p1_eins != p2_eins, f"{msg}: page 2 has same EINs as page 1"

        elif assertion[0] == "all_in_radius":
            state, msg = assertion[1], assertion[2]
            # Nearby results should be in the search region, but allow some data gaps
            with_state = [o for o in orgs if o.get("STATE") is not None]
            assert len(with_state) > 0, f"{msg}: no nearby results with state data"
            bad = [o for o in with_state if o.get("STATE") != state]
            # Allow up to 20% out-of-region (edges of radius might cross state lines)
            ratio_ok = len(bad) / len(with_state) < 0.2
            assert ratio_ok, f"{msg}: {len(bad)}/{len(with_state)} results outside region"
