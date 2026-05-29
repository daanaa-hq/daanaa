
## PR-0a — Safety fixes (2026-05-28)

| file | what | principle(s) | severity |
|------|------|--------------|----------|
| merit_api.py:1-5 | Rename "MeritGiving API" → "Daanaa API" in header; add `import hmac` | P3 | LOW |
| merit_api.py:212-223 | `MERIT_ADMIN_KEY` → `DAANAA_ADMIN_KEY` (backward-compat fallback kept); replace `!=` compare with `hmac.compare_digest` | P7 | MEDIUM |
| merit_api.py:271-297 | Add `_init_org_claims_table()` at module load — matching live DDL; fresh clone no longer crashes on first claim attempt | P9 | P0 |
| merit_api.py:276-295 | Wire strict CSP (default-src 'self'; script-src 'self'; style 'unsafe-inline'; no eval); HSTS gated on DAANAA_PROD env var | P2 | P0 |
| merit_api.py:614-622 | Strip -999 sentinels from /api/stats reserve buckets — use BETWEEN -120 AND 120 consistently | P3 | MEDIUM |
| merit_api.py:876-894 | claim_start: return `log_only` (not `letter_sent`) when Lob key absent; honest status propagated to DB and response | P3 | MEDIUM |
| scripts/overnight_pipeline.py:9 | Fix DB target meritgiving.db → merit_registry.db (overnight enrichment was writing to dead DB) | P9 | P0 |
| frontend/src/contexts/GivingListContext.tsx | Add `donateUrl?: string` to GivingListItem | P1 | MEDIUM |
| frontend/src/pages/OrganizationDetail.tsx | Pass `donateUrl` into givePayload — carries verified donate link into wallet/confirmation | P1 | P0 |
| frontend/src/components/OrgCard.tsx | Pass `donateUrl` in both addItem calls | P1 | MEDIUM |
| frontend/src/pages/GivingConfirmation.tsx | 0.3a: Remove "Daanaa emails it to you" letter promise — replace with "Request a receipt from the org" | P3,P8 | MEDIUM |
| frontend/src/pages/GivingConfirmation.tsx | 0.3b: Route "Complete your gift" to verified donate_url; no Lob key → plain text fallback (no Google search) | P1 | P0 |
| frontend/src/components/OrgList.tsx | "MeritGiving Organizations" → "Daanaa Organizations" (user-visible rebrand) | P3 | HIGH |
| venv/lib | Upgrade idna 3.13→3.17, starlette 1.0.0→1.2.0 (MEDIUM CVEs with available fix) | P9 | MEDIUM |
| docs/reviews/raw/ | pip_audit.txt, npm_audit.txt — 0 HIGH/CRITICAL remaining | P9 | — |

### Remaining after this PR
- transformers 2× MEDIUM CVE — no stable fix; ML-only, not on API path — document and revisit
- MERIT_ADMIN_KEY still accepted as fallback — remove after .env migration confirmed
- send_claim_letter.py:86 — verify_url embeds raw pin (0.2a); tracked for PR-0b

## Gate 0 close (2026-05-28)

| file | what | principle(s) | severity |
|------|------|--------------|----------|
| app.py | Deleted legacy FastAPI app (28KB, dead since daanaa_api.py/merit_api.py replaced it) | P9 | LOW |

### Stray DBs — documented, not deleted (human decision)
- `data/meritgiving.db` — legacy DB; overnight_pipeline now fixed to ignore it; safe to delete after confirming no unique hand-applied data
- `data/merit_state.db` — purpose unclear; inspect before deletion
- `data/merit_registry_backup.db` — backup of canonical DB; keep until next clean backup cycle

### ▶ MILESTONE GATE 0 — CLOSED 2026-05-28
All criteria met:
- ✅ All P0 security fixes merged (PR-0a + PR-0b)
- ✅ DB schema fully reconstructable from code (org_claims DDL now in merit_api.py)
- ✅ Principle-test suite green (12/12, tests/test_principles.py)
- ✅ Rebrand complete (user-visible strings, env vars, package name, dead files)
- ✅ overnight_pipeline writing to correct DB (merit_registry.db)
- ✅ CSP + hmac.compare_digest + opaque claim tokens in place
