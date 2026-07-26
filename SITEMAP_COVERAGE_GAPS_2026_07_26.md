# Sitemap Coverage Gaps Analysis (2026-07-26)

## Executive Summary

**Total pages found:** 60 files in `frontend/src/pages/`  
**Pages covered by audits:** 17 (28%)  
**Pages NOT covered:** 43 (72%)  
**Critical gaps:** Volunteer pages (3), giving flow (1), org claiming (3), partner pages (4)

---

## Audit Coverage Recap

### ✅ Currently Covered (17 pages)

| Page | Audit | Covered in |
|------|-------|-----------|
| Home.tsx | Typography | Font size, line-height, contrast |
| About.tsx | Typography + Methodology | Font size, line-height, contrast + copy links |
| Approach.tsx | Typography + Methodology | Font size, line-height, contrast + copy links |
| Charter.tsx | Typography | Font size, line-height, contrast |
| Legal.tsx | Typography | Font size, line-height, contrast |
| MemberBenefits.tsx | Typography | Font size, line-height, contrast |
| Security.tsx | Typography | Font size, line-height, contrast |
| ForNonprofits.tsx | Typography | Font size, line-height, contrast |
| ForVendors.tsx | Typography | Font size, line-height, contrast |
| Governance.tsx | Typography | Font size, line-height, contrast |
| Methodology2.tsx | Typography + Data + Methodology | Font size, line-height, contrast + data viz + copy |
| OrganizationDetail.tsx | Typography + Data + Methodology | Font size, line-height, contrast + confidence badge + copy |
| Directory.tsx | Data Coverage | Scoring display + confidence levels |
| CategoryPage.tsx | Typography + Data | Font size, line-height, contrast + scoring display |
| EventDetailPage.tsx | Typography | Font size, line-height, contrast |
| ResearchDashboard.tsx | Data Coverage | Data viz + stat displays |
| WalletPage.tsx | Data Coverage | Giving flow display |

---

## 🔴 Critical Gaps (43 pages not covered)

### TIER 1: USER-FACING PAGES (Need all three audits applied)

#### Volunteer Ecosystem (3 pages — NEW FEATURE)
- `VolunteerDiscoveryPage.tsx` — Volunteer search/discovery UI
- `VolunteerSearch.tsx` — Volunteer search results
- `VolunteerSubmission.tsx` — Volunteer event submission form
- **Impact:** Volunteer theme/typography NOT checked; no volunteer org/event scoring display audit
- **Fix:** Apply typography fixes + check if these pages display org scores

#### Giving Flow (1 critical page)
- `DonationReceipt.tsx` — Post-donation confirmation
- **Impact:** User-visible; typography not checked; may display org info
- **Fix:** Apply typography + data coverage checks

#### Organization Management (4 pages)
- `OrgClaimEditor.tsx` — Nonprofit editing their org claim
- `ClaimSuccess.tsx` — Claim confirmation
- `ClaimVerify.tsx` — Claim verification flow
- `NonprofitVerification.tsx` — Verification workflow
- **Impact:** Org-facing; typography not checked; displays org data
- **Fix:** Apply typography + check if org financial data shown

#### Partner/Vendor Pages (4 pages)
- `GuildPage.tsx` — Partner guild/community page
- `GuildReferral.tsx` — Partner referral page
- `PartnerDetail.tsx` — Individual partner profile
- `Partners.tsx` — Partner directory
- **Impact:** Partner-facing; typography not checked; may display org counts/stats
- **Fix:** Apply typography + check if partner sees aggregated org scores

#### Compare & Explore (2 pages)
- `ComparePage.tsx` — Side-by-side org comparison
- `CauseSpotlight.tsx` — Cause spotlight/rotation page
- **Impact:** Core user feature; typography not checked; displays multiple org scores
- **Fix:** Apply typography + data coverage + confidence badges

#### Admin/Analytics Dashboards (7 pages)
- `AdminPage.tsx` — Admin dashboard root
- `AdminCampaigns.tsx` — Campaign management
- `AdminOperations.tsx` — Operational admin
- `DashboardHub.tsx` — Analytics hub
- `LearningDashboard.tsx` — Learning/insights dashboard
- `SocialMediaDashboard.tsx` — Social content admin
- `EmailAutomationDashboard.tsx` — Email automation
- **Impact:** Internal only; typography not critical but should be consistent; may display org scores
- **Fix:** Apply typography for consistency; check score display

#### Research & Insights (3 pages)
- `OpenData.tsx` — Open data portal/exports
- `SectorHealth.tsx` — Sector-level health analytics
- `TiersPage.tsx` — Tier system explanation
- **Impact:** Public research pages; typography not checked; heavy data visualization
- **Fix:** Apply typography + verify data confidence explanations match methodology

#### User Account/Settings (2 pages)
- `SettingsPage.tsx` — User settings
- `ProfileContextsPage.tsx` — User profile/contexts
- **Impact:** User-facing; typography not checked
- **Fix:** Apply typography

