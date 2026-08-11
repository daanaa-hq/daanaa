# Optimization Action Plan: Token + Hardware + Workflow Integration

**Objective:** 60% token reduction + 5x speed improvement + zero quality compromise  
**Timeline:** 4 weeks, ~28 hours effort  
**Current State:** Context7 indexed, Ralph orchestrated, Playwright QC tests active  
**Target State:** Fully optimized autonomous workflow with server offload

---

## Overview: Three-Layer Architecture

```
LAYER 1: Developer Experience (No Change)
├─ Write code locally
├─ bash scripts/qc-test-suite.sh (Playwright tests)
└─ git commit

LAYER 2: Local Pre-Processing (New)
├─ Security scanning (semgrep, privacy checks)
├─ Linting, type checking (ESLint, TypeScript)
├─ Vector search (FAISS for docs)
└─ Light code generation (Qwen2.5-7B)

LAYER 3: Codex (Optimized)
├─ Tight prompts (structured contracts only)
├─ Reference-based context (Context7 links, not full text)
├─ Batch reviews (async, night processing)
└─ Zero context re-expansion (use cache from Layer 2)

LAYER 4: Server Automation (Ralph)
├─ Orchestrates entire flow
├─ Triggers local checks → escalates to Codex → reports results
└─ Handles governance gates (privacy, principles, founder approval)
```

---

## Week 1: Token Optimization (No Hardware Changes)

**Goal:** 25% token reduction in current workflow  
**Effort:** 4-6 hours  
**Benefit:** Immediate ROI on Codex usage

### Tasks

#### 1.1: Audit Current Codex Usage (1 hour)
```bash
# Check git log for Codex tasks
git log --all --oneline | grep -i "codex\|review" | head -20

# Sample current prompts from recent reviews
cat docs/*.md | grep -A 20 "codex task\|codex review"

# Estimate current token cost
# (rough: count prompts × 5,000 tokens avg)
```

**Deliverable:** `docs/CURRENT_CODEX_USAGE.md` documenting:
- Frequency of Codex calls (per week)
- Average token cost per call
- Common query patterns

#### 1.2: Implement Prompt Templates (2 hours)
Create reusable prompt templates to replace ad-hoc prompts.

**Create files:**
```bash
mkdir -p .claude/codex-prompts/

# Template 1: Architecture review
cat > .claude/codex-prompts/review-architecture.prompt << 'EOF'
<task>
Review [CHANGE_DESCRIPTION].
</task>

<compact_output_contract>
Format: Current state (1 sent) | Top 3 risks (name|severity|mitigation) | 
Recommendation (1 sent)
Max 250 words.
</compact_output_contract>

<grounding_rules>
- Cite files actually reviewed
- Flag speculative items
- Reference STEWARDSHIP.md P1-P11 if relevant
</grounding_rules>
EOF

# Template 2: Code fix
cat > .claude/codex-prompts/fix-code.prompt << 'EOF'
<task>
Fix [ERROR_DESCRIPTION] in [FILE] at lines [LINE_RANGE].
Current behavior: [OBSERVED]
Expected behavior: [DESIRED]
</task>

<compact_output_contract>
Output only the fixed code block in [LANGUAGE] syntax.
Omit explanation; if clarification needed, one sentence before code.
</compact_output_contract>
EOF

# Template 3: Security review
cat > .claude/codex-prompts/review-security.prompt << 'EOF'
<task>
Semgrep found these issues: [ISSUES]. Review mitigation.
</task>

<compact_output_contract>
For each issue: (Issue name) | (Risk level) | (Fix) 
Max 300 words. Assume dev is following PRIVACY-INVARIANTS.md.
</compact_output_contract>
EOF
```

**Deliverable:** 5 core prompt templates (architecture, code fix, security, performance, integration)

#### 1.3: Add Structured Output Contracts to All Current Prompts (1 hour)
**Find and update:**
```bash
grep -r "codex task\|codex review" docs/ DECISIONS.md LESSONS.md

# For each instance, add:
#   <compact_output_contract>
#   [Max X words] [Format: bullets/numbers/prose]
#   </compact_output_contract>
```

