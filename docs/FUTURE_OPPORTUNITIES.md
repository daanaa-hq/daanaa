# Future Opportunities (Post-Legal, Optional Revenue)

**Deferred initiatives.** These are valuable but create complexity or require legal clarity. Revisit after G1 legal review.

---

## Donation Letter Service (Post-G1, Optional)

**What:** Daanaa generates IRS §170(f)(8) donation receipt letters on behalf of nonprofits.

**Why deferred:** 
- Requires storing donation transaction data (email + amount + date)
- Potentially makes us "part of the transaction pipeline"
- Violates stewardship principle: "We don't touch money or transaction data"
- Needs legal review (G1) to clarify liability + data handling

**Legal questions (for attorney, G1):**
1. Can we legally generate receipts as org's agent without storing donation data?
2. If org uses Every.org or external processor, can we receive donation events without "touching the transaction"?
3. What's the liability if a receipt is incorrect or a donation is disputed?
4. Are there data privacy implications for storing donor emails?

**If legal approves:** 
- Could launch as paid service (G3+) for small nonprofits who lack receipt infrastructure
- Premium feature: $0.50–$2 per letter
- Org controls accuracy (they pre-authorize what we send)
- We issue on their behalf, not as merchant of record

**If legal doesn't approve:**
- Nonprofits use their own email service (Mailchimp, Constant Contact)
- Daanaa provides template (they generate + send)
- We stay out of the transaction loop entirely

**Timeline:** Revisit Q3 2026 (after G1 legal decision).

---

## Nonprofit Group Purchasing (GPO) — Post-G3

**What:** Daanaa facilitates bulk discounts on software, insurance, payment processing for member nonprofits.

**Why deferred:**
- Requires nonprofit adoption (100+ claimed orgs) = G3 milestone
- Needs legal entity + bylaws (GPO formation)
- Vendor negotiations complex (pricing, liability, member support)

**Current plan:**
- G3: Survey claimed orgs on top overspend categories
- Decision gate: Build vs. defer based on demand + fit
- If yes: Form separate nonprofit GPO, Daanaa is founding member
- Revenue: margin on vendor deals (~5–15%)

**Why it matters:**
- Second revenue stream (after services)
- Solves real nonprofit pain (payment processing fees = #1 overspend)
- Drives claiming adoption (nonprofits claim → access GPO)

**Timeline:** Q4 2026 (post-G3 survey).

---

## Donor Giving Portfolio (Private, Encrypted)

**What:** Donors can track their giving across multiple orgs (private, device-local or encrypted).

**Why deferred:**
- Requires secure data storage (encrypted or device-local)
- Creates donor profile (potential privacy concern)
- May encourage "giving performance" (not stewardship-aligned)

**Current plan:**
- Phase 4 (post-G4): If retention data shows demand
- Must be opt-in + explicitly private (never visible to others)
- Never used for re-engagement nudges or comparisons
- Behavioral psychology check: Does this respect autonomy or create pressure?

**If we do it:**
- Device-local (no sync) is best (zero server storage)
- Encrypted sync is okay (strong safeguards)
- Dashboard showing "you gave $X to 5 orgs" is useful (personal insight)
- Showing "other donors gave Y" is NOT (comparison pressure)

**Timeline:** Post-G4 (2027+), if data supports it.

---

## Org Impact Stories (Opt-In, No Burden)

**What:** Orgs can add impact updates to their Daanaa page (optional).

**Why deferred:**
- Creates pressure on orgs to "perform" / post regularly
- Violates stewardship: we don't want orgs diverting focus to Daanaa updates
- Better served by orgs' own channels (newsletter, website, social)

**Better approach:**
- Recommend orgs link their own newsletter / blog
- Don't ask them to create content FOR Daanaa
- Let their existing channels be the source of truth

**If we do it:**
- Optional (no pressure)
- One-click integration (link their existing newsletter)
- No "posting to Daanaa" required
- Not tracked or ranked

**Timeline:** Never, unless orgs request it (unlikely).

---

## Peer Recommendations (Careful Design)

**What:** "Similar orgs in your peer group" suggestions (geographic, NTEE, financial band).

**Why careful:**
- Could create comparison pressure (social proof backfire)
- Could suggest one org over another (we don't rank)
- Could be seen as algorithmic curation (violates independence principle)

**Safe version:**
- Show peer group: "This org is in the top 25% of financial health in its peer group"
- Show related causes: "Other orgs working on [cause] in [location]"
- Never show: "Donors like you also support X" (comparison)
- Never rank: "Best nonprofits" or "Top rated"

**Timeline:** Phase 4 (G4+), with strong behavioral psychology review.

---

## Behavioral Psychology Review Gate

**Before any future feature ships:**
1. Does this respect donor autonomy?
2. Does this create pressure or guilt?
3. Does this add work to nonprofits?
4. Does this compromise our independence?
5. Could this trigger reactance (pushback)?

**If you add a behavioral psychologist to your board/advisory, they're the final gate on these.**

---

## Summary: What We're NOT Building (Yet)

| Feature | Why Deferred | Revisit When |
|---------|-------------|---------------|
| Donation letters | Data privacy + transaction involvement | After G1 legal review |
| Org impact stories | Creates pressure on orgs | Never (unless orgs ask) |
| Donor email campaigns | Triggers reactance + nudging | Never (against stewardship) |
| GPO | Needs nonprofit adoption + legal entity | Post-G3 (100+ claimed orgs) |
| Gamification | Creates guilt + obligation | Never (behavioral backfire) |
| Social proof displays | Creates comparison anxiety | Never |
| Follower counts (public) | Creates performance pressure | Never |

---

## The Principle

**We defer complexity until:**
1. Legal clarity (G1)
2. Nonprofit adoption (G3)
3. User demand (signals)
4. Behavioral psychology sign-off (no dark patterns)
5. Stewardship alignment (principles pass)

**This keeps us focused on what we do best: simple, honest nonprofit discovery.**
