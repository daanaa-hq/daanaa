# Global Implementation Guide: Adapt Daanaa's Governance for Your NGO/Nonprofit

**TL;DR:** You have a team, a mission, and code to ship. Use this guide to build governance that scales with you, in your language and legal context.

---

## What You're Actually Building

You're not adopting Daanaa's platform. You're adopting **Daanaa's governance model** for your organization:

- **11 binding principles** (customize these)
- **Transparent decision log** (log why you choose what you choose)
- **Automated privacy gates** (code that enforces rules)
- **Team autonomy rules** (when engineers decide vs. leadership gate)
- **Accountability by default** (open records, auditable choices)

This works in **any country, for any civic-tech team, any nonprofit context.**

---

## Step 1: Assemble Your Team (Week 1)

You need **4 roles**. One person can do multiple.

### 1. Founder/Mission Keeper
**Who:** The person with the vision (you, probably)  
**Time:** 4 hours/week  
**Job:**
- Write the 8-12 constitutional principles for your org
- Make irreversible decisions (spending, public claims, data policy)
- Final call on principle conflicts
- Quarterly check: "Are we honoring our principles?"

### 2. Technical Lead
**Who:** Engineer or architect on your team  
**Time:** 6 hours/week  
**Job:**
- Design automated gates (what code patterns are forbidden?)
- Review privacy-touching code (faster than meetings)
- Maintain decision log (DECISIONS.md)
- Enforce "gates pass before merge"

### 3. Team Lead/Coordinator
**Who:** Project manager or senior engineer  
**Time:** 3 hours/week  
**Job:**
- Facilitate governance meetings (if questions arise)
- Make sure team understands principles (onboarding)
- Log lessons learned (LESSONS.md)
- Flag principle conflicts early

