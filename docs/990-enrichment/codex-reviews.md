# Codex Reviews — 990 Narrative Enrichment

Independent review checkpoints. Codex runs `codex exec -s read-only` (no
write access in this sandbox); Claude applies accepted findings directly.

---

## Review A — Architecture challenge (2026-08-16)

**Scope:** After Phase 0 system audit, before choosing final architecture.
Full prompt: `docs/990-enrichment/` git history / session log.

### Corrections to the Phase 0 audit (accepted)

1. `parse_990_xml()` is **not streaming** — `ET.fromstring()` builds a full
   tree. Fine for one filing at a time; audit's "streaming" language was
   imprecise.
2. The mission guard protects `claimed`/`nonprofit_supplied`/scraped missions,
   but **does not implement "latest IRS filing wins" for `irs_990` → `irs_990`
   replacement** — once `mission_source='irs_990'`, the guard clause
   (`mission_source IS NULL OR LIKE 'ai_%' OR mission IS NULL OR mission=''`)
   blocks even a newer, better 990 filing from updating it. Real gap, not
   just a doc issue — logged as a fix candidate for Phase 3.
3. `org_revenue_history` is `INSERT OR REPLACE` — equal-year records can be
   silently replaced, not just newer ones.
4. `refresh_recent_filings_batch.py` is transactional **per batch**, not per
   filing — safe atomically, but holds a potentially long SQLite write
   transaction.
5. Only `RETURN_TYPE == "990"` is processed by the direct-IRS pipeline today
   — 990-EZ and 990-PF are intentionally excluded. Confirmed by Phase 1
   sampling: 990-EZ has `PrimaryExemptPurposeTxt` (mission equivalent) and
   `ProgramSrvcAccomplishmentGrp/DescriptionProgramSrvcAccomTxt`; 990-PF has
   grant purposes/recipients but no mission-equivalent narrative field.

### Table reuse verdict

- **`extracted_programs`: do not reuse as-is.** Deployed schema is Schedule-O
  blob storage only (`EIN, schedule_o_text, schedule_o_year, schedule_o_source,
  extraction_confidence, extracted_at`). A dormant consumer
  (`scripts/enrichment/program_extraction.py`) assumes an incompatible
  program-row schema — `CREATE TABLE IF NOT EXISTS` never migrated it, so that
  script would fail on write. Historical dead code, not reusable.
- **`org_service_areas`: do not write to it from this project.** It's the
  self-reported/claimed geography store, writable through the claimed-org API,
  and **`/api/search` (daanaa_api.py:6066) uses it to elevate area matches in
  ranking**. Writing model-derived geography there would let an unverified
  extraction quietly change search ordering — a direct conflict with the
  no-ranking-manipulation constraint. Build a separate narrative-geography
  field instead.

### Recommended schema (lowest-complexity, evidence-complete)

```sql
-- one row per (ein, filing, field) — deterministic AND GPU-derived fields
irs_990_narrative_fields (
  ein, tax_year, object_id, field_name, value_json,
  source_xpath, source_excerpt, input_sha256,
  parser_version, model_version NULL, prompt_version NULL, created_at,
  PRIMARY KEY (ein, tax_year, object_id, field_name)
)

-- one row per structured program record (Part III item or Schedule O program)
irs_990_programs (
  ein, tax_year, object_id, program_name, description,
  source_excerpt, source_xpath, parser_version, created_at
)
```

Rejected: a generic evidence graph, or a separate versioned JSON schema per
field. Per-field evidence columns on a plain row cover the "evidence is
mandatory" principle without the extra machinery.

### Scope cuts (accepted — see architecture.md)

- **Cut** the standalone 100-filing gate unless the 15-30 filing review
  exposes a specific failure class worth isolating.
- **Cut** per-field versioned JSON schema + evidence-ID machinery for v1 —
  the plain evidence columns above are sufficient.
- **Defer** the 10,000-filing gate to a background operational scale test
  after first ship, not a pre-ship delivery gate.
- **Keep**: 15-30 stratified filings for parser/evidence review, a 1,000-filing
  dry run for reliability/throughput, and GPU input-hash caching keyed by
  normalized bounded input + prompt/schema/model version.

Lowest-cost first ship, in order:
1. Deterministically extract and store Part III records + Schedule O text
   (with source XPath + SHA-256) — no model involved.
2. Derive only `mission_summary` + structured programs from those bounded
   excerpts (never whole filings) via GPU.
3. Label every summary "derived locally from the organization's reported Form
   990 filing"; label outcomes specifically organization-reported, not
   verified.
4. **Do not touch** `mission`, `org_service_areas`, FTS, or `org_embeddings`
   in v1. New tables only.

### Live search path (resolves system-audit open question #2)

Confirmed by reading `daanaa_api.py` directly: **FTS5 + in-memory
`org_embeddings` is the live path**, not FAISS.
- `/api/search` (daanaa_api.py:6023) — FTS first, falls back to the in-memory
  vector matrix when FTS has too few candidates.
- `/api/search/semantic` (daanaa_api.py:5997) — queries the vector matrix
  directly.
- `build_faiss_index.py` produces deployment/precompute artifacts the live API
  does not load; `build_faiss_docs_index.py` is an internal docs index, unrelated.

Recommendation: when enrichment eventually feeds search, extend the live
`org_embeddings` document composition and selectively re-embed changed EINs.
Do not build a second FAISS path.

### Concurrency / production risk (accepted, informs Phase 3 scheduling)

- SQLite WAL allows concurrent readers, one writer. The 04:15 batch job holds
  a write transaction per batch — a narrative writer needs `busy_timeout`,
  retry/backoff, small commits, and to run **after**, not concurrent with, the
  04:15 job.
- Extending `write_filing()` directly would couple every nightly financial
  refresh to experimental narrative writes and make rollback harder — **run
  narrative extraction as a separate, resumable producer**, not inline in
  `write_filing()`.
- `precompute_similar_orgs` (running at audit time) reads the registry, writes
  static files — no table contention, but real RAM/CPU pressure. GPU narrative
  derivation must not run alongside large embedding/precompute jobs without an
  explicit resource check; the audit's hardware snapshot was time-specific,
  not a durable guarantee.
- FTS rebuild drops and recreates the live table — do not fold it into the
  first enrichment job.

### Verdict

Audit was directionally correct on "don't rebuild the deterministic
foundation." Codex's corrections narrow exactly where that foundation has
real gaps (mission upgrade path, form-type coverage) versus where I'd
over-scoped (JSON schema machinery, extra test gate, reusing wrong-shaped
tables). All findings above accepted into `architecture.md`.
