# Server Hardware Optimization Strategy

**Hardware Available:**
- Ryzen 9700X (16-core CPU)
- R9700 GPU (32GB VRAM, ROCm 6.4)
- Night window: 10pm–6am (8h for heavy compute)
- Day window: 6am–10pm (local inference only, light models)

**Goal:** Reduce Codex calls by 40-60% by offloading to local compute.

---

## Tier 1: Local Code Analysis (Replaces ~30% of Codex Reviews)

### What It Does
Runs static analysis, linting, and pattern matching locally **before** escalating to Codex.

### Where It Runs
**Droplet + Local Dev Machine**

### Models/Tools Needed
- **Tree-sitter AST analysis** (0-latency, zero tokens) — parse code structure locally
- **Rust analyzer** (fast, local) — type checking, refactoring hints
- **Semgrep** (open-source) — security pattern matching
- **ESLint + TypeScript compiler** (native) — linting/type checks

### Example: Security Review Before Codex
```bash
# Step 1: Run local security scan (10 seconds, 0 tokens)
semgrep scan --config p/security-audit frontend/src/

# Step 2: If issues found → Codex for mitigation strategy only (3,000 tokens)
# If clean → Skip Codex entirely (save 5,000+ tokens)

# Step 3: If Codex needed, feed it only the problem lines:
codex task "Semgrep found XSS vulnerability at lines 45-67 in TrustBadge.tsx.
Suggest fix." (vs. "Review entire component")
```

**Token Savings:** 5,000-8,000 tokens per review  
**Effort:** S (tools already exist, just orchestrate)

---

## Tier 2: Vector Embeddings + Local Semantic Search (Replaces ~20% of Context7 Calls)

### What It Does
Server-side vector DB for semantic search within org/scoring/API documentation. Eliminates need to query Context7 for every architectural question.

### Where It Runs
**Droplet (night window) + cached on dev machine**

### Hardware Used
- **GPU:** mxbai-embed-large (already in llama-server on port 11436)
- **Storage:** `org_embeddings` SQLite table (already exist)
- **CPU:** Ryzen 9700X for FAISS indexing

### Implementation
```python
# During night window (10pm-6am), precompute embeddings for all docs
python scripts/build_doc_embeddings.py \
  --source "docs/ CLAUDE.md STEWARDSHIP.md DECISIONS.md" \
  --model mxbai-embed-large \
  --output data/doc_embeddings.faiss

# On query, use FAISS + vector search (local, instant)
from faiss import IndexFlatL2
index = IndexFlatL2(1024)  # Pre-loaded at startup
query_embedding = get_embedding("How does V6 scoring work?")
similar_docs = index.search(query_embedding, k=3)  # 50ms, 0 tokens
```

**Result:**
- Context7 call (3,000 tokens): "How does V6 scoring work?"
- **Becomes:** Local FAISS search (0 tokens): Returns top 3 matching docs in 50ms

**Token Savings:** 3,000 tokens per query  
**Effort:** M (FAISS + embedding precompute pipeline)

---

## Tier 3: Local Code Generation + Review (Replaces ~15% of Codex Writes)

### What It Does
Run smaller, fast models locally for routine code changes. Escalate to Codex only for complex logic.

### Models to Deploy (Night Window)
```
# Already running:
- Qwen3-30B-Instruct (port 11437) — mission generation, moderate complexity

# Add for code generation:
- Qwen2.5-7B-Instruct (~3GB VRAM) — simple fixes, boilerplate, tests
- DeepSeek-Coder-6.7B (~5GB VRAM) — backend fixes, API routes

# Keep on standby:
- Mistral-7B (~4GB VRAM) — fallback for Qwen if needed
```

### Example: Test Generation Before Codex
```bash
# User: "Add tests for the new emailFilter function"

# Local flow:
1. Run Qwen2.5-7B locally (60 seconds)
   "Generate Playwright tests for emailFilter function"
   Output: tests/email-filter.spec.ts

2. Run ESLint + TypeScript on generated code (5 seconds)
   ✅ Passes? → Commit
   ❌ Fails? → Feed output to Codex with "Fix these TS errors"

# Token usage:
- Without optimization: Codex writes tests from scratch (8,000 tokens)
- With optimization: Codex fixes 3 TS errors (1,500 tokens)
- Savings: 6,500 tokens + 60 second Qwen latency vs. ~30s Codex latency
```

**Token Savings:** 5,000-8,000 tokens per generation  
**Effort:** M (add Qwen2.5-7B + DeepSeek-6.7B to night startup)

---

## Tier 4: Async Codex Task Batching (Runs ~20% faster, same tokens)

### What It Does
Queue Codex reviews overnight, don't block on response.

