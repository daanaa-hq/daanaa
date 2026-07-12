# Weekly Institutional Review - 2026-07-11

## Document Control

| Field | Value |
|---|---|
| Purpose | Manual weekly institutional review generated from local repository evidence. |
| Responsible role | Stewardship Systems Agent. |
| Authority level | Evidence snapshot and recommendation; not approval. |
| Review trigger | Next manual cycle, material incident, or sourced founder update. |
| Editable status | Generated artifact; corrections should be appended or regenerated. |
| Dependencies | `scripts/institution_weekly_review.py`, local repo, local SQLite DB, local process state. |
| Retirement condition | Retire when superseded by a better dated review. |

## Current State

- Branch status command: ok.
- Git state:
```text
## master...origin/master
 M daanaa_api.py
 M frontend/public/research-snapshot.json
 M institution/CONTINUOUS_IMPROVEMENT.md
 M institution/library/010_global_principles.md
 M precompute_output/cohort_context.json
 M precompute_output/content/about.json.gz
 M precompute_output/content/faqs.json.gz
 M precompute_output/content/guides.json.gz
 M precompute_output/content/homepage.json.gz
 M precompute_output/content/how_it_works.json.gz
 M precompute_output/content/legal.json.gz
 M precompute_output/content/methodology.json.gz
 M precompute_output/content/sector_health.json.gz
 M tests/conftest.py
 M tests/test_droplet_claim_proxy.py
 M tests/test_droplet_search.py
 M tests/test_merit_scorer_v5_0.py
 M tests/test_org_activity.py
?? AGENTS.md
?? frontend/eslint.config.js
?? institution/library/timeout
?? scripts/institution_weekly_review.py
?? tests/test_concierge_confirm.py
```
- Recent commits:
```text
252d41c3d8f docs: founder rulings folded into library drafts 007/009/010 (v0.2)
5fc5308962c docs: institutional library, Steward Charter, and governance corpus
31a5f5c0f6f feat: weekly token-usage review on home server (Mon 8am cron)
fdda4aaf180 fix: unknown /api/* paths return JSON 404, never the SPA shell
0aafd4b7f18 fix: scraper benchmark harness measured the wrong thing - repair + verdict
```
- Current diff summary:
```text
daanaa_api.py                                   | 229 +++++++++++++++++++-----
 frontend/public/research-snapshot.json          |   2 +-
 institution/CONTINUOUS_IMPROVEMENT.md           |   4 +-
 institution/library/010_global_principles.md    |  11 +-
 precompute_output/cohort_context.json           |   2 +-
 precompute_output/content/about.json.gz         | Bin 189 -> 189 bytes
 precompute_output/content/faqs.json.gz          | Bin 399 -> 399 bytes
 precompute_output/content/guides.json.gz        | Bin 317 -> 317 bytes
 precompute_output/content/homepage.json.gz      | Bin 1245 -> 1245 bytes
 precompute_output/content/how_it_works.json.gz  | Bin 441 -> 441 bytes
 precompute_output/content/legal.json.gz         | Bin 209 -> 209 bytes
 precompute_output/content/methodology.json.gz   | Bin 808 -> 808 bytes
 precompute_output/content/sector_health.json.gz | Bin 2856 -> 2856 bytes
 tests/conftest.py                               |   6 +-
 tests/test_droplet_claim_proxy.py               |  15 +-
 tests/test_droplet_search.py                    |  24 ++-
 tests/test_merit_scorer_v5_0.py                 |  15 ++
 tests/test_org_activity.py                      |   6 +-
 18 files changed, 257 insertions(+), 57 deletions(-)
```
- Validation summary:
  - `py_compile`: pass
  - `pytest_core`: pass
  - `pytest_claim`: pass
  - `frontend_lint`: pass
  - `frontend_tests`: pass
  - `frontend_build`: pass
