# TODOS.md

Deferred work, written down so it's real (operating agreement: vague intentions are
lies). Each item: what, why, and enough context to pick it up cold. Priority: P1 blocks
launch, P2 soon, P3 someday.

---

## Action layer — giving (the "information without action" thesis)

### P1 — G1 attorney review (the real gate)
Public "Give here" CTAs may count as soliciting donations → charitable-solicitation
registration in ~40 states. The give-path build is a two-way door; **public launch is
gated here.** Blocked on lawyer funds (~$300–500). Until then, build behind a flag, don't
promote. Context: `meritgiving-ops/partnerships/everydotorg-brief.md`, `LAUNCH-CHECKLIST.md` G1.

### P1 — G2 IRS auto-revocation filter
Suppress / clearly badge give paths for orgs on the IRS auto-revocation list. Routing a
gift to a revoked org is real harm + liability. Must be live before any give CTA. Pair
with Every.org's verified donate-ready status data. Context: `LAUNCH-CHECKLIST.md` G2.

### P2 — EIN-router fallback give-path (behind a feature flag)
Routing policy: org's own verified donate link first → Every.org EIN deep link (zero fee)
→ PayPal Giving Fund (dormant/unbankable orgs, check by mail). Build behind a flag, not
user-visible until G1 + G2 clear. Reuses the existing `donate_url` / `donate_confidence`
pipeline. Deferred per founder's "open Every.org partnership first" choice 2026-06-01.

### P2 — Every.org partnership
Outreach drafted, ready to send from `partners@daanaa.org`
(`meritgiving-ops/partnerships/everydotorg-brief.md`). Confirm contact address, send,
secure: Charity API access, verified-status data, zero-fee + for-profit-use terms.

### P3 — PayPal Giving Fund fallback
Secondary rail for truly dormant orgs (no bank, may never enroll) — PPGF mails a check
within ~75–90 days. Lower priority; Every.org covers the reachable majority first.

---

## Trust & brand

