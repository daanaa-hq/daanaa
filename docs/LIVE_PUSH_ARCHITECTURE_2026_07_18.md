# Live-Push Architecture for Org Profile Edits

**Date:** 2026-07-18  
**Trigger:** Board deferred item #15.3 (nonprofit dashboard live visibility)  
**Scope:** Design the sandboxed mechanism for real-time profile edits (24h delay → same-session visibility)  
**Safety bar:** Match `safe_deploy_droplet.sh` integrity guarantees (checksums, atomic swap, rollback)

---

## Problem Statement

**Today:** Org edits (mission, donate URL, website) are saved to `org_claims` in the local registry DB → included in next nightly precompute (~2-4h away, worst case ~24h). Org sees "Saved" but page doesn't change for hours, creating false impression Daanaa ignored the edit.

**Board decision:** Ship honest-timing disclosure now (done: "updates within 24 hours"). Defer REAL live-push to proper sandboxed follow-up because prior incident (2026-06-06 precompute corruption) proved unreviewed production writes bypass critical safety checks.

**Goal:** Same-session visibility (org edits profile → within minutes sees change on public page) without sacrificing the integrity safeguards that prevented worse 2026-06-06 outcomes.

---

## Design Principles

1. **Sandboxed writes:** Edits do NOT write directly to serving-layer static JSON. Instead, build an in-memory patch, validate, snapshot, swap atomically.
2. **Integrity-first:** Every change is verified before it touches the public page (checksum validation, data type checks, size bounds).
3. **Rollback-safe:** If anything fails, fall back to the last known-good precompute; no half-finished states on the serving layer.
4. **Audit trail:** Log every live edit with timestamp, org, fields changed, validation result, success/failure.
5. **Bounded scope:** Only mutable fields (mission, donate URL, website, cause tags). Scores, peer context, financial data stay immutable (precompute-only).

---

## Architecture

### Layer 1: Local Registry Write (Home Server)

**Existing behavior (no change):**
- Org POSTs edit to `PATCH /api/claim/profile` (daanaa_api.py)
- Validation + write to `org_claims` table (EIN-keyed, lock-free)
- Cache invalidation on the home API
- Org sees "Saved" message (now with honest-timing disclosure)

**New:** Also write to a live-patch queue (separate table, versioned):

```sql
CREATE TABLE IF NOT EXISTS live_profile_edits (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ein TEXT NOT NULL,
  field_name TEXT,  -- 'mission', 'donate_url', 'website', 'cause_tags'
  old_value TEXT,
  new_value TEXT,
  validated INTEGER DEFAULT 0,  -- 1 = passed integrity checks
  validation_error TEXT,
  pushed_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(ein) REFERENCES registry_enriched(EIN)
);
```

### Layer 2: Live-Patch Builder (Home Server, Hourly Cron)

**New daemon: `scripts/live_patch_builder.py`** (runs hourly via cron or on-demand)

**Steps:**
1. **Fetch pending edits** from `live_profile_edits WHERE validated=0` (newest first, per EIN)
2. **Validate each edit:**
   - Mission: length ≤300 chars, no prohibited tokens (shame words from P5 denylist), no URLs
   - Donate URL: valid HTTPS, reachable (HEAD request, cached 1h), matches claimed org domain or known processor (every.org, PayPal, etc.)
   - Website: valid HTTPS, distinct from donate URL, reachable (HEAD request, cached 1h)
   - Cause tags: JSON array, each tag in known taxonomy, ≤10 tags
3. **Mark validated=1** (or validation_error=reason if failed; still pushed but flagged)
4. **Load latest precompute snapshot** (e.g., `precompute/v1/content/orgs.json.gz`)
5. **Apply patches in-memory:**
   ```python
   org_detail = load_org_detail(ein)
   for edit in pending_edits:
       if edit.field == 'mission':
           org_detail['mission'] = edit.new_value
           org_detail['mission_source'] = 'claimed'
       # ... similar for donate_url, website, cause_tags
   ```
6. **Compute integrity hash:**
   ```
   h = sha256(json.dumps(org_detail, sort_keys=True).encode())
   ```
