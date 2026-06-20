# Monitoring & Alerting Setup

Keep the automation stack healthy and alert Akbar when something breaks.

---

## Real-Time Monitoring

### Chatwoot Health

**What to watch:**
- Incoming email/call volume (should be stable)
- Conversation response time (target: <24h for escalations)
- Conversation backlog count (target: <10 unresolved)

**Dashboard:**
```bash
# Open Chatwoot UI
open http://localhost:3000

# Daily report query (via psql)
docker-compose -f /opt/chatwoot/docker-compose.yml exec -T postgres psql -U postgres -d chatwoot_production -c "
  SELECT COUNT(*) as unresolved_tickets
  FROM conversations
  WHERE status = 'open';
"
```

### n8n Workflow Execution

**What to watch:**
- Email intent detection accuracy (target: >90%)
- Workflow execution errors (target: 0/hour)
- Execution time per email (target: <30 sec)

**Check logs:**
```bash
docker logs -f chatwoot_n8n_1 2>&1 | grep -E "executed|error|failed"
```

### Jambonz Call Quality

**What to watch:**
- Incoming call volume
- Call completion rate (made it to Chatwoot ticket)
- SIP trunk connection status

**Check status:**
```bash
# Verify SIP port is listening
netstat -tlnp | grep :5060

# Check for SIP errors
docker logs -f chatwoot_jambonz_1 2>&1 | grep -i "sip\|error"
```

---

## Automated Alerting

### Setup Email Alerts (via n8n)

Create a new n8n workflow: "Health Check & Alert"

**Trigger:** Cron job, every 30 minutes

**Logic:**
```
1. Query Chatwoot for unresolved ticket count
2. Query n8n execution logs for errors
3. Check if Jambonz is responding to test calls
4. If any metric exceeds threshold:
   → Send email to Akbar at akbar.khowaja@gmail.com
   → Include metric value + recommended action
```

**Workflow nodes:**

```json
{
  "nodes": [
    {
      "name": "Cron Trigger",
      "type": "Cron",
      "cron": "*/30 * * * *"
    },
    {
      "name": "Check Chatwoot Backlog",
      "type": "HTTP Request",
      "method": "GET",
      "url": "http://chatwoot:3000/api/v1/account/conversations",
      "headers": { "Authorization": "Bearer $CHATWOOT_TOKEN" }
    },
    {
      "name": "Check n8n Errors",
      "type": "HTTP Request",
      "method": "GET",
      "url": "http://n8n:5678/api/v1/executions?status=error&limit=10",
      "headers": { "X-N8N-API-KEY": "$N8N_API_KEY" }
    },
    {
      "name": "Check Jambonz Health",
      "type": "HTTP Request",
      "method": "GET",
      "url": "http://jambonz:3000/health"
    },
    {
      "name": "Evaluate Thresholds",
      "type": "Function",
      "code": "
        const unresolved = $node['Check Chatwoot Backlog'].json.count;
        const errors = $node['Check n8n Errors'].json.count;
        const jambonzHealthy = $node['Check Jambonz Health'].json.status === 'ok';
        
        let alerts = [];
        
        if (unresolved > 15) {
          alerts.push({
            severity: 'warning',
            message: 'High backlog: ' + unresolved + ' unresolved tickets',
            action: 'Review and prioritize oldest tickets'
          });
        }
        
        if (errors > 5) {
          alerts.push({
            severity: 'critical',
            message: 'High error rate: ' + errors + ' failures in last 30 min',
            action: 'Check n8n credentials and webhook endpoints'
          });
        }
        
        if (!jambonzHealthy) {
          alerts.push({
            severity: 'critical',
            message: 'Jambonz is not responding',
            action: 'Restart Jambonz: docker-compose -f /opt/jambonz/docker-compose.yml restart'
          });
        }
        
        return { alerts_count: alerts.length, alerts: alerts };
      "
    },
    {
      "name": "Send Alert Email",
      "type": "Gmail",
      "condition": "$node['Evaluate Thresholds'].json.alerts_count > 0",
      "to": "akbar.khowaja@gmail.com",
      "subject": "⚠️ Daanaa Automation Alert",
      "htmlBody": "
        <h2>{{ $node['Evaluate Thresholds'].json.alerts_count }} Alert(s) Detected</h2>
        {{ $node['Evaluate Thresholds'].json.alerts.map(a => 
          '<p><strong>[' + a.severity.toUpperCase() + ']</strong> ' + a.message + '<br/>Action: ' + a.action + '</p>'
        ).join('') }}
        <p><a href='http://localhost:3000'>Open Chatwoot</a></p>
      "
    }
  ]
}
```

