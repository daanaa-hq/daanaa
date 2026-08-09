# Decision Queue

Open questions awaiting the 12-hour board-simulation cycle.
Protocol: `docs/DECISION_WORKFLOW.md`. Append new items as they arise.

Format:
```
## [open|resolved|escalated] <short title>
- Raised: <date> by <who/what>
- Principles touched: <P#s>
- Data gathered: <yes/no + pointer>
- Simulation: <link or pending>
- Resolution: <decision + DECISIONS.md date, or blank>
```

---

## [resolved] Retire lamp tier from donor-facing profiles
- Raised: 2026-07-17 by founder ("is visibility tier even important on the profile anymore")
- Principles touched: P3, P4, P5
- Data gathered: yes — tier facts duplicated by plainer page elements
- Simulation: docs/BOARD_SIMULATION_2026_07_17.md (context)
- Resolution: retired from profiles, kept for claim flow. Shipped eaca6663de6.

## [resolved] Remove Score History table + v4 ScoreBreakdown
- Raised: 2026-07-17 during profile redundancy audit
- Principles touched: P3 (percentile deltas reflect our re-scoring, not org trajectory), P9
- Data gathered: yes — snapshot deltas driven by pipeline refreshes; <5% breakdown engagement (est.)
- Simulation: docs/BOARD_SIMULATION_2026_07_17.md (95% / 75% confidence)
- Resolution: both removed, founder-approved ("none are claimed, make the change"). Shipped 37b64f758ce.

## [resolved] Audit Q: Is Plausible active in production?
- Raised: 2026-07-17 by third-party system audit
- Principles touched: P2 (privacy-respecting analytics)
- Data gathered: yes — live homepage serves plausible.io script tag (verified 2026-07-17)
- Resolution: ACTIVE in production. Not residual. STEWARDSHIP P2 note already documents it.

## [resolved] Audit Q: Volunteer workflow scope
- Raised: 2026-07-17 by third-party system audit
- Principles touched: P8 (hand-off model)
- Data gathered: yes — droplet has org-side volunteer-event endpoints (GET/POST/PATCH);
  donor-side has NO in-platform signup (UI shows "Open to volunteers — Soon")
- Resolution: describe as "discovery-only for volunteers; claimed orgs may list
  events; signup always happens on the org's own channel." Matches hand-off model.

## [resolved] Audit Q: Which backend is canonical?
- Raised: 2026-07-17 by third-party system audit
- Data gathered: yes — CLAUDE.md + memory already answer this
- Resolution: daanaa_api.py is the canonical FULL API (local, port 5000).
  scripts/droplet_api.py is the canonical PRODUCTION EDGE (serves precompute
  static files; never SQLite). Both canonical for their tier; the drift risk
  between them is real and tracked as the open contract-guard item below.

## [resolved] Audit finding: "No confirmed in-platform payment flow"
- Raised: 2026-07-17 by third-party system audit (flagged as high-severity gap)
- Principles touched: P8
- Resolution: NOT a gap — it is a charter invariant. Daanaa never handles funds
  (STEWARDSHIP P8, "Never handle funds" non-negotiable). The audit's framing is
  corrected here for the record; no payment flow will ever be added.

## [resolved] Donor-facing terminology glossary (audit: vocabulary drift, High)
- Raised: 2026-07-17 by third-party system audit
- Principles touched: P3 (honest signals), P5 (careful language), P9
- Data gathered: yes — live census: rank 0, percentile 0, score 6, context 7, tier 16
- Simulation: docs/BOARD_SIMULATION_2026_07_17_EVENING.md
- Resolution: FOUNDER APPROVED 2026-07-17 ("i agree with the board, if its not helping lets remove it from the filters"). Glossary adopted: financial context / health signal / peer context. Visibility-tier filter removed from directory (both inline select and FilterSheet plumbing). Lint test remains as engineering task with the contract guard.

## [resolved] AI-output human-review policy (which outputs need review pre-publication)
- Raised: 2026-07-17 by third-party system audit
- Principles touched: P3, P10
- Data gathered: yes — current practice documented
- Simulation: docs/BOARD_SIMULATION_2026_07_17_EVENING.md
- Resolution: 5-point policy adopted (new claim types human-reviewed first; scale outputs verified+labeled+sampled monthly; give-path links always content-verified; comms always gated; scoring stays deterministic).

