"""MERIT data ingest pipeline.

Ingest stages:
  1. BMF (IRS Business Master File) — bmf.py
  2. ProPublica enrichment         — propublica.py (Phase 0, Week 5+)
  3. DuckDB local store            — duckdb_store.py
  4. Neon delta sync               — neon_sync.py

All stages run on home server. Only deltas push to Neon.
See SKILL.md: .claude/skills/irs-bmf-ingest/SKILL.md
"""

from .bmf import parse_bmf_csv

__all__ = ["parse_bmf_csv"]
