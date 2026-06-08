# Search UX & Categorization Notes

## Known Issue: Education Subcategory Precision (2026-06-08)

### Current Behavior
- Search "Education + Primary Schools" returns 295 results
- This is a **text match across all Education orgs** (NTEE1='B', 190K total)
- Matches "primary" OR "school" anywhere in name/mission
- Results include educational services, tutoring, parent orgs, actual schools

### Data Quality
- **B20 (Elementary/secondary schools)**: 3,829 — actual K-12 schools
- **B94 (Educational services)**: 19,877 — tutoring, test prep, support
- **Blank NTEECC**: 25,701 — miscoded or too broad
- Many real schools lack precise NTEECC classification

### Options for Future Improvement
1. **Hard constraint**: "Primary Schools" filter only searches B20 NTEECC
2. **Soft constraint**: B20 first, broaden if low results
3. **Dual results**: Show "B20 schools (3.8K)" and "Mentions primary (295)" separately

### Decision
**Status: Deferred** — Keep current broad search behavior. Revisit when:
- Real user behavior data available
- NTEECC data quality improved
- User feedback indicates intent mismatch

---

## Related: Tier Consolidation (2026-06-07)

Deployed: Spark · Candle · Torch · Beacon (4-tier system)
- Old DB values normalize at frontend display time
- Backend scorer updates deferred to next re-score
- Zero-disruption deployment ✓
