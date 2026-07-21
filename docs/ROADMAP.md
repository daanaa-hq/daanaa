# Daanaa Platform Roadmap — the seven stages

**Established:** 2026-07-21 (founder-defined arc; structure by AI engineering agent)
**Mission anchor:** Make giving easy.
**Spine + moat:** The Impact Wallet runs through every stage — each stage deposits into it
or draws from it. It is not just the connective architecture (spine); it is the **moat**
(founder, 2026-07-21): a private, accumulating ledger of a person's giving + time + intent,
plus the two-sided anonymized signal loop, compounds per user and per org and cannot be
copied by a competitor who lacks that history. The wallet is the source of all activities
and the defensible core. See
`.gstack designs/org-detail-revamp-20260721/impact-wallet-architecture.md`.

The stages are a **sequence of capability**, not walls. Each builds on the last, and the
wallet is the thread that carries a user (and a nonprofit) from one to the next. Earlier
stages keep improving as later ones land.

---

## The arc at a glance

```
  1 VISIBILITY ─▶ 2 FINDING ─▶ 3 TIME ─▶ 4 COMMUNITY ─▶ 5 PRODUCTIVITY ─▶ 6 COST ─▶ 7 GROWTH
     make legible   navigate    give time   interconnect    build tools      reduce    nonprofits
     + trustworthy  to the      + log it,   volunteers,     via EcoMargins,   cost via  thrive &
     + logged       right one   verifiably  boards, orgs    help create orgs  buying    scale
        │              │            │            │               │              │           │
        └──────────────┴────────────┴────────────┴───────────────┴──────────────┴───────────┘
                          ALL DEPOSIT INTO / DRAW FROM THE IMPACT WALLET
```

---

## Stage 1 — Visibility
**Goal:** Every nonprofit is legible, trustworthy, and actionable. A donor can make a
good decision with real information and real links, and log it for repeatability.

**Delivers:**
- Searchable directory + org detail pages (giving-first redesign, in progress)
- Evidence-based financial context (v5 scoring, peer benchmarks)
- Verified donate links + website discovery (donation pipeline, Charity Navigator scraper)
- Wallet log-keeping (bookmarks / intent today)

**Wallet connection:** the deposit habit starts here — save an org, mark giving/volunteer intent.

**Status:** ACTIVE. Org detail redesign (giving-first, interest-only) is the current work.
Volunteer = interest signal only in this stage; hour logging lands in Stage 3.

---

## Stage 2 — Finding
**Goal:** Help each person navigate to the *right* org or opportunity, not just browse.
Visibility makes orgs legible; Finding makes them navigable.

**Delivers:**
- High-quality search (exact-name pin, semantic + FTS — search-quality work ongoing)
- "Near me" / location discovery
- Wallet-driven suggestions (the loop's "suggest" step — reads your history on-device)
- Cause/peer-based recommendations

**Wallet connection:** the wallet's aggregate history powers discovery. Discovery becomes
a *withdrawal* from the wallet, closing the loop back to the top.

**Status:** Partially live (search overhaul 2026-07-18). Wallet-driven suggestion loop is future.

---

## Stage 3 — Time
**Goal:** Turn giving from money-only into money + time. Volunteering that is logged,
verifiable, and portable.

**Delivers:**
- Volunteer events (org-posted, geolocated — Meetup-like, free)
- Hour logging → the wallet's `time` contribution entries
- Org-attested, exportable hour credentials (college apps, employer VTO/match, board
  packets, federal service awards) — Daanaa relays the org's attestation, never certifies
- Two-tier wallet: private default, opt-in identified layer for exports

**Wallet connection:** THIS is where the wallet becomes a true impact ledger (funds + time).
The `ContributionEntry` model reserved in Stage 1 pays off here.

**Blocking before build:** legal (hour-verification liability, minor/COPPA consent), and the
board decision on wallet-as-ledger vs wallet-as-intent (P2). See stakeholder-simulation.md.

**Status:** DEFERRED. Interest signal seeded in Stage 1; verification is Stage 3.

---

## Stage 4 — Community
**Goal:** Interconnect the people and orgs — volunteers, board members, businesses, and
nonprofits supporting each other.

**Delivers:**
- Volunteer directory at scale (find opportunities near you)
- Board-member matching (a deeper flow than event RSVP — fiduciary, months-long, two-way vetting)
- Nonprofit-to-nonprofit interconnection (peer learning, shared resources)
- Business ↔ nonprofit connection

**Wallet connection:** the civic engagement ladder — a donor becomes a volunteer becomes a
board member, tracked continuously in the wallet.

**Status:** DEFERRED. Board matching explicitly separated from Stage 3 event RSVP.

---

## Stage 5 — Productivity
**Goal:** Boost nonprofit productivity with custom tools; help people start nonprofits.

**Delivers:**
- EcoMargins custom tools (capacity, finance, governance)
- Nonprofit creation support (incubator / startup path)
- Top rung of the engagement ladder for the most engaged users

**Wallet connection:** Part 3 is the top of the ladder, reached via the wallet's history —
not a bolted-on B2B side business. Employer-match exports (Stage 3) are the B2B wedge in.

**Status:** FUTURE.

---

## Stage 6 — Cost reduction
**Goal:** Lower nonprofits' operating cost so more of every dollar reaches the mission.

**Delivers:**
- Group purchasing (aggregate buyer power for small orgs)
- Shared services / vendor pooling

**Wallet connection:** cost saved is impact multiplied — surfaces in org financial context
(Stage 1) as improved efficiency.

**Status:** FUTURE.

---

## Stage 7 — Growth of nonprofits
**Goal:** The outcome the whole platform exists for — nonprofits thrive, scale, and sustain.

**Delivers:**
- Everything compounds: visible + findable + funded + staffed + governed + efficient orgs grow
- Growth signals feed back into Stage 1 visibility (a virtuous loop)

**Wallet connection:** the two-sided loop closes — healthier nonprofits attract more donors
and volunteers, whose wallets drive more discovery.

**Status:** NORTH STAR.

---

## Cross-stage invariants (true at every stage)

1. **Privacy spine (P2):** the wallet is device-first, private by default. The platform sees
   only anonymized aggregates. This is what lets us interconnect everything without becoming
   surveillance. Structural, not conventional (PRIVACY-INVARIANTS.md bar).
2. **Never handle funds / never certify (P8):** Daanaa is a hand-off + relay layer. It routes
   donations to the org's processor and relays the org's hour attestation — never the merchant
   of record, never the certifier of record.
3. **Evidence-based (P3):** every signal, score, and credential traces to real, reviewable data.
4. **No silent principle drift (P11):** material changes (e.g. wallet intent → ledger) require
   explicit board sign-off + a STEWARDSHIP.md revision-log entry.

---

## How the current work maps

| Work item | Stage |
|---|---|
| Org detail page redesign (giving-first, interest-only) | 1 Visibility |
| Charity Navigator website scraper | 1 Visibility |
| Donation link pipeline | 1 Visibility |
| Search quality overhaul | 2 Finding |
| Wallet-driven suggestion loop | 2 Finding |
| Volunteer hour verification + exportable credential | 3 Time |
| Wallet-as-ledger (ContributionEntry, two-tier visibility) | 3 Time (modeled in 1) |
| Board matching | 4 Community |
| EcoMargins tools, nonprofit creation | 5 Productivity |
| Group purchasing | 6 Cost reduction |