### Architecture
```
Developer: npm run build → commits to branch
    ↓
Ralph orchestration (async):
  ├─ Local: Run linting, tests, security scan (5 seconds)
  ├─ Async queue: Codex architectural review (return immediately)
  ├─ Dev continues working (not blocked)
  └─ Next morning: Review results in .codex-reviews/latest/

Developer next morning:
  └─ Check results: git log .codex-reviews/
     ├─ ✅ All pass
     ├─ ⚠️ 2 findings → fix
     └─ 🔴 Blocker → escalate
```

### Server-Side Daemon
```bash
# daemon: codex_batch_processor.py
# Runs during work hours, but processes reviews async

while True:
  queued = redis.lpop('codex_review_queue')  # Get queued Codex task
  if queued:
    result = run_codex_review(queued)
    save_to_reviews_cache(result)
    notify_slack(result)  # Alert dev if issues found
  sleep(60)
```

**Benefit:** Reviews happen in background; dev doesn't wait  
**Effort:** S (queue + daemon wrapper)

---

## Tier 5: Precomputed Architecture Snapshots (Replaces ~10% of Reviews)

### What It Does
Nightly digest of codebase state: "What changed? What are the risks?"

### Runs Nightly (11pm)
```bash
# snapshot_generator.py runs during night window

1. Analyze all commits since last snapshot
2. Run Qwen3-30B: "Summarize these changes and flag risks"
3. Cache result in .architecture-snapshots/YYYY-MM-DD.md
4. Email digest to team

# Result: When Codex is asked "What changed?", just query cache
context7 daanaa "What major changes in past 7 days?"
→ Returns pre-generated snapshot (0 tokens) instead of Codex review (5,000 tokens)
```

**Example Snapshot Output:**
```markdown
## Architecture Snapshot 2026-08-11

### Changes This Week
- Context7 integration (docs indexing)
- Ralph orchestration (workflow automation)
- Playwright QC tests (quality gates)

### Risk Assessment
- ✅ No security changes
- ✅ No schema changes
- ⚠️ New external dependency (Context7) — review impact
- 🔴 None

### Recommendations
1. Update DECISIONS.md with Context7 ROI
2. Monitor Codex batch queue performance
3. Schedule v6 scoring v7 planning

### Token Savings This Period
- Context7 integration saved ~40% on Codex reviews
- Local analysis saves ~30% on security reviews
- Total: 45,000 tokens saved
```

**Token Savings:** 3,000-5,000 tokens per snapshot query  
**Effort:** M (snapshot generator + email integration)

---

## Tier 6: Local Privacy-Compliance Checker (Replaces ~5% of Security Reviews)

### What It Does
**Before** sending code to Codex, run local privacy gate to catch obvious issues.

### Runs Locally (0 tokens)
```bash
# privacy_pre_check.sh runs before every commit

1. Check for env var fallbacks
   grep -r "process.env\|os.getenv" --include="*.ts" --include="*.py"
   → Flag: "Don't log process.env, use config"

2. Check for data exposure patterns
   grep -r "console.log\|print(" --include="*.ts" --include="*.py"
   → Flag: "No logging user/org data"

3. Check for tracking scripts
   grep -r "google.analytics\|facebook\|amplitude" frontend/
   → Flag: "Non-Plausible analytics detected"

4. Check for external API calls
   grep -r "fetch\|requests\|axios" src/ | grep -E "api\." | grep -v "localhost"
   → Flag: "Verify this external call is in PRIVACY-INVARIANTS"

# Result: 99% of privacy issues caught locally (0 tokens)
# Only edge cases escalate to Codex
```

**Token Savings:** 2,000-3,000 tokens per privacy review  
**Effort:** S (grep + bash orchestration)

---

## Execution Timeline: Staged Rollout

### Week 1 (Immediate, Low Effort)
- [x] Codex token optimization guide (already done)
- [ ] Local linting + security pre-checks (Semgrep + ESLint)
- [ ] Privacy pre-check bash script
- **Impact:** 15,000 tokens/week saved (~25% reduction)

### Week 2 (Medium Effort)
- [ ] Build doc embeddings pipeline (FAISS indexing nightly)
- [ ] Deploy Qwen2.5-7B + DeepSeek-6.7B models
- [ ] Set up vector search wrapper
- **Impact:** 20,000 tokens/week saved (~35% reduction)

### Week 3 (Integration Week)
- [ ] Integrate local code generation into Ralph workflow
- [ ] Set up Codex batch queue daemon
- [ ] Build architecture snapshot generator
- **Impact:** 30,000 tokens/week saved (~50% reduction)

### Week 4+ (Optimization & Tuning)
- [ ] Monitor token savings; adjust model allocation
- [ ] Add more vector-searchable doc sources
- [ ] Fine-tune prompt templates based on local analysis output
- **Target:** 60% total token reduction (stable state)

