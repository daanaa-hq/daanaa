# T-2026-08-12-001 — IRS Eligibility Schema Restoration (Long-Term Foundation)

| Field | Value |
|---|---|
| Owner | Claude Code (implementation) |
| Scope | Restore IRS eligibility columns + rebuild precompute with full tax-deductibility verification |
| Affected paths | `daanaa_api.py` (schema restoration), `scripts/precompute_generator.py` (rebuild), `scripts/overnight_pipeline.py` (scheduler), `data/merit_registry.db` |
| Authority constraints | Founder approved for long-term approach (Option A); no public claims publication until rebuild complete |
| Status | READY TO EXECUTE |
| Owner decision | Founder chose Option A (restore full verification) on Aug 11 — "we have flexibility, need to build for the long term" |
| Timeline | Aug 12 start, 4-6h execution, completion target Aug 12 evening |
| Validation | Precompute rebuild completes without errors, tax-deductibility badge displays correctly, smoke tests pass |
| Handoff target | Codex verification that schema is correct, precompute is valid, no data corruption |
| Branch | master (autonomous work, no feature branch needed) |

---

## Founder Decision: Why Option A (Long-Term)

**Founder guidance:** "We have flexibility, need to build for the long term."

**What this means:**
- Daanaa's value proposition depends on trust (Charter Principle #3)
- Current state (displaying "verified" with zero evidence) is unsustainable
- Building proper evidence foundation now prevents future rework
- Long-term vision: Tax-deductibility verification is a core trust signal, not an afterthought

**Stewardship alignment:**
- P#3 (evidence-based): Restore full verification columns enables evidence capture
- P#6 (mistakes corrected quickly): This was an error; fixing it properly is the right choice
- P#9 (decisions explainable): Can document "we chose Option A because long-term trust matters"

---

## What's Broken (Current State)

**Status:** IRS eligibility columns were dropped ~Aug 1. Precompute has been unrunnable since.

| Column | Status | Impact |
|--------|--------|--------|
| `irs_eligibility_verified` | MISSING | Can't distinguish verified vs unverified |
| `irs_eligibility_revoked` | MISSING | Can't identify revoked status |
| `irs_eligibility_exception` | MISSING | Can't flag edge cases |
| `irs_last_check_date` | MISSING | Can't show freshness of verification |

**Public impact:** Site displays "verified tax-deductible" badge (via org detail page) with ZERO underlying evidence.

**Data impact:** Precompute generator fails silently when trying to access deleted columns.

---

## Work Plan: Option A (Restore + Rebuild)

### Phase 1: Schema Restoration (30-45 min)

**Objective:** Restore IRS eligibility columns to `registry_enriched` table

**Steps:**
1. Create migration: `scripts/migrations/005_restore_irs_eligibility_columns.sql`
   - Restore `irs_eligibility_verified` (boolean, default NULL)
   - Restore `irs_eligibility_revoked` (boolean, default NULL)
   - Restore `irs_eligibility_exception` (text, optional)
   - Restore `irs_last_check_date` (timestamp, optional)
   - Add index on `irs_eligibility_verified, irs_last_check_date`

2. Run migration idempotently: `python3 scripts/migrations/run_migration.py 005`
   - Check: Columns exist and are nullable
   - Check: 2,056,834 rows still intact
   - Check: No data corruption

3. Verify schema: `SELECT * FROM registry_enriched LIMIT 1`
   - Confirm columns present
   - Confirm no errors

**Timeline:** 30-45 min

**Risk:** Low (adding columns is safe; data is backed up)

---

### Phase 2: Backfill IRS Verification (2-3 hours)

**Objective:** Populate IRS eligibility columns from authoritative source

**Option A-1: IRS Tax Exempt Organization Search API** (Recommended)
- Source: IRS official search (most authoritative)
- Coverage: All 501(c)(3) organizations in search
- Freshness: Updated daily
- Rate: ~100 lookups/sec (conservative)
- Estimated time: 20,000-25,000 orgs/hour × 2.056M orgs = ~80-100 hours (TOO SLOW)

**Option A-2: ProPublica 990 Dataset** (Faster fallback)
- Source: ProPublica aggregates IRS data + revocation list
- Coverage: ~1.9M organizations
- Freshness: Weekly
- Process: Parse `irs_has_revoked_status`, `irs_tax_exempt_org_search_status`
- Timeline: 1-2 hours (bulk processing)

**Option A-3: Hybrid** (Recommended)
- Start: ProPublica for bulk (~1.9M in 1-2h)
- Then: IRS API for gaps (~100K remaining, 1h)
- Total: 2-3 hours

**Claude's recommendation:** **Option A-3 (Hybrid)** — balances speed + accuracy

**Steps:**
1. Extract from ProPublica 990 dataset: `irs_has_revoked_status`, tax-exempt status
2. Backfill `registry_enriched` with verification results
3. Query IRS API for remaining ~100K orgs (missing from ProPublica)
4. Final count: All 2.056M orgs with IRS status verified

**Timeline:** 2-3 hours

**Risk:** Medium (data accuracy depends on ProPublica + IRS API)

---

### Phase 3: Precompute Rebuild (1-2 hours)

**Objective:** Regenerate 1.76M precomputed JSON pages with correct IRS data

