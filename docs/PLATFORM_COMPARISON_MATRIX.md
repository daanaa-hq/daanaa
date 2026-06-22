# Nonprofit Platform Field Comparison Matrix

**Context:** Comprehensive audit of what data fields are collected, displayed, and verified by Candid, Charity Navigator, GiveWell, Facebook for Nonprofits, and Daanaa. This matrix identifies critical gaps and informs which fields Daanaa should prioritize.

---

## Field-by-Field Comparison

| **Data Field** | **Candid** | **Charity Navigator** | **GiveWell** | **Facebook for Nonprofits** | **Daanaa Current** |
|---|---|---|---|---|---|
| **Mission Statement** | Y / Y / N | Y / Y / N | Y / Y / Y | Y / Y / N | **Y / Y / N** |
| | (990-extracted, unverified) | (990-extracted, ~1-2 yr lag) | (site visits + interviews, verified) | (self-reported, org-gated) | (IRS 990 + AI-generated + scraped) |
| **Service Areas (Geographic)** | Y / Y / N | Y / Y / N | Y / Y / Y | Y / N / N | **Y / Y / N** |
| | (from 990, often vague) | (990, limited detail) | (verified by site visits) | (category only, not geography) | (IRS BMF + 990 / state focus only) |
| **Service Areas (Programmatic)** | Y / Y / N | Y / Y / N | Y / Y / Y | Y / N / N | **Partial / Partial / N** |
| | (990 description, unverified) | (from NTEE + 990, limited) | (detailed program breakdown verified) | (category only) | (NTEE codes + AI cause_tags, confidence unknown) |
| **Leadership (Executive Director)** | Y / Y / N | Y / Y / N | Y / Y / Y | N / N / N | **N / N / N** |
| | (name/title from 990, no credential check) | (name/title from 990 only, no tenure verification) | (full bio + experience + tenure, verified) | (not surfaced) | (not collected) |
| **Leadership (Board Chair)** | Y / Y / N | Y / Y / N | Y / Y / Y | N / N / N | **N / N / N** |
| | (from claimed profiles only if org claims) | (limited to 990 names, no detail) | (full board directory + tenure, verified) | (not surfaced) | (not collected) |
| **Leadership (Board Members)** | Y / Y / N | N / N / N | Y / Y / Y | N / N / N | **N / N / N** |
| | (if org claims profile, self-reported) | (not available) | (full directory with bios, verified) | (not available) | (not collected) |
| **Financial Data: Revenue** | Y / Y / Y | Y / Y / Y | Y / Y / Y | N / N / N | **Y / Y / Y** |
| | (990 Form line 1d, annual) | (990 verified, 1–2 yr lag) | (990 + verified by site visits) | (not available) | (IRS 990 + ProPublica, recent vintage) |
| **Financial Data: Total Expenses** | Y / Y / Y | Y / Y / Y | Y / Y / Y | N / N / N | **Y / Y / Y** |
| | (990 Form line 18, annual) | (990 verified) | (990 + verified) | (not available) | (IRS 990 + ProPublica) |
| **Financial Data: Net Assets** | Y / Y / Y | Y / Y / Y | Y / Y / Y | N / N / N | **Y / Y / Y** |
| | (990 Part I line 22) | (990 verified) | (990 + verified) | (not available) | (IRS 990) |
| **Financial Data: Program Expense %** | Y / Y / Y | Y / Y / Y | N / N / N | N / N / N | **Y / Y / Y** |
| | (calculated from 990, quality varies) | (990, Charity Navigator rating pillar) | (not used—outcome-based instead) | (not available) | (calculated from 990 Form lines) |
| **Financial Data: Months of Reserve** | Y / Y / Y | Y / Y / Y | N / N / N | N / N / N | **Y / Y / Y** |
| | (calculated, variable quality) | (calculated, used in ratings) | (not used—cash flow analysis instead) | (not available) | (calculated from 990 data) |
| **Financial Data: Audit Status** | Y / Y / Y | Y / Y / Y | Y / Y / Y | N / N / N | **N / N / N** |
| | (990 Schedule O, Part IV Part B) | (990, verification status flagged) | (mandatory for grants, verified) | (not available) | (not collected; gap) |
| **Awards / Certifications: B Corp** | Y / Y / N | Y / Y / N | N / N / N | Y / Y / N | **N / N / N** |
| | (self-claimed, not verified) | (if in 990, not verified) | (not tracked) | (displayed if claimed) | (not collected; gap) |
| **Awards / Certifications: GuideStar Gold / Platinum** | Y / Y / N | N / N / N | N / N / N | N / N / N | **N / N / N** |
| | (Candid's own badge, based on profile completeness, not accuracy) | (Candid-only, not used) | (not used) | (not used) | (not collected; gap) |
| **Awards / Certifications: Charity Navigator Rating** | N / N / N | Y / Y / Y | N / N / N | N / N / N | **N / N / N** |
| | (not available) | (Charity Navigator's own rating system) | (not used—GiveWell ratings are selective) | (not used) | (not collected; gap) |
| **Awards / Certifications: Nonprofit Excellence** | Y / Y / N | Y / Y / N | N / N / N | N / N / N | **N / N / N** |
| | (self-claimed, unverified) | (if claimed, not verified) | (not used) | (not used) | (not collected; gap) |
| **Program Descriptions (What the org does)** | Y / Y / N | Y / Y / N | Y / Y / Y | Y / N / N | **Y / Y / N** |
| | (from 990 narrative, unverified) | (from 990, 1–2 yr lag) | (verified by site visits, detailed outcomes) | (category + org story, not detailed program list) | (990 + AI-generated missions, quality = confidence unknown) |
| **Volunteer Opportunities** | Y / Y / N | N / N / N | N / N / N | Y / Y / N | **N / N / N** |
| | (self-submitted by orgs, no validation) | (not available) | (not available) | (org can list opportunities) | (not collected; gap) |
| **Volunteer Hours (Historical)** | Y / Y / N | N / N / N | N / N / N | N / N / N | **N / N / N** |
| | (self-reported, unvalidated) | (not available) | (not available) | (not available) | (not collected; gap) |
| **Donation Links** | Y / Y / N | Y / Y / N | Y / Y / Y | Y / Y / Y | **Y / Y / Y** |
| | (collected, minimal verification) | (linked, basic validation) | (direct links to funded orgs, verified) | (direct integration, org-gated) | (verified pipeline, confidence score tracked) |
| **Donation Link: Payment Processors Supported** | Y / Y / N | Y / Y / N | Y / Y / Y | Y / Y / Y | **Y / Y / Y** |
| | (displays platforms, not verified) | (displays, basic check) | (verified by team) | (displays, platform-verified) | (pipeline detects + classifies: Stripe, PayPal, Donorbox, etc.) |
| **Impact Metrics: Beneficiaries Served** | Y / Y / N | Y / Y / N | Y / Y / Y | Y / Y / N | **N / N / N** |
| | (from 990 Part VII, unverified) | (from 990, low confidence) | (verified by site visits + RCT data) | (self-reported in stories, unvalidated) | (not collected; gap) |
| **Impact Metrics: Outcomes (Cost per Outcome)** | N / N / N | Y / Y / N | Y / Y / Y | N / N / N | **N / N / N** |
| | (not available) | (research-backed via Impact Genome partnership) | (core metric, verified by independent RCTs) | (not available) | (not collected; gap) |
| **Impact Metrics: Program Activity Data** | Y / Y / N | N / N / N | Y / Y / Y | Y / Y / N | **N / N / N** |
| | (from 990 line 1d, unverified) | (not available) | (verified by site visits + data review) | (self-reported stories, unvalidated) | (not collected; gap) |
| **Team / Staff Info: Names & Titles** | Y / Y / N | Y / Y / N | Y / Y / Y | N / N / N | **N / N / N** |
| | (from claimed profiles or 990, limited) | (from 990 only, ~5 key roles) | (full organization chart, verified) | (not surfaced) | (not collected; gap) |
| **Team / Staff Info: Bios / Experience** | N / N / N | N / N / N | Y / Y / Y | N / N / N | **N / N / N** |
| | (not available) | (not available) | (full bios, credentials, tenure; verified) | (not available) | (not collected; gap) |
| **Team / Staff Info: Headcount / FTE** | Y / Y / Y | Y / Y / Y | N / N / N | N / N / N | **Y / Y / Y** |
| | (from 990 Form lines, annual) | (from 990, used in accountability rating) | (available via 990, not emphasized) | (not available) | (IRS 990 employee_count field) |
| **Legal Status (501(c)(3) Verification)** | Y / Y / Y | Y / Y / Y | Y / Y / Y | Y / Y / Y | **Y / Y / Y** |
| | (from IRS master file) | (from IRS, verified) | (verified by site visits) | (EIN + 2–3 week identity gate) | (IRS BMF verified) |
| **Legal Status (EIN)** | Y / Y / Y | Y / Y / Y | Y / Y / Y | Y / Y / Y | **Y / Y / Y** |
| | (public from IRS) | (public from IRS) | (published) | (verified during org setup) | (public, indexed) |
| **Legal Status (Tax-Exempt Ruling Status)** | Y / Y / Y | Y / Y / Y | Y / Y / Y | N / N / N | **Y / Y / Y** |
| | (IRS exempt/revoked/suspended flags) | (IRS verified) | (verified) | (not available) | (IRS ruling_date + irs_revoked flag, org_status field) |
| **Legal Status (Tax Year of Latest Filing)** | Y / Y / Y | Y / Y / Y | Y / Y / Y | N / N / N | **Y / Y / Y** |
| | (from 990 header) | (tracked as "latest_tax_year") | (verified) | (not available) | (latest_tax_year field) |
| **Year Founded** | Y / Y / N | Y / Y / N | Y / Y / Y | N / N / N | **N / N / N** |
| | (from 990 if org claims, unverified) | (from 990 if reported, low confidence) | (verified by site visits) | (not available) | (not collected; gap) |
| **Contact Info: Phone** | Y / Y / N | Y / Y / N | Y / Y / Y | N / N / N | **N / N / N** |
| | (from BMF or 990, often stale) | (from 990, often stale) | (verified by site visits) | (not available) | (not collected; gap) |
| **Contact Info: Mailing Address** | Y / Y / Y | Y / Y / Y | Y / Y / Y | Y / Y / Y | **Y / Y / Y** |
| | (from IRS BMF, high confidence) | (from IRS BMF, verified) | (verified by site) | (verified during org setup) | (BMF backfilled, street_address field, 95.7% coverage) |
| **Contact Info: Email Address** | Y / Y / N | Y / Y / N | Y / Y / Y | Y / Y / Y | **N / N / N** |
| | (from 990 or website scrape, unverified) | (from 990 if reported, low confidence) | (verified by site visits) | (verified, org-gated) | (not collected; gap) |
| **Contact Info: Website** | Y / Y / Y | Y / Y / Y | Y / Y / Y | Y / Y / Y | **Y / Y / Y** |
| | (from 990 or web research, variable quality) | (collected, basic validation) | (verified by site visits) | (org provides, verified) | (collected + health-checked; website_status + website_final_domain fields) |
| **Geographic Reach: Countries** | Y / Y / N | Y / Y / N | Y / Y / Y | N / N / N | **N / N / N** |
| | (from 990 if org reports, unverified) | (from 990, low confidence) | (verified by site visits) | (not available) | (not collected; gap) |
| **Geographic Reach: States** | Y / Y / Y | Y / Y / Y | Y / Y / Y | Y / Y / N | **Y / Y / Y** |
| | (from 990 and BMF, high confidence) | (from 990 + BMF, verified) | (verified by site) | (org location, not service area detail) | (STATE field from BMF + IRS) |
| **Geographic Reach: Local / Regional Focus** | Y / Y / N | Y / Y / N | Y / Y / Y | Y / N / N | **N / N / N** |
| | (from 990 narrative, unverified) | (from 990 description, low confidence) | (verified by site visits) | (can set region, not verified) | (not collected; gap) |
| **NTEE Classification** | Y / Y / Y | Y / Y / Y | Y / Y / Y | N / N / N | **Y / Y / Y** |
| | (from IRS 990, high confidence) | (from IRS, verified) | (understood but not emphasized) | (not tracked) | (NTEE1 + NTEECC fields indexed) |
| **Social Media Links** | Y / Y / N | Y / Y / N | Y / Y / Y | Y / Y / N | **N / N / N** |
| | (collected from 990 / website scrape, unverified) | (collected, not verified) | (verified by site visits) | (org can add, platform-verified) | (not collected; gap) |
| **Beneficiary Demographics** | Y / Y / N | Y / Y / N | Y / Y / Y | Y / Y / N | **N / N / N** |
| | (from 990 Part VII if reported, unverified) | (from 990, low confidence) | (verified by site visits + data review) | (self-reported in stories, unvalidated) | (not collected; gap) |
| **Overhead Ratio / Admin Expense %** | Y / Y / Y | Y / Y / Y | Y / Y / Y | N / N / N | **Y / Y / Y** |
| | (calculated from 990 Form, quality varies) | (calculated, used in Financial Health rating) | (calculated, not emphasized) | (not available) | (calculated from 990 data) |
| **Data Freshness / Last Updated** | Y / Y / Y | Y / Y / Y | Y / Y / Y | Y / Y / Y | **Y / Y / Y** |
| | (from 990 tax year, lag ~1–2 yr) | (tracked, lag ~1–2 yr for 990 data) | (verified by site visits, recent) | (org can update, real-time) | (updated_at field tracked; website_checked_at + donate_checked_at logged) |
| **Data Source Attribution** | Y / Y / Y | Y / Y / Y | Y / Y / Y | N / N / N | **Y / Y / Y** |
| | (IRS source clear, Candid updates noted) | (IRS source cited) | (methodology published, sources cited) | (org-provided not clearly attributed) | (source field: IRS vs. ProPublica vs. scraped; mission_source tracked) |

---

## Summary Scoring (Verification Intensity)

| Platform | **Data Collected from Org** | **Data Verified Against Independent Source** | **Data Revisited Periodically** | **Overall Verification Bar** |
|---|---|---|---|---|
| **Candid** | High (claims-based) | Low (IRS only) | 1–2 yr (990 lag) | **Low—self-report heavy** |
| **Charity Navigator** | Medium (990 focus) | Medium (990 trusted, no field audit) | 1–2 yr (990 lag) | **Medium—data-sourced but dated** |
| **GiveWell** | High (site visits) | High (RCTs, leadership interviews, data review) | Continuous (selective, ~20–50/yr) | **High—gold standard for funded orgs** |
| **Facebook for Nonprofits** | High (org-provided) | High (2–3 week EIN/leadership identity gate upfront) | Low after approval (no re-verification) | **Medium—strict gate, then trust** |
| **Daanaa** | Medium (IRS + scraped) | Medium-High (IRS verified, website health-checked, donation links verified) | Annual–quarterly (nightly pipeline) | **Medium-High—automated but not human-intensive** |

---

## Critical Gaps in Daanaa vs. Peers

### Tier 1 (High Impact, Moderate Effort)

| **Field** | **Why It Matters** | **Peers' Approach** | **Daanaa Gap** | **Recommendation** |
|---|---|---|---|---|
| **Audit Status (Financial Audit)** | Signals financial rigor + accountability | Candid, CN, GiveWell all track; used in CN ratings | Not collected | Parse 990 Schedule O Part IV Part B; surface "Independent Audit" badge if clean |
| **Year Founded** | Trust signal—longevity, institutional stability | All peers collect; GiveWell verifies by site visits | Not collected | Extract from 990 or website; mark confidence level |
| **Email Address** | Critical for outreach + contact validation | All peers collect; CN + GiveWell verify by site visits | Not collected | Scrape from website + add org-claim mechanism (future) |
| **Leadership (ED + Board Chair)** | Accountability + track record signal | All collect names; GiveWell does deep credential check | Not collected | Extract from 990 Part VII-A; mark "from 990 only" |
| **Outcomes / Cost-Per-Beneficiary** | Trust + impact signal for donors | GiveWell does RCTs; CN uses Impact Genome | Not collected | Research partnerships (Candid, academic researchers) for outcome data feeds |

### Tier 2 (Medium Impact, Higher Effort)

| **Field** | **Why It Matters** | **Peers' Approach** | **Daanaa Gap** | **Recommendation** |
|---|---|---|---|---|
| **Geographic Service Area (Detail)** | Helps donors target giving + avoid duplication | All peers collect; GiveWell verifies | Not collected (only org state) | Parse 990 Part I description + website; mark "self-reported from 990" |
| **Beneficiary Demographics** | Equity signal; helps donors find underserved communities | All collect; GiveWell verifies by site visits | Not collected | Extract from 990 Part VII if present; otherwise flag as "not reported" |
| **Program Activity Data** | Donor trust signal (concrete outputs) | GiveWell verifies; Candid collects from 990 | Not collected | Add optional org-claim form for program counts + impact stories |
| **Volunteer Opportunities** | Engagement + on-the-ground trust signal | Candid + Facebook collect; unverified | Not collected | Scrape from website (hidden gems search angle); future org-claim form |
| **Social Media Links** | Modern trust signal + engagement channel | All peers collect; unverified | Not collected | Scrape from website + add org-claim mechanism |

### Tier 3 (Lower Impact or Longer-term)

| **Field** | **Why It Matters** | **Peers' Approach** | **Daanaa Gap** | **Recommendation** |
|---|---|---|---|---|
| **Team Bios / Experience** | Deep accountability signal | GiveWell only; labor-intensive | Not collected | Research partnerships or future org-claim forms; low ROI without GiveWell-level gate |
| **Beneficiary Impact Metrics (RCT-verified)** | Gold-standard trust signal | GiveWell only | Not collected | Integrate academic partnerships (research roadmap, not MVP) |
| **Certifications (B Corp, etc.)** | Third-party validation; usually credible | All peers collect; unverified | Not collected | Scrape from website + add org-claim mechanism; low trust if self-claimed only |
| **Countries Served (International Reach)** | Helps segment giving | All peers collect; unverified | Not collected | Parse 990 narrative; low priority unless org-targeted |

---

## Recommended Daanaa 12-Month Roadmap

### **Months 1–2: Quick Wins (High ROI, Low Friction)**
1. **Audit Status** — Parse 990 Schedule O Part IV Part B
   - Badge: "Independently Audited" (trust signal)
   - Conditional display: only if "yes"
   - Effort: ~4 hours (SQL + 990 schema parsing)

2. **Year Founded** — Extract from 990 Part I / website
   - Display on org card + detail page ("Since 1994")
   - Confidence levels: "from 990" vs. "from website" vs. "estimated"
   - Effort: ~6 hours (web scrape + 990 parsing)

3. **ED + Board Chair Names** — Extract from 990 Part VII-A
   - Display on org detail page only (not in search)
   - Mark: "from 990 filing only, not verified" 
   - Effort: ~4 hours (990 schema parsing)

### **Months 3–4: Medium Effort**
4. **Email Address** — Web scrape + optional org-claim form
   - Prioritize website contact forms + domain email extraction
   - Mark confidence ("verified from website" vs. "claimed by org")
   - Effort: ~12 hours (scraper + org-claim infrastructure)

5. **Geographic Service Area Detail** — 990 narrative parsing
   - Extract "Serves X states" / "Serves Y countries" from Part I text
   - Confidence: "self-reported from 990"
   - Effort: ~8 hours (NLP on 990 text)

6. **Beneficiary Demographics** — Parse 990 Part VII
   - Age, race/ethnicity, income level if reported
   - Conditional display: only if data present
   - Effort: ~6 hours (990 schema extraction)

### **Months 5–6: Web Scraping Layer**
7. **Volunteer Opportunities** — Website scrape
   - Detect volunteer landing pages + forms
   - Confidence flag: "found on website"
   - Integrate with hidden gems search ("Has volunteer opportunities")
   - Effort: ~16 hours (web scraper + UI integration)

8. **Social Media Links** — Website scrape
   - Extract Facebook, Twitter, LinkedIn, Instagram, TikTok
   - Validation: HTTP HEAD check that link resolves
   - Effort: ~8 hours (scraper + validation)

9. **Certifications (B Corp, Nonprofit Excellence, etc.)** — Website scrape
   - Parse for badge images + certification text
   - Mark: "claimed on website, not verified by Daanaa"
   - Effort: ~8 hours (scraper + badge database)

### **Months 7–12: Strategic Partnerships**
10. **Outcomes Data** — Research partnerships
    - Reach out to Candid, Impact Genome, academic researchers
    - Goal: feed verified cost-per-outcome data for major cause areas
    - Effort: ~business development (12+ weeks negotiation)

11. **Org-Claim Forms** — Infrastructure for voluntary submissions
    - Allow orgs to claim + update profile info
    - Start with: program counts, impact stories, volunteer opportunities
    - Effort: ~20 hours (form infrastructure + validation logic)

12. **Leadership Bios** — Future org-claim form
    - Allow ED/board chair to submit bio + credentials
    - Mark: "claimed by org, not independently verified"
    - Effort: ~12 hours (follow-up to org-claim forms)

---

## Key Design Principles for New Fields

When adding any new field, ensure:

1. **Confidence Levels Always Visible**
   - "From 990" ≠ "From website" ≠ "From org claim" ≠ "Verified by Daanaa"
   - Example: "Year Founded: 1994 (from 990 filing)" vs. "Year Founded: ~1994 (from website)"

2. **Fail-Closed Design**
   - If field unverified or missing, don't display it
   - Better to show less data than misleading data
   - Exception: fields explicitly marked "self-reported"

3. **Stewardship Alignment**
   - No field that enables tracking or public comparison of giving activity
   - No field that enables negative public shaming (e.g., "worst overhead ratios")
   - All new fields must pass STEWARDSHIP.md + PRIVACY-INVARIANTS.md check

4. **Peer Parity Where Possible**
   - Don't try to out-GiveWell GiveWell (RCTs are their moat)
   - Daanaa's strength: breadth + transparency about what we don't know
   - Position as "informed discovery" not "definitive assessment"

---

## Competitor Positioning

| **Daanaa Strength** | **Candid** | **Charity Navigator** | **GiveWell** | **Facebook for Nonprofits** |
|---|---|---|---|---|
| **Coverage** | 1.87M orgs (broader than CN, same as Candid) | 1.87M orgs (same) | ~100 organizations (selective) | ~1.5M verified 501c3s (subset) |
| **Trust Signal Design** | Lamp tiers + peer context (not size-ranked) | Letter ratings (opaque weighting) | Intensive vetting (gold standard but narrow) | Category-based, not rated |
| **Privacy** | None / tracking-light | Limited | Strong (donors private) | Weak (social signals encouraged) |
| **Transparency** | Low (scores are black-box) | Medium (methodology public, weights opaque) | High (methodology + reasoning published) | Low (platform decisions opaque) |
| **Data Freshness** | 1–2 yr lag (990s) | 1–2 yr lag (990s) | Current (site visits) | Real-time (org-updated) |
| **Daanaa Edge** | **Daanaa combines breadth + peer context + confidence levels—transparency about what's verified and what's not** |

---

## Files to Update

- `docs/RESEARCH.md` — Add section "Platform Comparison"
- `frontend/src/pages/OrgDetailPage.tsx` — New data fields as they roll out
- `docs/METHODOLOGY.md` — Explain data sources + verification confidence for each field
- `DECISIONS.md` — Log why we chose each new field (ROI + stewardship fit)

