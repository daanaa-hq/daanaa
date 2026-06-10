# PHASE 4 — Performance (measured 2026-06-09 18:55) — before-numbers

## Verdict: the public site is currently FAST; the real risk is swap exhaustion on the
## home server. Two audit hypotheses (embed hang, no caching) are FALSE.

## Measured baseline (before-numbers)
| Probe | Result |
|---|---|
| local /api/search?q=food+bank (cold) | **3.66 s** |
| local same query (warm, cached) | 0.007 s |
| local same query (3rd run) | 0.23 s |
| local /api/search/semantic (cold → warm) | 1.01 s → 0.11 s |
| local /api/organizations page 1 | 0.90 s |
| local /health | 0.0006 s |
| **https://daanaa.org/api/search (3 runs)** | **0.24 / 0.11 / 0.11 s** |
| https://daanaa.org/ homepage | 0.11 s |

System: 16 cores, load 0.21 (idle). Disk 59% used. RAM 30 GB: 18 GB used, 11 GB available.
**Swap: 7.8 / 8.0 GB used (97%).** Gunicorn: 5 procs (master+4 workers) ≈ 2.2 GB resident each.

## Hypotheses tested
- **"Droplet is slow"** → NOT reproducible today: 0.11 s through Cloudflare. Either fixed
  by the precompute/static architecture or intermittent. Keep this baseline for comparison.
- **"Embedding call can hang workers"** → FALSE. `_embed_query` (daanaa_api.py:193-216)
  posts to Vulkan llama-server with `timeout=5`, falls back to Ollama with `timeout=10`,
  both exception-wrapped returning None (semantic search degrades gracefully). ✔
- **"No caching"** → FALSE. In-process cache with tuned TTLs (daanaa_api.py:70-77:
  search 30 min, org 30 min, ntee 2 h). Cold→warm = 3.66 s → 0.007 s proves it works.

## Findings

### HIGH
1. **Swap 97% full on the home server** — 7.8/8.0 GB consumed while 11 GB RAM sits
   "available." Long-running processes (gunicorn workers ~2.2 GB each, llama servers)
   have been pushed to swap over 10 days uptime. This is the likely cause of
   intermittent multi-second cold-path stalls (page-fault storms), matching the 3.66 s
   cold search. Fix: (a) restart API weekly via cron (already have merit_daemon Sunday
   slot) to re-share CoW pages, (b) `vm.swappiness=10`, (c) verify the 546K-vector numpy
   matrix is actually shared post-fork — 2.2 GB × 4 workers resident suggests partial
   CoW breakdown.

### MED
2. **SQLite connections untuned** — daanaa_api.py:340-346. Per-request
   `sqlite3.connect(DB_PATH)` against a 9.6 GB DB with no PRAGMAs: no `mmap_size`, no
   `cache_size`, not read-only. Cold queries pay full page-read cost. Fix: on connect,
   `PRAGMA mmap_size=2147483648; PRAGMA cache_size=-64000;` and open catalog reads with
   `file:...?mode=ro` (also a safety win — read paths can't write).

### LOW
3. **Cold-path first-hit latency** — 3.66 s on uncached search is what users feel after
   any cache-expiry or restart. Mitigations: finding 2 above + a tiny warm-up script
   hitting the top-20 cached queries after restart (curl loop in restart_api.sh).

## Cross-phase
- Frontend fetch timeout (Phase 2 HIGH) is still the right fix for cold spikes: 10 s
  client timeout + error UI turns a hang into a message.
- Watchdog fix (Phase 3 MED) matters more given memory pressure → if gunicorn OOMs,
  nothing restarts it today.
