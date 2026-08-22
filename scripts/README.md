# Scripts Directory — Canonical Paths

This directory contains all backend services, data pipeline orchestration, and operations scripts for Daanaa.

**IMPORTANT:** One canonical path per capability. Find the right folder first before building or debugging.

---

## Quick Navigation

| What | Folder | Canonical File |
|------|--------|-----------------|
| **Production API** | `core/` | `droplet_api.py` |
| **Nightly orchestrator** | `core/` | `overnight_pipeline.py` |
| **Search indexing** | `search/` | `build_fts_index.py` |
| **Scoring (v6)** | `scoring/` | `daanaa_scorer.py` |
| **Website discovery** | `discovery/` | `discovery_daemon.py` |
| **Missions & embeddings** | `enrichment/` | `generate_missions.py`, `build_org_embeddings.py` |
| **Deployment** | `ops/` | `sync_droplet_api.sh` |
| **DB migrations** | `migrations/` | *(check folder for current version)* |

Each folder has a **README.md** explaining canonical files, how to use them, and what NOT to use.

---

## Directory Structure

```
scripts/
├── README.md                    # This file (navigation index)
│
├── core/                        # Production essentials
│   ├── README.md               # Canonical: droplet_api.py, overnight_pipeline.py
│   ├── droplet_api.py          # Flask backend (11k lines, 189 routes)
│   └── overnight_pipeline.py   # Nightly orchestrator
│
├── search/                      # FTS search indexing
│   ├── README.md               # Canonical: build_fts_index.py
│   ├── build_fts_index.py      # Main index builder
│   ├── search_index_delta.py   # Incremental updates
│   └── analyze_search_metrics.py
│
├── scoring/                     # Financial context scoring
│   ├── README.md               # Canonical: daanaa_scorer.py (v6)
│   ├── daanaa_scorer.py        # Active scorer
│   ├── compute_composite_score.py
│   └── *(historical scorers live in ../archive/scorers/; do not use)*
│
├── discovery/                   # Org enrichment
│   ├── README.md               # Canonical: discovery_daemon.py, website_discovery_comprehensive.py
│   ├── discovery_daemon.py     # Continuous daemon
│   ├── website_discovery_comprehensive.py
│   ├── charity_navigator_verify.py
│   └── *(supporting discovery utilities are kept in this directory)*
│
├── enrichment/                  # Missions & embeddings
│   ├── README.md               # Canonical per subdomain
│   ├── missions/
│   │   ├── generate_missions.py
│   └── enrich_cause_tags_mission.py
│   └── embeddings/
│       ├── build_org_embeddings.py
│       └── embedding_extraction.py
│
├── ops/                         # Operations & deployment
│   ├── README.md               # Canonical: sync_droplet_api.sh, safe_deploy_droplet.sh
│   ├── sync_droplet_api.sh     # Auto-deploy + smoke test + auto-rollback
│   ├── safe_deploy_droplet.sh  # Full deployment pipeline
│   ├── api_watchdog.sh
│   ├── daemon_health_lib.py
│   └── daanaa_backup.sh
│
├── migrations/                  # Database schema versions
│   └── *(inspect this directory for the applicable migration script)*
│
├── admin/                       # Admin utilities
│   └── admin_key_validator.py
│
├── testing/                     # Test & validation scripts
│   └── *(search-quality tests live in ../tests/)*
│
└── archive/                     # Dead code (do NOT use)
    ├── README.md               # "Everything here is archived"
    ├── legacy_agents/          # Historical agent implementations
    └── scorers/                # Historical scoring implementations
```

---

## How to Find What You Need

**Question: "Where is X?"**

**X = "the search index"**
→ `scripts/search/` → Read `README.md` → `build_fts_index.py` is canonical

**X = "the scoring system"**
→ `scripts/scoring/` → Read `README.md` → `daanaa_scorer.py` (v6) is canonical

**X = "how to deploy to the droplet"**
→ `scripts/ops/` → Read `README.md` → `sync_droplet_api.sh` is canonical

**X = "a script I found in root but don't understand"**
→ It's probably dead code or in-progress work. Check `git log` to see if it's actively maintained.
→ If last commit >30 days old, it's likely abandoned. Move to `archive/`.

---

## Backward Compatibility (Symlinks)

**Corrected 2026-08-22** (verified via `ls -la`, not assumed — a false symlink
claim here caused a real incident once already, DECISIONS.md 2026-08-16):

```
scripts/droplet_api.py          → ../droplet_api.py       (real symlink, confirmed)
scripts/core/droplet_api.py     → ../../droplet_api.py    (real symlink, confirmed)
scripts/overnight_pipeline.py   does NOT exist -- no compat symlink was ever
                                 created for this one. The only real file is
                                 scripts/core/overnight_pipeline.py.
```

**Old imports:**
```python
from scripts.droplet_api import app          # ✅ Works via symlink
from scripts.core.droplet_api import app     # ✅ Also works (actual file, via symlink)
from scripts.overnight_pipeline import main  # ❌ Does NOT work -- no symlink exists
from scripts.core.overnight_pipeline import main  # ✅ Works (actual location)
```

Both import paths work. **Prefer the new path** (`scripts.core.*`) in new code.

---

## Rules

✅ **DO:**
- Read the folder's README.md before building or debugging
- Use canonical files (marked in each folder's README)
- Check git history if you're unsure if a file is active
- Ask Akbar if you find yourself writing a new script (one canonical path per capability)

❌ **DON'T:**
- Edit archived files without asking Akbar
- Create new scripts in `root/` or a new folder without planning (talk to Akbar first)
- Assume a script is active because it exists (check `git log` + README.md)
- Import from scripts/ paths that aren't documented in a README.md

---

## Key Dates & Changes

- **2026-08-12:** Folder structure refactored to domain-first organization (Jake Van Clief model). Symlink compat layer created for backward compatibility.
- **2026-07-25:** v6 scoring went live (1.94M orgs with context)
- **2026-07-18:** Search quality audit baseline (52 tests, all passing)
- **2026-07-05:** Learned: Smoke test is non-negotiable. Service "active" ≠ pages rendering.

---

## Related

- `REPO_MAP.md` — Top-level navigation (database, frontend, deployment, etc.)
- `CLAUDE.md` — Operating agreement + architecture
- `docs/FOLDER_STRUCTURE_PLAN.md` — Why this structure exists + rationale
- `DECISIONS.md` — Why non-obvious choices were made
- `LESSONS.md` — Broke-then-fixed + preventing rules

---

## Getting Started

**First time here?**
1. Read this README.md (you're here ✅)
2. Find your domain's folder (search/, scoring/, etc.)
3. Read that folder's README.md
4. Look at the canonical file's docstring + first 50 lines
5. Run `grep -r "canonical_file" .` to find all places it's used
6. Check git log of that file to understand recent changes

**Building something new?**
1. Check REPO_MAP.md — is there already a canonical path for this?
2. Check this folder's README.md — might already exist
3. If not, talk to Akbar before writing (prevents duplication)
4. Create it in the right domain folder
5. Add a section to that domain's README.md explaining it

**Debugging a problem?**
1. Find the domain (search, scoring, discovery, etc.)
2. Read that folder's README.md "Troubleshooting" section
3. Check LESSONS.md for similar incidents
4. Check DECISIONS.md for recent changes to that domain
5. Read git log of canonical file (what changed? when?)
