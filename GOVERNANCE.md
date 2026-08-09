# Governance Framework

Daanaa is built on an open AI governance model. **This is where we make decisions transparent.**

## Start Here

The core innovation: governance is architecture, not policy.

We embed principles in code (privacy gates), structure decisions (founder gates), log everything (DECISIONS.md), and give Claude autonomy only on reversible work.

## The 11 Binding Principles

Read [STEWARDSHIP.md](STEWARDSHIP.md) in full.

Quick version:
1. **Mission before growth** — Growth can't override helping people give better
2. **Privacy is core** — No donor tracking, no public giving activity
3. **Evidence-based signals** — Every score/badge from real data only
4. **Small orgs deserve fairness** — Never disadvantage for being small
5. **Don't weaponize transparency** — Inform responsibly, no shame language
6. **Mistakes corrected quickly** — Accuracy > ego
7. **Independence protected** — No money can influence rankings
8. **Never control donor funds** — Hand-off only, never merchant of record
9. **Decisions explainable later** — Log why for future team members
10. **AI is a tool, not authority** — Humans accountable for AI outputs
11. **Principles not weakened** — Changes documented with reasoning

## How We Decide

See [institution/AUTONOMY_FRAMEWORK.md](institution/AUTONOMY_FRAMEWORK.md):

**Claude autonomous on:** Reversible code, performance tuning, bug fixes  
**Founder gates on:** Trust signals, public claims, spending, schema changes  
**Codex verifies:** Architecture, security, regressions  

## Privacy Enforcement (Automated)

See [institution/PRIVACY_GATES.md](institution/PRIVACY_GATES.md):

Every commit must pass 8 gates:
- Token pattern detection
- Log leakage detection
- Env var fallback detection
- Exfiltration vector detection
- Data boundary checks
- Config file safety
- PRIVACY-INVARIANTS compliance
- Entity firewall

**Exit code 0 = approved. Non-zero = blocked. No exceptions.**

## Decision Log

See [DECISIONS.md](DECISIONS.md):

Every non-obvious choice is logged:
- What we chose
- Why we chose it
- What we rejected
- Trade-offs accepted

This becomes your institutional memory.

## For Code Review

Your cousin reviewing this project should read in this order:

1. **This file** (GOVERNANCE.md) — 5 min
2. **[STEWARDSHIP.md](STEWARDSHIP.md)** — 10 min (principles)
3. **[institution/AUTONOMY_FRAMEWORK.md](institution/AUTONOMY_FRAMEWORK.md)** — 10 min (how Claude works)
4. **[DECISIONS.md](DECISIONS.md)** — scan for patterns (trust how we think)
5. **Then review code** — see it all in context

## Why This Matters

**Governance is not bureaucracy. Governance is infrastructure for trust.**

When you see Daanaa, you see:
- ✅ We govern AI explicitly
- ✅ Principles are in code, not just words
- ✅ Every decision is logged and explainable
- ✅ Privacy is automated, not hoped for

---

**Next:** [STEWARDSHIP.md](STEWARDSHIP.md) for the full principles.
