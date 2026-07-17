# System Inventory

## Platform layers

| Component | Purpose | Location | Entry point | Data received | Data produced | Confidence |
|---|---|---|---|---|---|---|
| Full API | Canonical backend for local/full functionality | [`daanaa_api.py`](/home/akbar/meritgiving/daanaa_api.py) | Flask app routes | HTTP requests, Firebase tokens, form payloads | JSON API responses, DB writes, email sends | Confirmed |
| Droplet API | Production-edge browse/search/detail server | [`scripts/droplet_api.py`](/home/akbar/meritgiving/scripts/droplet_api.py) | Flask app routes | HTTP requests | JSON responses from precomputed files and `search.db` | Confirmed |
| Frontend | Donor/nonprofit/admin UI | [`frontend/src`](/home/akbar/meritgiving/frontend/src) | React app | API responses, browser state, URL params | UI render, local wallet state, search requests | Confirmed |
| Data pipeline | Ingestion, scoring, enrichment, search build, and sync | [`scripts/`](/home/akbar/meritgiving/scripts) | Cron/scripts | IRS, ProPublica, local DB, local model services | Updated DBs, static artifacts, reports | Confirmed |
| Institutional memory | Governance, state, decisions, risks | [`institution/`](/home/akbar/meritgiving/institution) | Markdown files | Human-authored updates | Audit trail, strategy snapshots | Confirmed |

## Backend and API surfaces

| Surface | Purpose | Location | Evidence |
|---|---|---|---|
| `/api/search` | Keyword and fused search | [`daanaa_api.py`](/home/akbar/meritgiving/daanaa_api.py), [`scripts/droplet_api.py`](/home/akbar/meritgiving/scripts/droplet_api.py) | Search reliability test, droplet FTS path |
| `/api/organizations` | Browse and filter nonprofits | Same | Frontend directory calls, browse filters, droplet and full API logic |
| `/api/claim/*` | Nonprofit claim flow | [`daanaa_api.py`](/home/akbar/meritgiving/daanaa_api.py) | Claim flow tests |
| `/api/admin/*` | Admin actions | [`daanaa_api.py`](/home/akbar/meritgiving/daanaa_api.py) | Principle tests for timing-safe admin key |
| `/api/wallet/*` | Cross-device wallet sync | [`daanaa_api.py`](/home/akbar/meritgiving/daanaa_api.py) | Principle tests requiring Firebase auth |

## Data and storage

| Store | Purpose | Location | Read | Write | Confidence |
|---|---|---|---|---|---|
| `data/merit_registry.db` | Main registry and enrichment store | repo `data/` | API, scripts | Ingest/scoring/claim-related flows | Confirmed |
| `search.db` | Production-edge FTS/search database | droplet precompute path | Droplet API | Search build pipeline | Confirmed |
| `org_claims` table | Claim and verification records | SQLite | Claim flows, admin review, org detail merge | Claim start/verify/review | Confirmed |
| `wallet_analytics` and donor-learning tables | Learning and analytics scaffolding | `migrations/001`, `012` | Analytics/reporting scripts | Learning and intent tracking | Confirmed in schema, runtime usage requires verification |
| `org_embeddings` | Semantic search vectors | `data/merit_registry.db` | Search paths | Embedding pipeline | Confirmed |
| `org_fts` | Full-text search index | `data/merit_registry.db`, `search.db` | Search paths | Build scripts | Confirmed |

## External systems

| System | Use | Confidence |
|---|---|---|
| Firebase Auth / Google public keys | Wallet auth and token verification | Confirmed |
| ProPublica nonprofit API | Public nonprofit data source | Confirmed |
| IRS public data files | Public nonprofit data source | Confirmed |
| Plausible | Present in frontend assets and startup configuration | Strong evidence |
| Sentry | Optional error tracking in backend and frontend references | Strong evidence |
| AWS S3 / boto3 | Optional enrichment fetch in droplet API | Strong evidence |
| Twilio | Voice/messaging imports in backend | Strong evidence; production use not fully verified |

