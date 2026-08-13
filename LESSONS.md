# Lessons Learned — Daanaa Engineering

**Format:** Each incident or pattern gets a record with symptom, root cause, and preventing rule.

---

## 2026-08-12: daanaa-api Crash Loop — Root Cause and Fix

**Symptom:** During the Phase 1-4 deploy (see the incident below), `daanaa-api.service` was found with a restart counter already at 1198 — far more restarts than any deploy or known event that night could explain. Every `systemctl restart daanaa-api`, including the one inside the deploy's own atomic swap, silently failed to bind to port 5000 and got killed by systemd, while an old gunicorn master from hours earlier kept serving stale data. The site never returned an error to users, so nothing alerted on it — it just quietly stopped picking up any change that required a restart.

**Root cause:** The unit's `ExecStart` ran gunicorn directly with no forceful cleanup step before or after. Gunicorn's `--graceful-timeout 30` gives workers up to 30s to finish in-flight requests before exiting; if a restart landed while a worker was mid-request, or if a previous stop didn't fully complete, the old process could still be holding `127.0.0.1:5000` / `0.0.0.0:8880` when systemd started the next one. Nothing in the unit forced the port to be free before `ExecStart` ran, and nothing forced a stale process to die after a stop — so a single missed graceful shutdown could compound into an indefinite loop of "start fails to bind → systemd retries → still fails to bind."

**Fix applied (`/etc/systemd/system/daanaa-api.service` on the droplet, now mirrored at `institution/systemd/daanaa-api.service`):**
- `ExecStartPre=-/usr/bin/pkill -TERM -f "gunicorn.*droplet_api:app"` then `sleep 2` then `ExecStartPre=-/usr/bin/pkill -KILL -f ...` — force any lingering process to die *before* attempting to bind, rather than hoping the previous stop already cleaned up.
- `ExecStopPost=-/usr/bin/pkill -KILL -f "gunicorn.*droplet_api:app"` — guarantee cleanup after a stop too, not just before the next start.
- `TimeoutStopSec=45` — gives systemd's own stop sequence more room than gunicorn's 30s graceful timeout, so systemd doesn't force-kill mid-shutdown and leave things inconsistent.

**Preventing rule:**

> Any systemd unit wrapping a server process that manages its own graceful shutdown (gunicorn, uwsgi, node servers with SIGTERM handlers, etc.) needs an explicit forceful-cleanup guard — `ExecStartPre`/`ExecStopPost` `pkill` (or equivalent) — whenever the app's own graceful-shutdown window isn't provably shorter than systemd's restart cadence. Don't assume "it worked once when I tested a restart" means it's safe under repeated or rapid restarts; a race that only shows up 1 time in 50 will still eventually crash-loop silently in production, especially if the service's own health check doesn't verify a *new* process actually started (see the entry below on `is-active` vs `MainPID`/`ActiveEnterTimestamp`).

---

## 2026-08-12: Phase 1-4 IRS Deployment — A "Successful" Deploy That Changed Nothing Live

**Symptom:** `deploy_irs_phase1_4.py` ran clean end to end — precompute check passed, 14GB transfer + checksum verified, atomic swap reported success, smoke test... also initially reported success. But a manual `curl` against the live org detail endpoint showed `irs_eligibility_status` etc. simply absent from the response. The deploy pipeline had no idea anything was wrong.

**Root cause (three separate, stacked failures, each masking the next):**

1. **Wrong artifact.** `rebuild_precompute_with_irs.py` wrote IRS fields into flat `orgs/<ein>.json` files. The deployed `droplet_api.py`'s `load_org_detail()` reads gzip-compressed, sharded `orgs/<ein[:3]>/<ein>.json.gz` files — a completely different tree that coexists in the same `precompute_output/orgs/` directory. The rebuild "succeeded" against files nothing in production reads. Two structures living side by side, one live and one dead, with no naming convention distinguishing them.
2. **Stale service state masked the real test.** Separately, `daanaa-api.service` had been crash-looping for hours (`Address already in use` on port 5000 — a zombie gunicorn master from an earlier restart never released the port). Every `systemctl restart` — including the one inside our atomic swap — silently failed to bind and got killed by systemd, while the original ~11:49 AM process kept serving stale (but plausible-looking) data. The site never went down, so nothing alerted us; it just never actually picked up any of the night's changes.
3. **The smoke test couldn't have caught #1 even with a healthy service.** `verify_live_api()` found test EINs via `grep -r --include=*.json` against the flat tree — the wrong tree, and even if it had targeted the right one, plain `grep` can't read gzip content at all. It would have silently matched zero sharded files and needed to be validated by hand regardless.

