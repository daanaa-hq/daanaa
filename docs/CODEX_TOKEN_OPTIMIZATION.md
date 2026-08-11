# Codex Token Optimization Strategy

**Goal:** Reduce token usage in Codex reviews by 40-60% without compromising quality.  
**Applied to:** Architecture reviews, code fixes, architectural decisions  
**Constraints:** Quality gates remain intact; Stewardship principles non-negotiable

---

## Quick Wins (Implement Today)

### 1. Use Context7 for Background Context (Save 3,000-5,000 tokens/review)
**Before:**
```prompt
Review the Daanaa project. First, here's CLAUDE.md (20KB), STEWARDSHIP.md (12KB), 
DECISIONS.md (5KB), LESSONS.md (5KB)...
[Full 40KB of context pasted into prompt]
```
**Tokens used:** ~11,000 tokens for background

**After:**
```prompt
Review Daanaa (see architecture in Context7: npx context7 daanaa "how does 
the system work?"). Read DECISIONS.md and LESSONS.md directly from repo for 
recent context.
```
**Tokens used:** ~500 tokens for reference + Context7 handles doc lookups

**Implementation:**
- Remove full-file context from Codex prompts
- Reference Context7 for architecture/design
- Use git log for recent decisions (`git log --oneline -20`)
- Codex reads specific files directly when needed

---

### 2. Structured Output Contracts (Save 2,000-3,000 tokens/review)
**Before:**
```prompt
Analyze this code and provide a comprehensive review including:
- What works well
- What could be improved  
- Suggestions for refactoring
- Performance considerations
- Security review
- Testing gaps
- Documentation needs
- Long-term maintenance concerns
```
**Tokens used:** Codex generates 2,000+ word essay exploring all angles

**After:**
```prompt
<task>
Review this code change for quality and risks.
</task>

<structured_output_contract>
Format: Brief analysis only
1. What works well (1-2 sentences)
2. Top 3 gaps:
   - Name | Severity (high/medium/low) | Impact
3. Single highest-priority fix (1 sentence)
4. Effort estimate (S/M/L)

Constraints:
- Max 200 words total
- No generic advice unmoored to the code
- Cite specific line numbers if flagging issues
</structured_output_contract>
```
**Tokens used:** Codex outputs 200-300 words, exactly what's needed (vs 2,000+ exploratory)

**Implementation:**
- Always include `<compact_output_contract>` with `format:` and `max_length:`
- Use structured XML blocks (forces concise output)
- Request numbered lists over prose
- Specify "output no more than X words/lines"

---

### 3. Incremental Reviews (Save 5,000-8,000 tokens/review)
**Before:**
```prompt
Review all changes in this PR. [Attach entire 50KB diff of all files changed]
```
**Tokens used:** Full diff context = 14,000+ tokens just for context

**After:**
```prompt
Review only the changed lines in these files:
- frontend/src/components/TrustBadge.tsx (lines 45-67) — Firebase removal
- frontend/src/utils/taxDeductible.ts (new file) — IRS status mapping

[Show only changed lines, not full file]
```
**Tokens used:** ~2,000 tokens for focused diff

**Implementation:**
- Use `git diff <file>` instead of full file context
- Show only changed lines (not context lines) when possible
- Use line numbers to reference specific sections
- For new files, show only the essential parts (skip boilerplate)

---

### 4. Result Caching & Reuse (Save 2,000-4,000 tokens/review)
**Before:**
- Run Codex review on Monday: 12,000 tokens
- Run Codex review on Wednesday on same file: 12,000 tokens
- Total: 24,000 tokens

**After:**
- Run Codex review on Monday: 12,000 tokens
- Cache result in `.codex-reviews/<filename>.json`
- Wednesday: Reference cached review, only ask about delta changes
- Total: 12,000 + 2,000 = 14,000 tokens

**Implementation:**
```bash
# After Codex review completes, save result
codex review --save-to .codex-reviews/daanaa_api.py.json

# On next review of same file:
codex review daanaa_api.py --from-cache .codex-reviews/daanaa_api.py.json \
  "Focus only on changes since last review (see cache for baseline)"
```

**Cache structure:**
```json
{
  "file": "daanaa_api.py",
  "reviewed_at": "2026-08-11T23:00:00Z",
  "baseline_observations": {
    "architecture_quality": "high",
    "test_coverage": "good",
    "known_gaps": ["endpoint versioning", "rate limiting"]
  },
  "recommendations_implemented": [
    "Add privacy gates to /admin endpoints"
  ],
  "git_commit_base": "5777544309a"
}
```

