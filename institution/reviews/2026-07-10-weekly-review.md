# Weekly Institutional Review - 2026-07-10

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
## stewardship-system-bootstrap
?? AGENTS.md
?? frontend/eslint.config.js
?? institution/
?? scripts/institution_weekly_review.py
```
- Recent commits:
```text
29885aca88c log: v4_scores schema-drift lesson + flag pre-existing 51-test backlog
367b1eb59f6 fix: 2 more v4_scores schema-drift 500s (search, submission-status) + align stale legal-guard test
cfe376a5e4c test: T9 coverage for AnswerCard + action-row gating (37 new tests)
8ecb2f200da fix: Tax-deductible badge showed on revoked orgs, contradicting the revoked banner
f0bee315442 fix: org detail 500s on every request -- v4_scores schema drift
```
- Current diff summary:
```text
clean or unavailable
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
2183 /usr/local/bin/ollama serve
3891 java -XX:+IgnoreUnrecognizedVMOptions -Dfile.encoding=UTF-8 -Dlogfile.path=target/log -XX:+CrashOnOutOfMemoryError -server --add-opens java.base/java.nio=ALL-UNNAMED -jar /app/metabase.jar
4429 node /usr/local/bin/n8n
7659 /usr/local/bin/cloudflared tunnel --config /home/akbar/.cloudflared/config.yml run
7695 /usr/bin/cloudflared --no-autoupdate --config /etc/cloudflared/config.yml tunnel run
376571 /home/akbar/meritgiving/venv/bin/python3 /home/akbar/meritgiving/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 -b 0.0.0.0:8880 --timeout 120 --preload --access-logfile /home/akbar/meritgiving/logs/gunicorn_access.log --access-logformat %(t)s "%(r)s" %(s)s %(b)s %(M)sms --error-logfile /home/akbar/meritgiving/logs/daanaa_api.log --pid /home/akbar/meritgiving/logs/daanaa_api.pid daanaa_api:app
376600 /home/akbar/meritgiving/venv/bin/python3 /home/akbar/meritgiving/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 -b 0.0.0.0:8880 --timeout 120 --preload --access-logfile /home/akbar/meritgiving/logs/gunicorn_access.log --access-logformat %(t)s "%(r)s" %(s)s %(b)s %(M)sms --error-logfile /home/akbar/meritgiving/logs/daanaa_api.log --pid /home/akbar/meritgiving/logs/daanaa_api.pid daanaa_api:app
376601 /home/akbar/meritgiving/venv/bin/python3 /home/akbar/meritgiving/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 -b 0.0.0.0:8880 --timeout 120 --preload --access-logfile /home/akbar/meritgiving/logs/gunicorn_access.log --access-logformat %(t)s "%(r)s" %(s)s %(b)s %(M)sms --error-logfile /home/akbar/meritgiving/logs/daanaa_api.log --pid /home/akbar/meritgiving/logs/daanaa_api.pid daanaa_api:app
376603 /home/akbar/meritgiving/venv/bin/python3 /home/akbar/meritgiving/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 -b 0.0.0.0:8880 --timeout 120 --preload --access-logfile /home/akbar/meritgiving/logs/gunicorn_access.log --access-logformat %(t)s "%(r)s" %(s)s %(b)s %(M)sms --error-logfile /home/akbar/meritgiving/logs/daanaa_api.log --pid /home/akbar/meritgiving/logs/daanaa_api.pid daanaa_api:app
376604 /home/akbar/meritgiving/venv/bin/python3 /home/akbar/meritgiving/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 -b 0.0.0.0:8880 --timeout 120 --preload --access-logfile /home/akbar/meritgiving/logs/gunicorn_access.log --access-logformat %(t)s "%(r)s" %(s)s %(b)s %(M)sms --error-logfile /home/akbar/meritgiving/logs/daanaa_api.log --pid /home/akbar/meritgiving/logs/daanaa_api.pid daanaa_api:app
378965 /usr/local/bin/ollama runner --ollama-engine --model /usr/share/ollama/.ollama/models/blobs/sha256-819c2adf5ce6df2b6bd2ae4ca90d2a69f060afeb438d0c171db57daa02e39c3d --port 45649
1399790 /home/akbar/warehouse/llama-swap --config /home/akbar/warehouse/config.yaml --listen 127.0.0.1:8080
1473500 node --disallow-code-generation-from-strings --disable-proto=delete /usr/local/lib/node_modules/n8n/node_modules/.pnpm/@n8n+task-runner@file+packages+@n8n+task-runner_@opentelemetry+api@1.9.0_@opentelemetry_bd25ea1f047b3163759a25985b9c52da/node_modules/@n8n/task-runner/dist/start.js
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
| analytics_daily | 72 |
| analytics_search | 0 |
| feedback | 0 |
| v5_feedback | 1 |
| org_claims | 3 |
| org_interest | 1 |
| org_view_events | 64 |
| wallet_analytics | 0 |

