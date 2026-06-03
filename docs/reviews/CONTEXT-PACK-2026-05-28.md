# Daanaa — Context Pack for External Reviewer

**Date:** 2026-05-28
**Audience:** A senior reviewer who knows the mission but has no repo access.
**Goal:** Get you to a useful opinion in 10 minutes.

---

## 1. What Daanaa is

Daanaa (working domain: **daanaa.org**, rebranded from "MERIT / MeritGiving" on 2026-05-24) is a civic-good directory of US 501(c)(3) nonprofits. It assembles three public datasets (IRS Business Master File, NCCS, ProPublica Nonprofit Explorer 990 JSON/XML), normalizes them into a single SQLite-backed registry of ~430,000 deductible 501(c)(3) organizations, computes a 0-100 peer-context financial score for those with sufficient 990 data (~546K rows are scored across all tax-exempts; ~430K are 501(c)(3) deductible), benchmarks each organization against a peer group built from its NTEE subcategory × revenue band × (optionally) region, and exposes the result through a React/Tailwind UI.

There are two surfaces:

1. **Public directory.** Anyone can search by name, EIN, cause tag, state, NTEE category, tier. Org detail pages show the score, peer percentile, financial reserves, NTEE peer rank, and a "Give directly" button that links to the organization's own giving page (Donorbox, Givebutter, Stripe, PayPal, etc.) — **never to a Daanaa-hosted checkout**.
2. **Private Giving Wallet + Giving List.** Donors can save organizations, add intended amounts, choose between requesting an acknowledgment letter ($250+ IRS itemization path) or staying anonymous (split into bank-statement-sized entries), and log completed donations. All of this state is **localStorage / sessionStorage only**; nothing about a donor's giving history is sent to Daanaa's servers.

## 2. Stage

Pre-launch. The ops state file (`launch-blockers.md`) shows every Gate 2-7 line item still open: DNS pointing to the server, Google Workspace email, GitHub repo creation, Plausible/Sentry analytics, attorney consult, DBA filing of "Daanaa" under the founder's existing LLC. The STEWARDSHIP commitment was signed 2026-05-20 by the founder and the AI engineering agent; the rebrand from MERIT happened 2026-05-24. There is no CI, no staging environment, no production deploy yet. The product runs locally on a Ryzen 9700X + R9700 GPU box behind a forthcoming Cloudflare tunnel.

## 3. Stack

- **Backend:** Flask 3 + flask-cors + flask-limiter on Python, served by gunicorn `-w 4 --preload` on port 5000. Single SQLite file (~17 GB data directory). Entry point is a 3-line shim `daanaa_api.py` that imports a 1233-line `merit_api.py` (the file rename is queued for "Phase 3").
- **Search:** SQLite FTS5 + 1024-dim cosine vector search via local `llama-server` (Vulkan on the R9700 GPU), with Ollama fallback. The two paths are fused with Reciprocal Rank Fusion (k=60) and the result advertises `match_sources: ['keyword', 'semantic']` so the UI can show *why* an org appeared.
- **Embeddings:** `mxbai-embed-large` (1024-dim) precomputed for 546K scored orgs, loaded into a numpy matrix at gunicorn `--preload` time and CoW-shared across workers (~3 GB RAM).
- **Scoring (live, DB-backing):** `scripts/compute_composite_score.py` — `composite = 0.65 × revenue_pct_in_peer_group + 0.35 × reserve_pct_in_peer_group`. Peer group = NTEECC × revenue band × (region if regional group ≥ 30 orgs, else national fallback). Snapshots in `score_snapshots`; runs audited in `scoring_runs`. Versioned `v1`.
- **Frontend:** React 19, Vite 7, TypeScript 5.9, Tailwind, Radix UI primitives. 22 routes (`App.tsx`). Wallet/list state is React Context + localStorage. No global state library.
- **Data ingest:** A swarm of `scripts/agent*`, `scripts/overnight_*`, `scripts/enrich_*`, `scripts/ingest_*` python files (some live, some abandoned). `scripts/donation_link_pipeline.py` crawls verified org websites with robots.txt respect and per-domain rate limiting to discover and verify donate URLs (Donorbox, Givebutter, etc.) — confidence threshold 90 required.

## 4. The two hard invariants — and whether they hold

### Invariant 1 — Daanaa NEVER touches money.

**Holds.** I traced every donate/payment path in the code:

