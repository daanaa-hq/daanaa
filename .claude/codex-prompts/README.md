# Codex Prompt Templates

**Purpose:** Reusable, token-efficient prompts for Codex that enforce structured output and reduce context overhead.

**Token Savings:** ~25% per review (from 14.5K → 10K average)

---

## Templates

### 1. review-architecture.prompt
**Use for:** Architecture decisions, system design, integration patterns  
**Output:** Structured gap analysis + top 3 recommendations  
**Max tokens:** ~250 words  
**Context:** Via Context7 references, not full file paste

**Example:**
```bash
# Load template, substitute variables:
CHANGE_TYPE="Feature Development"
CHANGE_DESCRIPTION="Adding wallet sync via cloud backup"
SYSTEM="Wallet persistence"

# Codex command (conceptual):
codex task --template review-architecture \
  --var CHANGE_TYPE "$CHANGE_TYPE" \
  --var CHANGE_DESCRIPTION "$CHANGE_DESCRIPTION" \
  --var SYSTEM "$SYSTEM"
```

---

### 2. fix-code.prompt
**Use for:** Specific error fixes, code changes, bugfixes  
**Output:** Code block only (no prose)  
**Max tokens:** ~50 words (compressed output)  
**Key rule:** Minimal, conservative fixes only

**Example:**
```
FILE_PATH: frontend/src/utils/taxDeductible.ts
LINE_RANGE: 23-27
ERROR_TYPE: TypeScript type mismatch
ERROR_MESSAGE: Type 'boolean | null' is not assignable to type 'boolean'
CURRENT_BEHAVIOR: Function accepts null but parameter expects boolean
EXPECTED_BEHAVIOR: Function handles null as "unknown" status
```

---

### 3. review-security.prompt
**Use for:** Security audits, vulnerability assessment, compliance checks  
**Output:** Per-issue analysis (name | severity | fix | effort)  
**Max tokens:** ~400 words  
**Ties to:** PRIVACY-INVARIANTS.md + STEWARDSHIP.md principles

**Example:**
```
FINDING_TYPE: Tier 2 data flow audit (privacy gate)
TOOL_NAME: semgrep
ISSUE_COUNT: 3
ISSUES_LIST:
  - wallet data sent to external fetch()
  - console.log() with revenue fields
  - search endpoint accepts user_id parameter
```

---

### 4. review-performance.prompt
**Use for:** Performance optimization, latency reduction, scaling  
**Output:** Root cause + 3 optimizations ranked by ROI  
**Max tokens:** ~300 words  
**Baseline targets:**
- Org detail page: <3 sec
- Search: <1 sec
- Homepage: immediate

**Example:**
```
COMPONENT: GET /api/search endpoint
BASELINE_METRICS: p50 250ms, p95 475ms (from Gate 3 benchmark)
PROBLEM: Search response too slow for real-time typeahead
CONSTRAINTS: SQLite only (no separate cache store), <2GB droplet
```

---

### 5. review-integration.prompt
**Use for:** Cross-system integration, workflow orchestration, API contracts  
**Output:** Gap analysis + step-by-step pattern  
**Max tokens:** ~350 words  
**Key systems:** Context7, Ralph, Playwright, Codex, Stewardship gates

**Example:**
```
COMPONENT_A: Ralph (task orchestrator)
COMPONENT_B: Codex (architectural reviewer)
GOAL: Codex should review deployment before Ralph executes
PROBLEM: Ralph starts deployment without Codex sign-off on phase_deployment tasks
```

---

## Template Usage Rules

### When to Use a Template
✅ Use templates for recurring Codex tasks (architecture reviews, security audits)  
✅ Use when you need structured output (ranked lists, limited scope)  
✅ Use when context can be referenced via Context7 instead of pasted  

### When NOT to Use
❌ Don't use for one-off explorations (just ask Codex directly)  
❌ Don't use if full context is essential (security-critical decisions)  
❌ Don't use if output needs to be prose narrative (proposals, explanations)

### Structure of Each Template

Every template has:
```
<task>
  [What to do]
  [How to find context (Context7 refs, not full paste)]
</task>

<structured_output_contract>
  [Exact output format]
  [Word/line limits]
  [Conditional rules]
</structured_output_contract>

[Additional blocks as needed: grounding_rules, verification_loop, etc.]
```

---

## Variable Substitution

Before sending to Codex, replace all `[VARIABLE_NAME]` placeholders:

- `[CHANGE_TYPE]` → e.g., "Feature Development", "Bug Fix", "Refactor"
- `[FILE_PATH]` → e.g., "frontend/src/utils/taxDeductible.ts"
- `[COMPONENT_A]` → system/module name
- `[SYSTEM]` → e.g., "Wallet persistence", "Search indexing"

---

## Token Savings Breakdown

| Element | Before | After | Savings |
|---------|--------|-------|---------|
| Full context | 11,000 tokens | 500 tokens | 10,500 (95%) |
| Unstructured prompt | 1,500 tokens | 1,200 tokens | 300 (20%) |
| Exploratory output | 2,000 tokens | 1,000 tokens | 1,000 (50%) |
| **Total per review** | **14,500** | **2,700** | **11,800 (81%)** |

**Note:** Actual savings vary based on prompt complexity. Baseline: ~25% (conservative estimate for Week 3).

---

## Integration with Workflow

### Step 1: Identify the Task Type
```
"Need to review architecture changes" → use review-architecture.prompt
"Bug in TypeScript file" → use fix-code.prompt
"Security audit needed" → use review-security.prompt
```

### Step 2: Substitute Variables
```bash
TEMPLATE="review-architecture.prompt"
CHANGE_TYPE="Feature Development"
CHANGE_DESC="IRS eligibility schema rebuild"

# Load template, replace [CHANGE_TYPE] and [CHANGE_DESCRIPTION]
sed -e "s/\[CHANGE_TYPE\]/$CHANGE_TYPE/g" \
    -e "s/\[CHANGE_DESCRIPTION\]/$CHANGE_DESC/g" \
    ".claude/codex-prompts/$TEMPLATE"
```

### Step 3: Send to Codex
```bash
codex task --template <template_name> --var KEY VALUE ...
# OR manual:
cat .claude/codex-prompts/<template>.prompt | pbcopy  # Copy to clipboard
# Paste into Codex and go
```

### Step 4: Verify Output Meets Contract
✅ Word count within limit?  
✅ Format matches spec?  
✅ No generic advice?  
✅ All claims grounded?  

---

## Future Enhancements

- Add `--template` flag to Codex CLI for automatic variable substitution
- Create auto-validator that checks output against contract
- Add language-specific templates (Python, TypeScript, SQL review)
- Build template library by collecting recurring prompt patterns

---

## References

- `docs/CODEX_TOKEN_OPTIMIZATION.md` — Full token strategy
- `docs/CODEX_USAGE_AUDIT_2026_08_11.md` — Baseline metrics
- `CONTEXT7_RALPH_INTEGRATION.md` — System architecture (for Context7 links)