---

## GPU Utilization Plan

### Night Window (10pm–6am, 8 hours)
```
├─ Embedding generation (4h)
│  ├─ Doc embeddings (docs/ + CLAUDE.md + architecture)
│  ├─ Code embeddings (key API files)
│  └─ Org metadata embeddings (for ranking)
├─ Model warm-up (30m)
│  ├─ Load Qwen3-30B
│  ├─ Load Qwen2.5-7B
│  └─ Load DeepSeek-6.7B
├─ Batch processing (3h)
│  ├─ Async Codex reviews (high-effort only)
│  ├─ Mission generation (nightly)
│  └─ Architecture snapshots
└─ Maintenance (30m)
   ├─ FAISS index rebuild
   ├─ Embed cache cleanup
   └─ Results notification

Peak GPU load: ~28GB/32GB (sustainable)
```

### Day Window (6am–10pm, 16 hours)
```
├─ mxbai-embed-large (port 11436) — Query embeddings only (lightweight)
├─ Qwen3-30B (port 11437) — Light requests only (if not in night cycle)
└─ All other models: OFF (save heat, power)
```

---

## Expected ROI (Monthly)

| Optimization | Cost | Token Savings | Net Value |
|---|---|---|---|
| Codex prompt optimization | 0 effort-hours | 40,000 tokens | $$$ |
| Local pre-checks (semgrep, linting) | 2 hours | 60,000 tokens | $$$$ |
| Doc embeddings + vector search | 8 hours | 120,000 tokens | $$$$$ |
| Local code generation (Qwen2.5) | 12 hours | 180,000 tokens | $$$$$$ |
| Codex batch queue + snapshots | 6 hours | 90,000 tokens | $$$$$ |
| **Total** | **28 hours** | **490,000 tokens** | **~$12-18 in token cost** |

**Effort ROI:** 28 hours dev time = 490,000 tokens saved = ~1,400 tokens/hour  
**Cost ROI:** ~$12-18/month in Codex costs eliminated

---

## Implementation Resources

### Scripts to Create
- `scripts/local_security_check.sh` — Semgrep + pattern matching
- `scripts/build_doc_embeddings.py` — FAISS indexing nightly
- `scripts/code_embeddings_search.py` — Vector search wrapper
- `scripts/codex_batch_daemon.py` — Async queue processor
- `scripts/architecture_snapshot.py` — Nightly digest generator
- `scripts/privacy_pre_check.sh` — Local compliance checker

### Integrations to Build
- Ralph orchestration layer (trigger local pre-checks before Codex)
- `.codex-reviews/` cache + FAISS index coordination
- Slack notifications (review results summary)
- Morning digest email (snapshot + findings)

### Models to Deploy
- **Keep running:** Qwen3-30B, mxbai-embed-large
- **Add (night window):** Qwen2.5-7B, DeepSeek-6.7B (~8GB additional VRAM)
- **Fallback:** Mistral-7B (if needed for variety)

---

## Validation Metrics

Track these to verify optimization ROI:

```bash
# codex_metrics.sh (runs weekly)

1. Token usage trend
   git log --oneline DECISIONS.md | grep "Codex" | wc -l
   → Target: <4 Codex reviews/week (vs. 8 before)

2. Pre-check catch rate
   grep "privacy\|security\|lint" LESSONS.md | wc -l
   → Target: >80% of issues caught locally

3. Local model generation success rate
   ls .test-generations/ | grep "✅" | wc -l
   → Target: >70% of generated code passes ESLint

4. Latency improvement
   grep "latency" .architecture-snapshots/*.md | tail -1
   → Target: Dev waits <2 min for full review (vs. 10 min for Codex)

5. Cost savings
   git log DECISIONS.md | grep "tokens saved" | sum
   → Target: 400,000+ tokens/month
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Local models hallucinate | Always verify with ESLint/TypeScript before commit |
| Embeddings become stale | Rebuild nightly (automated) |
| GPU overheats at night | Monitor radeontop; cap compute if >85°C |
| Batch queue backs up | Monitor daemon; alert if queue >10 items |

---

## References

- **FAISS (Facebook AI Similarity Search):** https://github.com/facebookresearch/faiss
- **Qwen2.5-7B:** Hugging Face model (local via llama.cpp)
- **Semgrep:** https://semgrep.dev/
- **mxbai-embed-large:** Already running on port 11436
- **Codex batch API:** https://platform.openai.com/docs/guides/batch-processing

---

**Bottom Line:** With 28 hours of setup, save 490,000 tokens/month and cut review latency from 10 min to 2 min. Pure win.
