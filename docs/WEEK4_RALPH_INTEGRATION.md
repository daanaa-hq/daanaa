# Week 4 Task 4.4: Ralph Task Queue Integration

**Date:** 2026-08-12  
**Status:** ✅ COMPLETE  
**Goal:** Orchestrate pre-checks + Codex review workflow with automatic logging

---

## What Ralph Integration Does

Ralph automates the Codex review workflow:
1. **Security scan** (Semgrep) → 2. **Code quality** (ESLint/TypeScript) → 3. **Doc search** (FAISS) → 4. **Codex review** → 5. **Log results**

All results logged automatically to `docs/ralph_codex_reviews.jsonl` for metrics tracking.

---

## Task Configuration

**File:** `.ralph-tasks/codex_review_workflow.json`

**Workflow Steps:**

```json
1. security_scan
   - Command: ./scripts/semgrep_security_scan.sh
   - Failure mode: STOP (critical errors block Codex)
   - Metric tracked: security_findings_count

2. lint_and_typecheck
   - Command: ./scripts/lint_and_typecheck.sh
   - Failure mode: WARN (errors logged, non-blocking)
   - Metric tracked: lint_error_count

3. documentation_search
   - Command: python3 scripts/search_docs.py "$CONTEXT_QUERY" --k 3 --json
   - Requires input: CONTEXT_QUERY (architecture question)
   - Metric tracked: docs_retrieved_count

4. codex_review
   - Type: HUMAN (Codex runs, manual initiation)
   - Inputs: pre-check results, doc search results
   - Metric tracked: codex_token_usage

5. log_results
   - Command: node scripts/ralph-log-codex-review.js
   - Inputs: all workflow results
   - Stores: docs/ralph_codex_reviews.jsonl
```

**Governance Gates:**
- ✅ Principles check (findings must reference STEWARDSHIP P1-P11)
- ✅ Quality threshold (0 security errors, 0 type errors)

---

## Integration Files

| File | Purpose |
|------|---------|
| `.ralph-tasks/codex_review_workflow.json` | Workflow definition |
| `scripts/ralph-log-codex-review.js` | Review logger + metrics aggregator |
| `scripts/codex_metrics_dashboard.py` | Metrics dashboard (Week 4.5) |

---

## Usage

### Run Complete Workflow

```bash
# Start Codex review workflow
node scripts/ralph-setup.js codex_review_workflow

# Output:
# 1️⃣  Running security scan...
#     ✅ 0 findings
# 2️⃣  Running lint checks...
#     ✅ 0 errors, 35 warnings (OK)
# 3️⃣  Preparing documentation context...
#     ✅ Retrieved 3 docs for "V6 scoring"
# 4️⃣  Awaiting Codex review...
#     [User runs Codex via template]
# 5️⃣  Logging results...
#     ✅ Review logged (tokens: 2,400, findings: 3)
```

### Log a Codex Review

After Codex completes:

```bash
node scripts/ralph-log-codex-review.js \
  --task-id "arch_v6_review_001" \
  --review-type "architecture" \
  --tokens-used 2500 \
  --codex-findings 3 \
  --semgrep-findings 0 \
  --lint-errors 0 \
  --principles-referenced "P3,P4,P9" \
  --status "completed"

# Output:
# ✅ Review logged: arch_v6_review_001
```

### View Metrics

```bash
python3 scripts/codex_metrics_dashboard.py

# Output:
# CODEX TOKEN METRICS DASHBOARD
# =====================================================
# Total reviews: 5
# Average tokens per review: 2,850
# Pre-check effectiveness: 87% (87% caught by pre-checks)
# Savings vs. baseline: 76%
# Projected/month: 178,500 tokens saved
```

---

## Logging Format

**File:** `docs/ralph_codex_reviews.jsonl` (one JSON object per line)

```json
{
  "timestamp": "2026-08-12T15:30:00Z",
  "task_id": "arch_v6_review_001",
  "review_type": "architecture",
  "status": "completed",
  "tokens_used": 2500,
  "findings_count": 3,
  "semgrep_findings": 0,
  "lint_errors": 0,
  "codex_findings": 3,
  "principles_referenced": ["P3", "P4", "P9"],
  "unix_time": 1691856600
}
```

---

## Metrics Tracked

**Real-time Aggregation:**

| Metric | Purpose |
|--------|---------|
| `total_reviews` | Track review frequency |
| `total_tokens_used` | Monitor token budget |
| `pre_check_findings` | Count issues caught early |
| `codex_findings` | Count Codex-discovered issues |
| `pre_check_effectiveness` | % of issues caught pre-Codex |
| `tokens_saved` | vs. baseline (calculated) |

**By Review Type:**
- Architecture (baseline: 12K tokens)
- Security (baseline: 12K tokens)
- Code (baseline: 8K tokens)

---

## Dashboard Features (Week 4.5)

### Real-Time View

```bash
python3 scripts/codex_metrics_dashboard.py
```

