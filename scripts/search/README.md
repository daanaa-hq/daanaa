# Search — FTS Index Pipeline

## Canonical Files

- **`build_fts_index.py`** — Builds FTS5 full-text search index from `registry_enriched`. Runs nightly.
- **`search_index_delta.py`** — Incremental index updates for newly discovered orgs (faster than full rebuild).
- **`analyze_search_metrics.py`** — Query performance analysis + tuning (helps identify slow searches).

## How To...

**Rebuild the search index from scratch:**
```bash
python3 scripts/search/build_fts_index.py
```

**Add new searchable fields:**
1. Add column to schema (or update existing column in `registry_enriched`)
2. Update `_FTS5_FIELDS` in `build_fts_index.py`
3. Rebuild index via `build_fts_index.py`
4. Test via `tests/test_search_quality.py`

**Tune search quality:**
```bash
python3 scripts/search/analyze_search_metrics.py
python3 tests/search_quality_tests.py  # Verify no regression
```

## Testing

```bash
# Run 52 baseline search quality tests
python3 scripts/testing/search_quality_tests.py

# Test a specific query
python3 -c "
import sqlite3
conn = sqlite3.connect('data/search.db')
results = conn.execute(\"SELECT COUNT(*) FROM org_fts WHERE org_fts MATCH 'food'\").fetchone()
print(f'Found {results[0]} orgs for \"food\"')
"
```

## Database Contract

- **Input:** `data/merit_registry.db` table `registry_enriched` (columns: org_name, mission, cause_tags, etc.)
- **Output:** `data/search.db` virtual table `org_fts` (FTS5 full-text search index)
- **Nightly:** `overnight_pipeline.py` calls `build_fts_index.py` → updates `search.db` → syncs to droplet

## Do Not Use

- `search_index_v2.py` (superseded 2026-06-15)
- `legacy_fts_builder.py` (archived 2026-07-02)
- Other `*_search_*.py` files in root (debris from experimentation)

## Recent Changes

- 2026-08-12: Location parsing + cause synonym expansion added to droplet_api.py (improves search relevance)
- 2026-07-24: Fixed FTS sync drift (298K orgs missing from index)
- 2026-07-18: Search quality audit baseline (52 tests, all passing)

## Troubleshooting

**Search is slow (>1s)?**
→ Rebuild index: `python3 scripts/search/build_fts_index.py`

**Org not appearing in results?**
→ Check if it's in `registry_enriched`: `SELECT * FROM registry_enriched WHERE EIN = '<ein>'`
→ Check if it's in FTS index: `SELECT COUNT(*) FROM org_fts WHERE rowid = <fts_rowid>`

**Query returns 0 results unexpectedly?**
→ Run `scripts/search/analyze_search_metrics.py` to see if it's a known issue
→ Check DECISIONS.md for recent schema changes

## See Also

- `docs/GATE3_SEARCH_QUALITY_AUDIT.md` — Search-quality audit record
- `docs/FOLDER_STRUCTURE_PLAN.md` — Why this structure exists
