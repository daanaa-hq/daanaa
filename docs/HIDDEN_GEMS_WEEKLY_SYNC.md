# Hidden Gems Weekly Rotation & Sync

## Overview

Hidden gems (small, financially healthy, low-profile organizations) are rotated weekly to give every gem equal visibility. The rotation is deterministic and seed-driven by ISO week number, so all users see the same gems each week.

---

## Current Status (as of 2026-06-22)

- ✅ **Precompute script ready:** `scripts/precompute_hidden_gems.py` generates `ALL_<page>.json.gz` files for each week
- ✅ **Droplet deployment ready:** Static files served from `/data/precompute/v1/browse/hidden_gems/`
- ⏳ **Weekly cron:** Not yet installed (TODO)

---

## How It Works

1. **On the home server (Monday AM):**
   - `precompute_hidden_gems.py` runs with the current ISO week number as seed
   - Generates ~34K gems (33,971 as of database snapshot 2026-06-21)
   - Output: 1,359 pages in `precompute_output/browse/hidden_gems/ALL_<page>.json.gz`
   - Files are deterministic: same week number always produces same gems in same order

2. **On the droplet:**
   - Droplet API checks for `hidden_gem=1` parameter in GET /api/organizations
   - If set and no other filters, serves static files from `/data/precompute/v1/browse/hidden_gems/`
   - Zero query cost (static file read only)

3. **Frontend:**
   - Landing: `/directory` defaults to `hidden_gem=true`
   - Display: "Hidden gems · a fresh set each week" with "See all 1.8M" action to clear the filter

---

## Installation: Weekly Cron (TODO)

Add to root's crontab on the home server to run every Monday 7:00 AM UTC:

```bash
# Every Monday at 7:00 AM: Regenerate and sync hidden gems
0 7 * * 1 cd /home/akbar/meritgiving && source venv/bin/activate && \
  python3 scripts/precompute_hidden_gems.py && \
  rsync -avz --delete precompute_output/browse/hidden_gems/ \
    root@162.243.97.179:/data/precompute/v1/browse/hidden_gems/ 2>&1 | \
  tee -a logs/hidden_gems_sync.log
```

**To install:**
```bash
# Edit crontab
sudo crontab -e

# Paste the line above, save and exit
```

**To verify:**
```bash
sudo crontab -l | grep hidden_gems
```

---

## Manual Sync (if needed)

If you need to manually refresh hidden gems (e.g., after a database change):

```bash
cd ~/meritgiving

# Activate venv
source venv/bin/activate

# Regenerate with current ISO week seed
python3 scripts/precompute_hidden_gems.py

# Sync to droplet
rsync -avz --delete precompute_output/browse/hidden_gems/ \
  root@162.243.97.179:/data/precompute/v1/browse/hidden_gems/

# Verify (should show ~1,359 files)
ssh root@162.243.97.179 'ls /data/precompute/v1/browse/hidden_gems/ | wc -l'
```

---

## Testing

**Before installing cron, test the full flow:**

1. **Verify precompute script works:**
   ```bash
   python3 scripts/precompute_hidden_gems.py
   ls -lh precompute_output/browse/hidden_gems/ALL_1.json.gz
   ```
   Should show a file ~50KB.

2. **Verify rsync destination exists:**
   ```bash
   ssh root@162.243.97.179 'mkdir -p /data/precompute/v1/browse/hidden_gems'
   ```

3. **Do a test sync:**
   ```bash
   rsync -avz --delete precompute_output/browse/hidden_gems/ \
     root@162.243.97.179:/data/precompute/v1/browse/hidden_gems/
   ```

4. **Verify frontend can load hidden gems:**
   ```bash
   curl -s 'https://daanaa.org/api/organizations?hidden_gem=1&page=1' | \
     jq '.organizations | length'
   ```
   Should return 25 (the page size).

---

## Monitoring

Once cron is running, check the sync log weekly:

```bash
tail -20 ~/meritgiving/logs/hidden_gems_sync.log
```

Expected output (success):
```
building file list ... done
ALL_1.json.gz
ALL_2.json.gz
...
sent X bytes  received Y bytes  Z.ZZ bytes/sec
```

Expected output (failure) — investigate immediately:
```
rsync: ... connection refused
```

---

## Troubleshooting

**Problem: Cron doesn't run**
- Check it's installed: `sudo crontab -l | grep hidden_gems`
- Check system mail: `mail` (root cron errors go here)
- Check that droplet is reachable: `ping -c 1 162.243.97.179`

**Problem: Gems don't change week-to-week**
- Verify ISO week number is different: `python3 -c "from datetime import datetime; import datetime as dt; print(datetime.datetime.now().isocalendar()[1])"`
- Verify script uses `datetime.now().isocalendar()[1]` as seed (it does)

**Problem: Gems endpoint returns 0 results**
- Check files synced: `ssh root@162.243.97.179 'ls /data/precompute/v1/browse/hidden_gems/ | head -5'`
- Check file size: `ssh root@162.243.97.179 'du -sh /data/precompute/v1/browse/hidden_gems/'`
- See SEARCH_DB_DEPLOYMENT.md troubleshooting if API returns `unavailable` or `error`

---

## Future Enhancements

- [ ] Email notification on sync success/failure (use daanaa.org automation stack)
- [ ] Metrics: track sync duration, file count, org count per week
- [ ] A/B test gem rotation with users (e.g., 50% random sampling)
