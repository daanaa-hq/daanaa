# Launch Blockers — Daanaa

**Last updated:** 2026-05-26
**Milestone:** Gate 2 (Credits & Infrastructure) → Gate 6 (Pre-Launch Readiness)

Split: what Akbar does vs. what Claude does once Akbar provides the credential/URL.

---

## You do (external account creation)

| Item | Why | Gate | Status |
|------|-----|------|--------|
| Twitter/X — grab @daanaa | Brand presence before someone else takes it | Pre-gate | ☐ |
| LinkedIn — Daanaa company page | Funder credibility, outreach surface | Gate 6 | ☐ |
| Cloudflare — DNS for daanaa.org | Soft launch requires domain pointing at server | Gate 2 | ☐ |
| Google Workspace — akbar@daanaa.org | Professional email before any outreach | Gate 2 | ☐ |
| GitHub — create daanaa-org/daanaa repo | Code needs a home before CI can be wired | Gate 2 | ☐ |
| Plausible.io — daanaa.org site | Analytics before launch | Gate 5 | ☐ |
| UptimeRobot — monitor daanaa.org/health | Free uptime monitoring, alerts if server goes down | Gate 5 | ☐ |
| Sentry — free tier account | Error tracking in production | Gate 5 | ☐ |
| Attorney consult — before About page / broad outreach | Solicitation registration + scoring liability | Gate 5 | ☐ |
| DBA filing — "Daanaa" under EcoMargins LLC | Legal name before any public-facing presence | Gate 1 | ☐ |

---

## Send me → I wire it

Once you complete the items above, send me the output and I'll handle the integration:

| What to send | What I'll do |
|-------------|--------------|
| Plausible site ID (looks like `daanaa.org` or a UUID) | Wire `<script>` snippet into frontend `index.html` |
| Sentry DSN (looks like `https://xxx@o0.ingest.sentry.io/0`) | Wire Sentry SDK into frontend + configure source maps |
| GitHub repo URL (e.g. `github.com/daanaa-org/daanaa`) | Push codebase, create branch structure, wire CI (GitHub Actions) |

---

## Cloudflare DNS records (ready to paste)

When you're in Cloudflare, add these for daanaa.org pointing to your server:

```
Type  Name    Value                   Proxy
A     @       [your server IP]        DNS only (grey cloud) to start
A     www     [your server IP]        DNS only
```

Set **SSL/TLS → Full (strict)** after HTTPS is working on the server.

**Server IP:** check with `curl ifconfig.me` on the Ryzen box.

---

## Attorney consult — what to bring

Bring these three files printed or linked:
- `STEWARDSHIP.md`
- `meritgiving-ops/strategy/mission-lock.md`
- The About page (once drafted)

**Priority questions:**
1. Does linking donors to nonprofit giving pages constitute "solicitation" under state statutes? Start with California + New York.
2. Does ProPublica's CC BY-NC-ND license restrict a future revenue model for Daanaa?
3. Should EcoMargins LLC add a DBA "Daanaa" now, or form MeritGiving LLC separately?
4. Which states require charitable solicitation registration, and does the URS cover us?

**Free paths to find an attorney:**
- Law school nonprofit clinic in your city
- State bar pro bono referral program
- Volunteer Lawyers for the Arts (VLA)

---

## DBA filing — "Daanaa" under EcoMargins LLC

File with the Texas Secretary of State (or your county clerk, depending on Texas rules for DBAs).
- Texas calls it an **Assumed Name Certificate**
- Fee: ~$25 at county clerk
- Required before using "Daanaa" on contracts, bank accounts, or publicly

Once filed: open a bank account under "EcoMargins LLC dba Daanaa" — this is the account that receives any grant money or tips.

---

## Sequencing recommendation

```
Now          → Grab @daanaa on Twitter/X (before someone else does)
This week    → Cloudflare DNS + DBA filing (unlock domain + legal name)
This week    → GitHub repo (unlock code push + CI)
Before outreach → Google Workspace + LinkedIn (professional presence)
Before launch   → Plausible + UptimeRobot + Sentry (observability)
Before About page → Attorney consult (legal sign-off)
```