#### Special/Other (8 pages)
- `Feedback.tsx` — Feedback form
- `DonorFeedback.tsx` — Donor feedback
- `GuidedDiscovery.tsx` — Guided discovery UI (older feature?)
- `InvisibleLight.tsx` — Special/branded page
- `MeetInvisible.tsx` — Special event/meeting page
- `NotFound.tsx` — 404 error page
- `PilotSignup.tsx` — Pilot signup
- `WhyDaanaa.tsx` — Marketing/why page
- **Impact:** Mostly marketing/support; typography should be consistent
- **Fix:** Apply typography

#### Legal/Compliance (3 pages)
- `Privacy.tsx` — Privacy page (different from PrivacyPolicy.tsx?)
- `PrivacyPolicy.tsx` — Privacy policy (duplicate of Privacy.tsx?)
- `Terms.tsx` — Terms (different from Legal.tsx?)
- `VendorPolicy.tsx` — Vendor policy
- `Principles.tsx` — Principles page (related to charter?)
- **Impact:** Legal/compliance; typography not checked; some appear to be duplicates
- **Fix:** Apply typography; consolidate duplicates

#### Verification & Other (3 pages)
- `VerificationDashboard.tsx` — Verification workflow admin
- `NonprofitDashboard.tsx` — Nonprofit admin dashboard
- `EventLogHours.tsx` — Volunteer hour logging
- **Impact:** Mixed; some internal, some partner-facing; typography not checked
- **Fix:** Apply typography where user-facing

---

## Recommended Fixes (by priority)

### Priority 1: Critical User Paths (Fix immediately)

| Page | Gaps | Action |
|------|------|--------|
| VolunteerDiscoveryPage.tsx | Typography + data coverage | Add to audits; verify org/event display |
| VolunteerSearch.tsx | Typography + data coverage | Add to audits; check score display |
| VolunteerSubmission.tsx | Typography | Add to typography audit |
| DonationReceipt.tsx | Typography + data coverage | Add to audits; check org display |
| ComparePage.tsx | Typography + data coverage + confidence | Add to audits; update for v6 tiers |

### Priority 2: Org/Partner-Facing (Fix before org claiming goes live)

| Page | Gaps | Action |
|------|------|--------|
| OrgClaimEditor.tsx | Typography | Add to typography audit |
| NonprofitDashboard.tsx | Typography + data coverage | Add to audits |
| GuildPage.tsx | Typography | Add to typography audit |
| PartnerDetail.tsx | Typography + data coverage | Add to audits |

### Priority 3: Research & Insights (Fix before publishing research)

| Page | Gaps | Action |
|------|------|--------|
| OpenData.tsx | Typography + methodology links | Add to audits |
| SectorHealth.tsx | Typography + confidence messaging | Add to audits |
| TiersPage.tsx | Typography + v6 tier explanation | Add to audits |

### Priority 4: Legal & Marketing (Fix during brand/design polish)

All remaining pages need typography (line-height 1.6, light-mode gold fix, font-size standardization).

---

## Updated Coverage Plan

### Phase 1: Extend Audits (This week)

**New pages to add to existing audits:**

**THEME_TYPOGRAPHY_AUDIT:**
- Add all 60 pages to "ALL pages" line-height and contrast sections (currently implied, make explicit)
- Add specific font-size entries for: VolunteerDiscoveryPage, DonationReceipt, ComparePage, CauseSpotlight, OpenData, SectorHealth, TiersPage

**DATA_COVERAGE_GAPS:**
- Add: VolunteerDiscoveryPage, VolunteerSearch, ComparePage, CauseSpotlight, OpenData, SectorHealth, TiersPage, NonprofitDashboard, OrgClaimEditor, PartnerDetail, GuildPage

**METHODOLOGY_UPDATES_NEEDED:**
- Add: OpenData, SectorHealth, TiersPage as secondary pages that should link to methodology

### Phase 2: Implement (After audits extended)

1. Typography fixes (1.5 hours) — apply to ALL 60 pages
2. Data confidence badges (1 hour) — apply to pages that show org scores
3. Methodology links (30 min) — update secondary pages
4. Volunteer page checks (1 hour) — new feature, needs complete audit

---

## Files to Update

**Create/update:**
- ✏️ THEME_TYPOGRAPHY_AUDIT_2026_07_26.md — Add "ALL 60 pages" explicit list
- ✏️ DATA_COVERAGE_GAPS_2026_07_26.md — Add 11+ pages showing org data
- ✏️ METHODOLOGY_UPDATES_NEEDED.md — Add research pages

**Then commit together:**
```bash
git add *.md && git commit -m "docs: extend audits to full 60-page sitemap"
```

---

**Status:** Gap analysis complete. Ready to extend audits.  
**Next:** Approve extending audits, then implement Phase 1 typography fixes.
