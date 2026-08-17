# Codex Reviews — 990 Narrative Enrichment

Independent review checkpoints. Codex runs `codex exec -s read-only` (no
write access in this sandbox); Claude applies accepted findings directly.

---

## Review D — GPU enrichment (2026-08-16)

**Scope:** Phase 4 (GPU-derived semantic fields). Read
`scripts/enrichment/llm_extraction.py`'s narrative-enrichment additions,
`scripts/enrichment/narrative_990/gpu_enrichment.py`, and
`migrations/024_irs_990_narrative_gpu_summary.sql` directly, against the
architecture doc's claims. 7 questions: deterministic-vs-LLM division of
work, hallucination defenses, cache/version invalidation, batching, JSON
failure behavior, storage/stewardship separation, GPU-window appropriateness.

### Findings and resolution

| # | Finding | Verdict | Resolution |
|---|---|---|---|
| 1 | `significant_new_program`/`significant_change` are deterministically parsed but weren't fed into `build_narrative_input()` at all (at the time Codex read the file) | Real gap | **Fixed**, twice over: first as an LLM prompt hint (same session, before this review), then — per this review's stronger recommendation — persisted as their own deterministic columns in migration 024, independent of the model narrating them. Program expense amounts in the input with no corresponding output field, risking "expense size = importance" inference | Real, minor | **Fixed**: removed from input; descriptions only. |
| 2 | No source-span/evidence-reference on any generated claim, despite `architecture.md` claiming evidence IDs exist (stale language inherited from the original Codex Review A proposal, never actually implemented in the scoped-down v1). `grounded` is model self-certification, not independent verification, and conflates "thin input" with "unsupported output" | Real, most substantive finding | **Fixed**: `reported_outcomes` items now require a verbatim `evidence_quote`; `_verify_reported_outcomes()` mechanically checks it appears in the bounded input (normalized) before storage, drops and logs anything that doesn't match. `grounded`'s schema description reframed as diagnostic-only. |
| 3 | Cache invalidation logic is correct (`already_cached()` requires input hash + model + prompt version to all match), but the stored `model_version` value was the API-facing model-name string, not a real artifact identifier — wouldn't invalidate if the served gguf changed under the same name | Real, minor | **Fixed**: `MODEL_ARTIFACT_VERSION` constant stores the specific quantized filename, independent of what string the API call itself uses. |
| 4 | Sequential single-request calls are adequate for 24 filings but would take ~6.3 hours serial at 1.2s/filing against a ~19K-filing batch; the model launch already supports multi-slot continuous batching (`gpu_night.sh`'s `--parallel 6 --cont-batching`), matching the embedding server's `-np 16` convention — not used here | Real, scale concern | **Deliberately deferred** — a bounded-concurrency producer against a single-writer SQLite target is real engineering with real bug risk; better built carefully before the 1,000-filing gate than rushed same-session. Documented as an explicit open item, not silently skipped. |
| 5 | `_call_llm()`'s exception handling only covered `KeyError`/`JSONDecodeError` — a non-JSON response body, empty/absent `choices`, or wrong-shaped-but-valid JSON weren't all guarded | Real | **Fixed**: widened to `(KeyError, IndexError, TypeError, ValueError)` — `JSONDecodeError` is a `ValueError` subclass, so still covered. Added `_validate_shape()` for a local structural check (required keys present, array fields are lists) beyond `json.loads()` succeeding. Shared function — also hardens the original website-extraction callers. |
| 6 | Separate-table storage design confirmed correct: no Phase 4 write path touches `mission`, `cause_tags`, `org_service_areas`, scores, or embeddings — the only write is the standalone summary table | Confirmed, no issue | No change needed. Noted: row-level input hashing is provenance for the *filing*, not per-claim evidence — that's what finding #2's fix addresses. |
| 7 | Founder's 1-hour daytime exception was appropriate; nothing in the code requires daytime operation (local, synchronous). Code doesn't itself enforce the night-only window — acceptable if scheduling is the intended gate. Separately: `gpu_night.sh` documents 9pm-9am, CLAUDE.md documents 10pm-6am — a pre-existing discrepancy, unrelated to this project | Confirmed appropriate + unrelated pre-existing drift | Not this project's call to reconcile; flagged in `DECISIONS.md` for founder awareness. |

### Self-caught issue during fix verification (not a Codex finding)

Testing migration 024 via `db.executescript()` inside a `BEGIN`/`ROLLBACK`
block silently broke the rollback guarantee (`executescript()` implicitly
commits pending transactions, DDL inside it isn't covered by a later
`ROLLBACK`) — the table was created for real in production with the stale
pre-fix schema. 0 rows, caught on the next test run failing, corrected via
`DROP TABLE`, verified clean. Full writeup: `LESSONS.md` 2026-08-16. Test
harness fixed to `execute()` per statement and to explicitly verify rollback
by querying `sqlite_master` afterward.

### Verdict

"Directionally sound... require claim-level evidence plus local schema
validation, deterministic treatment of the significant-change flags, and a
measured 4-6-slot batch producer before the 1,000-filing run." First three
addressed same session; batching explicitly deferred with reasoning, not
silently dropped.

---

## Review B/C — Extended parser correctness/security (2026-08-16)

**Scope:** combined (per founder's "one system" directive collapsing the
originally separate XML-inventory and parser-correctness reviews into one
pass on the actual Phase 3 diff). Read `scripts/ops/fetch_irs_direct_filing.py`
directly (git diff against the pre-Phase-3 commit) and independently assessed
8 questions: XML/security, Schedule O regex correctness, mission-year guard
correctness, financial-write-guard correctness, idempotency, `cause_tags`
import safety, batch concurrency, and stewardship/ranking impact.

### Findings and resolution

| # | Finding | Verdict | Resolution |
|---|---|---|---|
| 1 | `ET.fromstring()` has no cap on document size/nesting/text length/repeating-group count; not an XXE risk (stdlib doesn't resolve external entities) but no defense against a pathologically large/deep filing | Real, low-severity (IRS is a trusted upstream in practice) | **Fixed**: added `MAX_FIELD_TEXT_LEN` (20K chars, ~4x the largest real Schedule O snippet seen) on every extracted text field, `MAX_LIST_ITEMS` (200, an order of magnitude above real filings' single-digit-to-low-dozens program/grant counts) on every repeating-group `findall()`. Full XXE/DTD hardening (defusedxml) left as a follow-up — matches the pre-existing financial parser's posture, not a regression introduced here. |
| 2 | `SCHEDULE_O_LINE_ALLOW` regex — checked against every documented real `FormAndLineReferenceDesc` value | **Correct**, no error found. Two acknowledged edge cases: rejects undocumented format variants ("Pt. III", "Part 3"), admits any line containing the literal word "MISSION" even hypothetically in an unrelated line | Not fixed — no counterexample found in real data; noted as a known limitation in the regex's own comment. |
| 3 | Mission-year guard does implement "newer wins" correctly on current data, but `mission_last_verified` is `TEXT` and compared lexically — a value shaped differently than a 4-digit year (e.g. an ISO timestamp) would sort wrong | Correct on live data today, real schema-contract fragility | **Fixed**: `CAST(mission_last_verified AS INTEGER)` on both sides of the comparison. Fails safe — a malformed existing value casts to 0, sorting below any real year, so it's treated as staler (replaceable) rather than newer (protected), which is the safe direction to fail in. |
| 4 | Financial guard (`if total_revenue is not None`) correctly protects revenue, but writes `total_assets` unconditionally within that block — a filing with parseable revenue but a failed/missing assets figure would still null out `total_assets` | **Real residual bug**, confirmed | **Fixed**: `COALESCE(new_value, existing_value)` on `total_assets` in both `org_revenue_history` and `registry_enriched` writes, so a per-field parse failure can never clobber a per-field value that was already known good. (Introduced a param-count bug applying this fix — caught by re-running the 24-filing regression test immediately after, fixed before commit.) |
| 5 | Idempotency of `extracted_programs` INSERT OR REPLACE, `cause_tags` merge, financial upserts | **Good**, no issue found | No change. |
| 6 | Importing `apply_rules`/`merge_tags` from `enrich_cause_tags_mission.py` at module level — safe today (no DB/network/CLI side effects at import time) but a script being used as a library without an explicit API contract | Correct as-is; architectural note for later | Not fixed now — noted as a future stability improvement (move `RULES`/`apply_rules`/`merge_tags` to a small dependency-free shared module) if/when that script's own CLI surface changes in a way that could break this import. |
| 7 | `process_batch()` holds one SQLite write transaction for the whole batch; the narrative writes now add ~4 more statements per filing inside that transaction, extending the single-writer lock hold on a large batch | Real operational scaling concern, not a correctness bug | Not fixed now — recommended chunked commits (250-500 filings/transaction) as a follow-up if/when a batch's registry-matched EIN count grows large enough to matter; writes are idempotent so chunking is safe to add later without a migration. |
| 8 | No writes to `org_service_areas` or any scoring/tier/percentile field (confirmed) — but `cause_tags` itself feeds both FTS ranking and semantic embeddings, so it DOES affect search-result ordering, just not trust/merit scoring | Accurate, needed explicit documentation | **Documented**: `architecture.md` and this file now state explicitly that STEWARDSHIP.md P7 ("no ranking manipulation") is understood here as governing *trust/merit* signals (score, tier, badges) — not *search relevance* ranking, which this project's stated goal is to improve. The distinction that makes this acceptable: tags are rule-derived from the org's own IRS-filed narrative (deterministic, evidence-grounded, same evidentiary bar the existing mission-derived `cause_tags` system already used), not inferred/guessed or paid-for influence. |

### Post-review validation

Re-ran the 24-filing dry-run regression (rolled-back DB transaction, same
harness as pre-review) after applying all fixes: identical positive results
(12/24 missions upgraded, 6/24 gained cause_tags, 16 new tags, 16/24
programs_available flipped, 6 Schedule O rows written), zero errors, zero
regressions on `total_assets`/`total_revenue` preservation.

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
