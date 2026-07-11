# Scraper Benchmark Results

Nightly performance tracking of web scraper implementations.

Auto-updated daily. Compare configurations to identify optimizations.


## Latest Run Summary

| Config | Throughput (/s) | Avg Latency (ms) | Success Rate | Duration (s) |
|--------|-----------------|------------------|--------------|--------------|
| current (requests + threads) | 1.39 | 665.24 | 99.4% | 300.35 |
| aiohttp (async) | 0 | 0 | 0.0% | 0.0 |
| current + ThreadPool x16 | 19.27 | 498.3 | 95.6% | 24.8 |
| aiohttp async x32 | 12.94 | 433.24 | 47.4% | 18.32 |
| current + ThreadPool x32 | 12.49 | 500.83 | 48.0% | 19.22 |
| aiohttp async x64 | 13.71 | 645.92 | 48.0% | 17.5 |

## Performance Trends

**current (requests + threads)**: 1.39/s 📈 (+0.10/s vs previous run)
**aiohttp (async)**: 0/s ➡️ (+0.00/s vs previous run)
**current + ThreadPool x16**: 19.27/s 📈 (+2.50/s vs previous run)
**aiohttp async x32**: 12.94/s 📈 (+0.15/s vs previous run)
**aiohttp async x64**: 13.71/s 📈 (+0.72/s vs previous run)

## Full History


### aiohttp (async)

| Timestamp | Throughput | Latency | Success | Duration |
|-----------|-----------|---------|---------|----------|
| 2026-07-06 | 0/s | 0ms | 0.0% | 0.0s |
| 2026-07-06 | 0/s | 0ms | 0.0% | 0.0s |

### aiohttp async x32

| Timestamp | Throughput | Latency | Success | Duration |
|-----------|-----------|---------|---------|----------|
| 2026-07-11 | 12.94/s | 433.24ms | 47.4% | 18.32s |
| 2026-07-11 | 12.79/s | 431.59ms | 47.6% | 18.61s |
| 2026-07-11 | 12.69/s | 418.4ms | 47.6% | 18.76s |
| 2026-07-11 | 21.74/s | 435.63ms | 87.5% | 1.61s |

### aiohttp async x64

| Timestamp | Throughput | Latency | Success | Duration |
|-----------|-----------|---------|---------|----------|
| 2026-07-11 | 13.71/s | 645.92ms | 48.0% | 17.5s |
| 2026-07-11 | 12.99/s | 699.36ms | 46.8% | 18.01s |
| 2026-07-11 | 13.28/s | 643.89ms | 47.4% | 17.85s |

### current (requests + threads)

| Timestamp | Throughput | Latency | Success | Duration |
|-----------|-----------|---------|---------|----------|
| 2026-07-06 | 1.39/s | 665.24ms | 99.4% | 300.35s |
| 2026-07-06 | 1.29/s | 712.38ms | 99.3% | 300.56s |

### current + ThreadPool x16

| Timestamp | Throughput | Latency | Success | Duration |
|-----------|-----------|---------|---------|----------|
| 2026-07-11 | 19.27/s | 498.3ms | 95.6% | 24.8s |
| 2026-07-11 | 16.77/s | 539.99ms | 95.6% | 28.51s |
| 2026-07-11 | 14.31/s | 690.19ms | 96.2% | 33.62s |
| 2026-07-11 | 6.62/s | 935.27ms | 90.0% | 5.44s |

### current + ThreadPool x32

| Timestamp | Throughput | Latency | Success | Duration |
|-----------|-----------|---------|---------|----------|
| 2026-07-11 | 12.49/s | 500.83ms | 48.0% | 19.22s |

*Last updated: 2026-07-11T06:06:37.878094+00:00*

## Analysis — 2026-07-11 (framework repaired)

The 2026-07-06 numbers were artifacts: the harness ran every fetcher serially
(1.39/s = 1/latency, not production speed) and called the async fetcher without
awaiting it (the "100% failure"). After adding concurrency-aware batch runners:

| Config | Success | Rate | Note |
|---|---|---|---|
| requests+threads x16 | 95.6% | 17–19/s | production behavior, measured honestly |
| aiohttp x12 + DNS throttle | 92% | 16.9/s | 1 connection failure |
| aiohttp x16 | 88% | 22.3/s | failures rising |
| aiohttp x32/64 | 47–48% | — | mass ClientConnectorError |

Root cause of the aiohttp collapse: NOT the library — the network path (home
router/NAT) fails connection attempts past ~12–16 concurrent SYNs to distinct
hosts. A DNS-throttling resolver (ThrottledResolver in
fetch_org_websites_async.py) was added and helps at the margin, but the
ceiling is environmental.

**Decision: keep requests+ThreadPool x16 (boring by default).** At the network
ceiling both stacks tie, and the threaded scraper is battle-tested. At a true
~17/s, the full 115K-site inventory re-scrapes in <2h of night window —
website scraping is not the enrichment bottleneck; scheduling and coverage
selection are. Revisit only if the box moves to a datacenter uplink (then
aiohttp's higher concurrency has headroom).