- Local services snapshot:
```text
2436 /home/akbar/warehouse/llama-swap --config /home/akbar/warehouse/config.yaml --listen 127.0.0.1:8080
2437 /usr/local/bin/ollama serve
3505 java -XX:+IgnoreUnrecognizedVMOptions -Dfile.encoding=UTF-8 -Dlogfile.path=target/log -XX:+CrashOnOutOfMemoryError -server --add-opens java.base/java.nio=ALL-UNNAMED -jar /app/metabase.jar
3917 node /usr/local/bin/n8n
4164 /home/akbar/meritgiving/venv/bin/python3 /home/akbar/meritgiving/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 -b 0.0.0.0:8880 --timeout 120 --preload --access-logfile /home/akbar/meritgiving/logs/gunicorn_access.log --access-logformat %(t)s "%(r)s" %(s)s %(b)s %(M)sms --error-logfile /home/akbar/meritgiving/logs/daanaa_api.log --pid /home/akbar/meritgiving/logs/daanaa_api.pid daanaa_api:app
5887 node --disallow-code-generation-from-strings --disable-proto=delete /usr/local/lib/node_modules/n8n/node_modules/.pnpm/@n8n+task-runner@file+packages+@n8n+task-runner_@opentelemetry+api@1.9.0_@opentelemetry_bd25ea1f047b3163759a25985b9c52da/node_modules/@n8n/task-runner/dist/start.js
7123 /usr/local/bin/cloudflared tunnel --config /home/akbar/.cloudflared/config.yml run
7129 /usr/bin/cloudflared --no-autoupdate --config /etc/cloudflared/config.yml tunnel run
7610 /home/akbar/meritgiving/venv/bin/python3 /home/akbar/meritgiving/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 -b 0.0.0.0:8880 --timeout 120 --preload --access-logfile /home/akbar/meritgiving/logs/gunicorn_access.log --access-logformat %(t)s "%(r)s" %(s)s %(b)s %(M)sms --error-logfile /home/akbar/meritgiving/logs/daanaa_api.log --pid /home/akbar/meritgiving/logs/daanaa_api.pid daanaa_api:app
7611 /home/akbar/meritgiving/venv/bin/python3 /home/akbar/meritgiving/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 -b 0.0.0.0:8880 --timeout 120 --preload --access-logfile /home/akbar/meritgiving/logs/gunicorn_access.log --access-logformat %(t)s "%(r)s" %(s)s %(b)s %(M)sms --error-logfile /home/akbar/meritgiving/logs/daanaa_api.log --pid /home/akbar/meritgiving/logs/daanaa_api.pid daanaa_api:app
7612 /home/akbar/meritgiving/venv/bin/python3 /home/akbar/meritgiving/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 -b 0.0.0.0:8880 --timeout 120 --preload --access-logfile /home/akbar/meritgiving/logs/gunicorn_access.log --access-logformat %(t)s "%(r)s" %(s)s %(b)s %(M)sms --error-logfile /home/akbar/meritgiving/logs/daanaa_api.log --pid /home/akbar/meritgiving/logs/daanaa_api.pid daanaa_api:app
7613 /home/akbar/meritgiving/venv/bin/python3 /home/akbar/meritgiving/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 -b 0.0.0.0:8880 --timeout 120 --preload --access-logfile /home/akbar/meritgiving/logs/gunicorn_access.log --access-logformat %(t)s "%(r)s" %(s)s %(b)s %(M)sms --error-logfile /home/akbar/meritgiving/logs/daanaa_api.log --pid /home/akbar/meritgiving/logs/daanaa_api.pid daanaa_api:app
```
- Local model inventory:
```text
NAME                        ID              SIZE      MODIFIED    
mxbai-embed-large:latest    468836162de7    669 MB    6 weeks ago
```

## Mission Alignment

Advanced the mission:

- Preserved free public discovery behavior while strengthening the stewardship layer around it.
- Added explicit authority ordering, durable handoff rules, and machine-readable operating state.
- Kept work local-only, no-spend, and reversible.

Did not materially advance the mission:

- Unverified financial and provider-console unknowns remain unresolved.
- No new representative nonprofit user evidence was gathered in this cycle.

Mission drift check:

- No evidence of growth-over-trust drift in this cycle.
- Risk remains where analytics/privacy docs conflict or where public copy may overstate certainty.

## User Experience

Verified user-signal surfaces exist for search, claims, feedback, view events, and wallet analytics tables.

Current friction still visible from institutional records:

- Search-result explanation can confuse users in some modes.
- Missing revenue can be misread as poor performance.
- Wallet/privacy documentation is not fully consistent.
- Hardcoded or unsourced public claims remain a trust risk.

Known aggregate signal counts:

| Signal | Count |
|---|---:|
| analytics_daily | 78 |
| analytics_search | 0 |
| feedback | 0 |
| v5_feedback | 1 |
| org_claims | 3 |
| org_interest | 3 |
| org_view_events | 125 |
| wallet_analytics | 0 |

Uncertain or unavailable:

- Support email volume is not available from a verified local export.
- Representative nonprofit interview or advisory evidence is still missing.
- Cloud/API usage is not available from a local source of truth.

## Highest Constraint

