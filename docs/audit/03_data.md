# PHASE 3 — Data Credibility (ingest, freshness, tiers, revocations) — 2026-06-09

## Verdict: revocation data is ingested but not honored in browse — 192,501 revoked orgs
## are listed with no disclosure. One leaked credential needs rotation confirmation.

## What's clean (verified)
- **Freshness is stored AND shown:** `irs_sync_log` (last sync 2026-06-07, 1.2M checked,
  159,715 revocations processed). API returns `irs_status_verified_at` (org detail +
  /api/stats) and `scores_last_updated`. Frontend shows "IRS status verified <date>" on
  OrganizationDetail (:1099) and as-of dates on CauseSpotlight + ResearchDashboard. The
  HIGH "no freshness" finding from the audit hypothesis is largely FALSE — only the
  Directory listing lacks a global "data as of" line (LOW).
- **Donate gate fails closed on revocation:** `_is_revoked()` check at daanaa_api.py:882
  blocks the donate affordance for revoked orgs ✔ (matches link-health fail-closed posture).
- **Tier assignment:** canonical v4 path is `scripts/merit_scorer_v4_0.py` →
  `load_v4_scores_to_db.py`, with `validate_v4_scores.py` as a validation step (exists,
  deterministic inputs). Legacy threshold code lingers in merit_scorer_db.py (old labels).

## Findings

### CRITICAL
1. **192,501 revoked orgs listed with zero disclosure** — `daanaa_api.py:1096`. The base
   browse/search filter is only `subsection='3' AND deductibility='1'`; `irs_revoked` /
   `org_status` is consulted ONLY by the donate gate. Verified by query: 192,501 rows with
   `irs_revoked=1 OR org_status='revoked'` pass the filter. These orgs appear in the
   directory with names, missions, and tier badges — and no UI surface shows revoked
   status (grep: only Legal.tsx mentions the word). Donations to auto-revoked orgs are
   NOT tax-deductible — listing them as normal tax-deductible 501(c)(3)s violates
   stewardship principle 3 (trust signals must reflect real data).
   Fix (choose): (a) add `AND COALESCE(irs_revoked,0)=0 AND org_status!='revoked'` to
   `_DEDUCTIBILITY_FILTER`, or (b) keep listed but render a prominent "IRS status:
   auto-revoked" banner + suppress tier badge. (a) is one line; (b) preserves discovery.

### HIGH
2. **Leaked TiDB credential in git history** — `scripts/daily_sync.sh:2-4`. Header says the
   old hardcoded `DATABASE_URL` "was leaked in git history and MUST be rotated in the
   TiDB/Aliyun console." Rotation status unverified. Fix: confirm rotation happened; if
   repo ever goes public, scrub history (git filter-repo) first.

### MED
3. **Watchdog guards a deleted file** — crontab `*/15 * * * * pgrep -f merit_api.py || python3
   merit_api.py`. merit_api.py no longer exists, so this fires a failing start every 15 min
   AND the real gunicorn daanaa_api has no watchdog at all. Fix: point watchdog at gunicorn
   master (or `curl -sf localhost:5000/health || ./restart_api.sh`).
4. **BMF ingest has no validation gate** — `scripts/ingest_bmf_master.py`: no EIN format
   check, row-count delta guard, or dedupe logic found (blind `INSERT OR REPLACE`). Also
   218,775 rows have NULL/empty `irs_revoked` (status unknown). Fix: pre-commit row-count
   delta (±20% aborts), EIN `^\d{9}$` check, and backfill the NULL revocation statuses.

### LOW
5. **Directory lacks a global freshness line** — org detail shows it, but browse/search
   does not. Fix: surface `/api/stats.scores_last_updated` as "Data as of <date>" in
   Directory footer.
6. **Scorer sprawl** — 6+ scorer files (v2_0, db, tier_b, tier_c, v4_0, agent2). v4_0 is
   canonical; rest should move to archive/ to prevent a future agent running the wrong one.