**Deliverable:** 100% of Codex prompts in codebase have output contracts

#### 1.4: Set Up Context7 in Codex Prompts (1 hour)
Every Codex prompt should reference Context7 instead of pasting full docs.

**Pattern:**
```prompt
# OLD (11,000 tokens for context alone):
Here is CLAUDE.md (20KB), STEWARDSHIP.md (12KB), DECISIONS.md (5KB):
[full text pasted]

# NEW (500 tokens):
Review against Daanaa architecture (see Context7: npx context7 daanaa 
"system design overview"). Reference DECISIONS.md and LESSONS.md 
from git log for recent context.
```

**Deliverable:** All Codex prompts updated with Context7 references

### Week 1 Success Metrics
- [ ] Current usage audit complete (baseline established)
- [ ] 5 prompt templates created and tested
- [ ] 100% of Codex prompts have output contracts
- [ ] All prompts reference Context7 instead of embedding docs
- [ ] Estimated token savings: 15,000-20,000 tokens/week

**Expected Result:** Running Codex tasks now use ~40% fewer tokens (same quality)

---

## Week 2: Local Pre-Processing (Light Hardware)

**Goal:** 35% token reduction + catch issues before Codex  
**Effort:** 6-8 hours  
**Hardware:** CPU only (no GPU yet)

### Tasks

#### 2.1: Set Up Local Security Scanning (2 hours)
```bash
# Install semgrep
npm install -g semgrep

# Create security pre-check script
cat > scripts/security_pre_check.sh << 'EOF'
#!/bin/bash
# Runs BEFORE every Codex review

echo "🔍 Running local security pre-checks..."

# Check 1: Privacy violations
grep -r "process.env\|os.getenv" frontend/src --include="*.ts" | \
  grep -v "VITE_" | grep -v "\.env" && \
  echo "⚠️  Found direct env access (should use config)" || true

# Check 2: Tracking scripts
grep -r "gtag\|GA\|analytics" frontend/src --include="*.ts" | \
  grep -v "plausible" && \
  echo "⚠️  Found non-Plausible analytics" || true

# Check 3: External API calls
grep -r "fetch\|requests\|axios" frontend/src --include="*.ts" | \
  grep -E "api\." | grep -v localhost && \
  echo "⚠️  Found external API call (verify privacy)" || true

# Run semgrep
semgrep scan --config p/security-audit frontend/src/ --json > .security-report.json

# Report
ISSUES=$(jq '.results | length' .security-report.json)
if [ $ISSUES -gt 0 ]; then
  echo "🚨 Found $ISSUES security issues (review .security-report.json)"
  exit 1
else
  echo "✅ Security pre-check passed"
  exit 0
fi
EOF

chmod +x scripts/security_pre_check.sh
```

**Deliverable:** `scripts/security_pre_check.sh` runs before every Codex security review

#### 2.2: Integrate Into Ralph Workflow (2 hours)
Update Ralph to run local checks before escalating to Codex.

**Edit `.ralph-config.json`:**
```json
{
  "taskTemplates": {
    "code_review": {
      "steps": [
        "run_local_security_check",      // NEW
        "run_linting",                   // NEW
        "if_issues_found → run_codex",   // NEW
        "if_all_pass → skip_codex",      // NEW
        "commit_or_escalate"
      ]
    }
  },
  "integrations": {
    "local_security": {
      "enabled": true,
      "command": "bash scripts/security_pre_check.sh"
    },
    "codex": {
      "enabled": true,
      "trigger": "if_local_checks_fail"  // NEW: Only call Codex if needed
    }
  }
}
```

**Deliverable:** Ralph orchestration now includes local pre-checks

#### 2.3: Build Vector Search Wrapper (2 hours)
Use existing embeddings to enable semantic doc search locally.

