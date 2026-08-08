# Open Decisions — Daily Review

Founder-facing queue. One line per item, newest first. Phone-readable.

**How this works:** I add items here when something needs your judgment rather than
my execution. You skim it daily. Anything I can decide from evidence, repo state, or
an approved default, I decide and do not list here — per the founder-attention policy,
listing a decision you don't need to make is a cost, not diligence.

**Status vocabulary:** `OPEN` · `ANSWERED` · `SUPERSEDED` · `EXPIRED` (unreviewed too long)

---

## OPEN

### 1. Cloudflare DNS still points at the dead droplet
**Decided already — this is an action, not a decision.** Both A records
(`daanaa.org`, `www`) still resolve to `162.243.97.179`, which no longer exists.
The site has been returning 522 throughout. My token has DNS read but not write.
- **You:** two field edits to `107.170.26.8`, or a token with Zone:DNS:Edit
- **Blocks:** every user-visible thing built on 2026-08-08 — v6 scoring, the rebuilt
  droplet, 92ms org pages, the tax-deductibility copy, the refreshed org data
- **Impact if deferred:** the site stays down

### 2. Firebase emulator toolchain for P0-SEC-001
Behavioural authorization tests are written but **cannot run** — no
`@firebase/rules-unit-testing`, no Java runtime. P0-SEC-001 is verified statically only.
- **Recommended default:** add both as dev dependencies (free, dev-only, no runtime cost)
- **If deferred:** the package ships behaviourally unverified, or waits
- **Cost:** none recurring; ~2 dev packages + a JRE

### 3. Codex review integration — does one exist?
The mandate routes significant work through independent Codex review. I have not
verified any integration exists on this server. Without one, packages accumulate in
`AWAITING_CODEX_REVIEW` and nothing ever leaves it.
- **Recommended default:** confirm whether a Codex CLI/workflow is configured; if not,
  decide whether review happens another way rather than letting the queue grow silently
- **Blocks:** P0-SEC-001 leaving `AWAITING_CODEX_REVIEW`

### 4. Lamp tier removal — scope is larger than first estimated
Approved in principle 2026-08-08 ("remove from all public-facing items"). Verified
surface: **20 frontend files**, 3 publicly served content pages (homepage,
how_it_works, methodology), the tier filter in `droplet_api.py`, a page description,
and **two published research pages** that document the tier system as findings.
- **Needs your read specifically on:** the research pages. Removing a mechanic the
  published research describes is a methodology-consistency question (Stewardship P9),
  not a UI cleanup. Options: retire the findings, or annotate them as superseded.
- **Not blocking:** the rest can proceed once the rebuild ships

---

## ANSWERED

| Date | Decision | Outcome |
|---|---|---|
| 2026-08-08 | Autonomy rule: reversibility + public claims, not backend/frontend | Approved; `CLAUDE.md` + `DECISIONS.md` reconciled |
| 2026-08-08 | Tax-deductibility wording | Approved; implemented, builds clean, not yet deployed |
| 2026-08-08 | v6 scoring only; retire v4/v5 surfaces | Approved; v6 coverage confirmed 99.78% of live orgs |
| 2026-08-08 | Hide lamp tiers | Approved in principle; scope item above |
| 2026-08-08 | Backup approach (`VACUUM INTO` + real verification) | Approved; 198s vs never-completing |
| 2026-08-08 | Delete 5 corrupt Aug-1 hourly backups | Approved; 115GB reclaimed |