---

### 5. Batch Related Reviews (Save 3,000-5,000 tokens/cycle)
**Before:**
```
Review 1: "Is TrustBadge component accessible?" — 5,000 tokens
Review 2: "Is OrgDetailPage accessible?" — 5,000 tokens  
Review 3: "Is HomePage accessible?" — 5,000 tokens
Total: 15,000 tokens
```

**After:**
```
Single review: "Audit accessibility across TrustBadge, OrgDetailPage, HomePage.
Format: [Component | Issue | Fix]. Max 300 words."
Total: 4,000 tokens (Codex handles all three in one efficient pass)
```

**Implementation:**
- Group related code reviews by theme (accessibility, performance, security)
- Ask Codex to review them in one pass with structured output
- Save 60-70% tokens vs. individual reviews

---

## Advanced Optimizations

### 6. Semantic Deduplication (Token Budget Management)
**Pattern:** Before asking Codex a question, check if Context7 can answer it first.

```bash
# Instead of asking Codex to explain V6 scoring:
npx context7 daanaa "How does V6 scoring work?" --tokens 2000
# If answer is sufficient, skip Codex (save 5,000+ tokens)

# Only escalate to Codex if Context7 answer is incomplete:
codex task "Context7 says [answer]. Is there an edge case in [specific area]?"
# Focused follow-up = 2,000 tokens vs. 8,000 for full review
```

**Token savings:** 40-50% on architectural questions

---

### 7. Prompt Template Library (Reusable, Token-Efficient)
**Create once, reuse forever:**

`.claude/codex-prompts/review-architecture.txt`:
```
<task>
[CHANGE_DESCRIPTION]
</task>

<compact_output_contract>
Format: 
- Current state (1 sentence)
- Top 3 risks (name | severity | mitigation)
- Recommendation (1 sentence)
Max 250 words.
</compact_output_contract>

<grounding_rules>
- Reference files you actually reviewed
- Flag speculative items
- Cite STEWARDSHIP.md Principles P1-P11 if applicable
</grounding_rules>
```

**Reuse pattern:**
```bash
codex task --template review-architecture \
  --var CHANGE_DESCRIPTION "Added Context7 + Ralph integration"
# Codex uses template + only fills variables = 40% token savings
```

---

### 8. Decision Tree: When to Use What (Avoid Mismatched Tool Use)

| Question | Tool | Why | Token Cost |
|----------|------|-----|-----------|
| "How does V6 scoring work?" | Context7 | Indexed docs, no LLM needed | 500 |
| "Is there an edge case in V6 when revenue band is unknown?" | Codex + Context7 ref | Requires reasoning | 2,000 |
| "Review this code change for security issues" | Codex review | Needs LLM analysis | 5,000 |
| "What are the 3 highest-impact optimizations?" | Codex (structured) | Needs prioritization | 3,000 |
| "How do I fix this bug?" | Codex --write | Needs implementation | 8,000 |

**Rule:** Use Context7 for knowledge, Codex for reasoning/analysis/implementation.

---

## Token Budget Framework

### Monthly Codex Budget (Estimated)

| Activity | Frequency | Cost/Run | Monthly |
|----------|-----------|----------|---------|
| Architecture review | 4x/month | 12,000 | 48,000 |
| Code review (PRs) | 20x/month | 5,000 | 100,000 |
| Bug fix implementation | 8x/month | 8,000 | 64,000 |
| Feature brainstorm | 4x/month | 4,000 | 16,000 |
| **Total (without optimization)** | — | — | **228,000** |

### After Optimizations Applied

| Activity | Reduction | New Cost/Run | Monthly |
|----------|-----------|--------------|---------|
| Architecture review | -45% (Context7) | 6,600 | 26,400 |
| Code review | -50% (incremental) | 2,500 | 50,000 |
| Bug fix | -30% (template + cache) | 5,600 | 44,800 |
| Feature brainstorm | -40% (structured) | 2,400 | 9,600 |
| **Total (with optimization)** | — | — | **130,800** |

**Savings: 97,200 tokens/month (43% reduction) — ZERO quality compromise**

---

## Implementation Checklist