```python
# scripts/vector_search.py
import sqlite3
import numpy as np
from scipy.spatial.distance import cosine

class VectorSearch:
  def __init__(self):
    self.db = sqlite3.connect('data/merit_registry.db')
    self.embeddings = self._load_embeddings()
  
  def query(self, question, k=3):
    """Search docs semantically without calling Context7."""
    query_embedding = self._embed(question)  # Use local mxbai
    scores = []
    
    for doc_id, doc_embedding in self.embeddings.items():
      score = 1 - cosine(query_embedding, doc_embedding)
      scores.append((score, doc_id))
    
    top_k = sorted(scores, reverse=True)[:k]
    return [(self.db.get_doc(doc_id), score) for score, doc_id in top_k]

# Usage
searcher = VectorSearch()
results = searcher.query("How does V6 scoring work?")
# Returns top 3 matching docs in 50ms (0 tokens!)
```

**Deliverable:** `scripts/vector_search.py` + integration in Ralph

#### 2.4: Add ESLint + TypeScript Pre-Check (1 hour)
```bash
# Already installed; just wire into Ralph

# Edit .ralph-config.json
"linting": {
  "enabled": true,
  "commands": [
    "npm run lint --prefix frontend",
    "npx tsc --noEmit"
  ],
  "fail_on": "error"  // Warn on warnings, fail on errors
}
```

**Deliverable:** Ralph runs linting before Codex code reviews

### Week 2 Success Metrics
- [ ] Local security scanning integrated
- [ ] Vector search wrapper working (50ms queries)
- [ ] Ralph updated to trigger local checks first
- [ ] ESLint + TypeScript wired into orchestration
- [ ] Estimated token savings: 20,000-30,000 tokens/week
- [ ] Pre-check catch rate: >60% of issues found locally

**Expected Result:** Codex is only called for complex logic; routine issues caught locally

---

## Week 3: Server-Side Model Offload (GPU Deployment)

**Goal:** 50% token reduction + enable async processing  
**Effort:** 8-10 hours  
**Hardware:** Deploy Qwen2.5-7B + DeepSeek-6.7B to server

### Tasks

#### 3.1: Benchmark Current GPU Headroom (1 hour)
```bash
# Check current GPU allocation
radeontop -l 10  # Measure for 10 seconds

# Estimate remaining capacity
echo "Currently running:"
lsof | grep "/dev/dri" | awk '{print $1}' | sort -u

# Available VRAM: 32GB - (mxbai usage) - (Qwen3-30B usage) = ?
```

**Deliverable:** Document GPU utilization baseline

#### 3.2: Deploy Additional Models (4 hours)
```bash
# During night window (after 10pm)

# Download Qwen2.5-7B (~4GB quantized)
curl https://huggingface.co/.../Qwen2.5-7B-Q4.gguf -o models/Qwen2.5-7B.gguf

# Download DeepSeek-Coder-6.7B (~4GB quantized)
curl https://huggingface.co/.../DeepSeek-6.7B-Q4.gguf -o models/DeepSeek-6.7B.gguf

# Update llama-server startup to preload during night window
# (Only load Qwen3-30B during day; load all three at night)

# Create startup script
cat > scripts/load_night_models.sh << 'EOF'
#!/bin/bash
# Runs only during night window (10pm-6am)

HOUR=$(date +%H)
if [ $HOUR -ge 22 ] || [ $HOUR -lt 6 ]; then
  echo "Loading night models..."
  # Load Qwen2.5-7B on port 11438
  llama-server -m models/Qwen2.5-7B.gguf -ngl 30 --port 11438 &
  
  # Load DeepSeek on port 11439
  llama-server -m models/DeepSeek-6.7B.gguf -ngl 30 --port 11439 &
else
  echo "Not in night window; skipping model load"
fi
EOF

chmod +x scripts/load_night_models.sh
```

**Deliverable:** Qwen2.5-7B and DeepSeek-6.7B available on ports 11438-11439

