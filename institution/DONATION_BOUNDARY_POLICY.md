# Donation Boundary Policy

**Status:** Adopted and binding · 2026-07-14  
**Authority:** Founder decision (FD-003) · Stewardship Principle 8 (never handle funds)  
**Applies to:** Every feature, workflow, and external integration at Daanaa

---

## The Boundary

Daanaa is a discovery and research platform, not a payment system. **Daanaa never receives, holds, routes, settles, or takes a percentage of charitable donations.**

This boundary is enforced in product design, not just in policy. It is non-negotiable.

---

## What Daanaa Will Never Do

1. **Never accept donations.** No donation form, no payment processor, no donor account, no giving transaction originates from Daanaa.

2. **Never hold money.** No Daanaa account ever holds donated funds, even temporarily. No escrow, no clearing account, no custodial relationship.

3. **Never process donations as merchant of record.** Daanaa is never the entity between donor and organization. Donors give directly to organizations through the organization's own payment processor.

4. **Never take a cut.** No percentage fee, no fixed fee per transaction, no commission on donations processed by organizations using Daanaa.

---

## What Daanaa Will Do

1. **Link to the organization's own donation page.** Daanaa discovers the organization's public donation URL (from their website), verifies it works and is controlled by the organization, and displays it prominently on the organization's profile page.

2. **Verify donation links are real.** Daanaa tests that the link is live, returns a 200 response, and is the organization's own URL (not a third-party re-router unless the organization explicitly claims it).

3. **Surface direct links only.** The donation URL comes from the organization's own website or is explicitly claimed by the organization in their dashboard. Daanaa never invent or re-route donations.

4. **Display high-confidence links prominently.** Donation links with ≥90 confidence appear in a "Give" button/section on the organization's profile. Links <70 confidence are flagged for human review or not surfaced.

---

## Optional Features (May Be Built in Future)

These features do NOT cross the boundary because they keep money and merchant relationships on the organization's side:

- **"Add to giving plan" (private bookmarking).** User creates a private list of organizations they intend to support. This is stored in the user's own Daanaa wallet (Tier 2 data, private, never shared). No money moves; no org is notified.

- **Private giving intent.** User records "I intend to give $500 to this org" in their personal wallet. This is a reminder for the donor, not a transaction. The org never sees it unless the donor tells them.

- **Export giving plan.** User can download their bookmarks and intents for their own records. Useful for end-of-year reporting or sharing with an advisor.

- **Manual handoff.** After browsing an org's profile, a button says "I'm ready to give" and opens the organization's donation link in a new tab. No tracking of completion, no receipt issued by Daanaa, no follow-up by Daanaa.

---

## Features That Cross the Boundary (Forbidden)

- Collecting donor identity (name, email, phone) as part of a donation flow inside Daanaa
- Processing any payment, even if passed through to the organization
- Issuing receipts or tax documentation
- Creating a donor database that could be used for marketing or contact
- Charging the organization a setup fee to list their donation link
- Taking a cut of donations as payment for Daanaa services
- Creating a "consolidated giving" account that pools donations from multiple donors
- Storing credit card numbers or payment methods
- Receiving donations on behalf of organizations, even if passed through the next day

---

## Relationship to Charter and Stewardship

**Charter Promise #1 (never take a cut):**  
This policy operationalizes that promise. Daanaa's role stops at the link. Money never enters Daanaa.

**Stewardship Principle 8 (never control donor funds):**  
This policy ensures Daanaa stays operationally independent and never becomes liable for regulatory oversight (money transmitter, charitable solicitation licensing, etc.).

**Stewardship Principle 1 (mission before growth):**  
This policy means Daanaa's revenue model (if any) must come from non-donation sources and must never incentivize taking a cut of giving.

---

## Implementation Guidance for Engineering

**In API and frontend:**
- Never build a donation acceptance endpoint
- Never store credit card data or payment processor credentials
- Never create a "merchant account" or "giving account" in Daanaa's database
- `donate_url` field in `registry_enriched` stores only the link itself; no transaction data follows it

**In integrations:**
- Stripe, PayPal, Square, etc. may be used to process Daanaa's own operational payments (e.g., server hosting), but never to process donations on behalf of organizations
- No donation router (GiveWP, GiveDirectly, etc.) ever connects Daanaa's database to a payment pipeline

**In product vision:**
- The "giving journey" ends at the organization's link
- Daanaa's job is "Go here." Not "Give here."
- If a future feature involves money, it crosses this boundary and requires explicit founder approval and a separate policy change

---

## Exception Process

If a future feature would appear to approach this boundary (e.g., "nonprofit fundraising toolkit"), it must:

1. Be explicitly named in a new founder decision (not assumed to be OK under this policy)
2. Have a legal opinion on money-transmitter and charitable-solicitation regulations
3. Update this policy document with the new boundary
4. Be announced publicly if it changes Daanaa's role

Silent creep across this boundary is a Stewardship Principle 11 (silent weakening) violation.

---

## Quarterly Self-Audit Question

Every quarter, this document is reviewed with one simple question:

**"Did any workflow, feature, integration, or external relationship cause Daanaa to receive, hold, route, process, or take a cut of any donation this quarter?"**

Answer recorded in `STEWARDSHIP.md` compliance log. Answer must be NO for Daanaa to remain in compliance with Stewardship Principle 8, Charter Promise #1, and this policy.

---

**Adopted by:** Founder decision FD-003, 2026-07-14  
**Effective immediately.**

