# Data Lineage

## Confirmed lineage

External nonprofit and public-source data enters the platform from public IRS and ProPublica sources. Evidence:

- Backend and stewardship docs describe public-data indexing and IRS/ProPublica sourcing.
- Search and claim tests use registry-derived rows and public-data assumptions.
- Multiple scripts explicitly call the ProPublica nonprofit API.

## Verified transformations

1. Ingestion and normalization
   - Scripts such as [`auto_ingest.py`](/home/akbar/meritgiving/scripts/auto_ingest.py), [`sync_irs_data.py`](/home/akbar/meritgiving/scripts/sync_irs_data.py), and [`build_registry_from_orgs.py`](/home/akbar/meritgiving/scripts/build_registry_from_orgs.py) indicate normalization into SQLite tables.
2. Matching and enrichment
   - EIN-based matching is visible in claim logic and in search/detail code.
   - Several scripts and comments refer to dedupe, revocation handling, donate URL verification, and website normalization.
3. Scoring and context
   - Financial context and peer comparison are computed from public filings and stored in registry fields.
4. Search indexing
   - `org_fts` is built for keyword search.
   - `org_embeddings` is used for semantic lookup.
5. Public rendering
   - Frontend and droplet API surface the resulting data to donors and nonprofits.

## Unverified connections

- Exact source-to-table lineage for every field is not fully proven by the repo snapshot alone.
- Some enrichment paths are clearly present in scripts but need runtime confirmation to mark as fully production-active.
- Some data products in migrations appear to be scaffolding or planned systems rather than active user-facing features.

