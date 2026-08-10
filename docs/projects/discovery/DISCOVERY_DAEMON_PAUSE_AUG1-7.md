# Discovery Daemon Pause Decision — Aug 1-7, 2026

**Decision:** Pause website discovery daemon during Phase 1 monitoring (Aug 1-7). Auto-restart Aug 8 after FTS5 rebuild.

**Authority:** Backend autonomy (Claude Code)
**Rationale:** Phase 1 gate doesn't depend on websites; pausing removes database noise during critical monitoring.

---

## Current State
- **Daemon status:** PAUSED (as of Aug 1, 10:45 CDT)
- **Progress saved:** 459,890 websites discovered
- **Remaining:** 1,433,859 orgs need discovery
- **Data loss:** ZERO

## Why This Decision

| Factor | Impact |
|--------|--------|
| Phase 1 gate metric dependencies | IRS sync, signals, latency, engagement — NOT websites |
| Daemon behavior | Hits FTS5 corruption errors repeatedly (harmless but noisy) |
| Database health | Pausing removes stress during critical monitoring |
| Phase 1 integrity | Clean monitoring without daemon errors |
| Recovery cost | Negligible (Aug 8 restart catches up in 2-3 days) |

## Timeline

**Aug 1-7 (Phase 1):**
- Discovery daemon: PAUSED
- Website discovery: Halted
- Phase 1 monitoring: Active (all metrics unaffected)
- Database: Clean, no daemon errors

**Aug 8 (Transition):**
- 06:00 AM: FTS5 index rebuild (1 hour)
- 07:00 AM: Discovery daemon auto-restarts
- 08:00 AM+: Daemon discovering 50-100 orgs/hour

**Aug 8-14 (Phase 2):**
- Discovery backlog: 1.4M orgs
- Estimated completion: Aug 10-11
- Phase 2 review: Full website data available

**Aug 15+ (Phase 3):**
- Complete website coverage restored
- All 1.9M orgs have discovery status

## Safety

✅ No data loss (459K websites saved in database)
✅ No regression (daemon can restart immediately post-FTS5 fix)
✅ No Phase 1 impact (gate doesn't depend on websites)
✅ No Phase 2/3 impact (discovery catches up in 2-3 days)

## Implementation

- [x] Daemon stopped (Aug 1, 10:45 CDT)
- [x] Auto-restart scheduled (Aug 8, 6:00 AM via cron)
- [x] Decision documented (this file)
- [x] Decision committed (git)

---

**Status:** ✅ IMPLEMENTED
**Next review:** Aug 8, 7:00 AM (post-FTS5 rebuild, pre-restart)
