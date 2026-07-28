# Phase 3 Deployment: Pause Memo

**To:** Founder  
**From:** Claude Code (AI Engineering Agent)  
**Date:** 2026-07-28 16:15 CDT  
**Re:** Phase 3 IRS Eligibility deployment paused — I/O concerns + root cause analysis  

---

## Status

**Deployment Status:** ROLLED BACK ✓  
**Live Platform:** Healthy, no data loss  
**Phase 3 Ready:** NO — blocked on investigation

---

## What Happened

We attempted to deploy Phase 3 IRS Eligibility to production today (2026-07-28). The deployment failed after 2+ hours with **zero files actually extracted on droplet**, despite logs showing "Extracting archive..."

**Timeline:**
- 12:26:50 CDT: Deployment started
- 13:30 CDT: You checked in; I reported still extracting (seemed normal)
- 15:04 CDT: Investigation revealed extraction never actually happened
  - Archive on droplet: 1.76M files (88% complete)
  - Local precompute: 1.98M files (100% complete)
  - Droplet extraction: 0 files extracted (process never ran)
- 15:30 CDT: Full rollback to last known good

**No impact to live platform.** API healthy, all routes working normally.

---

## Root Causes Identified

### Issue 1: Archive Payload Incomplete (88%)

The archive file (4.3GB) created in `.deploy_scratch/precompute_payload.tar.gz` only contained 1.76M of the expected 1.98M files.

**Why:** Initial tar command appears to have timed out or silently failed. Either:
- Tar was interrupted before completing
- Symlink (`.deploy_scratch/precompute/orgs` → `precompute_output/orgs`) wasn't dereferenced by tar
- Tar failed on a file and silently skipped remainder

**Impact:** Droplet extraction "succeeded" but only had 88% of data.

---

### Issue 2: Tar Process Never Started on Droplet

Despite logs showing "Extracting archive..." for 2h+, no tar process was actually running on droplet at 15:04 CDT.

**Why:** Deployment script got stuck waiting for extraction to complete, but extraction never spawned. Possible causes:
- Extraction command failed silently
- Script waiting on a process that exited immediately
- Hung in a subprocess call

**Impact:** Wasted 2+ hours of monitoring before discovering zero progress.

---

### Issue 3: I/O Contention Prevents Reliable Archive Rebuild

When we attempted to rebuild the archive locally, tar hung when reading precompute directory.

**Why:** Precompute has 1.98M small files (~8KB each gzipped) across 1000 prefix directories. This causes high metadata I/O:
- Each file requires a separate `stat()` call
- Compression adds CPU overhead
- Local system appears to have I/O bottleneck

**Evidence:**
```bash
# Simple tar read (no compression) timed out:
timeout 30 tar -cf - -C precompute_output orgs/ | wc -c
→ Terminated (30 second timeout)

# Compressed archive creation hung:
tar -czf precompute_payload.tar.gz ... 
→ Stuck at 836MB / 4.3GB (20%)
```

**Critical Concern:** Archive creation causes search/loading performance degradation (exactly what you warned about: _"i hope you are doing it in a way that does kill our search and loading speed"_).

---

## Why We Paused (Option B)

Continuing to retry the current deployment strategy would:

1. **Force multiple tar operations** on an already-stressed I/O system
2. **Impact live platform search/loading speed** during business hours
3. **Waste time** on a fundamentally unreliable approach (1.98M files in single tar)

**Better approach:** Investigate root causes, fix architecture, retry with confidence.

---

## Investigation Needed

### Questions to Answer

1. **Why did initial tar only capture 1.76M files?**
   - Was it interrupted/timed out?
   - Was symlink not dereferenced?
   - Did tar fail silently on an error?
   - Run: `tar -tzf .deploy_scratch/precompute_payload.tar.gz | grep "\.json\.gz$" | wc -l` to confirm