---

## Daily Health Report (Automated)

**When:** Every Monday at 9 AM UTC  
**What:** Aggregate metrics email to Akbar

**Workflow: "Weekly Health Summary"**

```json
{
  "trigger": "Cron at 09:00 UTC on Monday",
  "steps": [
    {
      "name": "Fetch Weekly Stats",
      "queries": [
        "Total emails received: SELECT COUNT(*) FROM metrics WHERE timestamp > NOW() - '7 days' AND source='email'",
        "Auto-response rate: SELECT COUNT(CASE WHEN auto_responded THEN 1 END) / COUNT(*) FROM email_metrics WHERE timestamp > NOW() - '7 days'",
        "Escalation rate: SELECT COUNT(CASE WHEN escalated THEN 1 END) / COUNT(*) FROM email_metrics WHERE timestamp > NOW() - '7 days'",
        "Voice calls received: SELECT COUNT(*) FROM metrics WHERE source='voice' AND timestamp > NOW() - '7 days'",
        "Avg response time (hours): SELECT AVG(EXTRACT(EPOCH FROM (responded_at - created_at))/3600) FROM conversations WHERE responded_at IS NOT NULL AND created_at > NOW() - '7 days'"
      ]
    },
    {
      "name": "Format Report",
      "body": "
        <h1>📊 Weekly Automation Report</h1>
        <table border='1'>
          <tr><th>Metric</th><th>Value</th><th>Target</th><th>Status</th></tr>
          <tr><td>Emails Received</td><td>{{ emails }}</td><td>5-50</td><td>{{ emailsStatus }}</td></tr>
          <tr><td>Auto-Response Rate</td><td>{{ autoResponseRate }}%</td><td>>75%</td><td>{{ autoResponseStatus }}</td></tr>
          <tr><td>Escalation Rate</td><td>{{ escalationRate }}%</td><td><30%</td><td>{{ escalationStatus }}</td></tr>
          <tr><td>Voice Claims</td><td>{{ voiceCalls }}</td><td>1-10</td><td>{{ voiceStatus }}</td></tr>
          <tr><td>Avg Response Time</td><td>{{ avgResponseTime }} hrs</td><td><24 hrs</td><td>{{ responseTimeStatus }}</td></tr>
        </table>
        <h3>Issues This Week</h3>
        <ul>
          {{ issues.map(i => '<li>' + i + '</li>').join('') }}
        </ul>
        <h3>Tuning Recommendations</h3>
        <ul>
          {{ recommendations.map(r => '<li>' + r + '</li>').join('') }}
        </ul>
      "
    },
    {
      "name": "Send Email",
      "to": "akbar.khowaja@gmail.com",
      "subject": "📊 Daanaa Weekly Report"
    }
  ]
}
```

---

## Manual Monitoring Checklist

**For when alerts fail or need manual verification**

### Every Morning (5 min)

```bash
#!/bin/bash

echo "=== CHATWOOT HEALTH ==="
docker exec chatwoot_postgres_1 psql -U postgres -d chatwoot_production -c \
  "SELECT COUNT(*) as unresolved FROM conversations WHERE status='open';"
# Expected: <10

echo "=== N8N HEALTH ==="
curl -s http://localhost:5678/api/v1/workflows | jq '.data | map(select(.active==false))'
# Expected: empty (all workflows active)

echo "=== JAMBONZ HEALTH ==="
netstat -tlnp | grep :5060
# Expected: showing LISTEN on port 5060

echo "=== RECENT ERRORS ==="
docker logs --since 2h --tail 20 n8n 2>&1 | grep -i error || echo "No recent errors"

echo "=== DISK SPACE ==="
df -h /data
# Expected: >20GB free
```

