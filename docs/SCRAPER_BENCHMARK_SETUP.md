# Scraper Benchmark Infrastructure

## Overview

Automated nightly testing framework to compare web scraper implementations (current, aiohttp, future: Colly, etc.).

**Goal:** Measure throughput, latency, error rates across configurations to guide optimization decisions.

**Frequency:** Nightly (9pm) + on-demand testing

**Results:** Auto-generated dashboard at `docs/SCRAPER_BENCHMARKS.md`

---

## Architecture

```
overnight_benchmark_runner.py (cron: 9pm daily)
    ↓
benchmark_scrapers.py (orchestrator)
    ├── fetch_org_websites.py (current baseline)
    ├── fetch_org_websites_async.py (aiohttp test)
    └── [future: Colly, Crawl4AI, etc.]
    ↓
data/scraper_benchmarks/{timestamp}.json (results)
    ↓
docs/SCRAPER_BENCHMARKS.md (dashboard - auto-updated)
```

---

## Setup (One-Time)

### 1. Install aiohttp dependency

```bash
cd ~/meritgiving
source venv/bin/activate
pip install aiohttp==3.9.1
```

### 2. Verify scripts exist

```bash
ls -la scripts/benchmark_scrapers.py
ls -la scripts/fetch_org_websites_async.py
ls -la scripts/overnight_benchmark_runner.py
```

### 3. Test benchmark manually (30 min)

```bash
# Test with 1000 orgs (balanced between time and accuracy)
python3 scripts/benchmark_scrapers.py --limit 1000 --all-configs

# Or test with smaller set for quick verification
python3 scripts/benchmark_scrapers.py --limit 100 --configs current aiohttp
```

Expected output:
- Summary table with throughput, latency, success rate
- `docs/SCRAPER_BENCHMARKS.md` updated with results
- Results saved to `data/scraper_benchmarks/{timestamp}.json`

### 4. Setup cron job

```bash
# Edit crontab
crontab -e

# Add this line to run benchmark every night at 9pm
0 21 * * * cd /home/akbar/meritgiving && source venv/bin/activate && python3 scripts/overnight_benchmark_runner.py >> /tmp/overnight_benchmark_cron.log 2>&1
```

**Verify cron is set:**
```bash
crontab -l | grep overnight_benchmark
```

---

## Running Tests

### Nightly (Automatic)
- Runs at 9pm via cron
- Tests current + all available scrapers
- 1000 orgs per config (balanced)
- Results logged to `logs/overnight_benchmark.log`

### On-Demand (Manual)

**Test all available scrapers:**
```bash
python3 scripts/benchmark_scrapers.py --limit 1000 --all-configs
```

**Test specific scrapers:**
```bash
python3 scripts/benchmark_scrapers.py --limit 1000 --configs current aiohttp
```

**Quick test (5 min):**
```bash
python3 scripts/benchmark_scrapers.py --limit 100 --timeout 120
```

**Just regenerate dashboard from existing results:**
```bash
python3 scripts/benchmark_scrapers.py --dashboard-only
```

---

## Results Interpretation

### Metrics

| Metric | Meaning | Target |
|--------|---------|--------|
| **Throughput** | Requests/second | Higher = better |
| **Latency** | Avg response time (ms) | Lower = better |
| **Success Rate** | % of orgs fetched successfully | >95% |
| **Duration** | Total wall-clock time | Lower = better |

### Example Output

```
BENCHMARK SUMMARY
====================================================
current (requests + threads)
  Throughput: 3.45 req/sec
  Latency: 289.5ms avg
  Success: 96.8%
  Duration: 289.0s

aiohttp (async)
  Throughput: 35.62 req/sec
  Latency: 28.1ms avg
  Success: 97.2%
  Duration: 28.1s

🚀 Speedup: aiohttp is 10.3x faster than current
```

---

## Adding New Scrapers

To test a new scraper implementation (e.g., Colly, Crawl4AI):

