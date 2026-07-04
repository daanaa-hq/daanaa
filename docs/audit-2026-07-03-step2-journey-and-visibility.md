# Daanaa Audit — Step 2: Journey & Visibility

**Date:** 2026-07-03 · **Method:** grounded in live prod (curl against daanaa.org) + real code · **Auditor:** Claude (partner review)

Covers **Search Visibility**, **Page Connectivity**, **UX Efficiency**. Pairs with Step 1 (`audit-2026-07-03-step1-trust-and-risk.md`).

---

## ⚠️ CORRECTION (2026-07-03, same day): the headline finding below was a FALSE ALARM

**There is no org-page SEO bug. Org pages are server-rendered correctly.** My original
finding (struck through below) was based on testing a *dashed* EIN (`/org/53-0196605`),
which is a URL format that appears **nowhere** in the product. Verified after the fact:

- Sitemap uses undashed EINs: `https://data.daanaa.org/sitemaps/orgs-0001.xml` → `/org/000019818`
- API returns undashed EINs (`"EIN":"464548728"`); the frontend links with those
- The canonical undashed URL renders correctly on the origin (Cloudflare-bypassed):
  ```
  GET http://127.0.0.1:5000/org/530196605
    <title>AMERICAN NATIONAL RED CROSS — Daanaa</title>
    <link rel="canonical" href="https://daanaa.org/org/530196605" />   ✓ self-referential
  ```
- `_meta_for_path()` in `scripts/droplet_api.py` (lines ~1455-1467) already handles
  `org/<ein>`: per-org title, self-canonical, AND `_org_jsonld()` Organization schema.
  It was there the whole time.

**Root cause of my error:** `load_org_detail()` computes the file-shard prefix as
`ein[:3]`. For `53-0196605` that's `53-` → wrong path → returns None → falls through to
the raw SPA shell (which has the homepage canonical). Real (undashed) EINs shard
correctly. I tested a format nothing uses and reported a 1.7M-page crisis that doesn't
exist. Correcting the record rather than letting it stand.

**Only real residual (LOW):** if any external site ever links a *dashed* EIN, that URL
serves the generic shell + homepage canonical. Cheap optional hardening: strip
non-digits from the EIN at the top of `load_org_detail()` so dashed URLs also resolve.
Not urgent — no canonical URL uses dashes.

---

### ~~🔴 THE ONE THING TO FIX (Step 2)~~ — WITHDRAWN, see correction above

~~**Every one of your 1.7M org pages tells Google it's a duplicate of the homepage.**~~
The machinery (`_inject_meta` + `_meta_for_path`) already covers org pages correctly for
the canonical undashed EIN format. No action needed. The genuine Step-2 items are the
connectivity/UX findings below.

**Deploy-hygiene note:** the root `droplet_api.py` in your local repo does **not** contain `_inject_meta` — only the deployed `/opt/daanaa/droplet_api.py` does. Your local copy is stale relative to prod. Reconcile before the next deploy or you'll ship a regression that removes server-side meta entirely.

---

## Search Visibility — full findings

| Sev | Finding | Evidence | Fix |
|-----|---------|----------|-----|
| **🔴 HIGH** | Org pages: homepage canonical + generic title (above) | live curl on 2 org EINs | Add `/org/<ein>` branch to `_inject_meta` |
| **MEDIUM** | No `Organization` JSON-LD on org pages server-side | `_inject_meta` supports a `jsonld` arg, unused for orgs | Include NonprofitOrganization schema — drives rich results for "[org] nonprofit" queries |
| **LOW** | Homepage meta description is generic/feature-listy | `"1.7M+ U.S. nonprofits, public records, peer context…"` | Rewrite to target "nonprofit directory" / "look up a charity" intent + differentiator (independent, covers all 1.7M not a curated subset) |
| **GOOD** | Static content pages correctly server-rendered | `/methodology`, `/directory` titles + canonicals correct | — credit; the pattern works, just extend it |
| **GOOD** | Both sitemaps live (HTTP 200) | `daanaa.org/sitemap.xml`, `data.daanaa.org/sitemap-index.xml` | Remove the `/stewardship` + `/principles` entries that 301 (wasted crawl) |

**Net:** you did the hard 80% (server-side meta infra + sitemaps). The missing 20% — the org-page branch — is the part that actually captures the traffic. This is the highest-ROI engineering task on the board.

