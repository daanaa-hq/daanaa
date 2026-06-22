# Search Database (search.db) Deployment & Safeguards

## Overview

The droplet's `search.db` is the authoritative FTS5 (full-text search) index for all 1.8M organizations. It powers the `/api/fused-search` and `/api/search` endpoints on daanaa.org.

**Critical:** If search.db is missing, empty (0 bytes), or corrupted, all search functionality fails silently and users see empty results. This document describes the safeguards and deployment procedures to prevent this.

---

## Safeguards (as of 2026-06-22)

### 1. Startup Validation

The droplet API (`droplet_api.py`) now includes a mandatory `_validate_search_db()` function that runs at startup and checks:

- ✅ `search.db` file exists at `/data/precompute/v1/search.db`
- ✅ File is not 0 bytes (catches empty placeholder files)
- ✅ `org_fts` FTS5 virtual table exists in the database
- ✅ `registry_enriched` table exists (for org detail lookups)
- ✅ `org_fts` table contains data (COUNT(*) > 0)

**If any check fails, the API exits with status code 1 and prints a detailed error message** (rather than starting and serving 0 search results).

Example error output:
```
FATAL: search.db is empty (0 bytes) at /data/precompute/v1/search.db. 
This is a deployment error. Sync from home server: 
rsync ~/meritgiving/data/merit_registry.db root@droplet:/data/precompute/v1/search.db
```

### 2. Table Name Mapping

The API code now consistently uses the correct table names:
- FTS search queries: `org_fts` (not `org_search`)
- Org detail/browse queries: `registry_enriched` (not `orgs`)

This prevents the "0 results" bug that occurred in June 2026 when table names diverged from the actual database schema.

---

## Correct Deployment Procedure

### Initial Deploy

1. **Sync search.db from home server to droplet:**
   ```bash
   rsync -avz ~/meritgiving/data/merit_registry.db \
     root@162.243.97.179:/data/precompute/v1/search.db
   ```
   (This file contains both the `registry_enriched` table and the `org_fts` FTS5 index.)

2. **Deploy droplet API:**
   ```bash
   rsync -avz ~/meritgiving/scripts/droplet_api.py \
     root@162.243.97.179:/opt/daanaa/droplet_api.py
   ```

3. **Restart the service:**
   ```bash
   ssh root@162.243.97.179 'systemctl restart daanaa'
   ```

4. **Verify startup:**
   ```bash
   ssh root@162.243.97.179 'journalctl -u daanaa -n 5 --no-pager'
   ```
   Look for: `✓ search.db validated: X organizations in FTS index (Y GB)`

5. **Test search:**
   ```bash
   curl -s 'https://daanaa.org/api/fused-search?q=food&page=1' | jq '.total'
   ```
   Should return a number > 0, not 0.

### Weekly Updates (optional)

If the home server's merit_registry.db is updated with new orgs or corrections, sync to droplet:

```bash
rsync -avz ~/meritgiving/data/merit_registry.db \
  root@162.243.97.179:/data/precompute/v1/search.db
```

No service restart needed unless API code changed. search.db is reloaded on the next query.

---

## Troubleshooting

### Symptom: daanaa.org/api/fused-search returns `total: 0`

**Check 1: Verify search.db exists and has data**
```bash
ssh root@162.243.97.179 'ls -lh /data/precompute/v1/search.db'
```
Should show a file > 1 GB (e.g., `9.9G`), not `0B`.

**Check 2: Restart API to trigger validation**
```bash
ssh root@162.243.97.179 'systemctl restart daanaa && sleep 3 && \
  journalctl -u daanaa -n 10 --no-pager | grep -E "validated|FATAL"'
```
If validation fails, the error message will explain the problem and how to fix it.

**Check 3: Verify org_fts table exists**
```bash
ssh root@162.243.97.179 'sqlite3 /data/precompute/v1/search.db \
  "SELECT COUNT(*) FROM org_fts;"'
```
Should return `1858452` (or close to it), not an error.

**Check 4: Test search locally**
```bash
ssh root@162.243.97.179 'curl -s http://127.0.0.1:5000/api/fused-search?q=food'
```
Should return results. If it returns `search_type: unavailable` or `error`, check error.log:
```bash
ssh root@162.243.97.179 'tail -50 /opt/daanaa/logs/error.log | grep -A2 "Search error"'
```

---

## Prevention Checklist

Before any deployment involving search:

- [ ] Confirm home server's `~/meritgiving/data/merit_registry.db` is not corrupted
  ```bash
  sqlite3 ~/meritgiving/data/merit_registry.db "SELECT COUNT(*) FROM org_fts;" > /dev/null && echo "✓ FTS index intact"
  ```

- [ ] Confirm rsync target path is **exactly** `/data/precompute/v1/search.db` (not a directory, not a symlink to a non-existent location)
  ```bash
  ssh root@162.243.97.179 'file /data/precompute/v1/search.db'
  ```
  Should show: `SQLite 3.x database, ... bytes`

- [ ] Never manually create an empty search.db file as a placeholder
  ```bash
  # ❌ NEVER DO THIS
  ssh root@162.243.97.179 'touch /data/precompute/v1/search.db'
  ```

- [ ] After deployment, always test search before considering it done
  ```bash
  curl -s 'https://daanaa.org/api/fused-search?q=test&page=1' | jq '.total'
  ```

---

## History

| Date | Event |
|------|-------|
| 2026-06-22 | Added startup validation + table name fixes; 0-byte search.db issue resolved |
| 2026-06-09 | Bug: search.db was 0 bytes (empty placeholder file); API returned 0 results |

