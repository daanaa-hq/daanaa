# Provider Access Map

## Document Control

| Field | Value |
|---|---|
| Purpose | Document where institutional authority, recovery access, billing, domains, production systems, and critical vendor controls live without storing secrets. |
| Responsible role | Chief Steward; Continuity Steward when appointed. |
| Authority level | Continuity and succession record; does not grant access by itself. |
| Review trigger | New provider, provider removal, billing change, admin change, deploy-key change, domain/DNS change, incident, or quarterly succession review. |
| Editable status | Editable by ordinary agents for structure and non-secret facts; named account holders and access grants require founder approval. |
| Dependencies | `institution/SUCCESSION.md`, `institution/RISK_REGISTER.md`, `institution/FOUNDER_REQUESTS.md`, `institution/library/013_critical_account_succession.md`. |
| Retirement condition | Retire only when replaced by a dedicated access-governance system with equivalent protections. |

## Rules

- Do not store passwords, API keys, recovery codes, private keys, OAuth secrets, seed phrases, billing card details, or backup encryption passphrases in this file.
- Name account roles and recovery responsibilities, not secret values.
- Prefer individually named accounts with MFA over shared logins.
- Record whether a second admin exists.
- Record where recovery instructions live.
- Record what breaks if the founder account is unavailable.
- Record the minimum action needed to remove single-founder dependence.

## Access Map

| Provider / system | Purpose | Current known owner | Second admin / recovery holder | MFA / recovery status | Billing owner | Secrets location | Continuity risk | Next action |
|---|---|---|---|---|---|---|---|---|
| GitHub organization / repo | Authoritative source code, institutional memory, issue/PR history. | Founder account; exact org admin list not verified from repo. | Pending founder naming of second admin. | Unknown from repo. | Unknown from repo. | Not in repo. | High: source and governance continuity depend on admin access. | Founder names second admin; add MFA/security-key requirement; document recovery procedure in `SUCCESSION.md`. |
| Domain registrar / DNS for `daanaa.org` | Public identity, DNS, email/domain recovery. | Unknown from repo. | Unknown. | Unknown. | Unknown. | Not in repo. | High: domain loss breaks public trust and service continuity. | Identify registrar, owner, MFA, renewal status, and emergency recovery contact. |
| Cloudflare / Pages / DNS edge if used | Public deployment, DNS/proxy, Pages deployments, cache. | Unknown from repo. | Unknown. | Unknown. | Unknown. | Not in repo. | High if production DNS or Pages depends on founder-only access. | Confirm account owner, project IDs, deployment authority, API-token owner, and rollback path. |
| DigitalOcean droplet | Production server / deployed edge/API path. | Unknown from repo; droplet documented as non-authoritative. | Unknown. | Unknown. | Unknown. | Not in repo. | High: outage recovery and billing may require console access. | Record droplet project, root-access policy, snapshot/backup status, firewall, and recovery owner. |
| Google Drive / `rclone daanaa-backup:` | Offsite backup target. | Unknown from repo. | Unknown. | Unknown. | Unknown/free tier unknown. | Rclone config outside repo. | High until offsite restore is verified. | Verify remote exists, list files, restore newest full backup to `/tmp`, record result. |
| Firebase / Google Cloud | Wallet sync/auth and Firestore-related services where active. | Unknown from repo. | Unknown. | Unknown. | Unknown. | Not in repo. | Medium-high: user auth/sync continuity and privacy controls may depend on console access. | Confirm active services, project owner, rules deployment authority, and export/delete procedure. |
| AWS / S3 historical backup paths | Legacy or historical backup/storage scripts. | Unknown; may be retired. | Unknown. | Unknown. | Unknown. | Not in repo. | Medium: stale scripts can mislead successors or restart paid storage. | Classify as active/retired; archive or mark superseded if Google Drive is canonical. |
| Stripe / payment tooling | Non-donation credits or paid services if active. | Unknown from repo. | Unknown. | Unknown. | Unknown. | Not in repo. | Medium-high: payment controls must not blur donation boundary or paid influence rules. | Confirm active status, product scope, webhook owner, and donation-boundary policy. |
| Plausible / analytics | Privacy-preserving usage analytics if active. | Unknown from repo. | Unknown. | Unknown. | Unknown. | Not in repo. | Medium: telemetry policy must match implementation. | Confirm account owner, data retention, domains, and privacy policy language. |
| Sentry / error monitoring | Optional error reporting where enabled. | Unknown from repo. | Unknown. | Unknown. | Unknown. | Not in repo. | Medium: can collect sensitive error context if misconfigured. | Confirm enabled status, scrubbing, retention, and privacy invariants. |
| Twilio / Jambonz / voice services | Voice/IVR/support experiments if active. | Unknown from repo. | Unknown. | Unknown. | Unknown. | Not in repo. | Medium: communication services can affect public trust and cost. | Classify active/retired; document approval requirement before use. |
| n8n / Chatwoot / automation stack | Support, triage, workflow automation if active. | Unknown from repo. | Unknown. | Unknown. | Unknown. | Not in repo. | Medium: automation may hold user communications or operational state. | Confirm active status, backup path, retention, and data categories. |
| Metabase / dashboards | Internal analytics and reporting if active. | Unknown from repo. | Unknown. | Unknown. | Unknown. | Not in repo. | Medium: dashboards may expose sensitive operational data. | Confirm active status, users, data sources, and export/retention. |
| Local home server | Development, data processing, local backups, AI memory. | Founder/local operator. | Unknown. | Physical/local controls unknown. | N/A. | Local only; not in repo. | High: substantial operational state remains local. | Complete AI memory migration, provider map, restore drills, and successor recovery test. |

## Minimum Second-Admin Standard

For GitHub and any critical provider that can block recovery:

1. Individually named account; no shared login.
2. Strong MFA, preferably hardware security key.
3. At least two registered recovery methods.
4. Recovery codes stored outside the repository.
5. Least privilege consistent with continuity.
6. Quarterly access review.
7. Removal procedure documented before access is granted.
8. Branch protections and production-deploy controls remain in force.

## Founder Input Needed

1. Name the trusted second GitHub admin.
2. Identify registrar/DNS provider and renewal owner.
3. Confirm DigitalOcean account owner and billing continuity.
4. Confirm `rclone daanaa-backup:` owner and whether the Google Drive backup is active.
5. Classify AWS/S3 backup scripts as active, legacy, or retired.
6. Confirm active status for Firebase, Stripe, Plausible, Sentry, Twilio/Jambonz, n8n/Chatwoot, and Metabase.

## Review Status

Status: framework ready; factual provider/account fields remain unverified from repository evidence.

Next review: after founder provides the second GitHub admin name and confirms offsite backup provider access.
