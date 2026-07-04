# Sprint 4: Donation Letter Generation

**Status:** ⏸️ BLOCKED BY LEGAL (can proceed when approved)  
**Estimated Effort:** 15 hours  
**Stewardship Impact:** HIGH (tax compliance, nonprofit communications)

---

## Legal Requirements (Gate: Attorney Review)

### IRS §170(f)(8) Compliance

Charitable contribution acknowledgment letters must:
- Be signed/issued by the nonprofit (not Daanaa)
- Provide org name, EIN, website
- State: "No goods/services provided in return" (if applicable)
- Disclose value of any benefits received
- Include tax year of donation
- Be delivered within reasonable time

### Daanaa's Role (Non-Merchant)
- **Do:** Generate template, route to nonprofit
- **Don't:** Hold funds, process payments, sign letters
- **Verify:** Nonprofit accepts liability for accuracy

### Compliance Verification Needed
- [ ] Template reviewed by attorney
- [ ] Nonprofit indemnification clause drafted
- [ ] IRS filing year sourced correctly from 990 data
- [ ] Test with real org before launch

---

## Database Schema

```sql
CREATE TABLE IF NOT EXISTS donation_letters (
  letter_id TEXT PRIMARY KEY,
  nonprofit_ein TEXT NOT NULL,
  donor_name TEXT NOT NULL,
  donor_email TEXT NOT NULL,
  donation_date TEXT,
  donation_amount DECIMAL(12,2),
  letter_type TEXT DEFAULT 'standard', -- standard|bequest|pledge
  tax_year INTEGER,
  filing_date TEXT,
  letter_html TEXT,
  pdf_url TEXT,
  status TEXT DEFAULT 'draft', -- draft|generated|sent|failed
  generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  sent_at TIMESTAMP,
  error_message TEXT,
  FOREIGN KEY(nonprofit_ein) REFERENCES registry_enriched(EIN)
);

CREATE TABLE IF NOT EXISTS donation_letter_templates (
  template_id INTEGER PRIMARY KEY AUTOINCREMENT,
  nonprofit_ein TEXT NOT NULL,
  template_html TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  approved_by_nonprofit_at TIMESTAMP,
  FOREIGN KEY(nonprofit_ein) REFERENCES registry_enriched(EIN)
);

CREATE INDEX idx_donation_letters_ein ON donation_letters(nonprofit_ein);
CREATE INDEX idx_donation_letters_status ON donation_letters(status);
```

---

## API Endpoints (Ready to Implement)

### 1. POST /api/nonprofit/{ein}/donation-letter/generate
Generate a donation letter for a donor.

**Request:**
```json
{
  "donor_name": "John Doe",
  "donor_email": "john@example.com",
  "donation_date": "2026-07-04",
  "donation_amount": 500.00,
  "letter_type": "standard"
}
```

**Response:**
```json
{
  "letter_id": "DL-ABC123XYZ",
  "status": "generated",
  "donor_name": "John Doe",
  "nonprofit_ein": "360822808",
  "letter_html": "<html>...",
  "pdf_url": "https://daanaa.org/api/donation-letter/DL-ABC123XYZ/pdf"
}
```

**Auth:** Firebase (nonprofit user only)  
**Implementation:** 2h

---

### 2. GET /api/donation-letter/{letter_id}
Retrieve a generated letter.

**Response:** Full letter data + PDF download URL

**Auth:** Public (no auth required for PDF download)  
**Implementation:** 1h

---

### 3. POST /api/nonprofit/{ein}/donation-letter/{letter_id}/send
Send letter to donor via email.

**Request:**
```json
{
  "recipient_email": "john@example.com",
  "message": "Thank you for your generous donation!"
}
```

**Response:** `{status: "sent", sent_at: "2026-07-04T..."}`

**Integration:** Twilio SendGrid  
**Auth:** Firebase (nonprofit user only)  
**Implementation:** 2h

---

### 4. GET /api/nonprofit/{ein}/donation-letters
List all letters for a nonprofit.

**Query params:** `?status=sent&limit=50`  
**Response:** Paginated list with filters

**Auth:** Firebase (nonprofit user only)  
**Implementation:** 1h

---

## Frontend Components (Ready to Implement)

### 1. DonationLetterForm.tsx
Form for nonprofit to generate letters.

**Fields:**
- Donor name
- Donor email
- Donation date
- Donation amount
- Letter type dropdown

**Behavior:**
- Validates amount > 0
- Calls POST /api/nonprofit/{ein}/donation-letter/generate
- Shows success message with download link
- Offers "Send to donor" action

**Implementation:** 2h

---

### 2. DonationLetterHistory.tsx
Dashboard widget showing recent letters.

**Display:**
- Table: Donor Name | Amount | Date | Status
- Filters: By status (draft/sent/failed)
- Pagination: 20 per page
- Actions: View | Send | Download | Delete

**Implementation:** 2h

---

### 3. DonationLetterPreview.tsx
Modal showing letter HTML preview before sending.

