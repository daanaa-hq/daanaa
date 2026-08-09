# Codex Review Status — 2026-08-08

**Reviewer:** Codex
**Status:** Active handoff; production actions remain gated
**Last updated:** 2026-08-08

## Purpose

Durable handoff for Claude Code and the founder. This file records what Codex has reviewed, what remains pending, and which actions are authorized.

## Completed reviews

### Tax-status recovery

- Local and disposable-copy migration logic was reviewed.
- Production preflight evidence was reviewed: database integrity reported `ok`, tax-status columns were present and populated, and the verified backup/snapshot was preserved.
- Exact production artifact parity was not independently completed because transfer infrastructure was blocked.
- Production `--apply` was not approved or executed.
- Work item was closed as an operational no-op with the parity limitation documented.

### Organization page review

Reviewed `frontend/src/pages/OrganizationDetail.tsx` and the served SPA shell for `/org/934334592`.

Findings:

1. The page shell returned HTTP 200, but that alone does not prove API data rendered.
2. The page starts many independent requests, including a duplicate organization/enrichment request.
3. Below-the-fold data should be lazy-loaded after the primary profile renders.
4. Optional request failures are largely silent; visible retry/degraded states are needed.
5. Server-rendered metadata must be verified on the actual running backend; generic homepage metadata was observed in the served shell during review.
6. API-base/CSP configuration involving `localhost` should be checked for LAN and production clients.
7. Mission text is forced to uppercase and the header is dense; readability and evidence hierarchy can improve.

No frontend changes were approved or deployed from this review.

**Claude Code follow-up (2026-08-08, read-only production check):** item 5 does not reproduce as of this check. `curl https://daanaa.org/org/934334592` returns org-specific title/description ("FEED THE PEOPLE NYC — Daanaa" + matching mission text), not generic homepage metadata. Not claimed resolved — most likely explanation is Codex's review captured evidence during the day's outage window (site was down ~14h) or before the precompute v2 swap. Needs a clean re-check once both parties agree on timing; not otherwise actioned.

### Operational control plane

Codex added and owns:

- `scripts/operational_preflight.py`
- `scripts/audit_backup_storage.py`
- `docs/OPERATIONAL_CONTROL_PLANE.md`
- `institution/tasks/T-2026-08-08-001-operational-control-plane.md`

These are read-only operational controls. They do not authorize deployment, migration, deletion, service restart, or backup pruning.

## P0-SEC-001 — Firestore nonprofit-verification rules

```
STATUS=COMPLETE
VERDICT=PASS (Codex: PASS WITH CONDITIONS, all addressed; deployed 2026-08-08)
BLOCKED_BY=NONE
NEXT_ACTION=none — optional authorized inspection of whether the collection held data prior to the fix (informational only, access is closed regardless)
UPDATED_AT=2026-08-08
```

