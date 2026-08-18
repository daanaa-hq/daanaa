# Codex Handoff: CRITICAL TASKS (2 Priorities)
**Date:** 2026-08-13  
**From:** Claude Code  
**To:** Codex  
**Urgency:** 🔴 CRITICAL — Two parallel priorities

---

## PRIORITY 1: Production Site Recovery

**Status:** 🔴 CRITICAL — daanaa.org API DOWN

**Symptoms:**
- Directory page returns "Unable to load organizations"
- API endpoints returning SPA fallback (HTML) instead of JSON
- SSH to droplet timing out (exit code 255)
- Droplet unreachable or service down

**Your Mission:**
1. Check droplet connectivity (167.170.26.8)
2. Verify droplet_api systemd service status
3. Restart if needed: `systemctl restart droplet_api`
4. Smoke test: `curl https://daanaa.org/api/health` should return JSON
5. Verify directory page loads: `https://daanaa.org/directory?sub=P33` should show results

**Timeline:** Immediate (within 1 hour)

---

## PRIORITY 2: Domain Guessing Engine (Production Scale)

**Status:** ✅ Script ready, needs Codex execution

**Your Mission:**
Execute the website discovery engine to find main links for 1.59M nonprofits.

### Script
```
scripts/continuous_discovery/domain_guess_engine.py
```

### Command (Full Authority Given)
```bash
source venv/bin/activate
nohup python3 scripts/continuous_discovery/domain_guess_engine.py \
  --limit 1000000 \
  --workers 16 \
  > logs/domain_guess_production_run.log 2>&1 &
```

### Execution Approach
- Use server hardware (droplet or local, your choice)
- Maximize parallelization (16-32 workers if resources allow)
- Monitor: `tail -f logs/domain_guess_production_run.log`
- Expected: 600K+ websites in 2-3 weeks

### Success Criteria
- [ ] Process starts without errors
- [ ] Log shows domain checks in progress
- [ ] 50K+ websites found in first 24 hours
- [ ] Database updates show `website_source='domain_guess'`

**Timeline:** Start after droplet recovery (Priority 1), or parallel if you want to use different hardware

---

## Your Autonomy

**Full authority to:**
- Restart/reboot droplet if needed
- Kill/restart services
- Pull code and execute without approval
- Adjust worker counts based on resource availability
- Escalate if hardware/network issues beyond your scope

---

## Handoff Documents Ready

- **Droplet Recovery:** Check systemd logs, restart service
- **Domain Guessing:** `docs/operations/deployment/handoffs/CODEX_HANDOFF_DOMAIN_GUESSING_ENGINE_PRODUCTION_20260813.md`
- **Monitoring:** `scripts/monitor_domain_guess.sh`

---

## Report Back When

1. **After Priority 1:** "Droplet API recovered. daanaa.org/api/health returns 200."
2. **After Priority 2 starts:** "Domain guessing engine running. X orgs/hour throughput."
3. **Daily:** "Found Y new websites. Still processing."

---

**Codex, you're cleared for full execution on both fronts. No waiting for approval. Just report status when complete.**

🚀 Go.

