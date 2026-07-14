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
- Required founder time: 20-45 minutes with agent support.
- Deadline: Before larger ingestion or outreach.
- Can work continue: Yes, but avoid deleting local backups.


### FR-2026-07-14-001: Complete Provider Access Map And Second Admin Assignment

- Decision or input needed: Name the trusted second GitHub admin and confirm current owner/recovery status for domain/DNS, Cloudflare, DigitalOcean, Google Drive/rclone backup, Firebase/Google Cloud, AWS/S3 legacy paths, Stripe, Plausible, Sentry, Twilio/Jambonz, n8n/Chatwoot, and Metabase.
- Why Daanaa cannot determine it safely: Provider-console access, billing ownership, MFA status, recovery codes, and admin lists are outside repository evidence and must not be guessed.
- Recommended default: Treat all unverified providers as founder-dependent until confirmed in `institution/PROVIDER_ACCESS_MAP.md`.
- Alternatives: If a provider is inactive or retired, mark it retired and document the replacement or removal path.
- Expected impact: Reduces founder-only continuity risk and makes emergency recovery executable by a qualified successor.
- Risk of delay: High for GitHub, DNS, DigitalOcean, and offsite backup; medium for inactive or experimental providers.
- Required founder time: 30-60 minutes with agent support.
- Deadline: Before public launch escalation, production credential rotation, or any larger outreach campaign.
- Can work continue: Yes, but do not claim provider resilience or offsite disaster recovery is complete until verified.