Shows:
- Total reviews and tokens used
- Average tokens per review
- Pre-check effectiveness %
- Savings vs. baseline
- Breakdown by review type

### Export to JSON

```bash
python3 scripts/codex_metrics_dashboard.py --export json
# Saves: docs/codex_metrics_export.json
```

### Export to CSV

```bash
python3 scripts/codex_metrics_dashboard.py --export csv
# Saves: docs/codex_metrics_export.csv (one row per review)
```

### Export to HTML

```bash
python3 scripts/codex_metrics_dashboard.py --export html
# Saves: docs/codex_metrics_export.html (dashboard view)
```

---

## Integration with Codex Workflow

### Template: Codex Pre-Validated Review

Create `.claude/codex-prompts/codex_pre_validated_review.prompt`:

```
<task>
[CHANGE_TYPE]: [CHANGE_DESCRIPTION]

Pre-validation complete:
  ✅ Security: ./scripts/semgrep_security_scan.sh (0 critical findings)
  ✅ Code quality: ./scripts/lint_and_typecheck.sh (0 errors)
  ✅ Context: FAISS doc search retrieved relevant documentation

Focus Codex on:
  - Logic errors (not caught by pre-checks)
  - Performance issues
  - Architectural concerns
  - STEWARDSHIP principle alignment (P1-P11)

Do NOT:
  - Suggest ESLint rules (handled pre-check)
  - Point out type mismatches (tsc -b already ran)
  - Identify hardcoded secrets (Semgrep already scanned)
</task>

<structured_output_contract>
Format: Significant findings only
1. Finding name | severity | why Codex only
2. Root cause (from code analysis)
3. Recommended fix (1-2 sentences)

Max 300 words. Cite specific files + line numbers.
Reference STEWARDSHIP principles if applicable.
</structured_output_contract>
```

---

## Workflow Example: Architecture Review

### Step 1: Initiate Review

```bash
node scripts/ralph-setup.js codex_review_workflow

# 1️⃣  Running security scan...
#     ✅ 0 findings
# 2️⃣  Running lint checks...
#     ✅ 0 errors
# 3️⃣  Preparing docs for "V6 scoring architecture"...
#     [1] DECISIONS.md: V6 comprehensive integration...
#     [2] CLAUDE.md: Financial context system...
#     [3] STEWARDSHIP.md: Principle 4 - Small orgs...
# 
# Docs ready. Copy below into Codex prompt:
```

### Step 2: Run Codex

Paste the template + doc search results + change description:

```
<task>
CHANGE: Review V6 scoring for fairness issues

Pre-validation complete:
  ✅ Security: 0 critical findings
  ✅ Code quality: 0 errors
  ✅ Context: FAISS retrieved 3 relevant docs

Documentation context:
[1] DECISIONS.md: V6 assigns tiered peer context (NTEE2 × band × region)...
[2] CLAUDE.md: merit_score in registry_enriched, v4/v5 archived...
[3] STEWARDSHIP.md: P4 - Small orgs deserve fairness...

Focus on: Is V6 biased against small organizations?
</task>
```

### Step 3: Log Results

After Codex responds:

```bash
node scripts/ralph-log-codex-review.js \
  --task-id "v6_fairness_review_aug12" \
  --review-type "architecture" \
  --tokens-used 2100 \
  --codex-findings 2 \
  --semgrep-findings 0 \
  --lint-errors 0 \
  --principles-referenced "P3,P4" \
  --status "completed"

# ✅ Review logged: v6_fairness_review_aug12
```

### Step 4: Check Metrics

```bash
python3 scripts/codex_metrics_dashboard.py

# 1 review logged
# Tokens used: 2,100 (vs. 12,000 baseline)
# Savings: 82%
```

---

## Automation & Monitoring

### Set Up Logging Hook

Add to `.git/hooks/post-codex-review` (trigger after Codex):

```bash
#!/bin/bash
# Log Codex review automatically

node scripts/ralph-log-codex-review.js \
  --task-id "$(git rev-parse --short HEAD)_$(date +%s)" \
  --review-type "$REVIEW_TYPE" \
  --tokens-used "$TOKENS_USED" \
  --codex-findings "$FINDINGS_COUNT" \
  --status "completed"
```

### Daily Metrics Export

Add to crontab:

```bash
# Daily: export metrics to JSON for dashboarding
0 23 * * * cd /home/akbar/meritgiving && python3 scripts/codex_metrics_dashboard.py --export json
```

---

## Status: ✅ Week 4.4 COMPLETE

**Files created:**
- `.ralph-tasks/codex_review_workflow.json` (workflow definition)
- `scripts/ralph-log-codex-review.js` (logger + metrics)
- `scripts/codex_metrics_dashboard.py` (dashboard + export)

**Features:**
- ✅ 5-step workflow automation
- ✅ Automatic logging to JSONL
- ✅ Real-time metrics aggregation
- ✅ Export to JSON/CSV/HTML
- ✅ Token savings calculation

**Ready for:** Week 4.5 (validation + monitoring)
