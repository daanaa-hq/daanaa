# Daanaa — Master Build Plan & Execution Spec

**For:** Claude Code (senior engineer, Opus-class reasoning), operating under the Daanaa Founding Stewardship Commitment.
**Date:** 2026-05-28
**Status:** Canonical. Supersedes and absorbs `DAANAA-REMEDIATION-AND-GOVERNANCE-SPEC.md` — work from this file only.
**Source inputs:** External review, strategy synthesis, advisory-board simulation, stewardship-alignment review, and the solo/budget + phased-roadmap decisions.

---

## North Star (so we never lose track)

Daanaa helps people act on their values — **giving money now, giving time later** — without Daanaa ever judging a nonprofit or touching a dollar. The product is one principled, installable experience across **web + iPhone + Android** for **search + a private wallet**, with **volunteering** added deliberately later. It must be **runnable by one human, self-funded**, and stay aligned with all 11 Stewardship principles as it grows.

**The hard constraints that shape every decision:**
- One operator. No team. Self-funded. → Favor low-maintenance, low-cost, low-liability choices.
- Daanaa never touches money (P8) and never judges orgs (mission/P4/P5).
- Do it right the *first* time *and every* time → ship a small correct core, design the seams so later phases slot in without rework, and let the governance loop enforce correctness as we grow.

---

## How to use this document

Work phase by phase. **Do not start a phase until the prior phase's Milestone Gate is met.** Each task cites the **principle (P#)** it serves and a severity. Never auto-merge to `main` — Principle 10 requires a human accountable for every change, so all work lands on a branch for Akbar's review, in the PR plan at the end.

---

## DECISIONS RESERVED FOR THE HUMAN (surface, never assume)

1. **Entity / revenue model (P7).** Daanaa is a for-profit LLC DBA. A model that charges rated orgs collides with independence. **Default: build nothing that charges rated orgs or touches the giving flow.** Flag for decision.
2. **Volunteering data source + license (Phase 3).** Requires a sourcing/licensing call and likely a counsel question. **Default: do not build until decided.**
3. **ProPublica CC BY-NC-ND.** Scores are derivative works; the *no-derivatives* clause is a launch question for Phase 2, not just monetization. **Default: log for counsel, do not resolve.**

---

## Roadmap & Milestone Gates (the tracking spine)

| Phase | Goal | Milestone Gate (definition of done) |
|------|------|--------------------------------------|
| **0 — Foundation & Safety** | Make the existing code safe, honest, and reconstructable; stand up the principle guardrails. | All P0 security/integrity fixes merged; DB fully reconstructable from code; principle-test suite green; rebrand complete. |
| **1 — Solo Launch (PWA)** | Directory + search + private wallet, installable on web/iOS/Android from one codebase. Scores OFF. | Search works; verified donate links work; wallet works offline as an installable PWA on iOS + Android; no money flow; principle tests green; seams designed for Phases 3–4; ready for human review. |
| **2 — Scores On** | Honest, fair, peer-bounded *financial-profile* score with a public methodology, corrections path, and the data-learning governance loop. | Methodology page live; every score carries as-of date + version; **bias audit (P4) passes**; appeal/opt-out functional; stewardship doc honest + re-signed. Scores publish only after all of these. |
| **3 — Volunteering** | Add volunteer events as a deliberate civic-action vertical, designed against the same principles. | Source/license decided; events vetted for trust-safety; slots into the Phase-1 civic-action model with no rework; same no-judging principles applied. |
| **4 — App-Store Presence** | Native presence *only if* PWA limits actually bite. | Demand-driven, not scheduled. Capacitor-wrap the same PWA codebase to both stores. |

Track progress by checking off each gate. A phase is not "started" until the prior gate is green.

---

## SECTION 0 — Operating rules (token + hardware discipline)

