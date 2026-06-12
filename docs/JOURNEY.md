# The Daanaa Journey

> **AI-generated · beta.** This history is compiled and maintained by Daanaa's AI
> engineering agent (Claude) from evidence, and reviewed by the founder. Accountability
> remains human (Stewardship principle 10). The public milestones page generated from
> this file carries the same label — we hold our own content to the provenance standard
> we hold everyone else's.

A running, evidence-anchored record of milestones as Daanaa grows. Maintained as a
historian's log: dates are taken from git history, the Stewardship revision log, and
the data itself — not from memory. This document is the source of truth for a future
public "Our Journey" / milestones page, and the spine of the eventual AI-impact case
(see `IMPACT.md` when it exists).

How to use: append a dated entry when a real milestone lands. Keep it honest — note
when something is potential vs realized. No inflation (Stewardship principle 3).

---

## 2026-05 — Genesis & foundation

**2026-05-16 — Build begins (as "MERIT").**
First commit: the platform baseline. Within the first day: the scoring-credibility
rework (a real financial score, framed as a visibility *journey*, never a verdict),
org pages, SEO, the lamp brand mark, and AI semantic search wired into the directory.

**2026-05-16 to 05-17 — The scoring methodology takes shape.**
Reserve-ratio composite → peer-distribution model (revenue *and* reserves ranked within
a peer group) → regional peer groups (US Census regions, minimum group size 30, national
fallback). The `score_snapshots` table is added so every score change is longitudinal and
auditable. The public `/methodology` page ships. This is the methodology still live today:
0.65 revenue + 0.35 reserve, within NTEE-subcategory + band + region.

**2026-05-17 — Data reaches real scale.**
ProPublica ingest brings ~1.78M financial-history rows and ~84% reserve coverage. AI
cause-tag extraction begins (local inference). The platform now describes the sector,
not just lists it.

**2026-05-20 — The Founding Stewardship Commitment is signed.**
Eleven binding principles: mission before growth, privacy as a core principle, evidence-
based trust signals, fairness to small orgs, never weaponizing transparency, never
controlling donor funds. Signed by the founder and the AI engineering agent. This is the
document everything else is held against.

**2026-05-24 — Rebrand: MERIT → Daanaa.**
"Daanaa" means *wise*. The Stewardship doc is consolidated from 12 to 11 principles
(no principle removed) with an "How implemented" section added to each.

---

## 2026-05-28 to 05-31 — Hardening, honesty, and the invisible 97%

**~2026-05-28 — Security + pipeline-quality + frontend-alignment pass.**
Trust-gating tightened (donate links fail closed on unverified status), FTS search
ranking weighted toward org names, security headers and CSP hardened.

**2026-05-29 — Mission quality at scale.**
Haiku rewrites of ~15K low-quality missions (bad phrases, PTA schools, chapter orgs).

**2026-05-30 — "The Invisible 97%" + scoring integrity.**
The light-reveal page ships: drag a lamp to make invisible nonprofits visible, by cause,
with brightness mapped to real coverage. A scoring-integrity bug is found and fixed: the
documented composite was being overwritten weekly by a revenue-only job; the composite is
made canonical and re-scored live (649K orgs). Mission generation switches to a faster,
cooler local 14B model, run on an overnight GPU schedule to manage heat.

**2026-05-31 — Provenance, privacy, and a trust bug caught in the open.**
- AI provenance shipped end to end: missions, donate links, and cause tags all carry a
  "beta" label and flip to org-verified on claim. AI/scraper disclosures added to the
  Legal page and footer.
- Privacy made enforceable: visitor IPs removed from access logs, `PRIVACY-INVARIANTS.md`
  + a `privacy_check.sh` pre-commit gate, and a stewardship-derived governance charter.
- Device-only wallet backup (self-text + passphrase-encrypted export) — no accounts, no
  server-stored giving data.
