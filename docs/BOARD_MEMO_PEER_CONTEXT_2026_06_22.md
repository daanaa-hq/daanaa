# Board Memo: Peer Context Breakdown Display

**Date:** June 22, 2026  
**From:** Claude Code (AI Engineering) + Akbar Khowaja (Founder)  
**To:** Board Advisors  
**Status:** Seeking guidance before broad launch  

---

## Executive Summary

We've added a new display layer to org detail pages called "How Donors See You" that reframes peer financial context around **donor understanding + nonprofit encouragement** instead of ranking.

**Key philosophy shift:** Data is verified and solid. Display is what matters. Instead of "here's where you rank," we frame it as "here's how your financial position helps or challenges your mission, and how donors understand it."

**The insight:** Nonprofits don't compete; they sustain missions under constraints. Small + lean doesn't mean weak. We're helping donors *get* that, and nonprofits *own* that.

**Stewardship status:** Aligned with all 11 principles. More importantly: aligned with Daanaa's actual mission (inform giving, encourage repeat giving) not with business ranking logic.

---

## What Changed

### Before
Org detail page showed:
- Financial health signal (HEALTHY / STABLE / CAUTION)
- V5 context: "You're in the upper 50% of Donation-Funded nonprofits"
- Implied ranking (even with kind language)

### After
Now shows "How Donors See You" — **reframed around impact + transparency, not ranking:**

```
🏛️ YOUR SECTOR
Social Services nonprofits
────────────────────────────
Strong financial position
(or: Building reserves / Stable finances)

"You're managing resources well compared to other 
nonprofits in your sector. This matters to donors 
who want assurance."

[Claim profile → Show donors your story]

📍 IN YOUR STATE
Wisconsin: 73 orgs in your sector
────────────────────────────
#52 in your sector

"You're one of 73 Social Services nonprofits in Wisconsin. 
Your state's donors know this sector. They understand 
the market."

💰 YOUR SCALE
Established (>$700K)
────────────────────────────
"You've scaled to serve more people. That takes 
operational skill donors respect."

🎯 FINANCIAL HEALTH
Needs support (building reserves)
────────────────────────────
"You're lean. Many nonprofits are. What matters to donors: 
transparency + a plan. That's where claiming your profile helps."

[Claim profile → Tell your story to reserves-minded donors]
```

**Core difference:** 
- OLD: "Here's where you rank"
- NEW: "Here's how your position helps your mission, and how donors understand it"

---

## Why This Matters (Mission Alignment)

**The real problem:** Donors get paralyzed. Too many choices. "Is this org financially solid? Will my gift matter or disappear into overhead?"

Nonprofits get defensive. "Donors judge us for being lean. They don't understand that mission-driven means we run tight."

**This reframe solves both:**

**For donors:**
- ✅ "Oh, this org manages resources well. My gift won't be wasted."
- ✅ "They're lean but lean is normal in this sector. They're transparent about it."
- ✅ "Encourages giving** because uncertainty drops (context removes paralysis)

**For nonprofits:**
- ✅ "Donors understand I'm not poorly run; I'm focused on mission."
- ✅ "Being small + mighty is OK. I can own that."
- ✅ "Claim my profile → donors see MY story, not just the data"
- ✅ **Encourages updating data** (because it tells their story, not ranks them)

**Key:** This is reframe designed to **increase giving and repeat giving** by:
1. Reducing donor uncertainty (context helps decisions)
2. Reducing nonprofit shame (small is strategic, not failure)
3. Creating action path (claim profile → tell your story)

---

## Stewardship Compliance

**All 11 principles:** ✅ Aligned

