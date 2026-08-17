# T-2026-08-16-003 — Drop legacy `registry_enriched.revenue_band` column

| Field | Value |
|---|---|
| Owner | Claude Code (implementation), founder approval required to execute |
| Scope | Drop `registry_enriched.revenue_band` (schema change) after a 30-day safety window |
| Affected paths | `data/merit_registry.db` (schema), any script still `SELECT`ing the raw column (should be none after this session's fix — verify again before dropping) |
| Authority constraints | Schema/migration change — requires explicit founder approval per CLAUDE.md's approval gates, regardless of how routine it looks |
| Status | SCHEDULED, not ready to execute until the date below |
| Do-not-execute-before | **2026-09-15** (30 days from decision date) |
| Founder decision | 2026-08-16 — "I think we should move to V6. Keep the old one for now and remove it after 30 days." |

---

## Why this exists

`registry_enriched.revenue_band` was found live and wrong on 2026-08-16 (`DECISIONS.md` same date) — a relic of a pre-V6 scorer generation, last meaningfully written ~2026-05-20, serving stale size-tier labels on the org detail page, directory listing, and search results (verified real case: the Michael & Susan Dell Foundation, $4.27B revenue, stored and served as `"Micro"`).

Fixed same day: every API response now computes its `revenue_band` live from V6's `peer_group.get_revenue_band()` via a shared `_replace_revenue_band()` helper in `daanaa_api.py`, applied at all 5 confirmed serving sites. The stored column is no longer read by any of those paths.

The column itself was deliberately **not** dropped immediately — kept as a 30-day rollback/audit window per founder decision, in case something downstream still depends on it that wasn't caught in this session's sweep.

## Before executing (2026-09-15 or later)

1. Re-run the same grep sweep this session did (`grep -rln "revenue_band" scripts daanaa_api.py`) to confirm nothing new started reading the raw column in the interim.
2. Confirm this fix actually reached the live droplet (`droplet_api.py`) — this session's fix was made and tested on the local codebase only; deployment is a separate, still-pending step (see `DECISIONS.md` 2026-08-16).
3. Get explicit founder sign-off for the actual `ALTER TABLE ... DROP COLUMN` (or equivalent), per the schema-change approval gate — this task file documents intent, it is not itself the approval.
4. Take a fresh DB backup immediately before executing (`scripts/ops/daanaa_backup.sh`), same convention as every other schema change this session.

## Not in scope for this task

- The frontend `discovery.ts` fix (already applied same day, separate from this column) — see `DECISIONS.md` 2026-08-16.
- `mapToDirectoryFilters()`'s dead `filters.revenue_band = ['0', '1']` code — confirmed unused (never called), left alone, not part of this cleanup.
