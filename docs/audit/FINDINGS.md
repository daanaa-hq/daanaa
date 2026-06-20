# Daanaa Audit Findings — running log (one line per finding)

## Post-audit: production search bug (2026-06-09 evening)
FIXED-DEPLOYED 2026-06-09 22:35 [search-accuracy] — droplet_api.py shipped to droplet (backup: droplet_api.py.bak_20260609), 3 indexes built on /data/precompute/v1/search.db (11s), daanaa.service restarted; verified live: screenshot query 0→2,314 results @0.59s, multi-cat 0→56,624 @0.27s, revenue band now actually filters (86,336 not 1.8M); guarded by tests/test_droplet_search.py

## Phase 1 — Backend
FIXED 2026-06-09 [auth] — was: hardcoded passcode + brute-forceable research auth — resolved by REMOVING the gate entirely (public aggregate data; passcode was also in the frontend bundle and the dashboard reads a static snapshot anyway); guarded by test_no_research_passcode_machinery
FIXED 2026-06-09 [auth] daanaa_api.py:312 — _CLAIM_SECRET now raises at startup under DAANAA_PROD without a real secret — guarded by test_claim_secret_fails_closed_in_prod
MED [mission] api/main.py:90 — /ntee endpoint ORDER BY total_revenue DESC (dormant, app not running) — archive api/main.py or switch sort before any deploy
MED [mission] api/main.py:114 — /search endpoint ORDER BY total_revenue DESC (dormant) — same fix as above
FIXED 2026-06-09 [info-leak] — both str(e) 500s now log via app.logger.exception and return generic messages
FIXED 2026-06-09 [validation] — _int_arg() helper replaces all 5 unguarded int casts; verified ?limit=abc → 200
LOW [network] restart_api.sh:22 — gunicorn binds 0.0.0.0:5000 (deliberate LAN+Tunnel) — document firewall assumption, consider ufw allowlist

## Phase 2 — Frontend
FIXED 2026-06-09 [resilience] frontend/src/data/api.ts — fetchJson now uses AbortSignal.timeout(10s) with a human-readable timeout message; all API calls covered
FIXED 2026-06-09 [resilience] Directory.tsx — fused error captured; degrades to keyword results when available, surfaces error UI only when nothing to show
FIXED 2026-06-09 [bug-found-in-session-3] daanaa_api.py:2202 — fused search 500'd on EVERY query (surge_boosts table absent; wiped by catalog sync) — now try/except OperationalError; pre-existing bug exposed because audit latency probes never checked status codes (lesson logged)
FIXED 2026-06-20 [a11y] frontend/src — FilterSheet: role=dialog + aria-modal + aria-label on close btn + aria-hidden on backdrop; ScoreBreakdown: aria-label on close; OrgClaimEditor: aria-label on tag remove btns; CompareBar already had labels
FIXED 2026-06-09 [cleanup] — 3 dead GivingList pages deleted; legacy scorers → archive/legacy_scorers_20260609/; dormant api/main.py → archive/api_fastapi_20260609/; CLAUDE.md architecture section rewritten (daanaa_api.py sole backend, v4_0 canonical scorer)
INFO [honesty] components/FinancialContext.tsx — tier labels render human-readable + confidence + explanation + data-quality flags — PASSES stewardship principle 3, no fix needed
INFO [xss] components/ui/chart.tsx:83 — dangerouslySetInnerHTML is shadcn CSS-var boilerplate, not user data — no action

## Phase 3 — Data credibility
FIXED 2026-06-09 [trust] daanaa_api.py:1096 — was: 192,501 revoked orgs in browse — _DEDUCTIBILITY_FILTER now excludes irs_revoked/org_status='revoked'; rows intact (reversible); detail route + donate gate unchanged; test_browse_excludes_revoked_orgs guards it; verified live (total 2,064,612→1,872,111)
HIGH [secrets] scripts/daily_sync.sh:2 — leaked TiDB DATABASE_URL in git history, rotation unconfirmed — verify rotation in TiDB/Aliyun console; scrub history before repo ever public
FIXED 2026-06-09 [ops] crontab — watchdog now scripts/api_watchdog.sh (health-check + retry + restart_api.sh); weekly Sunday 4:30 restart added; crontab backup in .backups/crontab_20260609.txt
FIXED+REVISED 2026-06-09 [ingest] — flagged script was legacy (writes obsolete table); ACTIVE sync (sync_irs_revocations.py) already had EIN checks + sync log; added file-shrink guard (>20% abort) + irs_revoked column update per sync; backfilled all 218,775 NULLs (30,713→1, rest→0; verified zero browse leakage — org_status had caught them); guarded by test_revocation_sync_updates_registry_column
FIXED 2026-06-09 [freshness] — Directory now shows "Built from public IRS data, last checked <date>" under the results count (uses stats.irs_status_verified_at; scores_last_updated was null)
LOW [cleanup] scripts/ — 6+ scorer versions; v4_0 canonical — archive the rest
INFO [freshness] PASSES mostly — irs_sync_log stored, API returns irs_status_verified_at, org detail + spotlight show dates
INFO [revocation-gate] daanaa_api.py:882 — donate affordance fails closed on revoked orgs ✔

## Phase 4 — Performance
REVISED 2026-06-09 [memory] — swap 97% full but NOT the API's doing: smaps_rollup shows workers at 472MB PSS, 2.25GB shared CoW (healthy), 0 swap. Culprit = Ollama (5.5GB VmSwap) + stray python3 (573MB). swappiness=10 already persisted in /etc/sysctl.d/99-ai-tuning.conf. Remaining action (Akbar): restart/trim Ollama when convenient — it's the active embed fallback while Vulkan 11436 is down
FIXED 2026-06-09 [db] — get_db now sets mmap_size=2GB + cache_size=64MB; novel-query latency 3.66s → 0.16s (mode=ro skipped — get_db serves write paths too, YAGNI)
FIXED 2026-06-09 [latency] — restart_api.sh warms 6 common searches + browse + stats + categories in background after health check
INFO [perf] daanaa.org measured FAST (0.11-0.24s via Cloudflare) — droplet slowness not reproducible 2026-06-09; baseline recorded
INFO [perf] embed calls have timeout=5/10 + Ollama fallback, fail graceful — hang hypothesis FALSE
INFO [perf] response cache works (TTLs 15min-2h); cold→warm 3.66s→0.007s

## Phase 5 — Stewardship
MED [governance] daanaa_api.py:1096 — Principle 3 gap = Phase 3 CRITICAL (revoked orgs w/ badges); cross-ref, fix once
FIXED 2026-06-20 [docs] docs/audit/README.md — "12 principles" → "11 principles" (canon); CLAUDE.md was already correct
INFO [governance] 9/11 principles verified enforced in code; privacy_check.sh live in pre-commit; all 7 privacy invariants re-verified including live log inspection

## Phase 0 — Structure (context notes, not defects)
INFO [docs] CLAUDE.md — references merit_api.py and app.py which no longer exist; daanaa_api.py is sole backend — update architecture table
INFO [frontend] frontend/src/pages — GivingListPage/GivingReview/GivingConfirmation still present after Giving List removal — verify dead code in Phase 2
INFO [pipeline] scripts/ — 4+ scorer variants (merit_scorer.py, _db, _tier_b, agent2_scorer) — confirm canonical in Phase 3
