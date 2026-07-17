# Daanaa: Infrastructure for Giving

**The vision in one sentence:** every one of America's 1.7 million nonprofits
gets the digital infrastructure to receive support — a page, honest context,
a verified way to give and volunteer — regardless of size, budget, or
technical capacity. And every person gets a way to give that is as easy as
it is sincere.

---

## The problem we exist to solve

Giving is harder than it should be, and hardest exactly where it matters most.

A donor who wants to support local work faces a maze: most small nonprofits
have no discoverable website, no donation page, no way to be found beyond
word of mouth. The infrastructure of generosity — discovery, trust, the
actual giving path — exists only for the largest organizations that can
afford to build it. The result is that attention and money pool around big
names while sincere community work stays invisible.

Meanwhile, the platforms that do exist mostly position themselves as
*watchdogs*: rate, grade, warn. That posture helps donors avoid bad actors
but quietly punishes small organizations for being small — thin filings and
modest websites read as red flags when they are really just the shape of
community-scale work.

## What we are building instead

**Daanaa is public infrastructure, not a gatekeeper.** Like roads, the value
is that everyone can use them:

1. **Every org gets a page.** All 1.7M active 501(c)(3)s are in the
   directory from public IRS data — nobody applies, nobody pays, nobody is
   left out for being too small to notice.

2. **Every page works toward a working "give" path.** Our discovery
   pipeline finds each org's website, donation page, and volunteer page,
   verifies them, and labels honestly what AI found versus what the org has
   confirmed. The hand-off is always to the org's own channel — money never
   touches us (STEWARDSHIP P8).

3. **Context, not verdicts.** Financial signals are peer-grouped so likes
   compare with likes, and phrased as invitations ("needs support") rather
   than judgments. A donor gets honest context in seconds; an org never gets
   publicly graded (P3, P4, P5).

4. **Private by default.** Giving is between the donor and the org. No
   tracking, no social pressure, no leaderboards; the Giving Wallet lives on
   the donor's device (P2).

5. **Orgs can claim and complete their page, free.** The claim flow turns
   the directory from a mirror of public data into living infrastructure the
   nonprofit itself maintains — missions, programs, volunteer events.

## How "make giving easy" decomposes

| Friction today | Infrastructure answer | Where it lives |
|---|---|---|
| "I can't find local orgs" | Full directory, search, proximity, cause tags, hidden gems | FTS + embeddings + weekly rotation |
| "Is this org real?" | IRS registration surfaced as a defensible fact on every page | Registered US Nonprofit badge, revocation sync |
| "Where do I actually give?" | Discovered + verified donation links; EIN fallback always present | Discovery daemon + Give-by-EIN |
| "Is my gift needed?" | Peer financial context, reserves as invitation | v5 health signals |
| "I want to give time, not money" | Volunteer link discovery + org-listed events | Volunteer rails |
| "I don't want to be tracked" | Device-first wallet, no accounts required, Plausible-only analytics | Privacy invariants |

## The operating model that makes it durable

- **Public data first, AI second, humans accountable.** Deterministic scoring
  from IRS data; local AI (our own hardware) for enrichment; every AI output
  labeled and reviewable; humans own the outcomes (P10).
- **Zero-marginal-cost infrastructure.** Local inference, static precompute,
  a $6 droplet at the edge. The cost of serving org #1,700,000 is the same
  as org #1 — which is what lets "everyone gets a page" stay true.
- **Governance as code.** Stewardship principles are enforced by pre-commit
  gates, privacy invariants, a decision workflow with 12-hour board
  simulations, and a public corrections path on every page (P6, P9, P11).
- **Independence forever.** No paid placement, no partner influence on
  visibility, never the merchant of record (P1, P7, P8).

## What success looks like

Not our traffic — **their capacity.** Success is a small food pantry whose
donation link works and gets used; a donor who found them in under a minute;
a volunteer who showed up because the page existed. We measure ourselves by
doors opened: orgs with working give-paths, donors who completed a hand-off,
organizations that claimed their infrastructure.

*Give with heart. We build the roads.*
