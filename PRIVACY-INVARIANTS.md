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

2. **Giving data never leaves the device.** Wallet data (`merit_wallet_donations`,
   `merit_wallet_volunteer`) lives in localStorage only. It must never be sent to any
   server endpoint. There is no server-side store of donor giving activity.

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

## Change protocol

Any change that touches an invariant above must: (a) update this file with the reason,
(b) keep `scripts/privacy_check.sh` green, and (c) be called out in the PR. Silent
weakening is a STEWARDSHIP principle 11 violation.
