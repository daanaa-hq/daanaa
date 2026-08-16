# 990 Narrative Enrichment — Architecture

Status: **Phase 3 implemented and dry-run validated** (2026-08-16). Synthesizes
`system-audit.md` + `xml-field-inventory.md` + `codex-reviews.md` into the
build plan. Revised same day per founder directive to maximize reuse of
existing tables/scripts over Codex Review A's original new-tables proposal —
see `DECISIONS.md` 2026-08-16 "990 Narrative Enrichment — reuse existing
tables/scripts instead of new ones."

---

## Summary

Most of the deterministic acquisition foundation (IRS batch discovery,
latest-filing selection, safe atomic writes) already exists in
`scripts/ops/fetch_irs_direct_filing.py` and
`refresh_recent_filings_batch.py`. This project extends that foundation with:

1. New deterministic extraction: Schedule O, grant purposes, structured Part
   III program records, 990-EZ mission/programs (currently 990-only).
2. **Reuse, not new storage**: Schedule O writes into the existing
   `extracted_programs` table (built for exactly this, never populated —
   new `schedule_o_source='irs_990_xml'` value alongside its original
   `'propublica_api'` design) and richer narrative text feeds `cause_tags`
   via the existing `enrich_cause_tags_mission.py` rules module, imported
   and reused as-is. No new tables shipped. `org_service_areas` is the one
   deliberate exception — see below.
3. GPU-derived semantic fields (mission summary, services, populations,
   geography, reported outcomes) computed only from the bounded deterministic
   excerpts above — never from a whole filing.
4. A separate, resumable producer job, run **after** the 04:15 financial
   refresh, not inline inside `write_filing()`.
5. No changes to `mission`, `org_service_areas`, FTS, or `org_embeddings` in
   v1 — new tables only, until the extraction is proven.

## Storage

```sql
CREATE TABLE irs_990_narrative_fields (
    ein             TEXT NOT NULL,
    tax_year        INTEGER NOT NULL,
    object_id       TEXT NOT NULL,
    field_name      TEXT NOT NULL,      -- 'mission_raw' | 'mission_summary' | 'services' | ...
    value_json       TEXT NOT NULL,      -- string or JSON array/object depending on field
    source_xpath    TEXT,               -- e.g. 'IRS990/ActivityOrMissionDesc'
    source_excerpt  TEXT,               -- exact raw text this value was derived from
    input_sha256    TEXT,               -- hash of source_excerpt, for GPU skip-caching
    parser_version  TEXT NOT NULL,
    model_version   TEXT,               -- NULL for deterministic fields
    prompt_version  TEXT,               -- NULL for deterministic fields
    created_at      TEXT NOT NULL,
    PRIMARY KEY (ein, tax_year, object_id, field_name)
);
CREATE INDEX idx_990nf_ein ON irs_990_narrative_fields(ein);

CREATE TABLE irs_990_programs (
    ein             TEXT NOT NULL,
    tax_year        INTEGER NOT NULL,
    object_id       TEXT NOT NULL,
    program_seq     INTEGER NOT NULL,   -- order within the filing
    program_name    TEXT,
    description     TEXT,
    expense_amt     REAL,
    revenue_amt     REAL,
    grant_amt       REAL,
    source_xpath    TEXT,
    parser_version  TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    PRIMARY KEY (ein, tax_year, object_id, program_seq)
);
CREATE INDEX idx_990prog_ein ON irs_990_programs(ein);
```

Rejected per Codex Review A: a generic evidence graph, a versioned JSON
schema file per field. Per-row evidence columns (`source_xpath`,
`source_excerpt`, `input_sha256`, `parser_version`) satisfy "evidence is
mandatory" without extra machinery.

**Current enrichment view**: since `(ein, tax_year, object_id)` always
identifies the row set for one org's latest processed filing, "current" is
just "the row set with the max `tax_year` for that EIN" — no separate
`_current` table needed at this scale; add one later only if query patterns
demand it (YAGNI, per CLAUDE.md).

## Parser extension (Phase 3) — implemented

Extended, not replaced, `scripts/ops/fetch_irs_direct_filing.py` (same file,
same functions, no parallel pipeline):

