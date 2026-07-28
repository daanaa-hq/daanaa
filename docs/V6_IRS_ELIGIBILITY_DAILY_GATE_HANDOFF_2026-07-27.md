# v6 IRS eligibility boundary: developer handoff

## Purpose

Daanaa must not present an organization as currently donation eligible based
on a stale or single-source flag. The daily boundary is now defined as:

1. IRS EO Business Master File: subsection `03` and `DEDUCTIBILITY=1`.
2. IRS Publication 78: the EIN is present with an accepted code (`PC`,
   `POF`, `SC`, `IND`, or `GOV`).
3. IRS auto-revocation list: the EIN is not currently revoked, unless the
   record includes a reinstatement date.

If any source is missing, malformed, older than seven days, or contradictory,
the job must report `BLOCKED` and must not weaken eligibility or activate a
candidate.

## What Codex completed locally

- Added `scripts/v6_refresh_irs_eligibility.py`.
- Default mode is read-only and fail-closed.
- `--refresh` downloads sources into a temporary directory and atomically
  replaces only complete files.
- `--apply` requires `--refresh`, creates a SQLite backup, performs one
  transaction, and writes an `ingestion_audit_log` row.
- No score, peer assignment, mission, wallet, or nonprofit-provided field is
  changed.
- Added four focused tests in `tests/test_v6_irs_eligibility.py`.
- Added the gate to `scripts/v6_daily_operations_automated.sh`.
- Dry-run ingestion is now skipped rather than allowed to hold the eligibility
  check hostage; apply-mode ingestion is capped at five minutes.
- SQLite backup and integrity checks now have bounded timeouts and fail closed.

## Developer integration still required

The new source evidence is not yet wired into the live public API. Before v6
or the donation links are activated, the team must make one canonical helper
or materialized eligibility field available to every public path:

- directory/search results;
- organization detail pages;
- donate-link/action rows;
- hidden gems and event discovery;
- v6 peer-context selection and API responses.

The helper must fail closed when the latest manifest is missing or stale. A
cached `deductibility='1'` value alone is not sufficient. Do not duplicate the
predicate in multiple routes.

## Commands for the team

Run from the repository root:

```bash
# 1. Local syntax and focused tests
bash -n scripts/v6_daily_operations_automated.sh
venv/bin/python -m py_compile scripts/v6_refresh_irs_eligibility.py
venv/bin/python -m pytest -q tests/test_v6_irs_eligibility.py

# 2. Refresh and inspect IRS evidence; this does not modify the database
venv/bin/python scripts/v6_refresh_irs_eligibility.py \
  --db data/merit_registry.db \
  --data-dir data/irs_authority/v6_eligibility \
  --refresh

# 3. Run the daily safety report. It must be PASS or an explicit BLOCKED
#    report; do not interpret NOT_CONFIGURED as success.
V6_APPLY_BACKFILL=false bash scripts/v6_daily_operations_automated.sh

# 4. Only after source review, API integration tests, and founder approval:
#    apply the source-backed field reconciliation.
venv/bin/python scripts/v6_refresh_irs_eligibility.py \
  --db data/merit_registry.db \
  --data-dir data/irs_authority/v6_eligibility \
  --refresh --apply
```

## Required tests before staging

- Fresh source: all three source families are under seven days old.
- Missing source: public eligibility is denied, not inferred.
- Pub 78 non-match: no donation-eligible presentation.
- BMF non-501(c)(3) or non-deductible code: denied.
- Current revocation: denied and excluded from numeric peer groups.
- Reinstatement: does not remain blocked solely because it appeared on an old
  revocation record; it still needs current Pub 78 and BMF evidence.
- Duplicate and malformed rows: quarantined/reported without partial writes.
- Transaction rollback: kill or fail the apply transaction and verify the
  backup and original row counts.
- API boundary: every public route uses the same helper and returns the source
  date/status needed for honest UI wording.

## Non-negotiable deployment gate

Do not enable v6 or claim that giving is tax deductible until the daily report
has current IRS evidence and the public API has passed the shared eligibility
predicate tests. This is a data-integrity gate, not a scoring preference.
