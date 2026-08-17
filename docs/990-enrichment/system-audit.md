# 990 Narrative Enrichment — System Audit (Phase 0)

Date: 2026-08-16
Branch: `feature/990-narrative-enrichment`
Author: Claude Code (Phase 0 inspection, pre-architecture)

Read-only inspection. No production changes made. Purpose: find what already
exists so the narrative-enrichment build extends it instead of duplicating it.

---

## 1. Headline finding: the deterministic foundation was built TODAY

`scripts/ops/fetch_irs_direct_filing.py` (committed 2026-08-16, commit
`e7741ae4aa5`) already implements most of Phase 1–3 of this project's
deterministic path:

- **Acquisition**: pulls IRS's own monthly submission index
  (`apps.irs.gov/pub/epostcard/990/xml/{year}/index_{year}.csv`), finds an
  EIN's latest `OBJECT_ID` + `XML_BATCH_ID` by `TAX_PERIOD`, downloads the one
  monthly batch ZIP (400–700MB, ~50-70K filings/batch) that contains it.
- **`parse_990_xml()`**: streaming ElementTree parse of one filing —
  financials (`CYTotalRevenueAmt`, `TotalAssetsEOYAmt`), Part IX functional
  expense breakdown, AND (added same day) mission text: prefers Part I
  `ActivityOrMissionDesc` (short explicit statement), falls back to Part III
  `ProgramServiceAccomplishmentGrp/DescriptionProgramServiceAccomTxt`
  (program-service accomplishment narrative) joined with blank lines.
- **`write_filing()`**: writes to 3 tables in one transaction
  (`org_revenue_history`, `irs_990_functional_expense_filings`,
  `registry_enriched`), with:
  - **never-downgrade guard** on financials: `UPDATE ... WHERE latest_tax_year
    IS NULL OR latest_tax_year < ?` — a newer filing only overwrites an older
    one.
  - **reconciliation check**: Part IX B+C+D must equal A within $1 or the
    expense breakdown is marked `rejected` (not applied), while revenue/assets
    still get written. This is exactly this project's "never replace good data
    with a bad extraction" principle, already implemented for the financial
    side.
  - **mission precedence guard**, copied verbatim from
    `scripts/enrichment/ingest_990_missions.py`'s existing rule: only writes
    `mission` when current `mission_source IS NULL OR LIKE 'ai_%' OR mission
    IS NULL OR mission = ''`. Never overwrites `claimed`, `nonprofit_supplied`,
    or a prior `irs_990` mission. Tags `mission_source='irs_990'`,
    `mission_last_verified=<tax_year>`.
- **`scripts/ops/refresh_recent_filings_batch.py`** (also 2026-08-16, 380
  lines): batch-mode sibling — downloads each unprocessed monthly IRS ZIP
  once, extracts every filing whose EIN is in `registry_enriched` (not the
  whole batch), delegates to the same `write_filing()`. Runs nightly via cron
  **04:15 daily**, state tracked in
  `data/ops_state/irs_direct_recent_filings_batches.json`. This closes gt990's
  ~2-3 month bulk-index lag. Verified end-to-end on live June 2026 batch
  (18,806/18,806 written) per project memory.

**Implication for this project**: do not rebuild IRS acquisition, latest-filing
selection, batch-vs-single-org strategy, or the mission-precedence/never-
downgrade write pattern. Extend `parse_990_xml()` and `write_filing()` in
place — add Program Service Accomplishments as a *separate* structured field
(currently only used as a mission fallback, not stored on its own), Schedule O,
grant purposes, and the GPU-derived semantic fields (services, populations,
geography, reported outcomes). The precedent for "how do we safely replace a
production field only when the new extraction is better" is proven code, not
a design question.

`scripts/enrichment/ingest_990_missions.py` is the earlier, NCCS-bulk-CSV-based
version of the same mission-precedence idea (reads
`data/nccs/F9-P01-T00-SUMMARY-*.CSV`, column `F9_01_ACT_GVRN_ACT_MISSION`,
same precedence rules, `PROTECTED_SOURCES = (claimed, nonprofit_supplied,
lucido)`). It's a different acquisition path (NCCS extract vs. direct IRS XML)
feeding the same target column — worth knowing both exist so the new pipeline
doesn't race either one on write order for the same EIN in the same run.

---

## 2. Existing 990-adjacent tables — two are built but empty

