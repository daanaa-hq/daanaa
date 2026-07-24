# Fix status: Local integration fixes implemented; production deployment still pending explicit approval.
# Daanaa Production Integration QA Audit

Date: 2026-07-24
Scope: Read-only verification after recent droplet deployments
Environment: https://daanaa.org

## Executive result

Local code and tests are healthy, and the public search and event listing flows respond. Production is not yet an integrated release because the deployed frontend and backend do not contain the same route set.

## Passing checks

- `GET /` → HTTP 200
- `GET /health` → HTTP 200, status `ok`
- `GET /api/search?q=food%20bank&limit=3` → HTTP 200 with search results
- `GET /api/organizations/391214392` → HTTP 200 with organization data
- `GET /api/volunteer-events` → HTTP 200 with 4 active events
- `GET /api/volunteer-events?state=TX` → HTTP 200
- Public frontend routes `/`, `/events/2`, `/volunteer`, and `/nonprofit` → HTTP 200
- Local backend regression and integration tests → 81 passed
- Local frontend tests → 215 passed
- Local frontend production build → passed
- Privacy invariant check → passed
- Backend module compilation → passed

## Production failures

### 1. Event list and event detail use different deployed route coverage

The public event list includes event ID 2, but:

- `GET /api/events/2` → HTTP 404 `Not found`
- `GET /api/organizations/391214392/volunteer-events` → HTTP 404 `Not found`

The local source contains the event detail and organization event routes. The list endpoint does not define an item route; the detail contract is GET /api/events/<id>. The failures above indicate deployment drift or an API process mismatch, not a local test failure. A volunteer can discover an event but cannot reliably open its API-backed detail or organization event view.

### 2. Profile Contexts are not deployed on the public frontend or API

- `GET /profile-contexts` → HTTP 404
- `GET /api/profile-contexts` → HTTP 404

The expected safe-disabled behavior from the local source is HTTP 403 when the feature flag is off. A 404 indicates the deployed route set is older or the request is reaching a different service.

### 3. Protected admin routes fall through to frontend HTML

- `GET /api/admin/intent/summary` → HTTP 200 with `index.html`
- `GET /api/admin/discovery/queue` → HTTP 200 with `index.html`

These should reach the API and return an authentication or feature-gate response, not frontend HTML. This can hide missing backend routes and may cause confusing client behavior.

## Local source alignment

The local branch contains:

- `GET /api/events/<event_id>`
- `GET /api/org/<ein>/volunteer-events`
- Profile Contexts API routes
- Intent and event discovery admin routes
- Frontend route `/profile-contexts`

Therefore the next action is deployment alignment, not a new feature build.

## Recommended developer action

1. Identify which API process and frontend artifact serve `daanaa.org`.
2. Confirm the deployed commit for both services.
3. Deploy the same approved commit containing the event detail and Profile Context routes.
4. Keep `ENABLE_PROFILE_CONTEXTS`, `ENABLE_INTENT_SIGNALS`, and `ENABLE_EVENT_DISCOVERY` disabled unless separately approved.
5. Configure the API proxy so `/api/*` never falls through to `index.html`.
6. Re-run the endpoint matrix above.
7. Only then perform authenticated Firebase QA for profile contexts and nonprofit workflows.

No production changes were made during this audit.
## Local fixes completed
- Added droplet proxy routes for event detail, profile contexts, intent, and discovery.
- Added profile contexts to the SPA allowlist.
- Added event detail and profile context routes to frontend deployment smoke coverage.
- Backend tests: 81 passed.
- Frontend tests: 215 passed.
- Frontend build, deployment syntax, compilation, and privacy checks: passed.
