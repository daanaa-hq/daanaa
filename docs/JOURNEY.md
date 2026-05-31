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

## AI-impact snapshot (as of 2026-05-31)

What the AI has done, with one founder and local + API compute. Honest framing: this is
*enabling* impact (a discoverable, described, scored profile for orgs that were opaque in
raw filings). *Realized* human impact — real donors giving to orgs they'd never have found
— is measured after launch.

| Metric | Count |
|---|---|
| Nonprofits indexed from raw IRS data | 1,811,930 |
| Given an AI-written plain-language mission (had none on file) | 324,110 |
| Made searchable by cause (AI tags) | 1,811,707 |
| Given a peer-context financial score (~650K full composite) | ~1.8M ranked |
| Small "hidden gem" orgs surfaced | 825 |
| Donate paths discovered + verified | 544 |

Counterfactual: the AI-written missions alone represent roughly **67 person-years** of
analyst work (324K filings × ~25 min each), produced in weeks for a few thousand dollars.

---

_Next milestones to watch: first real donor-facilitated gift to a sub-$100K org; first
org self-claim; public launch (see `LAUNCH-CHECKLIST.md` gates); the native app._