| Table | Status | Notes |
|---|---|---|
| `registry_enriched.mission` / `.mission_source` / `.mission_confidence` / `.mission_last_verified` / `.programs_available` | **Live, populated** | Primary target column. `mission_source` values in use: `ai_generated`, `ai_ntee`, `irs_990`, `claimed`, `nonprofit_supplied`, `lucido`, scraped. 1.58M orgs currently `ai_*` (candidates for `irs_990` upgrade). |
| `irs_990_functional_expense_filings` | **Live, populated** | Part IX only, per-filing, keyed `(EIN, tax_year, object_id)`. Has `validation_status`, `parser_version`, `reconciles` — the exact provenance pattern this project should reuse for narrative fields. |
| `org_revenue_history` | **Live, populated** | Financials only, keyed `(EIN, tax_year)`, `source` column already distinguishes `gt990_index` vs `irs_direct`. |
| `extracted_programs` | **Built, EMPTY (0 rows)** | `(EIN, schedule_o_text, schedule_o_year, schedule_o_source DEFAULT 'propublica_api', extraction_confidence, extracted_at)`, PK `(EIN, schedule_o_year)`. Designed for Schedule O narrative from the ProPublica API path — never wired up or populated. Reusable shape for Schedule O once we're pulling it from XML directly instead of ProPublica. |
| `org_service_areas` | **Built, essentially unused (1 row)** | `(id, ein, area_type DEFAULT 'local', area_values JSON, updated_at)`, `UNIQUE(ein)`. Reusable shape for the geography output field — `area_type`/`area_values` already anticipates something like `["Houston", "Harris County"]`. |

Two tables (`extracted_programs`, `org_service_areas`) were already designed
for pieces of this project's exact scope and never populated. Evaluate reusing
their shape (or migrating them) before creating new tables — check with Codex
in Review A whether their schema still fits, since they predate this project's
requirements (evidence/provenance fields, versioning) and may need columns
added rather than wholesale replacement.

No table currently exists for: mission_summary (AI-derived, distinct from
`mission` raw), services, populations_served, programs (structured,
Schedule-O-sourced or Part III–sourced with evidence), reported_outcomes,
new_or_changed_programs, other_useful_facts, or per-field evidence/source
snippets. These are new.

---

## 3. IRS/990 data source inventory (cron-scheduled, live)