**Steps:**
1. Run: `python3 scripts/precompute_generator.py --rebuild --with-irs-verification`
   - Generates 1.76M JSON files
   - Includes `irs_eligibility_verified`, `irs_last_check_date` in each org record
   - Parallel execution: 8 workers (proven safe)

2. Verify output:
   - Check: 1.76M files generated
   - Sample: 100 random orgs have IRS data populated
   - Check: File sizes reasonable (no truncation)

3. Backup: Rotate `.prev` backup (old precompute archived)

**Timeline:** 1-2 hours (parallel generation)

**Risk:** Low (precompute is static, safe to rebuild)

---

### Phase 4: Validation & Smoke Tests (30 min)

**Objective:** Verify everything works end-to-end

**Tests:**
1. Database integrity:
   ```sql
   SELECT COUNT(*) FROM registry_enriched WHERE irs_eligibility_verified IS NOT NULL;
   -- Expected: ~1.9M–2.0M rows
   ```

2. API response (org detail):
   ```bash
   curl http://localhost:5000/api/organizations?q=education&per_page=5
   # Verify: irs_eligibility_verified, irs_last_check_date present in response
   ```

3. Precompute sample:
   ```bash
   cat precompute_output/org_591123456.json | jq '.irs_eligibility_verified'
   # Expected: true | false | null
   ```

4. Frontend rendering:
   - Load org detail page for verified org → badge shows ✅
   - Load org detail page for unverified org → badge shows ⚠️
   - Load org detail page for revoked org → badge shows ✗

5. Smoke test (public URL):
   - `daanaa.org/org/591123456` loads without 500
   - Badge displays correctly
   - Response time < 300ms

**Timeline:** 30 min

**Risk:** Low (all data already backfilled)

---

## Timeline: Aug 12 Execution

| Phase | Duration | Start | Complete | Blocker |
|-------|----------|-------|----------|---------|
| 1: Schema restore | 45 min | 08:00 | 08:45 | None |
| 2: IRS backfill | 2-3h | 09:00 | 11:30 | Network (IRS API) |
| 3: Precompute rebuild | 1-2h | 11:30 | 13:30 | Disk I/O (parallel) |
| 4: Smoke tests | 30 min | 13:30 | 14:00 | None |
| **Total** | **4-6h** | **08:00** | **14:00** | **None** |

**If executed starting 08:00 CDT Aug 12:**
- Ready by 14:00 (2 PM CDT)
- Phase 2 launch readiness unblocked same day
- Precompute live on droplet by evening (async deploy)

---

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|------------|-----------|
| IRS API rate-limiting | Medium | Use hybrid approach (ProPublica bulk + API gap-fill); queue if needed |
| ProPublica data stale | Low | Acceptable (IRS updated weekly anyway; freshness documented) |
| Precompute disk space | Low | 16G available on local machine; rotation removes old files |
| Network outage during backfill | Low | Implement retry logic (3 attempts per batch, 30s backoff) |
| Schema migration fails | Low | Migration idempotent; can re-run; no data loss |

---

## Stewardship Alignment

**Principle #3 (evidence-based trust signals):**
- Current: Display "verified" with zero evidence ✗ VIOLATES
- After: Display "verified" with IRS API evidence ✅ COMPLIES

**Principle #6 (mistakes corrected quickly):**
- Acknowledged error: Columns dropped without replacement
- Action: Restore + backfill immediately ✅ COMPLIES

**Principle #9 (decisions explainable):**
- Choice documented: "Long-term foundation requires proper verification"
- Logic transparent: IRS data → badge mapping clear
- Future-proofed: Can audit verification decisions ✅ COMPLIES

---

## Deliverables

**Code commits:**
- `scripts/migrations/005_restore_irs_eligibility_columns.sql`
- `scripts/backfill_irs_verification.py` (ProPublica + IRS API hybrid)
- `scripts/precompute_generator.py` (updated to use restored columns)

**Data:**
- `data/merit_registry.db` with restored + backfilled IRS columns
- `precompute_output/` with 1.76M regenerated JSON files

**Documentation:**
- Task record (this file) with exact evidence
- Commit messages with reasoning
- `docs/DECISIONS.md` entry: "IRS Schema Option A chosen for long-term trust foundation"

---

## Handoff Checklist (For Codex)

- [ ] Schema migration applied successfully
- [ ] IRS backfill completed (row count verified)
- [ ] Precompute rebuild completed (file count verified)
- [ ] Smoke tests pass (API + frontend + database)
- [ ] No data corruption (integrity check clean)
- [ ] Precompute deployed to droplet (if applicable)
- [ ] Codex approval for merge

---

## Next Steps (After This Task)

1. Phase 2 Launch Readiness: Now unblocked (IRS schema fixed)
2. Methodology publication: Can publish with confidence (full verification in place)
3. Parallel performance optimization: Start Aug 12-16
4. Needs Network deployment: Aug 13 (after Phase 2 decision)

---

**Prepared by:** Claude Code  
**Founder decision:** Option A (Aug 11, "build for the long term")  
**Ready to execute:** Aug 12, 08:00 CDT  
**Target completion:** Aug 12, 14:00 CDT  
**Timeline:** 4-6 hours
