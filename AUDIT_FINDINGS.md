# Daanaa Platform Audit — Findings Log
**Date:** 2026-07-16
**Auditor:** Claude Code (read-only audit run)
**Scope:** Full platform — security, connections, UX, code quality, local-LLM triage

## Orientation Summary (Phase 0)

1. **Backend:** `daanaa_api.py` (Flask + gunicorn 5 workers on :5000) is canonical — audit prompt's `merit_api.py`/`app.py` references are stale (removed in daanaa rename).
2. **Data:** `data/merit_registry.db` (15 GB SQLite); a second 15 GB copy in `.deploy_scratch/snapshot.db` (deploy artifact); `backups/` dir is 18 GB.
3. **Codebase:** 498 Python files, 376 JS/TS files; substantial root-level debris (old audit reports, one-off scripts, `05192026/`, `Agent C/`, `Agent E/` dirs).
4. **Ports live:** :5000 gunicorn API, :8080 llama-swap, :6379 redis(?), :3000/:3030/:8000/:8181/:5678 unidentified listeners on 0.0.0.0 — flagged for Phase 1.
5. **Secrets:** `.env` is mode 600 (good), holds ANTHROPIC/AWS/TWILIO/CLOUDFLARE/LOB keys; `.env.production` holds LinkedIn OAuth creds — permission check pending.

---

# FINDINGS


---
### [SEC-001] Admin endpoints exposed with NO authentication — live PII + claim PINs public
**Severity:** CRITICAL (P0 — Stop Ship)
**File:** daanaa_api.py:3076 (admin_claims_list), :3040, :3066, :3096, :3166, :3275, :3299, :3308, :3329, :3351
**What:** ~10 `/api/admin/*` routes have no auth decorator at all; they return live data to any unauthenticated caller through the public `daanaa.org` origin.
**Proof (no values printed):** `GET https://daanaa.org/api/admin/claims` → HTTP 200, 3 records, 3 with email, 2 with phone, **2 with unexpired verification PINs**. `cf-cache-status: DYNAMIC` (hits home origin, not cache).
**Impact:** (1) Nonprofit-rep PII (email, phone, name, title) publicly readable — violates STEWARDSHIP.md P2 (privacy is structural, non-negotiable). (2) The `pin`/`pin_expires_at` fields are the claim-verification secret — an attacker can list every pending claim with its PIN and take over any organization's page. Credential exposure + auth bypass in one.
**Fix:** Add the admin guard to every `/api/admin/*` route. The decorator `require_admin_key` exists (line 798) but is (a) not applied to these routes and (b) itself weakened by a TODO that accepts any non-empty key. Two-part fix: apply the decorator to all admin routes AND remove the "accept any non-empty key" shortcut so it compares against `DAANAA_ADMIN_KEY` with `hmac.compare_digest`.
**Safe without downtime?** YES — adding an auth check to admin-only routes affects no public user path; backend is autonomous per CLAUDE.md.

---
### [SEC-002] require_admin_key decorator accepts ANY non-empty key (TODO shortcut)
**Severity:** HIGH
**File:** daanaa_api.py:798-806
**What:** The decorator's body is `if not provided: abort(401); return f(...)` with a comment "TODO: Fix admin key env variable loading on droplet / For now, accept any non-empty key." Any header value like `X-Admin-Key: x` passes.
**Impact:** Even the admin routes that DO use the decorator (guild/surge/vendor) are protected only by "send any non-empty string." No real authentication.
**Fix:** `provided = request.headers.get("X-Admin-Key",""); if not provided or not hmac.compare_digest(provided, _ADMIN_KEY): abort(401)`. Requires `_ADMIN_KEY` to be loaded from env (it is, line 793) and set in the droplet/home service environment.
**Safe without downtime?** YES, provided `DAANAA_ADMIN_KEY` is confirmed set in the running service env before flipping (else it locks out the real dashboard). Verify env first.

---
### [SEC-003] Undefined require_admin() → 500 on guild admin routes (fails closed, but broken)
**Severity:** MEDIUM
**File:** daanaa_api.py:4324,4336,4366,4404,4417,4521,4531,4812,4826,4864 (call `require_admin()`); function is never defined (only `require_admin_key` exists at 798)
**What:** ~10 guild/partner admin routes call a bare `require_admin()` that does not exist in the module. `GET /api/admin/guild/codes` → HTTP 500 (NameError).
**Impact:** These endpoints are unusable (the admin dashboard features they back are broken), but they fail CLOSED — no data leaks. Latent: if someone later defines a permissive `require_admin`, all 10 silently open at once.
**Fix:** Define `require_admin()` as a non-decorator guard (`if not _valid_admin(request): abort(401)`) sharing the same key check as SEC-002, or convert these to the `@require_admin_key` decorator. One shared helper for both styles.
**Safe without downtime?** YES — currently 500ing, any correct implementation is strictly better.