- `parse_990_xml()` gains: Schedule O explanation/line-reference pairs
  (filtered to `config/990_narrative_fields.yaml`'s allowlist), Schedule F/I
  grant purposes (junk-filtered; PF excluded — see yaml, mostly "SEE ATTACHED"
  in the sample), individual Part III program records via the *real*
  schema (a correction — the original fallback field name never matched any
  real 2026 filing), a second mission candidate (`MissionDesc`), and 990-EZ
  narrative support (`PrimaryExemptPurposeTxt` + `ProgramSrvcAccomplishmentGrp`,
  financials deliberately left unextracted pending EZ field-name verification).
- `write_filing()` extended in place — not a separate `write_narrative()` /
  separate producer script as Review A first proposed. One XML download, one
  parse, one write path, same transaction as the existing financial write.
  New writes: `extracted_programs` (Schedule O, `schedule_o_source='irs_990_xml'`),
  `cause_tags` (via imported `enrich_cause_tags_mission.apply_rules`/`merge_tags`,
  additive only), `programs_available` flip. All guarded the same way the
  existing mission write is guarded — never destroys better/more-recent data.
- Fixed: the mission guard now lets a **newer** `irs_990` filing replace an
  **older** one (was blocked once `mission_source='irs_990'` — Codex Review A
  finding).
- Fixed, found during this work (not previously exercised): the financial
  `UPDATE registry_enriched SET total_revenue = ?, ...` ran unconditionally
  even when `total_revenue` parsed as `None`, which would have silently
  written `NULL` over existing good financials once the tax-year guard
  passed. Now skipped when `total_revenue is None` — also what makes the
  990-EZ narrative-only path safe (EZ filings always have `total_revenue=None`
  by design).
- `iter_990_index_rows()`/`find_latest_filing()` gained an optional
  `return_types` parameter (default unchanged: `{'990'}`) so 990-EZ can be
  tested (`--include-ez` on the single-org CLI) without silently widening the
  nightly 04:15 cron's scope — that's a separate, reviewable decision.

**Validated** (24-filing dry run inside a rolled-back DB transaction — zero
production risk): 12/24 missions upgraded to real IRS text, 6/24 orgs gained
`cause_tags` (16 new tags total, manually verified against source text —
zero false positives found), 16/24 flipped `programs_available`, 6 Schedule O
rows written. Two concrete examples:

1. **Correction, not just upgrade**: a Denver-area org's AI-generated mission
   read "Delivers educational workshops and tutoring services to underserved
   students" — plausible-sounding, and wrong. Its real 990-EZ text: "TO RAISE
   FUNDS ANNUALLY TO SUPPORT STUDENTS IN FINANCIAL NEED AT DENVER ARCHIOCESE
   SCHOOLS TO HAVE THE OPPORTUNITY TO PARTICIPATE IN SPORTS." It's a Catholic
   school **sports scholarship fund**, not a tutoring org. Less polished
   prose, materially more accurate — exactly the P3 tradeoff this project
   exists to make, and the case for a separate GPU `mission_summary` layer
   (readable AND accurate) rather than smoothing the authoritative field itself.
2. **Real searchability signal a mission alone would miss**: a wildlife
   refuge's mission says nothing about job training or the arts. Its Schedule
   O does: "YOUNG SCIENTIST INTERNSHIPS AND HANDS-ON JOB TRAINING," an
   annual "ART IN THE WILD" community event, and a library outreach
   partnership. `cause_tags` correctly picked up `employment`, `job training`,
   `arts`, `arts education`, `education`, `literacy`, `library` — all
   traceable to literal program text, none invented. A donor searching "job
   training programs" would not have found this org before; now they will,
   through the existing FTS/embeddings pipeline, no new search code required.

Security posture (self-reviewed, Codex Review B/C in progress at time of
writing): `ET.fromstring` on untrusted IRS XML — stdlib `xml.etree
.ElementTree` disables external entity expansion by default since Python
3.7.1 (this repo runs 3.12); no `defusedxml` dependency added, matching
existing project convention (the pre-existing financials/mission parser used
the same approach). `unzip` shell-out extracts by a known, index-derived
`OBJECT_ID` filename — not user input.

## GPU enrichment (Phase 4) — implemented, 24-filing dry run validated

Founder granted an explicit 1-hour daytime exception to CLAUDE.md's
night-only GPU policy for this session (2026-08-16); code itself has no
day/night dependency, so it runs unattended overnight the same way.

- **Model**: Qwen3-30B-A3B-Instruct-2507-Q4_K_M via `llama-server`
  (`~/llama-vulkan/build/bin/llama-server`, port 11437, `--device Vulkan1
  -ngl 99 --ctx-size 16384 --jinja`). Had to launch with `-fit off` — the
  default auto-fit-to-device-memory step crashed silently on first attempt
  (no error, process just exited after "fitting params to device memory");
  the binary's own log suggested the flag. No daemon/launcher script for
  this specific model currently exists in the repo (only a health-check
  watchdog); started manually this session.
- **Code**: `scripts/enrichment/llm_extraction.py` — extended, not
  duplicated. That file already had the project's established local-LLM
  calling convention (`_call_llm()`, `response_format: json_schema`,
  temperature 0.1, fail-closed on any error) for scraped-website extraction;
  added `NARRATIVE_ENRICHMENT_SCHEMA`, `NARRATIVE_SYSTEM_PROMPT`,
  `build_narrative_input()`, `extract_narrative_enrichment()` to the same
  file, reusing `_call_llm()` as-is (widened its `max_input_chars`/
  `max_tokens` to optional parameters with unchanged defaults, so the
  existing website-extraction callers are untouched).
- **Input**: `build_narrative_input()` assembles Phase 3's already-extracted
  deterministic fields (mission text, Schedule O explanations, Part III
  program descriptions with expense amounts, grant purposes) into one
  labeled text block — never the whole XML file, never a network call to
  re-fetch anything.
- **Output schema — one real design finding**: the first schema version made
  `services`/`populations_served`/`geographies`/etc. optional. On a
  wildlife refuge with 12,444 chars of rich Schedule O content, the model
  returned only `mission_summary` + 4 empty arrays — not because the content
  wasn't there, but because a schema-constrained decoder can legally stop
  once required fields are satisfied. Confirmed via a raw non-schema call on
  the same input that hit `finish_reason=length` at 1200 tokens — the model
  could clearly generate more, the optional schema just let it not. Fix:
  made every field required (empty array is still a valid, honest answer,
  not a forced guess) — same input then correctly returned 7 services, 5
  geographies, 4 quantified `reported_outcomes`, 4 other facts, all
  manually verified traceable to source text.
- **Grounding**: enforced by (1) bounded input — the model only ever sees
  Phase 3's already-deterministic excerpts, never a whole filing or outside
  knowledge, (2) `NARRATIVE_SYSTEM_PROMPT`'s explicit rules (use only
  supplied text; never infer a population/geography from the org's name;
  never turn a stated goal into a claimed accomplishment; honest-empty over
  plausible-invented), (3) a model-self-assessed `grounded` boolean field,
  and (4) manual spot-check against source text (done for every example in
  this doc). `reported_outcomes` is structurally separate from
  `other_useful_facts` and always organization-reported, never verified —
  matches Stewardship P3/P5/P10.
