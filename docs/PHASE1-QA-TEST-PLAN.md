# Phase 1 QA Test Plan — Ways to Give

**Phase:** QA & Smoke Tests (Week 3)  
**Target Date:** 2026-08-02  
**Duration:** 1 day (4–5 hours)  
**Platforms:** Desktop (Chrome, Safari), Mobile (iPhone 14, Pixel 6)

---

## Test Scope

### Routes & Navigation (Critical Path)

| Test | Steps | Expected | Pass |
|---|---|---|---|
| **Check page loads** | Navigate to `/giving-via-checks` | Page renders, hero visible, no 404 | ☐ |
| **Stocks page loads** | Navigate to `/giving-via-stocks` | Page renders, hero visible, no 404 | ☐ |
| **Routers page loads** | Navigate to `/giving-via-routers` | Page renders, hero visible, no 404 | ☐ |
| **DAF page loads** | Navigate to `/giving-via-daf` (already live) | Page renders, familiar flow | ☐ |
| **Home → Giving pages** | Discover link path from home page if exists | Links discoverable or searchable | ☐ |

### Org Detail Integration (Critical Path)

| Test | Steps | Expected | Pass |
|---|---|---|---|
| **Org page shows all CTAs** | Open any org page → scroll to "How to Give" section | See 4 links: Checks, Stocks, Routers, DAF | ☐ |
| **Each CTA links correctly** | Click "Give by check" → lands on `/giving-via-checks` | Correct page loads | ☐ |
| **Each CTA links correctly** | Click "Give appreciated stock" → lands on `/giving-via-stocks` | Correct page loads | ☐ |
| **Each CTA links correctly** | Click "Give via PayPal or Facebook" → lands on `/giving-via-routers` | Correct page loads | ☐ |
| **Each CTA links correctly** | Click "Give via donor-advised fund" → lands on `/giving-via-daf` | Correct page loads | ☐ |
| **Secondary CTAs visible on multiple orgs** | Test 3+ random org pages | CTAs present on all | ☐ |

### IRS & External Links (Critical Path)

| Test | Steps | Expected | Pass |
|---|---|---|---|
| **IRS Pub 526 link works** | Click link on any page referencing Pub 526 | IRS.gov page loads (no 404) | ☐ |
| **Form 8283 link works** | Click link on stocks page | IRS Form 8283 instructions load | ☐ |
| **Crypto FAQ link works** | Click link on any page about digital assets | IRS FAQ page loads | ☐ |
| **Tax Exempt Search link works** | Click IRS Tax Exempt Organization Search link | IRS search tool loads | ☐ |
| **PayPal Giving Fund link works** | Click link on routers page | paypalgivingfund.org loads | ☐ |
| **Facebook Giving link works** | Click link on routers page | facebook.com/fundraisers loads | ☐ |
| **Benevity link works** | Click link on routers page | benevity.com loads | ☐ |
| **GiveDirectly link works** | Click link on routers page | givedirectly.org loads | ☐ |

### Copy & Language Audit (QA)

| Test | Location | Expected | Pass |
|---|---|---|---|
| **"Daanaa does NOT process" disclaimer** | All four pages | Present and visible | ☐ |
| **Tax disclaimer present** | Checks, Stocks, Routers pages | "This is not tax advice" or similar | ☐ |
| **No smart quotes or encoding issues** | All pages | Text renders cleanly | ☐ |
| **No broken links in copy** | Scan all text for `[text](url)` patterns | All links work | ☐ |
| **Consistent voice across pages** | Read all pages | Tone is warm, accessible, not condescending | ☐ |
| **No "Daanaa processes donations" language** | All pages | Phrase never appears | ☐ |
| **IRS links labeled clearly** | All pages | Links say "IRS" or "official" | ☐ |

### Responsive Design (Mobile/Desktop)

| Test | Device | Steps | Expected | Pass |
|---|---|---|---|---|
| **Hero section readable** | Mobile | Load checks page on iPhone 14 | Hero text legible, not truncated | ☐ |
| **Steps readable** | Mobile | Scroll through 4-step guide | All steps visible, numbers clear | ☐ |
| **CTAs clickable** | Mobile | Tap "Give by check" link | Link responds, no double-tap needed | ☐ |
| **Grid layouts responsive** | Mobile | View benefits/info grids | Cards stack vertically, readable | ☐ |
| **External links work on mobile** | Mobile | Tap IRS link | Opens correctly in browser | ☐ |
| **Footer navigation accessible** | Mobile | Scroll to bottom of page | TrustNav visible and usable | ☐ |
| **Wide layout on desktop** | Desktop (1920x1080) | Load page | Layout uses full width appropriately | ☐ |

### Performance (Baseline)

| Test | Metric | Expected | Pass |
|---|---|---|---|
| **Page load time** | Check page (Chrome DevTools) | < 2 seconds (First Contentful Paint) | ☐ |
| **No console errors** | Open DevTools console | 0 errors (warnings OK) | ☐ |
| **No JavaScript crashes** | Interact with all CTAs | No 500-level errors in network tab | ☐ |
| **Lighthouse score** | Run Lighthouse audit on checks page | Performance: > 85 | ☐ |

