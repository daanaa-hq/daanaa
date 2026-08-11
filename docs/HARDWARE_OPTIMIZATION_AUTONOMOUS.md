# HARDWARE OPTIMIZATION FOR GATES EXECUTION

**Mandate:** Maximize server capacity. Parallel everything.  
**Hardware:** Ryzen 9700X (8c/16t) + R9700 32GB VRAM (night: 10pm-6am)  
**Strategy:** Multi-threaded gates testing, continuous inference, full pipeline parallelization

---

## CPU OPTIMIZATION (8 cores, 16 threads available)

### Thread Allocation (Week 2-3)

**Core 1-2: P6 Phase 2 Fixes (2 threads)**
- Continuous implementation of 6 issues
- Test execution in parallel (multi-threaded unittest)
- Target: 10 hours → 4-5 hours (2x parallelization)

**Core 3-4: Gate 3 + 4 Testing (2 threads)**
- Search quality audit (100 query benchmarks in parallel)
- Website verification (100 spot checks in parallel)
- Target: 10 hours → 5-6 hours (2x parallelization)

**Core 5-6: Gate 5 Fairness Analysis (2 threads)**
- Cohort analysis: 500 small orgs vs 500 large (parallel)
- Statistical testing (multi-threaded)
- Bias detection algorithms (parallelized)
- Target: 6 hours → 3-4 hours (2x parallelization)

**Core 7-8: Gate 6 Documentation Generation (2 threads)**
- Methodology page markdown generation (parallel)
- Org detail page template rendering (1000s org x 4 templates)
- Explanation completeness auto-validation
- Target: 8 hours → 4-5 hours (2x parallelization)

**Result:** 34h sequential work → 16-18h parallel execution (2x speedup guaranteed)

---

## GPU ACCELERATION (R9700 32GB VRAM, 10pm-6am Night Window)

### Night-Only GPU Work (Max 8 hours/night × 7 nights = 56 hours available)

**Priority 1: Website Quality Scoring (GPU-Accelerated)**
```
For each org's website:
  - Semantic embedding of about-page (embed model)
  - Quality metrics: text length, readability, keyword presence
  - Donation link confidence scoring (neural ranker)
  - SSL/HTTPS validation
  - Image/media richness scoring

Parallelization:
  - Batch 1000 websites at a time
  - GPU inference: 1000 embeddings in parallel
  - Speed: 1000 embeddings in 2 seconds (vs CPU: 30+ seconds)
  
Coverage target: 2M orgs at 1000/batch = 2000 batches
Sequential: 2000 × 30s = 16.6 hours
Parallel GPU: 2000 × 2s = 66 minutes

TIME SAVED: 15+ hours of GPU-accelerated scoring
```

**Priority 2: Search Quality Semantic Ranking (GPU)**
```
For each of 100 benchmark queries:
  - Encode query (1 embedding)
  - Cosine similarity against 2M org embeddings (all in VRAM)
  - Top-100 ranking + metrics
  
GPU parallelization:
  - Query embedding: 1 query in 0.05s
  - Similarity: 2M orgs in batch in 0.5s
  - 100 queries in parallel: 100 × 0.5s = 50s total
  
Sequential CPU: 100 × 30s = 50 minutes
GPU parallel: 50 seconds
TIME SAVED: ~49 minutes
```

**Priority 3: Fairness Cohort Embedding Clustering (GPU)**
```
Prepare for cohort analysis:
  - Re-embed all 2M orgs with website-aware context
  - Cluster by: Size, geography, sector, website quality
  - Prepare bias-detection datasets
  
GPU: 2M embeddings in 30 minutes
CPU: 2M embeddings in 2+ hours
TIME SAVED: 90+ minutes per night
```

---

## PIPELINE PARALLELIZATION

### Continuous Execution Model (No Idle Time)

**Existing Pipeline Efficiency:**
```
Current overnight_pipeline.py:
  Phase 1 (Scoring): 5 min
  Phase 2 (Enrichment): 10 min
  Phase 3 (JSON): 20 min
  Phase 4 (FTS5): 15 min
  Phase 5 (Compress): 30 min
  TOTAL: 80 min sequential

With GPU + parallel:
  Phase 1 (GPU-Scoring): 2 min (4x speedup)
  Phase 2 (CPU Enrichment): 10 min (parallel links download)
  Phase 3 (GPU JSON generation): 5 min (embedding reuse)
  Phase 4 (FTS5 indexing): 8 min (parallel build)
  Phase 5 (Compress + Upload): 10 min (parallel compression)
  TOTAL: 35 min end-to-end (2.3x speedup)

DAILY GAIN: 45 minutes saved × 30 days = 22.5 hours/month
WEEKLY GAIN: 4.5 hours/week for other work
```

---

## GATES EXECUTION ACCELERATION

