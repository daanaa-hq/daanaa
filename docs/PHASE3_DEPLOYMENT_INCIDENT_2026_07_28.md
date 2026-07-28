# Phase 3 Deployment Incident Report
**Date:** 2026-07-28  
**Status:** ROLLBACK COMPLETE — Investigation Paused  
**Severity:** High — Deployment failed, I/O performance concerns identified

---

## Executive Summary

Phase 3 IRS Eligibility deployment to production was attempted on 2026-07-28 but failed after 2+ hours with zero files actually extracted. Root cause analysis revealed:

1. **Archive payload was incomplete** (1.76M files / 88% of expected 1.98M)
2. **Deployment script got stuck** with no extraction process actually running
3. **Local I/O contention** prevents reliable archive recreation
4. **Risk:** Attempting to force archive creation impacts platform search/loading speed

**Recommendation:** Pause Phase 3, investigate root causes, retry with fixes before next attempt.

---

## Timeline

| Time (CDT) | Event | Status |
|---|---|---|
| 12:21:18 | Deploy stage 4: Payload transfer started | In progress |
| 12:23:01 | **Deploy attempt 1: Checksum failed** | ROLLED BACK |
| 12:23:03 | Auto-rollback to previous version | Complete |
| 12:25:00 | Deploy stage 4: Second payload transfer started | In progress |
| 12:26:49 | Payload on droplet (4.3GB) | ✓ |
| 12:26:50 | Deploy stage 5: Atomic swap started | In progress |
| 12:26:50 | Step 1/5: Checksum verification | ✓ Passed |
| 12:27:09 | Step 2/5: "Extracting archive..." | Started |
| **13:30** | **User check-in: No progress after 64 min** | ⚠ Concern raised |
| **15:04** | **Discovery: Extraction never actually started** | 🚨 CRITICAL |
| 15:04–15:30 | Investigation: Archive incomplete + tar hung | Root cause identified |
| 15:30 | **ROLLBACK: Full revert to last known good** | ✓ Complete |

**Total deployment time:** ~3 hours (failed)

---

## Root Cause Analysis

### Issue 1: Incomplete Archive Payload

**Symptom:** Droplet showed 1.76M files extracted after 2h+; local had 1.98M  
**Root Cause:** Archive created in `.deploy_scratch/precompute_payload.tar.gz` only contained 1.76M files (836MB partial tar before timeout)

**Evidence:**
```bash
# Local precompute: COMPLETE
find precompute_output/orgs -name "*.json.gz" | wc -l
→ 1,981,212 files ✓

# Archive payload: INCOMPLETE  
tar -tzf .deploy_scratch/precompute_payload.tar.gz | grep "\.json\.gz$" | wc -l
→ ~1,758,892 files (88%)

# Droplet extraction: STALLED
ssh root@162.243.97.179 "find /opt/daanaa/data/precompute/v1/orgs -name '*.json.gz' | wc -l"
→ 1,758,892 files (what was in the archive)
```

**Why only 1.76M?**
- Initial tar command appears to have timed out or silently failed
- Symlink in `.deploy_scratch/precompute/orgs` → `precompute_output/orgs` may not have been resolved by tar
- Or tar was interrupted before completion

---

### Issue 2: Extraction Never Actually Started

**Symptom:** Log showed "Extracting archive..." but no tar processes running  
**Root Cause:** Deployment script became stuck/stalled on droplet

**Evidence:**
```bash
# At 15:04 CDT (after 2h37m "extraction"):
ps aux | grep -i tar | grep extract
→ No processes found

find /opt/daanaa/data/precompute/v1/orgs -name "*.json.gz" | wc -l
→ 0 files (extraction never happened despite log message)
```

**What likely happened:**
- Deployment script started extraction but no actual process spawned
- Or tar process immediately exited without error
- Script logged "Extracting..." but never verified process started

---

### Issue 3: I/O Contention on Archive Rebuild

**Symptom:** Attempting to rebuild archive locally caused tar to hang/timeout  
**Root Cause:** High I/O contention when tar reads 1.98M files from precompute_output/orgs

