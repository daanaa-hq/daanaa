# Database and Storage Map

## Databases

| Database | Role | Reads | Writes | Notes |
|---|---|---|---|---|
| `data/merit_registry.db` | Main registry and enrichment DB | Full backend, scripts | Ingestion, scoring, claims, enrichment | Primary source of truth in local/full mode |
| `search.db` | Lean production-edge search DB | Droplet API | Build pipeline only | Reopened on inode swap |
| Legacy/secondary DBs | Historical and compatibility stores | Some scripts | Some migration or legacy processes | Not authoritative in repo guidance |

## Important tables from evidence

| Table | Role |
|---|---|
| `registry_enriched` | Main nonprofit record table |
| `org_fts` | Full-text search index |
| `org_embeddings` | Embedding store |
| `score_snapshots` | Score history |
| `scoring_runs` | Scoring run metadata |
| `org_claims` | Claim records and verification state |
| `waitlist` | Waitlist data |
| `wallet_analytics` | Wallet analytics |
| `nonprofit_content` | Nonprofit-authored content |
| `nonprofit_verifications` | Verification audit trail |
| `verification_audit_log` | Verification audit events |

## Object and file storage

- Precomputed gzipped JSON files are served by the droplet API.
- Claims are also merged from per-EIN JSON files in the droplet path.
- Static frontend assets are served from the Vite build output.
- S3 enrichment fetches are present behind an optional boto3 path.