7. **Write patched org to staging dir:** `/data/precompute/v1/staging/{ein}.json`
8. **Write manifest:** `/data/precompute/v1/staging/MANIFEST.json`
   ```json
   {
     "version": "live-patch-2026-07-18T14:30:00Z",
     "base_snapshot": "precompute/v1/content/orgs.json.gz",
     "edited_orgs": [{"ein": "261234567", "fields": ["mission", "donate_url"], "hash": "abc..."}],
     "manifest_hash": "def...",
     "created_at": "2026-07-18T14:30:00Z",
     "expires_at": "2026-07-19T02:30:00Z"  // superseded by nightly deploy
   }
   ```

### Layer 3: Live-Patch Pusher (Droplet Edge, On-Demand or Hourly)

**New endpoint: `POST /api/admin/sync-live-patch` (droplet_api.py)**  
Requires: `X-Admin-Key` (same as other admin endpoints)

**Steps:**
1. **Fetch manifest** from home server via SSH or secure channel (e.g., S3 + signed URL)
2. **Verify manifest integrity:**
   ```
   manifest_hash = sha256(json.dumps(manifest_without_hash, sort_keys=True))
   assert manifest_hash == manifest['manifest_hash']
   ```
3. **Fetch org JSON files** from staging (one by one, with checksums):
   ```
   for org in manifest['edited_orgs']:
       org_json = fetch_org_patch(org['ein'])
       assert sha256(org_json) == org['hash']
   ```
4. **Load current content/orgs.json.gz** into memory (not modifying yet)
5. **Apply patches to in-memory copy:**
   ```
   for org in manifest['edited_orgs']:
       existing_org = load_org_from_precompute(org['ein'])
       if existing_org:
           patched = merge_org_fields(existing_org, org_json)
           write_patched_org_to_staging(patched)
   ```
6. **Recompute search index** for affected orgs (FTS5 re-index subset)
7. **Build new content tarball** (staging → `dist.new/content/`)
8. **Verify tarball integrity** (checksums for all contained files)
9. **Atomic swap:**
   ```bash
   mv dist.new/content dist/content.prev
   mv dist.new dist
   ```
10. **Rollback script ready:**
    ```bash
    if [ -f dist/content.prev ]; then
      mv dist/content dist/content.bad
      mv dist/content.prev dist/content
      systemctl restart daanaa  # reload from dist/content
    fi
    ```
11. **Log outcome** to `/var/log/daanaa/live-patch.log`
    ```
    2026-07-18 14:35:00 PUSH_START manifest_version=... edited_count=12
    2026-07-18 14:35:15 VALIDATE_OK all_orgs_checksummed
    2026-07-18 14:35:22 INDEX_REBUILD fts5_reindex_start
    2026-07-18 14:35:45 SWAP_OK dist.new→dist (prev backed up)
    2026-07-18 14:35:46 PUSH_COMPLETE elapsed=46s affected_orgs=12
    ```

### Layer 4: Org-Side Observability (SPA)

**Frontend: Claimed org dashboard shows live-patch status**

```tsx
// After edit:
- Immediately: "Saved. Your public page updates within 24 hours (usually sooner)."
- After ~5-10min (if live-patch succeeds): 
  "✓ Live! Your edits are now showing on your public page."
  (with a badge or checkmark on edited fields)
- If live-patch fails:
  "Your edits will appear on your public page at 2am PT (during our nightly update).
   [Why? Let us know if you'd like live updates.]"
```

**Backend: POST /api/claim/live-patch-status** (requires auth)
Returns: `{status: 'pending|live|failed', fields_live: ['mission', 'donate_url'], failed_reason: null}`

---

## Deployment & Rollback

### Normal path (success):
```
1. Org edits profile (home server)
   ↓
2. Edit saved to org_claims + live_profile_edits queue
   ↓
3. Hourly cron: live_patch_builder.py validates + prepares staging
   ↓
4. Droplet: sync-live-patch endpoint pulls + swaps (atomic)
   ↓
5. Org dashboard shows "✓ Live!" within 5-10 minutes
```

### Fallback path (live-patch fails):
```
1. sync-live-patch encounters validation error or swap failure
   ↓
2. Rollback triggered: restore dist/content.prev
   ↓
3. Log entry: failure reason + retry count
   ↓
4. Org still sees changes at 2am when nightly precompute runs
```

