# Phase 1 Complete — Comprehensive Accessibility & Confidence Fix

## 🎯 Three-Part Plan (Execute in Order)

### PART 1: Typography Utility Migration (33 pages)
**Goal:** Replace 623 inline `style={{ fontSize: 'clamp...' }}` with utility classes

**Pages affected:** About, OpenData, ComparePage, Security, ClaimSuccess, Approach, NotFound, GuildReferral, SectorHealth, EventDetailPage, Legal, ForNonprofits, Governance, TiersPage, MeetInvisible, MemberBenefits, OrganizationDetail, Methodology2, SettingsPage, Partners, Privacy, OrgClaimEditor, ForVendors, Charter, Terms, CategoryPage, VolunteerSearch, ClaimVerify, CauseSpotlight, VendorPolicy, Home, Directory, WhyDaanaa

**Execution:**
- Systematic find/replace: Map inline clamp() patterns to h1-display/h2-display/h3-display
- Validate: Build clean, no console errors
- Commit: One atomic commit with all replacements

**Estimate:** 2.5 hours

---

### PART 2: Border & Color Contrast Fixes (All pages)
**Dark mode borders:**
- Navy Mid (1.22:1 invisible) → Replace with Muted Cream or Light Grey
- 23 instances to fix

**Light mode borders:**
- Light Grey (476 instances, 1.22:1) → Replace with Navy Mid or charcoal
- Light Cream (78 instances, 1.14:1) → Replace with Navy Mid or charcoal  
- Muted Cream (46 instances, 1.49:1) → Replace with Navy Mid or charcoal

**Strategy:** Create theme-aware border utilities in CSS, replace inline border colors

**Estimate:** 2 hours

---

### PART 3: Confidence Badges (20 pages)
**New Component:** ConfidenceBadge.tsx
- High: 17.9% (direct 990 data)
- Good: 13.1% (NTEE-only)
- Low: 68.9% (no ranking)

**Integration Pages (20):**
- OrganizationDetail.tsx (primary)
- Directory.tsx, CategoryPage.tsx, ComparePage.tsx
- ResearchDashboard.tsx, Methodology2.tsx
- All secondary pages showing scores

**Execution:**
- Create component with Stewardship P3 messaging
- Integrate into pages displaying org scores
- Test on real orgs

**Estimate:** 2 hours

---

## Total Effort: ~6.5 hours
- Part 1: 2.5 hours (typography)
- Part 2: 2 hours (borders)
- Part 3: 2 hours (confidence badges)

**Quality bar:** All builds clean, no regressions, WCAG AA contrast throughout, Stewardship P3/P4/P6 aligned

---

## Execution Order (Start Now)

1. ✅ Part 1 — Utility migration (33 pages)
2. ✅ Part 2 — Border fixes (all pages)
3. ✅ Part 3 — Confidence badges (20 pages)
4. ✅ Final commit + verification

Starting Part 1 now.
