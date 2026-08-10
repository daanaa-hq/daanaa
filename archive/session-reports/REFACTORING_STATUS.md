# Blueprint Refactoring Status — 2026-07-05

## What We Have Ready

✅ **Complete Planning & Documentation:**
- `ROUTING_FIX_PLAN.md` — Full architecture (2300+ words)
- `BLUEPRINT_MIGRATION_STEPS.md` — Step-by-step walkthrough (300+ lines)
- `tests/test_routing.py` — 10+ routing safety tests (ready to use)
- `scripts/refactor_blueprints.py` — Helper script for dry-run/apply

✅ **Progress So Far:**
- Backend blueprint directory created
- Frontend blueprint created and verified
- API routes extracted (6934 lines)
- Route replacement logic validated (111 @api_bp.route conversions)
- New droplet_api.py skeleton created (129 lines vs 8282)

## The Challenge

The refactoring is **not complicated in concept** (separate API from SPA), but **tedious in execution** because:

1. **8K+ lines of interdependent code** — helper functions, global state, imports
2. **Circular dependencies** — e.g., limiter needs to be injected after app init
3. **Manual route migration** — 100+ decorators need proper handling

**Estimated effort to complete:** 2-3 hours of careful, methodical work (verify each step)

## Two Paths Forward

### Path A: Automated Refactoring (Recommended)
1. **Use the provided migration script** (`scripts/refactor_blueprints.py --apply`)
2. Manually review the generated files
3. Run routing tests (`pytest tests/test_routing.py -v`)
4. Deploy to staging droplet
5. Verify via curl

**Pros:** Scripted, repeatable, less error-prone  
**Cons:** Requires careful manual code review  
**Time:** 3-4 hours

### Path B: Manual Refactoring (Thorough)
1. Follow `BLUEPRINT_MIGRATION_STEPS.md` step-by-step
2. Extract and refactor code manually
3. Test at each step
4. Deploy incrementally

**Pros:** Full understanding of every change  
**Cons:** Time-consuming, high risk of missing dependencies  
**Time:** 4-5 hours

### Path C: Defer & Use Quick Fix (Fast)
1. Skip the refactoring for now
2. Just move the SPA fallback route to the END of droplet_api.py
3. Ensures recall endpoints work immediately
4. Plan full refactoring for next sprint

**Pros:** 30-minute fix, unblocks the system  
**Cons:** Doesn't solve the architectural problem long-term  
**Time:** 30 minutes

## Current State

- **Routing issue:** Not blocking users (API responses work, SPA serves)
- **Recall endpoints:** Exist but routing incorrect
- **Service:** Stable on droplet
- **Data:** Fully synced (macro + KG tables)

## Recommendation

**Do Path C (quick fix) now** — unblock the recall endpoints  
**Then do Path A (full refactoring) next sprint** — proper architectural fix

Quick fix:
```bash
# Move SPA fallback to the very end of the file
grep -n "@app.route('/', defaults=" droplet_api.py
# Note that line number
# Cut lines around it and move to the end of file
```

## What to Do Now

**Choose:**
1. **"Let's do Path A automation"** — I'll continue the refactoring
2. **"Let's do Path C quick fix"** — I'll move SPA fallback to end, deploy in 30 min
3. **"Let's defer this, I'll do it next sprint"** — Skip for now, proceed with data expansion

## Cost of Each Path

| Path | Time | Complexity | Risk | Benefit |
|------|------|-----------|------|---------|
| A (Full) | 3-4h | High | Medium | Perfect architecture, prevents future bugs |
| B (Manual) | 4-5h | Very High | High | Full understanding |
| C (Quick) | 30m | Low | Low | Immediate fix, temporary |

