# Daanaa Giving Wallet — Tester Guide

**Live Link:** https://daanaa.org/wallet/  
**Status:** Public beta (Jun 18, 2026)  
**Testing Period:** Jun 18–30  
**Feedback Deadline:** Jun 30 EOD

---

## Quick Start (2 minutes)

1. **Open the wallet:** https://daanaa.org/wallet/
2. **Search for an org:** Type a cause (e.g., "climate", "education", "health")
3. **Add to wallet:** Click "Add to Wallet" button
4. **Set intent:** Edit giving/volunteer/board intent in the modal
5. **Explore:** Sort, filter, search, remove orgs

---

## What to Test

### Core Features ✅

- **Search & Filter**
  - [ ] Search by org name (e.g., "Greenpeace")
  - [ ] Search by cause (e.g., "climate")
  - [ ] Filter by intent (Giving, Volunteering, Board)
  - [ ] Filter by financial health (HEALTHY, STABLE, CAUTION)
  - [ ] Sort by Recent, Name, Health
  - [ ] Clear filters button works

- **Add/Edit/Remove Orgs**
  - [ ] Click "Add to Wallet" on org detail page (if available)
  - [ ] Click "Add to Wallet" button on wallet page
  - [ ] Edit intent: select type (Giving/Volunteer/Board)
  - [ ] For Giving: set amount + frequency (year/month/one-time)
  - [ ] For Volunteering: set hours/week
  - [ ] For Board: note skills/interests
  - [ ] Add notes (200-char limit)
  - [ ] Remove org (confirm dialog)
  - [ ] "Already in Wallet" state shows for duplicates

- **Data Persistence**
  - [ ] Reload page → wallet persists
  - [ ] Close browser → wallet persists
  - [ ] Clear browser cache → wallet clears (expected)
  - [ ] Wallet shows correct count

- **UI/UX**
  - [ ] Page is responsive (test mobile + desktop)
  - [ ] Cards display org info clearly
  - [ ] Intent signals visible (giving $X/year, volunteer X hours/week, board)
  - [ ] Empty state helpful (shows CTA to add orgs)
  - [ ] Buttons are accessible (tab navigation works)
  - [ ] Colors readable (financial health badges distinct)

- **Edge Cases**
  - [ ] Add 5+ orgs → grid layout correct
  - [ ] Search with 0 results → message shows
  - [ ] Remove all orgs → empty state appears
  - [ ] Filter to 0 results → message shows
  - [ ] Note with 200+ chars → truncates
  - [ ] Rapid clicking add button → no duplicates

---

## Feedback Form

When you're done testing, fill out this form (5 min):

**Quick Survey:**
1. **Ease of use (1–5):** ___
   - Easy = 5, Hard = 1
   
2. **Visual design (1–5):** ___
   - Beautiful/clear = 5, Confusing/ugly = 1

3. **Feature completeness (1–5):** ___
   - All features work = 5, Broken/missing = 1

4. **Search/filter quality (1–5):** ___
   - Found orgs easily = 5, Couldn't find anything = 1

5. **Biggest issue (text):**
   ```
   What was most frustrating or confusing?
   ```

6. **Feature wish (text):**
   ```
   One thing you'd add or change?
   ```

7. **Recommend to donors (yes/no):**
   ```
   Would you use this to find nonprofits to support?
   ```

**Send feedback to:** [support@daanaa.org](mailto:support@daanaa.org)  
**Subject line:** `[Wallet Feedback] [Your Name]`

---

## Known Limitations (Expected, Not Bugs)

These are NOT bugs—they're expected for beta:

❌ **No account sync** — Wallet is device-only (no cloud backup yet). Clear browser cache = wallet gone.

❌ **No donation button** — Clicking an org goes to detail page, not donate link (Phase 2).

❌ **No sharing** — Can't share wallet with others yet (Phase 2).

❌ **No history** — Wallet doesn't show giving history or recurring donations (Phase 2).

❌ **Search is basic** — Full-text search on name/mission only (Elasticsearch integration coming).

---

## Report Bugs

If you find a real bug (crash, broken button, data loss), report it:

**Email:** [support@daanaa.org](mailto:support@daanaa.org)  
**Subject:** `[Bug] Wallet — [Issue]`

**Include:**
- What you did (step-by-step)
- What happened (screenshot if possible)
- Browser + device (Chrome on Mac, Safari on iPhone, etc.)
- Expected vs actual behavior

**Example:**
```
Subject: [Bug] Wallet — Can't edit giving amount

Steps:
1. Add org to wallet
2. Click "Edit" button
3. Change amount from $100 to $500
4. Click Save

Expected: Amount updates to $500
Actual: Amount stays $100, no error message

Browser: Chrome 126, Mac
```

---

## Private Note for Beta Testers

**Your privacy is protected:**
- Wallet data stays on YOUR device (browser localStorage)
- We can't see what orgs you add or your giving amounts
- No tracking, no analytics on your wallet activity
- Your email is only used for feedback response

**Your feedback shapes the product:**
- Issues you find → fixed before public launch
- Features you want → priorities for Phase 2
- UX problems → inform design improvements

---

## Timeline

| Date | Event |
|------|-------|
| **Jun 18** | Beta opens for testers |
| **Jun 20–30** | Feedback collection window |
| **Jun 30 EOD** | Feedback deadline |
| **Jul 1–5** | Fixes + Phase 2 planning |
| **Aug 15** | Public launch |

---

## Questions?

- **Technical issue?** → support@daanaa.org
- **Design feedback?** → support@daanaa.org (subject: Design)
- **Feature request?** → support@daanaa.org (subject: Feature)

---

## Thank You

You're helping build a better nonprofit discovery platform. Your feedback matters.

**Daanaa Team**  
Jun 18, 2026

---

## Testing Session Checklist

Use this to track your testing:

- [ ] Visited https://daanaa.org/wallet/
- [ ] Searched for org
- [ ] Added org to wallet
- [ ] Edited giving intent
- [ ] Set amount/frequency
- [ ] Added notes
- [ ] Removed org
- [ ] Tested filters (intent, health)
- [ ] Tested sort (recent, name, health)
- [ ] Tested search
- [ ] Reloaded page (checked persistence)
- [ ] Tested mobile view
- [ ] Filled feedback form
- [ ] Sent feedback email

**Time spent:** ___ min  
**Orgs tested:** ___ 
**Overall confidence (1-5):** ___
