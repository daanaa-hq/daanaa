# Deploy n8n Email Triage (Day 3)

## Target: Home Server or Droplet (Ryzen + GPU or minimal)

n8n handles email routing, intent detection, and FAQ bot automation. All logic is visual (no code) and reusable.

---

## Step 1: Deploy n8n

**Docker Compose** (`/opt/n8n/docker-compose.yml`)

```yaml
version: '3.8'

services:
  n8n:
    image: n8n/n8n:latest
    environment:
      N8N_BASIC_AUTH_ACTIVE: 'true'
      N8N_BASIC_AUTH_USER: akbar
      N8N_BASIC_AUTH_PASSWORD: secure_password_change_me
      N8N_HOST: n8n.daanaa.org  # Or: home-server-ip:5678
      N8N_PORT: 5678
      N8N_PROTOCOL: http  # Change to https if using SSL
      WEBHOOK_URL: http://n8n.daanaa.org/  # External webhook base
      DB_TYPE: postgres
      DB_POSTGRES_HOST: postgres
      DB_POSTGRES_USER: n8n
      DB_POSTGRES_PASSWORD: n8n_secure_password_change_me
      DB_POSTGRES_DB: n8n
    ports:
      - "5678:5678"
    depends_on:
      - postgres
    restart: unless-stopped
    volumes:
      - n8n_data:/home/node/.n8n

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: n8n
      POSTGRES_USER: n8n
      POSTGRES_PASSWORD: n8n_secure_password_change_me
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  n8n_data:
  postgres_data:
```

**Deploy:**
```bash
mkdir -p /opt/n8n
cd /opt/n8n
# Copy docker-compose.yml to this directory
docker-compose up -d
```

Access: http://localhost:5678 (or http://home-server-ip:5678)

---

## Step 2: Configure Email Ingestion

**Create n8n Workflow: "Email Triage"**

### Node 1: Email Trigger
- Service: Gmail (or custom IMAP)
- Account: daanaa@daanaa.org
- Trigger on: New email
- Credentials: (set up in n8n credentials panel)

### Node 2: Intent Detection
- Type: "HTTP Request" (call local LLM or simple rule-based)
- **Option A (Rule-based):**
  ```javascript
  // Route by keyword
  const text = $node.previous.data[0].body;
  if (text.includes('give') || text.includes('donate')) {
    return { intent: 'donation_link', priority: 'medium' };
  } else if (text.includes('volunteer') || text.includes('hours')) {
    return { intent: 'volunteer_hours', priority: 'low' };
  } else if (text.includes('support') || text.includes('help')) {
    return { intent: 'support_ticket', priority: 'high' };
  } else {
    return { intent: 'unknown', priority: 'low' };
  }
  ```

- **Option B (LLM):**
  Call local Qwen/Llama (home server GPU):
  ```json
  {
    "prompt": "Classify this email intent: {{email_body}}\nChoose: donation_link, volunteer_hours, support_ticket, or unknown",
    "model": "qwen2.5-32b"
  }
  ```

### Node 3: Route by Intent

**IF Donation Link:**
- Semantic search: Find org by name in email
- Get donate URL from registry
- Auto-reply: "Donate directly: [link]"
- Mark as solved (no Chatwoot ticket)

**IF Volunteer Hours:**
- Auto-reply: "Log volunteer hours: [link to LogVolunteerHours page]"
- Mark as solved

**IF Support Ticket:**
- Create Chatwoot ticket:
  ```json
  {
    "api": "chatwoot",
    "endpoint": "POST /api/v1/inboxes/1/contacts_messages",
    "email": "{{email_from}}",
    "message": "{{email_body}}",
    "subject": "{{email_subject}}"
  }
  ```

**ELSE (Unknown):**
- Create Chatwoot ticket (escalate to human)
- Tag: "email-escalated"

### Node 4: Send Auto-Response (if applicable)

```json
{
  "service": "Gmail",
  "to": "{{email_from}}",
  "subject": "Re: {{email_subject}}",
  "body": "[Email template based on intent]"
}
```