- **Branch first:** `git checkout -b build/2026-05-28`. Small, reviewable commits (PR plan at end). Never touch `main`.
- **Mechanical work → deterministic tools, zero model tokens:** `ripgrep`, `gitleaks`/`trufflehog`, `pip-audit`, `npm audit`, `pandas`.
- **Bulk/fuzzy + recurring heavy jobs → local inference** on `localhost:11434` (llama.cpp/Vulkan on the R9700, Ollama fallback): per-file summaries for files >200 lines before reasoning; embeddings; cause-tag extraction; name normalization; and all Phase-2 re-scoring/drift/bias jobs.
- **Reserve Claude tokens for judgment:** invariant proofs, scoring framing, methodology copy, security severity, governance design.
- **Evidence trail:** tool outputs → `docs/reviews/raw/`. Never re-read a file already summarized.
- **Change log:** every change appends `{file, what, principle(s), severity}` to `docs/CHANGELOG-2026-05-28.md`.
- **Design the seams (do-it-right rule):** before writing Phase-1 code, read the "Seam Design" requirements in Phase 1 so nothing built now must be torn up in Phase 3/4.

---

# PHASE 0 — Foundation & Safety

## 0.1 Pre-flight verification
- **DB reconstructability (P9):** `sqlite3 data/merit_registry.db .schema > docs/reviews/raw/live_schema.sql`; diff against every `CREATE TABLE` in code; write `docs/reviews/raw/schema_drift.md` listing every table/column not created by code. The hand-made `org_claims` table is one instance — find them all.
- **Rebrand scan:** `rg -i 'merit|meritgiving' --hidden -g '!.git'` → `docs/reviews/raw/rebrand.txt` (include file/dir names, `MERIT_ADMIN_KEY`, DB filenames, CORS allowlist, OG tags, `package.json` name).
- **Mistake Registry reality check (P6):** is the org-page component functional or a stub? Record it. If stub, it becomes a Phase-2 build task and the stewardship doc's claim is corrected now.

## 0.2 P0 backend fixes
| # | Task | P# | File |
|---|------|----|----|
| 0.2a | Hash claim PINs before logging; opaque HMAC token in verify URL (not raw PIN); `chmod 600 logs/`; regression test. | P2 | `scripts/send_claim_letter.py:138-148` |
| 0.2b | Add `_init_org_claims_table()` at module load matching live schema; fresh clone must come up clean. | P9 | `merit_api.py` |
| 0.2c | Replace `provided != _ADMIN_KEY` with `hmac.compare_digest`. | P7 | `merit_api.py:220` |
| 0.2d | Fix overnight pipeline DB target to `merit_registry.db`; grep all scripts for legacy `meritgiving.db`, migrate/delete. | P9 | `scripts/overnight_pipeline.py:9` |
| 0.2e | Lob fallback returns `status=log_only`, never `letter_sent`, when no key set. | P3 | claim/letter path |
| 0.2f | Strip `-999` sentinels from `/api/stats` reserve buckets. | P3 | `/api/stats` |
| 0.2g | Wire strict CSP + (prod) HSTS. **CSP is load-bearing for P2** — donor data is client-side, so without it an XSS exfiltrates the wallet. Treat as P0. | P2 | `set_security_headers` |
| 0.2h | `pip-audit`; resolve HIGH/CRITICAL → `docs/reviews/raw/pip_audit.txt`. | P9 | — |

## 0.3 P0 frontend fixes
| # | Task | P# | File |
|---|------|----|----|
| 0.3a | Remove the acknowledgment-letter promise (no backend; creates IRS-substantiation confusion). Replace with "request a receipt from the organization." | P3,P8 | `Wallet.tsx`, `GivingConfirmation.tsx` |
| 0.3b | Route "Complete your gift" to verified `apiOrg.donate_url`, not a Google search (routes trusting donors into sponsored scams). **P0.** | P1 | `GivingConfirmation.tsx:131` |
| 0.3c | Confirm wallet is localStorage-only and CSP-compatible (no inline/eval). | P2 | wallet context |
| 0.3d | `npm audit`; resolve HIGH/CRITICAL → `docs/reviews/raw/npm_audit.txt`. | P9 | — |
| 0.3e | If/when Sentry is wired: `beforeSend` scrubber strips URLs, localStorage, breadcrumbs. | P2 | analytics |

