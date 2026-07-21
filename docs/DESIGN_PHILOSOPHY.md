# Daanaa Design Philosophy — how we build and shape the experience

**Established:** 2026-07-21 (founder-defined). A guardrail for every product, code, and
copy decision. Sits under `STEWARDSHIP.md` and the Charter (those govern *what we must
never do*); this governs *how we build and how the experience should feel*.

**The one sentence:** We mold a mindset where giving is easy — in all its forms — by
removing everything that is not that.

Four traditions, held together:

---

## 1. Toyota — lean, kaizen, eliminate waste (muda)

- **Muda is the enemy.** Duplicate code, duplicate scripts, redundant UI, repeated work,
  dead files — all waste. Remove it on sight (boy-scout rule). Example: ~13 overlapping
  website-discovery scripts is muda; the target is one canonical path.
- **One canonical path per job.** Standardize. If two things do the same job, merge to one
  and delete the other. A new need becomes a *source/module* inside the canonical path, not
  a new parallel script.
- **Kaizen — continuous small improvement.** Ship small, reviewable increments, each
  verified. Not big-bang rewrites of live surfaces.
- **Just-in-time — build only what is needed now (YAGNI).** No Stage 3 code in Stage 1. No
  abstraction until two callers. Reserve seams (cheap) instead of building ahead (waste).
- **Poka-yoke — error-proof structurally.** Guardrails are code, not convention
  (privacy_check.sh, PRIVACY-INVARIANTS.md, failing-first tests on money/privacy/scoring).
- **Jidoka — stop the line on a defect.** A failed smoke test auto-rolls-back. A broken
  test is not "done." Surface problems, never hide them.

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
