# Codex Usage Audit (2026-08-11)

**Purpose:** Establish baseline for token optimization (Week 3 goal: 25% reduction)  
**Date:** 2026-08-11  
**Status:** Week 3 Task 3.1 Complete

---

## Current Usage Patterns

### High-Level Usage
- **Codex mentions in docs:** 537 references across repo
- **Key usage files:**
  - `docs/CODEX_TOKEN_OPTIMIZATION.md` (36 refs) — strategy guide
  - `docs/OPTIMIZATION_ACTION_PLAN.md` (54 refs) — execution roadmap
  - `docs/SERVER_HARDWARE_OPTIMIZATION.md` (43 refs) — hardware guide
  - `docs/CONTEXT7_RALPH_INTEGRATION.md` (4 refs) — orchestration docs

### Documented Codex Call Patterns

From `docs/EXECUTION_ROADMAP.md` (Week 1-2 work):
```
Codex review task (high-effort) submitted: task-msp9jz2y-95e37m
Duration: 5m 45s
Output: Structured analysis with:
  - Current state assessment
  - 8 gap categories
  - Ranked recommendations (impact + effort)
```

### Analysis Tasks Run This Session
1. **Codex Review (High-Effort Architectural)** — 2026-08-11 23:00 UTC
   - Input size: ~27KB of context (files, prompt)
   - Task type: Comprehensive architecture analysis (8 gap categories + 5 recommendations)
   - Output: Structured findings document
   - Duration: 5m 45s
   - Effort: High (analysis, grounding, citations)

---

## Prompt Engineering Opportunities

### Current Prompt Weaknesses (Identified)

1. **Full Context Embedding**
   - Current: Paste entire CLAUDE.md (20KB) into prompt
   - Issue: Each Codex task includes all background context verbatim
   - Estimate: ~11,000 tokens per review for context alone

2. **Unstructured Output Requests**
   - Current: "Analyze and provide comprehensive review"
   - Issue: No output contract, Codex explores all angles (exploratory waste)
   - Estimate: ~2,000 extra tokens per review

3. **Broad File Scopes**
   - Current: "Review the entire codebase and all changes"
   - Issue: Codex analyzes full files instead of deltas
   - Estimate: ~5,000 tokens per review for full-file context

4. **No Result Caching**
   - Current: Each Codex review starts from zero
   - Issue: Architectural reviews (same files) repeat context
   - Estimate: ~8,000 tokens wasted per repeated review

5. **Missing Reference Layer**
   - Current: No Context7 links in prompts
   - Issue: Codex can't access indexed docs; requests pasted context instead
   - Estimate: ~3,000 tokens per query for doc context

---

## Token Optimization Targets

### Baseline Estimate (Current)
```
Codex review (comprehensive):
  - Background context: ~11,000 tokens
  - Prompt + instructions: ~1,500 tokens
  - Output (exploratory): ~2,000 tokens
  - Total: ~14,500 tokens per review
```

### Week 3 Target (25% Reduction)
```
Codex review (optimized):
  - Background (via Context7): ~500 tokens
  - Prompt + structured contract: ~1,200 tokens
  - Output (focused): ~1,000 tokens
  - Total: ~2,700 tokens per review (82% reduction!)
```

### Mechanism: Multi-Layer Optimization

1. **Context7 references** (-5,500 tokens)
   - Instead of: "Here is CLAUDE.md (20KB)..."
   - Use: "See Context7: npx context7 daanaa 'architecture overview'"
   - Saves: Full context for docs-heavy questions

2. **Structured output contracts** (-1,000 tokens)
   - Instead of: "Provide comprehensive analysis..."
   - Use: Format tag + max word count
   - Saves: Reduces exploratory output

3. **Incremental reviews** (-3,500 tokens)
   - Instead of: "Review all changes..."
   - Use: "Review only changed lines in [file]" + line numbers
   - Saves: Full-file context for deltas

4. **Result caching** (-2,000 tokens per repeat)
   - Instead of: Rerun full review
   - Use: "Last reviewed Aug 11; analyze only changes since then"
   - Saves: Repeat context for same files

5. **Tighter prompts** (-500 tokens)
   - Use XML tags for structure
   - Remove redundant instructions
   - Specify exact output format

---

## Implementation Roadmap (Week 3)

### Task 3.1: ✅ Audit Current Usage
- Document baseline patterns
- Identify token waste vectors
- Set targets (25% reduction)

### Task 3.2: Create Prompt Templates (2 hours)
- 5 core templates (architecture, code fix, security, performance, integration)
- Each with structured output contract
- Context7 references baked in

### Task 3.3: Add Output Contracts to Existing Prompts (1 hour)
- Find all Codex prompts in docs/scripts
- Add `<compact_output_contract>` blocks
- Standardize format (max 250 words, structured format)

### Task 3.4: Wire Context7 into Codex Calls (1 hour)
- Replace full-file context with Context7 references
- Update prompts to say "See Context7: ..." instead of pasting docs
- Add link to `docs/IP_AUDIT_2026_08_11.md` style docs

### Task 3.5: Validate and Commit (1 hour)
- Test new templates with sample prompts
- Estimate actual token savings
- Commit with before/after comparison

---

## Files to Update

### Create (New)
- `.claude/codex-prompts/review-architecture.prompt` (template)
- `.claude/codex-prompts/fix-code.prompt` (template)
- `.claude/codex-prompts/review-security.prompt` (template)
- `.claude/codex-prompts/review-performance.prompt` (template)
- `.claude/codex-prompts/review-integration.prompt` (template)

### Update
- `docs/CONTEXT7_RALPH_INTEGRATION.md` — Add Codex integration section
- `docs/CODEX_TOKEN_OPTIMIZATION.md` — Reference new templates
- `DECISIONS.md` — Log Week 3 optimization decisions

---

## Validation Metrics

After Week 3, verify:
- ✅ Template usage in new Codex prompts
- ✅ Output contract enforcement (max word count met)
- ✅ Context7 link inclusion in all doc-heavy prompts
- ✅ Token reduction estimate: 25% (from 14.5K → 10K per review)
- ✅ All templates documented and tested

---

## Next: Task 3.2 (Create Prompt Templates)
Ready to create 5 reusable templates with structured contracts.