Uncertain or unavailable:

- Support email volume is not available from a verified local export.
- Representative nonprofit interview or advisory evidence is still missing.
- Cloud/API usage is not available from a local source of truth.

## Highest Constraint

Financial and infrastructure unknowns outside the repo limit responsible planning more than code quality now.

Evidence:

- FR-2026-07-10-001 through FR-2026-07-10-004 remain open
- GPU/CPU/cloud usage telemetry is still unknown
- Budget state remains in survival posture

## Options

1. Lowest-cost option: keep the survival posture, preserve unknowns explicitly, and wait for only the founder inputs that unblock responsible decisions.
   - Benefit: avoids fabricated data and avoids unnecessary work.
   - Cost: near zero.
   - Risk: slow progress on budgeting and continuity.

2. Balanced option: keep safe local improvements moving while narrowing the founder request queue to spend, backup, credential rotation, and deployment authority.
   - Benefit: preserves momentum without crossing human-accountability boundaries.
   - Cost: local synthesis time only.
   - Risk: medium-low.

3. Higher-investment option: add new telemetry and operational dashboards before the missing financial inputs are verified.
   - Benefit: richer visibility.
   - Cost: more engineering work and more moving parts.
   - Risk: medium because it can create noise before core unknowns are resolved.

## Stewardship Deliberation

- Mission Steward: favors the balanced option because it keeps improving service quality without inventing finances or bypassing human accountability.
- Small Nonprofit Executive Director: wants the team to stay useful and frugal rather than building heavy internal systems first.
- Nonprofit Finance And Compliance Representative: insists that unknown cash, recurring spend, and reserve posture must stay explicitly unknown.
- Donor And Funder Representative: wants credible stewardship evidence before outward funding or growth claims expand.
- Product And User Experience Representative: supports continuing low-risk product-quality work while waiting on founder-only inputs.
- Technology And Data Representative: prefers existing local services and deterministic code over new telemetry complexity.
- Security And Privacy Representative: supports waiting for founder-confirmed backup and credential status before changing data-handling assumptions.
- Legal And Regulatory Issue-Spotter: agrees that approval boundaries should stay strict until the founder resolves the delegation conflict.
- Financial Sustainability Representative: strongly favors the survival posture and opposes new paid tools.
- Ethics And Human Dignity Representative: supports honest uncertainty over false precision.
- Devil's Advocate: argues that the sampled search log errors may be a more urgent reliability constraint than financial unknowns.
- Long-Term Continuity Representative: agrees with the balanced option, but wants backup and credential clarity resolved soon because continuity cannot rely on assumptions.

Minority view: the Devil's Advocate warns that backend schema-drift errors in recent logs may justify a focused reliability task before another institutional iteration.

## Recommended Action

- Action: Keep safe local improvements moving and request only the minimum founder inputs needed for spend, backup, and credential decisions.
- Expected benefit: allow responsible financial, continuity, and approval decisions without inventing missing operational facts.
- Cost: local engineering time only; no new service or spend.
- Risk: low.
- Reversibility: high; config-only and testable.
- Evidence: open founder requests, survival-budget posture, unknown usage telemetry, and unresolved provider-console state.
- Confidence: medium.
- Success measure: founder-only unknowns remain narrowly scoped, explicitly tracked, and do not block safe local improvements.
- Stop condition: stop if a verified production reliability issue becomes a higher constraint than the current missing financial and continuity inputs.
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
- logs/daanaa_api.log: 16 flagged lines; sqlite3.OperationalError: no such column: v4.peer_cell_size; [2026-07-10 10:57:07,042] ERROR in app: Exception on /api/search [GET]; Traceback (most recent call last):;     rv = self.handle_user_exception(e); sqlite3.OperationalError: no such column: v4.peer_cell_size
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

Not yet stable enough for scheduling; manual review is useful, but one more clean cycle after the current improvement is still warranted.

## Evidence And Confidence

- High confidence: local repo facts, local DB counts, validation command results.
- Medium confidence: local service inventory and model availability.
- Low confidence: billing, provider-console state, active paid services, exact hardware utilization.

## Final Operating Question

What is the highest-impact action Daanaa can responsibly take now to advance its mission, improve life for the organizations it serves, honor stewardship obligations, use the fewest necessary resources, reduce unhealthy dependence on individuals, and leave the institution wiser than it was before?
