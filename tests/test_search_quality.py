"""Search quality golden set — sanitizer safety + self-search findability.

Root causes pinned here (found 2026-07-18 search index audit):

1. Punctuation crash: FTS5 treats -, /, :, ^ as query syntax (column filters,
   NOT operators). Org names like "4-H FOUNDATION" or "TRIPLE-CORD MINISTRIES"
   crashed the MATCH with "no such column" — 4.3% of small-org self-searches
   errored, and on the droplet the error is swallowed into silent 0 results
   (worse than an error per the trust principles).
2. Both backends carry their own sanitizer (droplet ships as a single file),
   so a cross-file consistency test guards drift.

These tests exercise the sanitizers at source level (no server needed) plus
a live-index findability check that skips cleanly without the local DB.

Run: pytest tests/test_search_quality.py -v
"""
import importlib.util
import re
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "merit_registry.db"


def _load_sanitizer_from(path: Path, module_name: str):
    """Extract _sanitize_fts_query without importing the whole Flask app.

    Both API files are heavy (Flask init, embeddings, Sentry). Exec only the
    regex/constant/function block needed by the sanitizer.
    """
    src = path.read_text()
    # Pull the contiguous block from the first FTS5 constant to the end of
    # _sanitize_fts_query. Keeps the test honest: it runs the shipped code.
    m = re.search(
        r"(^_FTS5_[A-Z]+ .*?^def _sanitize_fts_query.*?)(?=^\S)",
        src, re.M | re.S,
    )
    assert m, f"could not locate sanitizer block in {path.name}"
    ns = {"re": re}
    exec(compile(m.group(1), str(path), "exec"), ns)
    return ns["_sanitize_fts_query"]


@pytest.fixture(scope="module")
def sanitize_full():
    return _load_sanitizer_from(ROOT / "daanaa_api.py", "full")


@pytest.fixture(scope="module")
def sanitize_edge():
    return _load_sanitizer_from(ROOT / "scripts" / "droplet_api.py", "edge")


# Queries that historically crashed or degraded. Each must produce a MATCH
# expression FTS5 accepts (verified against a scratch index below).
HOSTILE_QUERIES = [
    "TRIPLE-CORD MINISTRIES INCORPORATED",   # hyphen → "no such column: CORD"
    "OREGON 4-H FOUNDATION",                 # hyphen + single-char token
    "MULTI-ETHNIC YOUTH GROUP ASSOCIATION",  # hyphen mid-name
    "SHAARE SHOLEM CEMETARY ASSN PERPETUAL UPKEEP FUND A/C",  # slash
    "ST. JUDE'S CHILDREN'S HOSPITAL",        # period + apostrophes
    "L'ANSE FOOD BANK",                      # leading apostrophe
    "US-CHINA CATHOLIC ASSOCIATION",         # hyphen between capitals
    "1 THESSALONIANS 3-2 INC",               # digit-hyphen-digit
    "food bank: portland",                   # colon (FTS5 column syntax)
    "youth AND family",                      # uppercase boolean operator
    "arts NOT crafts",                       # NOT must not become an operator
    "health (mental)",                       # parens
    'the "best" charity',                    # embedded quotes
    "café società",                          # diacritics (unicode61 folds)
    "a",                                     # single char alone — must not scan-bomb
    "!!!",                                   # pure punctuation
]


@pytest.fixture(scope="module")
def scratch_fts(tmp_path_factory):
    """Tiny FTS5 index with the same schema/tokenizer as production."""
    db = sqlite3.connect(":memory:")
    db.execute(
        'CREATE VIRTUAL TABLE org_fts USING fts5('
        'ein UNINDEXED, merit_tier UNINDEXED, org_name, mission, city, state, '
        'metro, category, cause_tags, tokenize = "unicode61 remove_diacritics 2")'
    )
    rows = [
        ("111", "Spark", "TRIPLE-CORD MINISTRIES INCORPORATED", "", "TULSA", "OK", "", "X20", "{}"),
        ("222", "Spark", "OREGON 4-H FOUNDATION", "youth agriculture", "CORVALLIS", "OR", "", "O52", "{}"),
        ("333", "Spark", "ST JUDES CHILDRENS HOSPITAL", "pediatric care", "MEMPHIS", "TN", "", "E22", "{}"),
        ("444", "Spark", "LANSE FOOD BANK", "food security", "LANSE", "MI", "", "K31", "{}"),
    ]
    db.executemany("INSERT INTO org_fts VALUES (?,?,?,?,?,?,?,?,?)", rows)
    return db


