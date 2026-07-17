# Board Simulation: Stakeholder Feedback
**Simulation Date:** 2026-07-17  
**Exercise:** External perspective on Profile Trust Signal Decisions  

---

## Legal Group Response

**Concern Level:** Low (advisory, not blocker)

> **Summary:** No disclosure obligations breached. Percentile history is internal ranking, not a fiduciary claim. Removal actually *reduces* liability surface.
>
> **Detailed take:**
> - ✅ We're not required to show historical percentile data anywhere (it's our methodology, not a regulated disclosure).
> - ✅ Raw 990 data table stays, so donors can reconstruct their own view if they want.
> - ⚠️ **The v4 ScoreBreakdown is murkier:** If we position it as "how we score," removing it without clear replacement language could be read as "we're hiding our scoring logic." **Mitigation:** Make sure the "How we assess nonprofits →" link is prominent and the methodology is publicly documented (not buried).
> - ✅ No risk here if we're transparent about why we changed it.
>
> **Recommendation:** Ship both removals. Add a 1-line note in the methodology page (if not there already): "Historical score movements largely reflect our data refresh cycles, not org-level change. Current year financials + health signal tell the real story."

---

## Accounting/Finance Group Response

**Concern Level:** Medium (methodological, not financial)

> **Summary:** Percentile deltas are noisy and misleading. Removal improves data honesty. v4 breakdown is redundant with v5. Both removals are sound.
>
> **Detailed take:**
> - 🔴 **Percentile history is a problem we've quietly known about:** Every time we re-score (data refresh, methodology tweak, new orgs added), ALL percentiles shift. An org that was 45th percentile in 2024 might be 40th in 2025 *because we added 500 new comparison orgs*, not because it got worse. We're showing that as "trajectory" when it's really "our dataset evolved."
> - ✅ This violates P3 (evidence-based signals). Remove it.
> - ✅ v4 ScoreBreakdown is legacy. v5 is our canonical model. Don't confuse donors by keeping both.
> - ⚠️ **One ask:** If we keep the raw 990 table (which we do), make sure the methodology link explains what *our* financial context score is measuring (archetype, band, health) vs. raw 990 numbers. Don't let donors think we're hiding a calculation.
>
> **Red flag we almost missed:** If any partner org is marketing "we're in the top 10% on Daanaa" based on the percentile history they saw, and we remove that visualization, they might complain. But that's a *them problem* — they shouldn't be using our internal ranking as their marketing anyway (P7: independence).
>
> **Recommendation:** Ship. Add one sentence to methodology: "Percentile rankings reflect your position within your peer group *at time of calculation*. Comparisons across years are not reliable indicators of org performance (peer groups expand/contract; our methods evolve)."

---

## Marketing Group Response

**Concern Level:** High (user experience, competitive differentiation)

> **Summary:** Removing the percentile table is good UX; removing v4 breakdown is risky if donors expect detailed explanations.
>
> **Detailed take:**
> - ✅ **Score History table: Remove it.** Most donors don't understand percentile deltas anyway. The ones who do (wealthy/technical) prefer raw data. The visualization adds chart-clutter without engagement payoff. We've seen zero user feedback asking for it.
> - ⚠️ **v4 ScoreBreakdown: Mixed signals.**
>   - *Pro:* Cleaner UX. Reduces "technical jargon" load. v5 is simpler and more humane.
>   - *Con:* Some high-engagement donor segments (DAF advisors, wealth managers) like diving deep. They're a small % but high-value. We'd be removing a signal they use.
>   - *Con:* Competitive angle: GiveWell, Charity Navigator both show detailed breakdowns. Not showing one might read as "less rigorous."
>   - *Pro:* Counter: Our "How we assess" methodology page can be *more* detailed than ever, just not inline on every profile. Cleaner separation.
> - **Recommendation:** Ship the percentile removal. **Conditional on v4 breakdown:** Test with 5 DAF partners first (30-min call). If they say "yeah, we just use the methodology link, no big deal," ship it. If they say "we use this every day," keep the breakdown but move it lower on the page (toggle stays, but deprioritized).

---

## ED (Executive Leadership) Group Response

**Concern Level:** Medium (nonprofit partner sentiment, mission fit)

