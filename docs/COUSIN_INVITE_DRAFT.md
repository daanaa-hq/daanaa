# Draft Email for Your Cousin

---

**Subject:** You asked about the AI governance work — it's now public

Dear [Cousin],

You asked me to show you the governance work once it was ready. It is now.

**[ADD GITHUB LINK HERE]**

---

## What This Is

Daanaa is a nonprofit-discovery platform (like a search engine for where to give). We index 2M+ 501(c)(3) organizations, assess financial health using public IRS data, and help donors make informed decisions.

**The part I want you to see:** It's built under a Founding Stewardship Commitment with 11 binding principles, and every single one is implemented in code, not just words.

---

## The Governance Work (15 min read)

Start with these three files. They're the core:

1. **GOVERNANCE.md** (5 min) — How we make decisions
   - Founder gates on public claims, spending, schema changes
   - Claude (the AI) is autonomous on reversible code only
   - Decision matrix showing who decides what and why

2. **institution/AUTONOMY_FRAMEWORK.md** (10 min) — When the AI decides
   - Reversible work (bug fixes, performance tuning, tests) = Claude autonomous
   - Irreversible work (public claims, spending, data changes) = Founder gates
   - Why this structure protects trustworthiness

3. **institution/PRIVACY_GATES.md** (10 min) — Proof it's enforced
   - 8 automated privacy gates on every commit
   - Code examples showing what's blocked and why
   - Exit code 0 = approved, non-zero = blocked (no exceptions)

---

## Why This Matters

Most platforms say "we respect privacy" and "we're transparent." This one **doesn't say it — the code enforces it.**

Every commit runs through 8 automated gates:
- ✅ Token pattern detection (no API keys in code)
- ✅ Log leakage detection (no donor data in logs)
- ✅ Env var safety (no hardcoded secrets)
- ✅ Exfiltration vectors (no data leaking to external services)
- ✅ Data boundaries (Tier 0 private / Tier 1 org / Tier 2 public)
- ✅ Config safety (secrets in environment only)
- ✅ Privacy invariants (donor PII never exposed)
- ✅ Entity firewall (Daanaa platform data stays separate from consulting business)

If a commit violates even one gate, it's rejected. No exceptions.

---

## The 11 Principles

Everything is built on these (from STEWARDSHIP.md):

1. **Mission before growth** — Helping donors give better, not scaling at all costs
2. **Privacy is core** — No donor tracking, no public giving activity
3. **Trust signals are evidence-based** — Scores and badges from real data only
4. **Small orgs deserve fairness** — No size-based disadvantaging
5. **Don't weaponize transparency** — Inform responsibly, no shame language
6. **Mistakes corrected quickly** — Accuracy over ego
7. **Independence protected** — No money can influence rankings
8. **Never control donor funds** — Hand-off model only
9. **Decisions explainable later** — Full decision log (DECISIONS.md)
10. **AI is a tool, not authority** — Humans accountable for AI outputs
11. **Principles not weakened** — Changes documented with reasoning

---

## How AI Fits In

This is the part I'm most proud of. Most companies say "we use AI responsibly." We actually define what that means:

- **Claude autonomous on:** Bug fixes, performance tuning, testing, documentation, reversible code
- **Claude asks permission on:** Public claims, spending, schema changes, feature launches
- **Claude never touches:** Donor/org secrets, data deletions, anything irreversible

So when you see code in the repo, you know: If it's reversible, Claude did it (with full transparency in git history). If it's irreversible, a human made the call.

---

## What's Live

- ✅ 2.05M nonprofits indexed
- ✅ v6 financial health scoring (99.83% coverage)
- ✅ Methodology documented with confidence margins
- ✅ Privacy gates enforced on every commit
- ✅ Decision log (why every choice was made)
- ✅ Lesson log (what broke and how we fixed it)

Going live October 1 on daanaa.org.

---

## How to Read It

**5-minute version:**
1. README.md (governance-first positioning)
2. GOVERNANCE.md (decision authority matrix)

**30-minute version:**
Add STEWARDSHIP.md + AUTONOMY_FRAMEWORK.md

**Full audit (1-2 hours):**
Add PRIVACY_GATES.md + DECISIONS.md + LESSONS.md + any code deep dives

---

## I'd Love Your Feedback

Review the governance structure and let me know:
- Is it clear how decisions are made?
- Does the autonomy framework make sense?
- What would make you trust it more?
- Are there gaps?

This goes live publicly in a few weeks. Your eyes on it before then would be invaluable.

---

Best,  
[Your Name]

P.S. — If you want to run the code locally or ask technical questions, let me know. I can walk you through the architecture.
