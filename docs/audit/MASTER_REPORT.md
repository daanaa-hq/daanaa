# Daanaa Audit — Master Report (2026-06-09)

> **STATUS UPDATE (same day):** Fix sessions 1–7 all executed. Every CRITICAL/HIGH/MED
> code finding is FIXED (see FINDINGS.md for per-item status). Remaining open items:
> TiDB credential rotation (Akbar, console), Ollama swap trim (Akbar, when convenient),
> a11y targeted pass (LOW), droplet deploy of the rebuilt frontend (needs approval).
> Bonus fixes found during sessions: dead principle-test suite revived (18 tests green),
> fused-search production 500 (surge_boosts), CLAUDE.md architecture refresh.

Audited: backend (daanaa_api.py, 48 routes), frontend (146 files), data pipeline,
performance (live-measured), governance (11 principles + 7 invariants).
**Totals: 1 CRITICAL · 5 HIGH · 7 MED · 9 LOW.** Full inventory: `FINDINGS.md`.

## Overall posture
Strong: no SQL injection (whitelist-guarded), no XSS, honest tier labeling, all 7 privacy
invariants verified live, no paid-placement logic, Claude API boundary clean, donate gate
fails closed, freshness dates shown, caching + embed timeouts working. The site is
currently fast (daanaa.org 0.11s). The audit's stale premises (no caching, embed hangs,
no freshness, doc conflicts) were all FALSE — the repo is better than its reputation.

---

## Top 5 fixes (mission risk × user impact ÷ effort)

### 1. Stop listing 192,501 revoked orgs as normal charities — CRITICAL
FINDINGS: Phase 3 line 1. `daanaa_api.py:1096` — `_DEDUCTIBILITY_FILTER` ignores
`irs_revoked`/`org_status`; revoked orgs show with tier badges, donations to them are
not tax-deductible. Donate button already gated (damage contained), but listing violates
Principle 3. **Effort: 30 min + one product decision.**
Decision needed: (a) exclude from browse (1-line filter change), or (b) keep listed with
a prominent "IRS status: auto-revoked" banner + suppressed badges (preserves discovery,
~2 hrs). Recommend (a) now, (b) later if wanted.

### 2. Close the research-auth hole — HIGH (two findings, one fix)
FINDINGS: Phase 1 lines 1-2. `daanaa_api.py:2322` working passcode `'daanaa2026'` in
source + `:2352` `@limiter.exempt` = guessable AND brute-forceable. **Effort: 15 min.**
Fix: remove fallback (disable research routes if env unset), remove exempt, add
`@limiter.limit("5 per minute")`.

### 3. Frontend resilience: timeout + surfaced errors — HIGH + MED
FINDINGS: Phase 2 lines 1-2. `data/api.ts` no fetch timeout (UI hangs minutes when API
slow) + `Directory.tsx:250,349` fused-search errors silently swallowed (failure looks
like "no results"). Together = the "site hangs blank" symptom. **Effort: ~1 hr.**
Fix: `AbortSignal.timeout(10_000)` in shared fetch helper; capture fused error and route
to existing error UI at Directory.tsx:796.

### 4. Ops pair: swap exhaustion + dead watchdog — HIGH + MED
FINDINGS: Phase 4 line 1 + Phase 3 line 3. Swap 7.8/8.0 GB full (cold-path stalls) AND
cron watchdog pgrep's deleted `merit_api.py` — gunicorn has no guardian. **Effort: 30 min.**
Fix: watchdog → `curl -sf localhost:5000/health || ./restart_api.sh`; weekly API restart
cron; `vm.swappiness=10`.

### 5. Confirm TiDB credential rotation — HIGH (user action, not code)
FINDINGS: Phase 3 line 2. `scripts/daily_sync.sh:2` documents a DATABASE_URL leaked into
git history; rotation unconfirmed. **Effort: 10 min in TiDB/Aliyun console.**
If repo ever goes public: `git filter-repo` first. Akbar must do this one.

---

## Quick wins (<30 min each)
- [P1-5] `daanaa_api.py:1537,1938` — generic 500 message, detail to log only
- [P1-6] add `_int_arg()` helper for 5 unguarded `int(request.args)` casts
- [P2-4] delete 3 dead GivingList pages
- [P3-5] "Data as of <date>" line in Directory footer (stats.scores_last_updated)
- [P3-6] archive 5 legacy scorer files, leave merit_scorer_v4_0.py
- [P0] update CLAUDE.md architecture table (merit_api.py/app.py gone; daanaa_api.py sole backend)
- [P1-3] raise at startup if DAANAA_PROD set and DAANAA_CLAIM_SECRET missing
- [P1-4] archive dormant api/main.py (revenue-DESC sorts = mission landmine)

## Fix sequence (one short Claude Code session each)
| Session | Scope | FINDINGS.md refs | Size |
|---|---|---|---|
| 1 | Revoked-org exclusion + test | Phase 3 #1 | 30-60 min |
| 2 | Research auth hardening + claim secret fail-closed | Phase 1 #1,2,3 | 30 min |
| 3 | Frontend timeout + fused error surfacing | Phase 2 #1,2 | 1 hr |
| 4 | Watchdog + weekly restart + swappiness | Phase 3 #3, Phase 4 #1 | 30 min |
| 5 | Quick-wins batch (all 8 above) | various | 1-2 hrs |
| 6 | SQLite PRAGMAs + warm-up loop | Phase 4 #2,3 | 1 hr |
| 7 | BMF ingest validation + NULL irs_revoked backfill | Phase 3 #4 | 1-2 hrs |
| — | (Akbar, no agent) rotate TiDB credential | Phase 3 #2 | 10 min |

## Open product decisions (not agent-resolvable)
- Revoked orgs: exclude vs. disclose-with-banner (Session 1 needs this answered first).
- Health tiers: forced thirds vs natural distribution (pre-existing open decision, unchanged).
