# Hardware Optimization Guide

**Date:** 2026-07-26  
**Server:** Ryzen 9700X + R9700 32GB VRAM  
**Status:** Light utilization, high swap pressure

---

## Current State (Snapshot 2026-07-26 15:24)

| Metric | Value | Threshold | Status |
|---|---|---|---|
| **CPU Idle** | 97.1% | <80% (good) | ✅ Plenty of headroom |
| **RAM Used** | 12GB / 31GB (38%) | <70% | ⚠️ Acceptable, but swap high |
| **Swap Used** | 3.5GB / 8GB (44%) | <20% | ❌ **Too high — indicates past memory pressure** |
| **Disk Used** | 582GB / 914GB (67%) | <75% | ⚠️ Approaching limit |
| **GPU Utilization** | Unknown | N/A | 🔍 Need `rocm-smi` check |

---

## Problems Identified

### 1. **HIGH SWAP USAGE (3.5GB)** ❌ CRITICAL

**Symptom:** System hit memory pressure at some point, started swapping to disk.

**Impact:** 
- Swapped memory is ~100x slower than RAM
- Slows enrichment daemon, inference servers, API
- Explains 0% efficiency in processing phase

**Immediate Fix (When at Server):**

```bash
# Clear swap caches (safe, doesn't lose data)
sudo sysctl -w vm.drop_caches=3   # Clear page cache + dentries
sync                               # Sync filesystem

# If still high, check what's using RAM
ps aux --sort=-%mem | head -20

# If one process is hogging RAM, consider restart:
# - Gunicorn: killall gunicorn (will auto-restart via systemd)
# - Embeddings: killall llama-server (restart via embed_server.sh)
```

**Long-term Fix:**
- Monitor swap usage: `watch -n 5 free -h`
- If swap > 2GB during idle: add more RAM or reduce worker count

---

### 2. **ENRICHMENT DAEMON STALLED** ❌ BLOCKS PIPELINE

**Symptom:** 0 links processed in 2h; efficiency at 0%

**Root Causes (Check in Order):**

```bash
# 1. Is daemon running?
ps aux | grep discovery_daemon

# 2. Is it blocked on database lock?
fuser data/merit_registry.db
lsof data/merit_registry.db

# 3. Are inference servers up?
curl http://localhost:11436/health  # Embeddings
curl http://localhost:11437/health  # LLM

# 4. Are there recent errors?
tail -100 logs/*.log | grep -i error
```

**Recovery (Choose One):**

**Option A: Soft Restart (Preferred)**
```bash
# Graceful shutdown
pkill -TERM discovery_daemon
sleep 5

# Restart
bash scripts/discovery_daemon.sh
```