---

## Page Connectivity — findings

**1. MEDIUM — The trust anchor isn't in the nav.**
Top nav is: **Discover** (`/directory`), **Volunteer**, **Claim your page** (`/for-nonprofits`), + wallet icon (`Navigation.tsx:24-26`). A donor looking at an org's peer score and asking "what does this mean / can I trust this?" has **no top-level path to `/methodology`** — the page that exists precisely to answer that. Methodology, Research, and About are all absent from the primary nav. At minimum, surface Methodology (the "not a rating agency" credibility rests on it being reachable).

**2. MEDIUM — `/research` is a dead end.**
`ResearchDashboard.tsx` and the research components contain **zero links to `/directory`**. A user learns "60% of human-services orgs sit in the CAUTION band" and then has nowhere to go — no "see these orgs" path. The insight doesn't convert to discovery. Fix: every research chart segment should link to `/directory?` with the matching filter pre-applied.

**3. GOOD — Causes → directory works.**
`CauseSpotlight.tsx:172` links to `/directory?category={code}`. The cause → filtered-directory path is intact. Credit — this is the pattern `/research` should copy.

**4. LOW — Org detail is long (1,546 lines) but mobile is handled.**
The desktop primary website CTA sits ~40% down the page (`OrganizationDetail.tsx:622`). Mitigated on mobile by a **sticky bottom CTA** with "Visit website" (`:1491-1531`). Desktop could use the same sticky treatment so the act-now action is always in reach without scrolling past financials.

---

## UX Efficiency — findings

**1. MEDIUM — `merit_score DESC` surfaces endowments first once you leave the gems lens.**
(Refined 2026-07-03 after checking real behavior — my first draft overstated this.)
The `/directory` **landing defaults to hidden gems** (small orgs, `Directory.tsx:168`),
so the landing page is mission-aligned — it does NOT bury small orgs. The real issue is
narrower but genuine: the sort is `merit_score DESC`, and the gems lens is **dropped on
search** (`:222`) and on **"See all"** (`:377`). Verified on prod: browsing all orgs by
the default sort returns a wall of score-100 **endowment funds / foundations / investment
corporations** (the highest-reserve, least need-based orgs) first — the opposite of "see
the overlooked." Two things worth deciding:
- **The "we don't rank" tension:** any score-ordered default is in friction with the
  stated no-ranking posture, on search + browse-all specifically.
- **Endowment-first browse-all** reads as off-mission. A relevance-first (on search) or
  within-band-shuffled (on browse-all) order would fit better; keep merit_score opt-in.

**2. MEDIUM — Two parallel trust systems on one page.**
Org pages show both the **Lamp Tier** (visibility/data-completeness) and **Peer Financial Context** (reserve percentile). These measure different things, but a casual donor won't distinguish them — two badges, two color systems, one confused reader. Consider visually subordinating one (tier as a small data-completeness chip, financial context as the headline) so there's a single primary signal.

**3. MEDIUM — Wallet has no close-the-loop.**
The wallet stores intent, but after a user clicks out to an org's site to give, there's no "did you give?" return moment. Without handling funds, a simple post-return "Mark as given / add a note" prompt closes the loop and makes the wallet a giving journal rather than a bookmark list that goes stale. (Architectural — from the design; worth a lightweight prototype.)

**4. LOW — Device-switch wallet loss isn't surfaced.**
localStorage-only wallet silently vanishes on a new device. That's the correct privacy default, but a one-line "saved on this device — sign in to sync" note prevents a confused "where did my list go" moment.

---

## Step 2 priorities (in order)

1. **Wire `/org/<ein>` into `_inject_meta`** in `droplet_api.py` — per-org title, description, **self-canonical**, Organization JSON-LD. Reconcile the stale local copy first. This is the single highest-ROI change across both audit steps.
2. **Fix the directory default sort** — one product decision that resolves both the UX burial and the Step 1 stewardship contradiction.
3. **Link `/research` into filtered `/directory`** — turn insight into discovery.
4. **Add Methodology (and Research) to the top nav** — make the trust anchor reachable at the moment of doubt.
5. Extend the mobile sticky CTA to desktop; add wallet close-the-loop + device-sync hint.

---
*Grounded in live prod behavior as of 2026-07-03. The org-canonical finding is verifiable right now: `curl -s https://daanaa.org/org/53-0196605 | grep canonical`.*
