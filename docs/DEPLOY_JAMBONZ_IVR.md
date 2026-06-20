# Deploy Jambonz Voice IVR (Day 2)

## Target: Home Server (Ryzen + R9700)

### Prerequisites
- Docker + Docker Compose installed
- SIP trunk account (Voxbeam / Plivo)
  - **Recommended:** Voxbeam (opensource-friendly, ~$20/mo)
  - DIDs available: $1-3/mo per number

### Step 1: Get SIP Trunk

**Voxbeam Setup (5 min)**
1. Sign up: https://www.voxbeam.com
2. Add credit ($20)
3. Order DID: +1 (833) DAANAA-2 (check availability)
4. Settings → SIP → Enable DID for SIP routing
5. Webhook/SIP endpoint: `sip.daanaa.org:5060` (or home server IP:5060)

**Store these credentials:**
```
SIP_TRUNK_USERNAME: your_voxbeam_sip_user
SIP_TRUNK_PASSWORD: your_voxbeam_sip_password
SIP_TRUNK_DOMAIN: voxbeam.com
DID_NUMBER: +1-833-DAANAA-2
```

---

### Step 2: Deploy Jambonz on Home Server

**Docker Compose File** (`/opt/jambonz/docker-compose.yml`)

```yaml
version: '3.8'

services:
  jambonz:
    image: jambonz/jambonz-core:latest
    environment:
      JAMBONZ_MYSQL_HOST: mysql
      JAMBONZ_MYSQL_USER: jambonz
      JAMBONZ_MYSQL_PASSWORD: jambonz_secure_password_change_me
      JAMBONZ_SIP_PORT: 5060
      JAMBONZ_TLS_PORT: 5061
      NODE_ENV: production
      DEBUG: jambonz:*
    ports:
      - "5060:5060/udp"
      - "5060:5060/tcp"
      - "5061:5061/tcp"
      - "3000:3000"  # Web UI (admin)
    depends_on:
      - mysql
    restart: unless-stopped
    volumes:
      - ./config:/etc/jambonz

  mysql:
    image: mysql:8
    environment:
      MYSQL_ROOT_PASSWORD: jambonz_root_password_change_me
      MYSQL_DATABASE: jambonz
      MYSQL_USER: jambonz
      MYSQL_PASSWORD: jambonz_secure_password_change_me
    volumes:
      - mysql_data:/var/lib/mysql
    restart: unless-stopped

volumes:
  mysql_data:
```

**Deploy:**
```bash
mkdir -p /opt/jambonz
cd /opt/jambonz
# Copy docker-compose.yml (above) to this directory
docker-compose up -d
```

---

### Step 3: Configure Jambonz Admin

1. **Access Web UI:** http://home-server-ip:3000
2. **Login:** (default admin/admin or create account)
3. **Add Carrier (SIP Trunk)**
   - Carrier name: "Voxbeam"
   - Outbound SIP Proxy: `voxbeam.com:5060`
   - SIP Username: (from step 1)
   - SIP Password: (from step 1)

4. **Add DID Route**
   - DID: `+1-833-DAANAA-2`
   - Route to: "Nonprofit Claim IVR" (webhook)

5. **Create Application: Nonprofit Claim IVR**
   - Name: "Nonprofit Claim"
   - Type: "Webhook"
   - Webhook URL: `http://localhost:8000/ivr/claim` (or n8n endpoint)

---

### Step 4: Voice Script

**Simple IVR Flow (Jambonz application):**

```json
{
  "name": "Nonprofit Claim",
  "application": {
    "say": {
      "text": "Welcome to Daanaa. Press 1 to claim your nonprofit page."
    },
    "listen": {
      "maxSpeechTime": 5,
      "digits": {
        "1": {
          "say": "Please say your organization's EIN, for example: 46-3120432"
        },
        "0": {
          "say": "To reach support, email support at daanaa dot org. Goodbye.",
          "hangup": {}
        }
      }
    }
  }
}
```

**Collect EIN → Create Ticket:**
- Speech recognition: EIN number (e.g., "46-3120432")
- Validate: Check against registry database
- Webhook to n8n: `POST /claim/verify` with EIN + phone
- Response: "Check your email for claim link"
- Chatwoot ticket auto-created for manual review

---

### Step 5: Test

```bash
# From any phone
call +1 (833) DAANAA-2

# You should hear:
# "Welcome to Daanaa. Press 1 to claim your nonprofit page."

# Press 1 → 
# "Please say your organization's EIN, for example: 46-3120432"

# Say: "46 3120432" (or similar)

# System responds:
# "Verifying... [wait] ...thank you. Check your email for your claim link."

# Chatwoot ticket created with:
# - EIN: 46-3120432
# - Org name: (looked up from registry)
# - Phone: (caller ID)
# - Timestamp
```

---

### Step 6: Connect to n8n (Day 3)

Once n8n is running, configure:

**Jambonz Application → n8n Webhook**
```
POST http://n8n-server:5678/webhook/claim-verify
{
  "ein": "46-3120432",
  "phone": "+1-555-0123",
  "transcript": "forty six three one two zero four three two"
}
```

**n8n Workflow:**
1. Receive webhook
2. Validate EIN (check registry)
3. If valid: create Chatwoot ticket
4. If invalid: return error to Jambonz IVR
5. Send SMS/email with magic link

---

## Rollback / Cleanup

```bash
cd /opt/jambonz
docker-compose down -v  # Remove containers + volumes
```

## Status
- [ ] Voxbeam account created
- [ ] DID ordered
- [ ] Docker/Docker Compose on home server
- [ ] Jambonz containers running
- [ ] Web UI accessible
- [ ] SIP trunk configured
- [ ] IVR script deployed
- [ ] Test call successful
- [ ] Connected to n8n (Day 3)

