# 990 Narrative Enrichment — Architecture

Status: draft, post Codex Review A. Synthesizes `system-audit.md` +
`xml-field-inventory.md` + `codex-reviews.md` into the build plan.

---

## Summary

Most of the deterministic acquisition foundation (IRS batch discovery,
latest-filing selection, safe atomic writes) already exists in
`scripts/ops/fetch_irs_direct_filing.py` and
`refresh_recent_filings_batch.py`. This project extends that foundation with:

1. New deterministic extraction: Schedule O, grant purposes, structured Part
   III program records, 990-EZ mission/programs (currently 990-only).
2. A new, narrowly-scoped storage layer — not a reuse of `extracted_programs`
   or `org_service_areas` (both wrong-shaped or actively used for ranking;
   see Codex Review A).
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

## Parser extension (Phase 3)

Extend, don't replace, `scripts/ops/fetch_irs_direct_filing.py`:

- `parse_990_xml()` gains: Schedule O explanation/line-reference pairs
  (filtered to a line-reference allowlist — see `config/990_narrative_fields.yaml`),
  Schedule F/I/PF grant purposes (junk-filtered), and individual Part III
  program records (not just joined into the mission fallback).
- New function `parse_990ez_xml()` (or a `form_type` branch in the same
  function) for 990-EZ's `PrimaryExemptPurposeTxt` +
  `ProgramSrvcAccomplishmentGrp`. 990-PF has no mission-equivalent field —
  only grant purposes/recipients apply there.
- New `write_narrative(db, ein, filing, narrative_data, now)` function,
  separate from `write_filing()`, called by a **new** producer script
  (`scripts/enrichment/narrative_990/extract_narrative_batch.py`), not
  inline in the nightly financial job. Reuses the same batch-download/extract
  machinery (`iter_990_index_rows`, `batch_zip_url`) but writes to the new
  tables only.
- Fix flagged in Review A: the mission guard should let a **newer** `irs_990`
  filing replace an **older** `irs_990` mission (currently blocked once
  `mission_source='irs_990'` is set). Small, isolated fix — add tax-year
  comparison to the guard.
- Security hardening (Phase 3 Codex Review C target): `ET.fromstring` on
  untrusted IRS XML — confirm `defusedxml` or an equivalent XXE-safe
  configuration is used (Python's stdlib `xml.etree.ElementTree` disables
  external entity expansion by default since 3.x, but confirm and add a test);
  `unzip` shell-out needs a filename allowlist check (target XML name is
  known ahead of time, but confirm no path traversal via crafted `OBJECT_ID`).

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