### Circuit breaker (abuse/attack):
```
- If >100 edits in 1 hour from single org → flag for review, pause live-push
- If >1000 edits in 24h across all orgs → disable live-push, return to nightly-only
- Maintain failure rate tracking; disable if >5% of live-pushes fail
```

---

## Data Integrity Safeguards

| Check | Location | Blocks If |
|-------|----------|-----------|
| **Mission length** | live_patch_builder.py | >300 chars |
| **Shame-word filter** | live_patch_builder.py | contains prohibited token (P5) |
| **Donate URL reachability** | live_patch_builder.py | HEAD request returns 4xx/5xx |
| **Donate URL domain** | live_patch_builder.py | doesn't match claimed org or known processor |
| **Website reachability** | live_patch_builder.py | HEAD request returns 4xx/5xx; Wayback fallback if site is temporarily down |
| **Cause tags valid** | live_patch_builder.py | tag not in known taxonomy or malformed JSON |
| **Manifest integrity** | sync-live-patch (droplet) | sha256 mismatch |
| **Org JSON integrity** | sync-live-patch (droplet) | sha256 mismatch |
| **Index rebuild** | sync-live-patch (droplet) | FTS5 reindex fails; prevents swap |
| **Atomic swap** | sync-live-patch (droplet) | ANY failure → rollback to .prev |

---

## Timeline

**Phase 1 (scope, this session):** ✓ Complete  
**Phase 2 (implementation, follow-up):**
- Week 1: Build live_patch_builder.py + live_profile_edits table schema
- Week 2: Test with 10 pilot orgs (internal + partners); audit logs
- Week 3: Gather metrics (latency, reliability, UX feedback)
- Week 4: Board gate 3 simulation on live-push; decide rollout or refinement

**Go-live criteria:**
- 99%+ success rate on edits (measured over 100+ edits)
- Latency <10 minutes from edit to live visibility
- Zero integrity failures (checksums, rollback events)
- Founder approval after pilot QA

---

## Principle Alignment

| Principle | Status |
|-----------|--------|
| P1 (mission) | ✓ Aligns: helps small orgs control their own narrative |
| P2 (privacy) | ✓ Aligns: no new data collection; edits stay org-owned |
| P3 (evidence-based, honestly stated) | ✓ Aligns: validation checks ensure accuracy; honest about latency window |
| P4 (small orgs fairness) | ✓ Aligns: live edits are most valuable for orgs with no other channels |
| P5 (no weaponization) | ✓ Aligns: shame-word filter + abuse circuit breaker prevent misuse |
| P6 (mistakes corrected) | ✓ Aligns: rollback mechanism undoes bad pushes; audit log tracks all |
| P7 (independence) | ✓ Aligns: no paid placement or algorithm influence; pure data edits |
| P9 (explainable) | ✓ Aligns: manifest + audit log make every push auditable |
| P10 (AI as tool) | ✓ Aligns: no AI involved; deterministic validation |

---

## Open Questions for Board

1. **Validation strictness:** Should we block live-pushes on reachability failures (conservative) or allow queueing with best-effort validation (pragmatic)?
2. **Latency SLA:** Target <10min? <5min? <30s? Trade-off: faster = higher-risk infrastructure.
3. **Pilot scope:** 10 pilot orgs or 100? How long to run before full rollout?
4. **Abuse policy:** Hard limit (100 edits/hour) or soft limit (flag for review)?

---

## Success Metrics

- **Org satisfaction:** Survey pilot orgs: "Did live edits improve your experience?" Target: 80%+ agree
- **Reliability:** 99%+ of live-pushes succeed without human intervention
- **Latency:** P50 <5min, P95 <10min, P99 <15min (edge case retries)
- **Safety:** Zero integrity incidents; zero unintended data loss; audit log 100% complete
- **Adoption:** % of claimed orgs who make edits post-live-push launch (trend indicator for engagement)

---

**Next step:** Board approval of architecture + pilot scope.  
**Prerequisite:** Commit this design; update DECISIONS.md with architecture choice.  
**Defer:** Implementation details (exact DB schema, endpoint specifics) to dev phase per board gate.
