# v6 Local Foundation and Candidate Status

Generated: 2026-07-27

## Scope

This checkpoint was completed locally against data/merit_registry.db.
It did not activate the API or frontend and did not deploy anything.

The database backup created before the foundation write is:

/tmp/merit_registry_pre_foundation_apply_20260727.db

## Phase 0A/0C local foundation

The additive normalized tables were populated from the existing
registry_enriched snapshot:

| Table | Rows |
|---|---:|
| org_financial_years | 953,919 |
| org_classifications | 5,102,213 |
| org_operating_context | 953,919 |

The ingestion audit recorded 2,618 records with financial values but no valid
tax year. They were quarantined rather than entering the financial-year table.

The source is a local registry snapshot. This is not yet a fresh external IRS,
NCCS, or ProPublica ingestion batch.

## Candidate run

Run ID: v6_foundation_candidate_20260727

The candidate ledger contains 1,910,561 assignments:

| Tier | Count | Share |
|---|---:|---:|
| Tier 1 direct | 336,735 | 17.62% |
| Tier 2 regional conditional | 893,721 | 46.78% |
| Tier 2 national conditional | 5,699 | 0.30% |
| Tier 3 broader regional | 50,752 | 2.66% |
| Tier 4 national | 2,763 | 0.14% |
| Tier 5 archetype only | 620,891 | 32.50% |

Numeric peer-context coverage: **67.50%**.

## Integrity checks

- Assignment count equals active, deductible, nonrevoked population.
- Distinct EIN count equals assignment count.
- Revoked assignments: 0.
- Numeric assignments below five scoreable peers: 0.
- Tier 5 assignments with numeric peer values: 0.
- Historical v6 legacy run remains preserved.
- Active API and frontend remain unchanged.

## Important limitations

This is a candidate run, not a canonical public scoring release.

The current backfill uses the existing local registry snapshot. It does not
yet ingest new external IRS, NCCS, or ProPublica records. The next validation
steps are:

1. Confirm source adapters and current source provenance.
2. Validate conditional revenue-band tables for organizations without revenue.
3. Review archetype quality and NTEE fallback behavior.
4. Run fairness and privacy checks.
5. Obtain founder approval before API or frontend activation.
