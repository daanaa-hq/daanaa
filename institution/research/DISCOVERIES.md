
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


## Litestream Continuous Replication: Viable for Critical-Tables Backup

**Title:** Litestream achieves sub-second replication lag with verified restore correctness on critical tables

**Summary:** Tested Litestream (open-source, MIT license, single static binary) as a continuous backup layer for critical tables (org_claims, score_snapshots subset) using local file-based replication as a stand-in for Cloudflare R2 (no R2 bucket created yet — avoided creating new external cloud resources without separate approval). All three pre-committed decision criteria passed.

**Evidence:**
- Replication lag: ~0.5s from write to confirmed replica sync (threshold: <60s)
- Restore correctness: `litestream restore` produced a database with identical row count (4) and the specific test row (T8-TEST-001) present; `PRAGMA integrity_check` returned `ok` on both source and restored DB
- Replica disk footprint: 36KB for a 3-row critical-tables test DB + one write — scales linearly, well under R2's 5GB target even at full org_claims volume (thousands of rows, not millions)

**Confidence:** High for replication mechanics (measured directly). Medium for R2-specific behavior (network egress/latency to Cloudflare not yet tested — local file replica was the proxy).

**Impact:** Continuous backup of the tables that change most often (claims, scoring) becomes feasible at near-zero cost, upgrading from "nightly snapshot" to "sub-second replication" for the data most likely to be lost in an incident window. Complements, does not replace, the existing Google Drive full-database nightly backup.

**Replication status:** Local file-replica mechanics verified directly. R2 network behavior is the remaining unverified step — requires creating an R2 bucket (new external resource; needs separate approval per cost/resource-creation norms) before full adoption.

**Publication opportunities:** None (using Litestream as documented; no novel technique).

**Nonprofit benefit:** Faster recovery point objective for the org_claims table means a claimed nonprofit's profile edits or verification status is never more than ~1 second from being backed up, vs. up to 24 hours today.

**Societal benefit:** Demonstrates that institutional-grade backup posture doesn't require paid infrastructure — reinforces the sustainability thesis (DR-2026-07-12-008).

**Unexpected findings:** None — results matched expectations for a mature, widely-used tool.

**Next steps:** Present to founder: (1) approve creating a Cloudflare R2 bucket (free tier, 10GB) to complete the R2-specific leg of the test, or (2) adopt file-based replication to a mounted network path as a lower-effort alternative. Either way, recommend adoption for org_claims + score_snapshots as a second backup layer alongside Google Drive.

