# Folder Structure Refactoring Plan — Jake Van Clief Model

**Purpose:** Reorganize codebase for Claude Code clarity + human onboarding. One canonical path per capability, clear ownership markers, colocation of related files.

**Current State:**
- 486 Python scripts, 151 shell scripts in `scripts/` directory
- 318 files in "misc" category (undefined purpose)
- Scattered subdirectories (ops/, agents/, discovery-phase/, linkedin/, etc.)
- No clear canonical vs. historical distinction
- High token overhead navigating (grep required just to find what's active)

**Target State:**
- **Domain-first organization**: search/, scoring/, discovery/, donations/, etc.
- **Canonical clarity**: Each directory has a README explaining canonical files + what to ignore
- **Frontend alignment**: `frontend/domains/` mirrors backend domains for consistency
- **Zero mystery files**: Every file is clearly labeled canonical, historical, or experimental

---

## Phase 1: Backend Scripts Reorganization

### New Structure (scripts/)

```
scripts/
├── README.md                           # INDEX: what's canonical per job
│
├── core/                               # Production essentials
│   ├── README.md                       # "What runs on the droplet"
│   ├── droplet_api.py                  # CANONICAL: Backend API (synced to droplet)
│   ├── overnight_pipeline.py           # CANONICAL: Nightly orchestrator
│   └── daanaa_api.py                   # Local dev (mirrors droplet_api.py)
│
├── search/                             # FTS search index
│   ├── README.md                       # Canonical: build_fts_index.py
│   ├── build_fts_index.py              # CANONICAL: FTS5 index builder
│   ├── search_index_delta.py           # Incremental index updates
│   ├── analyze_search_metrics.py       # Query analysis & tuning
│   ├── historical/                     # Old implementations
│   │   └── search_index_v2.py
│   └── tests/
│       └── search_quality_tests.py
│
├── scoring/                            # Financial context scoring
│   ├── README.md                       # Canonical: daanaa_scorer.py (v6)
│   ├── daanaa_scorer.py                # CANONICAL: v6 tiered peer context
│   ├── score_snapshots.py              # Version tracking
│   ├── compute_composite_score.py      # Supporting utilities
│   ├── historical/                     # Archived versions (v4, v5)
│   │   ├── merit_scorer_v4_0.py
│   │   └── merit_scorer_v5_0.py
│   └── tests/
│       └── scoring_validation.py
│
├── discovery/                          # Org discovery & enrichment
│   ├── README.md                       # Canonical paths
│   ├── discovery_daemon.py             # CANONICAL: Continuous discovery orchestrator
│   ├── website_discovery_comprehensive.py  # CANONICAL: Website extraction
│   ├── charity_navigator_verify.py     # CANONICAL: CN API verification
│   ├── donation_link_pipeline.py       # CANONICAL: Donate URL discovery
│   ├── supplementary/
│   │   ├── backfill_flame_websites.py
│   │   └── check_link_health.py
│   └── historical/
│       └── (other website_discovery_* scripts)
│
├── enrichment/                         # Data enrichment (missions, embeddings)
│   ├── README.md
│   ├── missions/
│   │   ├── generate_missions.py        # CANONICAL: Qwen mission generation
│   │   ├── enrich_cause_tags_mission.py
│   │   └── historical/
│   ├── embeddings/
│   │   ├── build_org_embeddings.py     # CANONICAL: mxbai-embed vectors
│   │   ├── embedding_extraction.py
│   │   └── historical/
│   └── tests/
│
├── ops/                                # Operations & deployment
│   ├── README.md                       # Canonical: sync_droplet_api.sh
│   ├── sync_droplet_api.sh             # CANONICAL: Deploy backend to droplet
│   ├── safe_deploy_droplet.sh          # CANONICAL: Safe deployment with rollback
│   ├── monitoring/
│   │   ├── api_watchdog.sh
│   │   ├── daemon_health_lib.py        # CANONICAL: Daemon health checks
│   │   └── healthcheck_droplet.sh
│   ├── backup/
│   │   └── daanaa_backup.sh            # CANONICAL: Backup orchestrator
│   ├── database/
│   │   ├── schema_migrations.py
│   │   └── database_reindex.sh
│   └── historical/
│
├── migrations/                         # Database schema
│   ├── README.md
│   ├── 001_initial_schema.sql
│   ├── 002_add_v6_columns.sql
│   └── run_migration.py
│
├── admin/                              # Admin tools
│   ├── README.md
│   ├── admin_key_validator.py
│   └── privacy_audit.py
│
├── testing/                            # Test scripts & validators
│   ├── README.md
│   ├── search_quality_tests.py         # CANONICAL: 52-test suite
│   ├── smoke_tests.sh
│   ├── performance_benchmarks.py
│   └── integration_tests.py
│
└── archive/                            # Dead code (do not use)
    ├── README.md                       # "These are not maintained"
    ├── old_agents/                     # agent1.py through agent13.py
    ├── deprecated_scorers/
    ├── experimental_apis/
    ├── old_website_discovery/
    └── one_offs_2026_q1/
```

---

## Phase 2: Frontend Alignment

Mirror backend domains in frontend where they have UI representation:

```
frontend/src/
├── domains/                            # NEW: Domain-aligned organization
│   ├── search/
│   │   ├── Directory.tsx              # CANONICAL: Search UI
│   │   ├── hooks/useSearchMetrics.ts
│   │   └── components/SearchBar.tsx
│   │
│   ├── discovery/
│   │   ├── NonprofitDashboard.tsx     # CANONICAL: Org dashboard
│   │   ├── OrganizationDetail.tsx     # CANONICAL: Org detail page
│   │   └── components/
│   │
│   ├── wallet/
│   │   ├── WalletPage.tsx             # CANONICAL: Giving wallet
│   │   ├── WalletContext.tsx          # CANONICAL: Wallet state
│   │   └── components/
│   │
│   ├── scoring/
│   │   ├── FinancialContext.tsx       # CANONICAL: v6 context display
│   │   ├── TrustBadge.tsx             # CANONICAL: Trust indicators
│   │   └── components/
│   │
│   └── home/
│       ├── Home.tsx                   # CANONICAL: Homepage
│       └── components/
│
├── shared/                             # Shared utilities (unchanged)
│   ├── components/
│   ├── contexts/
│   ├── hooks/
│   └── utils/
└── pages/                              # DEPRECATED: Legacy org (to be removed in Phase 3)
    └── README.md                       # "Migrating to domains/"
```

---

## Phase 3: Documentation Colocalization

Add README.md to each domain explaining:
1. **Canonical file**: The one source of truth for this capability
2. **Related files**: Supporting scripts/components
3. **Historical/deprecated**: What not to use
4. **How to extend**: Where new features belong
5. **Testing**: How to validate changes

Example `scripts/search/README.md`:

```markdown
# Search Index Pipeline

## Canonical Files
- **build_fts_index.py** — Builds FTS5 full-text search index (runs nightly)
- **search_index_delta.py** — Incremental updates for new orgs

## How to...
- Add a new searchable field → update `_FTS5_FIELDS` in build_fts_index.py + add column to schema
- Tune search quality → see search_quality_tests.py (52 test cases)
- Deploy new index → overnight_pipeline.py handles this automatically

## Do not use
- search_index_v2.py (superseded by build_fts_index.py, 2026-06-15)
- legacy_fts_builder.py (dead as of v4 scoring, archived 2026-07-02)

## Testing
```bash
python3 tests/search_quality_tests.py  # 52 baseline tests
```

## Troubleshooting
See docs/SEARCH_QUALITY.md for common issues.
```

---

## Phase 4: Root-Level Cleanup

**Frontend root** (`frontend/`):
- Keep: `src/`, `index.html`, `package.json`, `tsconfig.json`, `.eslintrc.json`
- Move: `dist/` only created by build, don't commit
- Archive: Old component folders (to `archive/components_20260401/`)

**Project root:**
- Keep: CLAUDE.md, STEWARDSHIP.md, REPO_MAP.md, package.json, etc.
- Move: Old analysis scripts → scripts/archive/
- Clarify: Which `*.md` files are canonical (use REPO_MAP.md) vs. historical

---

## Phase 5: Implementation Approach

**Step 1: Create new directory structure** (non-destructive, parallel)
```bash
mkdir -p scripts/{core,search,scoring,discovery,enrichment,ops,migrations,admin,testing,archive}
mkdir -p frontend/src/domains/{search,discovery,wallet,scoring,home}
```

**Step 2: Move canonical files** to their new locations
```bash
mv scripts/droplet_api.py scripts/core/
mv scripts/overnight_pipeline.py scripts/core/
mv scripts/build_fts_index.py scripts/search/
# ... (one by one with git mv for history preservation)
```

**Step 3: Add README.md to each domain** explaining canonical paths

**Step 4: Update imports** in other scripts to reflect new paths
- Run tests to verify no breakage
- Update any deployment scripts that reference old paths

**Step 5: Verify REPO_MAP.md** reflects new canonical paths

**Step 6: Move historical/dead code** to archive/
- Tag archive/ entries with "do not use" + reason + date

**Step 7: Archive old top-level scripts/** folders (ops/, agents/, etc.) if empty

---

## Expected Token Savings

| Activity | Before | After | Savings |
|----------|--------|-------|---------|
| "Where is scoring?" | grep -r "daanaa_scorer" | docs/FOLDER_STRUCTURE_PLAN.md + grep in domain/ | 60% |
| New contributor | Read 250-line REPO_MAP.md + grep | Read domain README.md (~30 lines) | 80% |
| Adding new search feature | Find test file manually | See scripts/search/README.md → tests/ | 50% |
| Debugging deployment | 5 different ops files to check | scripts/ops/README.md → canonical file | 70% |

---

## Rollout Timeline

- **Day 1**: Create structure + move core files (scripts/core/, scripts/search/, scripts/scoring/)
- **Day 2**: Move discovery, enrichment, ops
- **Day 3**: Frontend domains + symlink compat layer
- **Day 4**: Archive cleanup + REPO_MAP.md update
- **Day 5**: Testing + verification (all tests pass)

Total: **1 week** (can be done autonomously with Codex validation)

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Import breakage | Use `git mv` (preserves history), update imports incrementally, test each step |
| Cron jobs fail | Update all cron paths in systemd/ + institution/systemd/ before rollover |
| Deployment scripts confused | Symlink old paths → new paths as temporary compat layer (remove after 1 month) |
| Droplet sync breaks | Update `scripts/ops/sync_droplet_api.sh` path from `scripts/droplet_api.py` → `scripts/core/droplet_api.py` |

---

## Success Criteria

✅ All imports resolve without modification (or via symlinks)
✅ All 52 search quality tests pass
✅ All cron jobs execute successfully
✅ Droplet deployment works (smoke test 200)
✅ New contributor can find "where is X" in <2 min via REPO_MAP.md
✅ DECISIONS.md + LESSONS.md updated with changes + rationale

