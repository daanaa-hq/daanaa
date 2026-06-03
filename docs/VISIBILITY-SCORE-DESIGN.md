# Visibility Score Design

**Core principle:** Purely additive. No org is penalized for what it cannot afford.
Every point is earned by what exists — never deducted for what is missing.

**Second principle:** If Daanaa can provide a service on behalf of the org, the org earns
credit for it. Small orgs should not need a tech team to benefit from Daanaa's work.

---

## Score Components (0–100)

| Component | Points | Who provides it | How earned |
|-----------|--------|-----------------|------------|
| IRS active & not revoked | 20 | Daanaa auto | We cross-check against IRS revocation list on every update |
| Mission summary on profile | 15 | Daanaa auto | AI-generated summaries count — we made it for them |
| Donate path found & verified | 20 | Daanaa pipeline | Our donation link pipeline found and verified it |
| Verified working website | 15 | Daanaa pipeline | Pipeline crawled and confirmed live |
| Page claimed by the org | 20 | Org initiates | Org verifies via email PIN — only they can do this |
| Human-authored content added | 10 | Org adds | Mission, programs, or impact notes written by the org itself |

**Total: 100 points**

### What this means in practice

- An org that has never touched Daanaa can earn up to **55 points automatically**
  (IRS standing + mission summary + donate URL discovered + website found)
- They don't need a developer, a donor management system, or a budget
- The remaining **30 points** reward what only they can do: claim their page and tell their story
- A brand-new org with no website still starts at **20 points** (IRS standing)

### What this does NOT do

- Does not penalize orgs for being small
- Does not penalize orgs for filing a 990-N postcard
- Does not penalize orgs for not having a website
- Does not penalize churches or religious orgs for 990 exemption
- Does not compare Nano orgs against Large orgs on any metric

---

## Future Service Components (not yet built)

When Daanaa has legal and financial backing, these services add to the score:

| Service | Points | Prerequisite |
|---------|--------|-------------|
| Donation acknowledgment letter service active (IRS §170(f)(8)) | +5 | Legal counsel, processor partnerships |
| State compliance tracking enrolled | +5 | Compliance infrastructure |

These are bonus points on top of the 100 — they acknowledge the org is using Daanaa
as infrastructure, not just as a directory listing.

---

## The Lamp Journey

```
20 pts   IRS-recognized — you exist, you are real, you are indexed
35 pts   + Mission and donate path found (Daanaa's work)
50 pts   + Verified website (Daanaa's work)
70 pts   + Claim your page (your action)
80 pts   + Tell your story — human content (your action)
100 pts  Full presence — everything Daanaa can surface, you have provided
```

Every step up is an achievement. 20 is not a failure. 80 without a website is entirely possible.
The score rises with you — it never drops because of what you don't have.

---

## Implementation Notes

- `is_claimed` from org_claims table (claim_status = 'verified')
- `mission_source` NOT IN ('ai_web', 'ai_ntee', 'ai_haiku') → human mission = true
- `website_status = 'ok'` → verified website
- `donate_confidence >= 90` → verified donate path
- IRS revocation: cross-check against revoked_eins table
- Score computed on-the-fly from current DB state — no stored score field needed

---

## Not a financial score

The visibility score and the financial health score (0–100) are entirely separate.
An org with a visibility score of 80 may have no financial score (too small to score).
An org with a financial score of 95 may have a visibility score of 20 (never claimed).
These measure different things and are displayed independently.
