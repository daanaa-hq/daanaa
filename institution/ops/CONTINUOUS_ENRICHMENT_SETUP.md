# Continuous Enrichment Services — Home Server Setup

**Hardware:** Home server (Ryzen 9 7900X, 30GB RAM, GPU)  
**Not on droplet:** All enrichment runs locally; only precomputed outputs sync to droplet

---

## Architecture

| Service | Phase | Hardware | Schedule | Purpose |
|---------|-------|----------|----------|---------|
| **overnight_pipeline.py** | 1 (GPU) | Home server | 8pm-8am nightly | Mission generation, scoring, embeddings |
| **continuous_website_scraper.py** | 2 (I/O) | Home server | 24/7 continuous | Website discovery, validation |
| **cascading_link_scraper.py** | 3 (I/O) | Home server | 24/7 continuous | Donation & volunteer link extraction |

---

## Setup Option 1: Manual Shell Script

Start services manually:

```bash
cd ~/meritgiving
bash scripts/ops/start_continuous_enrichment.sh
```

Monitor logs:

```bash
tail -f logs/enrichment/continuous_website_scraper.log
tail -f logs/enrichment/cascading_link_scraper.log
```

Stop services:

```bash
pkill -f continuous_website_scraper.py
pkill -f cascading_link_scraper.py
```

---

## Setup Option 2: Systemd Services (Permanent)

Create service files (requires `sudo`):

```bash
sudo bash << 'EOF'
cat > /etc/systemd/system/daanaa-website-scraper.service << 'SERVICE'
[Unit]
Description=Daanaa Continuous Website Discovery
After=network.target

[Service]
Type=simple
User=akbar
WorkingDirectory=/home/akbar/meritgiving
Environment="PATH=/home/akbar/meritgiving/venv/bin:/usr/bin:/bin"
ExecStart=/bin/bash -c '. venv/bin/activate && python3 scripts/continuous_website_scraper.py --workers 8 --delay 5'
StandardOutput=journal
StandardError=journal
Restart=always
RestartSec=30
CPUQuota=50%
MemoryLimit=4G

[Install]
WantedBy=multi-user.target
SERVICE

cat > /etc/systemd/system/daanaa-cascading-scraper.service << 'SERVICE'
[Unit]
Description=Daanaa Cascading Link Discovery
After=network.target daanaa-website-scraper.service

[Service]
Type=simple
User=akbar
WorkingDirectory=/home/akbar/meritgiving
Environment="PATH=/home/akbar/meritgiving/venv/bin:/usr/bin:/bin"
ExecStart=/bin/bash -c '. venv/bin/activate && python3 scripts/cascading_link_scraper.py --workers 4 --delay 10'
StandardOutput=journal
StandardError=journal
Restart=always
RestartSec=30
CPUQuota=30%
MemoryLimit=2G

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable daanaa-website-scraper.service
systemctl enable daanaa-cascading-scraper.service
systemctl start daanaa-website-scraper.service
systemctl start daanaa-cascading-scraper.service
EOF
```

Check status:

```bash
systemctl status daanaa-website-scraper
systemctl status daanaa-cascading-scraper
systemctl journal -u daanaa-website-scraper -f
```

---

## Resource Allocation

**Website Scraper (Phase 2):**
- 8 parallel HTTP workers
- ~50-100MB RAM per worker
- CPU quota: 50% (won't starve other work)
- Memory limit: 4GB
- Designed for I/O wait (no GPU)

**Cascading Scraper (Phase 3):**
- 4 parallel HTTP workers
- CPU quota: 30% (lower priority, yields to GPU work)
- Memory limit: 2GB
- Starts after website scraper

**Nightly Pipeline (Phase 1):**
- GPU-intensive (runs 8pm-8am when demand is low)
- Uses Qwen2.5-32B (9GB) + embeddings server (2.9GB)
- CPU not limited (full machine available)

---

## Data Flow

```
Website scraped (Phase 2)
  ↓
website_status='ok' + quality_score updated
  ↓
Cascade triggered (Phase 3)
  ↓
donate_url extracted + tested + confidence-scored
  ↓
Write to registry_enriched.donate_url + donate_confidence
  ↓
Next nightly sync: copy precompute to droplet
  ↓
Droplet serves updated org profiles to users
```

---

## Monitoring

Check if services are running:

```bash
ps aux | grep continuous_website_scraper
ps aux | grep cascading_link_scraper
```

Sample logs to verify health:

```bash
# Website scraper should show batches completed
grep "Scraping" logs/enrichment/continuous_website_scraper.log | tail -5

# Cascading scraper should show donation links found
grep "Found" logs/enrichment/cascading_link_scraper.log | tail -5
```

Check database updates:

```bash
sqlite3 data/merit_registry.db \
  "SELECT COUNT(*) as orgs_with_websites FROM registry_enriched WHERE website_status='ok'"

sqlite3 data/merit_registry.db \
  "SELECT COUNT(*) as orgs_with_donation_links FROM registry_enriched WHERE donate_url IS NOT NULL"
```

---

## Expected Performance

**Website Scraper (Phase 2):**
- ~50-200 websites checked per batch
- ~1-2 seconds per website (HTTP + parsing)
- Total: 100-500 org websites validated per hour
- Covers all 2M orgs in ~2-4 weeks (continuous)

**Cascading Scraper (Phase 3):**
- Triggered by Phase 2 findings
- ~20-50 websites processed per batch
- Extracts and tests links: ~2-3 seconds per site
- Total: 50-100 donation links found per hour

**Nightly Pipeline (Phase 1):**
- Unchanged (8pm-8am)
- Full scoring, embeddings, FTS rebuild
- Uses GPU only when enrichment needed

---

## Troubleshooting

**Website scraper stuck?**
```bash
pkill -9 -f continuous_website_scraper.py
# Check for lock files in /tmp or database locks
sqlite3 data/merit_registry.db ".timeout 2000"
systemctl start daanaa-website-scraper
```

**Memory climbing?**
```bash
# Check which service is using RAM
top -p $(pgrep -f continuous_website_scraper)

# Restart service (systemctl handles this)
systemctl restart daanaa-website-scraper
```

**Database locked?**
```bash
# Find who has the lock
lsof | grep merit_registry.db

# Kill if orphaned
pkill -9 python3  # nuclear option
systemctl start daanaa-website-scraper daanaa-cascading-scraper
```

---

## Next Steps

1. Run Phase 2 test: `python3 scripts/continuous_website_scraper.py --limit 10`
2. Monitor logs for 1 hour
3. Install systemd services (with sudo) for permanent operation
4. Verify data flows to droplet nightly (check precompute sync)

