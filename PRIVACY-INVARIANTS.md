# Privacy Invariants — Daanaa

Privacy is the product's core selling point and STEWARDSHIP principle 2. These are
**hard invariants**, not guidelines. `scripts/privacy_check.sh` enforces the
machine-checkable ones; the rest require human review on any change that touches them.

Run the check: `bash scripts/privacy_check.sh` (exits non-zero on violation).
Wire it as a pre-commit hook or CI step so the build fails if privacy regresses.

## Invariants

1. **No third-party trackers or analytics.** No Google Analytics/gtag, Meta/Facebook
   pixel, Segment, Mixpanel, Hotjar, PostHog, Sentry, or any external beacon in the
   frontend or index.html. (If analytics is ever added, it must be a self-hosted,
   cookieless, privacy-respecting provider per STEWARDSHIP principle 2.)

2. **Giving data is account-scoped, not public.** Wallet data (bookmarks and giving
   intent) is stored on the user's device (localStorage) by default. No account is
   required to use the wallet; browsing Daanaa and bookmarking orgs works without
   authentication. Users may optionally sign in with Google to enable cross-device
   wallet sync; synced data contains bookmarks and intent only, never transactions or
   donor identity. Wallet contents are never exposed publicly, never shared with third
   parties, never used for advertising or outreach. No donor identity may be tied to
   giving amounts or organization choices in any endpoint accessible without the owner's
   own auth token. Evidence: `frontend/src/contexts/WalletContext.tsx` (device-first
   localStorage primary, optional server sync).
   *(Changed 2026-06-27: Product QA found wallet remains device-first. 2026-06-14 note
   overstated auth requirement. Updated to match implementation and STEWARDSHIP.md
   correction. Revised 2026-08-11 to match Codex findings.)*

3. **No visitor IP retention.** The access log format must omit the client host
   (`%(h)`). IPs may be used transiently for rate-limiting (in-memory only) but never
   persisted to disk.

4. **CSP stays strict.** No `unsafe-eval`, no wildcard (`*`) in `script-src` or
   `connect-src`. The CSP is load-bearing for keeping localStorage unreadable by XSS.

5. **No donor identity tied to giving.** No endpoint may accept a donor's identity
   (name, email, phone) together with what they gave or intend to give. `link_feedback`
   and `waitlist` are anonymous/email-only by design.

6. **Minimal, labeled server PII.** The only non-public PII on the server is waitlist
   emails and org-claim data (org email, IRS address, verification PIN). Any new PII
   column requires explicit review and a note here.

7. **Volunteer = connect, don't collect.** Volunteer interest is sent from the user's
   own device (deep link), with a user-controlled anonymous/named + age-range
   disclosure. Daanaa stores no volunteer contact list, so there is nothing to harvest
   or spam.

8. **Tier 2 entity firewall.** Data entrusted to Daanaa (org_claims contact,
   attestation, and behavioral fields; waitlist; wallet; feedback; call records) is
   never used for prospecting, lead scoring, marketing, or consulting by any entity —
   including EcoMargins Consulting LLC, Daanaa's operating company — and is never sent
   to external AI services (local inference only). Full classification:
   `institution/library/011_data_classification.md`. Enforced by privacy_check.sh
   GATE 8. *(Added 2026-07-13: dual-brand structure adopted — Daanaa free platform +
   EcoMargins paid consulting under one LLC, separated by this firewall.)*

## Change protocol

Any change that touches an invariant above must: (a) update this file with the reason,
(b) keep `scripts/privacy_check.sh` green, and (c) be called out in the PR. Silent
weakening is a STEWARDSHIP principle 11 violation.
