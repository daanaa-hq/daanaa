"""Droplet API search/filter regression tests.

Runs the droplet Flask app in-process against the local copy of the droplet
search DB (data/droplet_search.db). Guards the 2026-06-09 production bug:
multi-category (ntee=R,I) returned 0 results and revenue filters were
silently ignored — silent wrong results violate the trust principles harder
than errors do.

Run: pytest tests/test_droplet_search.py -v
Skips cleanly if the local droplet DB copy is missing.
"""
import os
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
DB = ROOT / "data" / "droplet_search.db"

pytestmark = pytest.mark.skipif(not DB.exists(), reason="no local droplet DB copy")


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    data_dir = tmp_path_factory.mktemp("droplet_data")
    (data_dir / "search.db").symlink_to(DB)
    browse = ROOT / "precompute_output" / "browse"
    if browse.exists():
        (data_dir / "browse").symlink_to(browse)
    old_precompute = os.environ.get("PRECOMPUTE_DIR")
    os.environ["PRECOMPUTE_DIR"] = str(data_dir)
    try:
        # Load the SHIPPED droplet API under a distinct module name — do NOT
        # `sys.path.insert + import droplet_api`: that steals the
        # sys.modules['droplet_api'] slot from the root home-variant module
        # that test_routing.py / test_spa_fallback.py target.
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "droplet_api_shipped_search", str(ROOT / "scripts" / "droplet_api.py"))
        droplet_api = importlib.util.module_from_spec(spec)
        sys.modules["droplet_api_shipped_search"] = droplet_api
        spec.loader.exec_module(droplet_api)
        droplet_api.DATA_DIR = Path(str(data_dir))
        yield droplet_api.app.test_client()
    finally:
        if old_precompute is None:
            os.environ.pop("PRECOMPUTE_DIR", None)
        else:
            os.environ["PRECOMPUTE_DIR"] = old_precompute


def test_multi_category_returns_results(client):
    d = client.get('/api/organizations?ntee=R,I&per_page=5').get_json()
    assert d['total'] > 0, "multi-category (ntee=R,I) returns 0 — the 2026-06-09 prod bug"
    assert all(o['NTEE1'] in ('R', 'I') for o in d['organizations'])


def test_revenue_filter_is_applied(client):
    base = client.get('/api/organizations?ntee=R&per_page=1').get_json()['total']
    d = client.get(
        '/api/organizations?ntee=R&min_revenue=50000&max_revenue=100000&per_page=5'
    ).get_json()
    assert 0 < d['total'] < base, "revenue band did not narrow results — filter ignored"
    assert all(50000 <= o['total_revenue'] <= 100000 for o in d['organizations'])


def test_multi_category_plus_revenue(client):
    """The exact query from the production screenshot."""
    d = client.get(
        '/api/organizations?ntee=R,I&min_revenue=50000&max_revenue=100000&per_page=24'
    ).get_json()
    assert d['total'] > 0
    for o in d['organizations']:
        assert o['NTEE1'] in ('R', 'I') and 50000 <= o['total_revenue'] <= 100000


def test_subcategory_prefix_match(client):
    d = client.get('/api/organizations?sub=I21&per_page=10').get_json()
    assert d['total'] > 0
    assert all(o['NTEECC'].startswith('I21') for o in d['organizations'])


def test_results_sorted_by_score_desc(client):
    d = client.get('/api/organizations?ntee=R,I&per_page=24').get_json()
    scores = [o.get('merit_score') if o.get('merit_score') is not None else -1
              for o in d['organizations']]
    assert scores == sorted(scores, reverse=True)


def test_keyword_search_with_filters(client):
    d = client.get(
        '/api/organizations?q=legal&ntee=R,I&min_revenue=50000&max_revenue=100000&per_page=5'
    ).get_json()
    assert d['search_type'] == 'fts'
    assert d['total'] > 0
    # accuracy over volume: every result honors every filter
    for o in d['organizations']:
        assert o['NTEE1'] in ('R', 'I') and 50000 <= o['total_revenue'] <= 100000



def test_keyword_directory_search_returns_fts_results(client):
    d = client.get('/api/organizations?q=food&per_page=5').get_json()
    assert d['search_type'] == 'fts'
    assert d['total'] > 0
    assert d['organizations']


def test_filter_indexes_exist():
    """Speed guard: the filter indexes must exist or browse full-scans 1.8M rows."""
    con = sqlite3.connect(str(DB))
    names = {r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='index'")}
    con.close()
    for idx in ('idx_orgs_ntee1_rev', 'idx_orgs_rev', 'idx_orgs_nteecc'):
        assert idx in names, f"missing index {idx} — rebuild_droplet_search_db.py creates it"


# ── QA 2026-07-24 regressions: seeded shuffle + has_revenue routing ──────────
# Both shipped as accepted-but-ignored parameters, which returns confidently
# wrong results rather than an error — the failure mode the trust principles
# care about most.

def test_has_revenue_excludes_orgs_without_revenue(client):
    """has_revenue=1 must not return orgs with null/zero total_revenue.

    Prod bug: `any_filter` omitted has_revenue, so a bare has_revenue=1 never
    reached the DB path (whose SQL is correct) and fell through to the
    precomputed browse files, which ignore the filter entirely.
    """
    d = client.get('/api/organizations?per_page=25&has_revenue=1').get_json()
    assert d['organizations'], "no rows returned — cannot evaluate the filter"
    bad = [o for o in d['organizations'] if not o.get('total_revenue')]
    assert not bad, (
        f"{len(bad)}/{len(d['organizations'])} rows have null/zero revenue "
        f"despite has_revenue=1, e.g. {bad[0].get('organization_name')!r}"
    )


def _eins(payload):
    return [o['EIN'] for o in payload['organizations']]


def test_same_seed_returns_same_order(client):
    """Same seed must reproduce the same slice — the documented session contract.

    Prod bug: shuffle_seed was threaded through both query paths but never
    used; random.randint() ran unseeded, so every request reshuffled. The
    determinism observed against daanaa.org was Cloudflare caching the URL.
    """
    a = _eins(client.get('/api/organizations?sort=random&seed=qa-one&per_page=5').get_json())
    b = _eins(client.get('/api/organizations?sort=random&seed=qa-one&per_page=5').get_json())
    assert a, "random sort returned no rows"
    assert a == b, f"same seed gave different results: {a} vs {b}"


def test_different_seeds_return_different_orders(client):
    """Different seeds must actually shuffle differently."""
    a = _eins(client.get('/api/organizations?sort=random&seed=qa-one&per_page=5').get_json())
    b = _eins(client.get('/api/organizations?sort=random&seed=qa-two&per_page=5').get_json())
    assert a and b
    assert a != b, "different seeds produced an identical page"


def test_seeded_random_paging_advances(client):
    """Page 2 must not repeat page 1 for the same seed."""
    p1 = _eins(client.get('/api/organizations?sort=random&seed=qa-one&per_page=5&page=1').get_json())
    p2 = _eins(client.get('/api/organizations?sort=random&seed=qa-one&per_page=5&page=2').get_json())
    assert p1 and p2
    assert p1 != p2, "page 2 repeated page 1 under the same seed"