- **Skip-cache**: implemented and tested (`gpu_enrichment.py`,
  `already_cached()`) — keyed on `(ein, tax_year, object_id)` +
  `input_sha256` + `model_version` + `prompt_version`. Verified: identical
  second call resolves in 0.000s with zero GPU cost; a hash/version mismatch
  correctly falls through to a real call.
- **Storage**: `migrations/024_irs_990_narrative_gpu_summary.sql` — **written
  and schema-tested in a rolled-back transaction, NOT applied to the live
  DB**. Requires founder approval per CLAUDE.md's schema-change gate. New
  table, deliberately separate from `registry_enriched`/`mission`/
  `cause_tags` — AI-derived summarization must stay visibly distinguishable
  from Phase 3's deterministic layer (Stewardship P3/P10), and must never
  reach `cause_tags` specifically, since Codex Review B/C confirmed that
  column feeds search-relevance ranking and needs to stay rule-derived to
  hold the same evidentiary bar.

### Benchmark, initial pass (24-filing dry run, before Codex Review D)

| Metric | Result |
|---|---|
| Filings with extractable input | 16/24 (8 were 990-PF, out of scope) |
| Failures/exceptions | 0 |
| Avg latency | 1.2s/filing (sequential, single request) |
| `grounded: true` | 14/16 |
| `services` / `geographies` / `populations_served` / `reported_outcomes` / `other_useful_facts` filled | 15 / 7 / 1 / 5 / 4 (of 16) |
| `new_or_changed_programs` filled | 0/16 — checked afterward: none of the 24 sampled filings actually had `significant_new_program`/`significant_change` set true, so this was correct/honest, not a gap |

### Codex Review D — findings and fixes (2026-08-16)

