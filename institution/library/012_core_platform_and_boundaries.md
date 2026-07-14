# Core Platform and Sustainability Boundaries
Library Document 012 · Version 1.0 (Draft for Founder Decision)
Prepared 2026-07-13

## Purpose

Founder decisions FD-002 and F-003 require explicit boundaries:
1. **What exactly is free forever?** (FD-002)
2. **What donation-adjacent features are allowed?** (F-003)

This document proposes the boundaries and requests founder approval.

---

## FD-002: What Is "Free Forever"?

### Proposed Definition

**The Daanaa core platform (free forever):**

1. **Discovery and research** — browsing, search, filtering by cause/location/financial health, viewing any org's public profile
2. **Peer financial context** — scores, rankings, percentiles, archetype classification, health signals shown on org pages
3. **Organizational profiles** — publicly available data (name, location, revenue, NTEE category, website, mission, leadership via public records)
4. **Correction mechanism** — ability to view, challenge, and correct data on any org page (requires org verification to edit)
5. **Nonprofit dashboard** (claimed by that org) — access to custom mission, peer comparison, discovery metrics, profile completeness, volunteer interest aggregates, all owned by the organization
6. **Data portability** — export all entrusted data at any time
7. **Data deletion** — delete all Tier 2 data at any time

**What is NOT in core:**
- Advanced analytics or custom reports (reserved for paid services)
- Bulk data export API (reserved for paid partners)
- White-label or embedded instances (paid services)
- Consulting or advisory services (separate EcoMargins business)

### Rationale

The core platform answers the original question: "Help me understand this organization better." It remains free because:
- It costs little to operate at scale (search index, static pages, simple database queries)
- Restricting it would undermine trust (free discovery is the entire premise)
- Revenue models should enhance, never restrict, core function

---

## F-003: Donation Boundary

### Proposed Rules

**Daanaa will never:**
- Hold, receive, or route any charitable donations
- Settle, process, or handle donated money
- Take any percentage of, fee from, or commission on donations
- Issue receipts or serve as a merchant of record
- Create accounts that accept donations on behalf of nonprofits

**Daanaa will:**
- Link directly to the organization's own donation page (discovered via website scraping)
- Verify that link works and is controlled by the organization
- Display the verified link prominently on the organization's profile page
- Surface direct donation links from the organization's own website only (never intermediary platforms unless the organization claims them)

**Optional features that could be adjacent (pending approval):**
- "Add to my giving plan" — allow a donor to bookmark orgs in their private wallet before giving
- Private giving intent (e.g., "I intend to give $500 to this org") — stored in user's wallet, never shared, never used for outreach
- Export giving plan — user can download their bookmarks/intents for their own records
- Manual handoff — "I'm giving now" button that opens the org's link (doesn't track completion)

**Never adjacent to Daanaa:**
- Donation processing (use the org's own payment processor)
- Donor identity collection from Daanaa (collect on the org's site)
- Percentage-based fees (breaks the principle)
- Donor list consolidation (doesn't happen)
- EcoMargins marketing to donors (firewall prevents this)

### Rationale

Daanaa is a discovery and research tool, not a payment system. Staying out of the money flow:
- Avoids money-transmitter licensing and regulatory burden
- Keeps the trust model simple (we touch no money, so we can't be tempted)
- Allows nonprofits to use their own, familiar payment processors
- Prevents false sense of Daanaa as an intermediary

---

## Impact on Charter Promises

**Charter #1 (never take a cut):** ✓ Supported — Daanaa never touches donations

**Charter #2 (never sell inside):** ✓ Supported — core platform free, paid services separate, never visible in core UI

**Charter #3 (never use what you give us to sell):** ✓ Supported — Tier 2 firewall + no donor tracking across platforms

**Charter #5 (never charge for platform):** ✓ Supported — core definitions fixed

---

## Next Steps

**Founder decision required on:**
1. Is this definition of "core platform" (7 items listed) correct?
2. Are the donation boundary rules (4 nevers, 4 wills, optional features) acceptable?
3. Should optional "adjacent" features be published as possibilities, or left unmentioned until later?

**Implementation path (after approval):**
- Add this document to the institutional library
- Update the Charter if any wording changes needed
- Begin F-008 Resilience work (restore test, succession plan)
- Return to FD-005 (entity separation) with legal + operational triggers defined

---

## Relationship to Other Documents

- Extends **STEWARDSHIP.md** principles 1, 7, 8 (mission, independence, money)
- Aligns with **Charter promises** #1, #2, #3, #5
- Complements **VENDOR-POLICY.md** (external vendors can't buy Daanaa data)
- Supports **Data Classification** (Tier 2 separation) by clarifying it's not for sale/use

