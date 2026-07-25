# Skill: Daanaa Data Gap Recovery

**Mission:** Close registry coverage gaps from public filings, strongest evidence first. Never let an AI guess outrank a document the organization signed.

## When to invoke

Use `/data-gap-recovery` when coverage for any registry field is low and the question is "where else can we get this?" — websites, missions, revenue, assets, governance. Also use it before inventing a scraper: the answer is usually already on disk.

## Source precedence (Stewardship P3, P10)

Strongest first. A weaker source never overwrites a stronger one.

| Rank | Source | `*_source` value | Why |
|---|---|---|---|
| 1 | Org told us directly | `claimed`, `nonprofit_supplied` | They own their own facts |
| 2 | Org told the IRS | `irs_990`, `irs_990_xml` | Signed, dated, public record |
| 3 | Bulk registry | `irs`, `bmf`, `nccs` | Public but secondhand |
| 4 | We inferred it | `ai_*`, `domain_guess` | Replace on sight when 1-3 available |

Write the source column on **every** ingest. A value with no provenance cannot be defended later and violates P3.

## What is actually on disk (verified 2026-07-25)

`data/nccs/` holds 8.3GB of Form 990 extracts, 2017-2023, five parts:

| File | Carries |
|---|---|
| `F9-P01-T00-SUMMARY` | **Mission text** (`F9_01_ACT_GVRN_ACT_MISSION`, ~60% fill), total revenue CY/PY, employees, volunteers, board size, and the **S3 URL of the raw 990 XML** |
| `F9-P02-T00-SIGNATURE` | Signing officer, preparer firm. No financials — do not look for balance sheet here |
| `F9-P06-T00-GOVERNANCE` | Conflict-of-interest, whistleblower, doc-retention policies; asset diversion; states filed. Its `URL` column is the XML link, **not** the org website |
| `F9-P09-T00-EXPENSES` | 137 expense columns: grants US/foreign, fundraising, legal, accounting, occupancy, travel, IT |
| `F9-P10-T00-BALANCE-SHEET` | `F9_10_ASSET_TOT_EOY`, `F9_10_LIAB_TOT_EOY`, plus cash, pledges, land, loans to officers |

**The website repository:** every NCCS row's `URL` points at that org's raw 990 XML on S3, and the XML contains `<WebsiteAddressTxt>` — the site the org reported on its return. ~52% of filings carry a real one. This is the highest-quality website source available.

**Dead ends, already checked — do not retry:**
- IRS BMF (`data/bmf.csv`) has no website column
- ProPublica cached JSON (`data/raw/propublica/`, 15,980 files) carries no website or URL field

## Scripts

| Script | Fills |
|---|---|
| `scripts/harvest_990_websites.py --year YYYY` | `website` from 990 XML. Async, ~560 filings/sec at `--concurrency 50`, checkpointed and resumable |
| `scripts/ingest_990_missions.py` | `mission` from Part I, superseding `ai_*` |
| `scripts/ingest_nccs_part10_balance_sheet.py` | `total_assets`, `total_liabilities` |
| `scripts/ingest_nccs_part1_financials.py` | `revenue_3yr_avg` |

Newest year first in every one; earlier years only fill remaining holes, so re-runs are safe.

## Hard-won rules

- **Never background a long job with `&` inside a foreground Bash call.** The call times out at 2 minutes and takes its children with it. Three ingest jobs died this way on 2026-07-25 and left empty logs. Use `run_in_background: true`.
- **One writer at a time.** SQLite serialises writers; a harvest and an ingest running together turn a 6ms query into seconds. Chain phases with an `until ! pgrep -f <script>; do sleep 20; done` guard.
- **Count with `COUNT(col)`, never `COUNT(CASE WHEN col IS NOT NULL THEN 1 ELSE 0 END)`** — the latter counts every row and reports 100% coverage for everything.
- **`cursor.rowcount` summed across year-files double-counts** orgs that filed every year. Report distinct coverage from a final `COUNT(col)`, not the running total.
- **Replacing missions invalidates embeddings.** `org_embeddings` is built from mission text; after a mission ingest the FTS index and vectors both describe text that no longer exists. Always follow with `build_fts_index.py --rebuild`, then `build_org_embeddings.py --overwrite`.

## Order of operations

1. Ingest (harvest / mission / financial) — one at a time
2. `python3 scripts/build_fts_index.py --rebuild`
3. `python3 scripts/build_org_embeddings.py --model mxbai-embed-large --dim 1024 --overwrite --vulkan --workers 16`
4. Verify, then ship via `/daanaa-deploy`

## GPU etiquette

Default is night-only, 10pm-6am, for heat (`gpu_night.sh`). The founder can lift it for a stated window; that lift is temporary and does not change the standing rule. When batch embedding, widen the server first — `EMBED_SLOTS=16 bash scripts/embed_server.sh start` — since 4 slots leave the GPU idle between requests.

## Definition of done

- Every written field carries its `*_source`
- Coverage reported as distinct `COUNT(col)`, before and after
- FTS rebuilt and embeddings refreshed if mission text moved
- Schema additions proposed to the founder, never applied unilaterally
- `DECISIONS.md` gets the source-precedence call, `LESSONS.md` gets anything that broke
