# Automated Deployment Guide

## Overview

Daanaa now has three automated deployment pipelines:

1. **On-Push Deployment** — Auto-deploy to droplet when you push to `master`
2. **Nightly Web Discovery Pipeline** — Runs at 11 PM, discovers websites and donation links
3. **Nightly Database Sync** — Runs after pipeline, syncs updated database to droplet

---

## 1. On-Push Deployment (Automatic)

**What happens:**
```
git push origin master
  ↓
[Git hook triggers]
  ↓
Frontend builds
  ↓
Code syncs to droplet
  ↓
API restarts
  ↓
Health check confirms success
```

**How to use:**
```bash
# Make your changes
git add <files>
git commit -m "your message"

# Push to master — deployment starts automatically
git push origin master
```

**Logs:**
- `~/meritgiving/logs/deployment.log` — tracks each deployment
- Check with: `tail -f ~/meritgiving/logs/deployment.log`

**Manual deployment (if needed):**
```bash
bash ~/meritgiving/scripts/deploy.sh
```

---

## 2. Nightly Web Discovery Pipeline (Automatic)

**When:** Every day at 11 PM (23:00)

**What runs:**
- Phase 2: HTTP verification (verifies 100K+ website candidates)
- Phase 3: Donation link extraction (finds give/donate links)
- Phase 4: GPU semantic verification (if embedding server available)

**Logs:**
- `~/meritgiving/logs/web_discovery_nightly.log` — pipeline progress

---

## 3. Nightly Database Sync (Automatic)

**When:** Right after web discovery pipeline completes (~11:30-11:45 PM)

**What happens:**
1. Compresses local database (19GB → ~4.5GB)
2. Transfers to droplet via SCP
3. Decompresses on droplet
4. Restarts API with new data
5. Verifies health

**Why:** Ensures www.daanaa.org always has the latest:
- v4 scores
- Website discovery data
- Donation links
- Organization metadata

**Logs:**
- `~/meritgiving/logs/db_sync.log` — sync progress and status

---

## Troubleshooting

### Deployment Failed

1. Check the log:
   ```bash
   tail -20 ~/meritgiving/logs/deployment.log
   ```

2. Common issues:
   - **SSH key error**: Verify `~/.ssh/daanaa_do` exists and is readable
   - **Build error**: Run `cd frontend && npm run build` locally to debug
   - **API restart failed**: SSH to droplet and check: `pkill -f gunicorn; ps aux | grep gunicorn`

3. Manual retry:
   ```bash
   bash ~/meritgiving/scripts/deploy.sh
   ```

### Database Sync Failed

1. Check log:
   ```bash
   tail -30 ~/meritgiving/logs/db_sync.log
   ```

2. Check droplet disk:
   ```bash
   ssh -i ~/.ssh/daanaa_do root@162.243.97.179 "df -h /"
   ```

3. If disk is full:
   ```bash
   ssh -i ~/.ssh/daanaa_do root@162.243.97.179 "rm /opt/daanaa/data/merit_registry.db.bak"
   ```

4. Manual sync:
   ```bash
   bash ~/meritgiving/scripts/sync_db_to_droplet.sh
   ```

---

## What Gets Deployed

### On Every Push to Master

- Frontend code (React/TypeScript)
- Backend code (Python/Flask)
- Scripts (data pipeline, utilities)
- Configuration files
- Database (if changed)

### Excluded (Never Synced)

- `.git/` — version control
- `node_modules/` — dependencies (droplet has its own)
- `venv/` — Python virtualenv
- `.env` — sensitive config
- `*.db.gz` — temporary files

---

## Monitoring

### Check Deployment Status
```bash
# Recent deployments
tail -20 ~/meritgiving/logs/deployment.log

# Last 5 deployments
grep "DEPLOYMENT SUCCESS\|DEPLOYMENT START" ~/meritgiving/logs/deployment.log | tail -10
```

### Check API Health
```bash
# Localhost
curl -s http://localhost:5000/api/stats | jq '.total_organizations, .scores_last_updated'

# Droplet (public site)
curl -s https://www.daanaa.org/api/stats | jq '.total_organizations, .scores_last_updated'

# Should match!
```

### Check Database Freshness
```bash
ssh -i ~/.ssh/daanaa_do root@162.243.97.179 \
  "curl -s http://localhost/api/stats | jq '.scores_last_updated'"
```

---

## Customization

### Change Deployment Time

Edit crontab:
```bash
crontab -e
```

Find this line:
```
0 23 * * * cd ~/meritgiving && ...
```

- `0 23` = 11 PM
- `0 00` = Midnight
- `0 03` = 3 AM
- [Cron syntax reference](https://crontab.guru)

### Change Deployment Branch

Edit `~/meritgiving/.git/hooks/post-push`:
```bash
if [ "$BRANCH" = "production" ]; then  # Change "master" to your branch
```

### Disable Auto-Deployment

```bash
rm ~/.git/hooks/post-push
```

To re-enable:
```bash
chmod +x ~/meritgiving/scripts/deploy.sh
bash ~/meritgiving/scripts/deploy.sh  # manual deployment
```

---

## SSH Key Setup (Already Done ✓)

- Key: `~/.ssh/daanaa_do`
- Permissions: `600`
- Used for: Droplet access (no password needed)

---

## Next Steps

1. **Test it:** Push a small change to master and watch the deployment
   ```bash
   git push origin master
   tail -f ~/meritgiving/logs/deployment.log
   ```

2. **Monitor the first nightly sync:** Check logs at 11:30 PM tomorrow
   ```bash
   tail -f ~/meritgiving/logs/db_sync.log
   ```

3. **Verify both sites match:**
   ```bash
   # Localhost
   curl -s http://localhost:5000/api/stats | jq .total_organizations
   # Droplet
   curl -s https://www.daanaa.org/api/stats | jq .total_organizations
   ```

---

## Emergency: Manual Deployment

If automation fails:

```bash
# Deploy frontend + restart API
bash ~/meritgiving/scripts/deploy.sh

# Sync database to droplet
bash ~/meritgiving/scripts/sync_db_to_droplet.sh

# Or both together
bash ~/meritgiving/scripts/deploy.sh && bash ~/meritgiving/scripts/sync_db_to_droplet.sh
```

All done! 🚀
