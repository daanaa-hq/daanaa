#!/usr/bin/env python3
"""Corpus-vocabulary typo correction for search — the zero-result rescue path.

Finite-corpus principle (docs/SEARCH_ENGINE_LESSONS.md lesson 3): the spelling
dictionary is our OWN index vocabulary via fts5vocab — corrections can only
ever point at words that actually appear in org records, never at generic
dictionary words. Algolia's rules applied:
  - correction is a fallback, never pollutes exact results (callers invoke
    this ONLY when the primary query returned nothing)
  - corrected results are labeled honestly (callers surface corrected_query)
  - typed tokens win unless an edit-1 neighbor is >=10x more common in the
    corpus ("CHILDERN" appears in 22 real org records; "CHILDREN" in ~190K —
    correct it; a legitimately rare word stays)

Speed contract: only runs on the zero-result path (happy path untouched);
every call carries a hard time budget (default 150ms) and vocab lookups are
point queries (~0.02ms measured). KEEP IN SYNC with the duplicated copy in
scripts/droplet_api.py (single-file deploy).
"""
import re
import sqlite3
import time

_ALPHA = 'abcdefghijklmnopqrstuvwxyz'
_APOS = re.compile(r"['’`]")
_CLEAN = re.compile(r'[^\w\s]', re.UNICODE)
_BUDGET_S = 0.15
_PREFER_FACTOR = 10   # corrected variant must be >=10x more common than typed

_vocab_ready: set = set()   # id(conn) values where temp vocab exists


def _ensure_vocab(conn: sqlite3.Connection) -> bool:
    """Create the temp fts5vocab view once per connection. Needs a connection
    WITHOUT PRAGMA query_only (temp vtable creation counts as a write)."""
    key = id(conn)
    if key in _vocab_ready:
        return True
    try:
        # 'col' type so counts can be scoped to the org_name column: with
        # row-level counts, mission prose polluted scoring ("across" appears
        # in ~200K mission blurbs and out-voted "cross" in org names —
        # "RED CROSS" got "corrected" to "RED ACROSS").
        conn.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS temp.org_vocab "
            "USING fts5vocab('main', 'org_fts', 'col')")
        _vocab_ready.add(key)
        return True
    except sqlite3.OperationalError:
        return False


def _doc_count(conn, term: str) -> int:
    row = conn.execute(
        "SELECT doc FROM temp.org_vocab WHERE term = ? AND col = 'org_name'",
        (term,)).fetchone()
    return row[0] if row else 0


def _edit1(tok: str):
    """Edit-distance-1 variants: deletes, transposes, replaces, inserts."""
    for i in range(len(tok)):
        yield tok[:i] + tok[i + 1:]
        if i < len(tok) - 1:
            yield tok[:i] + tok[i + 1] + tok[i] + tok[i + 2:]
        for c in _ALPHA:
            if c != tok[i]:
                yield tok[:i] + c + tok[i + 1:]
    for i in range(len(tok) + 1):
        for c in _ALPHA:
            yield tok[:i] + c + tok[i:]


def _best_variant(conn, tok: str, deadline: float):
    """Highest-doc-count edit-1 variant of tok, or (None, 0)."""
    best, best_doc = None, 0
    seen = {tok}
    for v in _edit1(tok):
        if time.time() > deadline:
            break
        if len(v) < 2 or v in seen:
            continue
        seen.add(v)
        d = _doc_count(conn, v)
        if d > best_doc:
            best, best_doc = v, d
    return best, best_doc


def correct_query(conn: sqlite3.Connection, text: str,
                  budget_s: float = _BUDGET_S) -> str | None:
    """Return a corrected query string, or None if nothing better was found.

    Call ONLY after the primary search returned zero results. `conn` must see
    org_fts in its main schema and must not be in query_only mode.
    """
    if not _ensure_vocab(conn):
        return None
    deadline = time.time() + budget_s
    toks = _CLEAN.sub(' ', _APOS.sub('', text)).split()[:6]
    if not toks:
        return None
    out, changed = [], False
    for tok in toks:
        low = tok.lower()
        if len(low) < 3:                      # too short to correct safely
            out.append(tok)
            continue
        own = _doc_count(conn, low)
        if time.time() > deadline:
            out.append(tok)
            continue
        best, best_doc = _best_variant(conn, low, deadline)
        if best and best_doc >= max(_PREFER_FACTOR * own, _PREFER_FACTOR):
            out.append(best.upper() if tok.isupper() else best)
            changed = True
        else:
            out.append(tok)
    return ' '.join(out) if changed else None