- The "Give directly" CTA on the org detail page is a plain `<a href={donate_url} target="_blank" rel="noopener noreferrer">` — the donor jumps off Daanaa to the org's own giving page.
- The Wallet/Giving List flows write only to localStorage/sessionStorage. `addDonationDirect` persists to a `merit_wallet_donations` key on the browser. Reference codes for the "letter requested" path are generated client-side (`DAANAA-YYYY-XXXX`) and stored locally.
- I enumerated all 22 API routes. The only POST/PATCH endpoints are `/api/waitlist` (email signup), `/api/link-feedback` (anonymous "this link is broken"), and `/api/claim/*` (nonprofit ownership claim via mailed PIN). None of them accept currency, amount, processor token, or any monetary payload.
- `donate_platform` field values include `stripe, paypal, venmo, cashapp, classy, donorbox...` but these are *string labels* used to render "via Stripe" etc.; no SDK is imported and no webhook endpoint exists.
- The Lob.com letter API is the only paid third-party touch (mails verification letters to claimant nonprofits), and Daanaa pays for that — it is not donor money.

### Invariant 2 — Private by default.

**Holds with one caveat.**

What hits the server:
- Newsletter signup: `email` (intended PII, opt-in, admin-key-gated retrieval).
- Anonymous link feedback: `EIN + reason` only — no IP, no donor data.
- Claim flow: claimant nonprofit's `email + EIN + IRS address` (which is itself public) + a server-generated 6-digit PIN, used once to verify ownership.

What does **not** hit the server:
- Donor identity, donor email, donor name, donor amount, donor giving history, intended giving list, organizations the donor has favorited, reference codes — *all of it* lives in the donor's browser. The only time donor email would touch the server is *if* the donor opts into the "request acknowledgment letter" path, but **the backend that would receive that data does not yet exist** (see §6, Finding 3). Today, even letter-request donor emails stay in localStorage.

**Caveat:** the claim-letter sender (`scripts/send_claim_letter.py`) logs the 6-digit PIN in plaintext to `logs/claim_letters.log` whenever Lob.com is not configured. The same log also stores the verify URL including the PIN as a query string. Anyone with read access to `logs/` can take over an unclaimed organization page. This is a Critical-adjacent privacy/integrity issue tracked as P0 Finding 1.

## 5. The scoring model — design summary

Daanaa's score is **deliberately peer-bounded, not absolute.** A $200K community arts org is never benchmarked against the Harvard endowment. The peer group is constructed as:

1. **Primary key:** NTEE-CC subcategory (3-char IRS code, e.g. `B24` = "Elementary, Secondary Education") × revenue band (7 bands from $0-100K up to $100M+).
2. **Regional refinement:** if the (subcategory, band, US Census region) bucket has ≥ 30 orgs, the org is scored within that regional bucket; otherwise it falls back to the national subcategory × band bucket.
3. **Score formula:**
   - `rev_pct` = revenue percentile within group (higher revenue → higher percentile)
   - `rsv_pct` = reserve percentile within group (more months-of-reserve → higher percentile)
   - `composite = 0.65 × rev_pct + 0.35 × rsv_pct`, clamped to [0, 100], rounded to 1 dp
4. **Reserve metric** is `months_of_reserve` from ProPublica when available; otherwise a crude `total_assets / total_revenue × 12` fallback (this is honest but coarse and should be documented in the public methodology page).
5. Each org also gets a **tier name** in the frontend vocabulary: Beacon > Lantern > Flame > Ember > Spark, and a **journey band**: Blazing > Burning Bright > Steady Flame > Growing > Just Starting. These are two parallel naming conventions and need a single explanation page so reviewers understand which is "where you are" vs "how much we know about you."

The composite scorer is `scripts/compute_composite_score.py` (live). A *second* scorer also lives in the repo — `scripts/merit_scorer_v3_3.py` — that uses four ratios (program 30%, sustainability 25%, reserves 25%, leverage 20%) and emits "Blazing/Burning Bright/..." bands. **This second model does not feed the live database.** This is a STEWARDSHIP §9 ("decisions should be explainable later") gap: two models sitting side by side with no documentation of which is canonical. P1 finding.

## 6. Top 10 findings across all lenses

1. **P0 — Claim-letter PIN logging is a silent takeover vector.** `scripts/send_claim_letter.py:138-148` writes the 6-digit PIN, the verify URL (also containing the PIN as a query string), the EIN, and the IRS address to a plaintext log whenever Lob.com is not provisioned. Anyone who can read `logs/claim_letters.log` can take over an unclaimed organization's page (which then lets them edit mission and donate_url). Mitigation: hash the PIN before logging, use an opaque token in the URL instead of raw PIN, chmod 600 on `logs/`.