### 4. You (The Whole Team)
**Time:** 5 min per commit  
**Job:**
- Ask "which principle does this touch?"
- Write DECISIONS.md entries for non-obvious choices
- Trust the gates (they're there for a reason)
- Speak up if something feels wrong

---

## Step 2: Write Your Principles (Week 2)

### Copy Daanaa's 11 as a starting point:

```
1. Mission before growth
2. Privacy is structural
3. Trust signals are evidence-based
4. Fairness to small/underrepresented orgs
5. Don't weaponize transparency
6. Fix mistakes quickly
7. Independence is protected
8. Don't control funds (or personal data)
9. Decisions are explainable
10. AI is a tool, not authority
11. Principles strengthen over time (not diluted)
```

### Then, customize for YOUR context:

**Question:** What does success look like for your organization?

- **Finding volunteers?** → Add: "Volunteers own their time, not exploited for data"
- **Serving refugee communities?** → Add: "No data used against vulnerable populations"
- **Global fundraising?** → Add: "Donor privacy across all jurisdictions"
- **Scientific research?** → Add: "Open methods + transparent limitations"
- **Grassroots organizing?** → Add: "No algorithmic suppression of marginalized voices"
- **Supporting informal economy?** → Add: "Unregistered orgs treated with equal dignity"

### Write them in plain language:

❌ **Don't do this:**
> Principle 7: Independence shall be construed as the absence of commercial incentive structures modulating algorithmic outputs.

✅ **Do this:**
> Principle 7: No partner pays us to change how we rank organizations. Our scores come from data, not deals.

**Time required:** 4 hours with your team. If you argue for >8 hours, you don't agree on mission yet.

---

## Step 3: Set Up Git-Based Governance (Week 3)

### In your repository root, create:

**STEWARDSHIP.md** (your principles)
```markdown
# [Your Organization]'s Stewardship Commitment

[Your mission statement]

## Binding Principles

1. [Your principle #1]
2. [Your principle #2]
...

## Who Signed
- [Your name] — Founder
- [Engineer name] — Technical lead
- [Team member] — Team
- [Partner org] — Community
```

**governance/DECISIONS.md** (decision log)
```markdown
# Decisions Log

## [Date]: [What we decided]

**Reasoning:** [Why]

**Affected:** [Which code/systems]

**Reversible:** [Yes/No/Medium - matters for big changes]

---
## [Earlier date]: [Previous decision]
...
```

**governance/LESSONS.md** (what broke and how we fixed it)
```markdown
# Lessons Learned

## [Date]: [What broke]

**Root cause:** [Why]

**Fix:** [What we did]

**Preventing rule:** [How we prevent this next time]

---
```

**institution/AUTONOMY_FRAMEWORK.md** (when team decides vs. gate)
```markdown
# Team Autonomy Rules

## Team Can Decide Autonomously:
- Code that reverses easily (revert = fix)
- Bug fixes
- Performance improvements
- Tests and documentation

## Leadership Gates (Founder Approval):
- Public claims (anything users see)
- Data schema changes
- Spending >$X
- New data collection

## Automated Gates (Code Blocks Commit):
- Credentials in code
- User data in logs
- Config mistakes
- Boundary violations

## Community Gates (Community Review):
- Algorithm changes that affect users
- New data retention policy
- Changes to public methodolody
```

### Set up Git hooks:

**`.git/hooks/pre-commit`** (runs before every commit)
```bash
#!/bin/bash
# Runs privacy gates, ensures DECISIONS.md touched for significant changes
bash scripts/privacy_check.sh || exit 1
```

**GitHub template** (in `.github/pull_request_template.md`)
```markdown
# What changed?
[Brief description]

# Why?
[Reference DECISIONS.md if non-obvious]

# Principle check
- [ ] I've considered which principles this touches
- [ ] This aligns with our stewardship commitment
- [ ] DECISIONS.md is updated (if this is non-obvious)

# Legal/Privacy
- [ ] No credentials added
- [ ] No user data in logs
- [ ] Complies with [GDPR/LGPD/local law]
```

**Time required:** 2 hours. Copy Daanaa's format, edit names.

---

## Step 4: Build Automated Gates (Weeks 4-5)

### Start with ONE gate: "No credentials in code"

**File:** `scripts/privacy_check.sh`

```bash
#!/bin/bash
# Catches credentials before they reach GitHub

PATTERNS=(
  "api_key"
  "secret"
  "password"
  "token"
  "private_key"
)

for pattern in "${PATTERNS[@]}"; do
  if git diff --cached | grep -i "$pattern" | grep -v ".md\|.example"; then
    echo "❌ Blocked: Found '$pattern' in staged code"
    exit 1
  fi
done

echo "✅ Passed: No credentials detected"
exit 0
```

### Add 2-3 gates over the next month:

1. **Credentials** (week 1) — blocks api_key, secret, password
2. **User data in logs** (week 2) — blocks user_id, email, phone in logging calls
3. **Config mistakes** (week 3) — blocks prod secrets in code

**Don't overdo it.** 3-5 gates is enough. More gates = more false positives = team ignores them.

**Time required:** 4 hours for first gate, 2 hours each for subsequent ones.

---

## Step 5: Onboard Your Team (Week 6)

### Team meeting (30 min):

1. **Share STEWARDSHIP.md** — "Here's what we believe"
2. **Show AUTONOMY_FRAMEWORK.md** — "Here's who decides what"
3. **Demo a gate** — "This code is blocked, here's why"
4. **Make it safe to ask** — "Questions? Good. The framework only works if we use it."

### For each new team member:

- [ ] Read STEWARDSHIP.md (10 min)
- [ ] Read AUTONOMY_FRAMEWORK.md (10 min)
- [ ] Do a code review together (they see gates in action)
- [ ] They make a small commit (experience DECISIONS.md requirement)
- [ ] Done—they're in the culture

**Time required:** 1 hour per person.

---

## Step 6: Test It Under Pressure (Weeks 7-8)

**This is the real test.** Something you want to ship will fail a gate. Here's what happens:

### Scenario: "We need to log user email to debug a bug"

**Engineer says:** "We need user_email in logs, just temporarily"

**Gate blocks it.** Your privacy_check.sh rule catches it.

**Leadership decision:**
- ❌ Option A: Bypass the gate (breaks governance, never do this)
- ✅ Option B: Update DECISIONS.md explaining exception, make it temporary (log an entry in LESSONS.md to fix this later)
- ✅ Option C: Find another debug method (log session ID instead)

**Outcome:** You've just proven your governance works. Celebrate.

### Another scenario: "New partner wants access to donor names"

**This touches Principle #8 (don't control funds).**

**Process:**
1. Engineer flags it in a PR
2. Tech lead asks founder
3. Founder gates it: "Not without donor consent"
4. Decision logged in DECISIONS.md
5. PR updated with solution: "Offer opt-in donor name sharing"

**This is when culture becomes real.**

---

## Regional Legal Compliance (Add as Needed)

### Europe (GDPR, local data laws)
```markdown
# Compliance Gate: GDPR

Before shipping data-touching code:
- [ ] Data minimization: collect only what's necessary
- [ ] Explicit consent: did users opt in?
- [ ] Data purpose: can we articulate the purpose?
- [ ] Retention: when do we delete this?
- [ ] Legal review: is this cross-border compliant?
```

### Global South (limited infrastructure)
```markdown
# Compliance Gate: Accessibility

- [ ] Feature works on 2G/3G connection
- [ ] Offline-first design (sync when internet available)
- [ ] Data footprint is small (<1MB)
- [ ] Doesn't require constant connectivity
```

### Any Country with Government Data Requests
```markdown
# Data Request Protocol

If government requests user data:
1. Log the request (timestamp, details)
2. Notify users (if not legally prohibited)
3. Provide minimal data (nothing beyond request)
4. Don't create new data to comply
5. Log the decision (LESSONS.md)
```

---

## What Happens at 6 Months

### Check 1: Are principles holding?
Read DECISIONS.md. Every decision should explain how it honors (or respectfully questions) your principles.

### Check 2: Are gates working?
Count how many times a gate caught something. If zero: too permissive. If >5/week: too strict.

### Check 3: Is the team culture real?
New person joining should hear "read STEWARDSHIP first" before "hello."

### Check 4: Any conflicts?
Are principles ever in conflict? (E.g., "be transparent" vs. "protect vulnerable people.") Document this—it's a real tension.

---

## What Happens at 12 Months

### Annual Principle Review

Ask the team (and your community):
- Are these principles still right for us?
- What did we learn that should change principle X?
- Did any principle hold us back? Was that worth it?

**You can update principles, but:**
- Make it explicit (version number, date, change log)
- Explain why (in DECISIONS.md)
- Get founder + team alignment

---

## Staffing Cost

| Role | Time | Annual Cost (salary basis) |
|------|------|---------------------------|
| Founder/Mission Keeper | 4 h/week | Included (founder time) |
| Technical Lead | 6 h/week | ~$8-12K (if not existing role) |
| Team Lead/Coordinator | 3 h/week | ~$4-6K (or existing PM) |
| Whole Team | 5 min/commit | Built in |
| **Total** | **13 h/week** | **$12-18K/year** or **Free** (if all existing roles) |

**Bottom line:** This is cheaper than a compliance department. Easier than a legal review for every decision. And it actually works.

---

## Common Mistakes (Don't Make These)

### ❌ Mistake 1: "We'll follow principles after we ship"
**What happens:** You ship. You say "we promise to be good." You're not.  
**Fix:** Commit principles BEFORE first deploy. Gates on day 1.

### ❌ Mistake 2: "Principles are inspiring but not binding"
**What happens:** Someone violates principle, says "we'll fix it later." You don't.  
**Fix:** AUTONOMY_FRAMEWORK makes some decisions requir founder approval. That's the binding part.

### ❌ Mistake 3: "Only security/legal people care about gates"
**What happens:** Engineers bypass gates. Gates become useless.  
**Fix:** Make the whole team own it. Everyone asks "does this violate a principle?"

### ❌ Mistake 4: "We'll add the log entries later"
**What happens:** DECISIONS.md goes stale. No one learns why past choices were made.  
**Fix:** DECISIONS.md entry is part of PR review. No merge without it (for non-trivial changes).

### ❌ Mistake 5: "Our context is so different, principles don't apply"
**What happens:** You skip governance. You make mistakes. You wish you'd had governance.  
**Fix:** Adapt principles to your context, don't skip them.

---

## Your Next Step

1. **Copy STEWARDSHIP.md** (from this repo) as template
2. **Your team** writes custom principles (4-hour meeting)
3. **Create DECISIONS.md** in your repo
4. **Add first privacy gate** (3-hour engineering task)
5. **Onboard team** (30-min meeting)
6. **Ship with governance** (from day 1)

---

## Questions?

- **"Does this slow us down?"** No. It catches mistakes that would slow you down anyway.
- **"What if we disagree on a principle?"** Good. Disagreement means you're thinking. Resolve it, log it, move on.
- **"Can we use this for a for-profit?"** Yes, adapt it. For-profit civic tech (benefit corp, etc.) works too.
- **"We're a small org, do we need this?"** Even more. Governance is how small teams punch above their weight.
- **"What if government requests data?"** DECISIONS.md + transparency = you're protected. Gives you a decision trail.

---

## Resources

- **Daanaa's full example:** [STEWARDSHIP.md](../STEWARDSHIP.md), [governance/DECISIONS.md](../governance/DECISIONS.md)
- **Framework explanation:** [docs/AI_GOVERNANCE_FRAMEWORK.md](../docs/AI_GOVERNANCE_FRAMEWORK.md)
- **Team story (how we did it):** [TEAM_STORY.md](../TEAM_STORY.md)
- **This repository:** Copy what works, ignore what doesn't

---

## License

Adapt freely. Improve it. Share your improvements. This is open governance for a global community.

**Daanaa's core model is:** Mission → Principles → Decisions → Accountability

**Your model is:** Your mission → Your principles → Your decisions → Your accountability

Make it yours.

---

**Built by:** Teams like yours, working in civic space, deciding to do governance right.

**For:** NGOs, nonprofits, civic-tech platforms, volunteer networks, grant finders—anywhere trust matters.

**This starts with YOU.**
