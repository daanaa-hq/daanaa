# Platform Features: Making Giving Easy & Repeat

**Retention features tied to behavioral psychology.** What we build, when, and why.

---

## What Already Exists (Live Today)

### 1. **Giving Wallet (Device-Local Bookmarks)**
- **What:** Donors can bookmark organizations they care about
- **How:** "Add to Wallet" button on org pages
- **Where stored:** Device-local (localStorage or encrypted sync optional)
- **Psychology it solves:** Availability heuristic (org stays in donor's memory)
- **Retention impact:** Bookmarked org = top-of-mind when donor returns

### 2. **Organization Profiles with Financial Data**
- **What:** Each org shows financial health signals (peer group, revenue band, efficiency)
- **How:** Displayed on org detail page
- **Data shown:** 
  - Peer group rank (e.g., "Top 25% of peer group for financial health")
  - Revenue band (Micro/Professional/Established)
  - Financial health signal (HEALTHY/STABLE/CAUTION)
  - Peer count ("Compared to 412 similar organizations")
- **Psychology it solves:** Loss aversion (donors see proof org is stable/trustworthy)
- **Retention impact:** Trust → repeat giving

### 3. **Search + Filters**
- **What:** Find orgs by cause, location, financial health
- **How:** Directory search, category filters
- **Helps with:** Discovering orgs (acquisition) + rediscovering bookmarked orgs (retention)

---

## What We Need to Build (G2: Giving Paths)

### Feature 1: **One-Click Giving from Wallet** (CRITICAL)

**What:** Donor returns to Daanaa, sees bookmarked orgs, one-click to donate

**Current flow (high friction):**
1. Donor bookmarks org
2. Weeks later, returns to website
3. Searches for org
4. Clicks org page
5. Scrolls to find "Donate" button
6. Clicks donate link (goes to Every.org or org's site)
7. Completes donation

**New flow (low friction):**
1. Donor bookmarks org
2. Weeks later, opens Daanaa
3. Sees "Your Giving Wallet" widget
4. Sees bookmarked org with one-click "Give Now" button
5. Clicks → goes directly to donation page (pre-filled with org)
6. Completes donation

**Where on platform:**
- Homepage: "Your Giving Wallet" section (if logged in or device cookies)
- Wallet page: Full list of bookmarks, sorted by recency or category
- Each bookmark card: "Give Now" button (links to verified donate URL)

**Psychology solved:**
- Decision fatigue (bookmark = pre-decision, just execute)
- Cognitive load (no re-search needed)
- Habit formation (easier routine = habit sticks)

**Retention impact:** 2–3x repeat gift rate (from behavioral research)

---

### Feature 2: **Donation Links (Org-Provided)** (CRITICAL)

**What:** When nonprofit claims their page, they provide their own donate link. Daanaa displays it.

**Current state:**
- Unclaimed orgs: No donate button (they haven't authorized a link)
- Claimed orgs: Org provides link when they claim
- Legal: Only claimed orgs can have "Give" CTAs (CA charitable solicitation compliance)

**Why this model:**
- Org controls their own link (not us discovering/verifying it)
- Org is responsible for the link (legal liability on them)
- Daanaa is a directory (showing what orgs have told us)
- We stay out of solicitation (org authorizes the link, not us)

**How it works:**
1. Org claims profile (email verification)
2. Org enters: "Our donation link is [URL]"
3. Daanaa displays it: "Donate" button on org page + Wallet card
4. Donor clicks → goes to org's link (Every.org, Donorbox, org website, etc.)

**Where on platform:**
- Org detail page: Large green "Give Now" button (ONLY if claimed org + link provided)
- Wallet card: "Give Now" button (ONLY if org claimed)
- Unclaimed orgs: No donate button (just "Claim this organization" prompt)

**Psychology solved:**
- Loss aversion (org-provided link = org authorization/legitimacy)
- Decision fatigue (no hunting for donate button)
- Trust (org has claimed their page = verified)

**Retention impact:** Removes friction barrier to repeat giving (but only for claimed orgs)

---

### Feature 3: **Org-Chosen Donation Method** (CRITICAL)

**What:** Orgs provide their own donate link. We display it. Org chooses processor (Every.org, Donorbox, own website, etc.)

**Current state:**
- Org claims profile
- Org provides: "Our donation link is [URL]"
- Org controls: Processor, receipts, donor handling
- Money never touches Daanaa (yellow pages model)

**Why this approach:**
- Org has full control (they choose Every.org OR direct-to-website OR Donorbox)
- Org receives receipts (if they use Every.org or equivalent)
- Daanaa is neutral (we're not requiring a specific processor)
- Legal: Org is responsible, not us

**Where on platform:**
- "Give Now" button routes to org's provided link
- Button shows org's chosen destination: "Donate via [Every.org / org website / Donorbox]"
- No Daanaa involvement in transaction

**Psychology solved:**
- Loss aversion (org link = org authorization)
- Reciprocity (org chooses if they want receipt infrastructure)

**Retention impact:** Low-friction giving to orgs' preferred platform

---

## What We Build (G3: Services + Growth)

### Feature 4: **Giving Wallet Enhancements** (POST-G2)

**What:** Make bookmarks smarter without adding org burden or donor tracking

#### A. Wallet Analytics (Private to Donor Only)
- Donor sees: "You've bookmarked 7 organizations across 3 causes"
- Shows: Total across bookmarks, causes represented, last bookmarked
- NOT shared publicly, NOT tracked by Daanaa
- Purely for donor's own insight

**Psychology solved:**
- Meaning-making (donor sees their own giving patterns)
- Autonomy (only donor sees this, no social pressure)

#### B. Smart Sort Options
- Sort bookmarks by: recency, cause, financial health, location
- Pinned favorites (pin 2–3 "donate soon")
- Search within wallet ("Show me all [cause] orgs in [city]")

**Psychology solved:**
- Cognitive load (easier to navigate own list)
- Decision fatigue (pre-sorted options)

#### C. Donation Reminder (Opt-In, Not Aggressive)
- **NOT email reminders** (causes reactance)
- **Instead:** Optional "Check in" checkbox
- If enabled: Daanaa shows gentle notification (in-app only): "You bookmarked [Org] 6 months ago. Still interested?"
- Donor can: "Yes, give now" / "Still interested, remind later" / "No, remove"
- Zero pressure. Zero email. Donor controls everything.

**Psychology solved:**
- Availability heuristic (if donor wants a reminder, provide it)
- Autonomy (completely opt-in, easy to dismiss)

**Retention impact:** Opt-in reminders can boost repeat giving 20–30% (among those who want them)

---

### Feature 5: **Peer Recommendations** (POST-G2, Careful Design)

**What:** Help donors discover related organizations without creating comparison pressure

#### Safe Implementation
- "Similar organizations in [cause] doing [work]"
- Example: Donor bookmarks a food bank → sees 3–5 other food banks + housing orgs in same city
- Framing: "Organizations working on [hunger] in [city]" (not "better" or "ranked")
- No social proof ("Donors like you also support...")
- No rankings

**Where on platform:**
- Org detail page: "Related organizations" section
- Wallet: "Explore related" from any bookmark

**Psychology solved:**
- Choice overload (curated list, not all 1.9M orgs)
- Loss aversion (peer context helps trust new orgs)
- **Does NOT create:** Comparison anxiety, social pressure, ranking

**Retention impact:** Donors expand to related causes (+15–20% portfolio size)

---

### Feature 6: **Nonprofit Claiming + Impact Stories** (G3, No Burden)

**What:** Orgs claim their profile; can optionally add context (not required)

#### What Orgs Can Do (Opt-In, Zero Pressure)
- Claim their profile (email verification)
- Add 1–2 sentence mission update (optional)
- Link to their newsletter (optional)
- Update financial info (auto-pulled from IRS, but org can correct)

#### What Orgs DON'T Have to Do
- Post regular updates to Daanaa (no "social media for nonprofits")
- Report to us (we use IRS data, not org-submitted reports)
- Maintain a feed (their website is their feed)

**Psychology solved:**
- No org burden (they focus on mission, not Daanaa updates)
- Transparency (org controls their narrative)
- Meaning-making (donors see org in their own words + IRS data)

**Retention impact:** Orgs that claim get 2x donor inquiry (claimed = verified)

---

## What We DON'T Build

### ❌ Email Reminder Campaigns
- **Why:** Causes reactance (pushback). Triggers "this feels like nagging."
- **Result:** Backfires. Donors unsubscribe.
- **Instead:** Optional in-app gentle reminder (opt-in, easy to dismiss)

### ❌ "Org Must Post Updates"
- **Why:** Creates burden + inauthentic storytelling
- **Result:** Orgs resent us. Stories feel forced.
- **Instead:** Link to org's own newsletter/website

### ❌ Social Proof Displays
- **Why:** Creates comparison anxiety ("Am I giving enough?")
- **Result:** Donors give less (not more) or leave platform.
- **Instead:** Peer context (similar orgs, not "donors like you")

### ❌ Gamification ("You've given 5 times!")
- **Why:** Creates guilt + obligation (not joy)
- **Result:** Donors resent. Gives. Decrease.
- **Instead:** No badges, no streaks, no scoring

### ❌ Public Giving Visibility
- **Why:** Violates privacy, creates social pressure
- **Result:** Donors avoid platform. Trust erodes.
- **Instead:** Private giving wallets (device-local or encrypted)

---

## The Feature Timeline

### **G2 (Weeks 6–12): Core Giving Paths**
- [ ] One-click giving from Wallet (CRITICAL)
- [ ] Org-provided donation links (CRITICAL) — orgs provide when they claim
- [ ] Simple give flow (no form friction)
- [ ] Revocation filter (quarterly IRS refresh)
- [ ] Claiming flow optimization (make it easy for orgs to provide link)

**Retention impact:** 2–3x repeat giving (low friction) for claimed orgs

### **G3 (Months 3–6): Services + Growth**
- [ ] Wallet enhancements (analytics, sort, optional reminder)
- [ ] Peer recommendations (related orgs)
- [ ] Nonprofit claiming + profile updates
- [ ] Group purchasing survey (GPO demand signal)

**Retention impact:** +20–30% from opt-in reminders, related discovery

### **G4+ (Months 5+): Advanced (If Demand Justifies)**
- [ ] Giving portfolio view (private, encrypted)
- [ ] Processor partnerships (Stax, Zeffy, etc.)
- [ ] Advanced analytics (for nonprofits: "Who are my donors?")

---

## The Retention Loop (Behavioral)

```
1. Donor discovers org on Daanaa (search, browse)
   ↓
2. [Org is CLAIMED? → Has donate link] YES / NO (unclaimed: no button)
   ↓
3. Adds to Wallet (bookmarks)
   ↓
4. Sees financial health signals (trust builds)
   ↓
5. Months later: Returns to Daanaa
   ↓
6. Sees Wallet, one-click "Give Now" (CLAIMED ORGS ONLY)
   ↓
7. Donates via org's link (Every.org / Donorbox / website)
   ↓
8. Org handles receipt (if they set it up)
   ↓
9. Sees peer orgs (expands portfolio)
   ↓
10. Repeats (habit forms)
```

**Key:** Only claimed orgs have "Give Now" buttons. This incentivizes claiming + keeps us out of solicitation.

**No nagging. No pressure. No tracking. Just easier giving (for claimed orgs).**

---

## Success Metrics (Product)

**By end of G2:**
- [ ] 1-click giving button clicked 2%+ of CLAIMED org page views
- [ ] Wallet adoption: 5%+ of visitors bookmark at least 1 org
- [ ] Claiming flow: 10%+ of orgs claim their profile (get donate button)
- [ ] Donations from Daanaa: 20+ per week from claimed orgs

**By end of G3:**
- [ ] Wallet engagement: 20%+ of donors return within 90 days
- [ ] Repeat gift rate: 45%+ of bookmarked CLAIMED orgs see repeat donors
- [ ] Claiming adoption: 20%+ of searchable orgs have claimed + active
- [ ] Average portfolio size: 3–4 orgs (vs. 1 historically)

**Behavioral validation:**
- [ ] Donors report: "Easy to find and support causes I care about"
- [ ] Orgs report: "Repeat donors from Daanaa increasing"
- [ ] Zero complaints about: Pressure, tracking, nagging

---

## Product Philosophy

**Every feature asks:**
1. Does this remove friction?
2. Does this build trust?
3. Does this respect autonomy?
4. Does this create pressure or guilt?
5. Does this burden nonprofits?

**If the answer is "yes" to 1–3 and "no" to 4–5, we build it.**

**If a feature creates pressure, we don't ship it.**

---

**This is how we solve retention without dark patterns.**