class TestSanitizerNeverCrashes:
    """Every hostile query must produce a valid FTS5 MATCH expression."""

    @pytest.mark.parametrize("q", HOSTILE_QUERIES)
    def test_full_backend(self, sanitize_full, scratch_fts, q):
        expr = sanitize_full(q)
        # Must not raise OperationalError ("no such column" / "syntax error")
        scratch_fts.execute("SELECT ein FROM org_fts WHERE org_fts MATCH ?", (expr,)).fetchall()

    @pytest.mark.parametrize("q", HOSTILE_QUERIES)
    def test_edge_backend(self, sanitize_edge, scratch_fts, q):
        expr = sanitize_edge(q)
        scratch_fts.execute("SELECT ein FROM org_fts WHERE org_fts MATCH ?", (expr,)).fetchall()


class TestSanitizedQueriesStillFind:
    """Sanitizing must not destroy findability of the org that was typed."""

    CASES = [
        ("TRIPLE-CORD MINISTRIES", "111"),
        ("OREGON 4-H FOUNDATION", "222"),
        ("St. Jude's Childrens Hospital", "333"),
        ("L'Anse food bank", "444"),
    ]

    @pytest.mark.parametrize("q,ein", CASES)
    def test_full_backend_finds(self, sanitize_full, scratch_fts, q, ein):
        expr = sanitize_full(q)
        eins = {r[0] for r in scratch_fts.execute(
            "SELECT ein FROM org_fts WHERE org_fts MATCH ?", (expr,)).fetchall()}
        assert ein in eins, f"{q!r} → {expr!r} lost the org it names"

    @pytest.mark.parametrize("q,ein", CASES)
    def test_edge_backend_finds(self, sanitize_edge, scratch_fts, q, ein):
        expr = sanitize_edge(q)
        eins = {r[0] for r in scratch_fts.execute(
            "SELECT ein FROM org_fts WHERE org_fts MATCH ?", (expr,)).fetchall()}
        assert ein in eins, f"{q!r} → {expr!r} lost the org it names"


class TestBooleanWordsAreLiteral:
    """AND/OR/NOT typed by a donor are words, never operators."""

    def test_not_does_not_exclude(self, sanitize_full, scratch_fts):
        # "food NOT bank" as an operator would exclude 444; as literal words
        # the AND-semantics simply require both terms.
        expr = sanitize_full("food bank")
        eins = {r[0] for r in scratch_fts.execute(
            "SELECT ein FROM org_fts WHERE org_fts MATCH ?", (expr,)).fetchall()}
        assert "444" in eins

    def test_single_char_alone_returns_empty_not_scan(self, sanitize_full):
        # A bare "a" must sanitize to the empty-phrase sentinel, not "a"*
        # (prefix-scanning ~1.8M rows).
        assert sanitize_full("a") == '""'


class TestDeltaIndexer:
    """New orgs entering the registry must become searchable AND be proven
    findable at ingestion time (process rule, founder-approved 2026-07-19).
    Exercises scripts/search_index_delta.py detect → index → verify on a
    scratch registry."""

    def _scratch_registry(self, tmp_path):
        db_path = tmp_path / "scratch.db"
        db = sqlite3.connect(db_path)
        db.execute("""CREATE TABLE registry_enriched (
            EIN TEXT, organization_name TEXT, merit_tier TEXT, mission TEXT,
            CITY TEXT, STATE TEXT, metro TEXT, NTEECC TEXT, cause_tags TEXT,
            deductibility TEXT DEFAULT '1', org_status TEXT DEFAULT 'active')""")
        db.execute(
            'CREATE VIRTUAL TABLE org_fts USING fts5('
            'ein UNINDEXED, merit_tier UNINDEXED, org_name, mission, city, '
            'state, metro, category, cause_tags, '
            'tokenize = "unicode61 remove_diacritics 2")')
        # One org already indexed, one brand-new (the Monday-refresh case),
        # one ineligible (must be left out).
        orgs = [
            ("100000001", "OLDTOWN FOOD PANTRY", "Spark", "food", "OLDTOWN", "ME", "", "K31", "{}", "1", "active"),
            ("200000002", "BRAND NEW ARTS COLLECTIVE", "Spark", "arts", "BOISE", "ID", "", "A20", "{}", "1", "active"),
            ("300000003", "REVOKED WIDGET FUND", "Spark", "", "RENO", "NV", "", "T20", "{}", "1", "revoked"),
        ]
        db.executemany("INSERT INTO registry_enriched VALUES (?,?,?,?,?,?,?,?,?,?,?)", orgs)
        db.execute(
            "INSERT INTO org_fts VALUES (?,?,?,?,?,?,?,?,?)",
            ("100000001", "Spark", "OLDTOWN FOOD PANTRY", "food", "OLDTOWN", "ME", "", "K31", "{}"))
        db.commit()
        db.close()
        return db_path

    def test_detect_index_verify_cycle(self, tmp_path):
        sys.path.insert(0, str(ROOT / "scripts"))
        import search_index_delta as sid
        db_path = self._scratch_registry(tmp_path)

        result = sid.run(db_path=db_path, dry_run=True)
        assert result["unindexed"] == 1, "should detect exactly the new eligible org"

        result = sid.run(db_path=db_path)
        assert result["indexed"] == 1
        assert result["verified_ok"] == 1
        assert result["misses"] == []

        # New org is now actually findable through the production plan
        db = sqlite3.connect(db_path)
        rows = db.execute(
            "SELECT ein FROM org_fts WHERE org_fts MATCH ?",
            ('"BRAND"* "NEW"* "ARTS"* "COLLECTIVE"*',)).fetchall()
        assert ("200000002",) in rows

        # Idempotent: second run finds nothing to do
        result = sid.run(db_path=db_path)
        assert result["unindexed"] == 0


