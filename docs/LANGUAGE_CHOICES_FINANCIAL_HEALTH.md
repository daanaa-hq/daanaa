# Financial Health Signal Language: Why "NEED_SUPPORT" Not "CAUTION"

**Effective:** 2026-07-15  
**Authority:** Stewardship Commitment Principle #5 (Transparency without Weaponization)  
**Applies to:** All user-facing descriptions of the `health_signal` variable

---

## The Principle

> We do not weaponize transparency. The goal of Daanaa is to inform responsibly, not to shame organizations publicly.

Stewardship Principle #5 recognizes that language shapes behavior. A nonprofit labeled "CAUTION" is one a potential supporter worries about. A nonprofit labeled "NEED_SUPPORT" is one that invites action.

The underlying data is identical. The choice of how to frame it is a decision about whether our platform encourages giving or discourages it.

---

## The Structural Truth About Nonprofit Finances

Nonprofits are **designed to run lean.**

- A for-profit company hoards cash reserves as a sign of health.
- A nonprofit that hoards cash is failing its mission — the money should be in programs, not warehouses.
- A nonprofit with "low" reserves (2–6 months operating expenses) is **spending on mission,** not sitting on capital.
- A nonprofit with very low reserves (<1 month) may face real challenges, but the cause is usually **mission growth outpacing fundraising**, not mismanagement.

The IRS recognizes this. Best-practice nonprofit management guides consider 2–6 months reserves healthy. The absence of 12+ months reserves is not a red flag; it is structural to the nonprofit model.

---

## Why "CAUTION" Fails

The label "CAUTION" implies warning, risk, and alarm. It frames a normal nonprofit operating pattern as abnormal. To a supporter who has never worked in the nonprofit sector:

- "CAUTION" reads as: _"This org might fail; be careful."_
- The impulse: _"I'd rather give to a safer org."_
- The outcome: **fewer donations, even though the org is structurally healthy.**

This is weaponized transparency. We are using data to discourage giving, not inform it.

---

## Why "NEED_SUPPORT" Works

The label "NEED_SUPPORT" acknowledges the structural reality: this org is doing its mission work and needs more supporters to grow it further. To the same supporter:

- "NEED_SUPPORT" reads as: _"This org is mission-focused and growing; they'd benefit from your help."_
- The impulse: _"I can make a tangible difference here."_
- The outcome: **more informed giving, aligned with how nonprofits actually work.**

This is transparency in service of mission. We are using data to encourage informed, thoughtful giving.

---

## What the Data Shows

The financial health signal comes from:
- **Reserve ratio:** months of operating expenses in the bank
- **Operating margin:** net revenue as a % of expenses
- **Revenue stability:** year-over-year volatility
- **Funder diversity:** concentration in top donor(s)

**Three buckets:**
1. **HEALTHY:** 6+ months reserves, positive operating margin >5%, stable revenue, diversified funding
2. **STABLE:** 3–6 months reserves OR healthy margins, OR solid diversification; handling mission work steadily
3. **NEED_SUPPORT:** <3 months reserves OR margin <2% OR concentrated funding OR growth outpacing reserves

All three are **normal states** for different-sized, different-stage nonprofits. None imply failure. The label simply says:
- **HEALTHY:** You have room to grow and invest.
- **STABLE:** You're managing well; you're keeping the mission funded.
- **NEED_SUPPORT:** More supporters can help you grow or stabilize your work.

---

## Implementation

### In API Responses

The `/api/nonprofit/<ein>/financial-health` endpoint returns `overall_signal: "NEED_SUPPORT"` (or HEALTHY/STABLE).

The narrative appended to each org's financial context on the detail page reads:

> **NEED_SUPPORT:** "Your organization is ready for more supporters. Many organizations in your funding model and size range are actively seeking supporters like you. Your peer view shows how similar organizations reach supporters, and your profile tools help more people discover your work."

This is not shame language. It is action language. It is true.

### In Database

`nonprofit_financial_health.health_signal` is a TEXT field with CHECK constraint:
```sql
health_signal IN ('HEALTHY', 'STABLE', 'NEED_SUPPORT')
```

(There is no 'CRISIS' signal. See below.)

### Never "CRISIS"

The worst bucket is **NEED_SUPPORT**, never "CRISIS." Why?

1. **One year of data is not enough to declare crisis.** The `merit_health_signal_v5` scorer deliberately caps at NEED_SUPPORT because a single year of negative margin can be a bad fundraising year, a capital campaign pause, or a planned deficit for growth. It is not an org failing.

2. **Shame labels discourage giving.** A founder or board might see an org labeled "CRISIS" and think "let's hide this" or "we don't want to appear this desperate." The org goes dark. Exactly the opposite of what transparency should enable.

3. **Transparency is structural.** Daanaa's role is to surface the data and context, then trust supporters to make informed decisions. If an org is truly in crisis, that will show in its completeness (missing recent filings), not in a binary label we impose.

---

## Verification

This language is verified in two places:

1. **Code:** `daanaa_api.py:_dashboard_financial_narrative()` returns the signal-appropriate narrative. Test: `tests/test_financial_health.py` checks that NEED_SUPPORT orgs receive the action-framed narrative.

2. **Data:** `nonprofit_financial_health` table contains zero rows with `health_signal = 'CAUTION'` (migrated to NEED_SUPPORT, 2026-07-15).

3. **User-facing:** Every org detail page and peer comparison shows the NEED_SUPPORT label alongside its peer percentile, making the context clear: "you're in the bottom quartile of reserves, here's how to grow them, here's what peers are doing."

---

## FAQ

**Q: Doesn't this hide financial problems?**

A: No. The reserves/margin/diversity data is always shown (numbers, trends, peer rank). We are not hiding anything; we are framing it with language that aligns giving with truth. A supporter seeing "NEED_SUPPORT, 2 months reserves, peers average 4 months" gets full context and can make an informed choice.

**Q: What if an org is genuinely failing?**

A: A failing org will show incomplete filings, missing contact, revoked status, or (if claimed by the org) an honest description of transition. The health signal is one data point, not a verdict. Daanaa surfaces all the pieces; supporters decide.

**Q: Is this different from v4 or v5 scoring?**

A: No. The underlying scores (reserve ratio, operating margin, peer rank) are identical. Only the label and narrative changed. (v4 had other labels like "Strong/Stable" on a different scale; v5 is "HEALTHY/STABLE/NEED_SUPPORT"; both are now using the v5 vocabulary with NEED_SUPPORT.)

---

## References

- **Stewardship Commitment:** `STEWARDSHIP.md` Principle #5
- **Methodology:** `docs/RESEARCH.md` (financial health scoring section)
- **Implementation:** `scripts/populate_financial_health_full.py` and `daanaa_api.py`
- **Migration:** `migrations/019_health_signal_language_update.sql`
- **Decision Log:** `DECISIONS.md` (2026-07-15 entry)