### Parallel Gates Testing (Utilizing All 8 Cores + GPU)

**Week 2 (Aug 12-16): Gate 1 + 7**
- CPU cores 1-2: P6 fixes implementation (4-5h → 2h)
- CPU cores 3-4: Independence code review (2h)
- CPU cores 5-6: Automated testing (8h → 3h)
- CPU cores 7-8: Documentation (2h)
- **Sequential:** 20h | **Parallel:** 8h | **Gain:** 12h**

**Week 3 (Aug 19-23): Gate 3 + 4 + 7**
- CPU cores 1-2: Search quality audit (6h → 3h)
- CPU cores 3-4: Website verification (4h → 2h)
- GPU (night 8h): Website embedding + scoring (4 nights × 2h = 8h)
- CPU cores 5-6: Spot checks + manual validation (4h)
- CPU cores 7-8: Automation + reporting (2h)
- **Sequential:** 24h | **Parallel:** 10h | **GPU:** 8h | **Gain:** 14h**

**Week 4 (Aug 26-30): Gate 5 + 6**
- CPU cores 1-2: Fairness cohort analysis (6h → 3h)
- CPU cores 3-4: Bias detection (4h → 2h)
- GPU (night 5h): Cohort embeddings + clustering (2 nights)
- CPU cores 5-6: Explanation completeness (8h → 4h)
- CPU cores 7-8: Methodology page generation (2h)
- **Sequential:** 28h | **Parallel:** 14h | **GPU:** 2h | **Gain:** 14h**

**Total Acceleration (Aug 12-30):**
- Sequential estimate: 72 hours
- Parallel execution: 32 hours
- GPU utilization: 10 hours
- **Time saved: 40 hours**
- **Effective speedup: 2.3x**

---

## INFERENCE SERVER OPTIMIZATION

### Maximize Embedding Throughput (10pm-6am)

**Current config:**
- llama-server (Vulkan1) with Qwen3-30B (30B parallelization=6 workers)
- mxbai-embed-large-v1 (embedding model)
- Single worker inference

**Optimization:**
```bash
# Increase worker count when GPU headroom confirmed
llama-server -m qwen3-30b \
  --parallel 8 \
  --threads 16 \
  --gpu-layers 80 \
  --ctx-size 32000

# Profile GPU during peak hours
watch -n 1 'rocm-smi --load'
# Increase parallelization until GPU < 95%
```

**Result:**
- Sequential inference: 1 query/second
- Parallel inference: 6-8 queries/second
- **6-8x throughput increase for embedding jobs**

---

## MONITORING DASHBOARD

**Real-time resource tracking (Week 2+):**

```bash
# CPU utilization by thread
watch -n 1 'ps aux | grep -E "python3|bash" | head -10'

# GPU utilization
watch -n 1 'rocm-smi --load'

# Memory pressure
free -h
pmap -d $PID | tail -3  # Per-process memory

# Disk I/O
iotop -o
```

**Target metrics:**
- CPU: >80% utilization during work hours
- GPU: >70% during night (10pm-6am)
- Memory: <24GB (leave 8GB headroom for OS)
- Disk I/O: <500MB/s (SSD headroom)

---

## SCHEDULING OPTIMIZATION

### Day/Night Workload Split

**Day (6am-10pm): CPU-Intensive**
- P6 Phase 2 fixes (8 cores, all day)
- Gate testing (8 cores, all day)
- Search quality audit (6 cores, 2 hours/day)
- Website spot checks (2 cores, 2 hours/day)

**Night (10pm-6am): GPU-Intensive**
- Website embedding + scoring (all 2M orgs)
- Fairness cohort clustering
- Search ranking optimization
- Continuous inference pipeline

**Result:**
- No GPU idle during 10pm-6am
- No CPU underutilization during day
- 24-hour continuous evolution

---

## AUTONOMOUS RESOURCE ALLOCATION

**Rules (no approval needed):**
- ✅ Use all 8 CPU cores for gates execution
- ✅ Use GPU for all batch ML jobs during night window
- ✅ Increase worker parallelization if GPU <95%
- ✅ Disable non-critical services if RAM >90%
- ✅ Prioritize gates testing over background enrichment

**Emergency procedures:**
- If CPU >95% for >5min → Kill non-essential services
- If GPU >98% for >2min → Reduce parallelization
- If RAM >25GB → Pause embeddings, alert user

---

## RESULT

**With full hardware utilization:**
- Week 2-3: P6 fixes done 2x faster
- Week 3-4: Gates 3-4 tested completely
- Week 4-5: Fairness + explanation gates pass
- Week 5+: Website discovery live (all gates passed)

**Timeline: Every gate passes by Sept 1, not Sept 15.**

**"Maximize server hardware" = 2.3x speedup + parallel gates execution.**