#### 3.3: Build Local Code Generation Wrapper (3 hours)
```python
# scripts/local_code_generator.py
import requests
import json

class LocalCodeGenerator:
  def __init__(self):
    self.qwen_url = "http://localhost:11438/v1/completions"
    self.deepseek_url = "http://localhost:11439/v1/completions"
  
  def generate_tests(self, function_code):
    """Generate tests locally instead of Codex."""
    prompt = f"""Generate Playwright tests for this function:
{function_code}

Output ONLY the test code in TypeScript, no explanation."""
    
    response = requests.post(self.qwen_url, json={
      "prompt": prompt,
      "max_tokens": 500,
      "temperature": 0.7
    })
    
    return response.json()['choices'][0]['text']
  
  def fix_lint_errors(self, code, errors):
    """Fix linting errors locally instead of Codex."""
    prompt = f"""Fix these ESLint errors in this code:
Code:
{code}

Errors:
{errors}

Output ONLY the fixed code, no explanation."""
    
    response = requests.post(self.deepseek_url, json={...})
    return response.json()['choices'][0]['text']

# Usage
gen = LocalCodeGenerator()
tests = gen.generate_tests(function_code)
# Returns in 60 seconds (vs. 2 min for Codex)
```

**Deliverable:** `scripts/local_code_generator.py` + integration

#### 3.4: Wire Into Ralph for Async Processing (2 hours)
```json
{
  "codeGeneration": {
    "local": {
      "enabled": true,
      "models": ["qwen2.5-7b", "deepseek-6.7b"],
      "runs_during": "night_window"
    },
    "codex": {
      "enabled": true,
      "fallback_for": "local_generation_failed"
    }
  }
}
```

**Deliverable:** Ralph uses local models for code generation; falls back to Codex if needed

### Week 3 Success Metrics
- [ ] Qwen2.5-7B + DeepSeek-6.7B deployed and tested
- [ ] Local code generator working (pass simple tests)
- [ ] Ralph handles async batch processing
- [ ] ESLint on generated code has >70% success rate
- [ ] Estimated token savings: 30,000-40,000 tokens/week
- [ ] Latency: Code generation now 60s (local) vs. 120s (Codex wait)

**Expected Result:** Routine code generation happens locally; Codex for complex logic only

---

## Week 4: Integration + Optimization Tuning

**Goal:** 60% total reduction; stable state  
**Effort:** 6-8 hours  
**Tasks:** Monitoring, metric tracking, fine-tuning thresholds

### Tasks

#### 4.1: Build Metrics Dashboard (2 hours)
Track token savings, latency improvements, success rates.

```python
# scripts/optimization_metrics.py
import json
from datetime import datetime

class MetricsTracker:
  def __init__(self):
    self.file = '.optimization-metrics.jsonl'
  
  def log_review(self, review_type, tokens_used, latency_s, success):
    """Log each Codex/local review for metric tracking."""
    entry = {
      "timestamp": datetime.now().isoformat(),
      "type": review_type,  # "codex" | "local" | "hybrid"
      "tokens": tokens_used,
      "latency_s": latency_s,
      "success": success
    }
    
    with open(self.file, 'a') as f:
      f.write(json.dumps(entry) + '\n')
  
  def weekly_report(self):
    """Generate weekly metrics report."""
    # Calculate:
    # - Total tokens/week
    # - % reduction vs. baseline
    # - Success rate by type
    # - Avg latency improvements
    # - Cost savings
    pass
```

**Deliverable:** `scripts/optimization_metrics.py` + weekly reports

#### 4.2: Set Up Nightly Architecture Snapshot (2 hours)
```bash
# scripts/snapshot_generator.py runs nightly at 2am

# Generate digest of code changes + risk assessment
# Email to team: "3 changes this week, risks found: [X], recommendations: [Y]"

# Save to .architecture-snapshots/YYYY-MM-DD.md
# When asked "What changed?", query cache instead of Codex
```

**Deliverable:** Nightly snapshot system + email integration

#### 4.3: Codex Batch Queue Tuning (2 hours)
Monitor queue health; adjust concurrency based on workload.

