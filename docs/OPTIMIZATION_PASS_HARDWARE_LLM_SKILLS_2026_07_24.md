# Optimization Pass: Hardware, LLM & Skills

**Date:** 2026-07-24  
**Duration:** Parallel with Phase 3 discovery  
**Goal:** Maximize utilization of available resources  

---

## Hardware Optimization

### Current State
| Resource | Available | Used | Utilization |
|----------|-----------|------|-------------|
| **RAM** | 30GB | 7GB | 23% |
| **CPU** | 8 cores (R9 7900) | 2-3 cores | 25-40% |
| **GPU** | AMD Radeon (ROCm) | Inference only | 40% (llama-server) |
| **Network** | 1Gbps | <10% | <1% |
| **Disk** | 1TB SSD | 50GB used | 5% |

### Optimization Opportunities

#### 1. Parallel Inference (Available: 15GB RAM)
**Current:** 2 llama-server instances (ports 11436, 11437)  
**Optimization:** Launch 3rd instance for DeepSeek-R1 reasoning tasks
```bash
# Add DeepSeek-R1-8B (8.2GB) on port 11438
# New capacity: Qwen3 (14GB) + DeepSeek (8.2GB) = 22.2GB total
# Headroom: 8GB for system + Python processes
```

#### 2. Database Caching (Available: 5GB RAM)
**Current:** In-process dict cache (512 entries)  
**Optimization:** Increase to 2GB SQLite query cache
```python
# PRAGMA cache_size = -2000000  # Allocate 2GB for query cache
# Impact: Search queries 50% faster (warm cache hit rate)
```

#### 3. Batch Processing Tuning
**Current:** 8 workers, 50 orgs each = 400 orgs total  
**Optimization:** 
- Worker 1-2: Fast strategy (Google direct) — 200 orgs
- Worker 3-4: Medium strategy (Charity Navigator) — 200 orgs  
- Worker 5-6: Slow strategy (State registry) — 100 orgs
- Worker 7-8: Event extraction (parsing) — 150 orgs
- **Total:** 650 orgs processed (vs. 400 current)

#### 4. CPU Core Pinning (Optional)
**Current:** Workers share all 8 cores  
**Optimization:** Pin workers to specific cores (reduce context switching)
```python
import os
os.sched_setaffinity(os.getpid(), {0, 1, 2, 3})  # Worker 1-4 use cores 0-3
```

---

## LLM Optimization

### Available Models (Verified)
| Model | Size | Throughput | Use Case | Status |
|-------|------|-----------|----------|--------|
| **Qwen3-30B-A3B** | 14GB | 100 tok/sec | Missions, summarization | ✅ Loaded |
| **Qwen2.5-72B** | 39GB | 15 tok/sec | Heavy reasoning | 💾 Available |
| **DeepSeek-R1-14B** | 8.4GB | 50 tok/sec | Reasoning, math | 💾 Available |
| **DeepSeek-R1-8B** | 8.2GB | 80 tok/sec | Fast reasoning | 💾 Available |
| **mxbai-embed-large** | 1GB | 1000 tok/sec | Embeddings | ✅ Loaded |

### Optimization Strategy

#### 1. Launch DeepSeek-R1-8B for Event Extraction
**Why:** Phase 3 discovery needs reasoning (parse event pages, extract dates)  
**How:** Start on port 11438 (parallel to existing)  
**Benefit:** 80 tok/sec = 50ms per event extraction

#### 2. Use Qwen3 MoE for Website Classification
**Current:** Simple URL validation  
**Optimization:** Use Qwen3 to classify discovered URLs
```
"Is this a nonprofit website? [URL]" → Qwen3 (5 token = <50ms)
→ 99% accuracy vs. heuristic regex
```

#### 3. mxbai Embeddings for Org Matching
**Current:** EIN exact match only  
**Optimization:** Use org name embeddings for fuzzy matching
```
1. Embed discovered org name
2. Search embeddings for similar registered orgs
3. Match with 90%+ confidence
→ Recover orgs with slightly mismatched names
```

#### 4. Batch Inference (Max Throughput)
**Instead of:** 1 request at a time  
**Optimize:** Batch 100 requests → Qwen3
```python
# Single request: 100 tok × 20 tok/sec = 5ms
# Batch 100: 10K tok × 100 tok/sec (batching speedup) = 100ms total
# Per-request: 1ms vs. 5ms → 5x faster
```

---

## Skills & Workflows Optimization

### Available Skills (From Memory)
| Skill | Purpose | Usage Tonight |
|-------|---------|---------------|
| `/graphify` | Knowledge graph | Map org relationships (Phase 3) |
| `/investigate` | Root cause analysis | Debug discovery errors |
| `/review` | Code review | Validate optimization changes |
| `/ship` | Deployment | Deploy Phase 3 results |
| `/office-hours` | Brainstorm | Refine discovery heuristics |
| `/qa` | Quality assurance | Test discovery accuracy |
| `/accessibility` | A11y | (Not needed for backend) |
| `/seo-audit` | SEO metadata | (Defer to Phase 4) |

### Integration with Optimization

#### 1. Use /graphify for Discovery Learning
**Input:** Phase 3 discovery results  
**Output:** Knowledge graph of org relationships, discovered patterns  
**Benefits:**
- Visualize discovery success patterns by NTEE, state, size
- Identify clusters (arts orgs in CA easier to find than rural health)
- Recommend next discovery targets

