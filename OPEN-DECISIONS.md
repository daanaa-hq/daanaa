# Open Decisions — Daily Review

Founder-facing queue. One line per item, newest first. Phone-readable.

**How this works:** I add items here when something needs your judgment rather than
my execution. You skim it daily. Anything I can decide from evidence, repo state, or
an approved default, I decide and do not list here — per the founder-attention policy,
listing a decision you don't need to make is a cost, not diligence.

**Status vocabulary:** `OPEN` · `ANSWERED` · `SUPERSEDED` · `EXPIRED` (unreviewed too long)

---

## OPEN

Nothing open right now. Everything from today's session is resolved (below) or
tracked as ordinary work in `TODOS.md` (doesn't need your judgment, just time):
card-level evidence markers, AI-slop audit for Directory/category pages, actual
deletion of the dormant lamp-tier engine, wallet explainer video, org-page loading
skeleton, hero mission-source attribution.

---

## ANSWERED

| Date | Decision | Outcome |
|---|---|---|
| 2026-08-08 | Search-and-discovery-first redesign | Homepage rebuilt (1081→360 lines, 11→4 sections) and org detail page (7 real bugs fixed) via `/plan-design-review` + `/plan-eng-review`. Both deployed, hash-verified against production. |
| 2026-08-08 | Tax-deductibility badge showing identical treatment for verified/unverified/unknown | Root cause found: frontend was reading a dead field (`irs_eligibility_status`, DB columns dropped ~2026-08-01) instead of the real `tax_deductible` boolean the backend already computed. Independently verified with Codex (caught a real gap in the first-pass plan — the search.db fallback path, where revoked orgs' pages live, never computed the field). Fixed frontend + backend, deployed, verified live. |
| 2026-08-08 | `daanaa-api` systemd unit renamed on droplet rebuild, 13 scripts still said `daanaa` | Found live when it blocked the tax-deductibility deploy. Fixed all 13 (including 2 on cron: 1:30am and 08:15 daily deploys were silently failing). Stale 55-day-old memory file (wrong droplet IP) also corrected — it caused a real misdiagnosis mid-incident, caught by a DigitalOcean console screenshot, not by retrying. |
| 2026-08-08 | `feat/retire-lamp-tiers` branch (5 commits, all deployed) — merge to master? | PR #1 opened and merged; branch deleted. |
| 2026-08-08 | `firebase login` blocking P0-SEC-001 deploy | Done; deployed, verified live against production Firestore (403 on unauthenticated access). |
| 2026-08-08 | Cloudflare DNS pointed at dead droplet | Fixed — both A records repointed, SSL Full→cert installed, site live |
| 2026-08-08 | Firebase emulator toolchain for P0-SEC-001 | Installed; 9/9 behavioural tests pass, proven against reverted rule |
| 2026-08-08 | Codex review integration — does one exist? | Confirmed yes; used for P0-SEC-001, lamp-tier (2 rounds), backend security review, and tax-deductibility fix |
| 2026-08-08 | Lamp tier removal — full scope (20+ files, content pages, research pages, backend filters) | Shipped and deployed. Founder poll resolved WhyDaanaa copy ("v6-only, beta, no history on live site") and backend tier-filter ("retire with the rest"). Verified live: `/api/methodology` → v6.0, zero tier names |
| 2026-08-08 | Autonomy rule: reversibility + public claims, not backend/frontend | Approved; `CLAUDE.md` + `DECISIONS.md` reconciled |
| 2026-08-08 | Tax-deductibility wording | Approved; deployed, verified live |
| 2026-08-08 | v6 scoring only; retire v4/v5 surfaces | Approved; v6 coverage confirmed 99.78% of live orgs |
| 2026-08-08 | Backup approach (`VACUUM INTO` + real verification) | Approved; 198s vs never-completing |
| 2026-08-08 | Delete 5 corrupt Aug-1 hourly backups | Approved; 115GB reclaimed |
| 2026-08-08 | Backend security fix (giving-profile route) — deploy now | Deployed to home server; severity corrected in the record (was LAN-scoped, never internet-facing — original claim was wrong) |
