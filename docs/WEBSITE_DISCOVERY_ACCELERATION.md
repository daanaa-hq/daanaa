# Website Discovery Acceleration Plan

**Context:** Backups cleaned, disk healthy (61% used, 350GB free)
**Target:** +500 new website links/day while Gates run in parallel

## Current Coverage
- Total orgs: 2.056M
- With websites: 461K (22.4%)
- Gap: 1.595M (77.6%) without website data

## Acceleration Strategy (Autonomous)

**Pipeline:** discovery_daemon.py (already running)
- Scrapes org websites from Google, GuideStar, Charity Navigator
- Validates links (HTTP 200, no redirects)
- Updates registry_enriched table

**Parallelization:**
- CPU: 8 cores available
- GPU: R9700 (10pm-6am night window)
- Batch size: 1000 orgs/batch
- Throughput: ~500-1000 links/day baseline

**Target acceleration:** 2-4x baseline
- Increase workers from 4 to 8
- Batch size: 1000 → 2000
- Result: 1000-4000 links/day

## Runbooks

```bash
# Monitor discovery daemon
tail -f logs/discovery_daemon.log

# Check stats
sqlite3 data/merit_registry.db "
  SELECT 
    COUNT(*) as total_orgs,
    SUM(CASE WHEN website IS NOT NULL THEN 1 END) as with_website,
    ROUND(100.0 * SUM(CASE WHEN website IS NOT NULL THEN 1 END) / COUNT(*), 1) as pct
  FROM registry_enriched
"

# Check recent discoveries
sqlite3 data/merit_registry.db "
  SELECT COUNT(*) as new_websites, MAX(updated_at) as latest
  FROM registry_enriched
  WHERE website_status = 'verified' AND updated_at > datetime('now', '-1 day')
"
```

## Autonomous Execution

- Run continuously in background (already scheduled)
- No manual intervention needed
- Report metrics daily
- Escalate errors if discovery rate drops >50%

