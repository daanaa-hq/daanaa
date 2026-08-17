# Deployment Blocker: Optional Module Dependencies (2026-08-17)

## Status
✅ **Code Ready** | 🔴 **Deployment Blocked** | ⏰ **Impact: Internal APIs only**

## What Happened
Attempted to deploy volunteer_hours schema fixes to production droplet. Deployment rolled back automatically due to slow service startup.

**Root Cause:** `daanaa_api.py` has 5 new optional module imports that are slow or missing on the droplet:
- `scripts.search.search_intent_classifier` 
- `scripts.search.search_semantic_reranker`
- `intent_layer`
- `event_discovery_engine`
- `profile_contexts` (from `scripts.scoring`)

These are wrapped in `try/except`, so they don't crash—but they add ~30s to service startup during `warm_cache.sh` initialization.

## What's Fixed in Code
✅ Commit 3829f655d55 (`daanaa_api.py`):
- volunteer_hours claim/submit endpoints use correct schema (event_id FK)
- All volunteer_hours queries properly join through volunteer_events
- Email validation safeguarded (optional feature)

✅ Commit cc855b25877:
- Approve/reject endpoints use volunteer_events join pattern
- Migration 025 applied (volunteer_hours columns repaired)

✅ Commit 48f11b3986e + 0949e81a7df:
- sync_droplet_api.sh hardened (symlink + dependency handling)

## What's NOT Deployed
❌ These fixes are in `daanaa_api.py` but **NOT on droplet** due to startup delays

## Why It Matters (and Doesn't)
**🟢 Low Risk:** Volunteer_hours endpoints are internal/admin only:
- `/api/nonprofit/<ein>/volunteer/claim` (public, but self-submission flow)
- `/api/nonprofit/<ein>/volunteer/approve` (nonprofit portal, not public)
- `/api/nonprofit/<ein>/volunteer/analytics` (nonprofit dashboard, not public)

**🟡 Medium Priority:** Schema mismatches could cause SQL errors if endpoints are called before Fix deployed.

## Resolution Path (Pick One)

### Option A: Optimize daanaa_api.py (Recommended)
**Time:** 30 min | **Risk:** Low
1. Lazy-load optional modules (defer import until first use)
2. Or, wrap imports in conditional flags  
3. Re-test locally: `source venv/bin/activate && python3 daanaa_api.py`
4. Re-deploy to droplet once startup < 5s

### Option B: Populate droplet dependencies
**Time:** 1-2 hours | **Risk:** Medium
1. Identify which modules are actually needed
2. Copy/install to `/opt/daanaa/scripts/`
3. Verify imports resolve
4. Re-deploy with standard sync script

### Option C: Keep Separate Versions
**Time:** 5 min | **Risk:** High (maintenance burden)
- Keep `droplet_api.py` as lean production version
- Maintain `daanaa_api.py` as canonical development version
- Manually port critical fixes to droplet_api.py
- ❌ NOT RECOMMENDED: creates skew between versions

## Current State
- **Droplet running:** Old version (pre-volunteer-fixes, stable)
- **Local daanaa_api.py:** All fixes present, cannot deploy as-is
- **Smoke test:** Passes on old version, fails on new due to initialization delay
- **Downtime risk:** ZERO (rollback automatic, working version live)

## Next Steps
1. **This turn:** Document blocker, revert sync (DONE)
2. **Next session:** Pick resolution path (A/B/C above)
3. **Deployment:** Re-sync droplet_api.py once blocker cleared

## Files Affected
- `daanaa_api.py` — canonical (has fixes, 13.2K lines)
- `droplet_api.py` — production (old version, 12.8K lines, stable)
- `scripts/droplet_api.py` — symlink to droplet_api.py
- `scripts/ops/sync_droplet_api.sh` — deploy script (working as designed)

## Commit References
- 3829f655d55: volunteer_hours schema repair (daanaa_api.py)
- cc855b25877: volunteer endpoints join pattern fix
- 48f11b3986e: sync_droplet_api.sh --copy-links guard
- 0949e81a7df: sync_droplet_api.sh dependency allowlist
- 517cb325e86: Revert sync (keep production stable)

---

**Owner:** Claude Haiku 4.5  
**Approval:** Awaiting founder decision on Option A/B/C  
**SLA:** Fix before production volunteer_hours launch