### P3 — Nested `<a>` inside `<a>` on org cards (HTML validity / hydration warning)
**What:** `OrgCard.tsx:336`'s cause-tag link renders inside `OrgCard.tsx:273`'s
whole-card link — an anchor nested inside an anchor. Browsers auto-correct this in
rendering but React logs "In HTML, `<a>` cannot be a descendant of `<a>`. This will
cause a hydration error" and "`<a>` cannot contain a nested `<a>`."
**Why:** Surfaced 2026-08-09 during the Directory page design review (console
errors while verifying an unrelated fix). Confirmed pre-existing, not caused by
today's changes.
**Pros:** Real hydration-warning fix; cause-tag clicks currently work by accident
(browser DOM correction), not by design.
**Cons:** Needs a structural fix (e.g. `stopPropagation` + a non-anchor clickable
span, or restructure so the cause tag isn't a true nested link) — not a one-line
change.
**Context:** Found via `agent-browser console --errors` while confirming the
mission-casing fix; not investigated further, no fix scoped yet.
**Depends on:** None.

### P3 — Mission source attribution in the hero (text, not just the AI badge)
**What:** The hero mission paragraph shows an `AiBadge` icon when the mission is
AI-generated, but doesn't say which source (IRS Form 990 / NTEE category /
organization website / verified by organization) the way the removed
`OrgInfoHierarchy` Mission tier used to.
**Why:** Removing that tier (2026-08-08, duplicate-content fix) dropped the only
place that spelled out the source in text. Stewardship P3 (evidence-based,
explainable) is still met via the icon + tooltip, but a text line would be
clearer for a donor who doesn't hover.
**Pros:** Small, focused addition; keeps the hero as the single home for mission
info instead of splitting it across two page locations again.
**Cons:** Hero is already dense (name, mission, location, CTAs, badges) — needs a
compact treatment, not a full sentence.
**Context:** Not urgent — the AiBadge already discloses AI-generated missions
visually; this closes a smaller gap (source for non-AI missions too, e.g. "IRS
Form 990" vs "organization website").
**Depends on:** None.

### P2 — Org page loading skeleton (replaces blank-screen spinner)
**What:** Build a skeleton loading state for `OrganizationDetail.tsx` that matches the
real layout (hero shape, badge row, content blocks) instead of the current blank navy
screen with a centered spinner.
**Why:** Surfaced 2026-08-08 during the org-page design review (Pass 2, Interaction
State Coverage). On a slow connection a blank screen reads as broken, not loading —
the highest-traffic decision page on the site shouldn't risk that impression.
**Pros:** Standard, well-understood pattern; meaningfully improves perceived
performance without any backend change.
**Cons:** Real, separate work — needs to track the actual DOM shape (hero height,
badge row, sidebar) closely enough to avoid layout shift when real content arrives.
**Context:** Deferred out of the same pass that shipped the flame-language fix,
FAQ tense fix, category-dedup fix, "Size: 0" fix, financial-history consolidation,
and duplicate-content removal — kept those changes focused and independently
verifiable rather than bundling in a bigger UI addition.
**Depends on:** None.

### P3 — Wallet explainer video (replaces the homepage text pitch)
**What:** A short explainer video/audio for how the Giving Wallet works, to replace the
homepage's WalletSection text pitch + preview mockup once produced. Explore NotebookLM
(feed it the wallet docs/methodology, generate an Audio Overview or video overview) as a
low-effort production path before committing to a full video shoot.
**Why:** Surfaced 2026-08-08 during the homepage redesign — video explains "how it works"
better than a text pitch for a skeptical first-time visitor (ease-over-persuasion
research cited in that session). Video production is its own workstream, not a same-day
build.
**Pros:** Stronger trust/comprehension than text; NotebookLM path is genuinely low-effort
compared to a real production pipeline.
**Cons:** Still needs a script/source doc, a review pass for accuracy (Stewardship P3 —
nothing unverified stated as fact), and hosting/embed decisions.
**Context:** For now, the homepage carries one line + a link to /wallet instead of the
full pitch section — swap this TODO's output in later without re-touching the homepage IA.
**Depends on:** None to start exploring NotebookLM; final embed depends on where the
homepage settles after this redesign ships.

### P2 — Partnership logos (build when the first partner signs)
**Honesty guardrail (Stewardship): a logo only renders once that partner is genuinely on
board. No logo before a signed deal — that would be a fake trust signal.**
Data-driven so it's structurally impossible to show an unconfirmed partner:
- A `frontend/src/data/partners.ts` config: `{ name, logoUrl, url, role, status: 'live' | 'pending' }`.
- A `<GivingPartners>` strip that renders ONLY `status: 'live'` entries; renders nothing
  when there are none.
- Two placements: (1) on the give path — "Routed via [logo], 100% to the nonprofit"
  (functional + often required attribution); (2) a quiet "Giving partners" strip on About
  (and maybe Home).
Trigger to build: the moment Every.org (or any partner) is confirmed. ~10-minute add then.
Do NOT build the empty component now (YAGNI — no caller yet).

### P2 — Card-level evidence markers (data source + last-verified date)
**What:** Small marker on `OrgCard.tsx` (and search results) showing where the data came
from (IRS/ProPublica) and when it was last verified — not just asserted once on the
homepage trust block.
**Why:** Proves trust at the actual decision moment (the card the donor is about to click),
not only on first landing. Ties to the Fogg credibility research (specificity beats a
single hero-level claim) surfaced during the 2026-08-08 homepage design review.
**Pros:** Reinforces credibility sitewide; cheap per-card once the data field exists.
**Cons:** `OrgCard.tsx` is a widely-reused component — any change ripples across
Directory, category pages, compare, wallet. Needs a data-freshness field wired through
the API (`daanaa_api.py` response), not just a frontend change.
**Context:** Surfaced as an explicit alternative to (not a replacement for) the homepage
second-beat trust block — founder chose the single block for now, logged this as the
distributed-trust follow-up.
**Depends on:** API exposing a last-verified/data-source field per org (check if one
already exists before adding a new column).

### P2 — AI-slop audit beyond the homepage
**What:** Run `/design-review` (or a targeted plan-design-review pass) on Directory,
category pages, and the org-card grid against the AI Slop blacklist (icon-in-circle
grids, cookie-cutter section rhythm, generic 3-column feature grids).
**Why:** The "doesn't look like AI" ask covered the whole site; the 2026-08-08 review
only audited the homepage.
**Pros:** Completes the original ask; these pages get far more traffic per session than
the homepage does once a visitor starts browsing.
**Cons:** Separate review pass, separate approval cycle — don't want to block the
homepage ship on it.
**Context:** Sequencing one surface at a time (homepage first, since it ships the new
trust-beat and consolidated IA) keeps each pass reviewable.
**Depends on:** Homepage redesign shipping first, so there's a consistent pattern to
extend rather than two designs evolving in parallel.

### P3 — Actually delete the dormant lamp-tier/visibility engine (not just retired copy)
**What:** Remove `getTierFromOrg`/`getTierSummary`/`TIER_COLORS`/`TIER_INK`/`TIER_MICROCOPY`/
`merit_tier` logic from `TrustBadge.tsx`, delete `LampMark.tsx`, and the 5 `tier-*` CSS
vars from `index.css`/`tailwind.config.js`. Update the two call sites in
`Directory.tsx`/`OrganizationDetail.tsx` to stop computing `trustSummary` from tier logic
(it's currently unused by `OrgCard` anyway — confirm nothing else needs it, then drop the
prop entirely).
**Bigger than first scoped:** `AdminPage.tsx` (624 lines, the only importer of `LampMark`)
is itself entirely dead code — `App.tsx:25` lazy-imports it but no `<Route>` in the app
ever renders it (`/admin` routes to `DashboardHub`, `/admin/operations` to
`AdminOperations`). Confirmed via full-repo grep: `AdminPage` has exactly one reference
outside its own file, the unused import. Before deleting, check whether `AdminPage.tsx`
has functionality (org moderation? data QA?) that's genuinely needed and just lost its
route by accident — if so, re-route it instead of deleting; if it was superseded by
`DashboardHub`/`AdminOperations`, delete the whole file.
**Why:** 2026-08-08's retirement removed the tier system from public copy but left the
underlying engine live — see LESSONS.md 2026-08-08 entry. Dead code that still computes
"Beacon/Torch/Candle/Spark" classifications is a Toyota-muda + explainability smell: a
future engineer greps for "tier" and finds a fully wired system, not a retired one. Same
logic applies to a 624-line unrouted admin page — either it's needed (re-route it) or it's
muda (delete it); leaving it orphaned is the worst of both.
**Pros:** Codebase actually matches the "retired" claim; removes ~150 lines of dead tier
logic, one dead component, and resolves whether a 624-line admin page is lost
functionality or dead weight.
**Cons:** Touches a widely-imported file (`TrustBadge.tsx` — also exports
`getFinancialHealth`, `financialContextLabel`, `PASSING_BANDS`, which ARE still live and
must NOT be removed in the same pass). Needs care to remove only the dormant tier exports.
Determining whether `AdminPage.tsx` lost its route by accident needs a git-blame/history
check, not just a grep.
**Context:** Low urgency — nothing user-facing is broken, this is pure cleanup. Not
blocking the homepage redesign.
**Depends on:** None — can be done independently, any time.

---

## Answer Card sprint (phase 1 → phase 2 gate)

### P2 — Gate homepage/causes phases on proven indexation, not calendar weeks
Outside-voice finding (Codex, 2026-07-10 eng review): the whole answer-card strategy
bets on Google distributing 1.7M org pages, but Search Console indexation status is
still unverified (the design doc's own open Assignment item). Before starting phase 2
(homepage, weeks 3-4), check: how many org pages are indexed, impressions/CTR by page
state (scored vs no-data vs revoked), and external website/donate handoff rate — not
just the 3-person hallway test. If indexation is weak, redesigning the homepage
decorates pages Google is ignoring instead of compounding the real bottleneck.
Context: `~/.gstack/projects/meritgiving/akbar-master-design-20260710-000500.md`
(Recommended Approach, phase sequencing). Revisit via /plan-ceo-review if the numbers
come back weak — don't silently proceed on the calendar.
Depends on: Search Console access (already a design-doc dependency).

### P2 — Sitemap deploy pipeline: daanaa.org DONE 2026-07-10; data.daanaa.org refresh blocked on Cloudflare token
Resolved 2026-07-10: richness-first org sitemaps are now live on daanaa.org itself —
`https://daanaa.org/sitemap-index.xml` + `/sitemaps/orgs-0001..0035.xml` (1,746,595
URLs, scored orgs first). Files live at droplet `/opt/daanaa/visibility/` (deliberately
OUTSIDE `/opt/daanaa/frontend/dist`, which `deploy_morning.sh` rsyncs with `--delete`)
and are served by two new nginx locations in `/etc/nginx/sites-available/daanaa`
(backup: `/root/nginx-daanaa.bak-20260711014934`). Redeploy any time with
`scripts/ops/deploy_org_sitemaps.sh` (generate → rsync → public smoke test).
The three blocking questions were answered: (1) directory mismatch was a non-issue —
`build_overlay.py` already invokes `generate_visibility_exports.py` with
`--dist visibility/public`; the `dist/` default only applies standalone and is what
the droplet path now uses. (2) Beacon crash = transient schema-parse collision with a
concurrent FTS rebuild (quick_check ok, not reproducible); step 3 of
`run_visibility_pipeline.sh` is now non-fatal per founder decision so it can't block
the deploy steps. (3) still open — no cron schedule for the visibility subsystem.
REMAINING: data.daanaa.org (Cloudflare Pages overlay) is still serving the old
EIN-ascending sitemaps from Jul 1. `visibility/public/` + `visibility/cloudflare-public/`
are regenerated and ready, but `npx wrangler pages deploy` needs `CLOUDFLARE_API_TOKEN`
(not stored anywhere on this box; past deploys were interactive via
`deploy_cloudflare_pages_interactive.sh`). Founder: run
`DEPLOY=1 visibility/scripts/deploy_cloudflare_pages.sh` with the token exported.
Also recommended (frontend-gated, needs approval): add
`Sitemap: https://daanaa.org/sitemap-index.xml` to `frontend/public/robots.txt`,
and a weekly cron for `scripts/ops/deploy_org_sitemaps.sh`.

### P3 — Track claim-flywheel evidence before treating it as a growth pillar
Outside-voice finding (Codex): `org_claims` currently has 3 rows. The design doc frames
"claim this page" as a core growth loop for the invisible 97%, but there's essentially
no evidence yet that the loop converts. Not blocking phase 1 (the claim CTA already
exists and phase 1 doesn't remove it) — just don't plan future phases assuming this
loop works until claim-rate data says so. Track claim conversions from no-data-card
impressions once phase 1 ships.

### P2 — 51 pre-existing test failures in tests/ unrelated to tonight's work
Found 2026-07-10 while verifying a v4_scores schema-drift fix via a full-suite
A/B run (`git stash` comparison against an isolated DB copy). Baseline was 53
failed/261 passed BEFORE any of tonight's changes — these are pre-existing, not
caused by this session. Spans wallet-sync (`test_wallet_sync.py` — spot-checked
`test_wallet_requires_auth`: `/api/wallet` doesn't exist as a route anymore,
falls through to the SPA catch-all and returns 200 HTML instead of 401 JSON —
stale test coverage for a removed/refactored endpoint, NOT a live auth bypass,
but worth confirming that for every failure in this cluster, not just the one
spot-checked), nonprofit-portal (`test_nonprofit_endpoints*.py`, Stripe webhook
+ letter-credit tests), SPA/routing (`test_spa_fallback.py`, `test_routing.py`),
enrichment integration (`test_enrich_batch_integration.py`), and v5 scorer
validation (`test_merit_scorer_v5_0.py`). Not triaged individually — only one
spot-check was done to rule out an urgent security issue.
Context: run `DB_PATH=data/merit_registry.db.bak-<latest> python3 -m pytest tests/`
(the live dev gunicorn holds a persistent DB lock; use a backup copy to test
standalone) to reproduce the current failure list.
Depends on: nothing blocking — this is stale test debt, not a production issue,
but a large cluster of `assert 200 == 401`/`assert 405 == 200` results across
one subsystem (wallet-sync) is worth a dedicated look in case it's one shared
root cause (e.g. a route rename) rather than 15 independent bugs.

---

## Ops / launch (see LAUNCH-CHECKLIST.md for the full gate list)
- P2 — Minova disclosure + written consent before any public/LinkedIn announcement (task #20).
- P3 — Cloudflare SSL Full(strict) + origin cert before heavy launch (currently Flexible for beta).
- P3 — DKIM record for daanaa.org (Google Workspace → Authenticate email).

### ✅ DONE 2026-07-10 — Rebuild enrichment loop properly (Layer 1 Qwen parsing fix) before re-enabling cron
Resolved same day: structured output via response_format json_schema + fail-closed
parsing (see DECISIONS.md 2026-07-10); cron re-enabled; 5-org live run verified.
Original entry kept below for context.
The 2am `enrichment_loop_8pm_8am.sh` cron was disabled 2026-07-10 (see DECISIONS.md):
Layer 1 (missions/cause tags/websites/donate links — the stages that actually feed the
site) was already disabled due to Qwen verbose-output parse errors, and Layer 2
(contact/programs/S3 embeddings) was removed as zero-yield. To resume enrichment growth:
fix the Qwen response parsing in `scripts/qwen_inference.py` (or constrain output via
grammar/JSON mode on the llama-server), re-enable Layer 1, verify yield on a 100-org
dry run, then restore the cron line (backup of the old crontab was in session scratchpad;
the line is commented in place). If contact/programs enrichment is ever wanted again,
wire the already-fetched website HTML (`scripts/website_content.py`) into the extractors
and remove the hardcoded Houston/Texas service-area heuristic in
`scripts/programs_extraction.py`. Note: 8 pre-existing test failures in
`tests/test_enrich_batch_integration.py` + `test_enrich_batch_real_inference.py` test the
consolidated Layer 1 flow and should pass again once Layer 1 is fixed.

### P3 — Recall-system backend is dormant with no consumer — drop or rebuild
Frontend consumers deleted 2026-07-10 (MacroContextCard, KnowledgeGraphCard, api.ts
types). Backend remains: `/api/organizations/<ein>/recall` in daanaa_api.py, tables
knowledge_graph_entities (60K rows of NTEE-letter junk), knowledge_graph_relationships
(30K), macro_context_snapshots (1K, CPI index stored where inflation % expected),
context_recall_orchestrator*.py, expand_macro_context.py. Not on cron, costs nothing.
Next cleanup pass: either drop the tables + endpoint + scripts, or rebuild with real
data (FRED inflation %, real entity extraction) if the product ever wants macro context.

## Quarterly graphify dead-code audit due (2026-07-21)
Graph refreshed automatically. Run the actual audit manually (or ask Claude Code):
grep the graph for duplicate function/class names across files + isolated
(<=1 edge) nodes, verify each with git log + grep for live references,
archive confirmed-dead files to archive/dead_code_$(date +%Y%m%d)/ with a
30-day recall README. See DECISIONS.md 2026-07-21 for the reference pattern.
(Next auto-reminder: ~2026-10-19)