> **Summary:** Nonprofit partners won't care about these removals. But we should validate the broader UX simplification.
>
> **Detailed take:**
> - ✅ **Nonprofit partner perspective:** The orgs we list don't look at their own percentile history—they see it as "marketing ammo" at best, noise at worst. Removing it won't upset them.
> - ✅ **Mission fit:** Cleaner, simpler profiles = easier for donors to understand the org's *actual* work. That's mission-aligned (P1).
> - ⚠️ **But:** We should spot-check one thing: Are any nonprofits currently using our "percentile rank" in their own marketing or board reports? (Unlikely, but possible.) One quick email to 10 partner orgs: "Do you ever reference your Daanaa percentile score?" If yes, give them 30 days' notice before removal.
> - ✅ **The philosophy is sound:** "We're prioritizing clarity over precision-jargon." That's very on-brand for us.
>
> **Recommendation:** Ship both. Send a 1-paragraph heads-up to claimed orgs: "We're simplifying the profile experience. Your financial story is now told through [health signal, peer group, raw 990]. Methodology link updated with details."

---

## Donor Group Response

**Concern Level:** Low (they don't use these features much)

> **Summary:** Most donors won't notice. Power users might miss v4 depth; they'll find it in the methodology. No blocker.
>
> **Detailed take:**
> - ✅ **Percentile history: No one uses it.** We've watched session recordings (Hotjar). Donors scroll past the table. The ones who care about "how the org has changed" read the raw 990 amounts or skip it entirely. The visualization adds time to page load; removing it is a win.
> - ✅ **v4 ScoreBreakdown: Low engagement.** The toggle exists; <5% click it. The ones who do are mostly wealth advisors or board members doing due diligence. They're not scared by a link to the methodology page instead.
> - ⚠️ **But the page-simplification has a risk:** If we remove *both*, the profile becomes more "surface-level." Some donors (the ones who do deep dives) might feel we're "dumbing it down." **Mitigation:** The methodology link is extremely prominent. Make it clickable from the health signal too, not just at the bottom.
> - 💡 **Opportunity:** The freed-up vertical space could show something donors actually ask about: "What does this org spend on programs?" (program expense %). We show it in the context card, but burying it. Donors care about that more than percentile history.
>
> **Recommendation:** Ship both. A/B test whether moving the program expense % up in the visual hierarchy increases engagement. (If donors care about the bottom line, show it sooner.)

---

## Synthesis: Cross-Cutting Themes

| Theme | Status | Action |
|-------|--------|--------|
| **Data honesty** | ✅ Strong consensus | Ship both. Percentile deltas are misleading; remove them. |
| **Methodology transparency** | ✅ Strong consensus | Make the "How we assess" link more prominent. Test that it's working for power users. |
| **Nonprofit partner notification** | ⚠️ Recommended | Send 1-paragraph heads-up to claimed orgs (30 days' notice). |
| **DAF/wealth advisor impact** | ⚠️ Recommended | Quick 5-org spot check on v4 breakdown usage before shipping. |
| **Page-simplification UX** | ✅ Opportunity | Consider showing program expense % higher on page (frees space, addresses donor question). |

---

## Confidence Levels

| Decision | Confidence to Ship | Conditions |
|----------|------------------|-----------|
| Remove Score History table | 95% | None. Clear win. |
| Remove v4 ScoreBreakdown | 75% | Conditional: 5-org DAF spot check, + methodology link audit. |

---

## Recommended Action

**1. Ship Score History removal immediately** (today). No downside, clear principle alignment.

**2. For v4 ScoreBreakdown, do a 24-hour spot check:**
   - Email 5 active DAF/advisor partners: "Do you ever use the 'Score Breakdown' toggle on our profiles?"
   - Audit the methodology page: Is it comprehensive enough to replace the inline toggle?
   - If both are green, ship. If either is red, keep the toggle but deprioritize it (move lower, less prominent).

**3. Send nonprofit partner heads-up** (same email as the spot check): "Simplifying profile UX. Your financials now shown as [X]. Details in methodology. Questions? Reply."

**4. Consider the program expense % optimization** (post-ship): Use the freed-up space to bubble up the donor question most people ask anyway.

---

## Risk: Overcorrection?

**Question for founder:** Are we worried we're *over-simplifying*? That donors will demand "why can't I see how the org ranked over time?" 

**Counter:** If they do, the raw 990 data table + methodology link give them enough to reconstruct it themselves. And our A/B tests (if we run them) will tell us if simplification hurts engagement or helps it.

**Principle check:** P3 says "trust signals must be evidence-based and honestly stated." Percentile deltas are *not* honest signals of org trajectory. Removing them strengthens P3.

