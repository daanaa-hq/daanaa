# Daanaa Open Tasks

Tasks are read by the ops dashboard. Format:
- `- [ ]` = open   → shows as pending
- `- [x]` = done   → shows as complete
- `## Section` = group header
- Lines starting with `>` = notes (not shown as tasks)

---

## Akbar — This Week
- [ ] Open Relay business bank account (relay.app — under EcoMargins Consulting LLC EIN)
- [ ] Create two Relay sub-accounts: "EcoMargins" (ESG revenue) + "Daanaa" (credits, ops, support)
- [ ] Grab @daanaa on Twitter/X
- [ ] Submit Anthropic Startup Program application (up to $25K credits)
- [ ] Submit AWS Activate Founders application
- [ ] Submit Microsoft Founders Hub application
- [ ] Submit Google for Startups Cloud application
- [ ] Set up Cloudflare account + deploy coming soon page to daanaa.org
- [ ] Wire email form (Formspree signup → replace REPLACE_ME in coming-soon/index.html)
- [ ] Add Founder & CEO title to LinkedIn (EcoMargins Consulting LLC / Daanaa)

## Akbar — Gate 1 Legal
- [ ] Draft operating agreement for EcoMargins LLC (single-member, covers all 4 DBAs — free Texas template or LegalZoom ~$99)
- [ ] File DBA "Daanaa" — Texas Assumed Name Certificate (~$25, Harris County Clerk)
- [ ] File DBA "ZDPark" — same process (~$25)
- [ ] File DBA "Surfce" — same process (~$25, can wait until project is active)
- [ ] Book attorney consult (review operating agreement + solicitation registration for Daanaa)

## Akbar — User Research
- [ ] Complete 5 nonprofit ED conversations (target: 10 by Gate 4)
- [ ] Complete 5 donor conversations (target: 10 by Gate 4)

## Akbar — Gate 2 Infrastructure
- [ ] Create daanaa-org/daanaa GitHub repo
- [ ] Set up Google Workspace (akbar@daanaa.org)
- [ ] Set up Cloudflare DNS for daanaa.org
- [ ] Set up UptimeRobot — monitor api.daanaa.org/health + alert on downtime (free tier)
- [ ] Sign up for VolunteerMatch API key (Q3 — needed for volunteer discovery feature)

## Build — Done
- [x] Gate 0: Security fixes + principle tests (2026-05-28)
- [x] PWA + seam design — offline shell, ENABLE_SCORES, civic actions (2026-05-28)
- [x] Mission quality patch — per-org source, city casing, boilerplate filter (2026-05-29)
- [x] Morning brief cron (7am daily → logs/morning_brief_YYYY-MM-DD.md)
- [x] 4-hour pipeline monitor cron (→ logs/pipeline_status.log)
- [x] Coming soon page — daanaa.org holding page (coming-soon/index.html)
- [x] Brand logo library — 26 NTEE category folders (brand/logos/A-Z/)
- [x] Ops dashboard — Claude API chat, model selector, clickable tasks, comments
- [x] Frontend stat alignment — all pages show 1.6M live from API
- [x] GPU utilization upgrade — Qwen 5 slots, mission gen 5 workers
- [x] FTS index — 1,811,924 rows (keyword search ready)
- [x] Embeddings — 1,811,930 rows (semantic search ready)
- [x] Operating agreement draft — meritgiving-ops/legal/

## Security & Code Review
- [x] Stewardship principle tests — 12/12 passing
- [x] No payment SDK or routes (P8)
- [x] CSP headers wired (P2)
- [x] Admin key uses hmac.compare_digest (P7)
- [x] CORS locked to known origins
- [x] Rate limiter (flask-limiter) active on API
- [x] npm audit — 0 vulnerabilities
- [x] Ops dashboard auth — token-gated (OPS_TOKEN in .env, hmac.compare_digest); was open on 0.0.0.0:5001
- [x] Remove localhost from CSP connect-src in production build (env-gated on DAANAA_PROD)
- [x] Add principle test: no PII in logs (test_log_scripts_no_pii_columns + test_generated_logs_have_no_emails — 14/14 passing)
- [x] Delete .bak files — merit_api.py.bak (vite.config.ts.bak already gone)
- [ ] Rotate Anthropic API key (shared in chat — new key at console.anthropic.com → update meritgiving/.env)
- [ ] Wire HTTPS / certbot on server before Cloudflare DNS goes live
- [ ] Commit new scripts to git — ops_server.py, morning_brief.py, pipeline_check.py, ops_watchdog.sh
- [ ] Wire Formspree in coming-soon/index.html (replace REPLACE_ME with real form ID)
- [ ] Plausible analytics — send Akbar the script snippet to add to index.html
- [ ] Sentry error tracking — wire SDK once Akbar creates account and sends DSN
- [ ] Solicitation registration review — attorney consult before public launch

## Build — Upcoming
- [ ] Support button → Stripe → Daanaa Relay sub-account (post-Cloudflare, label "Support Daanaa" not "Donate")
- [ ] Volunteer discovery feature — VolunteerMatch/Idealist API on org profiles (Q3)
- [ ] Return-URL wallet callback handler (post-stealth-beta)
- [ ] Claim portal 4-layer verification logic (Sep)
- [ ] EcoMargins ESG portal MVP (Oct — first revenue event)
- [ ] GitHub repo daanaa-org/daanaa — push codebase + wire CI (Gate 2)
- [ ] LinkedIn Daanaa company page (Gate 6)
- [ ] Sector report v1: "The Invisible Majority" (Aug draft)
- [ ] Newsletter issue 1 draft (Aug)
- [ ] Transactional email — SES or SendGrid (needed for claim confirmations at stealth beta)

## Claude Code MCP Connectors
> Wire these as the team grows. Each gives Claude Code direct access to a live system.
- [ ] GitHub MCP server — wire after daanaa-org/daanaa repo is created (Gate 2); enables issue/PR management from Claude Code chat
- [ ] SQLite MCP server — direct DB queries from ops dashboard and Claude chat without custom endpoints
- [ ] Sentry MCP — surfaces errors in Claude Code chat once DSN is set up

## Automation Skills (build as team grows)
> Claude Code skills that automate repeated workflows. Add to ~/.claude/skills/ as ops matures.
- [ ] /deploy skill — build frontend → copy to dist → restart API → smoke test health endpoint
- [ ] /data-update skill — pull new IRS/ProPublica data → run scorer → reindex FTS → verify counts
- [ ] /pipeline-check skill — one-shot status: mission gen + donate pipeline + DB health + GPU
- [ ] /claim-review skill — pull pending claim queue → verify against IRS → flag for approve/deny

## Data Pipeline
- [x] 1,811,930 embeddings complete (mxbai 1024-dim)
- [x] 1,820+ verified donate URLs (Jun 28 milestone met early)
- [ ] Mission generation: ~1.56M orgs remaining (running at 5 workers/slots, ~90h ETA)
- [ ] Web crawler: 5,918 orgs remaining for page cache
- [ ] Donation link pipeline: 251K queue pending
- [ ] Reach 50% mission coverage before stealth beta

## Gates
- [x] Gate 0: CLOSED 2026-05-28
- [ ] Gate 1: Legal Foundation (bank account + attorney — Akbar, overdue)
- [ ] Gate 2: Credits & Infrastructure (Jun 16)
- [ ] Gate 3: Data Foundation (Jul 14)
- [ ] Gate 5: Trust Foundation (Sep 8) — includes insurance ~$500/yr
- [ ] Gate 7: Public Launch (Nov 10)
