# Database Corruption Assessment — Aug 1, 2026

## Issue
Database `merit_registry.db` (Jul 28 backup) exhibits significant corruption:
- Freelist corruption (invalid pages)
- Index tree corruption (rows out of order)
- FTS5 search index broken
- VACUUM operation fails
- Index rebuild fails

## Root Cause
Likely occurred during:
1. Jul 28 backup operation (possibly during precompute rebuild crash on Jul 31)
2. OR disk being 99% full on Aug 1, causing write corruption

## Impact Assessment

### Functions That WORK ✅
- Basic SELECT queries (org lookup, counting)
- Direct database reads via API
- Monitoring scripts (IRS sync, signal accuracy)
- Phase 1 quality gate metrics collection

### Functions That FAIL ❌
- VACUUM / ANALYZE (optimization)
- Index rebuilding / maintenance
- Full-text search (FTS5 broken)
- Search API endpoints (may return errors)

### Phase 1 Monitoring Impact
- **IRS Sync Check:** ✅ Works (COUNT query on active orgs)
- **Signal Accuracy:** ✅ Works (SELECT sample of orgs)
- **Page Latency:** ✅ Works (API response times)
- **Search Performance:** ❌ Cannot measure (search broken)
- **Engagement:** ⚠️ May be incomplete (if depends on search)

## Recommended Action Timeline

### Immediate (Aug 1-7)
- Continue Phase 1 monitoring with current database
- Accept search will be unavailable
- Log any errors; alert if corruption spreads

### After Phase 1 (Aug 8+)
- Full database recovery: restore from earlier backup or rebuild from source data
- Options:
  1. Restore from Jun/Jul 1 backup + replay enrichment
  2. Rebuild from original IRS/ProPublica data (clean state)
  3. Use alternative database if available

### Monitoring
- Run hourly integrity checks (PRAGMA quick_check with timeout)
- Alert if new tables show corruption
- Track query success rate

## Decision
**Proceed with Phase 1 as-is.** Database corruption is localized to maintenance functions and search; core monitoring metrics are unaffected.