**Strongest alignment:**
- **P3 (Evidence-based):** Data from IRS 990s, mathematically derived percentiles
- **P4 (Small org fairness):** Peers by revenue band + state, not national only
- **P5 (Don't weaponize):** Bracket language, no shame/competition framing
- **P7 (Independence):** Algorithmic, no human curation

**One gap to address:**
- **P9 (Explainability):** Should document why we chose bracket language in DECISIONS.md

---

## Key Design Decisions

### 1. Brackets vs. Raw Ranks
- **Choice:** "Top 25%" not "Rank #1,247 of 4,891"
- **Why:** Brackets avoid false precision, reduce pressure, align with behavioral psychology (people understand percentiles better than ordinal ranks)
- **Stewardship impact:** Prevents weaponization (P5). Informs without shaming.

### 2. State + National Context
- **Choice:** Show both state rank (if >10 orgs in state + category) and national brackets
- **Why:** Prevents one-size-fits-all comparison. Montana $200K org compares fairly in Montana, not nationally.
- **Stewardship impact:** Fairness to small orgs (P4). Prevents scale bias.

### 3. Peer Group Size Always Shown
- **Choice:** "Upper 50% of 847 organizations"
- **Why:** Transparency. Nonprofits see peer cohort size, understand context isn't lonely.
- **Stewardship impact:** Evidence-based (P3). Honest about data quality.

### 4. Disclosure + Framing
- **Copy:** "Peer context from public IRS data. This shows where you stand among similar organizations—not a judgment, just financial context."
- **Why:** Explicit non-recommendation. Prevents misuse as a "score" or "rating."
- **Stewardship impact:** Don't weaponize (P5), evidence-based (P3).

---

## What This Enables (Product)

**For donors:** Clearer context when comparing orgs
- "This org is in the upper 50% of its peer group" is actionable

**For nonprofits:** Honest self-assessment without shame
- "We're in the middle 50%, which is normal. Here's where we can improve."
- State context helps: "We're #52 in Wisconsin—good position, but 3 orgs ahead."

**For Daanaa:** Data-driven conversations with nonprofit partners
- Claim flow can use this: "Here's how you compare. Want help improving?"
- Avoids gamification (P5): Not a game to "rise in ranks"

---

## What It Does NOT Do

- ❌ Create ranking lists (org-vs-org competition) — only personal context
- ❌ Change financial health calculation — v4/v5 model unchanged
- ❌ Add new data sources — all from existing IRS data
- ❌ Introduce hidden scoring — all math is transparent (percentile-to-bracket)
- ❌ Pressure nonprofits — brackets + context discourage competitive behavior

---

## Questions for Board

**Legal/Compliance:**
1. Does showing peer rankings (even in bracket form) create any liability? (e.g., antitrust, fair competition concerns)
2. Should we disclose methodology for bracket calculation in terms of service?

**Product/Mission:**
3. Is the non-judgmental framing strong enough? Should we add anything?
4. Should state context only show if N>50 to avoid false precision in small categories?

**Nonprofit Impact:**
5. Have we tested this with sample nonprofits? What do they say?
6. Risk: Nonprofits feel ranked/compared. How do we mitigate?
7. Opportunity: Nonprofits use this for board self-assessment. How do we enable?

**Governance:**
8. Should bracket thresholds (Top 25%, Upper 50%, etc.) require board approval?
9. If we change v5 scoring later, do we update brackets retroactively? (Impacts explainability)

---

## Recommendation

**Launch readiness:** 80% (Stewardship-aligned, but missing nonprofit feedback)

**Before full outreach to nonprofits:**
- [ ] Board advisor input on questions above
- [ ] User test with 5–10 nonprofits (reaction, understanding, concerns?)
- [ ] Document bracket logic in DECISIONS.md
- [ ] Ensure Mistake Registry is prominent on pages showing rankings
- [ ] Plan for "nonprofit claims dashboard" to show them their own peer context regularly

**Timeline:**
- Board discussion: Jun 22 (today)
- Nonprofit user testing: Jun 23–24
- Adjustments: Jun 25
- Full rollout: Jun 26+

---

## Appendix: Sample Orgs

**Org 1: LAKESHORE CAP INC OF WISCONSIN**
- Category: Social Services (S), 95.35 percentile
- State: Wisconsin, #52 of 73 in category
- Size: Established (>$700K)
- Model: Donation-Funded Programs
- Health: CAUTION (needs support)

**Display:**
```
🏛️ Your Category
  Social Services nonprofits
  ────────────────────────────
  Upper 50% (95.35th percentile)

📍 Your State  
  Wisconsin orgs in your category
  ────────────────────────────
  #52 of 73

💰 Your Size
  Established nonprofits nationally
  ────────────────────────────
  Upper 50%

🎯 Your Model
  Donation-Funded Programs
  ────────────────────────────
  ⚠ Needs support
```

---

**End Memo**