- A device test caught a real trust bug: the org headline showed a stale score (90) while
  the table below showed the real composite (81). Fixed so every surface agrees.

---

## 2026-06-01 — Infrastructure, operations, and the AI team comes online

**2026-06-01 — The operational layer is built.**
The platform acquires real operational infrastructure for the first time:

- **9 role-addressed email aliases** (`hello@`, `orgs@`, `legal@`, `trust@`, `contact@`,
  `security@`, `privacy@`, `partners@`, `verify@` at daanaa.org) — each with a defined
  department owner, autonomy tier (high/medium/low), and Stewardship-aligned guardrail
  (no AI auto-send on legal, security, privacy, or verification channels).
- **AI email triage agent** (`scripts/email_agent/`) — reads the single receiving inbox,
  classifies by `To:` alias, labels by department, creates Gmail Drafts for reply. No
  auto-send yet; a human reviews every draft. Templates are deterministic (no LLM in the
  loop), available 24/7, and carry an AI-disclosure footer per the Stewardship commitment.
  Daily cron at 7:30am.
- **GitHub org `daanaa-hq`** — the first external code repository. Private. All commits
  pushed. The platform has version control outside the local machine for the first time.
- **Anthropic Startup Program application filed** — seeking API credits to accelerate
  mission generation (currently 61,200 scored orgs still without a mission statement).
- **Site email routing** — claim/verify flows → `orgs@`, legal section → `legal@`/`trust@`/
  `privacy@`/`partners@`, FAQ data-error → `trust@`, footer "Report a data issue" link
  added. The Stewardship correction channel is now a real, routable address.

This milestone marks the shift from a one-person technical build to a functioning
operational entity: a real org identity (daanaa.org email addresses), a real code home
(GitHub), an AI team member for email (the triage agent), and the first formal
relationship with Anthropic as a partner.

---

## AI-impact snapshot (as of 2026-06-01)

What the AI has done, with one founder and local + API compute. Honest framing: this is
*enabling* impact (a discoverable, described, scored profile for orgs that were opaque in
raw filings). *Realized* human impact — real donors giving to orgs they'd never have found
— is measured after launch.

| Metric | Count |
|---|---|
| Nonprofits indexed from raw IRS data | 1,811,930 |
| Given an AI-written plain-language mission (had none on file) | 569,262 |
| Made searchable by cause (AI tags) | 1,811,707 |
| Given a peer-context financial score (~650K full composite) | ~1.8M ranked |
| Small "hidden gem" orgs surfaced | 825 |
| Donate paths discovered + verified (confidence ≥90) | 375 |
| Websites verified live | 114,295 |

Counterfactual: the AI-written missions alone represent roughly **118 person-years** of
analyst work (569K filings × ~25 min each), produced in weeks for a few thousand dollars.

---

**2026-06-01 (evening) — daanaa.org deployed to production.**
DigitalOcean Droplet (NYC2, $8/mo) running gunicorn on port 80. Lean 1.7GB DB (stripped from
19GB full DB — ML tables excluded, web tables preserved). 2GB swap, UFW firewall, fail2ban,
log rotation, auto security updates. Daily rsync cron syncs fresh data from the home Ryzen
pipeline to the cloud server every morning at 7am. Beta banner live. One founder action
remaining: flip Cloudflare A records to Proxied → daanaa.org goes public.

---

_Next milestones to watch: daanaa.org public (Cloudflare proxy flip); first visitor;
first feedback email; Anthropic startup credits approved; first real donor-facilitated
gift to a sub-$100K org; first org self-claim; the native app._

---

## 2026-06-01 (22:40 UTC) — 🚀 daanaa.org is LIVE

The platform went public. After indexing 1.8M nonprofits, generating 569K AI missions,
building the email agent, and deploying to DigitalOcean, daanaa.org served its first
public request over HTTPS. Beta tag live. Search working. The invisible 97% are now
findable by anyone with the link.

One founder. AI agents. Roughly two months from first commit to public civic infrastructure.

