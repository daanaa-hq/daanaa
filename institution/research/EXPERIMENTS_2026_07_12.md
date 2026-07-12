# Institutional Science Experiments — T7 & T8

**Authority:** EXECUTION_HANDOFF_2026_07_12.md, Research Directive 2026-07-12  
**Hypothesis-driven:** Each experiment pre-commits decision rule before running.  
**Logging:** Every result (positive or negative) goes to DISCOVERIES.md + LESSONS.md

---

## T7: sqlite-vec on Droplet (Semantic Search at 2GB)

**Hypothesis:** 546K × 1024-dimensional org embeddings can run semantic search on the 2GB droplet via sqlite-vec, eliminating the 2.2GB in-RAM matrix that caused INC-003.

**Pre-committed decision rule:**
- **Decision trigger:** Both (a) AND (b) must pass:
  - (a) Query p95 latency < 150ms over 100 representative queries (seed: top-searched orgs)
  - (b) Recall@10 > 0.95 vs. exact numpy cosine similarity (ground truth on home server)
- **If both pass:** Propose shipping semantic search to the droplet; log as success + next steps
- **If either fails:** Log negative result + why; keep semantic search on home server; file hypothesis invalidation in DISCOVERIES.md

**Protocol (home server, GPU-heavy):**
1. Build sqlite-vec DB from existing `org_embeddings` table (546K rows)
2. Create test set: 100 random orgs + their top 10 neighbors (via numpy cosine, home server baseline)
3. Run same 100 queries against sqlite-vec; measure:
   - File size (target: <2GB)
   - Query latency p50/p95 (target: <150ms p95)
   - Recall@10 (target: >0.95)
4. Log results in DISCOVERIES.md regardless of outcome

**Why this matters:** If it passes, the droplet gains semantic search at zero cost (no more embedding matrix). If it fails, we document why and keep the status quo (still better than Postgres).

---

## T8: Litestream Continuous Replication (Backup to R2)

**Hypothesis:** Litestream can continuously replicate critical database tables to Cloudflare R2 free tier (10GB, zero egress), upgrading backup posture from nightly to real-time at zero cost.

**Pre-committed decision rule:**
- **Decision trigger:** All three (a) AND (b) AND (c) must pass:
  - (a) Replica lag < 60 seconds (commits hit R2 within 1 minute)
  - (b) R2 usage < 5GB after 48h of continuous replication (two pipeline cycles)
  - (c) Restore correctness: `litestream restore` from R2 produces byte-for-byte identical database
- **If all pass:** Adopt Litestream alongside (not replacing) Google Drive; log as success
- **If any fails:** Log negative result; keep Google Drive-only; document constraints in LESSONS.md

**Protocol (home server, test environment):**
1. Install Litestream binary (single static file, ~20MB)
2. Create test DB: replica of critical tables only (org_claims, org_enrichment, score_snapshots) — skip the full merit_registry.db (9.6GB)
3. Run nightly pipeline twice (48h of data churn) with Litestream replicating to R2
4. Measure: replica lag, R2 space used, restore time
5. Test restore: pull DB from R2, verify row counts & checksums match live DB
6. Log results in DISCOVERIES.md

**Why this matters:** If it passes, we get continuous backup for free. If it fails, we know the constraint and document it (e.g., "replication lag >5 min" or "R2 usage grows to 8GB").

---

## Logging both results

Regardless of outcome, each experiment produces:
1. **DISCOVERIES.md entry** — 11-component record: title, summary, evidence, confidence, impact, replication status, publication opportunities, nonprofit benefit, societal benefit, unexpected findings
2. **LESSONS.md entry** — if something surprising happened (negative result, unexpected performance, blocker found)
3. **REGISTRY.md update** — mark hypothesis as "completed" with date and outcome link

**Execution order:** T7 first (emoji-based feedback is faster), then T8 (runs in parallel as needed).