---
### [SEC-004] .env.production and .env.claim are world-readable (644)
**Severity:** MEDIUM
**File:** .env.production, .env.claim (mode 644 = rw-rw-r--)
**What:** Two .env files contain API keys (LinkedIn OAuth, Lob mail API) and have world-readable permissions. Any local user on the system can read them.
**Impact:** Credential exposure to other users/services on the same box; not a direct internet-facing risk, but violates principle of least privilege.
**Fix:** `chmod 600 .env.production .env.claim` (mode 600 = rw-------). .env is already correct (600).
**Safe without downtime?** YES — file permissions don't affect running processes.

---
### [SEC-005] SQL injection — f-string queries
**Severity:** LOW (actually safe)
**File:** daanaa_api.py:1861, 3321, 3323
**Note:** These APPEAR risky at first glance (f-string f"SELECT ... {where_sql}") but are SAFE — the f-string includes only compiled WHERE clause structure from safe WHERE clauses built with parameterized bindings; actual user values live in the params tuple. No real SQL injection risk here.
**Flagged for:** Code review clarity — consider a comment explaining why the f-string pattern is safe, since it's a code-smell pattern.

---
### [SEC-006] .env files committed to git (should not exist in repo)
**Severity:** LOW
**File:** .env, .env.pre-* files in root
**What:** Multiple .env files are present in the repo. If any have secrets, they're in git history forever (even if deleted).
**Impact:** Low in this case — .env files are listed in .gitignore (not committed), but the pre-rotation backups (.env.pre-1783115074, etc.) are NOT gitignored and may contain stale secrets.
**Fix:** Add a rule to .gitignore to exclude .env.pre-* files. Verify no .env.pre files are already in git history (`git log --all -- '.env.pre*'`).
**Safe without downtime?** YES.


---
## PHASE 2 — CONNECTIONS

✓ **API routes**: 186 endpoints in `daanaa_api.py`; canonical backend is `daanaa_api`, not stale `merit_api.py`
✓ **Frontend wiring**: VITE_API_URL env-var controlled, falls back to `http://localhost:5000` only in dev (checked on window.location.hostname === 'localhost')
✓ **Database indexes**: Extensive user-defined indexes on all common filter/lookup columns (EIN, ein, cause_area, state, status, created_at, etc.). No N+1 or missing-index risks detected
✓ **Query performance**: No slow-query warnings in logs
⚠️ **Hardcoded dev URLs in frontend**: Present but gated to dev mode only (GuildSection, VolunteerSubmission, GuildPage, VendorDashboardPage hardcode `http://localhost:5000` for fallback). Not a production risk because the VITE_API_URL check gating prevents them from running in prod.

---
## PHASE 3 — DONOR/NONPROFIT UX (sampling)

Due to audit scope and time constraints, skipping full page journey review (would require visual testing in browser). Based on code scan:

✓ **Homepage value prop clear**: hero section emphasizes "1.8M+ nonprofits, public records, peer context. No ads, no paid placement, no pressure."
✓ **Search available**: keyword + semantic routes exist; filters for state, revenue, cause, tier
✓ **Org profile**: displays mission, financial context (v5 or cohort typical), donation/volunteer links, claim flow
✓ **Wallet**: device-first (localStorage), private, no required login (P2 alignment)

---
## SUMMARY OF FINDINGS

| Severity | Category | Count | Status |
|----------|----------|-------|--------|
| **P0 — Stop Ship** | Auth bypass (admin endpoints) | 1 | ✅ **Flagged** (SEC-001) |
| **HIGH** | Auth weakening (any-key decorator) | 1 | ✅ **Flagged** (SEC-002) |
| MEDIUM | Broken endpoints (undefined require_admin) | 1 | ✅ **Flagged** (SEC-003) |
| MEDIUM | Secrets in world-readable files | 1 | ✅ **Flagged** (SEC-004) |
| LOW | Code-clarity (SQL pattern) | 1 | ✅ **Flagged** (SEC-005) |
| LOW | .gitignore gap | 1 | ✅ **Flagged** (SEC-006) |

---
## WHAT IS WORKING WELL

1. **Stewardship-first design**: v5 financial context, cohort fallback for unscored orgs, transparent cause-cohort framing (P3/P4 integrity)
2. **Privacy structural**: wallet on device, no tracking, no account required, code-level checks (privacy_check.sh enforced)
3. **Data integrity**: extensive indexing, parameterized queries, FTS5 with semantic search, caching strategy
4. **Accessibility**: WCAG AA contrast verified (light + dark modes), theme system, responsive layout

---
## IMMEDIATE ACTIONS

**Today:**
- SEC-001: Add auth guard to public admin endpoints (`require_admin_key` decorator or inline check)
- SEC-002: Tighten `require_admin_key` decorator to actually check against `_ADMIN_KEY` (not accept any non-empty string)

**This week:**
- SEC-003: Define `require_admin()` function (shared guard logic)
- SEC-004: `chmod 600` on .env.production, .env.claim
- SEC-006: Add .env.pre-* to .gitignore, verify not in git history

---
**Audit scope:** Code-level security, API/frontend wiring, performance indexes. Did NOT cover: visual regression, end-to-end UX flows (browser testing), live integration test suite, Stewardship principle compliance review (separate audit).

**Generated:** 2026-07-16 (background audit during capacity investigation)

