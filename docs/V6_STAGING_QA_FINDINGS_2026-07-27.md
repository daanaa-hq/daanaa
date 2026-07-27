# v6 Staging QA Findings

## Findings corrected locally

1. The API looked only for a scoring run with status active, while the
   corrected founder-review run is intentionally status candidate.
   The handler now selects the explicit run ID from V6_CANDIDATE_RUN_ID and
   permits candidate or active status.

2. The API selected an archetype column that does not exist on
   v6_peer_context_assignments. It now joins the organization snapshot for the
   current classified archetype.

3. The API used methodology_version and lowercase EIN names that did not match
   the SQLite schemas. Explicit aliases now normalize the API contract.

4. The conditional-band query expected an EIN column that does not exist in the
   normalized table. It now uses run_id and peer_group_key.

5. A no-revenue Tier 2 organization with no qualifying conditional band could
   have received blended peer statistics. The API now suppresses those
   statistics and explains that no conditional numeric comparison is available.

6. The frontend had two TypeScript errors: optional percentile narrowing and
   ApiOrganization.EIN casing. Both are corrected.

## Verification

- v6 unit tests: 12 passed
- Privacy check: passed
- Frontend production build: passed
- Direct API smoke test: passed
- No-revenue Tier 2 smoke test: passed
- Active API/frontend deployment: not performed

## Required documentation correction

The staging summary and activation guide should be updated to identify
v6_foundation_candidate_20260727_corrected as the review candidate and to
remove stale references to an active run or a 3.8M assignment expectation.