### Browser Compatibility

| Browser | Device | Load Check Page | Load Stocks Page | Load Routers Page | Load Org Page with CTAs | Notes |
|---|---|---|---|---|---|---|
| Chrome | Desktop | ☐ | ☐ | ☐ | ☐ | |
| Safari | Desktop | ☐ | ☐ | ☐ | ☐ | |
| Safari | iPhone | ☐ | ☐ | ☐ | ☐ | |
| Chrome | Android | ☐ | ☐ | ☐ | ☐ | |

---

## Edge Cases & Scenarios

### Donor Journey (User Flow)

**Scenario 1: Donor wants to give by check**
1. Start on home page
2. Search/navigate to org detail page
3. See "Give by check" CTA
4. Click → lands on `/giving-via-checks`
5. Reads 4-step guide, gets mailing address from org page
6. Proceeds to write check
- **Expected:** Seamless flow, no broken links, clear next steps ☐

**Scenario 2: Donor has appreciated stock**
1. On org detail page, sees "Give appreciated stock" CTA
2. Click → lands on `/giving-via-stocks`
3. Learns 12-month holding rule, calls nonprofit
4. Nonprofit gives brokerage account details
5. Donor completes transfer
- **Expected:** Page provides all info needed to proceed ☐

**Scenario 3: Donor prefers PayPal/Facebook**
1. On org detail page, sees "Give via PayPal or Facebook" CTA
2. Click → lands on `/giving-via-routers`
3. Chooses platform, clicks link
4. Searches for nonprofit by name or EIN
5. Completes donation on platform
- **Expected:** Page clearly explains each platform, links work ☐

**Scenario 4: Donor has questions about tax treatment**
1. On any page, sees "This is not tax advice" disclaimer
2. Clicks IRS link to Pub 526
3. Reads official guidance
4. Consults tax professional
- **Expected:** Daanaa links, doesn't advise ☐

---

## Test Data & Setup

### Test Nonprofits (For Org Detail Testing)

Use these real orgs to test CTAs on live data:

| EIN | Org Name | Mailing Address | Notes |
|---|---|---|---|
| 52-1756991 | Direct Relief | 6 Mauch Chunk St, Easton, PA 18042 | Major org, full data |
| 91-1663519 | Charity: Water | 316 W 33rd St Fl 3, New York, NY 10001 | Known for giving options |
| 26-3049434 | National Park Foundation | 1420 K St NW, Washington, DC 20005 | Well-maintained records |

### Test Data Checklist

- [ ] Org detail pages load (no 500s)
- [ ] EIN visible and copy-able
- [ ] Mailing address shown (for checks)
- [ ] Secondary CTAs render correctly
- [ ] Links to giving methods are live

---

## Sign-Off Checklist

**Before QA Begins:**
- [ ] Test environment is fresh (no old build artifacts)
- [ ] Frontend build succeeded (`npm run build`)
- [ ] Droplet (production) is at last known-good version

**During QA:**
- [ ] All critical path tests marked ☐
- [ ] Screenshots taken of any issues (for bug reports)
- [ ] Links tested in real network (not just localhost)

**After QA:**
- [ ] No P0/P1 bugs found (critical failures)
- [ ] All external IRS/platform links verified (no redirects or 404s)
- [ ] Mobile experience passes (no layout breaks)
- [ ] QA sign-off: `_______________ Date: _____`

---

## Known Limitations & Won't-Test

- **Don't test full donation flows** — We link to external sites; they handle processing
- **Don't test nonprofit responses** — Verification is on org, not Daanaa
- **Don't test legal/tax accuracy** — That's the legal review gate (Week 1–2)
- **Don't load test** — Not needed for educational pages (low traffic)

---

## Failure Criteria (STOP & ESCALATE)

Any of these = stop testing, escalate to founder:
1. **500-level error on any giving page** → Rollback, investigate
2. **Any IRS link returns 404** → Update link before launch
3. **CTAs missing from org detail pages** → Code not deployed correctly
4. **"Daanaa processes" language anywhere** → Edit & retest
5. **Page takes >5 seconds to load** → Performance issue

---

## Success Criteria (PASS)

All of the following = ready to ship:
- ✅ All critical path tests pass (0 failures)
- ✅ All external links work (IRS, platforms)
- ✅ Mobile experience responsive (no layout breaks)
- ✅ No JavaScript errors in console
- ✅ CTAs visible & clickable on 100% of test orgs
- ✅ Copy audit clean (no smart quotes, correct language)
- ✅ Lighthouse score > 85
- ✅ QA sign-off obtained

---

**Test Lead:** Daanaa QA  
**Test Date:** 2026-08-02  
**Results:** TBD  
**Sign-Off:** _________________ Date: _____
