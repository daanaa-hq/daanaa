# The Scraping Army Plan

## Executive Summary

We're building **sustainable, extensible web scraping infrastructure** for Daanaa and future projects.

**Current state:** 8 ThreadPool workers + requests = ~3 req/sec = 3-10 min for 86K URLs

**Goal:** 10-100x faster while maintaining quality + infrastructure that supports future projects

**Approach:** Test-driven optimization — measure each candidate, choose winner by data

---

## Phase Timeline

### Phase 1: aiohttp (This Week) ⚡
- **What:** Async Python variant using aiohttp + asyncio
- **Expected speedup:** 10-50x (30-100 req/sec)
- **Time to implement:** 4-8 hours
- **Risk:** Low (well-tested library, same Python codebase)
- **Effort to integrate:** Medium (swap fetch_url function)

**Deliverables:**
- ✅ `scripts/fetch_org_websites_async.py` (done)
- ✅ `scripts/benchmark_scrapers.py` (done)
- ✅ `scripts/overnight_benchmark_runner.py` (done)
- ⏳ Manual benchmark (30 min, your review)
- ⏳ Set up cron job (5 min)
- ⏳ 3 nights of data + decision

**Decision gate:** aiohttp is 5x+ faster than current with 95%+ success rate?
- **YES** → Adopt aiohttp as new baseline, plan Colly (Phase 2)
- **NO** → Keep investigating, try Colly sooner

---

### Phase 2: Colly (Next Month - Optional) 🚀
- **What:** Rewrite scraper in Go using Colly framework
- **Expected speedup vs current:** 50-200x (50-200 req/sec)
- **Expected speedup vs aiohttp:** 5-10x
- **Time to implement:** 2-3 weeks
- **Risk:** Medium (new language, larger rewrite)
- **Benefit:** Highest throughput, true distributed ready, future-proof

**Only pursue if:**
- aiohttp becomes bottleneck (network saturation)
- Nightly crawls still take 2+ minutes
- Scraping becomes core product

**How to start:**
1. Write Colly prototype (standalone)
2. Register in benchmark framework
3. A/B test vs aiohttp on 10K URLs
4. If Colly wins decisively → schedule 2-3 week migration

---

### Phase 3: Ongoing Capability Building 📊
- Framework stays in place **permanently**
- New scrapers added as needed (Crawl4AI for JS, Scrapy for scale, etc.)
- Each gets benchmarked automatically
- Dashboard shows historical trends

---

## Running the Benchmarks

### This Week: Manual Test

```bash
# Install aiohttp (one-time)
cd ~/meritgiving
source venv/bin/activate
pip install aiohttp

# Test with 1000 orgs (30 min)
python3 scripts/benchmark_scrapers.py --limit 1000 --all-configs

# You'll see:
# - Summary table (throughput, latency, success %)
# - Results saved to data/scraper_benchmarks/{timestamp}.json
# - Dashboard updated at docs/SCRAPER_BENCHMARKS.md
```

### Next Week: Automate

```bash
# Add to crontab to run nightly at 9pm
crontab -e

# Add this line:
0 21 * * * cd /home/akbar/meritgiving && source venv/bin/activate && python3 scripts/overnight_benchmark_runner.py >> /tmp/overnight_benchmark_cron.log 2>&1

# Verify:
crontab -l | grep overnight_benchmark
```

### Every Morning: Review

```bash
# Check latest results
tail -50 logs/overnight_benchmark.log

# View dashboard
cat docs/SCRAPER_BENCHMARKS.md
```

---

## What We've Built

### Files Created

| File | Purpose | Extensible? |
|------|---------|-----------|
| `scripts/benchmark_scrapers.py` | Orchestrator for all scrapers | ✅ Yes - add configs in main() |
| `scripts/fetch_org_websites_async.py` | aiohttp variant | ✅ Yes - template for future variants |
| `scripts/overnight_benchmark_runner.py` | Cron automation | ✅ Yes - modify to add email alerts, Slack, etc. |
| `docs/SCRAPER_BENCHMARK_SETUP.md` | Setup guide | ✅ Yes - update as variants added |

### Framework Capabilities

✅ **Pluggable** — Add scrapers without modifying core

✅ **Automatic** — Nightly runs, no manual effort

✅ **Measurable** — Throughput, latency, errors tracked

✅ **Auditable** — All results saved as JSON

✅ **Visual** — Auto-updated dashboard with trends

✅ **Extensible** — Template for future variants (Colly, Crawl4AI, etc.)

---

## Metrics to Watch

### Throughput (req/sec)
- Current: ~3
- aiohttp target: 30-100
- Colly target: 50-200

### Latency (avg ms)
- Current: ~300-400ms
- aiohttp target: <50ms
- Colly target: <10ms

### Success Rate
- Target: >95% (same as current)
- Alert if drops below 90%

### Duration (86K URLs)
- Current: 3-10 min
- aiohttp target: 15-60 sec
- Colly target: 5-30 sec

