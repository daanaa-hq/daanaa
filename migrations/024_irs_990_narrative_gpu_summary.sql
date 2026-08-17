-- Migration 024: irs_990_narrative_gpu_summary
-- Date: 2026-08-16
-- Part of docs/990-enrichment/ (990 Narrative Enrichment project, Phase 4).
-- NOT YET APPLIED to merit_registry.db -- requires founder approval per
-- CLAUDE.md's schema/migration approval gate. Written and validated in a
-- rolled-back DB transaction during this session; this file is the
-- reviewable artifact for that approval.
--
-- One additive, standalone table. Does not touch registry_enriched's
-- existing columns or any other live table.
--
-- Why a genuinely new table here, unlike Phase 3 (which reused
-- extracted_programs + cause_tags per DECISIONS.md 2026-08-16 "reuse
-- existing tables"): this stores AI-DERIVED content (mission_summary,
-- services, populations_served, geographies, reported_outcomes,
-- new_or_changed_programs, other_useful_facts) from the local Qwen3-30B
-- model, which is categorically different from Phase 3's deterministic
-- XML extraction and rule-based cause_tags. Nothing in the existing schema
-- fits AI-summarized content with a "grounded" self-assessment flag and
-- model/prompt versioning -- Codex Review A confirmed this is genuinely new
-- work, not a reuse candidate.
--
-- Deliberately NOT written into registry_enriched, mission, or cause_tags:
-- per Stewardship P3/P10, AI-derived summarization must stay distinguishable
-- from the deterministic mission field and from cause_tags (which, per
-- Codex Review B/C, feeds search-relevance ranking and must stay
-- rule-derived/deterministic, not raw LLM output, to hold the same
-- evidentiary bar). This table is a separate, clearly-labeled layer,
-- consumed by the org page (Phase 7) with explicit "Daanaa's summary of
-- this organization's own filing" attribution -- never presented as
-- verified fact.

CREATE TABLE IF NOT EXISTS irs_990_narrative_gpu_summary (
    ein                       TEXT NOT NULL,
    tax_year                  INTEGER NOT NULL,
    object_id                 TEXT NOT NULL,
    -- Deterministic pass-through, NOT AI-derived (Codex Review D, 2026-08-16):
    -- parse_990_xml() already extracts these as real filing booleans
    -- (SignificantNewProgramSrvcInd/SignificantChangeInd) but Phase 3 never
    -- persisted them anywhere. Stored here at the same per-filing grain as
    -- the GPU summary for convenience, but their provenance is the XML
    -- filing itself, not the model -- established the fact that something
    -- changed; new_or_changed_programs_json below is the model's (unverified)
    -- attempt to describe WHAT, when the text identifies it.
    significant_new_program   INTEGER,
    significant_change        INTEGER,
    mission_summary           TEXT,
    services_json             TEXT,       -- JSON array
    populations_served_json   TEXT,       -- JSON array
    geographies_json          TEXT,       -- JSON array
    reported_outcomes_json    TEXT,       -- JSON array of {claim, value, evidence_quote}, organization-reported only, evidence-quote-verified before storage
    new_or_changed_programs_json TEXT,    -- JSON array
    other_useful_facts_json   TEXT,       -- JSON array
    grounded                  INTEGER,    -- model's own self-assessment; diagnostic signal only, not independent verification (Codex Review D)
    input_sha256              TEXT NOT NULL,  -- hash of the bounded input text -- skip-cache key
    model_version              TEXT NOT NULL,  -- specific quantized artifact, e.g. 'Qwen3-30B-A3B-Instruct-2507-Q4_K_M'
    prompt_version              TEXT NOT NULL,  -- bump when NARRATIVE_SYSTEM_PROMPT or schema changes
    created_at                 TEXT NOT NULL,
    PRIMARY KEY (ein, tax_year, object_id)
);
CREATE INDEX IF NOT EXISTS idx_990_gpu_summary_ein ON irs_990_narrative_gpu_summary(ein);
CREATE INDEX IF NOT EXISTS idx_990_gpu_summary_hash ON irs_990_narrative_gpu_summary(input_sha256, model_version, prompt_version);

-- Rollback: DROP TABLE irs_990_narrative_gpu_summary; DROP INDEX idx_990_gpu_summary_ein; DROP INDEX idx_990_gpu_summary_hash;
-- No data loss to any live-served field -- this table has no existing readers.
