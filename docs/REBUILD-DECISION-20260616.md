# Database Rebuild Decision — 2026-06-16

## Context

Two competing database states:

**Option A: New Validated Rebuild**
- 1,977,759 orgs (from BMF + 990-N extracts)
- 1,395,651 with NTEE1 (70.6% coverage)
- Zero corruption (validated, filtered bad data)
- Lost 517K NTEE classifications

**Option B: Restored Backup (Chosen)**
- 2,064,613 orgs (from BMF only, no 990-N)
- 1,912,693 with NTEE1 (92.6% coverage)
- 107 negative expenses + 1,277 empty STATE (minor issues, fixed)
- 537,920 orgs already scored (v4)
- 650,722 with financial data

## Decision: Restore Backup (Option B)

**Why:** NTEE classification coverage is foundational. It drives:
1. **Peer grouping** — score computation requires org category
2. **Cause filtering** — directory features depend on NTEE1
3. **Recommendations** — similar organizations depend on category
4. **Search/discovery** — users filter by cause, location, org type

Losing 517K classifications to add 350K new (but unclassified) orgs is a net loss for the product.

## Actions Taken

1. **Restored backup** → `/data/merit_registry.db`
   - Old DB: 2.06M orgs, 92.6% NTEE
   - Kept new rebuild as reference: `merit_registry_20260616_validation_rebuild.db`

2. **Cleaned data issues**
   - 107 negative expenses → set to NULL
   - 1,277 empty STATE → set to NULL
   - All required fields now complete

3. **Validated restored DB**
   - ✓ API healthy
   - ✓ No corruption
   - ✓ NTEE coverage at 92.6%
   - ✓ 537,920 orgs with merit scores

## Lessons for Future Rebuilds

- **Data breadth ≠ data quality.** Adding 350K unclassified orgs broke critical features.
- **Validate the impact of schema changes.** The new rebuild introduced 990-N data with 70.7% NTEE gap.
- **NTEE classification is a hard constraint.** Any rebuild must maintain or improve coverage.
- **Backup before major changes.** Backups saved us here.

## Next Steps

1. Use this restored database as the stable foundation
2. Compute v5 context (archetype, health signals, peer groups)
3. Build FAISS for similar-org recommendations
4. Test claim system on solid data
5. When ready for future expansion (adding 990-N), backfill missing NTEE via AI inference or ProPublica mapping

---

**Status:** Active  
**Database:** `/home/akbar/meritgiving/data/merit_registry.db` (restored, validated, 2.06M orgs, 92.6% NTEE)
