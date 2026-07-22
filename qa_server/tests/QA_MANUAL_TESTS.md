# Simple Manual Testing Guide for Daanaa
**Date:** July 22, 2026  
**For:** Third-party QA testers (non-technical)

---

## ✅ What You're Testing

You'll test the **Daanaa nonprofit discovery platform** to make sure:
- Donors can find nonprofits easily
- Nonprofits can log in and manage volunteer hours
- Everything is clear and works smoothly

---

## 📋 Test Credentials

### Nonprofit Staff Account (for testing nonprofit features)
- **Email:** test@testnonprofit.org
- **Password:** TestNonprofit2024!
- **Nonprofit:** Test Food Bank (EIN: 123456789)

### Donor Testing (no login needed)
- Use your own email or a test email
- You don't need to actually donate (we'll test the process, not complete it)

---

## 🎯 Test Scenarios

### SECTION A: DONOR DISCOVERY (Anyone can do this)

**Scenario 1: Find a nonprofit by searching**

1. Go to https://daanaa.org
2. In the search box at the top, type: `food bank`
3. Press Enter or click Search
4. **CHECK:** Do you see results with nonprofit names and locations?
5. **CHECK:** Can you see a financial health score (number out of 100)?
6. **PASS:** At least 5 nonprofits appear in the results

---

**Scenario 2: Click on a nonprofit to see details**

1. From your search results (from Scenario 1), click on any nonprofit name
2. **CHECK:** Does the page load showing:
   - Organization name?
   - Location (city, state)?
   - Mission statement (what they do)?
   - Financial health score?
   - A "Donate" link?
3. **PASS:** All of the above appear on the page

---

**Scenario 3: Use the "Add to Wallet" button**

1. While viewing a nonprofit detail page (from Scenario 2)
2. Look for a button that says "Add to Wallet" or "Save"
3. Click it
4. **CHECK:** Does it show a confirmation? (message, checkmark, or color change?)
5. **PASS:** Button responds to your click (shows it saved)

---

**Scenario 4: Browse categories**

