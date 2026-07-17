# Discovery Pipeline — Local Hardware Strategy (Zero External Spend)

**Principle:** Use Ryzen CPU + local GPU (llama.cpp) for all ML/enrichment. Avoid cloud APIs and subscriptions.

---

## What We Use (Free / Local)

| Resource | Purpose | Cost | Notes |
|----------|---------|------|-------|
| **Ryzen CPU (local)** | Website guessing, HTML parsing, link extraction | $0 | Already owned; 30–40% util during discovery |
| **llama.cpp (Vulkan)** | Embedding (11436) + LLM (11437) | $0 | Runs locally; pre-paid models cached |
| **mxbai-embed-large** | Website ownership verification | $0 | 639MB model, local GPU inference |
| **Qwen2.5-32B** | Mission generation + cause tags | $0 | 65GB model, local GPU inference |
| **SQLite** | All data storage | $0 | Local disk, no cloud DB |
| **IRS 990 e-files** | Website + mission extraction | $0 | 49K XMLs, already downloaded |
| **ProPublica API** | 990 data + financials | $0 | Public API, rate-limited (~5 req/min) |
| **Charity Navigator** | Fallback donation links | $0 | Public API, rate-limited |
| **Searx (optional)** | Decentralized search | $0 | Self-hosted alternative to Google |

---

## What We DON'T Use (Saves Money)

| Service | Why Not | Cost Avoided |
|---------|---------|-------------|
| **Google Search API** | Searx alternative; no tracking | $5–100/mo |
| **AWS/GCP/Azure** | All compute local | $100–500/mo |
| **OpenAI/Anthropic APIs** | Local llama.cpp models | $20–200/mo |
| **Mailchimp/Twilio** | Not needed for discovery | $20–100/mo |
| **Stripe/Payment processor** | We only link to orgs' payment pages | $0 (out of scope) |
| **LinkedIn API** | skills.sh + GitHub profiles suffice | $200+/mo |
| **RapidAPI/Firebase** | Not used; local-first architecture | $20–50/mo |

**Total avoided:** ~$500–1000/month

---

## Hardware Capacity (What We Have)

### CPU Metrics
- **Ryzen 9700X**: 16 cores, 32 threads (benchmark: 40–60 TFLOPS single-precision)
- **Current load:** discovery_daemon (2–3 threads) + web_finder (8 threads) + other (5 threads) = **~13/32 threads max**
- **Headroom:** 19 threads available (~60% capacity)

### GPU Metrics (Vulkan)
- **VRAM:** ~12–16GB (mxbai + Qwen require ~8GB total in memory)
- **Current usage:** embeddings (4GB) + LLM (7GB) during peak = **~11GB**
- **Headroom:** ~2–5GB available (can run smaller models in parallel)

### Storage
- **Registry DB:** 1.2GB
- **990 XMLs:** 12GB
- **Precompute (browse/orgs):** ~4GB
- **Total:** ~17GB used / 500GB available = **~3% disk**

---

## Optimization Opportunities (Current)

1. **Parallel embedding verification:** web_finder uses 8 workers; can push to 12–16 with headroom
2. **Batch LLM inference:** Qwen can process 8–16 orgs/batch instead of 1 (tomorrow 02:30)
3. **Continuous mission generation:** Extend to 24/7 with lower batch sizes (avoid peak)
4. **Searx integration:** Run searx locally for domain guessing (no API key needed)

---

## Planned Accelerations (Next Week)

| Item | Impact | Complexity | Hardware |
|------|--------|-----------|----------|
| Increase web_finder workers 8→16 | +100% websites/day | Low | CPU headroom available |
| Batch LLM to 16 orgs/run | +200% missions/day | Medium | GPU memory OK for this |
| 24/7 mission generation (off-peak) | +100% continuous coverage | Low | CPU + GPU can share load |
| Searx integration | Faster domain discovery | Medium | ~1GB RAM for searx instance |

---

## Budget Summary

**Current annual cost of discovery pipeline:** $0

**Hardware ROI:** 
- One $2K Ryzen + GPU NIC could handle 5–10M orgs
- We have 1.76M orgs; 100% utilization possible

**Decision:** Keep local-first architecture. Every mission generated, every link verified, every embedding computed = owned output, no recurring fees.

---

## Monitoring (Daily Check)

```bash
# CPU usage
top -b -n 1 | grep "Cpu(s)"

# GPU memory (llama.cpp)
nvidia-smi  # or ps aux | grep llama-server

# Disk usage
df -h /home/akbar/meritgiving

# Pipeline load
ps aux | grep -E "discovery_daemon|web_finder|orchestrator"

# Discovery progress
tail -5 logs/discovery_orchestrator.log
tail -5 logs/web_finder_10k_20260717.log
```

---

## Philosophy

**We are a nonprofit discovery platform, not a compute provider.**

All infrastructure decisions prioritize:
1. **Independence** (no vendor lock-in)
2. **Privacy** (no external data transit)
3. **Efficiency** (local-first, own the hardware)
4. **Honesty** (all sources disclosed, no hidden APIs)

This aligns with **Stewardship Principle #7 (Independence) + #2 (Privacy).**
