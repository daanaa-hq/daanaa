# Phase 1 Monitoring Dashboard

**Period:** Aug 1-7, 2026  
**Metric Cadence:** Daily checks  
**Escalation:** Critical issues → immediate investigation

---

## Daily Checklist

### Morning (9am CDT)
- [ ] Check Plausible: Any new errors in signals endpoint?
- [ ] Verify IRS sync ran overnight (check /tmp/irs_sync.log)
- [ ] Spot-check 3 random orgs: Signals match IRS website

### Evening (6pm CDT)
- [ ] Org page load time: Should be <150ms
- [ ] Search performance: Should be <1s (cached queries <100ms)
- [ ] API error rate: Should be 0% for signals endpoint

---

## Weekly Report (Fridays)

**Week 1 (Aug 8):**
- Signal accuracy: Random sample of 10 orgs
- API uptime: Percentage 200 responses
- User feedback: Any issues reported?
- Performance trends: Load times stable/improving/degrading?

---

## Critical Alerts

| Alert | Threshold | Action |
|-------|-----------|--------|
| Signals endpoint errors | >5% | Page on-call, investigate |
| Org page load time | >500ms | Check database query, check droplet load |
| IRS sync failure | No sync for 24h+ | Restart daemon, check S3 connectivity |
| Search degradation | >3s for repeated query | Check FTS index, restart API |

---

## Success Metrics (Aug 7 Gate)

✅ Signal accuracy: ≥95% (spot check 10 random orgs)  
✅ API uptime: 99.5%+ (signals endpoint)  
✅ Page performance: <200ms (org detail pages)  
✅ Zero critical bugs reported  
✅ IRS sync: <24h lag on all updates  

If all ✅ → Proceed to Phase 2  
If any ❌ → Debug and retry Aug 7