1. **Create implementation file** (e.g., `scripts/fetch_org_websites_colly.py`)
   - Must export a `fetch_url(website)` function
   - Returns `(status_code, html_bytes)`

2. **Register in `benchmark_scrapers.py`**
   ```python
   # In main() function:
   try:
       from fetch_org_websites_colly import fetch_url as colly_fetch
       configs["colly"] = create_scraper_config("Colly (Go)", colly_fetch)
   except ImportError:
       pass  # Not available yet
   ```

3. **Run benchmark**
   ```bash
   python3 scripts/benchmark_scrapers.py --all-configs
   ```

4. **Results appear in dashboard automatically**

---

## Decision Criteria

### When to Switch to aiohttp?

✅ **Switch if:**
- aiohttp consistently 5x+ faster than current
- Success rate ≥ 95%
- Stable across multiple runs (check dashboard trend)

❌ **Don't switch if:**
- Success rate < 95%
- High variance between runs
- Implementation has bugs (check logs)

### When to Adopt Colly?

✅ **Consider if:**
- aiohttp plateaus (approaching network limits)
- Nightmares take >5 minutes even with async
- 86K URLs grows to 500K+

---

## Monitoring

### Daily checklist (after nightly run)

1. **Check logs:**
   ```bash
   tail -50 logs/overnight_benchmark.log
   ```

2. **Review dashboard:**
   ```bash
   cat docs/SCRAPER_BENCHMARKS.md
   ```

3. **Look for regressions:**
   - Did any config get slower?
   - Did error rate increase?
   - Did a network issue affect all configs equally?

### Weekly review

- Compare week-over-week trends
- Document any changes (code, network, schema)
- Adjust if bottlenecks shift

---

## Troubleshooting

### "ImportError: No module named aiohttp"

```bash
source venv/bin/activate
pip install aiohttp
```

### "No test orgs found"

The `registry_enriched` table may be empty or schema changed. Verify:
```bash
sqlite3 data/merit_registry.db "SELECT COUNT(*) FROM registry_enriched WHERE website_status='ok' AND website IS NOT NULL;"
```

### "Timeout reached"

Increase `--timeout` for slower networks:
```bash
python3 scripts/benchmark_scrapers.py --limit 1000 --timeout 900  # 15 min
```

### Cron isn't running

Check if cron is enabled:
```bash
sudo service cron status
```

Verify crontab:
```bash
crontab -l
```

Check logs:
```bash
grep CRON /var/log/syslog | tail -20
```

---

## Next Steps

### Phase 1 (This Week)
- [ ] Install aiohttp
- [ ] Test benchmark manually (limit=1000)
- [ ] Review results
- [ ] If aiohttp wins: commit + merge code
- [ ] Set up cron

### Phase 2 (Next Week)
- [ ] Run 3 nightly benchmarks
- [ ] Review trend in dashboard
- [ ] Decide: keep aiohttp or keep investigating current

### Phase 3 (Optional - Next Month)
- [ ] If aiohttp wins decisively, plan Colly evaluation
- [ ] Set deadline for Colly prototype (2 weeks)
- [ ] Begin parallel Colly implementation

---

## Files Reference

| File | Purpose |
|------|---------|
| `scripts/benchmark_scrapers.py` | Orchestrator - runs all configs, generates results |
| `scripts/fetch_org_websites_async.py` | aiohttp variant (test) |
| `scripts/fetch_org_websites.py` | Current implementation (baseline) |
| `scripts/overnight_benchmark_runner.py` | Cron entry point |
| `data/scraper_benchmarks/` | JSON results (one per night) |
| `docs/SCRAPER_BENCHMARKS.md` | Auto-updated dashboard |
| `logs/overnight_benchmark.log` | Cron execution logs |

---

## Questions?

- **Why aiohttp first?** Low effort (4-8h), high impact (10x), validates async approach before major Colly rewrite.
- **Why 1000 orgs?** Balances run time (~30 min) with statistical significance. 100-500 is too small, 5000+ takes too long.
- **Why every night?** Catches performance regressions early, provides trend data, costs nothing (runs off-peak).

