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

## GPU enrichment (Phase 4)

- Model: Qwen3-30B-A3B-Instruct via existing `llama-server` (port 11437,
  currently not running — starts on demand). Per CLAUDE.md, GPU is
  night-only (10pm-6am Central) for heat management; batch benchmarking and
  production runs scheduled inside that window unless the founder grants an
  explicit exception.
- Input: bounded, concatenated deterministic excerpts for one filing (mission
  candidates + Schedule O explanations + Part III program descriptions +
  grant purposes) — never the whole XML file.
- Output: strict JSON per the schema in the original project brief
  (`mission_summary`, `services[]`, `populations_served[]`, `geographies[]`,
  `programs[]` with `source_evidence_ids`, `reported_outcomes[]` explicitly
  marked `organization_reported: true`, `new_or_changed_programs[]`,
  `other_useful_facts[]`). Every derived claim must carry
  `source_evidence_ids` pointing at `irs_990_narrative_fields`/
  `irs_990_programs` rows; omit rather than guess when evidence is absent.
- Skip-cache: `input_sha256` (hash of the bounded excerpt bundle) +
  `model_version` + `prompt_version` — reuse the row if all three match a
  prior run, per Codex Review A ("GPU input hash caching, keyed by normalized
  bounded input + prompt/schema/model version").
- Gate: 15-30 filing manual review (already sampled — Phase 1 output) → fix
  obvious failure classes → 1,000-filing dry run for throughput/reliability
  (Codex-recommended; standalone 100-filing gate cut unless the first review
  surfaces something worth isolating) → 10,000-filing scale test deferred to
  a background operational check post-ship, not a pre-ship gate.

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

- **v1 ships no search or ranking change.** New tables only.
- When validated: extend `org_embeddings`' document composition (mission +
  services + populations + geography + program names, per the brief's
  compact-document example) and selectively re-embed changed EINs — do not
  introduce FAISS (confirmed dead in the live API path).
- Org page: new "What they do" section reading from
  `irs_990_narrative_fields`, clearly labeled organization-reported with a
  filing-year citation (matches existing E6 compensation-disclosure
  precedent — `tax_prd_yr` shown alongside 990 compensation data per
  Stewardship Compliance Log 2026-07-01).
- **Coordinate, don't duplicate, with the unshipped small-org-clarity
  Phase 3** (`leadership_info`/`service_scope`/`org_stability_signal`/
  `mission_attribution` API fields, committed but frontend never shipped —
  see `system-audit.md` §7). Both are "At a Glance"-style structured sections
  on the same page; propose one combined frontend pass when Phase 7 starts
  rather than shipping two separate sections that compete for the same space.

## What's explicitly deferred

- PDF/OCR fallback (MarkItDown) — only if XML coverage measurement (Phase 6)
  shows a real gap.
- 10,000-filing scale gate — background op check post-ship.
- Search/ranking integration — after extraction accuracy is validated on the
  1,000-filing dry run.
- `org_service_areas` — never written to by this project; self-reported
  geography stays self-reported.
