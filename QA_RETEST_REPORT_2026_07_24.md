# QA Retest Report — Shuffle and Guided Discovery Fixes

Date: 2026-07-24
Scope: Local code and API retest after commits `ffcd0afc8de`, `e6a2dde2725`, and `089a245f76c`
Deployment: None performed
Overall result: **Not ready for founder approval or deployment**

## Summary

The frontend build, automated tests, and privacy gate pass. The reported fixes are not complete end to end. Shuffle still does not vary by seed in the running local API, “Near me” does not yet affect the query, and “Show another list” has a logic error that makes the first follow-up request empty.

## Retest results

| Issue | Result | Evidence |
|---|---|---|
| Seed added to frontend API URL | PASS | `frontend/src/data/api.ts` includes `sp.set('seed', params.seed)` |
| Backend random sort | FAIL | `scripts/droplet_api.py` `_order_clause()` has no `random` branch and falls back to organization name |
| Different shuffle seeds | FAIL | `retest-one` and `retest-two` both returned `ZZYZX FOUNDATION` first |
| ZIP/city input | PARTIAL PASS | Input and `custom-zip:value` state exist; API resolution still needs end-to-end test |
| State selector | PASS | State values are encoded as `custom-state:XX`; all 50 states appear in the selector |
| Near me | FAIL | Browser permission is requested, but coordinates are discarded and state remains `near-me`; `mapToDirectoryFilters` sends no `near` value |
| Show another list | FAIL | Initial results are all added to `shownOrgs`; handler filters the current `results`, so `newCandidates` is immediately empty |
| Randomize it button | PARTIAL | Button changes the frontend seed and triggers refetch, but backend seed behavior remains unverified and currently fails locally |
| Frontend tests | PASS | 12 suites, 215 tests |
| Frontend build | PASS | TypeScript and Vite build completed |
| Privacy gate | PASS | Machine-checkable privacy invariants passed |

## Remaining defects

### P0: Backend random ordering is still absent

The frontend contract is ahead of the backend. Passing `seed` is not enough. The API must use the seed to produce a deterministic order, and different seeds must produce different orders.

Required test contract:

```text
same filters + same seed → same ordered EIN list
same filters + different seed → different ordered EIN list
same filters + no seed → documented default behavior
```

The implementation must work across pages and filtered results, not only within the first page.

### P1: “Show another list” cannot produce a new list

The initial fetch does this:

```text
allResults → shownOrgs
```

The next action does this:

```text
results - shownOrgs → empty
```

The fix needs to retain a larger candidate pool, request another page/window, or fetch again with a new seed. It must not filter the currently displayed list after marking every displayed item as already shown.

### P1: “Near me” is permission-only, not location-aware

The browser obtains latitude and longitude but does not use them. The current code comment confirms this is unfinished. Choose one safe implementation:

- Resolve the coordinates to a coarse city/state or ZIP and pass only that coarse location; or
- Add a backend proximity contract that accepts the coordinates securely and does not retain them.

Do not persist precise coordinates or place them in analytics or shareable URLs.

## Recommended next steps

1. Implement and unit test backend seeded random ordering.
2. Retest two seeds against the actual API process after restarting the local service with the updated source.
3. Fix `Show another list` using a larger candidate pool or a new API request.
4. Complete or temporarily disable `Near me` until it changes results correctly.
5. Add guided discovery tests for URL encoding, location mapping, shortlist limits, and repeat-list behavior.
6. Re-run production smoke checks only after the public service is reachable.
7. Obtain founder approval before deployment or A/B testing.

