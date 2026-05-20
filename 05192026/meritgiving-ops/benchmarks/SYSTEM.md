# Benchmarking System

**How MERIT measures Claude and agent performance, and how the system gets sharper over time.**

Claude doesn't have native self-measurement. This document is the instrumentation MERIT puts around Claude to make sure performance is visible, trending in the right direction, and continuously improving.

---

## Layer 1: Token economy tracking

### What we measure
- Tokens in / tokens out per API call
- Cost per call ($)
- Which agent made the call
- What task it accomplished
- Outcome (success / partial / failure / escalated)

### How we track it
- Every API call wrapped in a `track_claude_call()` helper
- Logged to Postgres `claude_calls` table
- Daily aggregation by `credits-tracker` worker

### Key metrics
| Metric | Target | Direction |
|---|---|---|
| Cost per ADR logged | < $0.50 | trending down |
| Cost per morning brief | < $1.00 | trending down |
| Cost per claim verification (Phase 1+) | < $2.00 | trending down |
| Cost per BMF ingest run | < $0.10 (mostly local) | flat |
| Total monthly Claude API spend | < $50/mo Phase 0 | flat |
| Total monthly with credits | < $300 net | flat |

### Regression alerts
- Any agent's avg cost > 30% above last month → ops-lead notification
- Total monthly burn projecting > $300 net → P1 escalate
- Any single call > 100K tokens → audit log + review

### Schema (Postgres)

```sql
CREATE TABLE claude_calls (
  id SERIAL PRIMARY KEY,
  ts TIMESTAMPTZ DEFAULT NOW(),
  agent_name VARCHAR(64) NOT NULL,
  task_id VARCHAR(128),
  model VARCHAR(64) NOT NULL,
  input_tokens INTEGER NOT NULL,
  output_tokens INTEGER NOT NULL,
  cached_tokens INTEGER DEFAULT 0,
  cost_cents INTEGER NOT NULL,
  outcome VARCHAR(32),
  notes TEXT
);

CREATE INDEX idx_claude_calls_agent_ts ON claude_calls(agent_name, ts);
CREATE INDEX idx_claude_calls_task ON claude_calls(task_id);
```

---

## Layer 2: Output quality grading

### Weekly sampling
Every Friday retro, sample 3 random Claude outputs from the week:
1. One agent-generated artifact (brief, draft, code)
2. One Claude Code session output
3. One automated worker output

Score 1-10 on:
- **Accuracy:** Was it factually correct?
- **Brevity:** Was it appropriately concise?
- **Mission-alignment:** Did it honor mission lock?
- **Actionability:** Could the recipient act on it?

### Monthly trend
Aggregate 12 samples/month into `meritgiving-ops/benchmarks/quality-YYYY-MM.md`. Plot median + worst-case.

### Goals
| Metric | Gate 4 (Week 12) | Gate 7 (Week 24) | Year 1 |
|---|---|---|---|
| Median accuracy | ≥ 8/10 | ≥ 9/10 | ≥ 9/10 |
| Median brevity | ≥ 8/10 | ≥ 9/10 | ≥ 9/10 |
| Median mission-alignment | ≥ 9/10 | 10/10 | 10/10 |
| Median actionability | ≥ 8/10 | ≥ 9/10 | ≥ 9/10 |
| Worst-case any category | ≥ 6/10 | ≥ 7/10 | ≥ 7/10 |

### What to do with bad scores
- Single low score (< 6): note it; don't act
- Two low scores in same category: review the agent's prompt and patterns
- Pattern of low scores: refactor the agent definition + update CLAUDE.md
- Pattern of low scores in mission-alignment: STOP shipping that agent's work until fixed

---

## Layer 3: Capability gap log

Every time Claude says "I can't" or "I don't have access to" or asks you a question that wasn't strictly needed, log it.

### Format
File: `meritgiving-ops/benchmarks/capability-gaps.md`

```markdown
| Date | Agent | Gap description | Resolution path |
|---|---|---|---|
| 2026-05-19 | morning-briefer | Can't access Stripe payout schedule | Add Stripe MCP to morning-briefer tool list |
| 2026-05-20 | data-lead | Can't reach Texas SOS website | Add fetch tool with TX SOS allowlist |
```