Full record in `codex-reviews.md`. Summary of what changed:

- **Evidence-quote verification added** — the single biggest finding.
  `reported_outcomes` items now require a verbatim `evidence_quote`; a new
  `_verify_reported_outcomes()` mechanically checks (whitespace/case
  normalized) that the quote actually appears in the bounded input before
  the item is kept — anything that doesn't match is dropped and logged, not
  stored. `grounded` was reframed in its own schema description as a
  diagnostic self-assessment, not independent verification or a publication
  gate (it's the same model self-certifying its own output).
- **Program expense amounts removed from GPU input** — included with no
  output field using them, risking implicit "expense size = importance"
  inference. Descriptions only now.
- **`significant_new_program`/`significant_change` now persisted as their
  own deterministic columns** (migration 024), not just an LLM prompt hint —
  their provenance is the filing itself, independent of whether the model
  successfully narrates what changed.
- **Fuller model-artifact identifier** for cache provenance
  (`Qwen3-30B-A3B-Instruct-2507-Q4_K_M`, not just the API-facing model-name
  string, which doesn't distinguish a swapped gguf file served under the
  same name).
- **`_call_llm()`'s error handling widened** — the original except clause
  only caught `KeyError`/`JSONDecodeError`; a non-JSON response body
  (`ValueError`), empty/absent `choices` (`IndexError`/`TypeError`) weren't
  covered. Shared function, so this also hardens the original
  website-extraction callers.
- **Local schema-shape validation added** (`_validate_shape()`) — confirms
  every required key is present and array fields are actually lists before
  the result is accepted, beyond just `json.loads()` succeeding.

**Re-benchmarked after fixes** (same 24 filings, migration applied+rolled-back
correctly this time — see production near-miss below): 16/16 written, 0
failed. Evidence verification dropped 3 of 11 model-generated
`reported_outcomes` (paraphrased rather than quoted verbatim — e.g. the
model wrote "$300,0..." where the source said "300,000" without a dollar
sign) — 8 outcomes survived verification across the 16 filings. This is the
verification working as designed: it trades recall for precision (some
true-but-paraphrased claims get dropped) rather than risk storing an
unverifiable one, which is the correct direction for an accuracy-sensitive
donor-facing claim.

**Not fixed, deliberately deferred**: Codex's batching recommendation
(4-6 concurrent requests with bounded-concurrency + chunked commits) — real
engineering work with real concurrency-bug risk against a single-writer
SQLite target; sequential is adequate for the sample size validated so far
and should be built carefully before the 1,000-filing gate, not rushed
inside this session. The `gpu_night.sh` vs. CLAUDE.md GPU-window discrepancy
Codex found (9pm-9am vs. documented 10pm-6am) is pre-existing and unrelated
to this project — flagged in `DECISIONS.md`, not silently resolved one way
without knowing which is authoritative.

### Production near-miss during testing (self-caught, corrected same session)

Testing migration 024 used `db.executescript()` inside a `BEGIN`/`ROLLBACK`
block, assuming the same rollback safety used throughout this session.
`executescript()` doesn't honor that — it implicitly commits any pending
transaction and its own DDL isn't covered by the later `ROLLBACK`. The table
was created for real in production (schema-change without the approval
CLAUDE.md requires), caught when a second test run failed on a missing
column that should have been rolled back. **0 rows had been written** —
caught before any data existed, corrected via `DROP TABLE`, verified clean.
Full root-cause writeup: `LESSONS.md` 2026-08-16. Test harness fixed to
`execute()` each statement individually (which does honor the transaction)
and to explicitly verify rollback by querying `sqlite_master` afterward,
not just trust it.

### Open items before production wiring

1. **Migration 024 needs founder approval** before any real
   (non-rolled-back) write — everything in this section was validated in a
   transaction that's confirmed to actually roll back now.
2. Batching/concurrency for the 1,000-filing gate (see above) — not started.
3. `gpu_night.sh` / CLAUDE.md GPU-window reconciliation — flagged, not this
   project's call to resolve.

## Scheduling / concurrency

- Runs as its own cron entry, scheduled **after** 04:15 (e.g. 05:30, after
  the direct-filing batch job and before the 05:00 Sunday website-expansion
  job on the days they'd overlap) — never concurrent with the financial
  refresh, per Codex Review A's SQLite single-writer concern.
- `busy_timeout` + retry/backoff + small per-filing commits (not one
  transaction per batch), unlike the existing batch job's per-batch
  transaction — narrative writes shouldn't hold a long lock.
- GPU derivation checks `precompute_similar_orgs` / embedding-build job state
  before running a large batch (simple PID/lock-file check against
  `daemon_state` table conventions, per `docs/DAEMON_HEALTH_STANDARD.md` —
  don't grep logs, read published state).

## Search / org page integration (Phases 7-8, deferred until extraction is validated)

- **v1 ships no search or ranking change.** Storage only:
  `extracted_programs` (Schedule O), `cause_tags` (deterministic rule-derived
  tags, Phase 3), `irs_990_narrative_gpu_summary` (GPU-derived fields, Phase
  4 — migration 024 applied 2026-08-16, table live, 0 rows until a real run).
- When validated: extend `org_embeddings`' document composition (mission +
  services + populations + geography + program names, per the brief's
  compact-document example) and selectively re-embed changed EINs — do not
  introduce FAISS (confirmed dead in the live API path).
- Org page: new "What they do" section reading from
  `irs_990_narrative_gpu_summary` (+ `extracted_programs` for raw Schedule O),
  clearly labeled organization-reported with a filing-year citation (matches
  existing E6 compensation-disclosure precedent — `tax_prd_yr` shown
  alongside 990 compensation data per Stewardship Compliance Log 2026-07-01).
- **Coordinate, don't duplicate, with the unshipped small-org-clarity
  Phase 3** (`leadership_info`/`service_scope`/`org_stability_signal`/
  `mission_attribution` API fields, committed but frontend never shipped —
  see `system-audit.md` §7). Both are "At a Glance"-style structured sections
  on the same page; propose one combined frontend pass when Phase 7 starts
  rather than shipping two separate sections that compete for the same space.

### Required framing before any of this reaches a live page (blocking Phase 7)

Checked against the Daanaa Charter (`institution/DAANAA-CHARTER.md`) and
STEWARDSHIP.md directly, not just in the abstract — two concrete risks found
in this session's own real output, not hypothetical:

1. **Charter #7** ("we say 'we don't know enough,' never 'they failed'"):
   one of the 24 real sampled filings — a small org whose Schedule O read
   *"Supported a local drug take-back program; limited activity due to
   health issues"* — is a real, sympathetic, honest self-report. Shown
   without care next to an org whose Schedule O ran 5,700 characters, it
   reads as *this org didn't do much*, even though it's the org's own words
   offered in good faith, not a Daanaa judgment. **Rule for Phase 7**: a
   thin or absent narrative section renders as "Limited public filing detail
   available" or equivalent — never an empty section, a placeholder that
   implies absence-of-effort, or a visual contrast that reads as a score.
2. **Stewardship P4** (small-org fairness): narrative richness in a 990
   filing correlates with the org having staff/time to write a detailed
   Schedule O, not with the quality of the org's work — a data artifact, not
   a merit signal. **Rule for Phase 7**: no UI treatment (badge, checkmark,
   "complete profile" styling, sort order) may treat narrative-field
   completeness as a positive signal. If completeness needs to be visible at
   all, it's descriptive ("from the org's [year] filing"), never evaluative.
3. **Stewardship P10** (AI is a tool, not an authority): every
   `irs_990_narrative_gpu_summary` field shown on a page needs an explicit,
   literal attribution — "Daanaa's summary of this organization's own
   filing" or equivalent — visually distinct from `extracted_programs`'
   deterministic Schedule O text (which is the org's own words verbatim,
   a stronger evidentiary tier) and from `mission` (also the org's own
   words, IRS-sourced, Phase 3). Three tiers, three different confidence
   levels, must not be visually flattened into one "About this org" block
   that reads as equally authoritative throughout. `reported_outcomes`
   specifically needs "as reported by the organization, not independently
   verified" on or immediately next to every instance where it's shown —
   not just implied by field naming in the database.

These three are now explicit go/no-go criteria for Phase 7's design pass,
not general reminders — Phase 7 should not ship without them designed in,
regardless of how good the underlying extraction is.

## What's explicitly deferred

- PDF/OCR fallback (MarkItDown) — only if XML coverage measurement (Phase 6)
  shows a real gap.
- 10,000-filing scale gate — background op check post-ship.
- Search/ranking integration — after extraction accuracy is validated on the
  1,000-filing dry run.
- `org_service_areas` — never written to by this project; self-reported
  geography stays self-reported.