2. **Why does tar hang when reading precompute_output/orgs?**
   - System I/O bottleneck? (Need: `fio` benchmark)
   - Kernel buffering issue? (Need: `vmstat`, `iostat -x`)
   - Symlink resolution problem? (Need: `ls -l precompute_output/orgs`)
   - Tar command option issue? (Test: `--dereference` vs `--hard-dereference`)

3. **Is 1.98M files in single archive fundamentally unsustainable?**
   - Yes, probably. Recommend: chunked approach (000–999 prefixes = 1000 small archives, 4–16MB each)

### Recommended Actions (Before Next Attempt)

**Week 1:**
- [ ] Run I/O benchmark: `fio` on precompute_output/orgs to establish baseline
- [ ] Verify precompute directory: Check for symlinks, special files, permissions issues
- [ ] Test tar options locally: `--dereference`, `--hard-dereference`, rsync
- [ ] Check system load during archive creation: Use `top`, `iostat`, `vmstat` in parallel

**Week 2:**
- [ ] Design chunked archive strategy (1000 small archives by EIN prefix)
- [ ] Implement chunked archive creation + verification script
- [ ] Update deployment playbook with new strategy + monitoring
- [ ] Add archive validation to preflight checklist

**Week 3:**
- [ ] Retry Phase 3 with chunked strategy during night window
- [ ] Monitor system load throughout
- [ ] Verify each chunk's integrity before proceeding

---

## Documentation Created

All findings documented for future reference:

- **`docs/PHASE3_DEPLOYMENT_INCIDENT_2026_07_28.md`** — Comprehensive incident report with timelines, root cause analysis, and medium-term recommendations
- **`LESSONS.md` (updated)** — Two new entries capturing checksum issue + archive completeness issue with preventing rules
- **This memo** — Executive summary and next steps

---

## Confidence Levels

| Action | Confidence | Why |
|---|---|---|
| Live platform healthy | 100% | Rollback complete, API verified responding |
| Archive was incomplete | 95% | Verified file count (1.76M vs 1.98M) |
| Extraction never ran | 95% | Zero processes, zero files at 15:04 |
| I/O is bottleneck | 80% | Tar hangs, but need `fio` to confirm |
| Next attempt will succeed | 40% | Without addressing archive strategy + I/O |
| Next attempt will succeed (with fixes) | 85% | If we implement chunked strategy + monitoring |

---

## Timeline to Next Attempt

**Conservative estimate (address all concerns):**
- Investigation: 3–5 days
- Design review: 2–3 days
- Implementation: 3–5 days
- Testing (dry-run): 2–3 days
- **Next production attempt: Mid-August (14–21 days)**

**Aggressive estimate (minimal investigation, chunked strategy only):**
- Implementation: 2–3 days
- Testing: 1–2 days
- **Next production attempt: Early August (4–7 days)**

---

## Questions for You

Before we proceed, clarification needed on:

1. **Timing:** When do you want Phase 3 live? (Informs investigation depth vs. speed tradeoff)
2. **Performance:** Is it acceptable to run archive operations during 10pm–6am night window only?
3. **Strategy:** Approved to move to chunked archive approach (1000 small files instead of 1 large)?
4. **Testing:** Can we do full dry-run on staging before production attempt?

---

## Appendix: Full Documentation

- **Incident Report:** `docs/PHASE3_DEPLOYMENT_INCIDENT_2026_07_28.md` (comprehensive, includes checklist for next retry)
- **Original Playbook:** `docs/PHASE3_DEPLOYMENT_PLAYBOOK.md` (still valid, but archive strategy needs redesign)
- **Lessons:** `LESSONS.md` (two new entries with preventing rules)
- **Process Doc:** `docs/PHASE3_PROCESS_DOCUMENTATION.md` (still valid, update after fixes)

---

**Bottom line:** Phase 3 is paused, rollback is complete, investigation checklist is ready. We have clear paths to fix this. Recommend investigating I/O baseline this week and making architecture decision (chunked vs. single archive) before next attempt.

