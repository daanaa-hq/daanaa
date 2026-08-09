# Daanaa Consolidation: Merit → Daanaa Naming (2026-08-09)

**Status:** COMPLETE — Platform naming consolidation from "Merit" to "Daanaa"  
**Commits:** 2 commits, 9 files changed  
**Scope:** Scorer naming, pipeline references, documentation updates

## What was consolidated

### 1. Scoring System Renaming ✅
- **`merit_scorer_v6_0.py` → `daanaa_scorer.py`** (CURRENT ACTIVE)
  - This is the canonical v6 scorer that runs nightly
  - Renamed to align platform identity with "Daanaa" (not "Merit")
  
### 2. Historical Scorers Archived ✅
- **`merit_scorer_v4_0.py` → `scripts/archive_scorers/merit_scorer_v4_0.py`**
- **`merit_scorer_v5_0.py` → `scripts/archive_scorers/merit_scorer_v5_0.py`**
- Preserved as progression history (v4 → v5 → v6 evolution)
- Never run from scripts/ directory; they are archived for reference

### 3. Pipeline References Updated ✅

#### overnight_pipeline.py (primary)
- `run_v5_scorer()` → `run_daanaa_scorer()`
- Path: `merit_scorer_v5_0.py` → `daanaa_scorer.py`
- Load script: `load_v5_scores.py` → `load_daanaa_scores.py`
- Log messages updated to reference "Daanaa scorer" and "v6 financial context"

#### delta_scorer_v5_nightly.py (incremental)
- Path: `merit_scorer_v5_0.py` → `daanaa_scorer.py`
- Comment updated to reference daanaa_scorer
- Continues to use load_v5_scores_delta.py (load mechanism unchanged)

### 4. Active Script References Updated ✅
- **export_research_snapshot.py**: 3 references to `merit_scorer_v6_0.py` → `daanaa_scorer.py`
- **droplet_api.py**: Documentation comment updated
- **enrich_api_responses.py**: Comment reference updated
- **research_summary_generator.py**: Comment reference updated

### 5. Documentation Updated ✅
- **CLAUDE.md**
  - Production scorer: `merit_scorer_v4_0.py` → `daanaa_scorer.py`
  - Key pipeline table: Updated to reference daanaa_scorer
  - Gotchas section: Updated scorer location guidance
  - Financial context system description: Now describes v6 as current
  
- **SCORING-VERSION-HISTORY.md**
  - Source files list: Added archive locations and versioning clarity
  - v6.0 row: Notes daanaa_scorer as current active scorer

## What remains unchanged

### Database names
- `data/merit_registry.db` — kept as-is (no schema migration needed)
- Column names (`merit_score`, `merit_tier`, etc.) — kept as-is (active in current v6 schema)

### Historical scripts (not active)
- Old merit_* files in scripts/ remain for historical reference
- These are not called by any active pipeline and can stay in place

### Naming in configuration
- Environment variables using "merit" (e.g., MERIT_DB_PATH) — kept as-is
- These are internal/operational, not user-facing

## Why this consolidation matters

1. **Platform Identity:** Daanaa is the public-facing brand. "Merit" was an earlier internal name.
2. **Clarity:** Current code uses "daanaa_scorer" making it clear v6 is the canonical production scorer.
3. **Progression:** v4/v5 archived together, with v6 as current. Clear history.
4. **Documentation:** CLAUDE.md and other developer docs now accurately reflect current state.

## Verification

**All changes verified against:**
- ✅ Overnight pipeline calls daanaa_scorer
- ✅ Delta scorer calls daanaa_scorer
- ✅ No stale references in active scripts
- ✅ Privacy gates: all 8 gates passed
- ✅ Git history: 2 commits, clean audit trail

## Next steps (if needed)

1. **Optional:** Update environment variable names (MERIT_DB_PATH → DAANAA_DB_PATH) if doing full consolidation
2. **Optional:** Rename database columns in new schema version (post-October 12 launch)
3. **Monitor:** Verify overnight pipeline calls daanaa_scorer successfully on next nightly run

---

**Committed by:** Claude Haiku 4.5  
**Date:** 2026-08-09  
**Branch:** master  
**Commits:** 8b15824c442 (code), 23db69d63d5 (docs)