| Source | Script | Cadence | What it covers |
|---|---|---|---|
| IRS BMF (identity/classification/revocation) | `scripts/migrations/refresh_irs_data.sh` | Mondays 02:00 | New orgs, NTEE, status |
| IRS revocation list | `scripts/ops/sync_irs_revocations.py` | Daily 03:00 | Full sync, marks revoked inactive |
| gt990 e-file index (bulk, public S3) | `scripts/cron_refresh_gt990.sh` → `scripts/ops/refresh_gt990_index.sh` / `refresh_stale_orgs_from_gt990.py` | Sundays 01:00 | Bulk filing index; ~2-3mo rebuild lag |
| IRS direct-filing recent batch (this project's foundation) | `scripts/ops/refresh_recent_filings_batch.py --apply` | **Daily 04:15** | Closes gt990's lag; financials + mission text already |
| 990-attested website expansion | `scripts/discovery/expand_990_coverage.py --workers 12` | Sundays 05:00 | Extracts org-attested websites from fresh filings |

The IRS's own S3 bucket (`s3://irs-form-990`) was discontinued Dec 31 2021 —
confirmed dead, do not target it. `apps.irs.gov/pub/epostcard/990/xml` (direct
publishing, still active, updates monthly) is the live source the 04:15 job
already uses.

Local raw archive present: `data/990_xml/`, `data/990n_data.zip`,
`data/cache/gt990_index_2026-03-20.csv`, `data/cache/gt990_latest.csv`,
`data/irs_soi/*.zip` (SOI extracts, different product from the XML filings).

---

## 4. Search / embeddings infrastructure

- **FTS5**: `scripts/search/build_fts_index.py` rebuilds `org_fts` virtual
  table; `search_index_delta.py` for incremental adds. Table lives in
  `merit_registry.db`, checked once at API startup (`_fts_available`, cached).
- **Semantic**: `scripts/enrichment/embeddings/build_org_embeddings.py` builds
  `org_embeddings` (mxbai-embed-large, ~546K vectors) loaded into RAM at API
  startup (`--preload`, CoW across gunicorn workers).
- **Reranking / intent**: `scripts/search/search_semantic_reranker.py`,
  `search_intent_classifier.py`, `ntee_synonyms.py` — an existing layer this
  project should feed into (compact enrichment documents), not replace.
- A parallel FAISS path also exists (`build_faiss_index.py`,
  `build_faiss_docs_index.py`, `rebuild_faiss_with_directmap.py`) — needs a
  Codex-reviewed decision on whether new enrichment embeds go through the
  FTS5+org_embeddings path (API's live path) or FAISS (unclear if live);
  default to the API's live path unless told otherwise.

---

## 5. V6 peer-grouping (do not touch, per project brief)

- Scorer: **`scripts/scoring/daanaa_scorer.py`** — CLAUDE.md says
  `scripts/daanaa_scorer.py`; that path is stale, the real file lives under
  `scripts/scoring/`. (Doc drift, flagged for a separate fix — not touched
  here, out of this project's scope.)
- Peer-group alignment: `scripts/scoring/peer_group.py` (153 lines) — shared
  module for aligning "Similar Organizations" to an org's own `scoring_tier`,
  per the 2026-08-16 founder directive (see project memory
  `project_peer_group_drift_founder_decision_2026_08_16`).
- **Currently running**: `python3 -m scripts.core.precompute_similar_orgs
  --workers 2` (3 processes, ~34 min elapsed at inspection time) — this is the
  Pass 2 parallelization from the most recent commit
  (`46cecce83af`), actively regenerating similar-orgs precompute using
  `peer_group.py`. This project's narrative enrichment is conceptually
  downstream of this (Section "V6 peer context" in the brief: keep financial
  peer-context and narrative extraction separate, use narrative only to add
  color/context around already-computed peer groups). No overlap requiring
  coordination, but worth knowing this job is mid-run.

---

## 6. Hardware / local inference

| Component | Finding |
|---|---|
| CPU | 16 cores (`nproc`) |
| RAM | 30Gi total. **At inspection time: 22Gi used, 478Mi free, swap 7.9/8Gi used** — system is under real memory pressure right now, driven by `precompute_similar_orgs --workers 2` (3 processes × ~4.7GB RSS each). Not a blocker, but batch-inference benchmarking (Phase 4) should wait for this job to finish or explicitly account for the headroom it's using. |
| GPU | AMD, 2 devices visible under `rocm-smi` (one is likely the iGPU/reporting artifact — needs confirmation, not the R9700 alone). ROCm SMI responds; `rocm-smi` shows Device 0 at 100% GPU%, Device 1 at 99% GPU% — high utilization even with the 30B model server (port 11437) not currently running, so this is more likely non-inference load; needs a clean re-check when the box is idle. |
| Inference runtimes present | `llama-server` (Vulkan build at `~/llama-vulkan/build/bin/llama-server`) currently serving only the embedding model on **port 11436** (mxbai-embed-large-v1, `-ngl 99 --device Vulkan1 --ctx-size 16384 -np 16 --embeddings`). Port 11437 (Qwen3-30B-A3B-Instruct, the mission/narrative generation model per CLAUDE.md) is **not currently running** — needs to be started for Phase 4 benchmarking, or launched on demand per job. `llama-swap` present (`~/warehouse/llama-swap`), and `ollama` running as a system service (port 11434, fallback per CLAUDE.md). `watchdog_llama.sh` running to keep llama-server alive. |
| Codex CLI | `/home/akbar/.local/bin/codex`, version `codex-cli 0.147.0` — available for Review A onward, will invoke via `codex exec -s read-only` per session convention (workspace-write is broken in this sandbox; Claude applies Codex's reviewed suggestions directly). |

**Action before Phase 4 benchmarking**: confirm GPU idle state and whether
port 11437 needs an explicit start command (per CLAUDE.md, GPU is
"night-only, 10pm–6am" for heat management — Phase 4 benchmarking with the
30B model should be scheduled inside that window or an explicit exception
requested, not run ad hoc during the day).

---

## 7. Frontend / org page (Phase 7 target)

- Org detail page: `frontend/src/pages/OrganizationDetail.tsx` — "giving-first"
  layout per `REPO_MAP.md`. Confirmed existence; full read-through deferred
  to Phase 7 (don't redesign the page, only inspect its existing UX at that
  point per project brief).
- Existing "At a Glance" precedent: the `feedback_small-org-clarity` work
  (prior checkpoint, 2026-08-09) already added 4 API fields
  (`leadership_info`, `service_scope`, `org_stability_signal`,
  `mission_attribution`) intended for an "At a Glance" section on this exact
  page, but the frontend half was never shipped (Phase 3 of that project was
  still pending when this session picked up). **This project's Phase 7 should
  check whether that unshipped work overlaps or should be done together** —
  both are adding structured, evidence-labeled narrative sections to the same
  page. Flagging for Codex Review A rather than deciding unilaterally.

---

## 8. Governance / conventions confirmed applicable

- Mission field already carries a `mission_source` provenance column with a
  documented precedence order — this project's "evidence is mandatory" and
  "never replace good data with bad extraction" principles are not new asks,
  they're the existing convention, now extended to more fields.
- Stewardship P3 (evidence-based), P5 (no shaming/weaponized transparency),
  P10 (AI is a tool, not an authority) are directly implicated by "reported
  outcomes must be labeled organization-reported, not independently verified"
  — matches this project's Phase 7 language requirements exactly.
- `docs/990-enrichment/` did not exist before this audit; created fresh.

---

## Open questions for Codex Review A

1. `extracted_programs` / `org_service_areas` — reuse existing empty tables
   (migrate schema) or design fresh tables? They predate this project's
   evidence/provenance requirements.
2. FAISS vs. FTS5+org_embeddings — which is the actually-live semantic search
   path new enrichment documents should feed?
3. Should Program Service Accomplishments be pulled out of the mission
   fallback in `parse_990_xml()` into its own structured field now (low-cost,
   the parser already visits that XML node), even before GPU-derived summary
   work begins?
4. Small-org-clarity's unshipped Phase 3 frontend — same page, same "At a
   Glance" concept — coordinate or keep separate?
5. Lowest-cost way to extend `write_filing()`'s pattern to new narrative
   fields without duplicating its transaction/guard logic.