- [ ] **Week 1:** Set up Context7 caching + structured output contracts in all Codex prompts
- [ ] **Week 2:** Implement incremental review patterns (diff-only, not full files)
- [ ] **Week 3:** Build `.codex-reviews/` cache structure + decision tree logic
- [ ] **Week 4:** Create prompt template library (5 core templates)
- [ ] **Ongoing:** Before every Codex prompt, ask "Can Context7 answer this?"

---

## Guardrails (Quality Non-Negotiables)

✅ **DO optimize:** Background context, output format, batching, caching  
✅ **DO use:** Tight prompts, structured contracts, incremental reviews  
❌ **DON'T compromise:** Principles check (Stewardship P1-P11), privacy gates, security depth  
❌ **DON'T skip:** Review of critical files (API, auth, privacy, scoring)  
❌ **DON'T cache:** Security-sensitive reviews (once per release, full cost OK)

---

## Example: Applying to Current Codex Review

**Current (High-Cost) Approach:**
```
"Review Daanaa architecture. Here is CLAUDE.md (20KB), STEWARDSHIP.md (12KB), 
DECISIONS.md (5KB), PRIVACY-INVARIANTS.md (8KB)...
Please provide comprehensive analysis of centralization gaps, automation gaps, 
bottleneck opportunities, quality optimizations, security vulnerabilities, 
speed optimizations, token efficiency, and state synchronization."

Tokens: ~15,000 for context + exploring all 8 areas
```

**Optimized Approach (Using Context7 + Structured Contract):**
```
<task>
Review Daanaa automation architecture for gaps.

Reference: See Context7 for system design (npx context7 daanaa "architecture"). 
Read DECISIONS.md and LESSONS.md from git log for recent context.
Do NOT include full CLAUDE.md or STEWARDSHIP.md — assume knowledge of principles.

Analyze these 8 gap categories:
1. Centralization — single sources of truth
2. Automation — remaining manual steps
3. Bottlenecks — human wait points
4. Quality — missing test coverage
5. Security — privacy edge cases
6. Speed — parallel opportunities
7. Tokens — LLM cost reduction
8. State sync — git/config/runtime alignment
</task>

<structured_output_contract>
Format: 8 sections, 2-3 sentences each (one per gap above)
Each section: Name | Root cause | Recommendation

Then: Top 3 findings ranked by impact (Effort est. S/M/L)

Constraints:
- Max 800 words total
- Cite specific files/lines if flagging gaps
- Flag speculative findings with "(hypothesis)"
- No elaboration beyond what's needed
</structured_output_contract>

Tokens: ~5,000 total (vs. 15,000 unoptimized)
- Context7 reference saves: 10,500 tokens (context alone)
- Structured contract saves: 1,000 tokens (prevents exploration)
- Savings: 70% vs. unstructured approach
```

---

## Using the Prompt Templates (Week 3 Implementation)

**Location:** `.claude/codex-prompts/`

**5 Core Templates:** (see README.md for full guide)
1. `review-architecture.prompt` — Architecture decisions, system design
2. `fix-code.prompt` — Specific error fixes, bugfixes
3. `review-security.prompt` — Security audits, compliance checks
4. `review-performance.prompt` — Performance optimization, latency reduction
5. `review-integration.prompt` — Cross-system integration, API contracts

**Usage Pattern:**
```bash
# 1. Load template
cat .claude/codex-prompts/review-architecture.prompt

# 2. Substitute variables
# Replace [CHANGE_TYPE], [CHANGE_DESCRIPTION], [SYSTEM] with actual values

# 3. Send to Codex
# Paste into Codex CLI or UI

# 4. Verify output meets contract
# Check word count, format, grounding rules
```

**Expected Token Savings:**
- Full review (old): 14.5K tokens
- Full review (optimized template): 2.7K tokens
- Conservative estimate (Week 3): 25% reduction (to 10.8K)
- Aggressive estimate: 81% reduction (achievable with discipline)

---

## References

- **Context7 API:** https://github.com/upstash/context7
- **Prompt Templates:** `.claude/codex-prompts/` (5 templates + README)
- **Template Usage Guide:** `.claude/codex-prompts/README.md`
- **Codex Prompting:** `.claude/plugins/cache/openai-codex/codex/1.0.6/skills/gpt-5-4-prompting`
- **Token Counter:** Use `wc -w` on prompt text, divide by 4 for rough token estimate

---

**Remember:** Optimized prompts aren't lazy — they're *precise*. Codex produces better output when you tell it exactly what you need. Use the templates; they're production-ready.