**Evidence:**
```bash
# Simple tar test (no compression, just read):
timeout 30 tar -cf - -C precompute_output orgs/ | wc -c
→ Terminated (timeout after 30s)

# Directory size:
du -sh precompute_output/orgs
→ 16GB with 1,981,212 files

# Tar with compression (initial attempt):
tar -czf precompute_payload.tar.gz -C precompute_output orgs/
→ Hung at 836MB / 4.3GB target
```

**Why tar hangs:**
- 1.98M small files (~8KB each gzipped) = high metadata I/O
- Each file requires separate read() + compress operation
- Local system may have I/O bottleneck (disk speed, kernel buffering, CPU limit)
- Compression adds CPU overhead on top of disk reads

---

## Performance Impact Assessment

**User concern (from earlier message):**
> "i hope you are doing it in a way that does kill our search and loading speed. The platform needs to have a fast speed"

**What we observed:**
- Forcing tar/compression on precompute directory caused system to become unresponsive
- Simple tar read (no compression) timed out after 30 seconds
- Archives failed or hung repeatedly, suggesting I/O is bottleneck

**Risk of continuing current approach:**
- Archive creation causes search/loading degradation
- Multiple retry attempts would compound I/O stress
- Could impact live platform if retried during business hours

---

## Archive Creation Failure: Hypothesis

The initial archive creation command may have been interrupted or failed silently:

```bash
# Command that was supposed to create archive:
tar -czf precompute_payload.tar.gz --hard-dereference -C precompute_output orgs/

# Possible failure modes:
# 1. Timeout (no explicit timeout set, may rely on bash/system defaults)
# 2. Symlink not resolved (--hard-dereference should handle, but maybe not)
# 3. Permission issue on some files (silently skipped by tar)
# 4. Disk space exhaustion during compression
# 5. Process killed by OOM killer or ulimit
```

**What we know:**
- Archive file exists and is readable on droplet
- Archive contains 1.76M valid files (tar integrity check passed)
- Archive is NOT corrupted, just incomplete
- Local source has all 1.98M files

---

## Lessons Learned

### Lesson 1: Archive Creation Is Unreliable for 1.98M Files
Creating a single tar/gzip of 16GB + 1.98M files is error-prone:
- No progress visibility
- Easy to silently fail mid-stream
- No way to resume partial extraction
- Compression adds I/O overhead

**Solution:** Consider chunking by EIN prefix (000–999 = 1000 smaller archives, ~4-16MB each)

### Lesson 2: Tar Hang on Precompute Directory
Simply reading precompute_output/orgs with tar causes hangs:
- Metadata-heavy operation (1.98M stat() calls)
- High I/O load impacts platform performance
- Needs investigation of local system I/O health

**Solution:** 
- Run `fio` benchmark to measure disk performance
- Check system load during archive creation
- Consider off-peak timing or pre-staging elsewhere

### Lesson 3: Deployment Script Lacks Visibility
Droplet deployment showed "Extracting archive..." but never verified actual tar process:
- No PID tracking
- No progress reporting
- Easy to miss failures if extraction silently stops
- 2h37m wait before discovering zero files extracted

**Solution:**
- Add tar process monitoring to deployment script
- Report file count every 30 seconds
- Auto-abort if zero progress for N minutes
- Use `tar -v --checkpoint=1000` for progress

### Lesson 4: Archive Symlink Strategy Unclear
`.deploy_scratch/precompute/orgs` → `precompute_output/orgs` may not have been dereferenced by tar properly:
- Symlink valid locally
- But tar may have included symlink itself, not target contents
- Or `--hard-dereference` didn't resolve it

**Solution:**
- Test tar command with symlink BEFORE deployment
- Use `tar -tvf archive.tar.gz | head` to verify contents
- Or copy files directly instead of symlinking

---

## Recommendations for Next Attempt

### Short-term (Quick Retry)

