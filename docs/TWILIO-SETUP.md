# Twilio Setup for Nonprofit Claim System

## Current State
- Phone: (747) 832-2622
- Account: My first Twilio account (trial: $14.35)
- Voice routing: Active but pointing to demo
- SMS: Not configured
- Emergency address: Not registered

## What to Configure

### 1. Voice Webhook (Incoming Calls)
**Current:** `https://demo.twilio.com/welcome/voice/`  
**Change to:** `https://daanaa.org/api/claim/phone-callback` (or `http://localhost:5000/api/claim/phone-callback` for local testing)

**In Twilio Console:**
1. Go to Phone Numbers → (747) 832-2622 → Voice Configuration
2. Under "A call comes in", change URL to your endpoint
3. HTTP method: POST
4. Save

**Endpoint expects:**
```json
{
  "From": "+17478322622",
  "CallSid": "CA...",
  "AccountSid": "AC...",
  "ApiVersion": "2010-04-01"
}
```

Response should return TwiML (XML) for voice instructions.

### 2. SMS Webhook (Incoming SMS)
**Not yet configured.** Add:
1. Go to Phone Numbers → (747) 832-2622 → Messaging Configuration
2. Under "A message comes in", set URL to: `https://daanaa.org/api/claim/sms-callback`
3. HTTP method: POST
4. Save

**Endpoint expects:**
```json
{
  "From": "+1234567890",
  "To": "+17478322622",
  "Body": "...",
  "MessageSid": "SM..."
}
```

### 3. Emergency Address (Required)
**Status:** Not registered (will incur $75 charge per emergency call)

**Fix:**
1. Click "Add Emergency Address" button (top of page)
2. Fill in: Your nonprofit's legal address (or operational address)
3. Verify and save
4. Cost: One-time setup, protects against $75/call charges

**Recommended address:** Your organization's main office or headquarters

### 4. A2P 10DLC Registration (For SMS)
**Status:** Required for US messaging

**Process:**
1. Click "Initiate A2P 10DLC registration" (Messaging section)
2. Follow Twilio's brand/campaign registration
3. Takes ~24-48 hours
4. Free (included in Twilio)

---

## API Endpoints to Implement

### POST /api/claim/phone-callback
Handles incoming phone calls. Should:
1. Extract caller info (From, CallSid)
2. Look up claim status in org_claims table
3. Return TwiML response with voice instructions

Example TwiML:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="woman">Thank you for verifying your nonprofit claim.</Say>
  <Record maxLength="60" />
</Response>
```

### POST /api/claim/sms-callback
Handles incoming SMS. Should:
1. Extract message text
2. Validate against claim PIN or status
3. Return TwiML response with SMS reply

---

## Testing (Local)

Use `ngrok` to expose localhost to Twilio:
```bash
ngrok http 5000
```

Then update Twilio webhooks to point to:
- `https://{ngrok-url}/api/claim/phone-callback`
- `https://{ngrok-url}/api/claim/sms-callback`

This lets you test locally before deploying.

---

## Security Checklist

- [ ] Verify webhook signatures (Twilio sends X-Twilio-Signature header)
- [ ] Rate-limit phone callbacks (prevent abuse)
- [ ] Validate EIN format before processing
- [ ] Log all calls/SMS for compliance
- [ ] Use HTTPS only (no plain HTTP in production)
- [ ] Mask PII in logs (claim tokens, PINs)

---

## Cost Notes

- Inbound calls: $0.0075/min
- Inbound SMS: $0.0075/msg
- Emergency address: One-time setup
- A2P 10DLC: Free (included)
- Trial account: $14.35 available

For light usage (test phase), costs are minimal. Production pricing scales with volume.
