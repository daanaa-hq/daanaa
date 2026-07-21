# Daanaa Design Philosophy — how we build and shape the experience

**Established:** 2026-07-21 (founder-defined). A guardrail for every product, code, and
copy decision. Sits under `STEWARDSHIP.md` and the Charter (those govern *what we must
never do*); this governs *how we build and how the experience should feel*.

**The one sentence:** We mold a mindset where giving is easy — in all its forms — by
removing everything that is not that.

Four traditions, held together:

---

## 1. The Toyota Way — how a company compounds for decades

Toyota's durability comes from two pillars — **continuous improvement** and **respect for
people** — held over a very long horizon. We adopt the whole system, not just "lean," because
we are building a 100-year public trust, not a quarter's feature set. The manufacturing
concepts translate directly to platform + product development.

**Observe reality before deciding (the core):**
- **Genchi genbutsu (go and see).** Decide from real observation at the source, never from
  assumption or opinion. In product terms: *watch what users actually do.* Our self-hosted
  analytics (`stats.daanaa.org`, privacy-safe) and the wallet's private intent signals are our
  "go and see" instrument. Before we claim a redesign works, we observe the behavior change
  (do donate clicks rise?). The CN scraper we deleted is the anti-pattern — built on an
  assumed need, not an observed one.
- **PDCA (Plan-Do-Check-Act).** Every meaningful change is an experiment, not a verdict. Ship
  the smallest version (Do), *observe* real behavior (Check), then adjust (Act). "Verified on
  prod" means it renders; "validated" means the observed behavior improved. Keep the two
  honest and separate.
- **Ask "why" five times.** Fix root causes, not symptoms. (The 27s local API → stuck query →
  a diagnostic that never had a canonical home.)

**Eliminate waste, unevenness, and overburden (muda, mura, muri):**
- **Muda (waste) is the enemy.** Duplicate code/scripts, redundant UI, repeated work, dead
  files. Remove on sight. One canonical path per job — a new need becomes a *source/module*
  inside it, never a 14th parallel script.
- **Mura (unevenness).** Smooth the flow — steady small increments over lurching big-bangs;
  consistent patterns over one-off special cases.
- **Muri (overburden).** Don't overload a live surface (or the team, or the box) with a risky
  all-at-once change. Right-size every increment.

**Build to real demand, improve forever, protect quality:**
- **Pull, not push (just-in-time / YAGNI).** Build what observed demand calls for, when it
  calls for it. No Stage 3 code in Stage 1. No abstraction until two callers. Reserve cheap
  seams instead of building ahead.
- **Kaizen (continuous improvement).** Many small, reviewable, verified improvements compound
  into long-term success. This is how decades are won — not heroic rewrites.
- **Jidoka (automation with a human touch) + andon (stop the line).** Error-proof structurally
  (poka-yoke: privacy_check.sh, PRIVACY-INVARIANTS.md, failing-first tests). When a defect
  shows, stop and fix it — a failed smoke test auto-rolls-back; a broken test is not "done."
- **Nemawashi (decide by consensus, then act).** Surface a change, get sign-off, then move
  decisively — matches "human in command" and the board-sim habit.

**Respect for people (the other pillar):**
- The user's time and dignity are the point — especially the smallest org and the newest
  donor. Observe them, don't manipulate them. The mission/charter guardrails (section 4) are
  how respect-for-people stays structural, not sentimental.

**Long-term over short-term:** every decision is explainable years later (P9) and serves the
100-year horizon over this week's convenience (P11). Toyota's compounding came from refusing
to trade the long game for a short one — so do we.

## 2. Marie Kondo — keep only what serves; everything has a home

- **Does it serve the giving decision?** Every element on a page must earn its place against
  the mission. If it doesn't help someone give (or volunteer, or trust), it goes — or it is
  tucked behind an expandable. Two controls doing the same job is clutter: keep one.
- **Discard with gratitude.** Archive dead scripts and retired features cleanly (don't leave
  debris). Note what was removed and why (DECISIONS/LESSONS), then let it go.
- **Everything has one home.** The Impact Wallet is the home for a user's contributions
  (funds + time). One data primitive, one ledger — not scattered concepts. See
  `impact-wallet-architecture.md`.
- **Calm over dense.** Skimmable, quiet, ordered. The casual visitor is never overwhelmed;
  the interested one can open more.

## 3. American openness — transparent, accessible, welcoming

- **Transparent.** Evidence-based signals, visible corrections (Mistake Registry), open
  data, explainable decisions. Say what we know, believe, and haven't resolved.
- **Accessible.** Plain language, no jargon, WCAG, mobile-first, works without an account.
- **Welcoming and equal.** The smallest org gets the same dignity as the largest. No shame,
  no gatekeeping, no pressure.

## 4. Mission + Charter as guardrails (language and purpose)

- **Language guardrail:** human-readable, no shame framing, no jargon, no dashes as
  connectors (see copy-voice). Additive, never a verdict.
- **Purpose guardrail:** make giving easier; privacy is structural; never handle funds,
  never certify — only relay and hand off. Independence protected. (STEWARDSHIP P1-P11.)

---

## How to apply it (the working test)

Before adding anything — code, a script, a UI element, a sentence — ask in order:

1. **Muda?** Does this already exist? Can I reuse/extend the canonical path instead of
   adding a parallel one? (Toyota)
2. **Serve?** Does this earn its place by making giving easier? If not, cut it or tuck it.
   (Kondo)
3. **Open?** Is it transparent, accessible, plain, and welcoming to the smallest org?
   (American openness)
4. **In bounds?** Does the language and purpose hold to the mission and charter?
   (Guardrails)

If all four pass, build it — small, verified, in its one right home.

5. **Observe (after shipping).** A shipped change is a PDCA experiment, not a verdict. Go and
   see: watch real behavior via `stats.daanaa.org` and wallet intent signals. "Verified" =
   it renders; "validated" = the behavior improved. If it didn't, adjust (Act). Never declare
   a redesign a success on assumption — the user's actual behavior is the source of truth.

---

## Live examples (2026-07-21)

- **Org page giving-first edit:** donate leads (serves the mission); volunteer is
  interest-only (JIT — no Stage 3 hour code yet); maps to existing `addToVolunteering`
  (no muda / no forked model).
- **Frontend dedup:** `getActionRowLinks` computed once not twice; `propublicaOrgUrl`
  helper replaces 3 hand-built URLs (muda removed).
- **Open decision:** two wallet heart-button sets on the org page do the same job (clutter,
  Kondo) — flagged to consolidate to one.
- **Backend:** the CN website scraper should fold into the canonical discovery path as a
  source, not become the 14th standalone script (muda / one-canonical-path).

## Related

- `STEWARDSHIP.md`, `institution/DAANAA-CHARTER.md` — the never-promises (what we must not do)
- `docs/ROADMAP.md` — the 7 stages this philosophy builds
- `impact-wallet-architecture.md` — the one-home principle in architecture form
