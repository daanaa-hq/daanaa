# Capability Gap Log

**Every time Claude says "I can't" or asks a question that wasn't strictly needed, log it here.**

Pattern detection drives skill creation. Same gap appearing 3+ times → create a SKILL.md.

---

## Active gaps

| Date | Agent | Gap description | Frequency | Resolution path | Status |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Resolved gaps (history)

| Date | Resolved by | Gap description | Solution |
|---|---|---|---|
| - | - | - | - |

---

## How to use

When Claude says any of:
- "I can't access X"
- "I don't have a tool for X"
- "Can you tell me X?" (where Claude should have figured it out)
- "I'm not sure how to do X"

→ Log it here with:
- Date
- Which agent (or "Claude Code session")
- 1-line description
- (Later, on retro) Resolution path

## Pattern threshold
- 1 occurrence: monitor
- 2 occurrences: note pattern, plan resolution
- 3+ occurrences: create SKILL.md or update agent definition this week

## Examples of resolutions
- Need new MCP server → add to `.mcp.json`
- Missing context in prompt → update agent's system message
- Need new tool capability → write SKILL.md
- Question that should have been answered → update CLAUDE.md
- Gap is intentional (out of scope) → mark as "won't fix"