### Pattern detection
- Same gap 3+ times → create SKILL.md to address it
- Gap blocks a critical workflow → P1 escalate, fix this week
- Gap is a "won't fix" (out of scope) → mark and move on

### How this becomes "autonomous capability addition"
Gap logged → pattern detected → skill created → agent now handles it → gap closed → never asked again.

This is the iteration loop. It compounds: by Month 6, common gaps are all closed, and Claude handles 95%+ of asks without re-asking.

---

## Layer 4: External benchmarks (Claude watches; CEO doesn't need to)

### What gets monitored
Quarterly `/model-upgrade-check` slash command runs:

1. **Anthropic releases:** new models, deprecation notices, new features
2. **Claude Code changelog:** new commands, MCP improvements
3. **MCP server registry:** new servers worth adopting
4. **Key GitHub repos** (see list below)
5. **Token cost trends:** Anthropic pricing changes
6. **Benchmark publications:** SWE-bench, HumanEval-X, ARC-AGI scores when relevant

### Watchlist repos
- `anthropics/claude-cookbooks` — official patterns
- `anthropics/anthropic-cookbook` — production patterns
- `anthropics/prompt-eng-interactive-tutorial`
- `modelcontextprotocol/servers` — official MCP reference
- `modelcontextprotocol/awesome-mcp-servers` — community curated
- `Aider-AI/aider` — efficient repo-map and edit patterns
- `cline/cline` — VS Code AI patterns
- `continuedev/continue` — context management patterns
- `getzep/graphiti` — agent memory patterns
- `simonw/llm` — Simon Willison's LLM CLI; great pattern observations

### Output
Quarterly memo: `meritgiving-ops/benchmarks/ecosystem-YYYY-QN.md`
- New models worth adopting (with cost/quality analysis)
- New patterns to incorporate
- Deprecated patterns to phase out
- New MCP servers to evaluate
- New tools that could displace current ones

### Recommendations come with ADRs
Don't just adopt; document the decision. Every model swap, every new MCP server, every pattern change gets an ADR.

---

## Layer 5: Public efficiency reporting

### What we publish (Phase 0 build log, then Phase 1+ public)
- Monthly: "MERIT ops at $X/month, Y agents, Z workflows"
- Quarterly: detailed breakdown of cost per outcome
- Annually: full year retrospective with metrics

### Why this matters
- Forces operational honesty
- Invites community improvement suggestions
- Differentiates from opaque incumbents
- Builds funder credibility (we are operationally disciplined)

### What we DON'T publish
- Detailed prompt engineering (could be copied)
- Exact agent definitions (those are competitive)
- Specific dollar amounts on individual sponsors
- User-level data of any kind

---

## Self-improvement loop (the meta-system)

The whole thing is designed to compound:

```
1. Claude does work
2. Token cost logged (Layer 1)
3. Output sampled and graded (Layer 2)
4. Gaps captured (Layer 3)
5. External patterns watched (Layer 4)
6. Public reporting forces discipline (Layer 5)
7. Patterns become skills
8. Skills get refined
9. New ADRs document improvements
10. Loop continues, each cycle cheaper and better
```

Goal: by Month 12, Claude-per-MERIT operations are 50% more efficient than Month 1.

## What this looks like in practice

**Monday morning of Week 4:**
- Open `/ceo` dashboard
- See: "Claude API spend this month: $12 (target <$50). 92% within budget."
- See: "Quality trend: 8.7 median (target ≥8). No regressions."
- See: "Capability gaps closed this week: 3. New gaps: 1 (Stripe Identity API)."
- Click into benchmark dashboard if curious about details.

**Monthly review (1st of month):**
- credits-tracker auto-generates "Cost per outcome" report
- Quality grader auto-generates monthly quality trend
- capability-gaps.md reviewed for new skill candidates
- 30-minute review with strategy-lead

**Quarterly:**
- `/model-upgrade-check` runs
- Ecosystem memo published
- Major adjustments via ADRs
- Public report drafted for build-in-public

## How to know this is working

Three signals:
1. **Cost per outcome trending down** — system is learning
2. **Gap log shrinking** — capabilities filling in
3. **Quality scores trending up** — outputs getting sharper

If any of those reverse, the system has a real problem. Escalate.

If all three are healthy, MERIT is genuinely operating at improving efficiency over time. That's the moat we're building under the moats.
