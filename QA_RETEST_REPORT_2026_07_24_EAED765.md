# QA Retest Report — Commit `eaed76598d4`

Date: 2026-07-24
Scope: Local checkout on `master`
Deployment: None performed
Overall result: **Not ready for founder approval or deployment**

## Executive result

The frontend build, automated tests, privacy gate, and “Near me” placeholder behavior pass. The core random sort contract does not pass in the checked-out API source, and the QA summary does not match the source currently available in `scripts/droplet_api.py`.

## Results

| Test | Result | Evidence |
|---|---|---|
| Same seed reproducibility | Not certified | API random branch is absent in checked-out backend source |
| Different seeds produce different order | FAIL | Local API returned `ZZYZX FOUNDATION` first for both `retest-one` and `retest-two` |
| “Show another list” no immediate exhaustion | PASS in code review | `showAnotherCount` increments and is a fetch dependency |
| “Show another list” fresh candidates | Not fully certified | Freshness depends on the backend random seed contract, which currently fails |
| “Near me” permission prompt | PASS in code review | Handler only sets the coming-soon message and does not call geolocation |
| “Near me” fallback | PASS in code review | City and ZIP input remain available |
| Frontend tests | PASS | 12 suites, 215 tests |
| Frontend build | PASS | TypeScript and Vite build completed |
| Privacy gate | PASS | Machine-checkable privacy invariants passed |

## Blocking finding: source mismatch

The QA summary states that `droplet_api.py` contains an in-memory seeded shuffle implementation. In the checked-out repository, `scripts/droplet_api.py` still contains:

- `_order_clause()` branches for revenue and merit score only
- A default alphabetical `organization_name` order
- No `sort == 'random'` branch
- No `seed` handling
- No `random.Random(seed).shuffle(...)` implementation

The checked-out source therefore cannot satisfy:

```text
same filters + same seed → same ordered list
same filters + different seed → different ordered list
```

The frontend does include the seed parameter in `frontend/src/data/api.ts`, but that alone cannot change backend ordering.

## Guided discovery findings

### “Show another list”

The previous immediate exhaustion bug is corrected structurally. `showAnotherCount` is included in the results effect dependency list, and clicking the button increments it. However, the effect currently fetches the same API request without passing a new discovery seed or page/window parameter. It will only produce a different list after the backend or frontend adds a varied seed to that request.

### “Near me”

The new behavior matches the stated placeholder requirement. It shows:

```text
Coming soon! For now, use a city name or ZIP code above.
```

No browser geolocation permission is requested. This is correctly a deferred feature, not a working proximity search.

## Verification commands

```text
npm test -- --runInBand       PASS: 215 tests
npm run build                 PASS
bash scripts/privacy_check.sh PASS

# Local API smoke test
curl ...sort=random&seed=retest-one  → ZZYZX FOUNDATION
curl ...sort=random&seed=retest-two  → ZZYZX FOUNDATION
```

## Required next action

1. Reconcile the source mismatch. Confirm whether the random backend implementation is in another file, generated artifact, or deployment-only tree.
2. Make the canonical checked-out API implement seeded random ordering.
3. Pass a new seed or candidate window when `showAnotherCount` changes.
4. Run the same-seed and different-seed API tests against the actual process started from that source.
5. Only then rerun the full QA plan and seek founder approval.

