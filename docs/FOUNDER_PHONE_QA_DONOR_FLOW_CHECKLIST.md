# Founder Phone QA — Donor Flow Checklist

**Task:** #17 — Real-phone walk-through of search → org page → donate → wallet  
**Duration:** ~15 minutes  
**Setup:** Real mobile device (not emulator), on live daanaa.org

---

## Pre-Call Setup (5 min)

- [ ] Clear browser cache on test device
- [ ] Use incognito/private mode (fresh state, no localStorage)
- [ ] Verify internet connection is stable
- [ ] Have daanaa.org open on phone already
- [ ] Have wallet visible in browser dev tools (to watch localStorage)

---

## Part 1: Discovery (3 min)

**Goal:** Verify search surface the right orgs and feel discoverable

### Golden Path Queries
- [ ] Search: "food banks near me" → expect location-aware results + small orgs visible
- [ ] Search: "Red Cross" (self-search) → expect exact name in top 5
- [ ] Search: "education" (cause tag) → expect mixed sizes, not just big orgs
- [ ] Search: "small nonprofit" (proxy for small-org visibility) → expect diversity

### Inspect Results
- [ ] Does each org show: name, location, mission, financial context?
- [ ] Is peer context label clear and not shaming? ("Financially Healthy," not "A-rated")
- [ ] Can you click through to org detail page smoothly?

---

## Part 2: Org Detail Page (4 min)

**Goal:** Verify trust signals + donation pathway are clear

### Trust Signals
- [ ] Mission statement is present and readable (AI-generated or claimed — label visible?)
- [ ] Financial context shown with peer group context (archetype + band + health signal)
- [ ] Source attribution visible (e.g., "IRS 2024 filing via ProPublica")
- [ ] Edit path visible if org is claimed ("Claim & correct this profile")

### Donation Path
- [ ] Donation button/link prominent and clear
- [ ] Link label matches donation method (e.g., "Give via Every.org" if routed there)
- [ ] Link goes to org's own processor (not Daanaa's internal handler)
- [ ] Mobile tap is comfortable (not too small, easy target)

---

## Part 3: Donation Hand-Off (5 min)

**Goal:** Verify hand-off is clean + wallet capture feels natural

### The Click
- [ ] Tap donate button
- [ ] Expected destination: org's own site (Every.org, PayPal, Stripe, etc.)
- [ ] Does the page load quickly on 4G? (simulate slowness if possible)
- [ ] Does the URL look trustworthy? (org's domain or known processor)

### Post-Donation Flow
- [ ] After donating on org's site, can you navigate back to daanaa.org?
- [ ] Browser back button works smoothly
- [ ] Wallet prompt appears (if we show one) — not pushy, not hidden
- [ ] "Add to wallet" UX feels natural, not like a dark pattern

### Wallet Capture
- [ ] Click "Add to wallet" (or equivalent)
- [ ] Watch localStorage update (dev tools → Application → localStorage)
- [ ] Verify org appears in wallet bookmark list
- [ ] Can you see the org card in the wallet (name, location, amount given)?

---

## Part 4: Return Visits (2 min)

**Goal:** Verify wallet persistence and rediscovery

### Bookmark Persistence
- [ ] Close browser completely
- [ ] Reopen daanaa.org
- [ ] Navigate to wallet/bookmarks
- [ ] Org still there? (localStorage should persist)
- [ ] Can you see wallet on a different device? (only if you later sign in, if wallet sync exists)

### Rediscovery
- [ ] Search for the same org again
- [ ] Does it appear quickly in search?
- [ ] Does the wallet mark it as "already saved"? (visual indicator)

---

## Part 5: Edge Cases (if time)

- [ ] Try searching for a small org with no website — does it show? Is it labeled honestly ("no website," not penalized)?
- [ ] Try an org with partial/stale financial data — does it show "not enough data" clearly, not "weak financials"?
- [ ] Try a mobile-only experience — does the layout collapse gracefully? Are buttons easy to tap?

---

## Feelings Check (At End)

Ask yourself:
- **Trust:** Do I believe the financial context is fair and evidence-based?
- **Clarity:** Do I understand why each org appears and in what order?
- **Frictionless:** Did I hit unexpected dead ends or confusing CTAs?
- **Dignity:** Did the platform treat small orgs with respect, not as second-tier?

---

## Notes for This Call

- **Main question:** Does the flow feel frictionless end-to-end?
- **Red flag:** Any confusing labels, misleading CTAs, or surprise redirects?
- **Success metric:** You can find an org, verify trust, donate, and save it to wallet in <5 min

---

## After Call

- [ ] Note any rough edges or confusion
- [ ] Flag if any labels felt misleading (P3/P5 violation)
- [ ] Suggest if small-org visibility felt fair
- [ ] Share any "aha" moments or delight points

**Report to:** DECISIONS.md + this checklist file for posterity
