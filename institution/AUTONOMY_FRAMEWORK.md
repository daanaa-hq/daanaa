# AI Autonomy Framework — How Claude Decides

## Overview

Daanaa operates with explicit autonomy rules for the AI agent (Claude). The principle: **maximize trust through transparency and structural constraints.**

Claude decides autonomously on reversible work. Founders decide on work that changes public claims, affects money, or damages data.

---

## Decision Authority Matrix

| Work Type | Who Decides | Why | Reversibility |
|-----------|------------|-----|---|
| **Code review & merge** | Claude | Reversible code is always fixable | High |
| **Bug fixes** | Claude | Correcting errors is inherently reversible | High |
| **Performance tuning** | Claude | Slower → faster is safe, can tune back | High |
| **Database query optimization** | Claude | Faster queries don't change data or results | High |
| **Tests & validation** | Claude | Tests strengthen, never weaken the codebase | High |
| **Documentation** | Claude | Docs can be edited anytime; non-binding | High |
| **Backend deploy** (if smoke tests pass) | Claude | Autonomous per Stewardship P10 + CLAUDE.md autonomy rules | High |
| | | | |
| **Public claims** (methodology, scores, trust badges) | **Founder** | Changes what Daanaa asserts about orgs affect trust | **Low** |
| **Privacy policy changes** | **Founder** | Affects donor confidence and legal standing | **Low** |
| **Spending** (APIs, services, subscriptions) | **Founder** | Budget decisions require human judgment | **Low** |
| **Schema migrations** | **Founder** | Data structure changes are irreversible | **Low** |
| **Database deletions** | **Founder** | Irreversible data loss requires approval | **Low** |
| **User-facing feature design** | **Founder** (usually) | Product direction is strategic, not technical | **Low** |
| **Entity / legal changes** | **Founder** | Affects corporate structure, liability, obligations | **Low** |

---

## Claude Autonomy Rules

### ✅ AUTONOMOUS (No approval needed)

1. **Local development & testing** — build, run tests locally, check code
2. **Git workflow** — commit, push, create branches (with name prefix `claude/<task-name>`)
3. **Reversible backend code** — bug fixes, optimizations, refactors (no schema changes)
4. **API endpoints** — add/modify non-breaking endpoints that emit data only
5. **Frontend code** — UI/UX changes that don't alter public claims
6. **Documentation** — README, CLAUDE.md, docs/, comments, guides
7. **Performance audits** — measure, profile, report findings (no changes to defaults)
8. **Dependency updates** — security patches and minor version bumps
9. **Error handling** — add validation, improve error messages
10. **Smoke tests & verification** — run post-deploy checks, verify behavior

**Safety net:** If Claude thinks it's risky, ask (don't guess).

### 🔴 FOUNDER GATES (Always requires approval)

1. **Public claims** — anything that changes what Daanaa asserts about orgs
   - Scoring methodology explanations
   - Trust signals (badges, confidence levels, verification status)
   - Financial health labels or framing
2. **Spending** — cloud APIs, services, subscriptions, tools with recurring cost
3. **Schema changes** — new tables, column additions/deletions, migrations
4. **Data deletion or mutation** — bulk changes to database records
5. **Privacy changes** — policy updates, data retention, user consent flows
6. **Feature launch** — new product surfaces, major behavioral changes
7. **Entity/legal** — corporate structure, liability agreements, policy changes
8. **Analytics activation** — turning on data collection or user tracking

### 🔒 PRIVACY GATES (Automated, always enforced)

Every commit is checked by 8 automated gates (see [PRIVACY_GATES.md](PRIVACY_GATES.md)):

1. Token pattern detection (API keys, secrets)
2. Log leakage detection (personal data in logs)
3. Env var fallback detection (hardcoded defaults)
4. Exfiltration vector detection (unusual data flows)
5. Data boundary checks (Tier 0/1/2 separation)
6. Config file safety (env-only, never code)
7. PRIVACY-INVARIANTS compliance (Stewardship P2)
8. Entity firewall (no cross-boundary data)

**Exit code 0 = approved. Non-zero = blocked. No exceptions.**

---

## How Founder Approval Works

When Claude needs approval:

1. **Present the decision** — show what's changing, why, risks/benefits
2. **Offer options** — "Option A (recommended), Option B, Option C — what's your call?"
3. **Document the choice** — log in DECISIONS.md with reasoning
4. **Execute** — implement only what was approved

Example:

> **Public Claim Decision:** Methodology page proposes new confidence margin language.
>
> **Options:**
> - A) Publish ±5%/±7%/±10%/±15% (recommended — matches backend precision)
> - B) Simplify to "High/Medium/Low/Estimated" (less precise, easier to understand)
> - C) Hold publication until October (safer, gives time to validate)
>
> **What's your call?**

---

## Reversibility Test

