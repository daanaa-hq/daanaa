# Workflow Catalog

## 1. Nonprofit-data workflow

| Item | Evidence |
|---|---|
| Trigger | Scheduled scripts and ingest jobs in `scripts/` |
| Entry points | `sync_irs_data.py`, `auto_ingest.py`, `build_registry_from_orgs.py`, `build_search_db.py` |
| Transformations | Normalize, dedupe, score, enrich, build FTS/search artifacts |
| Storage | `registry_enriched`, `org_fts`, `org_embeddings`, `search.db` |
| User-visible result | Public nonprofit profile and searchable directory |
| Confidence | Confirmed in broad shape; some specific per-field edges require verification |

## 2. Donor journey

| Stage | Evidence |
|---|---|
| Landing/search | Homepage and directory pages call search APIs |
| Evaluate org | Org detail pages show context, peer comparison, mission, website, donate URL, and trust badges |
| Save/bookmark | Wallet and saved-org hooks exist |
| Conversion | Direct hand-off to org-owned website or external destination, not in-platform money movement |
| Confidence | Strong evidence for discovery/evaluation; donation completion is not implemented as a platform payment flow |

## 3. Nonprofit journey

| Stage | Evidence |
|---|---|
| Discovery | Nonprofit directory, claim and nonprofit-facing pages |
| Claim request | `/api/claim/start` and claim tests |
| Verification | Phone/name/title/attestation checks, PIN email flow, admin notification |
| Profile access/update | Claim editor and nonprofit dashboard pages |
| Confidence | Confirmed for claim flow, partial for update/review workflow details |

## 4. Financial transaction workflow

| Stage | Evidence |
|---|---|
| Payment initiation | Not confirmed as an in-platform payment flow |
| Provider/webhook | No confirmed payment processor routes in the backend tests |
| Reconciliation | Not confirmed |
| Confidence | No confirmed payment processing workflow; platform language emphasizes hand-off, not custody |

## 5. Volunteer workflow

| Stage | Evidence |
|---|---|
| Discovery | Volunteer search page and volunteer URL fields |
| Creation/publication | `nonprofit_content` schema and volunteer-related columns in registry appear in migrations/scripts |
| Registration/completion | Not confirmed as a full lifecycle |
| Confidence | Partial; discovery and intent surfaces are present, full lifecycle not confirmed |

## 6. Administrative workflow

| Stage | Evidence |
|---|---|
| Authentication | `DAANAA_ADMIN_KEY` checked with constant-time compare |
| Review | Claim/admin endpoints and dashboards |
| Audit trail | Claim and verification tables, logs, snapshots |
| Confidence | Confirmed at auth gate level; detailed review queue behavior requires more validation |

## 7. AI and scoring workflow

| Stage | Evidence |
|---|---|
| Input data | Public nonprofit filings, missions, websites, embeddings |
| Deterministic calculations | Peer percentiles, revenue bands, reserve context, FTS sorting |
| AI-assisted steps | Mission generation, cause tags, embeddings, enrichment scripts |
| Human control | Stewardship rules and tests require honest language and reviewability |
| Confidence | Confirmed that both AI-assisted and deterministic steps exist; exact production boundaries vary by path |

