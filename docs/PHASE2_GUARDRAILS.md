# Phase 2 Guardrails — Founder-Approved

**Date Approved:** 2026-07-27  
**Authority:** Founder approval  
**Scope:** Frontend integration of IRS eligibility helper  

---

## Core Rules (Non-Negotiable)

### 1. Revoked Organization Handling

**Search & Directory:**
- Hide revoked profiles from `/search`, `/directory`, org listing pages
- Never show donate CTA for revoked orgs
- Do NOT use language like "ineligible", "failed", or "revoked" in search results

**Direct Access:**
- Revoked profiles remain accessible via direct URL: `/org/[EIN]`
- Purpose: Transparency, donor verification, historical records
- Show full context on direct profile page: status + disclaimer + dates

**Donate Action:**
- Suppress normal donate button/CTA
- Replace with: "IRS revocation record found. Do not assume a contribution is tax-deductible without confirming the current IRS status."
- Link to: Organization's website (let them handle it)

### 2. Unknown & Unverified Records

**Before Donation:**
- Show neutral warning badge before any donate action
- Language: "Tax deductibility not verified" (never "ineligible" or "undeductible")
- Do NOT say: "likely tax-deductible" or "probably eligible"

**Warning Copy:**
- **Unverified (BMF-only):** "The latest IRS evidence does not include a complete verification. Check the IRS before giving."
- **Unknown (stale manifest):** "We do not have complete current IRS evidence for a tax-deductibility statement."

**Donation Still Allowed:**
- Unverified and unknown do NOT suppress donate CTA
- Warning appears, but donor can proceed
- This respects donor agency while being honest about limitations

### 3. Wallet & Giving Intent

**Historical Display:**
- Show entry: "Your giving intent for [Org] on [date]"
- Add: "Daanaa recorded this organization as not revoked on [date]"
- Add disclaimer: "This is not a tax receipt or determination of deductibility."

**MUST NOT Say:**
- ❌ "Your gift was deductible"
- ❌ "You gave to a tax-exempt organization" (might have been revoked since)
- ❌ "This org is eligible" (status may have changed)

**MUST Say:**
- ✓ "Daanaa recorded this status on [date]"
- ✓ "This is not a tax receipt"
- ✓ "See IRS Publication 526 for deductibility rules"

**Timestamps Required:**
- When wallet entry was created (intent date)
- When we recorded org status (manifest date)
- If org was later revoked: show revocation date separately

**No Retroactive Rewrites:**
- If org gets revoked, historical wallet entry shows both dates
- Example: "Intent: June 1, 2025 | Org revoked: Sept 15, 2025"
- Never change the "intent date" or "recorded date" retroactively

### 4. Pre-Donation Warnings

**Trigger:** User clicks "Donate" for unknown/unverified org

**Modal/Dialog Should Show:**
```
⚠️  Tax Deductibility Not Verified

Daanaa does not have complete current IRS evidence for [Org Name].

This means:
• We cannot confirm whether donations are tax-deductible
• You should verify directly with the organization or IRS
• Keep your own records of the donation for tax purposes

Still want to donate? [Visit Their Site] [Cancel]
```

**For Revoked Orgs:**
```
⛔ IRS Revocation Record Found

[Org Name] appears on the IRS auto-revocation list.

This means:
• Donations made after the revocation date are NOT tax-deductible
• Check the organization directly for reinstatement status
• You may be able to donate to an updated organization

Still want to proceed? [Organization Website] [Cancel]
```

### 5. Final Daily Gate Requirement

**Before Any Public Activation:**
- Run `bash scripts/v6_daily_operations_automated.sh`
- Confirm all gates pass (preflight, validation, revocation, integrity)
- Verify manifest is fresh (< 7 days old)
- Document results in deployment log

**No public changes go live until:**
- Daily gate passes ✓
- Manifest is current ✓
- Search/directory filtering working ✓
- Wallet disclaimers displaying ✓

---

## Phase 2 Deliverables (Frontend)

### 1. Components to Create/Update

**New Component: `IrsEligibilityContext.tsx`**
- Reusable badge + disclaimer display
- Props: `status`, `recordedAt`, `organizationName`
- Shows: badge text + explanation + sources

**Update 8 Pages:**
1. `OrganizationDetail.tsx` — Show status + disclaimer above donate
2. `SearchResults.tsx` — Filter hidden orgs, show warning badges
3. `DirectoryPage.tsx` — Filter hidden orgs
4. `DonateActionRow.tsx` — Suppress button for revoked, show warning for unknown
5. `WalletPage.tsx` — Show disclaimer + dates on historical entries
6. `HiddenGemsCarousel.tsx` — No hidden gem if currently revoked
7. `EventDiscovery.tsx` — Filter out currently revoked event hosts
8. `PeerContextResponses.tsx` — Show status in peer comparisons

### 2. API Changes (Phase 2, not Phase 1)

**Endpoint Updates:**
- `/api/org/:ein` — Add 4 eligibility fields (additive)
- `/api/search` — Add eligibility_status to results, filter revoked
- `/api/similar` — Add eligibility status
- `/api/hidden-gems` — Filter by eligibility status

**Response Format:**
```json
{
  "EIN": "111111111",
  "organization_name": "Example Org",
  "merit_score": 75,
  ...
  "irs_eligibility_status": "verified",
  "irs_eligibility_checked_at": "2026-07-27T19:56:59Z",
  "irs_eligibility_sources": ["Publication 78", "BMF subsection 03"],
  "irs_eligibility_explanation": "Current IRS BMF, Publication 78, and revocation records support tax-deductible eligibility."
}
```

### 3. Tests Required

**Backend Tests (already done in Phase 1):**
- ✓ All 5 statuses
- ✓ Public visibility rules
- ✓ Donate suppression
- ✓ Wallet disclaimers

**Frontend Tests (Phase 2):**
- Badge rendering per status
- Copy accuracy (no false deductibility claims)
- Donate button hidden for revoked
- Warning modal appears for unknown/unverified
- Wallet shows disclaimer + dates
- Direct URLs still accessible
- Search filters out revoked
- Financial scores visible regardless of eligibility status

---

## Deployment Checklist

**Before Frontend Build:**
- [ ] Diff review of all changed files
- [ ] All tests passing (backend + frontend)
- [ ] Copy review (no false deductibility claims)

**Before Live Activation:**
- [ ] Final daily gate passes
- [ ] Manifest is fresh (< 7 days)
- [ ] Search/directory filtering working
- [ ] Wallet disclaimers displaying correctly
- [ ] Direct URLs accessible and working
- [ ] Donate suppression for revoked verified
- [ ] No revoked orgs in hidden gems
- [ ] Founder approval of final deployment

---

## Steering Principles

1. **Evidence-based** — All status claims tied to IRS data
2. **Fair to BMF-only** — Marked unverified, not ineligible  
3. **No shame** — Neutral language, never weaponized
4. **Donor agency** — Warnings given, but donor decides
5. **Historical integrity** — Timestamps preserved, no rewrites
6. **Transparent** — Revoked orgs still discoverable via direct URL

---

## Contact & Approval

**Approved by:** Founder  
**Date:** 2026-07-27  
**Implementation:** Ready to proceed to Phase 2 frontend work

**Next step:** Show frontend diff before build/deploy for founder review
