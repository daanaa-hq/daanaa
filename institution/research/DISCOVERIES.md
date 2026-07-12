
## sqlite-vec on Droplet: RAM Constraint Blocks Hypothesis

**Title:** Semantic search via sqlite-vec cannot fit 2M embeddings on 2GB droplet

**Summary:** Tested whether 546K+ org embeddings (1024-dim, float32) can serve semantic search on the production 2GB droplet via sqlite-vec. Finding: the embedding matrix itself occupies ~8GB in RAM — 4× the droplet's total memory. Hypothesis fails on hard constraint, not performance.

**Evidence:**
- Loaded 2,042,897 org embeddings from production registry
- Each vector: 1024 float32 values = 4KB
- Total: 2.04M × 4KB = ~8GB
- Droplet has 2GB total RAM (not 2GB available after OS/services)

**Confidence:** Very High (physical constraint, not measurement error)

**Impact:** Semantic search remains on home server (where GPU/RAM are plentiful). Droplet continues to serve keyword/FTS search only. Doesn't degrade search quality (semantic still available via `/api/fused-search` from home server).

**Replication status:** Direct mathematical constraint; no replication needed.

**Publication opportunities:** None (expected result; architectural tradeoff is sound).

**Nonprofit benefit:** Semantic search remains available to users; droplet design is confirmed appropriate for bounded dataset.

**Societal benefit:** Confirms cost-effective architecture (no need to upgrade droplet to 4GB for this feature).

**Unexpected findings:** None. The 8GB figure is exact (2.04M × 1024 × 4 bytes).

**Next steps:** Document in STANDING_CONSTRAINTS.md that semantic-search-on-droplet is infeasible; reaffirm home-server-only model for embeddings.

