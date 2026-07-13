# T12 Search Excellence — Measurement & Phased Improvement

**Authority:** EXECUTION_HANDOFF_2026_07_12.md (T12 strategy)  
**Goal:** Ship SQLite-native search improvements measured by real behavior  
**Phase:** Measurement first (weeks 1–2), then improvement (weeks 3–8)

---

## Phase 1: Measurement (Weeks 1–2)

**Objective:** Establish baseline for zero-result rate and user search patterns.

### What to measure

1. **Zero-result rate** (primary metric)
   - Queries that return 0 results
   - Track: unique queries, frequency, user feedback (if any)
   - Target: identify top 20 queries that fail

2. **Search engagement** (secondary)
   - Queries per user session
   - Result-click rate (do results drive action?)
   - Time spent on results page before navigating away

3. **Query patterns** (diagnostic)
   - Most common search terms
   - Geographic patterns (state, zip filtering)
   - NTEE category filters

### Implementation

**✅ DONE (2026-07-12):** Combined approach — Plausible events + backend detail logging.

Frontend (Option A): `frontend/src/pages/Directory.tsx` tracks search metrics via `trackSearchMetrics()` from `lib/analytics.ts`. Events include:
- `query_length` (characters in search term)
- `result_count` (number of results returned)
- `zero_results` ('yes' or 'no')
- `filters_applied` (count of active filters)
- `mode` ('keyword', 'fused', 'filtered')

Backend (hybrid of Options A+B): `/api/event` endpoint stores aggregates in `analytics_search_metrics` table (daily grouped stats) + individual zero-result queries in `analytics_zero_result_queries` table for pattern discovery. No raw query text in Plausible; individual queries logged server-side only (privacy: aggregates only, pattern discovery table is founder-readable).

**Query baseline & top failing queries:**
```bash
python3 scripts/analyze_search_metrics.py --days 7 --show-queries
```
Shows:
- Zero-result rate % (primary metric)
- Top 20 queries that returned zero results (for Phase 2 test set)
- Search patterns (avg query length, filter usage)

### Success criteria (1-week checkpoint)

- [ ] Measurement infrastructure live (Plausible events or logging)
- [ ] Baseline zero-result rate captured
- [ ] Top 20 failing queries identified
- [ ] Founder reviews findings, greenlights Phase 2

---

## Phase 2: Typo Tolerance (Weeks 3–4)

**Hypothesis:** SQLite trigram module reduces zero-results by 15–25% for misspellings.

**Decision rule:** Recall@5 > 0.90 on test set of 50 common typos (from Phase 1 data).

### Implementation

```sql
-- Add trigram index to org_fts
CREATE VIRTUAL TABLE org_fts_trigram USING fts5(
  organization_name, mission, cause_tags,
  content=registry_enriched,
  content_rowid=EIN
);

-- Spellfix1 layer for suggestions
CREATE VIRTUAL TABLE spellfix_orgs USING spellfix1(
  rank=10
);
INSERT INTO spellfix_orgs(word) SELECT organization_name FROM registry_enriched;
```

**Query logic:**
```python
def search_with_typo_tolerance(query):
    # Exact FTS5 match first
    results = fts_search(query)
    
    if len(results) == 0:
        # Suggest corrections
        corrections = db.execute(
            "SELECT word FROM spellfix_orgs WHERE word MATCH ? LIMIT 3",
            (query,)
        ).fetchall()
        return {
            "results": [],
            "zero_results_typo": True,
            "suggestions": [c[0] for c in corrections]
        }
    return {"results": results}
```

### Test set (from Phase 1 data)

Build a CSV of 50 top failing queries + their intended org names. Example:
```
Query,Expected Result,Category
"fod bank","Food Bank","NTEE-I"
"enviromental","Environmental Org","NTEE-C"
"womens shelter","Women's Shelter","NTEE-O"
```

Run the typo-tolerant search, measure recall. Ship if recall > 0.90.

---

## Phase 3: Baked Synonyms (Weeks 5–6)

**Hypothesis:** AI-generated synonyms for NTEE categories + common cause keywords improve discovery.

**Decision rule:** Recall@10 improves by >10% for category-ambiguous queries ("health", "services", "support").

### Implementation (nightly pipeline)

```python
# scripts/generate_search_synonyms.py
# For each NTEE category + top 100 cause tags, generate related terms via Qwen

SYNONYM_MAP = {
    "NTEE-I (Youth)": ["youth", "kids", "children", "young people", "teen", "adolescent"],
    "NTEE-K (Education)": ["school", "learning", "training", "tutoring", "education", "academic"],
    "cause:food": ["food", "hunger", "nutrition", "meals", "groceries", "pantry", "food-insecurity"],
    ...
}

# At bake time, expand FTS index:
# INSERT INTO org_fts(text) SELECT org_name || ' ' || STRING_AGG(synonyms, ' ')
#   FROM registry_enriched
#   LEFT JOIN synonym_map USING (ntee1, cause_tags)
```

### Measurement

Before/after on Phase 1 failing queries:
- Old: 8 results for "health services"
- New: 45 results for "health services" (more orgs discoverable)
- Verify recall on a 20-query holdout set

---

## Phase 4: Hybrid Semantic (Weeks 7–8)

**Hypothesis:** FTS (narrow to 100 candidates) + semantic rerank (top 10 by similarity) improves ranking quality.

**Decision rule:** Click-through rate on result #1–3 improves >15% vs. FTS-only ranking.

### Implementation

```python
def fts_then_semantic_search(query, limit=10):
    # Step 1: FTS narrows to 100
    candidates = fts_search(query, limit=100)
    
    # Step 2: Re-rank top 100 by semantic similarity (via home-server embedding API)
    ranked = semantic_rerank(query, [c['ein'] for c in candidates])
    
    return ranked[:limit]
```

**Measurement:** A/B test
- Bucket A: FTS-only results (current)
- Bucket B: FTS + semantic rerank (new)
- Metric: click-through rate on position 1–5 results

---

## Timeline & Go/No-Go Gates

| Week | Phase | Gate | Owner |
|------|-------|------|-------|
| 1–2 | Measurement | Zero-result baseline + top 20 queries | Founder reviews |
| 3–4 | Typo tolerance | Recall@5 > 0.90 on test set | Auto-pass if met |
| 5–6 | Synonyms | Recall@10 improves >10% | Auto-pass if met |
| 7–8 | Semantic | CTR improves >15% in A/B test | Auto-pass if met |

Each phase gates the next. If a phase fails its criterion, hold that phase (don't ship) and move to the next.

---

## Why this order

1. **Measurement first:** Can't improve what you don't measure. Zero-result rate is the clearest signal.
2. **Typo tolerance early:** Fixes the highest-frequency low-hanging fruit.
3. **Synonyms next:** Expands vocabulary without changing ranking logic.
4. **Semantic last:** Most complex, only needed if FTS + synonyms don't hit targets.

---

## Staffing

- **Measurement (Phase 1):** Frontend event logging (1 hour) + analysis (founder or data review)
- **Typo & synonyms (Phases 2–3):** Backend SQL + nightly pipeline (4–6 hours)
- **Semantic (Phase 4):** Endpoint wiring + A/B test (3–4 hours)

Total: ~12–14 hours engineering time over 8 weeks (1.5–2 hrs/week), self-paced.

---

## Success = Shipping

Shipping criterion: any phase that passes its gate AND doesn't break existing behavior ships immediately.
All phases are backward-compatible (FTS-only search still works as fallback).

No "perfect" search required; incremental improvement is the goal.
