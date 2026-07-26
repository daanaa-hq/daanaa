# Phase 4 Roadmap: Nonprofit Data Ownership & Governance

**Timeline:** Aug 5–31, 2026 (post-v6 launch)  
**Theme:** Give nonprofits agency over their profile data + trust verification layer

---

## Priority 1: Nonprofit Governance Editor (2–3 days)

**Why:** Nonprofits without recent 990 filings can now claim governance data directly, improving T3/T4 visibility and data ownership.

**Scope:**
- Create `/nonprofit/profile-settings` page with tabs
  - Basic: mission, website, donate link (existing)
  - **Governance (new)**: board_size, independent_members, policies, net_assets
  - Contact & Communications
  - Volunteer Settings

**Fields to add:**
```
Governance Section:
- Board Size (number input)
- Independent Board Members (number input)
- ☐ Has Conflict of Interest Policy (checkbox)
- ☐ Has Whistleblower Policy (checkbox)
- ☐ Has Document Retention Policy (checkbox)
- Net Assets / Total Assets (optional dollar amount)
```

**Backend:**
- Add to `org_claims` table: `board_size_claimed`, `board_independent_count_claimed`, `has_coi_policy_claimed`, etc.
- New endpoint: `PUT /api/organizations/{ein}/governance` (update claimed data)
- GET response: prefer claimed data over NCCS (claimed = higher trust tier)
- Add badge to org profile: "✓ Verified by Organization" for claimed governance

**Trust Hierarchy:**
```
T1 Direct: IRS 990 data (highest authority)
T2 Claimed: Nonprofit-attested governance (high authority) ← NEW
T3 NCCS: Public 990 data (medium)
T4 Inferred: Peer inference (medium)
```

**Success Metrics:**
- 10%+ of T3/T4 nonprofits claim governance data within 30 days
- Claimed data reduces T3→T1 upgrade wait time (don't need new 990 filing)
- Donor trust signal: "verified by organization" differentiates claimed from inferred

---

## Priority 2: NCCS Governance Display Improvements (1 day)

**Why:** Show governance data discovered from NCCS filings, not just inferred peer context.

**Scope:**
- Update FinancialContext component to show governance signals for T1+T2 orgs
- Display: board_size, policy flags (COI, whistleblower, doc retention) + data source
- When nonprofit claims data: show "Verified by [Org Name]" vs "From 2023 Filing"

**Fields to surface:**
- Board Size & Independent Members
- Conflict of Interest Policy (yes/no)
- Whistleblower Policy (yes/no)
- Document Retention Policy (yes/no)

---

## Priority 3: Governance Data Quality Pipeline (1–2 days)

**Why:** Bulk-verify claimed governance data + flag outliers for follow-up.

**Scope:**
- Batch QA script: compare claimed vs. NCCS data for discrepancies
- Flag nonprofits where claimed data conflicts with recent 990 (manual review)
- Monthly digest: "X orgs claimed governance data; Y conflicts found"
- Notify org: "Your claimed board size differs from your 2023 990 by X members — verify?"

---

## Priority 4: Trust Badges & Verification Layer (2 days)

**Why:** Donors see at-a-glance which org data is verified vs. inferred vs. claimed.

**Scope:**
- Add trust indicator badges:
  - 🔒 Direct: "Org's actual 990 data"
  - ✓ Claimed: "Verified by organization"
  - 📊 Inferred: "Based on similar organizations"
  - ℹ️ Limited: "Category-level context only"
- Update org detail page: show data source + freshness date (e.g., "2023 990 filing")

---

## Dependencies & Sequencing

1. **Phase 3 complete:** v6 launch + legal sign-off (Aug 5)
2. **Priority 1** (Nonprofit Governance Editor) → unblocks priorities 2–4
3. **Priorities 2–4** run in parallel (governance display, QA pipeline, trust badges)

---

## Acceptance Criteria (Phase 4 Complete)

- [ ] Nonprofits can edit governance data from profile settings
- [ ] Claimed data appears on org profile with "✓ Verified" badge
- [ ] Governance data (board_size, policies) displays on T1+T2 org pages
- [ ] Trust badges clearly distinguish direct/claimed/inferred/limited data
- [ ] 10%+ of T3/T4 nonprofits have claimed governance data within 30 days
- [ ] No conflicts between claimed and NCCS data (or flagged + resolved)

---

## Notes

- **Stewardship alignment:** P2 (data ownership) + P3 (evidence-based verification) + P9 (explainability)
- **Unblocks:** T3/T4 orgs no longer need to wait for 990 filing to improve their profile
- **Future:** Could add claimed financials (revenue, expenses, reserves) in Phase 5

---

**Owner:** TBD  
**Est. Effort:** 5–7 days total (all priorities)  
**Estimate Date:** 2026-08-31