### Every Monday (15 min)

```bash
#!/bin/bash

# 1. Check Metabase dashboard manually
open http://localhost:3000/dashboard/1

# 2. Review Chatwoot conversation summaries
# Settings → Reports → Conversation Summary

# 3. Check database disk usage
docker exec chatwoot_postgres_1 du -sh /var/lib/postgresql/data
# Expected: <5GB

# 4. Review error logs for patterns
docker logs --since 7d n8n 2>&1 | grep -i error | sort | uniq -c | sort -rn
```

---

## Incident Response Playbook

### Incident: High Email Backlog (>15 unresolved)

**Alert received:** Email from health check workflow  
**Time to respond:** Within 1 hour

**Diagnosis:**
1. Open Chatwoot dashboard
2. Count unresolved tickets by age
3. Check if auto-response rate dropped or stayed high

**Resolution:**

**Case A: Auto-response rate is high (>75%), but manual tickets piling up**
- Likely cause: Akbar hasn't reviewed escalations in a while
- Action: Batch review 5 old tickets, mark resolved
- Prevention: Set 24-hour response SLA alert for escalations

**Case B: Auto-response rate dropped (<60%)**
- Likely cause: New email patterns not being detected
- Action: Review last 10 escalations, identify pattern
- Fix: Add new intent keywords to n8n Intent Detector
- Test: Send 3 test emails with new pattern before re-enabling

**Case C: System is slow/errors spiking**
- Likely cause: Service overload or database full
- Actions:
  1. Check system resources: `htop`, `df -h`
  2. Check database size: `psql -d chatwoot_production -c 'SELECT pg_size_pretty(pg_database_size(current_database()))'`
  3. If >90% full: truncate old logs/metrics
  4. Restart services if needed

---

### Incident: No Incoming Emails for 30 min

**Alert received:** Health check shows 0 emails in last 30 min (unusual)  
**Time to respond:** Within 5 minutes

**Diagnosis:**
1. Check Gmail trigger is still enabled in n8n
2. Verify daanaa@daanaa.org is still receiving emails (test send one)
3. Check n8n error logs

**Resolution:**

**Case A: Gmail trigger is disabled or crashed**
- Action: Restart n8n
- Command: `docker-compose -f /opt/n8n/docker-compose.yml restart`
- Verify: Wait 60s, send test email, should receive within 5 min

**Case B: Gmail authentication expired**
- Action: Re-authenticate Gmail in n8n
- Steps:
  1. Open n8n UI
  2. Credentials → Gmail
  3. Click "Reauthenticate"
  4. Follow OAuth flow
  5. Test workflow

**Case C: Email volume actually dropped (no real issue)**
- Action: No action needed, monitor for return to normal

---

### Incident: Jambonz Not Answering Calls

**Alert received:** Call test fails, Jambonz health check returns `not_ok`  
**Time to respond:** Immediately (calls are failing)

**Diagnosis:**
1. Check if Jambonz container is running
2. Check if SIP port 5060 is listening
3. Check Voxbeam account (is DID still active?)

**Resolution:**

**Case A: Container crashed**
- Command: `docker-compose -f /opt/jambonz/docker-compose.yml restart`
- Verify: Wait 30s, test call should work

**Case B: SIP port not listening**
- Issue: Port binding failed (another service using it?)
- Action:
  1. Find process: `lsof -i :5060`
  2. Kill if it's not Jambonz: `kill -9 <PID>`
  3. Restart Jambonz

**Case C: Voxbeam DID issue**
- Issue: Account suspended or DID disabled
- Action:
  1. Log into Voxbeam: https://www.voxbeam.com/user
  2. Check account balance (needs >$5)
  3. Check DID status (should be "Active")
  4. If disabled, contact support or re-enable

---

## Logging & Retention

### What to Log

Every automation workflow should log:
- Execution timestamp
- Input data (anonymized)
- Decision made (which branch taken)
- Output (ticket created? response sent?)
- Any errors or timeouts

### Log Retention