---

## Decision Framework

### After 3 nights of benchmarks, ask:

**Q1: Is aiohttp 5x+ faster?**
- YES → Proceed to Q2
- NO → Stop, wait for Colly

**Q2: Is aiohttp 95%+ success rate?**
- YES → Adopt aiohttp
- NO → Debug, fix, retry

**Q3: Is aiohttp stable across runs?**
- YES → Deploy to production
- NO → Find variance source, fix

**Q4: Is 86K URLs now <1 min?**
- YES → aiohttp wins, evaluate Colly later
- NO → Plan Colly for next month

---

## Integration Points

### When to integrate aiohttp into pipeline

**Option A: Replace in overnight_pipeline.py** (Safest)
```python
# Change line 480 from:
fetch_org_websites()  # Current

# To:
fetch_org_websites_async(workers=100)  # New
```

**Option B: Keep both, choose at runtime** (Flexible)
```python
if config.get("use_async_scraper"):
    fetch_org_websites_async(workers=100)
else:
    fetch_org_websites()
```

**Option C: Run A/B test in parallel** (Data-driven)
```python
# Run both, compare results, choose winner
```

---

## Success Criteria

✅ **Week 1:** aiohttp benchmark runs, dashboard populates

✅ **Week 2:** 3+ nights of data, showing consistent speedup

✅ **Week 3:** aiohttp integrated, baseline updated

✅ **Month 2:** Colly prototype (if needed), A/B tested

✅ **Ongoing:** Dashboard maintained, new scrapers added as needed

---

## Why This Approach

### Data-Driven
- Not guessing — measuring actual performance
- Benchmark framework forces rigor

### Low Risk
- aiohttp is well-tested, MIT licensed
- Fallback to current always available
- 4-8 hour investment for 10x potential return

### Extensible
- Framework stays in place permanently
- Future projects inherit working benchmarking
- Pattern established for adding Colly, Crawl4AI, etc.

### Sustainable
- Automation means no manual testing overhead
- Trends visible over time
- Easy to onboard team to "how we measure scrapers"

---

## Next Actions

### Today
- [ ] Review this plan
- [ ] Confirm aiohttp approach
- [ ] I'll: Install aiohttp, run manual benchmark

### This Week
- [ ] Manual test complete (1000 orgs)
- [ ] Review benchmark results
- [ ] Approve cron job setup
- [ ] Set reminder for nightly review

### Next Week
- [ ] Cron job running, 3 nights of data
- [ ] Decision: adopt aiohttp or investigate further?
- [ ] If YES → Plan integration into overnight_pipeline.py
- [ ] If NO → Debug issues, retry

### Next Month
- [ ] aiohttp live (if Phase 1 succeeded)
- [ ] Dashboard + trend analysis
- [ ] Optional: Colly prototype decision

---

## Questions?

**Q: Will this slow down the nightly pipeline?**
A: No. Benchmarks run independently. When integrated, aiohttp is faster, not slower.

**Q: What if benchmarks show aiohttp is slower?**
A: Investigate why. Might be network-bound, not CPU/GPU. Then evaluate Colly.

**Q: Can we test Colly now?**
A: Yes, but let's validate async approach first (aiohttp). Colly is bigger rewrite — want to know if async is the right direction first.

**Q: What about Scrapy?**
A: Good for 100K+ URLs on cluster. Overkill for 86K on single machine. If aiohttp hits limits, consider then.

**Q: How do we integrate into tonight's 9pm pipeline?**
A: After Phase 1 succeeds (3 nights of data + decision). Not until we know aiohttp wins.

---

## Success Looks Like

**Next Friday (7 days):**
```
🎯 Manual benchmark complete
   ✅ aiohttp: 35 req/sec (10x current)
   ✅ Success: 97%
   ✅ Dashboard populated
   → DECISION: Proceed with Phase 2
```

**Next Thursday (14 days):**
```
📊 Three nights of data
   ✅ aiohttp trending stable
   ✅ No regressions
   ✅ Team reviewing results
   → DECISION: Integrate aiohttp or iterate
```

**Next Month (30 days):**
```
⚡ aiohttp live in production
   ✅ 86K URLs: 30 sec (vs 3-10 min)
   ✅ Nightly pipeline 5-10x faster
   ✅ Framework proven, ready for Colly prototype
   → NEXT: Plan Phase 2 or move to other projects
```

---

## The Bigger Picture

This isn't just about faster scraping. We're building:

1. **Repeatable infrastructure** — Apply to future projects
2. **Measurement discipline** — Data-driven decisions, not guesses
3. **Optimization mindset** — Systematic approach to bottlenecks
4. **Team capability** — Everyone knows how to benchmark, add variants

Six months from now, you'll have:
- Proven scraping pipeline (current, async, maybe Colly)
- Benchmark framework working for other tasks
- Data-driven culture around performance
- Extensible pattern for new optimizations

This is how great infrastructure gets built. 🚀