## 0.4 Principle-test harness (the "do it right every time" guardrail — stand it up now)
Create `governance/PRINCIPLE_TESTS.md` (principle → invariant → test) and `tests/test_principles.py`, run in CI and pre-deploy. **A failing principle test blocks deploy.**
- **P8:** no route accepts currency/amount/processor token; no payment SDK; no webhook.
- **P2:** wallet writes never hit the server; security headers include CSP.
- **P1/P7:** no `paid_placement`/`sponsored`/`featured` field affects ordering or score; admin compare is constant-time.
- **P3:** (active once scores ship) every served score carries `as_of` + `methodology_version`.
- **P9/P10:** scoring deterministic (same input + weights → same score); DB schema fully reconstructable from code (0.1 diff is empty).
- **P6:** corrections endpoint exists and persists.

## 0.5 Cleanup & rebrand finish
- Delete confirmed-dead files only after 0.1 confirms none hold a sole copy of a hand-applied change: `app.py*`, `*.backup.*`, `*.broken.*`, `fix_*.py`, `vite.config.ts.bak`, `entities.json`, `0]`, `cloudflared.deb`, stray DBs, and abandoned dirs (`merit-platform/`, `nonprofit-explorer/`, `static_web/`, `ui_backups/`). Restore/delete corrupt `scripts/clean_names.py`.
- Rename: `merit_api.py`→ proper module, `MERIT_ADMIN_KEY`→`DAANAA_ADMIN_KEY` (+`.env`), `package.json` name `my-app`→`daanaa-web`, fix `tests/merit.spec.js` (old port 8081 + "MeritGiving").

**▶ Milestone Gate 0:** all P0 fixes merged; `schema_drift.md` empty; principle tests green; rebrand complete.

---

# PHASE 1 — Solo Launch (PWA): search + wallet, scores OFF

## 1.1 PWA conversion (one codebase → web + iOS + Android)
- Add a web app manifest (name, icons, theme, `display: standalone`) and a service worker (offline app shell + cache strategy for static assets and the search UI).
- Verify **installability** and home-screen launch on iOS Safari and Android Chrome; verify the **wallet works offline** (localStorage persists; app shell loads with no network).
- Note in `docs/PWA_NOTES.md`: iOS push-notification support is historically limited for PWAs — verify current capability before relying on notifications; not a launch blocker.

## 1.2 Seam design (so Phases 3–4 need no rework — the do-it-right payoff)
- **Generalize the data model to "civic actions."** An org has one or more ways to act: `give_money` (donate_url) now; `give_time` (volunteer_event) later. Do not hardcode "donation" through the codebase — use an action-type abstraction so volunteering slots in without schema churn.
- **Generalize the wallet** from "saved donations" to "saved civic actions," so future volunteer commitments live in the same localStorage wallet with no migration of users' local data.
- **Version and structure the API** (`/api/v1/…`) with extensible response shapes; keep the **search service reusable** so volunteering search reuses the same infra.
- **Isolate platform/native concerns** behind a thin layer so a future Capacitor wrap is clean and all logic stays in the shared React app.

## 1.3 Scores OFF
- Feature flag `ENABLE_SCORES=false`. The directory, search, verified donate links, and wallet ship; scores stay dark until Phase 2's gate.

**▶ Milestone Gate 1:** search works; verified donate links work; wallet installable + offline on iOS & Android; principle tests green; no money flow; seams designed per 1.2; branch ready for human review (not merged).

---

# PHASE 2 — Scores On (only when ready for the dispute load)

## 2.1 Scoring honesty & fairness
- **Consolidate to one canonical, versioned scorer (P9).** Archive the non-canonical one. **Recommended default (flag for Akbar):** adopt the multi-factor v3.3-style logic (program / sustainability / reserves / leverage — closer to mission than raw-revenue weighting); expose weights in `scoring/weights.v2.yaml` with a one-line rationale each; bump to `v2`.
- The live 65/35 revenue-weighted formula **violates P4** (rewards bigger/richer within band) — do not ship it.
- **As-of date on every score (P3).** **Flag reserve estimate** (`assets/revenue×12`) as an estimate (P3).
- **Neutralize tier-as-verdict vocabulary (P5):** one vocabulary, reframed as a neutral **"financial profile,"** with a plain-language meaning beside each label.