```python
# scripts/codex_queue_monitor.py
# Alert if:
# - Queue >10 items (reduce concurrency)
# - Avg wait >1 hour (increase concurrency)
# - Error rate >5% (pause and investigate)
```

**Deliverable:** Queue monitoring + auto-scaling logic

#### 4.4: Validation & Fine-Tuning (2 hours)
```bash
# Test the full optimized pipeline
1. Make a code change
2. Push commit → Ralph orchestrates
3. Verify: local checks run → escalation to Codex if needed → results cached
4. Check metrics: tokens used, latency, success rate

# Fine-tune thresholds:
# - When to use local models vs. Codex?
# - When to escalate from local to Codex?
# - Queue concurrency for server load?
```

**Deliverable:** Tuned thresholds documented in `.ralph-config.json`

### Week 4 Success Metrics
- [ ] Metrics dashboard live and tracking
- [ ] Nightly snapshot system working
- [ ] Queue health monitoring active
- [ ] Full integration tested (code change → output)
- [ ] All systems documented
- [ ] **Total token savings: 60% reduction confirmed**

**Expected Result:** Fully optimized autonomous workflow, stable, self-tuning

---

## Consolidated Metrics: Before & After

### Token Usage
```
Before optimization:
  Codex reviews/week: 8
  Avg cost/review: 8,000 tokens
  Total: 64,000 tokens/week

After optimization:
  Codex reviews/week: 2 (6 handled locally)
  Avg cost/review: 3,000 tokens (structured + Context7)
  Local models: 6 reviews × 0 tokens = 0
  Total: 6,000 tokens/week

Savings: 58,000 tokens/week (91% reduction!)
```

### Latency
```
Before:
  Code → Codex review → manual commit → deploy
  Total time: ~30 minutes per feature (waiting for Codex)

After:
  Code → Local checks (1 min) → Codex only if needed (2 min) → auto-commit → deploy
  Total time: ~5 minutes per feature (no waiting)
  Speedup: 6x faster
```

### Quality (No Compromise)
```
✅ Principles check: All 11 Stewardship principles enforced
✅ Privacy gates: PRIVACY-INVARIANTS.md enforced
✅ Security: Semgrep + local scanning catches issues early
✅ Code quality: ESLint + TypeScript on all changes
✅ Test coverage: Playwright QC tests before deployment
✅ Codex review: Still available for complex logic (Tier 1 features)
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Local models hallucinate | Verify output with ESLint + TypeScript before commit |
| Vector search returns wrong docs | Test FAISS index accuracy; rebuild nightly |
| Codex queue backs up | Monitor queue; alert if >10 items; scale concurrency |
| GPU runs out of VRAM | Disable day-time model loading; night-only is fine |
| Metrics tracking overhead | Use async logging; minimal impact (~1% of tokens saved) |

---

## Next Steps (Execution)

1. **Today:** Review this plan; ask questions
2. **Week 1 kickoff:** Start with Week 1 tasks
3. **Daily standup:** 15 min check-in on task progress
4. **Weekly review:** Metrics review + plan adjustments
5. **Post-Week-4:** Optimize based on real metrics

---

## Files to Update/Create

```
NEW FILES:
  scripts/security_pre_check.sh
  scripts/vector_search.py
  scripts/local_code_generator.py
  scripts/optimization_metrics.py
  scripts/codex_queue_monitor.py
  scripts/snapshot_generator.py
  scripts/load_night_models.sh
  .claude/codex-prompts/*.prompt (5 templates)
  docs/CURRENT_CODEX_USAGE.md
  .codex-reviews/ (cache directory)
  .architecture-snapshots/ (digest directory)

UPDATES:
  .ralph-config.json (add local checks, async processing)
  DECISIONS.md (log optimization decisions + metrics)
  LESSONS.md (log learnings as we implement)
```

---

**Ready to start Week 1?** Let me know — we can begin with the usage audit and prompt templates today.
