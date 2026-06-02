# Partnership Brief — Every.org

**Goal:** Give every one of the 1.8M U.S. nonprofits — especially the invisible 97%
with no website or donate button — a **zero-fee** working "give" path, with Daanaa
staying a discovery + hand-off layer that **never touches funds.**

**Why Every.org is the partner of record:** a nonprofit itself (aligned values, won't
extract), passes ~100% to the recipient org (processing covered by optional donor tips),
free Charity API, EIN-based donate links (`every.org/[EIN]/donate`), built for exactly
this. PayPal Giving Fund is the secondary fallback for truly dormant orgs (mails a check).

**Status:** outreach drafted, not yet sent. Send from `partners@daanaa.org`.

---

## One-pager (the brief to attach or paste)

**What Daanaa is.** A civic nonprofit-discovery platform (daanaa.org, live in beta).
We index all 1.8 million IRS-registered 501(c)(3)s — including the ~97% with no online
presence — and use AI to give each a plain-language mission, a peer-context financial
score, and a verified way to be found. Privacy-first: no donor accounts, no tracking,
giving records stay on the donor's device. Built by a solo founder using AI. Operated by
EcoMargins LLC (DBA Daanaa); Daanaa itself is free and non-commercial.

**The problem we solve together.** The invisible 97% can't *receive* money today — no
website, no processor, no donate button. Discovery without a give path is half a product.
Every.org already solves the receiving side for any org by EIN. Pairing Daanaa's discovery
of the long tail with Every.org's zero-fee receiving rail makes 1.8M orgs not just
findable but **giveable** — most for the first time ever.

**What we're asking for.**
1. **Charity API access** to deep-link / route donations to any org by EIN, with the
   long tail as the focus.
2. **Donate-ready / verified-status data** so we only ever surface a give path for an
   org that can actually receive (pairs with our IRS auto-revocation filter — we will not
   route to revoked orgs).
3. **Confirmation of the zero-fee-to-nonprofit model** and **for-profit-use terms** —
   Daanaa is free and civic but sits under an LLC; we want to use the API correctly.
4. A short intro call.

**What's in it for Every.org.** Qualified donation volume routed to the long tail of orgs
that have no other on-ramp; a discovery surface that sends donors to Every.org's give flow;
a mission-aligned partner that shares your "100% to the nonprofit" and transparency values.

**The boundary, stated plainly.** Daanaa never becomes the merchant of record and never
holds donor money. The donor lands on Every.org's give flow; Every.org remits to the org.
Zero fund-handling risk to you, by design.

---

## Outreach email (ready to send from partners@daanaa.org)

> **To:** partnerships@every.org (confirm correct address) · **Subject:** Daanaa × Every.org — a zero-fee give path for the invisible 97%
>
> Hi Every.org team,
>
> I'm Akbar, founder of Daanaa (daanaa.org) — a civic platform that indexes all 1.8
> million U.S. nonprofits, including the ~97% with no website or donate button, and uses
> AI to make them findable. We're live in beta.
>
> Discovery without a way to give is only half the product. The invisible orgs we surface
> have no way to *receive* money today. Every.org already solves that for any org by EIN —
> at zero fee to the nonprofit, which matters enormously to us. We'd like to route donors
> to your give flow as the on-ramp for the long tail. Daanaa never touches funds; the donor
> gives through Every.org and you remit to the org.
>
> Three things I'd love to figure out:
> 1. Charity API access for EIN-based give paths, focused on the long tail.
> 2. Verified donate-ready status so we only ever show a give path for an org that can
>    actually receive (we filter out IRS-revoked orgs).
> 3. The right terms — Daanaa is free and civic but operates under an LLC, so I want to use
>    the API correctly (non-commercial vs enterprise).
>
> Could we find 20 minutes? Mission-wise I think we're pointed at the exact same thing —
> getting support to the small organizations everyone else overlooks.
>
> Thanks,
> Akbar Khowaja · Founder, Daanaa · partners@daanaa.org · daanaa.org

---

## Open items this unblocks / depends on
- **G1 attorney review** — required before publicly promoting any "Give here" CTA
  (charitable-solicitation registration). The build is a two-way door; the public launch
  is gated here. (Blocked on lawyer funds.)
- **G2 IRS auto-revocation filter** — must suppress/badge give paths for revoked orgs
  before any go-live. Pair with Every.org's verified-status data.
- **Build:** EIN-router fallback give-path logic (direct link → Every.org → PPGF) behind a
  feature flag, ready to flip when G1+G2 clear. (Not started — deferred per founder's "open
  Every.org first" choice.)
- **PayPal Giving Fund** — secondary fallback for dormant/unbankable orgs (check by mail).