## 2.2 Methodology page (a P3 compliance deliverable) — `/methodology`
States: data sources + as-of dates; what the score **is** (peer-bounded financial-profile signal); what it is **not** (not impact/effectiveness/worthiness — say so prominently); peer-group construction; weights + rationale; limitations; corrections/appeal + opt-out.

## 2.3 Trust, consent & corrections (P3/P6/P7)
- Make the Mistake Registry **functional** (corrections reach a human-reviewed queue with visible status).
- Org **correction + appeal** endpoint and **opt-out** path (also the legal defensibility shield).
- **Independence guard (P7):** test asserting no code path alters an individual org's score outside published methodology.

## 2.4 Living-governance data loop (run on the R9700, not the API)
- **Quarterly re-score** on refreshed IRS/990 data; re-embedding + re-scoring all ~546K orgs run **locally**.
- **Drift detection:** diff new `score_snapshots` vs prior version; route sharp tier swings to human review → `governance/drift/{date}.md`.
- **Bias audit (P4) — the Phase-2 gate:** per peer band, test whether smaller orgs systematically score lower within band; if so, the model violates P4 and must be revised before scores publish.
- **Mistake → validation-rule loop (P6):** recurring correction types become new ingest validation rules.
- **ADRs (P9/P11):** scoring/methodology/principle changes get a decision record; principle-touching ones trigger re-sign.

## 2.5 Stewardship doc remediation (governance failing its own rules)
- Rewrite aspirational "How implemented" blocks to honest present state (P3).
- Remove the AI from the **Signatories** table → "Operated under these principles" line (P10).
- Re-collect the human signature after the 12→11 change; add rule: AI-proposed principle edits need human approval **before** they land (P11).

**▶ Milestone Gate 2:** methodology live; every score carries as-of + version; **bias audit passes**; appeal/opt-out functional; stewardship doc honest + re-signed. Only then flip `ENABLE_SCORES=true`.

---

# PHASE 3 — Volunteering events (deliberate vertical)

- **Source/license decision (reserved for human + counsel):** VolunteerMatch / Idealist / JustServe / org-submitted — each with its own ToS/licensing surface (same shape as the ProPublica question).
- **Trust-safety vetting:** in-person events carry more real-world risk than a donate link; define a vetting/verification standard before listing. No judging of organizations (mission/P4/P5) carries over.
- **Reuse the Phase-1 seams:** events are a `give_time` civic-action type; volunteering search reuses the search service; commitments live in the existing wallet. No rework if 1.2 was done right.

**▶ Milestone Gate 3:** source/license decided; vetting standard live; events integrated via the civic-action model with no schema churn.

---

# PHASE 4 — App-store presence (only if PWA limits bite)

- Demand-driven, not scheduled. If real users need native push/discovery, **Capacitor-wrap the same PWA codebase** to both stores — no second codebase. Budget the store accounts only at this point.

---

## PR plan (reviewable units for human accountability, P10)

1. **PR-0a Safety:** 0.2 + 0.3.
2. **PR-0b Guardrails + cleanup:** 0.4 + 0.5.
3. **PR-1 PWA launch:** 1.1 + 1.2 + 1.3.
4. **PR-2 Scores + methodology + trust:** 2.1–2.3.
5. **PR-3 Governance loop + stewardship:** 2.4 + 2.5.
6. **PR-4 / PR-5:** Phases 3 / 4 when reached.

Each PR description lists tasks, principles served, and gate criteria met. Append all to `docs/CHANGELOG-2026-05-28.md`.

---

*Operate under the Stewardship Commitment. When in doubt, prefer honesty about a gap over a confident claim that hides it (Principle 3). Ship small, ship correct, design the seams, let the guardrails hold the line.*
