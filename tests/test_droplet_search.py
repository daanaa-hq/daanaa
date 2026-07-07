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
    os.environ["PRECOMPUTE_DIR"] = str(data_dir)
    sys.path.insert(0, str(ROOT / "scripts"))
    import droplet_api
    # Module may have been imported with a different DATA_DIR; pin it.
    droplet_api.DATA_DIR = Path(str(data_dir))
    return droplet_api.app.test_client()


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
