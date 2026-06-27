# Daanaa Visibility Export

Generated on 2026-06-24 from local project data only. No deployment was performed, and no production application code was changed.

## Primary Source

The export uses `data/merit_registry.db`, table `registry_enriched`.

This table contains the required fields:

- `EIN` -> `ein`
- `organization_name` -> `name`
- `CITY` -> `city`
- `STATE` -> `state`
- `NTEE1` / `NTEECC` -> `category_letter` and `category_name`

Only active deductible organizations are exported:

```sql
WHERE EIN IS NOT NULL
  AND EIN != ''
  AND organization_name IS NOT NULL
  AND organization_name != ''
  AND org_status = 'active'
  AND CAST(deductibility AS TEXT) = '1'
```

## Record Counts

- `data/merit_registry.db:registry_enriched`: 2,042,897 records
- Records with EIN: 2,042,897
- Records with name: 2,042,897
- Records with city: 2,042,896
- Records with state: 2,041,620
- Records with NTEE category: 1,755,600
- Active records: 1,946,650
- Exported active deductible records: 1,836,736

Registry `source` counts:

- `IRS_BMF`: 1,040,281
- `NCCS_ONLY`: 550,772
- `bmf_stub`: 451,843
- `null`: 1

Registry `data_source` counts:

- `irs_soi`: 558,055
- `bmf`: 419,161
- `propublica`: 42,449
- `gt990_index`: 1,872
- blank/null: 1,021,360

## Discovered Data Sources

- `data/merit_registry.db`: primary active SQLite registry. `registry_enriched` contains EIN, organization name, city, state, NTEE category, status, deductibility, and enrichment fields.
- `data/search.db` and `data/droplet_search.db`: derived search/static-serving SQLite databases with registry copies used by public lookup paths.
- `data/eo1.csv`, `data/eo3.csv`, `data/eo4.csv`, `data/cache/bmf_new/*.csv`, `data/bmf/2026-04-BMF.csv`, `data/raw/2023_eo_bmf.csv`: IRS Exempt Organizations Business Master File extracts.
- `data/master_orgs.csv` and `data/csv/master_orgs.csv`: master organization CSV snapshots used by older ETL scripts.
- `data/corepcf/*.csv` and `data/nccs/*.CSV`: NCCS/Core financial and category inputs keyed by EIN.
- `data/propublica_cache/*.json`: cached ProPublica Nonprofit Explorer organization responses keyed by EIN.
- `data/xml/{2020,2022}/*.xml` and `data/csv/*_parsed.tar.gz`: IRS 990 XML filings and parsed archives.
- `data/990n_data.zip`, `data/epostcard.zip`, `data/data-download-epostcard.txt`, `data/csv/postcard_filers.csv`: IRS 990-N/e-postcard sources.
- `precompute_output/ein_map.json.gz` and `precompute_output/orgs/`: generated static org lookup/precompute artifacts when present.
- `migrations/*.sql`, `scripts/ingest_*.py`, `scripts/import_bmf_orgs.py`, `scripts/propublica_backfill.py`, `scripts/overnight_build.py`: schema and ETL scripts that create, ingest, and backfill nonprofit data.

## Files Created

- `scripts/generate_visibility_exports.py`
- `data/orgs.csv`
- `dist/sitemap-index.xml`
- `dist/sitemaps/orgs-0001.xml` through `dist/sitemaps/orgs-0037.xml`
- `dist/llms.txt`
- `dist/open-data.html`
- `dist/visibility-manifest.json`
- `README-visibility.md`

## EIN Format

Exported EIN values are strict 9-digit machine identifiers with no dash, for example `123456789`. Public UI may display the same EIN as `12-3456789`, but CSV keys and profile URLs should keep the 9-digit form.

## Generated CSV Columns

`data/orgs.csv` contains:

```text
ein,name,city,state,category_letter,category_name,profile_url
```

`profile_url` is generated as:

```text
https://daanaa.org/org/{ein}
```

## Regenerate

Run:

```bash
python3 scripts/generate_visibility_exports.py
```

Optional paths:

```bash
python3 scripts/generate_visibility_exports.py \
  --db data/merit_registry.db \
  --orgs-csv data/orgs.csv \
  --dist dist
```

The script opens the SQLite database in read-only mode and rewrites only the visibility/export artifacts listed above.


## Deploy To Cloudflare Pages

When you are ready to publish the overlay, use the interactive wrapper:

```bash
./visibility/scripts/deploy_cloudflare_pages_interactive.sh
```

The script will prompt for the Cloudflare API token locally if `CLOUDFLARE_API_TOKEN` is not already set, then deploy the `visibility/cloudflare-public` bundle to the `daanaa-visibility` Pages project.
