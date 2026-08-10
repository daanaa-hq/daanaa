# 24-Hour Governance Quick-Start

**For teams who want to start TODAY.**

This is the absolute minimum to have working governance by tomorrow morning. Not comprehensive, not perfect—just functional.

---

## Copy-Paste in 2 Hours

### Step 1: Create STEWARDSHIP.md (30 min)

```markdown
# [Your Organization]'s Governance Commitment

We build [what you build] to help [who you help] [do what they need].

## Our 3 Core Principles

1. **[Mission] comes first** — [one sentence explaining how]
2. **[Privacy/Security/Fairness] is structural** — [one sentence explaining how]
3. **[Public claim] is evidence-based** — [one sentence explaining how]

## Who Signed
- [Your name] — Founder
- [Team member] — Team

## How This Works
See DECISIONS.md for why we chose what we chose.
```

**Time: 30 min. Copy Daanaa's principles, change 3 words.**

### Step 2: Create governance/DECISIONS.md (30 min)

```markdown
# Decisions Log

## [Today's date]: [What you decided]

**Reasoning:** [Why in 2 sentences]  
**Principle:** References [Principle #X]  
**Reversible:** Yes / No

---
```

**Time: 30 min. Create file, add 1 entry (any recent decision).**

### Step 3: Add one privacy gate (1 hour)

Create `scripts/privacy_check.sh`:

```bash
#!/bin/bash
# Blocks credentials in commits

if git diff --cached | grep -E "api_key|secret|password|token|AWS_"; then
  echo "❌ Blocked: credential detected"
  exit 1
fi
echo "✅ Passed"
exit 0
```

Install hook:
```bash
cp scripts/privacy_check.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

**Time: 1 hour. Paste script, install hook, test it.**

### Step 4: Add to GitHub PR template (.github/pull_request_template.md) (30 min)

```markdown
## What changed?
[Brief]

## Why?
[Reference DECISIONS.md]

## Principle check
- [ ] Honors our 3 core principles
- [ ] DECISIONS.md updated (if non-obvious)
- [ ] Privacy gate passed
```

**Time: 30 min. Create template, copy text above.**

---

## That's It (4 Hours Real Time)

You now have:
- ✅ Published principles
- ✅ Decision log (can be updated)
- ✅ One privacy gate (blocks credentials)
- ✅ PR checklist (reminds team)

**This is governance. Not perfect. Functional.**

---

## How to Use It (Starting Tomorrow)

### Every commit:
```bash
git commit -m "feature: add X"
# Hook runs, checks for credentials
# ✅ Passes? Commit succeeds
# ❌ Fails? Fix credential, try again
```

### Every PR:
- [ ] Honors principles (yes/no)
- [ ] DECISIONS.md updated (if new)
- [ ] Check passes

### Every month:
- Skim DECISIONS.md
- Ask: "Did we honor our 3 principles?"
- Update principles if needed (rare)

---

## Next Steps (When You Have Time)

**Week 2:**
- Add 2 more privacy gates (logging, config mistakes)
- Write AUTONOMY_FRAMEWORK.md (10 min)

**Week 3:**
- Team meeting: "Here's our governance"
- Everyone reads STEWARDSHIP.md (10 min)

**Month 2:**
- Add first LESSONS.md entry (what broke + how we fixed it)
- Quarterly principle review

---

## If You're Using This Framework

Add this to your repo:

```json
{
  "governance_framework": "Daanaa AI Governance (Adapted)",
  "framework_version": "1.0",
  "quick_start_hours": 4,
  "principles_count": 3,
  "adoption_date": "YYYY-MM-DD",
  "team_size": 3,
  "reference": "https://github.com/daanaa/daanaa/docs/QUICKSTART_24HOUR.md"
}
```

Add to your README:
```markdown
## Governance
This project uses the [Daanaa AI Governance Framework](link). See [STEWARDSHIP.md](STEWARDSHIP.md).
```

---

## Real Example (Daanaa's 3 if we did this today)

**STEWARDSHIP.md:**
```
## Our 3 Core Principles

1. **Mission to help donors decide comes first** — Every feature must serve donors, not growth
2. **Donor privacy is structural** — No tracking, no exposure of giving activity, enforced by code
3. **Trust signals are evidence-based** — Only real IRS data, honest about limits, logged decisions
```

**Minimal governance:** 4 hours, 1 privacy gate, decision log started.

**Real governance (month 2):** Add lessons, expand principles, add 2 more gates.

---

## Questions?

- **"This feels too simple"** → Simplicity is the point. Complexity kills governance.
- **"Do we need legal review?"** → Only if you're in a heavily regulated space (healthcare, finance). Nonprofits usually don't.
- **"What if we violate a principle?"** → Log it in DECISIONS.md, explain why, fix it next. That's the process.
- **"Can we skip this?"** → You can. But when you have your first conflict, you'll wish you'd started.

---

**Start today. Governance is a habit. Make it easy.**

Built by: Teams like yours, working on civic good  
From: Daanaa's full framework ([docs/AI_GOVERNANCE_FRAMEWORK.md](../docs/AI_GOVERNANCE_FRAMEWORK.md))
