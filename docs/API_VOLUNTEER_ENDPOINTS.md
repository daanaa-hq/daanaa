# Volunteer Hours API Documentation

Base URL: `https://daanaa.org`

---

## Endpoints

### 1. Submit Volunteer Hours
**POST** `/api/nonprofit/{ein}/volunteer/submit`

Submit volunteer hours for approval. Requires nonprofit ownership verification via Firebase token.

#### Request
```bash
curl -X POST https://daanaa.org/api/nonprofit/360822808/volunteer/submit \
  -H "Authorization: Bearer {firebase_id_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "volunteer_name": "John Doe",
    "volunteer_email": "john@example.com",
    "hours": 5.5,
    "service_date": "2026-07-04",
    "activity_description": "Event setup and registration"
  }'
```

#### Request Body
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| volunteer_name | string | Yes | Volunteer full name (max 200 chars) |
| volunteer_email | string | Yes | Email address (max 254 chars, valid format) |
| hours | number | Yes | Hours worked (must be > 0, < 999) |
| service_date | string | Yes | Date worked (ISO format: YYYY-MM-DD) |
| activity_description | string | Yes | What they helped with (max 500 chars) |

#### Response (201 Created)
```json
{
  "claim_code": "VOL-ABC123DEF456",
  "claim_url": "https://daanaa.org/volunteer/submit?code=VOL-ABC123DEF456"
}
```

#### Error Responses
- **400 Bad Request** — Missing required fields
- **401 Unauthorized** — No valid Firebase token
- **403 Forbidden** — Nonprofit ownership not verified
- **500 Server Error** — Database error

---

### 2. Claim Volunteer Hours
**POST** `/api/volunteer/claim`

Volunteer claims hours using claim code and email verification.

#### Request
```bash
curl -X POST https://daanaa.org/api/volunteer/claim \
  -H "Content-Type: application/json" \
  -d '{
    "code": "VOL-ABC123DEF456",
    "email": "john@example.com"
  }'
```

#### Request Body
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| code | string | Yes | Claim code from nonprofit (format: VOL-XXXXXXXXXX) |
| email | string | Yes | Email to verify (must match submitted email) |

#### Response (200 OK)
```json
{
  "status": "claimed",
  "message": "Hours claimed. Nonprofit will review."
}
```

#### Error Responses
- **400 Bad Request** — Missing code or email
- **403 Forbidden** — Email doesn't match submitted email
- **404 Not Found** — Invalid claim code
- **500 Server Error** — Database error

---

### 3. Get Pending Approvals
**GET** `/api/nonprofit/{ein}/volunteer/pending`

List volunteer hours awaiting nonprofit approval.

#### Request
```bash
curl https://daanaa.org/api/nonprofit/360822808/volunteer/pending \
  -H "Authorization: Bearer {firebase_id_token}"
```

#### Response (200 OK)
```json
[
  {
    "id": "VOL-ABC123DEF456",
    "volunteer_name": "John Doe",
    "volunteer_email": "john@example.com",
    "hours": 5.5,
    "service_date": "2026-07-04",
    "activity_description": "Event setup and registration",
    "status": "confirmed"
  },
  {
    "id": "VOL-XYZ789ABC123",
    "volunteer_name": "Jane Smith",
    "volunteer_email": "jane@example.com",
    "hours": 3.0,
    "service_date": "2026-07-05",
    "activity_description": "Data entry",
    "status": "pending"
  }
]
```

#### Error Responses
- **401 Unauthorized** — No valid Firebase token
- **403 Forbidden** — Nonprofit ownership not verified
- **500 Server Error** — Database error

---

### 4. Approve Volunteer Hours
**POST** `/api/nonprofit/{ein}/volunteer/{id}/approve`

Approve volunteer hours submission.

#### Request
```bash
curl -X POST https://daanaa.org/api/nonprofit/360822808/volunteer/VOL-ABC123DEF456/approve \
  -H "Authorization: Bearer {firebase_id_token}" \
  -H "Content-Type: application/json"
```

#### Response (200 OK)
```json
{
  "status": "approved"
}
```

#### Error Responses
- **401 Unauthorized** — No valid Firebase token
- **403 Forbidden** — Nonprofit ownership not verified
- **404 Not Found** — Volunteer hours record not found
- **500 Server Error** — Database error

---

### 5. Reject Volunteer Hours
**POST** `/api/nonprofit/{ein}/volunteer/{id}/reject`

Reject volunteer hours submission with optional reason.

#### Request
```bash
curl -X POST https://daanaa.org/api/nonprofit/360822808/volunteer/VOL-ABC123DEF456/reject \
  -H "Authorization: Bearer {firebase_id_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Hours are incorrect; please resubmit with correct times"
  }'
```

#### Request Body
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| reason | string | No | Reason for rejection (displayed to volunteer) |

#### Response (200 OK)
```json
{
  "status": "rejected"
}
```

#### Error Responses
- **401 Unauthorized** — No valid Firebase token
- **403 Forbidden** — Nonprofit ownership not verified
- **404 Not Found** — Volunteer hours record not found
- **500 Server Error** — Database error

---

## Authentication

All endpoints requiring nonprofit access need a valid Firebase ID token in the `Authorization` header:

```
Authorization: Bearer {firebase_id_token}
```

Get your token in the frontend:
```javascript
const idToken = await getIdToken();
const response = await fetch('/api/nonprofit/{ein}/volunteer/submit', {
  headers: {
    'Authorization': `Bearer ${idToken}`,
    'Content-Type': 'application/json'
  }
});
```

---

## Rate Limiting

- **POST endpoints:** 30 requests per hour per IP
- **GET endpoints:** 60 requests per hour per IP

Rate limit headers in response:
```
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 29
X-RateLimit-Reset: 1688573400
```

---

## Status Codes Reference

| Code | Meaning |
|------|---------|
| 200 | Success — Request completed |
| 201 | Created — Resource created successfully |
| 400 | Bad Request — Invalid parameters |
| 401 | Unauthorized — Missing or invalid token |
| 403 | Forbidden — Don't have permission |
| 404 | Not Found — Resource doesn't exist |
| 500 | Server Error — Internal error |

---

## Examples

### Complete Flow

1. **Nonprofit submits hours:**
```bash
curl -X POST https://daanaa.org/api/nonprofit/360822808/volunteer/submit \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "volunteer_name": "Alice",
    "volunteer_email": "alice@example.com",
    "hours": 4,
    "service_date": "2026-07-04",
    "activity_description": "Food prep"
  }'

# Response:
# {"claim_code":"VOL-XYZ789ABC123","claim_url":"https://daanaa.org/volunteer/submit?code=VOL-XYZ789ABC123"}
```

2. **Volunteer claims (triggered by email link):**
```bash
curl -X POST https://daanaa.org/api/volunteer/claim \
  -H "Content-Type: application/json" \
  -d '{
    "code": "VOL-XYZ789ABC123",
    "email": "alice@example.com"
  }'

# Response:
# {"status":"claimed","message":"Hours claimed. Nonprofit will review."}
```

3. **Nonprofit approves:**
```bash
curl -X POST https://daanaa.org/api/nonprofit/360822808/volunteer/VOL-XYZ789ABC123/approve \
  -H "Authorization: Bearer $TOKEN"

# Response:
# {"status":"approved"}
```

---

**Last updated:** July 4, 2026
