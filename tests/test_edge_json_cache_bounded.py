"""Edge per-worker JSON cache must be bounded.

2026-07-18 incident: droplet_api.py's `_json_cache` cached every precompute
.json.gz it ever served, forever, per worker. Org detail traffic (1.76M
distinct files, crawlers walking them) grew each gunicorn worker to ~475MB in
hours on the 2GB droplet, filled swap completely, and starved the OS page
cache for the 1.75GB search.db — turning sub-second searches into 13s cold
random I/O even though the query plan was correct. This test pins the fix:
the cache evicts once it reaches its cap.

Run: pytest tests/test_edge_json_cache_bounded.py -v
"""

import gzip
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
EDGE_API = REPO / "scripts" / "droplet_api.py"


@pytest.fixture(scope="module")
def edge():
    spec = importlib.util.spec_from_file_location("droplet_api_under_test", EDGE_API)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["droplet_api_under_test"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.principle
def test_json_cache_is_bounded(edge, tmp_path):
    cap = getattr(edge, "_JSON_CACHE_MAX", None)
    assert cap is not None and cap > 0, (
        "droplet_api.py lost _JSON_CACHE_MAX — the per-worker JSON cache "
        "must be bounded (2026-07-18 swap-thrash incident)")

    edge._json_cache.clear()
    n = cap + 50
    for i in range(n):
        p = tmp_path / f"f{i}.json.gz"
        with gzip.open(p, "wt", encoding="utf-8") as f:
            json.dump({"i": i}, f)
        assert edge.load_json_gz(p) == {"i": i}

    assert len(edge._json_cache) <= cap, (
        f"cache grew to {len(edge._json_cache)} entries past cap {cap} — "
        "eviction is not happening")


@pytest.mark.principle
def test_json_cache_keeps_recently_used(edge, tmp_path):
    """Eviction must be LRU-shaped: a key re-read just before overflow
    survives, so hot content files aren't churned out by org-page crawls."""
    cap = edge._JSON_CACHE_MAX
    edge._json_cache.clear()

    hot = tmp_path / "hot.json.gz"
    with gzip.open(hot, "wt", encoding="utf-8") as f:
        json.dump({"hot": True}, f)
    edge.load_json_gz(hot)

    for i in range(cap - 1):
        p = tmp_path / f"cold{i}.json.gz"
        with gzip.open(p, "wt", encoding="utf-8") as f:
            json.dump({"i": i}, f)
        edge.load_json_gz(p)
        edge.load_json_gz(hot)  # keep hot entry recent

    # One more insert forces an eviction; the hot key must survive it.
    p = tmp_path / "one_more.json.gz"
    with gzip.open(p, "wt", encoding="utf-8") as f:
        json.dump({"x": 1}, f)
    edge.load_json_gz(p)

    assert str(hot) in edge._json_cache, (
        "recently-used entry was evicted — eviction is not LRU")