2. **P0 — `org_claims` table is referenced in code but never created.** `merit_api.py` has `_init_waitlist_table()` and `_init_link_feedback_table()` at module load, but no `_init_org_claims_table()`. The live DB has the schema (someone created it by hand), but a fresh deployment will 500 on `POST /api/claim/start`. The whole claim flow is one git-clone away from broken.

3. **P0 — The Wallet "letter pending" promise is vapor.** The UI tells the donor: *"Once they upload your letter, Daanaa emails it to you and stores it in your wallet."* No backend endpoint exists for nonprofits to upload acknowledgment letters; no mailer worker exists. Reference codes are generated client-side and have no server-side counterpart. This directly violates STEWARDSHIP §3 (evidence-based trust). Either build the backend or rewrite the copy in this sprint.

4. **P0 — `overnight_pipeline.py` writes to the wrong database.** Line 9 hardcodes `data/meritgiving.db` (legacy). The canonical DB is `data/merit_registry.db`. Any "overnight enrichment" job is silently appending to a dead database.

5. **P1 — Two scoring models, one canonical: undocumented.** `compute_composite_score.py` (live, 2-factor) and `merit_scorer_v3_3.py` (unused, 4-factor) coexist with similar method names. The public methodology page must cite the live one; the other should be deleted or moved to `archive/`.

6. **P1 — Admin auth uses non-constant-time string compare.** `merit_api.py:220` does `provided != _ADMIN_KEY`. A network-adjacent attacker can extract the admin key via timing oracle. One-line fix to `hmac.compare_digest`.

7. **P1 — Confirmation flow sends donors to a Google search.** `GivingConfirmation.tsx:131` builds `https://www.google.com/search?q=${orgName}+donate` as the "Complete your gift" link, even when the org has a verified `donate_url` in `apiOrg.donate_url`. The link verification pipeline goes to enormous effort to find the right page; the confirmation flow then ignores it. Donor ends up clicking the first sponsored Google result, which is sometimes a bad-faith middleman.

8. **P1 — `scripts/clean_names.py` is corrupted.** The file is 10 bytes of Alibaba S3 `NoSuchBucket` XML, presumably from a download that piped wrong. The name-cleaning step in the pipeline is referenced but not executable. Restore from git or delete.

9. **P1 — Tests reference an old port and an old brand.** `tests/merit.spec.js:3` sets `BASE_URL=http://localhost:8081` (the old FastAPI port) and line 7 asserts the visible text "MeritGiving." All four Playwright cases will fail post-rebrand. Either rewrite them or delete and start fresh.

10. **P2 — Repo hygiene blast radius.** Root has 3 live Python entry points (`merit_api.py`, `daanaa_api.py`, plus dead `app.py`), 8+ `app.py.backup.*` / `app.py.broken.*`, 13+ `fix_*.py` one-shot scripts, a `vite.config.ts.bak`, an `entities.json`, a file literally named `0]`, plus 4 SQLite DBs (`merit_registry.db` canonical, plus `meritgiving.db`, `merit_state.db`, `merit_registry_backup.db`). The `merit-platform/` and `nonprofit-explorer/` subdirectories appear to be earlier-incarnation projects that are not deployed. A newcomer (or a future agent) reading the tree cannot tell what is live.

## 7. Open strategic questions

These come from reading the strategy docs (`meritgiving-ops/strategy/`) cross-referenced with code state:

1. **What is the revenue model?** STEWARDSHIP §1 explicitly says it is undefined. The strategy docs (`funding-strategy.md`, `phase-plan.md`) describe grants and credits but no recurring revenue. Without a model, the runway question is unanswered. (Suggested: foundation grants → optional donor-side "tip" on the giving-list confirmation → nonprofit-side claimed-profile premium for analytics, in that order. None of these are wired today.)

2. **What is the legal entity?** ADR-001 contemplates operating as a DBA under the founder's existing LLC ("EcoMargins LLC dba Daanaa"). The DBA filing is unchecked in `launch-blockers.md`. Until that lands, "Daanaa" is operating as an unregistered name.

3. **Does the platform need to register for charitable solicitation?** Linking donors to nonprofit giving pages may or may not constitute "solicitation" under state statutes — the strategy doc flags California and New York as the priority opinions to get. No counsel has been retained.

4. **ProPublica's CC BY-NC-ND license.** The 990 JSON Daanaa indexes is CC BY-NC-ND. NC ("non-commercial") is the risk surface for any future revenue model. Confirm with counsel before any monetization.