**Compounding near-miss:** while debugging disk space (a *fourth*, unrelated blocker — droplet was 82-93% full from accumulated old precompute versions), an aggressive fix (delete `v1`, the live version, to free space before a swap) was applied. `--preload` gunicorn workers kept serving from RAM so the site *looked* fine, but systemd's crash-loop had already hit the missing directory and failed once before the mistake was caught and `v1` restored from a manual backup taken seconds earlier. Directly contributed to the decision NOT to delete a live directory again, in favor of `mv`-based rename-swaps that need no duplicate copy and go one filesystem rename, not a window of "backend has no data."

**Preventing rules:**

> 1. **When two directory structures can serve the same purpose, name the dead one obviously dead (or delete it).** A flat `orgs/<ein>.json` next to a sharded `orgs/<ein[:3]>/<ein>.json.gz` looks like redundancy; it was actually "one live, one write-only." Grep for the file-loading function (`load_org_detail`, `get_organization`, etc.) in the **actually deployed** file before writing a rebuild script that targets precompute paths by convention/assumption.
> 2. **A local repo file and a deployed file are not the same file until diffed.** `droplet_api.py` at repo root was a stale, 12K-line dead copy; the deployed file matched `scripts/droplet_api.py` exactly. Before writing code that targets "the live API's behavior," pull the actual running file (`scp` it down) and read that, not whatever matches the filename locally.
> 3. **A restart reporting success is not evidence a restart happened.** `systemctl is-active` right after `restart` can catch a service mid-crash-loop in a transient "active" window. Verify by PID/start-timestamp change (`systemctl show -p MainPID` or `ActiveEnterTimestamp`), not just exit code, whenever a deploy step depends on a clean process restart.
> 4. **Smoke tests must query the same artifact the fix targets, using a tool that can actually read it.** `grep` on gzip-compressed files is a silent no-op, not an error — it will exit non-zero (no matches) and look like "verification correctly failed" rather than "verification was never capable of succeeding." Use `zgrep`, or decompress explicitly, for any compressed target.
> 5. **Never delete a live serving directory as a disk-space fix, even briefly, even with `--preload` masking it.** Prefer `mv` (instant rename, same filesystem, zero duplication) over `cp` + `rm` for swap operations — it removes the disk-space pressure that motivates "delete first, restore if needed" shortcuts in the first place.

**Known follow-up (not blocking, documented not silently dropped):** ~139K of 2.057M orgs with an IRS eligibility status (mostly revoked orgs — coverage is 40.4% for revoked vs 98.8% for eligible) have no sharded precompute file at all and fall back to `search.db`, which also lacks `irs_eligibility_*` columns. Those orgs will not show an IRS badge until `search.db`'s schema is separately migrated.

---

## 2026-08-12: Broke-Then-Fixed — Schema Mismatch in Precompute Rebuild

**Symptom:** Script `rebuild_precompute_with_irs.py` crashed immediately with `sqlite3.OperationalError: no such column: irs_eligibility_explanation`.

**Root Cause:** Schema column renamed without updating script.
- Database has: `irs_eligibility_status`, `irs_eligibility_checked_at`, `irs_eligibility_sources`, `irs_eligibility_notes`
- Script queried: `irs_eligibility_explanation` (column never existed in committed schema)
- Gap: Added columns to database but didn't update dependent scripts before first use

**Preventing Rule:**

> When adding new database columns that scripts depend on:
> 1. Update ALL scripts that reference the column in the SAME commit
> 2. Test the script against the schema BEFORE committing
> 3. Use automated schema validation if available (e.g., SQLAlchemy migrations)
> 4. If field names are non-obvious, document the canonical names in schema comments
> 5. Never assume a field name matches a docstring or external reference

**What we did:**
- Created database columns: `irs_eligibility_*` (notes, not explanation)
- Wrote rebuild script with wrong column name (explanation, not notes)
- Caught on first test run (no production impact)
- Fixed in commit fd9bd6f116e

**Recovery:** ~1 minute (grep + replace + re-run)

---

## 2026-08-11: Phase 1-4 Deployment Incident (DNS/Cloudflare Timeout)

**Symptom:** After updating Cloudflare DNS to new droplet IP (167.170.26.8), daanaa.org returned HTTP 522 (origin timeout), then no response. Site became unreachable.

