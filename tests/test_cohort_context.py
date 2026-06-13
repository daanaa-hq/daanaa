"""Cause-cohort financial context for UNSCORED orgs.

These pin the two Stewardship guardrails that keep this honest:
  - Suppression: a cause-cohort with fewer than MIN_SAMPLE scored orgs is never
    published, so we never quote a "typical" resting on a handful of orgs (P3,
    no false precision).
  - Fallback: when the narrow NTEE subcategory is too thin/absent, we fall back
    to the broad NTEE1 bucket — and we tell the UI which level we used (`level`)
    so the wording can stay honest.
  - Robustness: the "typical" is the median, so a few huge-endowment outliers
    can't inflate it.

The aggregation reads a SQLite DB, so we build a tiny throwaway DB and point the
enrich module at it.
"""

import json
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import precompute_cohort_context as pcc
import enrich_api_responses as enrich


def _make_db(path, rows):
    """rows: list of (nteecc, ntee1, months_of_reserve, health_signal)."""
    conn = sqlite3.connect(str(path))
    conn.execute(
        """CREATE TABLE registry_enriched (
            NTEECC TEXT, NTEE1 TEXT, months_of_reserve REAL,
            merit_archetype_v5 TEXT, merit_health_signal_v5 TEXT
        )"""
    )
    conn.executemany(
        "INSERT INTO registry_enriched VALUES (?,?,?, 'x', ?)",
        rows,
    )
    conn.commit()
    conn.close()


@pytest.fixture
def built(tmp_path, monkeypatch):
    """Build a cohort_context.json from a controlled population."""
    db = tmp_path / "reg.db"
    out = tmp_path / "cohort_context.json"
    # B20: 40 orgs (above MIN_SAMPLE=30) -> published as subcategory.
    #      reserves 1..39 plus one 9999 outlier; median must stay near ~20.
    # B99: 5 orgs (below MIN_SAMPLE) -> suppressed at subcategory level.
    # Broad "B" gets all 45 -> above MIN_SAMPLE, published as fallback.
    rows = []
    for i in range(1, 40):
        rows.append(("B20", "B", float(i), "HEALTHY" if i > 20 else "CAUTION"))
    rows.append(("B20", "B", 9999.0, "HEALTHY"))  # outlier
    for i in range(5):
        rows.append(("B99", "B", 3.0, "CAUTION"))

    _make_db(db, rows)
    monkeypatch.setattr(pcc, "DB_PATH", db)
    monkeypatch.setattr(pcc, "OUT_PATH", out)
    pcc.build()

    # Point the enrich lookup at the freshly built file and clear its cache.
    monkeypatch.setattr(enrich, "COHORT_PATH", out)
    enrich._COHORT_CACHE = None
    return json.loads(out.read_text())


def test_thin_subcategory_is_suppressed(built):
    # B99 has only 5 orgs — must NOT appear at subcategory level.
    assert "B99" not in built["by_nteecc"]


def test_large_subcategory_is_published(built):
    assert "B20" in built["by_nteecc"]
    assert built["by_nteecc"]["B20"]["n"] == 40


def test_median_resists_outlier(built):
    # 39 values 1..39 + one 9999. Median of 40 values ~ 20, NOT dragged upward.
    median = built["by_nteecc"]["B20"]["median_reserve"]
    assert 18 <= median <= 22, f"median {median} should resist the 9999 outlier"


def test_sample_size_is_published(built):
    # The number the UI shows must be present so users see what it rests on.
    assert built["by_nteecc"]["B20"]["n"] == 40


def test_lookup_prefers_subcategory(built):
    ctx = enrich.get_cohort_context("B20", "B")
    assert ctx is not None
    assert ctx["level"] == "subcategory"
    assert ctx["ntee_code"] == "B20"


def test_lookup_falls_back_to_broad(built):
    # B99 is suppressed at subcategory level, so an org in B99 falls back to "B".
    ctx = enrich.get_cohort_context("B99", "B")
    assert ctx is not None
    assert ctx["level"] == "broad"
    assert ctx["ntee_code"] == "B"


def test_lookup_returns_none_when_nothing_qualifies(built):
    # Unknown codes with no qualifying bucket -> None (UI shows nothing).
    assert enrich.get_cohort_context("Z99", "Z") is None
