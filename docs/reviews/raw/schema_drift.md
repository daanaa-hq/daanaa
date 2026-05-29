# Schema Drift Report — 2026-05-28
## Tables in live DB vs code-created at startup (merit_api.py)

### Tables auto-created by merit_api.py on startup
- `waitlist` — `_init_waitlist_table()` ✓
- `link_feedback` — `_init_link_feedback_table()` ✓

### Tables that MUST exist but are NOT created by merit_api.py
These require a hand-applied migration or a fresh pipeline run. A fresh clone
pointing at an empty DB will crash when these are accessed.

| Table | Used by | Severity |
|-------|---------|----------|
| `org_claims` | `/api/claim/start`, `/api/claim/verify`, `/api/claim/profile` | **P0 — API crash on claim attempt** |
| `registry_enriched` | All org-lookup routes | P0 — but this is seeded by data pipeline; documented as expected |
| `donate_work_queue` | donation_link_pipeline.py | LOW — background script only |
| `page_cache` | fetch_org_websites.py, generate_missions.py | LOW — background script only |
| `org_embeddings` | /api/search (semantic) | MEDIUM — search degrades gracefully |
| `human_review_queue` | donation_link_pipeline.py | LOW |
| `release_batches` | donation_link_pipeline.py | LOW |
| `blocked_domains` | donation_link_pipeline.py | LOW |
| `donation_link_evidence` | donation_link_pipeline.py | LOW |
| `agent_job_log` | pipeline scripts | LOW |
| `scoring_runs` | scoring scripts | LOW |
| `score_snapshots` | scoring scripts | LOW |
| `propublica_financials` | ingest scripts | LOW |
| `revenue_percentiles` | scoring scripts | LOW |
| `nccs_core_2019` | ingest scripts | LOW |
| `irs_bmf` | ingest scripts | LOW |
| `org_fts_*` | /api/search (FTS) | MEDIUM — search degrades gracefully |

### Fix required for 0.2b
Add `_init_org_claims_table()` to merit_api.py at module load (matching the
live DDL at docs/reviews/raw/live_schema.sql:560–580).

### Tables in live DB NOT in any current code
None found — all tables have at least one script reference.

### Verdict
schema_drift is NOT empty — `org_claims` is the sole P0 gap. All others are
pipeline-only tables created by scripts run as part of initial data load.