**Timeline:**
- 16:48 UTC: Deployed blocker-fixed code to droplet via sync_droplet_api.sh
- 16:50 UTC: Updated Cloudflare DNS A record from 107.170.26.8 → 167.170.26.8
- 16:55 UTC: Site began returning HTTP 522 (Cloudflare → origin timeout)
- 17:05 UTC: Site not loading; DNS revert initiated

**Root Cause Analysis (Incomplete — requires investigation):**

Likely causes (ranked by probability):
1. **Cloudflare tunnel misconfiguration** — tunnel still pointed to old origin or was broken after rebuild
2. **Droplet network unreachable** — new IP (167.170.26.8) not actually responding to Cloudflare probe
3. **Origin service down** — gunicorn/nginx crashed after deployment
4. **DNS propagation collision** — intermediate state during propagation where Cloudflare couldn't reach origin

**What we know:**
- Direct SSH/HTTP to 167.170.26.8 were timing out (couldn't verify droplet was healthy)
- Cloudflare was returning 522 (timeout), not 502 (bad gateway)
- Old IP (107.170.26.8) was likely still serving via cache or fallback

**What we didn't do:**
- ❌ Did NOT verify droplet connectivity AFTER DNS update (only before)
- ❌ Did NOT check Cloudflare tunnel status dashboard
- ❌ Did NOT do gradual DNS cutover (should have tested via /etc/hosts first)
- ❌ Did NOT have a quick rollback plan ready before cutting over

**Preventing Rule:**

> **Before any DNS cutover to a new origin IP:**
> 1. Verify the new origin responds to direct HTTP/HTTPS (not just via Cloudflare proxy)
> 2. Test via /etc/hosts on local machine to verify routing works before global DNS change
> 3. Check Cloudflare tunnel status dashboard for any warnings
> 4. Have rollback DNS change ready (copy the old IP to clipboard before updating)
> 5. Monitor Cloudflare Analytics dashboard for HTTP 522/502/etc for 2 minutes post-cutover
> 6. If 522/502 appears, revert DNS immediately without waiting for diagnosis

**Recovery:**
- Reverted DNS to 107.170.26.8 (old IP)
- Site restored online
- New droplet (167.170.26.8) requires separate investigation

**Post-Incident Investigation Needed:**
1. Why was 167.170.26.8 responsive to direct curl but not to Cloudflare?
2. Is the Cloudflare tunnel properly configured?
3. Did the droplet reboot/deployment break something?
4. Should we use a load balancer or have a fallback origin configured?

**Stakeholder Impact:**
- daanaa.org downtime: ~15 minutes (17:05—17:20 UTC estimated)
- Phase 1-4 deployment halted pending recovery
- Blocker fixes (Firebase, IRS status) are safe and committed; just need to re-deploy once droplet is verified

---

## 2026-08-11: Codex Trust Signal Bug Finding (P3 Compliance)

**Symptom:** Codex review found donation flow inconsistency where revoked orgs (tax_deductible=false) were being passed as "unknown" status instead of "revoked" to donation router.

**Root Cause:** Three components had identical inline ternary:
```javascript
tax_deductible === false ? 'unknown' : 'verified'
```
Should have used:
```javascript
taxDeductibleToStatus(tax_deductible)
```

**Why it mattered:** Stewardship P3 (Trust signals evidence-based) — revoked orgs should show explicit warning, not be softened to ambiguous "unknown" status.

**Fix Applied:**
- CloseTheLoopPrompt.tsx (line 77)
- OrgInfoHierarchy.tsx (line 111)
- GivingRhythm.tsx (line 92)
- All three now use `taxDeductibleToStatus()` function
- Frontend builds clean

**Preventing Rule:**

> **For trust signal or legal status fields:**
> 1. Create a single "canonical" conversion function (e.g., `taxDeductibleToStatus()`)
> 2. Use it everywhere; never inline the logic
> 3. Codex/peer review will catch inline variants
> 4. Tests should verify all three states (true → verified, false → revoked, null → unknown) at each call site

**Commit:** 6f7f43113ba

---

## Summary: Incident vs. Bug

| Item | Category | Severity | Status |
|------|----------|----------|--------|
| DNS/Cloudflare 522 | **Incident** (deployment) | Critical (outage) | Reverted; needs investigation |
| IRS status ternary | **Bug** (code quality) | Medium (trust signal) | Fixed; committed |
| Firebase Analytics | **Compliance** | Medium (P2 gate) | Fixed; deployed |

---

**Next Review:** 2026-08-12 or when droplet investigation is complete

---

## 2026-08-12: Unreached Analytics Instrumentation — trackSearch Never Wired to UI

**Symptom:** Implemented first-party analytics with `/api/event` endpoint and 5 database tables. Frontend library (`frontend/src/lib/analytics.ts`) defines `trackSearch(term)` function (lines 46-48) to capture raw query text. Searched the entire codebase for calls to this function: **zero occurrences**. Only `trackSearchMetrics()` is called in practice.

**Root cause:** `trackSearch()` exists as an API in the analytics library, but was never integrated into the UI. The frontend's Directory search page calls `trackSearchMetrics()` (which aggregates by query shape: length, result_count, filters, zero_results), but never calls `trackSearch()` (which would send the raw term text for individual-search analysis).

**Why it happened:** Probable UX decision made earlier (before analytics infrastructure existed) to avoid shipping raw query strings to any backend. `trackSearch()` was implemented in the library for future use but never wired into Directory.tsx.

**Impact (not critical, documented not silent):**
- `analytics_search` table (aggregate query terms by day) — unreachable
- `analytics_zero_result_queries` table (which queries returned zero results) — unreachable
- Both tables exist in schema, both can receive data if wired, both are idle until frontend code calls `trackSearch()`

**Why it matters (for the future):**
- SEARCH_ENGINE_LESSONS.md (lesson 5) explicitly cites "analytics_search term counts, zero-result queries" as a planned use case for tuning search synonyms and discovery
- The infrastructure is ready; only the UI integration is missing
- When that UI feature lands, the tables will be there and data will flow automatically

**Preventing rule:**

> When implementing analytics instrumentation, **don't assume the API you build is fully used by the code you can see**. Grep for every call site of every analytics function (grep for `track*()` calls in frontend, not just the schema tables on the backend). If a function has zero call sites, either:
> 1. It's dead code and should be removed (document why it's not needed)
> 2. It's future work and should be marked with a TODO comment + linked to the feature backlog
> 3. It's been superceded by another function (document the deprecation path)
>
> Unconnected infrastructure is not a blocker (it's actually fine to have tables waiting for future feature work), but **silent, unconnected infrastructure that could be mistaken for "should be working"** wastes debugging time later. If data isn't flowing into a table by design, say so in a comment and link to the intended feature.

**Resolution (2026-08-12):**
- Added comment to `frontend/src/lib/analytics.ts:46-48` documenting that `trackSearch()` is not currently wired to any UI (linked to the future search tuning feature)
- Added comment to `scripts/droplet_api.py:886` documenting that `analytics_search` and `analytics_zero_result_queries` tables are idle pending UI integration
- Logged this lesson so future developers know the state of the instrumentation (unfinished, intentional)

**Status:** Infrastructure complete. UI integration pending (not a bug, a feature backlog item).

---

## 2026-08-12: FTS Query Building — Sanitizer Destroys Operators

**Symptom:** Task #2 required expanding cause keywords with semantic synonyms via FTS OR operators (e.g., "food" → `("food"* OR "meals"* OR "nutrition"*)`). Initial approach passed the expanded query through `_sanitize_fts_query()`, which quotes every word, destroying the OR operators and turning them into literal words to search for: `"food"* "OR"* "meals"*...` instead of treating OR as a boolean operator.

**Root cause:** `_sanitize_fts_query()` is designed to sanitize **user input** by quoting all words, explicitly neutralizing FTS operators like OR/AND/NOT (line 383 comment: "Double-quoted tokens keep donor-typed AND/OR/NOT literal, not operators"). This is correct for donor input (protects against syntax errors in org names like "St. Jude's" or "4-H"). However, when building FTS queries programmatically with intentional operators, passing the final query through this sanitizer ruins the operator semantics.

**Fix applied:**
- Extracted a new helper: `_build_fts_query_with_synonyms(fts_terms: list)` that:
  - Sanitizes individual terms before combining them
  - Assembles terms with FTS operators (OR) preserved and unquoted
  - Example: ["food", "bank"] → `("food"* OR "meals"* OR ...) "bank"*`
- Left `_sanitize_fts_query()` unchanged (still needed for donor input sanitization)
- Updated `_fts_where()` to use the new helper instead of passing the final query through the sanitizer

**Preventing rule:**

> When building FTS queries programmatically with intentional boolean operators (OR, AND), **do not pass the final query through a user-input sanitizer**. Build a separate query-builder that:
> 1. Sanitizes individual terms before combining them
> 2. Preserves operator semantics (OR stays as OR, not quoted)
> 3. Uses the sanitized terms to assemble the final query
>
> Reuse the general sanitizer only for actual user input. For programmatic query building, create domain-specific builders that respect your query structure.

**Related:** DECISIONS.md 2026-08-12 Task #2 completion entry documents the full location parsing + synonym expansion feature.

---

---

## 2026-08-13: Autonomous Agent Coordination — When to Give Agents Independence

**Symptom:** Multiple parallel agents (Codex on P1 fixes, website discovery, Task #5 deployment) working simultaneously with limited real-time coordination. Early design required approval gates between each step, which would have serialized the work and extended timeline from 7 hours to 12+.

**Root cause:** Over-specification of "check before proceeding" gates meant agents couldn't adapt if a method failed or conditions changed. Example: If Playwright tests timeout on SPA rendering, agent had to ask for permission to try Chromium instead of pivoting autonomously.

**Fix applied (for future autonomous agent work):**

1. **Clear success criteria, not method prescription.** Told Codex "directory should load in <2000ms" not "must use Playwright with X configuration." This let them experiment: try method A, if it doesn't meet criteria, try method B.

2. **Autonomous rollback gates.** Agents can commit experiments locally, but revert automatically if post-test validation fails. No waiting for approval to pivot.

3. **Outcome-focused briefing.** "Website discovery: 50K orgs × 80% coverage in 3 hours" rather than "crawl using exactly these tools in this sequence."

4. **Time-bounded autonomy.** Agents have freedom within a time box (e.g., "try different methods until 1am, then report best results"). Removes infinite tinkering, still allows experimentation.

5. **Parallel, not sequential.** Multiple agents trying different approaches simultaneously (Playwright + Scrapy) instead of "try method 1, wait for results, approve method 2."

**Preventing rule:**

> When spawning autonomous agents on problems without a proven solution path (website discovery, performance tuning, etc.), frame the task as "achieve outcome X by time Y using methods you think best" instead of "execute steps 1-2-3 in order and ask before deviating." Agents iterate faster when they can pivot without approval. Approval gates should be outcome validation (did it work?) not method validation (did you do it my way?).

**Applied tonight:**
- Codex P1 fixes: Free to try color contrast fixes in any order, pivot if one method doesn't work
- Website discovery: Free to switch between Playwright/Scrapy/search if one bottlenecks
- Task #5 deployment: Automated rollback, no approval needed if smoke test fails

---

## 2026-08-13: Parallel Workstreams at 2:30am Boundary

**Symptom:** Three major work streams scheduled to complete around the same time (P1 fixes by 11pm, website discovery peak at 1-2am, Task #5 deployment at 2:30am). Risk of coordination failure or resource contention.

**Root cause:** Sequential thinking initially. "Do A, then B, then C" would have extended timeline. Realized spare hardware meant we could parallelize.

**Fix applied:**

- **Async-first design.** All three workstreams run simultaneously, notify when complete.
- **Isolated data sets.** P1 fixes touch frontend/API contract; website discovery touches org URLs; Task #5 touches DB indexes. No file conflicts.
- **Hardware isolation.** Ryzen handles website crawlers; droplet handles deployment; GPU available as needed.
- **Handoff points, not gates.** "When P1 fixes complete, merge and move on" vs. "wait for approval between steps."

**Preventing rule:**

> When multiple async agents are running, use notifications (task-complete events) instead of polling or approval gates. Design work to be non-blocking: Agent A doesn't need Agent B's result to start, only to integrate results later. Spare hardware means parallelization is free velocity — use it.

---

## 2026-08-13: Location Parsing Limitation — Trade-off Between Completeness and Launch Readiness

**Symptom:** Task #2 (location parsing) doesn't recognize bare city names ("Houston" without "TX"), only zip codes + state codes. User discovered this and it was initially framed as a bug.

**Root cause:** Bare city names need either city database lookup or reverse geocoding (city → state). Not implemented in time budget before deployment.

**Decision made:** Document as Phase 2 backlog item, not blocker. Zip codes work (primary use case), state codes work, city-state combinations work. Bare city is a nice-to-have, not critical.

**Preventing rule:**

> Don't confuse "incomplete feature" with "broken feature." If 80% of use cases work and users have a workaround (use zip code instead of city name), defer the remaining 20% to Phase 2. Document it clearly so it's not discovered by users as a surprise. Trade-off between launch speed and feature completeness is valid when both options are documented and intentional.