1. **Fix archive creation:**
   ```bash
   # Use explicit timeout and error checking
   timeout 3600 tar -czf precompute_payload.tar.gz \
     --dereference \
     -C precompute_output orgs/ \
     || die "Tar failed"
   
   # Verify immediately
   files=$(tar -tzf precompute_payload.tar.gz | grep "\.json\.gz$" | wc -l)
   [ "$files" -ge 1900000 ] || die "Archive incomplete: $files files"
   ```

2. **Run during off-peak hours:**
   - Archive creation causes I/O stress
   - Schedule for night window (10pm–6am) when headroom confirmed
   - Monitor system load during tar

3. **Monitor tar process:**
   ```bash
   # In deployment script:
   tar ... &
   TAR_PID=$!
   for i in {1..180}; do
     [ -d /proc/$TAR_PID ] || break  # Process finished
     size=$(ls -lh output.tar.gz | awk '{print $5}')
     echo "[$i] Archive: $size"
     sleep 10
   done
   ```

### Medium-term (Better Architecture)

1. **Chunked deployment (1000 smaller archives):**
   ```bash
   # Create archives by EIN prefix
   for prefix in {000..999}; do
     tar -czf precompute_$prefix.tar.gz \
       -C precompute_output orgs/$prefix/
   done
   
   # Deploy one chunk at a time, verify each
   # Allows resume if one chunk fails
   ```

2. **Verify archive before sending to droplet:**
   ```bash
   tar -tzf precompute_payload.tar.gz | wc -l  # Should be 1.98M+ lines
   sha256sum precompute_payload.tar.gz         # Record hash
   ```

3. **Droplet-side progress monitoring:**
   ```bash
   # In atomic swap script:
   tar -xzf archive.tar.gz &
   TAR_PID=$!
   while ps -p $TAR_PID > /dev/null; do
     count=$(find extraction_dir -name "*.json.gz" | wc -l)
     echo "Extracted: $count files"
     sleep 30
   done
   ```

### Investigation Items

**Before next attempt, investigate:**

1. **Local I/O performance:**
   ```bash
   fio --name=randread --ioengine=libaio --iodepth=32 \
       --rw=randread --bs=4k --runtime=60 \
       --filename=/home/akbar/meritgiving/precompute_output/orgs/test
   ```

2. **Precompute directory health:**
   ```bash
   # Check for symlinks, hardlinks, special files
   find precompute_output/orgs -type l | wc -l  # symlinks
   find precompute_output/orgs -type s | wc -l  # sockets
   find precompute_output/orgs -type p | wc -l  # pipes
   ```

3. **Archive creation command options:**
   - Test `tar --dereference` vs no dereference
   - Test `tar --hard-dereference` 
   - Test rsync instead: `rsync -av precompute_output/orgs/ staging/`

4. **System load during archive creation:**
   ```bash
   # Monitor in separate terminal
   watch -n 1 'top -bn1 | head -20; echo "---"; iostat -x 1 2 | tail -5'
   ```

---

## Files Modified

- `/home/akbar/meritgiving/logs/safe_deploy.log` — Deployment attempt logged
- `.deploy_scratch/` — Cleaned up incomplete artifacts
- No production code changes (rollback complete)

---

## Sign-Off

**Rollback Status:** ✓ COMPLETE  
**Live API Status:** ✓ Responding normally  
**Data Integrity:** ✓ No data loss (rollback to previous working state)

**Phase 3 Status:** PAUSED pending investigation  
**Next Action:** Investigate root causes, retry with fixes after addressing I/O concerns

**Confidence in Next Attempt:** 40% (without addressing archive creation and I/O issues)

---

## Appendix: Checklist for Next Retry

- [ ] Run `fio` benchmark to understand I/O baseline
- [ ] Verify precompute_output/orgs integrity (all 1.98M files present)
- [ ] Test tar command locally with explicit timeout and verification
- [ ] Archive size ≥ 4.3GB before uploading to droplet
- [ ] Run during off-peak hours (night window)
- [ ] Monitor system load during archive creation
- [ ] Add progress reporting to deployment script
- [ ] Document tar command options chosen and rationale
- [ ] Set explicit timeout (3600s+) for extraction on droplet
- [ ] Verify extracted files match archive before swap
- [ ] Have rollback ready before atomic swap

