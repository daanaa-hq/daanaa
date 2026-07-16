# GPU Architecture — Discovery Pipeline

## Rule: Never Block the Daemon

The discovery daemon must stay responsive. GPU enhancement runs **separate from** and **async to** the main loop.

---

## Architecture

### Phase 1: CPU-Based Discovery (Responsive)
**discovery_daemon.py**
- HTTP fetching + HTML parsing (CPU-optimized workers: 30 concurrent, 8 parse workers)
- Link verification (CPU: URL patterns, HTTP status checks, timeout=10s)
- Database writes (CPU-bound SQLite)
- **No GPU calls** in the main loop

**Why:** Discovery runs 24/7. GPU latency or timeout would stall the daemon and freeze the system.

---

### GPU Enhancement Layer (Optional, Non-Blocking)
**gpu_link_verifier.py**
- Semantic embeddings (mxbai-embed-large on port 11436)
- Batch confidence scoring (optional post-processing)
- **Short timeout:** 2 seconds (fail-fast if GPU is busy)
- **Async calls only** — never block discovery

**When to use:**
- Link refinement (after discovery, not during)
- Confidence boosting for borderline cases
- Scheduled batch re-scoring (off-peak)

**Never use:**
- In the main discovery loop
- For blocking verification
- If it increases tail latency

---

## Current GPU Usage

**Inference servers (always on):**
- Port 11436: mxbai-embed-large embeddings (Vulkan, -ngl 99)
- Port 11437: Qwen2.5-32B missions (Vulkan, -ngl 99)

**VRAM: 76% allocated, 0% utilized during discovery**
- Ready for async scoring tasks
- Never becomes a bottleneck

---

## Safe GPU Integration

If using `gpu_link_verifier.py`:

```python
# ❌ DON'T: Block on GPU in daemon loop
for org in orgs:
    gpu_verified = verifier.embed_batch(...)  # HANGS if GPU is busy

# ✅ DO: Async scoring, separate from discovery
# Daemon completes discovery, then:
# 1. Queue links for async GPU scoring (background job)
# 2. Or skip GPU entirely if CPU verification is sufficient
```

---

## Decision: CPU-First for Phase 1

**Keep Phase 1 CPU-only.** GPU is available for Phase 2+ enhancements:
- Phase 2 (CN scraper): Optional GPU confidence boosting
- Phase 3 (gap-filling): GPU semantic search for candidates
- Post-phase: Batch re-scoring with full GPU utilization

This protects the main discovery loop from GPU latency/hangs.