**Option B: Hard Restart (If soft doesn't work)**
```bash
# Kill + wait
pkill -9 discovery_daemon
pkill -9 python3  # Nuclear if needed (will kill embeddings too)

# Restart everything
bash scripts/embed_server.sh &
bash scripts/watchdog_llama.sh &
sleep 30
bash scripts/discovery_daemon.sh
```

**Verify:**
```bash
# Should see links processing within 2 min
python3 scripts/blitz_efficiency_tracker.py  # Should show >0%
```

---

### 3. **DISK SPACE APPROACHING LIMIT** ⚠️ WATCH

**Current:** 582GB / 914GB (67%)  
**Danger Zone:** >75%  
**Time to Limit:** ~7–10 days at current usage

**What to Check:**

```bash
# Find largest directories
du -sh data/* scripts/* logs/* | sort -hr | head -10

# Old log cleanup (safe)
find logs -name "*.log" -mtime +30 -delete
find logs -name "*.log.1" -delete

# Model cache (if needed)
du -sh ~/.cache/ ~/.local/share/

# Backup database (before it fills)
tar -czf backups/merit_registry_$(date +%Y%m%d).tar.gz data/merit_registry.db
```

---

## Optimization Actions (Priority Order)

### Tier 1: Do Immediately (Blocks Production)

1. **Drop swap caches**
   ```bash
   sudo sysctl -w vm.drop_caches=3
   sync
   ```

2. **Verify inference servers**
   ```bash
   curl http://localhost:11436/health
   curl http://localhost:11437/health
   ```

3. **Restart enrichment daemon if needed**
   ```bash
   pkill discovery_daemon
   sleep 5
   bash scripts/discovery_daemon.sh
   ```

### Tier 2: Monitor (This Session)

- Watch swap usage: `watch -n 5 free -h`
- Watch CPU: `watch -n 5 top -bn1 | head -15`
- Check GPU: `watch -n 5 rocm-smi` (if available)

### Tier 3: Long-Term (This Week)

- Clean old logs (>30 days)
- Archive old backups
- Consider RAM upgrade if swap > 2GB remains during idle

---

## Performance Tuning (Optional)

### If GPU is Underutilized

**Current:** mxbai embeddings on GPU (11.6% RAM = 3.7GB)

**Optimization:**

```bash
# Check if GPU can handle higher batch size
# Current: --batch-size 512 --np 16 (parallel)
# Try: --batch-size 1024 --np 32 (if GPU has headroom)

# Edit: ~/.local/share/...llama-server command
# Then restart embed_server.sh
```

### If CPU is Underutilized (97% idle)

**Current:** Gunicorn 4 workers (could do more)

**Note:** 4 workers is already good for 8-core CPU. Don't increase.

### If Inference is Slow

**Checklist:**
- [ ] GPU is active (`rocm-smi` shows >50% util)
- [ ] Swap is <1GB
- [ ] Network is not saturated (`iftop` or `nethogs`)
- [ ] Database isn't locked (`lsof data/merit_registry.db`)

---

## Monitoring Commands (Bookmark These)

```bash
# System snapshot
free -h; df -h /; ps aux --sort=-%mem | head -5

# Background jobs
jobs; screen -ls; systemctl --user status

# Inference servers (health check)
curl http://localhost:11436/health && echo "✓ Embeddings" || echo "✗ Embeddings"
curl http://localhost:11437/health && echo "✓ LLM" || echo "✗ LLM"

# Enrichment pipeline
python3 scripts/blitz_efficiency_tracker.py

# Watch GPU (if available)
radeontop -b -d /dev/dri/card0 2>/dev/null | head -10

# Database status
sqlite3 data/merit_registry.db ".stat" | head -5
```

---

## Emergency Procedures

### If System is Slow (Everything)

```bash
# 1. Clear caches
sudo sysctl -w vm.drop_caches=3; sync

# 2. Kill non-critical processes
pkill gunicorn
pkill discovery_daemon

# 3. Restart critical stack
systemctl start daanaa-api
bash scripts/embed_server.sh &
bash scripts/discovery_daemon.sh

# 4. Wait 30s and test
curl http://localhost:5000/api/health
```

### If Disk is Full (>80%)

```bash
# 1. Find what's using space
du -sh /* | sort -hr | head -10

# 2. Emergency cleanup (in order)
rm -rf backups/*_old.tar.gz            # Old backups
find logs -name "*.log.1" -delete      # Rotated logs
find /tmp -type f -mtime +7 -delete    # Old temp files

# 3. If still critical, archive and delete:
tar -czf offsite_backup_$(date +%Y%m%d).tar.gz data/
rm -rf logs/*.log.{1..10}              # Keep only current
```

### If GPU Memory is Full

```bash
# Check what's on GPU
rocm-smi

# Restart embedding server (frees GPU memory)
pkill llama-server
sleep 5
bash scripts/embed_server.sh
```

---

## Scheduled Maintenance

### Weekly (Every Monday)

```bash
# Clean old logs
find logs -name "*.log" -mtime +30 -delete

# Clear temp files
find /tmp -type f -mtime +7 -delete

# Backup metrics
tar -czf backups/metrics_$(date +%Y%m%d).tar.gz logs/daanaa_api.log
```

### Monthly (1st of month)

```bash
# Archive old backups
mv backups/ backups_archive_$(date +%Y%m)/

# Disk cleanup
du -sh data/* | sort -hr
# Archive models if unused

# Restart all services (planned downtime, 15 min)
systemctl restart daanaa-api
bash scripts/embed_server.sh &
bash scripts/discovery_daemon.sh
```

---

## Capacity Planning

**Current Hardware:**
- RAM: 31GB (38% used, but 44% swap pressure → need monitoring)
- CPU: Ryzen 9700X (97% idle → plenty of headroom)
- Disk: 914GB (67% used → ~7 days until 75%)
- GPU: R9700 32GB VRAM (3.7GB used by embeddings)

**Recommended Actions (Next Quarter):**
- [ ] Archive old backups (free 50–100GB)
- [ ] Monitor swap weekly (if >2GB during idle, add RAM)
- [ ] Profile inference server (see if GPU can handle higher throughput)

---

## When Everything Works

**Green Light Indicators:**
- ✅ Swap usage < 1GB
- ✅ CPU idle > 70%
- ✅ Disk usage < 75%
- ✅ Blitz efficiency > 50%
- ✅ All inference servers responding

**If All Green:**
- Scale up enrichment (increase worker processes)
- Increase batch sizes on GPU
- Monitor only weekly instead of daily

---

**Prepared by:** Claude Code  
**For:** Akbar Khowaja (at server)  
**Last Updated:** 2026-07-26  
**Next Review:** Daily until swap < 1GB