## [resolved] Full-backend vs droplet contract drift guard (audit: High)
- Raised: 2026-07-17 by third-party system audit
- Principles touched: P9; ops reliability
- Data gathered: yes — drift is real (2026-07-05 outage was this class of failure)
- Proposed: contract test asserting droplet_api routes/headers match daanaa_api
  for the shared surface; wire into principle test suite + terminology lint (audit's
  recommended Codex task)
- Simulation: docs/BOARD_SIMULATION_2026_07_17_EVENING.md
- Resolution: approved — contract test + terminology lint into principle suite (engineering task).

## [resolved] Charity Navigator fallback — implement live API checks?
- Raised: 2026-07-17 by founder (verify low-confidence links legally, without getting blocked)
- Principles touched: P3 (evidence-based links), P7 (disclosed source), legal/ToS compliance
- Data gathered: yes — CN ToS read 2026-07-17: prohibits automated extraction + republishing
- Simulation: docs/BOARD_SIMULATION_2026_07_17_EVENING.md
- Resolution: NO scraping ever (Phase 2b auto-activation disabled); API fallback retired (produced 1 link); official-API-with-consent is the only future path, founder-gated.

## [resolved] web_finder success rate — is 14% acceptable or does strategy need rework?
- Raised: 2026-07-17 from orchestrator test run (14 verified / 100 attempted)
- Principles touched: P3 (only verified sites go live), resource stewardship
- Data gathered: yes — misses are narrow candidate generation (acronym domains like vlt.org never guessed), not strict verification
- Simulation: docs/BOARD_SIMULATION_2026_07_17_EVENING.md
- Resolution: keep verification thresholds; add LLM candidate tier (Qwen 11437); re-measure.

## [resolved] Org profile edits don't appear on public page for hours (interconnection gap)
- Raised: 2026-07-18 by AI agent, during nonprofit-dashboard "interconnected spine" build
- Principles touched: P3 (evidence-based & honestly stated — org sees no timing info),
  P9 (decisions explainable), P4 (small orgs deserve equal, working tools)
- Data gathered: yes — confirmed via code read. PATCH /api/claim/profile writes
  mission/donate_confirmed directly to registry_enriched on the LIVE local DB
  (daanaa_api.py). The PUBLIC daanaa.org site is served by droplet_api.py from
  precompute static JSON files snapshotted at the last full deploy (nightly
  02:30 cron, or manual — can be hours to ~24h stale). Also confirmed
  merge_claims() in droplet_api.py reads from CLAIMS_DIR, which NO code in the
  repo ever writes to — it is dead code, silently a no-op today.
- Simulation: docs/BOARD_SIMULATION_2026_07_18_NONPROFIT_INTERCONNECTION.md
- Resolution: ship honest 24h-disclosure now (P3); defer live-push mechanism
  to a properly sandboxed follow-up (founder-affirmed: "for now just claimed"
  scope); retire dead CLAIMS_DIR/merge_claims code. See DECISIONS.md 2026-07-18.