The journey from here is realized human impact: the first donor who finds an organization
they'd never have discovered, and gives.

---

## 2026-06-02 — Every scored nonprofit now has a voice

Overnight, on the local 14B GPU model (heat-safe 10pm-6am window), the mission backlog for
scored organizations went from **61,200 to 225**. ~61,000 plain-language missions generated
in one night, bringing the total to **630,237**. The 225 that remain are orgs with too
little usable source data to describe honestly, not a backlog.

What this means: every nonprofit that has enough data to be scored and surfaced now also
has a clear mission a donor can read, where most had nothing before. The "find the invisible
97%" promise is no longer aspirational for the scored set; it is done. Counterfactual: the
missions alone now represent roughly **131 person-years** of analyst work (630K filings x
~25 min each), produced in weeks on a single desktop GPU for the cost of electricity.

Honest framing (Stewardship 3): this is *enabling* impact, a readable, scored, findable
profile for orgs that were opaque in raw IRS filings. *Realized* impact, a donor giving to
one of these because they finally could, is still ahead.

## 2026-06-08 — First auto-detected IRS data delta (the registry now self-updates)

For the first time, the platform **detected new IRS data on its own** and folded it in
safely. The monthly IRS Exempt-Organizations Business Master File refreshed upstream
(Last-Modified 2026-06-08); a check found **26,565 new 501(c)(3) organizations** missing
from the registry — small local nonprofits: volunteer fire-relief associations, food
pantries, PTAs, lake-protection groups. The invisible 97%, newly visible. Registry grew
1,819,272 → **1,845,837**.

We did it the careful way: download → validate in an isolated `VACUUM INTO` **sandbox**
(the live DB never at risk) → confirm 0 malformed records and a sane NTEE/state spread →
apply only the genuinely-new rows. A 218,844-EIN revocation/gap signal was surfaced for
human review, **not** blind-purged.

Hard lesson banked: a bulk write can't out-retry ~13 concurrent pipeline writers fighting
SQLite's single WAL slot (and SIGSTOP deadlocks a writer mid-transaction). The answer is
**stop → apply → restart** — cleanly SIGTERM the batch writers, insert uncontended, relaunch.
Live apply went from 13+ minutes of failures to **6 seconds**.

Institutionalized: a **daily IRS watch now takes priority over all other overnight work**
(cron 21:00, before the GPU window), so new organizations are detected, validated, applied,
and given a mission the same night — automatically, every day.

---

## 2026-06-12 — The day organizations could take the pen

The claim flow went **live on daanaa.org end to end**: a nonprofit leader finds their
page, signs two attestations with their name on them, gets a branded DKIM-authenticated
email, takes our verification call, enters the PIN, and their page opens for editing.
The last mile took detective work — production wasn't serving our fixes because the
droplet, not the home box, serves daanaa.org; the claim API now reaches home through a
**reverse SSH tunnel** the droplet proxies into, so the registry and every secret stay
in the house.

Around the flow, a whole operating company grew in one day: an **admin Claims queue**
with a Today worklist and call checklist, an append-only **org_activity timeline**
behind every event, a **/partners page** and a payment-processor pitch built on the
number nobody else has (only 1,391 of 2,064,613 orgs have a known giving link), the
header cut to two links with **"Claim your page"** front and center, one word — *page* —
made true site-wide, and STEWARDSHIP **P2 revised in the open** (founder-signed) to
allow optional sign-in for wallet sync, bookmarks and intent only.

By night's end the platform watches itself: a **watchdog** probes the full claim path
every five minutes and emails on state change, **nightly backups** capture the
irreplaceable tables, a **morning digest** delivers the day's worklist, and a one-time
**PIN nudge** keeps slow claims alive. The strategy is written down too: the page is
the product, win a neighborhood not the nation, free giving-infrastructure setup as
the claim magnet, and the quiet verified room as the moat. First real claimant: still
ahead — and now everything is ready for them.