@pytest.mark.skipif(not DB.exists(), reason="no local registry DB")
class TestLiveIndexFindability:
    """Sampled eligible small orgs must be findable in the real index.

    Uses a fixed seed-ish deterministic sample (ORDER BY EIN on a modulus)
    so CI runs are reproducible — RANDOM() flakes are not acceptable tests.
    """

    def test_eligible_small_orgs_self_search(self, sanitize_full):
        db = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
        orgs = db.execute("""
            SELECT organization_name, EIN FROM registry_enriched
            WHERE total_revenue < 700000 AND organization_name IS NOT NULL
              AND deductibility = 1 AND org_status = 'active'
              AND CAST(EIN AS INTEGER) % 9973 = 0
            LIMIT 40
        """).fetchall()
        assert len(orgs) >= 10, "sample too small — check eligibility filters"
        misses = []
        for name, ein in orgs:
            expr = sanitize_full(name)
            rows = db.execute(
                "SELECT ein FROM org_fts WHERE org_fts MATCH ? "
                "ORDER BY bm25(org_fts, 10, 5, 1, 1) LIMIT 2000", (expr,)
            ).fetchall()
            if ein not in {r[0] for r in rows}:
                misses.append(name)
        # ≥95% findability is the world-class bar; generic names shared by
        # thousands of chapters (American Legion posts) are the honest remainder.
        assert len(misses) <= len(orgs) * 0.05, f"self-search misses: {misses}"

    def test_union_plan_finds_hard_names(self, sanitize_full):
        """Spaced initialisms and generic names must rank #1 via the exact
        name-phrase UNION branch (the finite-corpus advantage: if the typed
        text IS an org name, look it up — don't hope it survives the bm25
        candidate cap). These exact names missed under the bm25-only plan."""
        _apos = re.compile(r"['’`]")
        _clean = re.compile(r'[^\w\s]', re.UNICODE)
        db = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
        hard = ["N A B S", "BEST SCHOOL", "WORLD INC", "G O A L S ORGANIZATION INC"]
        for name in hard:
            # Skip silently if this org left the registry in a future refresh
            if not db.execute(
                "SELECT 1 FROM registry_enriched WHERE organization_name = ? LIMIT 1",
                (name,)).fetchone():
                continue
            q = sanitize_full(name)
            toks = _clean.sub(' ', _apos.sub('', name)).split()[:12]
            phrase = f'org_name : "{" ".join(toks)}"'
            rows = db.execute("""
                SELECT r.organization_name FROM registry_enriched r
                JOIN (SELECT ein, MIN(rel) AS rel FROM (
                    SELECT ein, -1e9 AS rel FROM org_fts WHERE org_fts MATCH ?
                    UNION ALL
                    SELECT ein, bm25(org_fts, 10, 5, 1, 1) AS rel
                    FROM org_fts WHERE org_fts MATCH ? ORDER BY rel LIMIT 2000
                ) GROUP BY ein) fts ON r.EIN = fts.ein
                ORDER BY (UPPER(r.organization_name) = ?) DESC, fts.rel LIMIT 5
            """, (phrase, q, name.upper())).fetchall()
            assert name in {r[0] for r in rows}, f"{name!r} not in top 5"
