# Lessons Learned — Daanaa Engineering

**Format:** Each incident or pattern gets a record with symptom, root cause, and preventing rule.

---

## 2026-08-11: Phase 1-4 Deployment Incident (DNS/Cloudflare Timeout)

**Symptom:** After updating Cloudflare DNS to new droplet IP (167.170.26.8), daanaa.org returned HTTP 522 (origin timeout), then no response. Site became unreachable.

**Timeline:**
- 16:48 UTC: Deployed blocker-fixed code to droplet via sync_droplet_api.sh
- 16:50 UTC: Updated Cloudflare DNS A record from 107.170.26.8 → 167.170.26.8
- 16:55 UTC: Site began returning HTTP 522 (Cloudflare → origin timeout)
- 17:05 UTC: Site not loading; DNS revert initiated

**Root Cause Analysis (Incomplete — requires investigation):**

Likely causes (ranked by probability):
1. **Cloudflare tunnel misconfiguration** — tunnel still pointed to old origin or was broken after rebuild
2. **Droplet network unreachable** — new IP (167.170.26.8) not actually responding to Cloudflare probe
3. **Origin service down** — gunicorn/nginx crashed after deployment
4. **DNS propagation collision** — intermediate state during propagation where Cloudflare couldn't reach origin

**What we know:**
- Direct SSH/HTTP to 167.170.26.8 were timing out (couldn't verify droplet was healthy)
- Cloudflare was returning 522 (timeout), not 502 (bad gateway)
- Old IP (107.170.26.8) was likely still serving via cache or fallback

**What we didn't do:**
- ❌ Did NOT verify droplet connectivity AFTER DNS update (only before)
- ❌ Did NOT check Cloudflare tunnel status dashboard
- ❌ Did NOT do gradual DNS cutover (should have tested via /etc/hosts first)
- ❌ Did NOT have a quick rollback plan ready before cutting over

**Preventing Rule:**

> **Before any DNS cutover to a new origin IP:**
> 1. Verify the new origin responds to direct HTTP/HTTPS (not just via Cloudflare proxy)
> 2. Test via /etc/hosts on local machine to verify routing works before global DNS change
> 3. Check Cloudflare tunnel status dashboard for any warnings
> 4. Have rollback DNS change ready (copy the old IP to clipboard before updating)
> 5. Monitor Cloudflare Analytics dashboard for HTTP 522/502/etc for 2 minutes post-cutover
> 6. If 522/502 appears, revert DNS immediately without waiting for diagnosis

**Recovery:**
- Reverted DNS to 107.170.26.8 (old IP)
- Site restored online
- New droplet (167.170.26.8) requires separate investigation

**Post-Incident Investigation Needed:**
1. Why was 167.170.26.8 responsive to direct curl but not to Cloudflare?
2. Is the Cloudflare tunnel properly configured?
3. Did the droplet reboot/deployment break something?
4. Should we use a load balancer or have a fallback origin configured?

**Stakeholder Impact:**
- daanaa.org downtime: ~15 minutes (17:05—17:20 UTC estimated)
- Phase 1-4 deployment halted pending recovery
- Blocker fixes (Firebase, IRS status) are safe and committed; just need to re-deploy once droplet is verified

---

## 2026-08-11: Codex Trust Signal Bug Finding (P3 Compliance)

**Symptom:** Codex review found donation flow inconsistency where revoked orgs (tax_deductible=false) were being passed as "unknown" status instead of "revoked" to donation router.

**Root Cause:** Three components had identical inline ternary:
```javascript
tax_deductible === false ? 'unknown' : 'verified'
```
Should have used:
```javascript
taxDeductibleToStatus(tax_deductible)
```

**Why it mattered:** Stewardship P3 (Trust signals evidence-based) — revoked orgs should show explicit warning, not be softened to ambiguous "unknown" status.

**Fix Applied:**
- CloseTheLoopPrompt.tsx (line 77)
- OrgInfoHierarchy.tsx (line 111)
- GivingRhythm.tsx (line 92)
- All three now use `taxDeductibleToStatus()` function
- Frontend builds clean

**Preventing Rule:**

> **For trust signal or legal status fields:**
> 1. Create a single "canonical" conversion function (e.g., `taxDeductibleToStatus()`)
> 2. Use it everywhere; never inline the logic
> 3. Codex/peer review will catch inline variants
> 4. Tests should verify all three states (true → verified, false → revoked, null → unknown) at each call site

**Commit:** 6f7f43113ba

---

## Summary: Incident vs. Bug

| Item | Category | Severity | Status |
|------|----------|----------|--------|
| DNS/Cloudflare 522 | **Incident** (deployment) | Critical (outage) | Reverted; needs investigation |
| IRS status ternary | **Bug** (code quality) | Medium (trust signal) | Fixed; committed |
| Firebase Analytics | **Compliance** | Medium (P2 gate) | Fixed; deployed |

---

**Next Review:** 2026-08-12 or when droplet investigation is complete