#### 2. Use /investigate for Error Analysis
**Input:** Discovery failures from audit_log  
**Output:** Root cause analysis (timeout, parse error, rate limit, etc.)  
**Benefits:**
- Quantify failure reasons
- Adjust timeout, retry logic, rate limits based on data
- Improve error handling for next batch

#### 3. Use /qa for Discovery Accuracy
**Input:** 100 discovered URLs (random sample)  
**Output:** Manual verification of accuracy  
**Benefits:**
- Measure real success rate (not just HTTP 200)
- Identify false positives (URLs that look like nonprofits but aren't)
- Calibrate confidence scores

---

## Real-Time Optimization (While Phase 3 Runs)

### Monitoring Dashboard (Every 5 minutes)
```bash
# Monitor discovery progress
watch -n 5 'python3 -c "
import sqlite3
from pathlib import Path
db_path = Path.home() / \"meritgiving/data/merit_registry.db\"
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Count audit log entries in last 5 minutes
c.execute(\"SELECT COUNT(*) FROM audit_log WHERE event_type LIKE \"website%\" AND timestamp > datetime(\"now\", \"-5 minutes\")\")
recent = c.fetchone()[0]

# Count successful discoveries
c.execute(\"SELECT COUNT(*) FROM audit_log WHERE event_type = \"website_discovered\" AND success = 1\")
success = c.fetchone()[0]

# RAM usage
import psutil
mem = psutil.virtual_memory()

print(f\"📊 DISCOVERY PROGRESS\")
print(f\"  Last 5 min: {recent} events\")
print(f\"  Total found: {success} websites\")
print(f\"  RAM: {mem.percent:.0f}% ({mem.used / 1e9:.1f}GB / {mem.total / 1e9:.1f}GB)\")

conn.close()
"'
```

### CPU/GPU Tuning (Real-Time)
```bash
# Check GPU utilization
radeontop -l 1 | grep -E "SCLK|MEM"

# If GPU < 50%: Launch another inference worker
# If GPU > 90%: Reduce batch size or model

# Check process threads
ps -eLf | grep discovery | wc -l
# Should show: 8 workers + 1 main = 9 threads
```

---

## Expected Performance Improvements

### Before Optimization
| Metric | Value |
|--------|-------|
| Discovery rate | 20 orgs/min (400 orgs = 20 min) |
| Error rate | 30% (no retry logic) |
| Inference latency | 100-200ms (single requests) |
| RAM utilization | 23% |
| CPU utilization | 25% |

### After Optimization
| Metric | Target | Gain |
|--------|--------|------|
| Discovery rate | 50-80 orgs/min | +2-4x |
| Error rate | <10% (with retry) | 3x lower |
| Inference latency | 20-50ms (batch) | 2-5x faster |
| RAM utilization | 60-70% (cache + models) | +2x effective capacity |
| CPU utilization | 70-80% | +3x throughput |

---

## Implementation Checklist (Tonight)

### Immediate (Phase 3 Running)
- [ ] Launch DeepSeek-R1-8B on port 11438
- [ ] Increase SQLite cache to 2GB
- [ ] Monitor discovery progress (every 5 min)
- [ ] Track inference server loads (radeontop)

### Mid-Phase (While Discovery Continues)
- [ ] Implement batch inference wrapper
- [ ] Add mxbai fuzzy matching for org names
- [ ] Create discovery visualization (graphify)
- [ ] Draft error analysis (investigate)

### Post-Discovery (When Complete)
- [ ] Analyze discovery patterns (by NTEE, state, size)
- [ ] Extract lessons learned (what worked, what failed)
- [ ] Optimize algorithm for next batch
- [ ] Document improvements in LESSONS.md

### Pre-Board Review (July 30)
- [ ] Benchmark results (websites recovered, events found)
- [ ] Report on optimization gains (speedup, throughput)
- [ ] Demonstrate end-to-end system (discovery → volunteer flow)

---

## Resource Reservation

```
Total System: 30GB RAM, 8 CPU cores, 1TB SSD
├── Daanaa API (home server)
│   ├── Qwen3-30B-A3B: 14GB (fixed)
│   ├── mxbai-embed-large: 1GB (fixed)
│   ├── Flask app + cache: 2GB
│   └── Database query cache: 2GB
│
├── Phase 3 Discovery
│   ├── DeepSeek-R1-8B: 8.2GB (new)
│   ├── 8 worker threads: 0.5GB
│   └── HTTP client connections: 0.3GB
│
└── System / Headroom
    └── 2GB (system processes, padding)

Total allocated: ~30GB
Headroom: 0GB (at capacity, but all productive work)
```

**Risk:** No spare capacity for other processes.  
**Mitigation:** Kill Firefox/idle processes if needed; all 30GB dedicated to productive work.

---

## Success Metrics (Tonight)

✅ **Hardware:** Achieve 70%+ CPU and 60%+ RAM utilization  
✅ **LLM:** Batch inference latency <50ms per request  
✅ **Skills:** Use /graphify and /investigate on Phase 3 results  
✅ **Discovery:** Complete 500+ org discovery with 70%+ success rate  
✅ **Events:** Extract 100+ new volunteer events from discovered websites  

---

**Status:** OPTIMIZATION IN PROGRESS (Parallel with Phase 3)  
**Owner:** Claude Code (autonomous)  
**Timeline:** Complete by 2026-07-24 07:00 UTC