Rule `firestore.rules: nonprofit_verifications` — `allow read, write: if request.auth.uid != null` (any authenticated user, full read/write over every nonprofit's verification records) → `allow read, write: if false`.

Tested: 6 static + 9 behavioural (real Firestore emulator), both proven to fail against the reverted rule. Codex round 1: PASS WITH CONDITIONS — all 5 conditions addressed (see full disposition in `agent-operations/journals/2026-08-08-p0-sec-001.md`).

**Deployed** via `firebase deploy --only firestore:rules --project the-giving-wallet` (the only project on this account). Not taken on the CLI's word: verified independently against the live production database —

```
curl https://firestore.googleapis.com/v1/projects/the-giving-wallet/databases/(default)/documents/nonprofit_verifications/test-verify-deploy
→ HTTP 403 PERMISSION_DENIED
```

matching exactly what the emulator suite predicted. Branch `p0-sec-001-firestore-hardening` pushed. Codex's condition 4 (whether the collection held data before this fix) remains open and unanswered — access is closed regardless of that answer, so it's informational, not blocking.

## Backend security review

```
STATUS=COMPLETE
VERDICT=PASS (founder-approved and deployed 2026-08-08)
BLOCKED_BY=NONE
NEXT_ACTION=none — awaiting Codex round-2 confirmation for the record only, not a blocker
UPDATED_AT=2026-08-08
```

**Severity correction, recorded here for the audit trail (Stewardship P6 — errors
corrected and documented, never hidden):** this package was earlier characterized
as "same review weight as P0-SEC-001," implying internet-facing exposure. That
was wrong. Verified post-deploy: the vulnerable route was reachable only via the
home server (`localhost:5000` / LAN) — `droplet_api.py`, which actually serves
`daanaa.org`, never had this route. The 200 status observed at
`daanaa.org/api/donor/.../giving-profile` earlier today was the SPA catch-all
returning HTML (`content-type: text/html`), not the vulnerable JSON endpoint
(`application/json`) — status code was checked, response body was not, at the
time of the original claim. Real bug, real fix, but LAN-scoped, never
internet-facing. Founder approved deployment before this correction was found;
deployment proceeded because the fix is correct and reversible regardless of
the severity mischaracterization.

**Round 1 conditions — all resolved, tested locally, not deployed:**

1. Production-serving path verified (read-only, SSH) to run the canonical 110,823-byte `droplet_api.py` with zero `v4_scores`/`org_embeddings` matches and zero `giving-profile` matches, on both current and `.prev` rollback copies. The vulnerable root-level file was never shipped to production.
2. Duplicate route copies (stray root `droplet_api.py`, `daanaa_api.py.pre-student-service.backup` — the latter newly found by Codex) recorded, confirmed unreferenced/unimported, left in place per no-deletion constraint.
3. `tests/test_giving_profile_route_removed.py` added (3 tests). Note: first draft asserted 404, which is wrong for this app (unmatched `/api/*` paths fall through to the SPA catch-all, 200/HTML — confirmed against a path that never existed). Rewritten to assert the removed route now behaves identically to any other unmatched path. Proven both directions with a real reintroduced handler.
4. `/api/health` alias removed from this package (was out-of-scope; the pre-existing test it patched is failing again, correctly).

Two additional real bugs found and fixed while resolving conditions:
- `test_embeddings_startup_regression.py` was logically ineffective (Codex's finding) — traced to a genuine bug in `daanaa_api.py` itself: `_load_embeddings()` swallows its own exceptions and never re-raises, so the startup code's blind "call then print success" reported success unconditionally. Fixed the code (checks `_emb_loaded` now) and the test (asserts the conditional exists). Proven both directions.
- `test_footer_links_to_visibility_discovery_hub` fix was initially "proven" against the wrong file — edited the main repo's `Footer.tsx` while the test's `ROOT` resolves to the worktree's own copy. Caught before reporting; redone correctly and proven against the actual tested file.

Full suite: `pytest tests/test_badge_progress_regression.py tests/test_embeddings_startup_regression.py tests/test_ops_alert_routing.py tests/test_giving_profile_route_removed.py tests/test_principles.py -q` → **37 passed, 1 skipped**.

Distinguishing test tiers: all of the above is **tested locally** (isolated worktree, in-memory/temp SQLite) except the production-serving-path check, which is **read-only production verified** (SSH file inspection, no writes). No **production mutation executed**. Nothing committed, pushed, or deployed.

**Scope:** `backend/2026-08-08-api-and-search` worktree at `/tmp/daanaa-backend-work`. Nothing committed to any shared branch. Full log: `/tmp/codex_backend_review.log`.

**Sub-verdict 1 — giving-profile route removal: PASS WITH CONDITIONS**

Justified: `tests/test_principles.py:58-80` requires no server-side giving route exist; `HEAD` had an unauthenticated `GET /api/donor/<donor_id>/giving-profile` returning donor preferences; canonical `daanaa_api.py` now has no route (removal comment at line 11393); no frontend caller found. Blast-radius approach (live reachability, auth absence, row count, callers) was appropriate, though the live-200 and row-count claims are journal assertions Codex could not independently reproduce from its environment.

**Not repository-wide complete** — the same route also exists in:
- `droplet_api.py` (the stray root-level shadow file, previously flagged, not deleted per constraint)
- `daanaa_api.py.pre-student-service.backup` (**newly found by Codex**; confirmed by Claude Code as a dead file — nothing imports or references it, 468KB, untouched since Aug 8 14:05)

Required follow-up:
1. Founder approval + P0-SEC-001-level security review before any deployment.
2. Confirm the production-serving path cannot reach root `droplet_api.py`.
3. Record an explicit decision for the duplicate route copies; do not delete under current constraint.
4. Add a regression test asserting the canonical API 404s this route.

**Sub-verdict 2 — approved-scope fixes: PASS WITH CONDITIONS**

Focused suite passes (34 passed, 1 skipped) and the pre-fix reasoning is sound for badge-progress, embeddings ordering, and ops-alert routing. Four conditions:

1. `test_embeddings_startup_regression.py:125` is logically ineffective for the claimed bug — current code still prints success immediately after `_load_embeddings()` inside the same `try` block; the assertion only rejects success text appearing *after* `except`, which doesn't match this shape. **Fix required.**
2. `test_footer_links_to_visibility_discovery_hub` checks the URL and label exist independently, not that they form the same link — can pass if the URL is dead and the label appears elsewhere. **Fix required.**
3. `test_no_paid_placement`'s comment-stripper is fragile and doesn't catch every bare SQL identifier form of "promoted". **Acknowledged, lower priority.**
4. `/api/health` alias (`daanaa_api.py:1927`) is outside the approved four-item scope and absent from the journal's scope accounting. **Remove from this package, or get explicit scope approval.**

Root `droplet_api.py` and the prior-commit authorship collision: correctly left unactioned, per instruction — founder decision, not engineering.

## Lamp-tier re-check

```
STATUS=WAITING_REVIEW
VERDICT=BLOCKED
BLOCKED_BY=precompute_content.py not yet touched (explicitly blocking); research pages still render live tier data; new copy needed for WhyDaanaa.tsx; unresolved coverage claim; backend tier-filter coupling undecided
NEXT_ACTION=Founder decision needed on scope (see below) before further engineering; mechanical items (precompute separation, coverage claim) can proceed without new copy
UPDATED_AT=2026-08-08
```

```
STATUS=COMPLETE
VERDICT=PASS (founder-directed, deployed 2026-08-08)
BLOCKED_BY=NONE
NEXT_ACTION=none — Codex re-review welcome for the record, not a blocker
UPDATED_AT=2026-08-08
```

**Round 2 — founder poll resolved every open item, all now shipped:**

- `WhyDaanaa.tsx`: "Visibility levels"/"What each tier means" → "Financial context"/v6 framing. Link target was already correct.
- `ResearchFindings.tsx`: the live interactive Beacon/Torch/Candle/Spark chart (still clickable, still linked to tier-filtered directory results) **removed entirely**, not just captioned — per founder direction ("current methodology only... in beta... don't confuse users," a future "learning deck" mentioned as separate/later work, not built here). Replaced with a non-tier org-count-by-category view on the same data. Fixed 2 remaining tier references in "Key Insights." Found and fixed a real bug in my own earlier edit: a `<div>` nested inside an `<h3>` plus a stray duplicate `</div>`.
- `ResearchLimitations.tsx`: confirmed clean — the earlier P5 fix already removed its only tier reference; no superseded banner added since nothing retired-and-active remains to caption.
- `OrgCard.tsx`: the 99.78%/87.5% claim (a code comment, never user-facing) given its exact denominator, date, and re-runnable SQL.
- `scripts/precompute_content.py` — **the item explicitly blocking deployment**: `methodology.json.gz` tiers → v6 context levels (matches `Methodology2.tsx` wording exactly); `tier_distribution` stats removed (confirmed unconsumed); `how_it_works.json.gz`'s Spark→Blazing "Lamp journey" (same ranking-advancement framing problem as the old ForNonprofits copy) replaced with 3 v6 steps — not linked from any live page, but `droplet_api.py` still serves the endpoint directly, so fixed rather than left stale.

Regenerated and shipped. **Verified live**: `GET https://daanaa.org/api/methodology` → `version: v6.0`, `context_levels: [Full Context, Regional Context, Broad Category, Archetype Only]`, zero tier names. Frontend deployed, smoke-tested: `/`, `/methodology`, `/research`, `/why-daanaa`, `/for-nonprofits`, `/tiers` (redirects, no longer 404s), `/org/<ein>` — all 200.

**Deferred, explicitly not blocking, no live user exposure:** `scripts/research_summary_generator.py` still computes a `merit_tier` distribution into a DB table that `export_research_snapshot.py` reads into `research-snapshot.json` — but nothing in the frontend reads those fields anymore (verified before deferring). Dead data, not a live claim. Backend tier-filter query support in `daanaa_api.py`/`droplet_api.py` was retired in a separate commit the same day (see below).

**Original scope, for reference:**

Resolved since the first BLOCKED verdict:
- `ForNonprofits.tsx` — tier journey replaced with v6-oriented, P4-compliant guidance. ✅
- `/tiers` route redirects to `/methodology#financial-context`; `TiersPage.tsx` removed; Governance links migrated. ✅
- `ResearchLimitations.tsx` P5 dormancy wording corrected. ✅
- `About.tsx`, `Approach.tsx` addressed. ✅

Still open:
1. `WhyDaanaa.tsx` still contains "Visibility levels" / "What each tier means" copy (line 141). **Needs new donor-facing wording — founder review required, same as prior copy changes today.**
2. `ResearchFindings.tsx` has a dated Superseded notice but still renders **live, interactive** Beacon/Torch/Candle/Spark charts with links to tier-filtered directory results — not treated as historical.
3. `ResearchLimitations.tsx` has no dated Superseded notice (the P5 wording fix was applied, but the notice itself was not added here — it was added to ResearchFindings only).
4. `research-snapshot.json` still contains live lamp-tier data the UI treats as active.
5. **`scripts/precompute_content.py` still entirely untouched** — no commit, still contains hardcoded lamp-tier/"Lamp journey" content at lines 162–173 and 311–341. Explicitly blocks deploying any frontend methodology/research copy: until this regenerates, precompute-generated pages would serve tier language while the frontend says tiers are retired.
6. The 99.78%/87.5% coverage claim in `OrgCard.tsx:132` still lacks a denominator, snapshot date, or query — remains an unreproducible number in a code comment.
7. `TrustBadge.tsx` still has lamp tier types, derivation, and progression logic — open.
8. `LampMark.tsx` still exists, used by `AdminPage` — potentially fine to defer if confirmed admin-only, not yet confirmed.
9. `daanaa_api.py` / `droplet_api.py` tier filter support still coupled to research/directory query paths — **Codex says not safely deferred**, needs a decision on whether legacy tier backend/admin support becomes its own package.
10. `research_summary_generator.py` / `export_research_snapshot.py` still generate lamp-tier data consumed by the live research page — open.

The external-link fix and regression-guard commits (already deployed and verified live) are outside this blocker and do not affect the verdict.

## Coordination rules

- Claude Code works in its isolated backend worktree.
- Codex reviews evidence and operational impact; it does not edit Claude-owned backend files.
- Do not use broad `git add -A` in a shared checkout.
- Do not rewrite authorship history for already committed files without explicit approval.
- Every verdict must include exact files, commit SHA or working-tree state, tests and exit codes, deployment target, smoke results, and rollback evidence.

## Current authorization

Authorized:

- local/disposable tests;
- read-only production checks;
- backend work in the isolated worktree;
- preparation of review artifacts;
- mechanical fixes to the 4 open backend conditions (tests, scope-trim, documentation) that require no new public wording.

Not authorized:

- production `--apply`;
- destructive infrastructure actions;
- IAM, SSH, firewall, DNS, or retention changes;
- deployment based only on a provisional or missing verdict;
- new public claims or methodology wording without review (blocks: `WhyDaanaa.tsx` tier copy, any further lamp-tier public-facing rewrite).
