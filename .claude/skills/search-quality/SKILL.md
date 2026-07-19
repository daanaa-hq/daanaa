---
name: search-quality
description: Audit and enforce the world-class search bar — sanitizer safety, self-search findability, relevance ordering, latency, and zero-result gap mining. Use when asked about search quality, "can donors find X", search regressions, or after any change to FTS indexing, sanitizers, or ranking.
---

# Search Quality Audit

Daanaa's search bar of record (established 2026-07-18, task #18):

| Metric | Bar | Measured |
|---|---|---|
| Self-search: typed org name in top 5 | ≥ 95% | **99.993% — EXHAUSTIVE, all 1,758,892 eligible orgs** (2026-07-19) |
| Hostile-query SQL errors (hyphens, slashes, quotes) | 0 | 0 |
| Search latency (union plan, local) | p95 < 500ms | p50 49ms / p95 212ms |
| Small-org share in broad queries | ≥ 20% | passing |

The 131 exhaustive misses (0.007%) are all orgs whose full registered name is
a single generic word shared by thousands ("LIFE", "FIRST", "WOMEN", "OHIO",
truncated chapter names) — more than 5 orgs share the exact name, so no
ranking can put all of them in the top 5 simultaneously. Location narrows
these; not a defect. CSV: logs/search_exhaustive_misses_20260719_004729.csv.

## The invariants (never regress these)

1. **Sanitizer parity** — `_sanitize_fts_query` is duplicated in `daanaa_api.py`
   and `scripts/droplet_api.py` (single-file droplet deploy). Any edit to one
   MUST be mirrored in the other. `tests/test_search_quality.py` exercises both.
2. **Punctuation never crashes** — FTS5 treats `- : / ( ) "` as syntax. All
   donor text goes through the sanitizer before MATCH. Apostrophes FUSE
   ("L'Anse" → "LAnse", matching IRS's "LANSE"); everything else → space.
3. **Relevance order only for text queries** — browse (no `q`) stays neutral
   A-Z (2026-07-04 decision). With `q`, exact typed-name match pins first,
   then bm25. Never rank by size or merit unless explicitly requested via
   `sort=` (P7).
4. **Eligibility filter** — org_fts intentionally indexes only
   `deductibility = 1 AND org_status = 'active'` orgs (~1.76M of 2.06M).
   A "missing from index" finding must check this filter before being
   declared a gap. Validators must sample eligible orgs only.
5. **Embedding rows via `_emb_index`** — never `int(ein)` as a matrix index
   (EINs are tax IDs; leading-zero EINs would read another org's vector).

## New-org process rule (founder-approved 2026-07-19)

Every org entering the registry is made searchable AND proven findable at
ingestion time via `scripts/search_index_delta.py` (detect unindexed →
incremental FTS INSERT → self-search each through the production plan).
Wired into `refresh_irs_data.sh` (weekly IRS load, Step 5) and
`overnight_pipeline.py` (Step 7.5 nightly safety net). Misses are logged to
`logs/search_index_delta.log` — a nonzero miss count there is an incident,
not noise. Full-corpus proof: `scripts/search_exhaustive_validator.py`.

## Audit procedure

```bash
source ~/meritgiving/venv/bin/activate

# 1. Golden set (sanitizer safety + findability, both backends, ~2s)
python3 -m pytest tests/test_search_quality.py -q

# 2. Statistical self-search + latency (300 eligible small orgs, ~1 min)
python3 scripts/search_ranking_validator.py

# 3. Live behavioral probes (the hyphen query is the canary — it crashed
#    the old code; 0 results here means the sanitizer regressed)
curl -s "https://daanaa.org/api/search?q=4-H+foundation" | python3 -c \
  "import json,sys; d=json.load(sys.stdin); assert d.get('total',0) > 0, 'SANITIZER REGRESSION'; print('live 4-H probe OK:', d['total'])"

# 4. Zero-result gap mining (what donors typed that found nothing)
sqlite3 -readonly ~/meritgiving/data/merit_registry.db \
  "SELECT query, occurrence_count, last_seen_at FROM analytics_zero_result_queries
   ORDER BY occurrence_count DESC LIMIT 20;"
```

## When a metric fails

- SQL errors > 0 → sanitizer drift between the two files; diff the
  `_sanitize_fts_query` blocks first.
- Self-search < 95% → check FTS index freshness
  (`SELECT COUNT(*) FROM org_fts` vs eligible count) — the nightly
  `overnight_pipeline.py` rebuilds it; a stale index means the pipeline broke.
- Latency p95 > 500ms → look for single-char prefix tokens leaking through
  (the sanitizer drops lone single chars) or a missing `LIMIT 2000` cap.
- Zero-result patterns clustering → candidates for `_FTS5_NOISE` additions,
  synonym expansion, or missing data — log findings in DECISIONS.md.

## Deploy reminders

- `daanaa_api.py` change → `./restart_api.sh` + local behavioral probes.
- `scripts/droplet_api.py` change → `bash scripts/ops/sync_droplet_api.sh`.
  If the smoke probe reports failure with "ssh connection refused", the site
  may still be healthy — verify behaviorally via https://daanaa.org before
  declaring an incident (2026-07-18: probes failed on SSH rate-limit while
  the deploy had actually succeeded).
