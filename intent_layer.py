"""Privacy-preserving shared intent signals for Daanaa.

This module stores aggregateable workflow signals only. It deliberately has no
person, email, wallet, IP, or donor identity fields. A user's private wallet
remains separate from nonprofit-facing aggregate demand signals.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

INTENT_KINDS = {"give", "volunteer", "learn", "partner", "claim"}
INTENT_STAGES = {"expressed", "matched", "action_started", "verified", "completed", "withdrawn"}


def ensure_schema(db: sqlite3.Connection) -> None:
    db.execute("""
        CREATE TABLE IF NOT EXISTS intent_signals (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            kind         TEXT NOT NULL,
            ein          TEXT,
            event_id     INTEGER,
            source       TEXT NOT NULL,
            stage        TEXT NOT NULL DEFAULT 'expressed',
            evidence     TEXT NOT NULL DEFAULT '{}',
            created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.execute("CREATE INDEX IF NOT EXISTS idx_intent_ein ON intent_signals(ein, kind, stage)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_intent_event ON intent_signals(event_id, kind, stage)")
    db.commit()


def _clean_ein(ein: str | None) -> str | None:
    if not ein:
        return None
    value = "".join(c for c in str(ein) if c.isdigit())[:10]
    return value or None


def record_intent(
    db: sqlite3.Connection,
    *,
    kind: str,
    source: str,
    ein: str | None = None,
    event_id: int | None = None,
    evidence: dict | None = None,
) -> int:
    """Record an anonymous signal and return its internal id."""
    if kind not in INTENT_KINDS:
        raise ValueError("invalid intent kind")
    if not source or len(source) > 120:
        raise ValueError("source is required")
    if event_id is None and not _clean_ein(ein):
        raise ValueError("ein or event_id is required")
    if evidence is not None and not isinstance(evidence, dict):
        raise ValueError("evidence must be an object")

    ensure_schema(db)
    cur = db.execute(
        "INSERT INTO intent_signals (kind, ein, event_id, source, evidence) VALUES (?, ?, ?, ?, ?)",
        (kind, _clean_ein(ein), event_id, source.strip(), json.dumps(evidence or {}, sort_keys=True)),
    )
    db.commit()
    return int(cur.lastrowid)


def transition_intent(db: sqlite3.Connection, intent_id: int, stage: str) -> None:
    """Advance an internal workflow signal without adding identity data."""
    if stage not in INTENT_STAGES:
        raise ValueError("invalid intent stage")
    ensure_schema(db)
    db.execute(
        "UPDATE intent_signals SET stage=?, updated_at=? WHERE id=?",
        (stage, datetime.now(timezone.utc).isoformat(), intent_id),
    )
    db.commit()


def summarize_intent(db: sqlite3.Connection, *, ein: str | None = None, event_id: int | None = None) -> dict:
    """Return counts only; no individual signal details are exposed."""
    ensure_schema(db)
    where, params = [], []
    if ein:
        where.append("ein=?")
        params.append(_clean_ein(ein))
    if event_id is not None:
        where.append("event_id=?")
        params.append(event_id)
    clause = (" WHERE " + " AND ".join(where)) if where else ""
    rows = db.execute(
        "SELECT kind, stage, COUNT(*) AS count FROM intent_signals" + clause + " GROUP BY kind, stage",
        params,
    ).fetchall()
    return {row["kind"] + ":" + row["stage"]: row["count"] for row in rows}