## [resolved] Nightly full re-verification of all beta links vs tiered cadence
- Raised: 2026-07-18 by founder ("why are we reverifying links so quickly —
  use that capacity to find new ones")
- Principles touched: P3 (link freshness = trust), P5 (politeness — nightly
  HTTP checks against 18.6K nonprofit websites exceeds need)
- Data gathered: yes — all ~18.6K beta links get re-verified nightly at the
  9pm GPU-night start (~18 links/sec, ~17-50 min of the 12h window; 2,216
  distinct timestamps across the burst, so real checks, not a bulk stamp).
  Documented policy (reverify_stale_links.py) is a 90-DAY SLA — current
  behavior is ~90x stricter than policy. Capacity cost is modest but the
  nightly load on nonprofits' websites is unnecessary.
- Proposed: tiered cadence — first 7 days nightly (new links fail fast),
  then weekly to day 30, then the documented 90-day SLA. Freed window goes
  to Phase-2 discovery (2.03M orgs with no known website).
- Simulation: not needed — founder approved directly ("Update nightly ques")
- Resolution: tiered Phase 0 shipped 2026-07-18 — new/problem/never-checked
  links audited nightly; stable beta/claimed links weekly; 90-day SLA backstop
  unchanged. Verified against live DB: tonight audits 3,064 instead of 21,722
  (86% reduction). Freed hours flow to Phase 1/2 discovery automatically
  (cpu_night loop is sequential).

## [resolved] Five-item reliability & quality program (post-hoc gate review)
- Raised: 2026-07-18 by AI agent; founder caught that the list was presented
  WITHOUT a gate review ("did you go through this process before coming to me?")
- Principles touched: P6 (unalerted regressions = uncorrected mistakes), P9
  (untested backups = unexplainable resilience claims), P4 (golden set must not
  encode size bias; registries serve small orgs), P3/P5 (registry provenance +
  terms of use), P1 (public civic data)
- Data gathered: yes — item 1 validated by the 2026-07-18 unalerted 21s search
  regression; item 2 by zero restore rehearsals on record; item 4 by the
  2026-07-17 presence-only-test escape; item 5 is unscoped (that is the task)
- Simulation: docs/BOARD_SIMULATION_2026_07_18_IMPROVEMENT_PROGRAM.md
- Resolution: unanimous — execute 1 (SLO latency alert), 2 (restore drill),
  4 (golden set) autonomously now; 3 (founder phone QA) prep checklist, wait
  for founder; 5 (state registries) scoping ONLY, returns to board with
  per-state terms table before any ingestion. Process lesson recorded:
  proposals go through gates BEFORE reaching the founder.

## [resolved] V6 financial-context accuracy: dead component, wrong tier vocabulary, disjoint data pipeline
- Raised: 2026-08-08 by AI agent, mid-task — asked to bring the Research page's
  V6 data up to date; verifying that draft with Codex surfaced a live donor-facing
  defect much bigger than the original task.
- Principles touched: P3 (trust signals must be evidence-based and honestly
  stated — the org-detail "financial context" box was showing "not enough
  data" for every organization, and a separate false "percentile" claim was
  actually the retired v4 lamp score under an unrelated grouping), P6 (errors
  corrected quickly, documented not hidden), P4 (Broad Category orgs were
  silently excluded from Wallet's "emerging" filter due to the same
  wrong-vocabulary bug).
- Data gathered: yes.
  - Codex review #1 (codex exec, read-only): flagged the false percentile
    claim and the "Regional Context" tier's description claiming the
    opposite of what it does (drops region, compares nationally).
  - Direct SQL verification against scripts/merit_scorer_v6_0.py (the script
    that actually writes scoring_tier): confirmed scoring_tier and
    scoring_tier_v6_inference — two columns that look like variants of the
    same thing — agree on 58 of 2,056,834 rows. They are disjoint pipelines.
  - Codex review #2: confirmed the org-detail page's "central financial
    insight" component called a route that never existed in droplet_api.py
    (/api/organizations/:ein/financial-context), always 404ing; the intended
    replacement (FinancialContext.tsx) was dead code (imported nowhere) and
    itself checked scoring_tier against a third, unrelated vocabulary.
  - Codex review #3: caught that fixing the frontend alone was insufficient —
    droplet_api.py's get_v6_context() sourced peer-group size/description
    from the same disjoint pipeline, which could overwrite correct
    precomputed values even after the frontend fix.
- Simulation: none run — this was framed as a correction to methodology
  already board-approved 2026-07-25 (NTEE2 x 5-Band x Census Region), not a
  new methodology decision, so no docs/BOARD_SIMULATION_*.md was written.
  Founder explicitly asked whether this reasoning was sound ("does codex have
  any recommendations or have you run it by the board") before deploy;
  logging this entry is the founder-directed answer to that question.
- Resolution: founder approved via direct question-and-answer (not a board
  simulation) after the AI agent presented Codex's three review passes, the
  live-impact scope (every org page), and the SQL verification. Merged
  65a029dde13 (PR #6). Fixed: FinancialContext.tsx tier vocabulary,
  droplet_api.py get_v6_context() data source, WalletPage.tsx filter/sort,
  Methodology page + Research page tier descriptions, two deploy scripts'
  dead smoke tests. Deferred to TODOS.md: guided peer-group funnel + EIN
  peer-lookup features (Codex-reviewed for feasibility, not built this pass).