1. Go back to the homepage (https://daanaa.org)
2. Look for a way to browse by category (might say "Browse by Cause" or "Categories")
3. Click on any category (like "Health" or "Education" or "Environment")
4. **CHECK:** Do results filter to show only that category?
5. **PASS:** You see nonprofits in just that category

---

**Scenario 5: Search by location**

1. On the homepage, look for a location filter or search option
2. Type or select a state (like "CA" for California)
3. **CHECK:** Do results show only nonprofits from that state?
4. **PASS:** Location filtering works

---

### SECTION B: NONPROFIT STAFF FEATURES

**Scenario 6: Nonprofit login**

1. Go to https://daanaa.org
2. Look for a link that says "For Nonprofits" or "Nonprofit Login" (usually at top-right or in a menu)
3. Click it
4. Enter the email: `test@testnonprofit.org`
5. Enter the password: `TestNonprofit2024!`
6. Click "Log In"
7. **CHECK:** Do you see a welcome message or a dashboard?
8. **CHECK:** Do you see your nonprofit's name (Test Food Bank)?
9. **PASS:** You're logged in and see the nonprofit dashboard

---

**Scenario 7: View the nonprofit dashboard**

1. After logging in (from Scenario 6), look at the main dashboard page
2. **CHECK:** Do you see:
   - Organization name (Test Food Bank)?
   - A welcome message (might say "Welcome back" or "Getting started")?
   - Volunteer hours information?
   - A list of events or activities?
   - Profile information (mission, website, etc.)?
3. **PASS:** Dashboard shows at least 3 of the above items

---

**Scenario 8: View volunteer hour submissions**

1. While logged in as nonprofit staff, look for "Volunteer Hours" or "Submissions"
2. Click on it
3. **CHECK:** Do you see:
   - A list of volunteer submissions?
   - The volunteer's name?
   - Hours submitted?
   - The date?
   - An "Approve" or "Review" button?
4. **PASS:** You can see at least one submission to review

---

**Scenario 9: Approve a volunteer submission**

1. From the volunteer hours list (Scenario 8), find a submission
2. Click "Approve" or a similar button
3. **CHECK:** Does it show a confirmation? (message like "Approved" or "✓"?)
4. **CHECK:** Does the status change (from "Pending" to "Approved")?
5. **PASS:** Submission is marked as approved with visual feedback

---

**Scenario 10: Edit nonprofit profile**

1. While logged in, look for a "Profile" or "Edit Profile" option
2. Click it
3. You should see fields like:
   - Organization name
   - Website
   - Mission statement
   - Services/programs offered
   - Service areas (cities/regions you serve)
4. **CHECK:** Can you edit at least one field? (try changing text)
5. **CHECK:** Is there a "Save" button?
6. **PASS:** You can edit and save profile information

---

**Scenario 11: View profile help/guidance**

1. While in the profile editor, look for "?" icons or "Learn More" links
2. Click on one
3. **CHECK:** Does helpful information appear? (explanation of what the field means)
4. **CHECK:** Is the language clear and supportive?
5. **PASS:** Help text is visible and helpful

---

**Scenario 12: Review dashboard overview**

1. From the main nonprofit dashboard, look for an "Overview" section
2. **CHECK:** Do you see helpful cards showing:
   - Volunteer hours submitted this month?
   - Profile completion percentage?
   - Number of events posted?
   - Any other stats or information?
3. **CHECK:** Are there any tooltips (small "?" icons) for guidance?
4. **PASS:** Dashboard overview provides useful information at a glance

---

### SECTION C: USER EXPERIENCE & ACCESSIBILITY

**Scenario 13: Page loading speed**

1. Go to https://daanaa.org
2. Click on a nonprofit result
3. **CHECK:** Does the page load in under 3 seconds?
4. **CHECK:** Is there a loading indicator if it takes more than 1 second?
5. **PASS:** Page loads quickly and smoothly

---

**Scenario 14: Mobile-friendly design (test on phone)**

1. On a smartphone or tablet, go to https://daanaa.org
2. **CHECK:** Is the layout readable without zooming?
3. **CHECK:** Can you click buttons easily without accidentally hitting the wrong one?
4. **CHECK:** Does text wrap properly (not cut off)?
5. **PASS:** Website works well on mobile

---

**Scenario 15: Button clarity**

1. Navigate to a nonprofit detail page
2. Look at all the buttons (Donate, Add to Wallet, etc.)
3. **CHECK:** Is it clear what each button does? (label is obvious)
4. **CHECK:** Do buttons look clickable? (distinct from regular text)
5. **PASS:** All buttons are clearly labeled and look interactive

---

**Scenario 16: Error handling (intentional failure)**

1. Search for a nonprofit using a weird search like: `xyzabc123`
2. **CHECK:** Do you see a clear message like "No results found"?
3. **CHECK:** Is it not a blank page or error message?
4. **CHECK:** Does it suggest: "Try a different search"?
5. **PASS:** Empty results are handled gracefully with a helpful message

---

**Scenario 17: Help & Support visibility**

1. Go to the nonprofit dashboard (after logging in)
2. Look for a "Help" button or "Support" link
3. **CHECK:** Is it easy to find?
4. Click on it
5. **CHECK:** Do you see helpful information or FAQs?
6. **PASS:** Help is accessible and informative

---

### SECTION D: TRUST & SECURITY

**Scenario 18: Data source visibility**

1. View a nonprofit detail page
2. Look for information about where the financial data comes from
3. **CHECK:** Does it say something like "IRS Form 990" or "From public records"?
4. **CHECK:** Is there a date showing when the data was updated?
5. **PASS:** Data sources are clearly labeled

---

**Scenario 19: Privacy & donation handling**

1. Search for a nonprofit
2. Click "Donate" or donation link
3. **CHECK:** Does it leave the Daanaa website? (goes to nonprofit's site)
4. **CHECK:** Does it NOT ask for credit card info on Daanaa?
5. **CHECK:** Is there language saying "You will donate directly to [Nonprofit]"?
6. **PASS:** Donations are handled by the nonprofit, not Daanaa

---

**Scenario 20: Nonprofit login security**

1. Try logging in with wrong password
2. **CHECK:** Do you get an error message? (NOT "wrong email" specifically, but "invalid login")
3. **CHECK:** Are you NOT logged in?
4. **PASS:** Wrong credentials are rejected

---

---

## 📊 What to Report

### If a test PASSES ✅
- Just note it passed
- Example: "Scenario 1: PASS - Found 10 food banks in search results"

### If a test FAILS ❌
- Screenshot (if possible)
- What you did (step-by-step)
- What you expected to happen
- What actually happened
- Example:
  ```
  Scenario 8: FAIL
  Steps: Logged in → Clicked "Volunteer Hours"
  Expected: See list of submissions
  Actual: Got blank page with no data
  Screenshot: [attached]
  ```

### If something seems unclear ⚠️
- Note what was confusing
- Suggest better wording if applicable
- Example: "Scenario 11: The 'Learn More' link text is small and hard to find"

---

## 🎬 Sample Test Run (Step-by-Step)

**Day 1 Test (Estimated time: 30 minutes)**
- Scenario 1: Search (5 min)
- Scenario 2: View details (5 min)
- Scenario 3: Add to Wallet (3 min)
- Scenario 6: Nonprofit login (5 min)
- Scenario 7: View dashboard (5 min)
- Scenario 13: Loading speed (2 min)

**Day 2 Test (Estimated time: 40 minutes)**
- Scenario 4: Browse categories (5 min)
- Scenario 5: Search by location (5 min)
- Scenario 8: View volunteer submissions (5 min)
- Scenario 9: Approve submission (5 min)
- Scenario 10: Edit profile (5 min)
- Scenario 14: Mobile testing (10 min)

**Day 3 Test (Estimated time: 40 minutes)**
- Scenario 11-12: Dashboard help (10 min)
- Scenario 15-17: UX & support (15 min)
- Scenario 18-20: Trust & security (15 min)

---

## ✨ Success Criteria

**ALL TESTS PASS if:**
- ✅ All 20 scenarios complete without errors
- ✅ Buttons and links work
- ✅ Pages load quickly
- ✅ Text is clear and helpful
- ✅ No confusing error messages
- ✅ Mobile works well

**At least 90% of tests pass = GOOD**  
**Less than 80% pass = Needs fixing before release**

---

## 📞 Questions?

If you get stuck:
1. Try refreshing the page (Ctrl+R or Cmd+R)
2. Clear browser cache and try again
3. Try a different browser (Chrome, Safari, Firefox)
4. Note what you were doing and report it

---

## 🚀 When You're Done

Send results to: **QA Lead**

Include:
- [ ] Number of tests passed
- [ ] Any failures (with screenshots)
- [ ] Any unclear areas or confusing wording
- [ ] Overall impression (was it easy to use?)

**Thank you for testing! 🎉**