5. **Which canonical scorer ships in v1?** As noted in finding 5, there are two. Pick one publicly before the methodology page can be honest.

6. **Letter pipeline: build or remove?** Finding 3. The site currently promises a service it cannot perform.

7. **Domain coordination.** Ops docs and `DAY_1_ACTION_PLAN.md` still reference `meritgiving.org`; code, OG tags, and CORS allowlist say `daanaa.org`. One of them is wrong. Reconcile before any funder reads either.

## 8. Proposed next steps (in priority order)

### This sprint (P0 — block launch until done)

1. Hash claim PINs before logging; chmod 600 `logs/`; replace `verify_url` PIN with HMAC token.
2. Add `_init_org_claims_table()` to `merit_api.py` so a fresh deploy comes up clean.
3. Either build a minimal letter-upload backend (`POST /api/claim/letters` with nonprofit auth + email-out worker) **or** strip the "Daanaa will email you the letter" copy from `Wallet.tsx` and `GivingConfirmation.tsx`. Pick one this week.
4. Fix `overnight_pipeline.py:9` to point at `merit_registry.db`. Grep all scripts for the legacy DB and migrate or delete.
5. Replace admin-key compare with `hmac.compare_digest`.
6. Write a pytest suite for the claim flow, deductibility filter, FTS sanitizer, and admin auth — at least 20 cases.

### Before broad outreach (P1)

7. Carry `donate_url` through the Giving List → Review → Confirmation flow so the "Complete your gift" link goes to the verified page, not Google.
8. Pick one scorer, delete the other, write the methodology page.
9. Fix `tests/merit.spec.js` (port + brand) or replace with a fresh Playwright spec.
10. Restore or delete `scripts/clean_names.py`.
11. Wire Content-Security-Policy header in `set_security_headers`. Add HSTS in production config.
12. Lob fallback must return `status=log_only` instead of `letter_sent` when no Lob key is set.
13. Strip sentinel values from `/api/stats` reserve buckets (currently `< 0` count includes `-999` sentinels).

### Post-launch hygiene (P2)

14. Delete dead root files (`app.py*`, `merit_app.py`, `merit_daemon.py`, `merit_master.py`, `app_with_feedback.py`, `debug_app.py`, `ui_agent.py`, all `fix_*.py`, all `app.py.backup.*`, `merit_api.py.bak`, root `index.html`, `vite.config.ts.bak`, `entities.json`, `0]`, `cloudflared.deb`).
15. Delete `merit-platform/`, `nonprofit-explorer/`, `static_web/`, `ui_backups/`.
16. Split `merit_api.py` into Flask blueprints (search, claims, admin, public).
17. Rename `MERIT_ADMIN_KEY` env var → `DAANAA_ADMIN_KEY` (coordinate with `.env`).
18. Rename `frontend/package.json` "name" from `my-app` to `daanaa-web`.
19. Decide and document the cleanup of dual scoring vocabularies (Beacon/Lantern/... vs Blazing/Burning Bright/...).

---

## 9. Highest-leverage single next move

**Solve findings #1 and #3 together this week.**

Finding #1 (claim PIN log) and finding #3 (vapor letter-pending UX) are the two most direct violations of STEWARDSHIP §3 (evidence-based trust). Both are low-effort relative to their impact:

- Finding #1: ~2 hours of work to hash the PIN, change the URL to use HMAC token, chmod the log, and write a regression test.
- Finding #3: a one-day decision — *build* the upload-letter endpoint (large) or *remove* the promise from the UI (small). Choose remove for now; the founding ops doc allows it ("planned UX improvement"); the live UI currently promises it as fact.

Together they remove the two findings most likely to embarrass the platform at launch: an integrity bug that lets an attacker silently claim any unclaimed org, and a UX promise the platform cannot keep. Everything else can wait for Gates 6-7.

---

## 10. What the reviewer should ask back

If the reviewer can come back with answers to any of these, the next iteration will be sharper:

1. Is the letter-pipeline UX promise worth building, or should it be removed?
2. Of the two scorers in the repo, which is the public-methodology one?
3. Has counsel weighed in on whether `daanaa.org` linking constitutes "solicitation" in CA/NY?
4. Is the founder OK with deleting ~50% of root-level files (all legacy)?
5. What is the timeline to Gate 6 (Pre-Launch Readiness) — weeks, or months?
6. Will the production deploy live on the same Ryzen box, or will we move to a cloud host? (Affects HSTS, CORS allowlist, log permissions.)

---

**End of context pack.** Total: ~2700 words.
