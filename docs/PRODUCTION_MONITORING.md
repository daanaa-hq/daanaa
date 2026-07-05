# Phase 2 Production Monitoring

**Goal:** Track volunteer hours + guild system health in production

---

## Key Metrics to Monitor

### Volunteer Hours Pipeline

| Metric | Target | How to Check |
|--------|--------|--------------|
| Submissions/day | >0 | `SELECT COUNT(*) FROM volunteer_hours WHERE DATE(created_at) = TODAY` |
| Claim success rate | >80% | Claims with status='confirmed' / Claims attempted |
| Approval rate | >70% | Approved / (Approved + Rejected) |
| API latency p95 | <500ms | Check /api/stats response time |
| Error rate | <1% | 5xx errors / total requests |

### Guild System

| Metric | Target | How to Check |
|--------|--------|--------------|
| Guild page views | >10/day | Plausible analytics (daanaa.org/stats) |
| Guild display on org pages | 100% render | Manual test 3 random orgs |
| Member org links working | 100% | Spot check 5 links |

### System Health

| Metric | Target | How to Check |
|--------|--------|--------------|
| API uptime | >99.5% | Droplet systemctl status daanaa |
| Database query time | <10ms | Spot check guild lookup queries |
| Frontend bundle loads | <3s | Browser DevTools Network tab |

---

## User Feedback Collection

### Where to Look

1. **Email:**
   - Support inbox: akbar.khowaja+support@daanaa.org
   - Watch for issues, praise, feature requests

2. **In-App (Coming Soon):**
   - Add "Report a mistake" link on volunteer pages
   - Add feedback form after approval confirmation

3. **Manual Outreach:**
   - Contact 3-5 early nonprofits
   - Ask: "Is this working? Any blockers?"

### Feedback Template

When user reports an issue:
```
Date: [YYYY-MM-DD]
Feature: [volunteer hours / guild system]
Issue: [description]
User: [nonprofit EIN or email]
Severity: [low / medium / high / critical]
Status: [new / investigating / fixed / monitoring]
```

---

## Logging Checklist

### Volunteer Hours Endpoints
- [ ] POST /nonprofit/{ein}/volunteer/submit → log (nonprofit_ein, status, claim_code_prefix)
- [ ] POST /volunteer/claim → log (code_prefix, email_domain, success)
- [ ] GET /nonprofit/{ein}/volunteer/pending → log (nonprofit_ein, count)
- [ ] POST /nonprofit/{ein}/volunteer/{id}/approve → log (nonprofit_ein, status)
- [ ] POST /nonprofit/{ein}/volunteer/{id}/reject → log (nonprofit_ein, reason_length)

### Guild Endpoints
- [ ] GET /api/guild/:slug → log (slug, status, member_count)
- [ ] GET /api/org/{ein}/guild → log (ein, found, tier)

---

## Weekly Check-in (Every Monday)

### Monday 9am Check

1. **Error Log Scan** (5 min)
   ```bash
   ssh root@162.243.97.179 "tail -100 /opt/daanaa/logs/error.log | grep -E 'volunteer|guild'"
   ```

2. **Database Stats** (2 min)
   ```bash
   sqlite3 /home/akbar/meritgiving/data/merit_registry.db << 'SQL'
   SELECT 'Volunteer Hours' as metric, COUNT(*) FROM volunteer_hours
   UNION ALL
   SELECT 'Guild Memberships', COUNT(*) FROM guild_membership;
   SQL
   ```

3. **Email Check** (5 min)
   - Any user complaints?
   - Any praise worth noting?

4. **Manual Spot Check** (5 min)
   - Visit /partner/salesforce-nonprofit (page loads?)
   - Visit random org detail page (guild shows?)
   - Check /volunteer/submit on mobile (responsive?)

### Monthly Deep Dive (1st of month)

1. **Adoption metrics**
   - How many nonprofits used volunteer hours?
   - How many volunteers claimed?
   - Approval rate?

2. **Performance review**
   - Any latency spikes?
   - Any error patterns?

3. **User feedback synthesis**
   - What issues came up?
   - What features requested?
   - Priority for Phase 2.1?

---

## Incident Response

### If API is Down
1. Check service: `systemctl status daanaa`
2. Check logs: `tail -50 /opt/daanaa/logs/error.log`
3. Restart if safe: `systemctl restart daanaa`
4. If still down, escalate

### If Error Rate Spikes
1. Check recent deploys (did we break something?)
2. Check database (is it healthy?)
3. Check rate limits (are we being DoS'd?)
4. Roll back if necessary

### If Users Report Issues
1. Reproduce locally
2. Check if it's a data issue or code issue
3. Fix and deploy
4. Notify user of fix

---

## Data Points to Preserve

Keep these metrics quarterly for trend analysis:
- Total volunteer hours submitted
- Total volunteer hours claimed
- Approval rate
- Common rejection reasons
- Guild page traffic
- Error patterns

---

## Success Criteria (30 days)

✅ Zero critical bugs reported  
✅ >90% API uptime  
✅ <1% error rate  
✅ ≥5 nonprofits using volunteer hours  
✅ ≥10 volunteers claimed hours  
✅ No user complaints about bugs

---

**Last updated:** July 5, 2026  
**Next review:** July 12, 2026
