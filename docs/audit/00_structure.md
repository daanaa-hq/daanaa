# Daanaa Structure Map — PHASE 0 (2026-06-09)

## Backend
- **Single active backend:** `daanaa_api.py` (Flask + SQLite, :5000, 2,731 lines). ~48 routes.
- **CLAUDE.md is stale:** `merit_api.py` and `app.py` no longer exist at root — daanaa_api.py absorbed everything.
- `api/main.py` (FastAPI, 120 lines, 4 routes: /, /percentile, /ntee, /search) — secondary specialist.
- Route groups: public org/search (~14), submit/feedback/waitlist (~8), claim flow (5), admin `X-Admin-Key` (~7), research dashboard auth-gated (~10), SPA fallback.

## Database — data/merit_registry.db (9.6 GB)
- `registry_enriched`: **2,064,612 rows, 537,920 scored** (merit_score NOT NULL).
- 54 columns incl. `irs_revoked`, `bmf_present`, `org_status`, `data_badges`, `donate_confidence`.
- Supporting tables: `org_fts` (FTS5), `org_embeddings`, `revoked_eins`, `irs_sync_log`,
  `score_snapshots`, `scoring_runs`, `v4_scores`, `org_claims`, `waitlist`, `feedback`,
  `donate_handoffs`, `analytics_daily/search`, `research_*` summaries, `page_cache`.
- Other DBs (legacy/secondary): meritgiving.db 1.3G, merit_state.db 271M, droplet_search.db 862M, backup 1.2G.

## Frontend — frontend/src (146 .ts/.tsx files)
- 31 pages (Home, Directory, OrganizationDetail, Wallet, ComparePage, ResearchDashboard, claim flow, Governance, Methodology2…).
- ~30 components + ui/ + research/. Key: OrgCard, FinancialContext, TierBreakdown, TrustBadge, SearchBar, GivingListDrawer.
- Note: GivingListPage/GivingReview/GivingConfirmation pages still present despite Giving List removal (memory says removed) — verify in Phase 2.

## Pipeline — scripts/ (221 .py files)
- Scorers: merit_scorer.py, merit_scorer_db.py, merit_scorer_tier_b.py, agent2_scorer.py (version sprawl — canonical one TBD Phase 3).
- BMF ingest: ingest_bmf_master.py, import_bmf_orgs.py, bmf_delta_analysis.py, agent6_bmf.py, daily_sync.sh.

## Flags for later phases
- P1: 48 routes in one 2,731-line file — input validation density check.
- P2: orphaned Giving List pages; tier-label explanation.
- P3: scorer sprawl (4+ scorer files); revoked_eins + irs_sync_log exist — verify wired in.
- P4: 9.6 GB DB + ~546K embedding vectors in RAM per CLAUDE.md.