### Node 5: Log to Metabase

```json
{
  "api": "http://metabase:3000/api/",
  "action": "log_email_metric",
  "data": {
    "timestamp": "{{$now}}",
    "intent": "{{intent}}",
    "auto_responded": true/false,
    "channel": "email"
  }
}
```

---

## Step 3: Configure FAQ Bot (Optional - Semantic Search)

**Create Separate Workflow: "FAQ Bot"**

1. **Trigger:** Incoming email with "?", "help", or "how"
2. **Semantic Search:**
   - Embed email query using local mxbai-embed-large (home server GPU)
   - Search against FAQ embeddings (pre-computed)
   - Return top 3 matches
3. **Match Confidence Check:**
   - If score > 0.8: Send auto-response + FAQ link
   - If score < 0.8: Create ticket (human review)

**FAQ Sources:**
- `daanaa.org/faq` (web scrape)
- `docs/CUSTOMER_SERVICE_STRATEGY.md` (manual)
- Historic email patterns (learn over time)

---

## Step 4: Test

**Manual Test:**
```bash
# Send email to daanaa@daanaa.org
# Subject: "How do I give to [Org Name]?"

# Expected:
# 1. n8n catches email (within 5 min)
# 2. Intent detected: "donation_link"
# 3. Auto-reply sent: "Donate directly: [link]"
# 4. No Chatwoot ticket created
```

**Test Intent Detection:**
- "I volunteered 10 hours" → volunteer_hours
- "I want to give $100" → donation_link
- "Your website is broken" → support_ticket
- "Hi there" → unknown (escalate)

**Metrics Check:**
- Metabase dashboard shows:
  - Emails received: N
  - Auto-responses sent: N
  - Escalation rate: N%
  - Response time: avg X min

---

## Step 5: Connect to Chatwoot

**n8n HTTP Request → Chatwoot API**

```json
{
  "method": "POST",
  "url": "http://chatwoot-api/api/v1/inboxes/1/messages",
  "auth": {
    "bearer": "{{chatwoot_api_token}}"
  },
  "body": {
    "content": "{{email_body}}",
    "email": "{{email_from}}",
    "source_id": "email",
    "custom_attributes": {
      "email_subject": "{{email_subject}}",
      "auto_classification": "{{intent}}",
      "escalated": true
    }
  }
}
```

**Chatwoot Setup:**
1. Get API token: Settings → API Tokens → Generate
2. Create inbox: "Email"
3. Get Inbox ID: Inboxes → [Email] → Settings
4. Store in n8n credentials

---

## Step 6: Backtest Rules

Before go-live, run n8n against historic emails:

```sql
-- Count emails by intent (simulate)
SELECT intent, COUNT(*) as count
FROM email_metrics
GROUP BY intent
ORDER BY count DESC;

-- Check auto-response accuracy
SELECT auto_responded, escalated, COUNT(*) 
FROM email_metrics
WHERE timestamp > NOW() - INTERVAL '1 day'
GROUP BY auto_responded, escalated;
```

**Target:**
- Auto-response rate: >70%
- Escalation rate: <30%
- Human accuracy on escalations: >90%

---

## Tuning

**Add Intent Patterns Over Time:**

After each week:
1. Review Chatwoot tickets tagged "email-escalated"
2. Extract new patterns
3. Update n8n intent detection rules
4. Re-test

**Example:**
```javascript
// Week 1: Added new intent
if (text.includes('refund') || text.includes('money back')) {
  return { intent: 'refund_request', priority: 'high' };
}
```

---

## Status
- [ ] PostgreSQL running
- [ ] n8n containers up
- [ ] Email credentials configured
- [ ] Intent detection rules built
- [ ] Chatwoot integration tested
- [ ] FAQ bot (optional) deployed
- [ ] Auto-response templates created
- [ ] Metabase metrics logging working
- [ ] Test emails classified correctly
- [ ] Go-live ready