- **Chatwoot logs:** Keep 90 days (PostgreSQL backup)
- **n8n logs:** Keep 30 days (Docker logs rotation)
- **Jambonz logs:** Keep 30 days
- **Metabase metrics:** Keep forever (aggregated data)

---

## Health Check Script (Run Manually)

```bash
#!/bin/bash
# File: /home/akbar/meritgiving/scripts/health_check.sh
# Usage: bash health_check.sh
# Run every morning to verify all systems are healthy

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         Daanaa Automation Stack Health Check              ║"
echo "╚════════════════════════════════════════════════════════════╝"

# 1. Docker containers
echo ""
echo "📦 CONTAINER STATUS"
docker-compose -f /opt/chatwoot/docker-compose.yml ps 2>/dev/null | tail -5
STATUS=$?
if [ $STATUS -eq 0 ]; then echo "✅ Chatwoot"; else echo "❌ Chatwoot"; fi

docker-compose -f /opt/n8n/docker-compose.yml ps 2>/dev/null | tail -3
STATUS=$?
if [ $STATUS -eq 0 ]; then echo "✅ n8n"; else echo "❌ n8n"; fi

docker-compose -f /opt/jambonz/docker-compose.yml ps 2>/dev/null | tail -3
STATUS=$?
if [ $STATUS -eq 0 ]; then echo "✅ Jambonz"; else echo "❌ Jambonz"; fi

# 2. API endpoints
echo ""
echo "🌐 ENDPOINT STATUS"
curl -s http://localhost:3000/health &>/dev/null && echo "✅ Chatwoot API" || echo "❌ Chatwoot API"
curl -s http://localhost:5678 &>/dev/null && echo "✅ n8n UI" || echo "❌ n8n UI"

# 3. Database connectivity
echo ""
echo "💾 DATABASE STATUS"
docker exec chatwoot_postgres_1 pg_isready &>/dev/null && echo "✅ PostgreSQL (Chatwoot)" || echo "❌ PostgreSQL (Chatwoot)"

# 4. SIP trunk
echo ""
echo "📞 TELEPHONY STATUS"
netstat -tlnp 2>/dev/null | grep -q :5060 && echo "✅ SIP Port 5060" || echo "❌ SIP Port 5060 not listening"

# 5. Disk space
echo ""
echo "💿 DISK USAGE"
DISK=$(df /data | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK" -lt 80 ]; then echo "✅ /data: ${DISK}% used"; else echo "⚠️  /data: ${DISK}% used (FULL!)"; fi

# 6. Unresolved tickets
echo ""
echo "📋 BACKLOG STATUS"
UNRESOLVED=$(docker exec chatwoot_postgres_1 psql -U postgres -d chatwoot_production -c "SELECT COUNT(*) FROM conversations WHERE status='open';" 2>/dev/null | grep -oE '[0-9]+' | head -1)
if [ -z "$UNRESOLVED" ]; then echo "⚠️  Could not fetch count"; else
  if [ "$UNRESOLVED" -lt 10 ]; then echo "✅ Unresolved: $UNRESOLVED (<10)"; else echo "⚠️  Unresolved: $UNRESOLVED (>10)"; fi
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║ Check complete. Address any ❌ issues immediately.          ║"
echo "╚════════════════════════════════════════════════════════════╝"
```

Make it executable:
```bash
chmod +x /home/akbar/meritgiving/scripts/health_check.sh
```

Run daily:
```bash
/home/akbar/meritgiving/scripts/health_check.sh
```

---

## Alert Thresholds

| Metric | Yellow (Warning) | Red (Critical) | Response Time |
|--------|---|---|---|
| Unresolved tickets | >10 | >20 | 1 hour |
| Email backlog (unparsed) | >50 | >100 | 30 min |
| n8n workflow errors/hour | >1 | >5 | 30 min |
| Chatwoot uptime | <99% | <95% | 5 min |
| Jambonz call failures | >10% | >30% | 15 min |
| Response time to escalation | >12h | >24h | 2 hours |
| Database disk usage | >75% | >90% | 2 hours |
| Avg email processing time | >60s | >120s | N/A (investigate) |