**Shows:**
- Full letter text
- Org info populated correctly
- Donation details
- Tax year from 990 data
- Donor info

**Implementation:** 1h

---

## Implementation Plan (When Legal Approves)

### Phase 4a: Core Infrastructure (4h)
- [ ] Create database tables
- [ ] Build letter template system (HTML generation)
- [ ] Implement IRS filing year lookup (from 990 data)
- [ ] Create helper functions for letter generation

### Phase 4b: API Endpoints (6h)
- [ ] POST /api/nonprofit/{ein}/donation-letter/generate
- [ ] GET /api/donation-letter/{letter_id}
- [ ] POST /api/nonprofit/{ein}/donation-letter/{letter_id}/send
- [ ] GET /api/nonprofit/{ein}/donation-letters
- [ ] PDF generation via wkhtmltopdf or Puppeteer

### Phase 4c: Frontend (4h)
- [ ] DonationLetterForm component
- [ ] DonationLetterHistory component
- [ ] DonationLetterPreview modal
- [ ] Wire into nonprofit dashboard

### Phase 4d: Testing & Compliance (1h)
- [ ] E2E test: generate → preview → send
- [ ] Verify §170(f)(8) compliance in output
- [ ] Test with real nonprofit account
- [ ] Verify emails deliver

---

## Letter Template (Requires Attorney Review)

```html
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6;">
  <p>{{ DATE }}</p>
  
  <p>Dear {{ DONOR_NAME }},</p>
  
  <p>We are delighted to acknowledge receipt of your generous contribution of 
  ${{ AMOUNT }} to {{ ORG_NAME }} (EIN: {{ EIN }}) on {{ DONATION_DATE }}.</p>
  
  <p>Your donation is essential to our mission of {{ MISSION_STATEMENT }}. 
  It enables us to continue our vital work in communities we serve.</p>
  
  <p><strong>Tax Acknowledgment:</strong> This letter is an acknowledgment of 
  your contribution for tax purposes. In accordance with IRS regulations 
  (§170(f)(8)), we confirm that we provided no goods or services in return 
  for your contribution. This letter is based on information you provided 
  and is valid only for the tax year {{ TAX_YEAR }}.</p>
  
  <p><strong>Financial Information (FY {{ TAX_YEAR }}):</strong><br/>
  Form 990 Filing Date: {{ FILING_DATE }}<br/>
  Organization Type: {{ ORG_TYPE }}<br/>
  Tax-Exempt Status: Verified by IRS</p>
  
  <p>For questions or to receive acknowledgment of your contribution, 
  please contact us directly. More information about our organization is 
  available at {{ WEBSITE }}.</p>
  
  <p>Thank you again for your support.</p>
  
  <p>Sincerely,<br/>
  {{ ORG_NAME }}<br/>
  EIN: {{ EIN }}</p>
</body>
</html>
```

**Note:** Template must be approved by attorney before use.

---

## Stewardship Alignment

**Principle 1: Mission before growth**
- ✅ Letters serve nonprofit mission (donor records), not Daanaa growth

**Principle 2: Privacy**
- ✅ Donor info never stored by Daanaa (routed directly to nonprofit)
- ✅ Letters sent via nonprofit's email, not Daanaa's

**Principle 3: Trust signals evidence-based**
- ✅ Tax year sourced from real 990 data
- ✅ EIN, status verified from registry

**Principle 7: Independence**
- ✅ Letters issued by nonprofit, not Daanaa
- ✅ Daanaa is conduit only, nonprofit retains liability

**Principle 8: No fund control**
- ✅ Daanaa never handles funds (still true)
- ✅ Letters reference donations made elsewhere

**Principle 10: AI is a tool**
- ✅ Human review: nonprofit writes/approves letters
- ✅ Audit trail: letter generated at, signed by nonprofit

---

## Risk Mitigation

### Legal Risk
- [ ] Require attorney sign-off on template
- [ ] Add nonprofit indemnification clause
- [ ] Track letter version for audit purposes

### Compliance Risk
- [ ] Validate IRS filing year from 990 data
- [ ] Test with 990-exempt and 990-N orgs
- [ ] Reject donations if tax year unknown

### Privacy Risk
- [ ] Donor email never persisted in Daanaa
- [ ] Sent via nonprofit SMTP, not Daanaa
- [ ] Deletion rights: nonprofit controls their letters

---

## Definition of Done

- [ ] Legal review complete & approved
- [ ] Database tables created & indexed
- [ ] All 4 API endpoints implemented & tested
- [ ] 3 frontend components built & integrated
- [ ] Letter template verified compliant
- [ ] E2E test: generate → send → verify
- [ ] Documentation updated
- [ ] Code committed & deployed

---

## Timeline (When Approved)

- **Day 1 (4h):** Database + infrastructure
- **Day 2 (6h):** API endpoints
- **Day 3 (4h):** Frontend + testing
- **Ship:** Friday evening

---

**Status: READY FOR IMPLEMENTATION (Awaiting Legal Gate)**