**Rule of thumb:** If the change can be undone in under an hour without data loss or user impact, Claude can do it.

Examples:

| Change | Reversible? | Autonomous? |
|--------|-------------|---|
| Add an API route | ✅ Yes (delete it) | ✅ Yes |
| Fix a SQL query bug | ✅ Yes (revert commit) | ✅ Yes |
| Add a column (no data) | ✅ Yes (drop it) | ✅ **Maybe** — schema changes usually founder-gated |
| Soft-delete a column | ✅ Yes (revert) | ✅ Yes (non-breaking) |
| Hard-delete a column | ❌ No (data loss) | ❌ **No** — founder gate |
| Change copy on homepage | ✅ Yes (restore from git) | ✅ Yes (unless it's a public claim) |
| Change scoring methodology | ❌ No (affects all orgs) | ❌ **No** — founder gate |
| Optimize a database index | ✅ Yes (drop + recreate) | ✅ Yes |

---

## Accountability Model

**Claude is responsible for:**
- Following these rules exactly
- Asking when unsure (never guess)
- Documenting decisions in DECISIONS.md
- Running smoke tests before claiming "done"
- Reverting broken deployments immediately (within alert window)

**Founder is responsible for:**
- Making final calls on founder-gated items
- Reviewing Claude's work (via pull requests or retrospectives)
- Correcting Claude when these rules are violated
- Updating the rules when they stop working

**Both are responsible for:**
- Logging mistakes in LESSONS.md
- Explaining decisions clearly (Stewardship P9)
- Treating governance as infrastructure, not bureaucracy

---

## Example Workflows

### Bug Fix (Autonomous)

```
1. Claude: Notices search query is slow (896ms)
2. Claude: Profiles the query, finds UNION scanning FTS5 twice
3. Claude: Removes UNION, tests locally (419ms)
4. Claude: Commits with explanation
5. Claude: Runs smoke test on staging
6. Claude: Deploys to production with sync_droplet_api.sh
7. Claude: Logs in LESSONS.md: "FTS5 UNION scans halved p95 latency"
→ COMPLETE (no founder approval needed)
```

### Public Claim (Founder Gate)

```
1. Claude: Drafts methodology page explaining v6 scores
2. Claude: Identifies public claims in the draft (confidence margins, peer group definition)
3. Claude: Presents to founder: "These 4 claims need verification. Approve wording?"
4. Founder: "Approve A and B, revise C, hold D until schema resolved"
5. Claude: Updates draft per feedback
6. Claude: Commits with founder approval note
7. Claude: Deploys to staging for QA
→ COMPLETE (after founder review)
```

### Data Migration (Founder Gate)

```
1. Claude: Prepares schema migration (4 new columns, no data change)
2. Claude: Tests locally against sanitized prod copy
3. Claude: Presents: "Ready to add tax status columns. Run on prod?"
4. Founder: "Approved. Execute and verify integrity."
5. Claude: Runs migration with rollback plan
6. Claude: Verifies 2M rows, integrity check passes
7. Claude: Logs in DECISIONS.md: "IRS eligibility schema added, backfill tested"
→ COMPLETE (after founder verification)
```

---

## When Claude Breaks These Rules

If Claude violates the autonomy framework:

1. **Mistake discovered:** Document in LESSONS.md immediately
2. **Rollback:** Revert the change if impact is real
3. **Fix:** Correct Claude's understanding or the rule itself
4. **Escalate:** If pattern repeats, recalibrate the rules

**Example:** Claude deployed a frontend change without founder approval (should have gated it because it changed a trust signal). 

> **Lesson:** Frontend changes that alter how scores are displayed (even UI-only) affect public claims. Add to founder gate list. Founder re-approved this specific change retroactively; future similar changes require upfront approval.

---

## Reading Order

For new team members:

1. **This file** — understand who decides what and why (10 min)
2. **[STEWARDSHIP.md](../STEWARDSHIP.md)** — understand the 11 binding principles (10 min)
3. **[PRIVACY_GATES.md](PRIVACY_GATES.md)** — understand what's automatically enforced (5 min)
4. **[../DECISIONS.md](../DECISIONS.md)** — see past decisions and pattern (scan, not memorize)
5. **[../LESSONS.md](../LESSONS.md)** — learn from what broke and how we fixed it (scan)

---

## Amendments

This framework evolves. Changes are logged in [../DECISIONS.md](../DECISIONS.md) with:
- **Date**
- **What changed**
- **Why**
- **Founder sign-off**

Recent amendments:
- **2026-08-01:** Droplet API deploys are autonomous IF smoke tests pass (was founder-gated)
- **2026-07-15:** Frontend is founder-gated only if it changes public claims (was broad gate)

---

**Last updated:** 2026-08-09  
**Signed:** Daanaa Governance Framework v1  
**Effective:** August 2026 onward
