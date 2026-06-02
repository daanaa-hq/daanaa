# Daanaa Open Tasks

Tasks are read by the ops dashboard. Format:
- `- [ ]` = open   → shows as pending
- `- [x]` = done   → shows as complete
- `## Section` = group header
- Lines starting with `>` = notes (not shown as tasks)

Last refreshed 2026-06-02.

---

## Action Items — Now (priority order)
> The tech is ahead of the legal clearance. #1 unblocks the most.
- [ ] **Fund + book the attorney consult (Gate 1)** — one ~$300-500 call unblocks the giving action-layer (solicitation registration), the Minova disclosure wording, AND public launch
- [ ] **Send the Every.org partnership email** from partners@daanaa.org (draft ready: meritgiving-ops/partnerships/everydotorg-brief.md) — zero-fee give path for the invisible 97%
- [ ] **Device QA** — open daanaa.org on your phone: welcome slideshow, feedback page, beta banner render right (Claude can't see rendered output)
- [ ] **Finish credit apps** — Microsoft Founders Hub, Google for Startups, AWS Activate (5-min forms each)
- [ ] **Approve push** of uncommitted docs (operating agreement, Every.org brief, TODOS.md, official-links decision, G2 gate, new welcome copy)
- [ ] **Minova disclosure + written consent** before any LinkedIn / public announcement (needs the attorney too)

## Done Tonight (2026-06-01 → 06-02)
- [x] GitHub org + repo live — github.com/daanaa-hq/daanaa (private), all commits pushed
- [x] daanaa.org LIVE — DigitalOcean droplet, HTTPS via Cloudflare, hardened (UFW, fail2ban, swap, auto-updates)
- [x] Cloudflare DNS + proxy + SSL configured; nameservers moved from Namecheap
- [x] 9 daanaa.org email aliases (hello/orgs/legal/trust/contact/security/privacy/partners/verify) → forward to one inbox
- [x] accounts@daanaa.org login vault (entity-owned, external recovery, never AI-touched)
- [x] Email triage agent — classifies by alias, drafts replies, daily 7:30am cron (no auto-send)
- [x] Anthropic Startup Program application submitted
- [x] Live-DB split — user data (feedback/analytics/signals) survives the nightly catalog sync
- [x] Feedback page (/feedback) — anonymous, optional email
- [x] First-party privacy analytics + hidden visitor counter (no cookies/IP/session record)
- [x] Welcome slideshow for new visitors (5 slides) — copy reworked 2026-06-02
- [x] Daily DB sync cron (home → droplet, 7am) + daily live-DB backup
- [x] G2 donate-eligibility gate — never present a donate path for non-deductible / revoked orgs (9 tests passing)
- [x] Operating agreement adopted (CLAUDE.md) + DECISIONS.md + LESSONS.md + TODOS.md seeded

## Akbar — Gate 1 Legal
- [ ] Draft operating agreement for EcoMargins LLC (single-member, covers DBAs)
- [ ] File DBA "Daanaa" — Texas Assumed Name Certificate (~$25, Harris County Clerk)
- [ ] Book attorney consult (operating agreement + solicitation registration for Daanaa) ← the keystone

## Akbar — Banking & Brand
- [ ] Open Relay business bank account (under EcoMargins LLC EIN)
- [ ] Two Relay sub-accounts: "EcoMargins" (ESG revenue) + "Daanaa" (credits, ops, support)
- [ ] Grab @daanaa on Twitter/X (handle squatting risk)
- [ ] Minova outside-activity disclosure before LinkedIn founder title

## Giving Action Layer (post Gate 1)
> The "information without action" build. Public CTAs gated on Gate 1 + G2.
- [ ] Every.org partnership — Charity API, verified-status data, zero-fee + for-profit-use terms
- [ ] EIN-router fallback give-path behind a feature flag (direct link → Every.org → PayPal Giving Fund)
- [ ] Ingest IRS Auto-Revocation list into revoked_eins (scripts/ingest_auto_revocation.py is ready)
- [ ] Partnership logos component — build when first partner signs (spec in TODOS.md; no fake logos)

## Infrastructure / Ops
- [ ] UptimeRobot — monitor daanaa.org/health (free)
- [ ] Sentry error tracking — wire SDK once account + DSN exist
- [ ] DKIM record for daanaa.org (Google Workspace → Authenticate email)
- [ ] Cloudflare SSL Full(strict) + origin cert before heavy launch (currently Flexible for beta)
- [ ] Rotate Anthropic API key (was shared in chat earlier)

## Data Pipeline
- [x] 1,811,930 embeddings (mxbai 1024-dim) + FTS index (1.81M rows)
- [x] 569,262 AI missions generated (31% coverage)
- [x] 375 verified donate URLs (confidence >= 90); 114,295 websites verified
- [ ] Mission backlog: ~61,200 scored orgs without a mission (GPU clears overnight, 10pm-6am)
- [ ] Reach 50% mission coverage before stealth beta

## Gates
- [x] Gate 0: CLOSED 2026-05-28
- [ ] Gate 1: Legal Foundation (attorney + bank — the current blocker)
- [~] Gate 2: Credits & Infrastructure (GitHub + Cloudflare + Workspace done; credits pending)
- [ ] Gate 3: Data Foundation
- [ ] Gate 5: Trust Foundation (G2 revocation gate in code; needs data + insurance)
- [ ] Gate 7: Public Launch
