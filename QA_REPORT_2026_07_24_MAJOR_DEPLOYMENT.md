# QA Report — Major Deployment Audit

Date: 2026-07-24
Scope: Current `master` checkout and read-only production smoke tests
Deployment: No changes made by QA
Overall status: **Production is reachable, but release gaps remain. Do not treat this as a clean pass.**

## What was checked

Recent commits cover:

- seeded/random directory behavior and performance changes
- revenue presence filtering and revenue sort
- removal of the primitive `/discover` guided page
- discovery component theme and routing cleanup
- existing event, volunteer, organization, and protected dashboard routes

## Results

| Area | Result | Evidence |
|---|---|---|
| Production homepage | PASS | HTTP 200, about 109 ms |
| Production directory | PASS | HTTP 200, about 113 ms |
| Production volunteer page | PASS | HTTP 200, about 110 ms |
| Production health endpoint | PASS | HTTP 200, about 97 ms |
| Frontend automated tests | PASS | 12 suites, 215 tests |
| Frontend build | PASS | TypeScript and Vite build completed locally in about 4 seconds |
| Privacy gate | PASS | All machine-checkable privacy invariants passed |
| Production random seed behavior | FAIL | Different seeds returned the same first three organizations in alphabetical order |
| Production search latency | FAIL | `/api/search?q=health&per_page=5` returned HTTP 200 in 8.70 seconds |
| Production revenue presence filter | FAIL | `has_revenue=1` response included organizations with `total_revenue: null` |
| Primitive guided discovery route | EXPECTED 404 | `/discover` returns 404 after intentional removal |
| Home guided discovery handoff | GAP | Home still says “Not sure where to begin?” but provides no working action after `/discover` was removed |
| Protected nonprofit dashboard | PASS | Unauthenticated request returned 401 |
| Organization detail API | PASS | `/api/organizations/832672211` returned 200 |
| Volunteer event index | PASS | `/api/volunteer-events` returned 200 and listed four events |
| Event detail API | FAIL | `/api/events/2` returned 404 even though event 2 appears in `/api/volunteer-events` |
| Event page shell | PARTIAL | `/event/2`, `/events/2`, and event subpage shells returned 200, but the event data API is 404 |

## Blocking findings

### 1. Production random sort is not deployed or not active

Production returned the same list for `seed=qa-one` and `seed=qa-two`:

```text
0 TIENOU TI DIERO BAAFIRI
004TH DISTRICT COMMUNITY YOUTH AND RETIREMENT ORGANIZATION
02 SCHOLARSHIP FUND INC
```

The current checkout contains seeded shuffle code in the canonical root `droplet_api.py`, but the public API behavior does not reflect it. Possible causes include an older production API process, the wrong API upstream, or the home `daanaa_api.py` being exposed instead of the canonical droplet API.

### 2. Production search is too slow

`/api/search?q=health&per_page=5` returned 200 but took approximately 8.7 seconds. This fails the stated sub-second user experience target and needs profiling before further visibility work.

### 3. Revenue filter is not active in production

`/api/organizations?per_page=3&has_revenue=1` returned records including `total_revenue: null`. The frontend and current local source include the filter, so production is likely serving an older API build or route.

### 4. Event detail data is inconsistent

The public event index lists event 2 as:

```text
Volunteer Support Opportunities: AKF Houston Golf Tournament 2026
```

But `/api/events/2` returns 404. The event page shell loads, which can create a blank or misleading page for users. This should be fixed or the event shell should fail clearly with a user-facing message.

### 5. Home page has a dead discovery invitation

The primitive `/discover` route was removed, but the home page still presents the question “Not sure where to begin?” without a button or alternate action. Either:

- remove that block until guided discovery returns, or
- replace it with a working link to `/directory` and clear language such as “Browse causes and organizations.”

## Production release recommendation

Do not run the planned A/B test or announce the deployment as complete yet. First:

1. Confirm which API service and commit production is running.
2. Restart or deploy the canonical API code through the approved release process.
3. Re-test seeded random ordering and `has_revenue=1` publicly.
4. Profile and correct the 8.7 second search path.
5. Repair the event detail route/data contract.
6. Remove or reconnect the home discovery block.
7. Run the health and smoke suite again, then obtain founder approval.

## Preservation note

The working tree contains an existing user modification to `frontend/public/research-snapshot.json`. QA did not modify or revert it.

