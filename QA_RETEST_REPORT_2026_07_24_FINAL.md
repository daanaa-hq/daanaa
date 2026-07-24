# Final QA Retest Report — `eaed76598d4` plus follow-up fixes

Date: 2026-07-24
Scope: Current checkout on `master`, isolated local API worker, frontend test/build, and privacy checks
Deployment: None performed
Result: **Local implementation passes the reported functional blockers; production approval remains pending service restart and smoke testing.**

## Test results

| Area | Result | Evidence |
|---|---|---|
| Same seed produces same order | PASS | Isolated current `daanaa_api.py` worker returned the same 3 names for `test-seed-1` twice |
| Different seed produces different order | PASS | `test-seed-1` returned `NVAK INC`, `KNOWLEDGE RECOVERY FUND INTERNATIONAL`, `CHARLES & SYLVIA DAY CHARITABLE TR`; `different-seed` returned `HERD SPORTS INCORPORATED`, `PTA FLORIDA CONGRESS`, `SHEPHERDS DOOR INC` |
| Frontend sends random seed | PASS | `getOrganizations()` sends `sort=random` and `seed` |
| Show another list seed refresh | PASS in code review | `showAnotherCount` generates a new seed and is included in the results effect dependency list |
| Near me placeholder | PASS in code review | Click shows “Coming soon! For now, use a city name or ZIP code above.” and does not request geolocation |
| Frontend tests | PASS | 12 suites, 215 tests |
| Frontend build | PASS | TypeScript and Vite build completed in about 4 seconds |
| Privacy gate | PASS | All machine-checkable privacy invariants passed |

## Important environment finding

The pre-existing local service on port 5000 was still serving the older worker and returned identical results for different seeds. I started a temporary isolated worker on port 5002 from the current checkout. That worker passed the same-seed and different-seed contract.

Before any further QA conclusion or deployment, restart the normal local/staging service from the current commit and rerun:

```bash
curl "http://localhost:5000/api/organizations?sort=random&seed=test-seed-1&per_page=3"
curl "http://localhost:5000/api/organizations?sort=random&seed=different-seed&per_page=3"
```

Do not use a stale worker as production evidence.

## Remaining release gates

1. Restart the normal local or staging API service from the current commit.
2. Repeat the two-seed API test on that service.
3. Run the browser flow for three consecutive “Show another list” clicks.
4. Run read-only production smoke checks for `/`, `/directory`, `/discover`, `/health`, and the random API contract.
5. Obtain explicit founder approval before deployment or A/B testing.

## Conclusion

The code in the current checkout now supports the claimed seeded shuffle behavior, and the frontend follow-up seed fix is present. Local automated verification passes. This is **ready for staging or QA-team retest**, not yet a production deployment approval, because the normal service must be restarted and the public endpoints must be verified after that restart.