Recent backend search failures are a higher immediate constraint than the remaining institutional unknowns.

Evidence:

- Sampled daanaa_api log still contains recent /api/search exceptions tied to v4 schema drift
- R-013 is open in the institutional risk register
- Current automated checks do not directly exercise the failing search path against the live backend

## Options

1. Lowest-cost option: keep the institutional loop manual and verify whether the logged search failures still reproduce on the current backend.
   - Benefit: confirms whether the risk is stale or active before broader work.
   - Cost: local engineering time only.
   - Risk: low.

2. Balanced option: add a targeted `/api/search` regression test around the schema-drift path and re-run the weekly review after verification.
   - Benefit: turns a log-discovered risk into a durable guardrail.
   - Cost: local engineering time only.
   - Risk: low and reversible.

3. Higher-investment option: expand observability around backend runtime failures before confirming the specific search-path regression.
   - Benefit: broader telemetry.
   - Cost: more engineering work and more moving parts.
   - Risk: medium because instrumentation can outpace the specific repair need.

## Stewardship Deliberation

- Mission Steward: favors the balanced option because broken search directly harms nonprofit discovery.
- Small Nonprofit Executive Director: wants search reliability fixed before more institutional overhead is added.
- Nonprofit Finance And Compliance Representative: sees no cost blocker to a local regression test and prefers proof over assumption.
- Donor And Funder Representative: treats search correctness as a trust signal because it shapes which nonprofits people can find.
- Product And User Experience Representative: sees repeated search errors as user-facing breakage that should outrank internal unknowns.
- Technology And Data Representative: supports converting the log finding into direct test coverage on the live backend path.
- Security And Privacy Representative: prefers a local verification/test fix over adding new telemetry.
- Legal And Regulatory Issue-Spotter: sees no new regulatory exposure in local reliability verification.
- Financial Sustainability Representative: favors the balanced option because it is low-cost and reduces wasted debugging later.
- Ethics And Human Dignity Representative: notes that a broken search path can invisibly suppress nonprofits, which is a fairness concern.
- Devil's Advocate: warns that the log sample may be stale if the code was already fixed but not re-exercised.
- Long-Term Continuity Representative: supports closing or confirming R-013 with evidence before the loop shifts attention elsewhere.

Minority view: the Devil's Advocate argues for a quick reproduction check first so the institution does not over-prioritize an already-fixed error based only on old log lines.

## Recommended Action

- Action: Verify the current /api/search path against the live backend shape and add targeted regression coverage before treating the reliability risk as closed.
- Expected benefit: restore confidence that the core search path works and cannot silently regress on the same schema-drift class.
- Cost: local engineering time only; no new service or spend.
- Risk: low.
- Reversibility: high; config-only and testable.
- Evidence: recent log evidence, open R-013, and absence of direct coverage on the live backend search path.
- Confidence: medium.
- Success measure: the failing search path is either reproduced and covered by a regression test or proven clean with updated evidence, and R-013 can be narrowed accordingly.
- Stop condition: stop if the verification shows the log evidence is stale and no current search failure reproduces.
- Human approval requirement: none for local-only config repair; deployment remains approval-gated.

## Financial And Infrastructure Stewardship

- Default budget posture: survival.
- Known recurring cost from repo evidence: documented DigitalOcean droplet resize to $16/mo, not billing-verified.
- GPU capacity: unknown from durable local telemetry.
- CPU capacity: unknown from durable local telemetry.
- Suitable local workloads: embeddings, mission drafting, routine extraction/summarization where privacy allows.
- Suitable cloud workloads: only high-value reasoning where explicitly permitted and justified.
- Data that must remain carefully controlled: private nonprofit operational data, sensitive claims information, and any consequential legal/financial judgments.

## Security, Reliability, And Documentation Notes

- Recent sampled logs:
- logs/daanaa_api.log: 13 flagged lines; sqlite3.OperationalError: no such column: v4.peer_cell_size; [2026-07-10 15:58:15,376] ERROR in app: Exception on /api/search [GET]; Traceback (most recent call last):;     rv = self.handle_user_exception(e); sqlite3.OperationalError: no such column: v4.peer_cell_size
- logs/embed_server.log: 0 flagged lines; no flagged lines in sampled tail
- logs/nightly_search_deploy.log: 0 flagged lines; no flagged lines in sampled tail
- Bootstrap unresolved risks remain open in `institution/RISK_REGISTER.md`, especially R-001 through R-006 and R-010 through R-012.
- No secrets were added by this workflow; institutional files remain local repo content only.

## Kill And Simplification Review

- Stop: adding more skills before repeated work demonstrates need.
- Delete: nothing in this cycle; no safe deletion candidate was verified.
- Merge: keep coordination in `institution/HANDOFF_PROTOCOL.md` plus `institution/tasks/` instead of adding another tracker.
- Automate later: scheduling the weekly review only after one more clean manual cycle.
- Return to manual: financial intake remains manual until verified founder inputs exist.
- Paid tool no longer justified: none newly identified from local evidence.
- Feature lacking evidence: broader telemetry expansion beyond existing first-party signals.
- Document lacking purpose: none newly identified inside the institutional layer.

## Founder Dependencies

```text
# Founder Requests

## Document Control

| Field | Value |
|---|---|
| Purpose | Queue only decisions or inputs the institution cannot responsibly determine alone. |
| Responsible role | Stewardship Systems Agent. |
| Authority level | Request queue; not approval by itself. |
| Review trigger | Weekly review, blocked work, or new approval-gated decision. |
| Editable status | Editable by ordinary agents. |
| Dependencies | `GOVERNANCE.md`, `BUDGET_STATE.md`, `RISK_REGISTER.md`. |
| Retirement condition | Retire when replaced by an authenticated task/approval system. |

## Queue

### FR-2026-07-10-001: Confirm Current Monthly Spend And Runway

- Decision or input needed: Current cash, committed monthly costs, runway, and any services that are paid or trial-ending.
- Why Daanaa cannot determine it safely: Billing consoles and bank data are not in the repo and must not be guessed.
- Recommended default: Operate under survival scenario until confirmed.
- Alternatives: Responsible growth scenario if runway and committed revenue justify it.
- Expected impact: Prevents uncontrolled recurring cost and supports funding prioritization.
- Risk of delay: Moderate; spending decisions remain constrained.
- Required founder time: 15-30 minutes.
- Deadline: Before approving any new paid service or infrastructure upgrade.
- Can work continue: Yes, with no new spending.

### FR-2026-07-10-002: Confirm TiDB Credential Rotation

- Decision or input needed: Whether the leaked TiDB/Aliyun credential noted in `SECURITY_NOTES.md` has been rotated.
- Why Daanaa cannot determine it safely: Requires provider console access.
- Recommended default: Treat as unrotated until confirmed.
- Alternatives: If pipeline is unused, rotate then retire related legacy code.
- Expected impact: Reduces credential-history risk before any public repo exposure.
- Risk of delay: High if credential is still valid.
- Required founder time: 10-20 minutes.
- Deadline: Before repository is made public or shared widely.
- Can work continue: Yes, avoiding use of TiDB paths.

### FR-2026-07-10-003: Clarify Approval Model Conflict

- Decision or input needed: Whether Codex should follow the new stricter bootstrap rule requiring approval for production deployment, even where older `CLAUDE.md` says backend deploy is autonomous.
- Why Daanaa cannot determine it safely: This changes operational authority.
- Recommended default: Use stricter approval rule until explicitly narrowed.
- Alternatives: Delegate specific deploy scripts after proven smoke/rollback and human sign-off.
- Expected impact: Reduces production incident risk while stewardship layer is new.
- Risk of delay: Low; safe local work can continue.
- Required founder time: 5 minutes.
- Deadline: Before any production deployment.
- Can work continue: Yes.

### FR-2026-07-10-004: Confirm Offsite Backup Status

- Decision or input needed: Whether `rclone` or another offsite backup target is configured and recently verified.
- Why Daanaa cannot determine it safely: Repo notes say offsite may be no-op; actual remote config may be outside repo.
- Recommended default: Treat offsite backup as not verified.
- Alternatives: Google Drive, S3, Backblaze B2, or another low-cost remote with restore test.
- Expected impact: Reduces catastrophic data-loss risk.
- Risk of delay: High if local disk fails.
```

## Recommendation On Scheduling

Not yet stable enough for scheduling; the loop should clear the current search-reliability follow-up before moving from manual reviews to automation.

## Evidence And Confidence

- High confidence: local repo facts, local DB counts, validation command results.
- Medium confidence: local service inventory and model availability.
- Low confidence: billing, provider-console state, active paid services, exact hardware utilization.

## Final Operating Question

What is the highest-impact action Daanaa can responsibly take now to advance its mission, improve life for the organizations it serves, honor stewardship obligations, use the fewest necessary resources, reduce unhealthy dependence on individuals, and leave the institution wiser than it was before?
