# Phase 3 Implementation Checklist

Use this for tracking progress across the full Phase 3 build.

---

## PHASE 3 ARCHITECTURE (COMPLETE ✓)

### Database Schema
- [x] Design 5 tables (letter_credit_purchases, donor_messages, etc)
- [x] Add indexes for performance
- [x] Create migration file (`migrations/phase3_schema.sql`)
- [x] Write migration runner in daanaa_api.py
- [x] Test migrations on local database

### Backend Endpoints
**Letter Credits (3 endpoints)**
- [x] POST /api/nonprofit/letter-credits/purchase
  - [x] Accept: stripe_payment_method_id, idempotency_key, quantity
  - [x] Validate: payment method format, quantity range
  - [x] Return: 202 Accepted with purchase_id
  - [x] Store: pending record in letter_credit_purchases
- [x] GET /api/nonprofit/letter-credits/balance
  - [x] Query: sum of letters_remaining from all purchases
  - [x] Aggregate: lifetime_purchases, lifetime_spend_cents
  - [x] Return: 200 OK with balance object
- [x] POST /api/webhook/stripe
  - [x] Verify: Stripe signature (HMAC-SHA256)
  - [x] Whitelist: payment_intent.succeeded only
  - [x] Update: purchase status to 'succeeded'
  - [x] Insert: letter_credits row with 100 letters
  - [x] Email: confirmation to nonprofit ED

**Donor Messages (4 endpoints)**
- [x] POST /api/nonprofit/donor-messages/send
  - [x] Accept: donor_email, donor_name, subject, body, track_opens
  - [x] Validate: email format, required fields
  - [x] Generate: tracking_pixel_id + encrypted token
  - [x] Inject: pixel as <img src=...> in message body
  - [x] Return: 201 Created with message_id, pixel_url
- [x] GET /api/nonprofit/donor-messages
  - [x] Accept: status filter, limit, offset
  - [x] Return: 200 OK with list of messages
  - [x] Include: open_count, link_clicks per message
- [x] GET /api/nonprofit/donor-messages/:id/events
  - [x] Query: all events for message_id
  - [x] Return: 200 OK with timeline (opens, clicks)
  - [x] Include: timestamp, IP, user_agent per event
- [x] GET /api/nonprofit/pixel/:id
  - [x] Return: 1x1 transparent GIF
  - [x] Log: open event async (non-blocking)
  - [x] Increment: donor_messages.open_count
  - [x] Set: first_opened_at (on first open only)

**Impact Dashboard (1 endpoint)**
- [x] GET /api/nonprofit/dashboard/impact
  - [x] Accept: period query param (last_7_days|last_30_days|all)
  - [x] Calculate: credit_utilization metrics
  - [x] Calculate: donor_engagement metrics
  - [x] Calculate: volunteer_impact metrics
  - [x] Calculate: revenue_equivalent metrics
  - [x] Calculate: forecast metrics
  - [x] Return: 200 OK with all 5 metric groups

### Type Safety
- [x] LetterCreditBalanceSchema (Zod)
- [x] LetterCreditPurchaseSchema
- [x] DonorMessageSchema
- [x] DonorMessageSendSchema (with validation)
- [x] DonorMessageEventSchema
- [x] MessageEventsResponseSchema
- [x] CreditUtilizationSchema
- [x] DonorEngagementSchema
- [x] VolunteerImpactMetricSchema
- [x] RevenueEquivalentSchema
- [x] ForecastSchema
- [x] ImpactMetricsSchema

### Testing
- [x] Write 37 tests (failing-first TDD)
- [x] Letter credit tests (purchase, balance, webhook, idempotency)
- [x] Donor message tests (send, list, events)
- [x] Pixel tracking tests (log, increment, set timestamp)
- [x] Impact dashboard tests (metrics calculation)
- [x] Database schema tests (table + column verification)
- [x] Add mocking for Stripe, email service

### Documentation
- [x] Write Phase 3 Implementation Guide
- [x] Write Phase 3 Next Steps (frontend roadmap)
- [x] Write Delivery Summary
- [x] Create this checklist

---

## PHASE 3 FRONTEND (PENDING - 3-4 WEEKS)

### CreditPurchaseModal.tsx (Week 1)
**Component**
- [ ] Create component file
- [ ] Props: nonprofitEin, authToken, isOpen, onClose, onPurchaseComplete
- [ ] Import: Dialog, Button, Input (shadcn)
- [ ] Implement: quantity selector (1-10)
- [ ] Implement: real-time cost display ($10/pack)
- [ ] Implement: Stripe card element integration
- [ ] Implement: loading state during payment
- [ ] Implement: error handling + retry
- [ ] Implement: success confirmation card
- [ ] Implement: auto-refresh balance on success

**Validation**
- [ ] Use LetterCreditPurchaseSchema
- [ ] Validate quantity: 1 ≤ qty ≤ 10
- [ ] Validate email (optional, for receipt)
- [ ] Validate Stripe response

**Integration**
- [ ] POST /api/nonprofit/letter-credits/purchase
- [ ] Polling: GET /api/nonprofit/letter-credits/balance every 2s
- [ ] Timeout: 30 seconds, show error if not succeeded
- [ ] Success: show toast, close modal, refresh parent

**Testing**
- [ ] Quantity selector updates cost correctly
- [ ] Stripe card element renders
- [ ] Payment sends correct data to backend
- [ ] Polling works (success within 30s)
- [ ] Cancel works
- [ ] Error handling shows retry button

**Dashboard Integration**
- [ ] Add button: "Buy Letter Credits"
- [ ] Click → open modal
- [ ] On success → refresh balance card

---

### DonorMessagesCard.tsx (Week 2)
**Component**
- [ ] Create component file
- [ ] Props: nonprofitEin, authToken
- [ ] Layout: 2 tabs (Send New Message | Sent Messages)

**Tab 1: Send New Message**
- [ ] Input: donor_email (required, validated)
- [ ] Input: donor_name (optional)
- [ ] Input: message_subject (required)
- [ ] Textarea: message_body (required, min 10 chars)
- [ ] Dropdown: template selector (defaults + custom)
- [ ] Toggle: "Track opens" (default: ON)
- [ ] Button: Send Message
- [ ] On success: toast, clear form, switch to tab 2

**Tab 2: Sent Messages**
- [ ] Table layout:
  - Columns: Date Sent | Donor | Subject | Opens | Clicks | Status
  - Sort: by date descending
  - Pagination: 10/page
  - Status filter: All | Sent | Draft | Failed
- [ ] Click row: expand to show timeline (open DonorMessageTimeline modal)
- [ ] Hover: show "Copy Pixel URL" tooltip

**Validation**
- [ ] Use DonorMessageSendSchema
- [ ] Email must have @
- [ ] Subject: required, >1 char
- [ ] Body: required, >10 chars

**Integration**
- [ ] POST /api/nonprofit/donor-messages/send
- [ ] GET /api/nonprofit/donor-messages
- [ ] GET /api/nonprofit/donor-messages/:id/events (via modal)
- [ ] Copy pixel URL to clipboard

**Testing**
- [ ] Send form validation works
- [ ] Email required + validated
- [ ] Subject/body required
- [ ] Send sends correct data
- [ ] List shows messages
- [ ] Status filter works
- [ ] Pagination works
- [ ] Click row opens timeline modal

**Dashboard Integration**
- [ ] Add card: "Donor Messages"
- [ ] Show: "X messages sent this month, Y% open rate"
- [ ] Button: "Send Thank You"

---

### ExportButton.tsx (Week 3)
**Component**
- [ ] Create component file
- [ ] Props: nonprofitEin, authToken, dataType, defaultFormat
- [ ] Dropdown button with format options: CSV | PDF | Excel
- [ ] On click: POST /api/nonprofit/exports/{type}?format={fmt}
- [ ] Show progress modal: indeterminate bar + elapsed time
- [ ] Polling: GET /api/nonprofit/background-jobs/{job_id} every 1s
- [ ] On complete: show download link, auto-download
- [ ] On error: show error message, retry button
- [ ] Button: Cancel (DELETE /api/nonprofit/background-jobs/{job_id})

**Features**
- [ ] Format selector (CSV, PDF, Excel)
- [ ] Progress bar with elapsed time
- [ ] Download link on completion
- [ ] Auto-download file
- [ ] Error handling with retry
- [ ] File size display
- [ ] Responsive on mobile

**Integration**
- [ ] POST /api/nonprofit/exports/volunteer-hours
- [ ] GET /api/nonprofit/background-jobs/{job_id}
- [ ] DELETE /api/nonprofit/background-jobs/{job_id}
- [ ] GET /api/nonprofit/exports/{job_id}.csv (download)

**Testing**
- [ ] Dropdown shows all formats
- [ ] CSV export completes in <10s
- [ ] PDF export completes in <30s
- [ ] Excel export completes in <30s
- [ ] Download file has correct format
- [ ] Cancel stops export
- [ ] Retry after error works
- [ ] File size shown

**Dashboard Integration**
- [ ] Add button: "Export Data"
- [ ] Show in volunteer section
- [ ] Can export: CSV | PDF | Excel

---

### ImpactForecast.tsx (Week 4)
**Component**
- [ ] Create component file
- [ ] Props: nonprofitEin, authToken
- [ ] 4-card grid layout

**Card 1: Credit Utilization**
- [ ] Title: "Letter Credits"
- [ ] Metric: "X / Y letters used (Z%)"
- [ ] Trend: ↑ up | ↓ down | → flat (with color)
- [ ] Secondary: "$X spent this month"
- [ ] Sparkline: 7-day trend

**Card 2: Donor Engagement**
- [ ] Title: "Donor Messages"
- [ ] Metric: "X messages sent"
- [ ] Stats: "Y% opens, Z% clicks"
- [ ] Trend: ↑ up | ↓ down | → flat
- [ ] Sparkline: message volume trend

**Card 3: Volunteer Impact**
- [ ] Title: "Volunteer Hours"
- [ ] Metric: "X hours verified"
- [ ] Value: "$Y @ $28.50/hour"
- [ ] Stats: "Z volunteers, avg W hrs"
- [ ] Trend: ↑ up | ↓ down | → flat

**Card 4: Revenue Equivalent**
- [ ] Title: "Total Impact"
- [ ] Metric: "$X total value"
- [ ] Breakdown: "$Y letters + $Z volunteer"
- [ ] Trend: ↑ up | ↓ down | → flat

**Forecast Section**
- [ ] Title: "Next 30 Days Projection"
- [ ] Projection 1: "X letters expected"
- [ ] Projection 2: "Y hours expected"
- [ ] Confidence: "Z% confidence"
- [ ] Notes: "Based on last 60 days"

**Validation**
- [ ] Use ImpactMetricsSchema
- [ ] All numbers ≥ 0
- [ ] Percentages 0-1
- [ ] Trend: 'up' | 'down' | 'flat'

**Integration**
- [ ] GET /api/nonprofit/dashboard/impact

**Testing**
- [ ] All 4 cards render
- [ ] Sparklines show
- [ ] Trends display correctly
- [ ] Forecast section visible
- [ ] Confidence % displayed
- [ ] Responsive on mobile
- [ ] Empty state if no data yet

**Dashboard Integration**
- [ ] Add card: "Impact Forecast"
- [ ] Click card → show period selector (last 7 / 30 / all)
- [ ] Metrics update on period change

---

### DonorMessageTimeline.tsx (Week 4 Bonus)
**Component**
- [ ] Create component file
- [ ] Props: messageId, nonprofitEin, authToken, isOpen, onClose
- [ ] Modal wrapper

**Message Header**
- [ ] To: donor email | donor name
- [ ] Subject: message subject
- [ ] Sent: formatted date + time

**Event Timeline**
- [ ] Vertical timeline (left border)
- [ ] Each event shows:
  - [ ] Icon (envelope, eye, link, etc)
  - [ ] Time (relative: "10 min ago")
  - [ ] Event type + description
  - [ ] IP address (redacted)
  - [ ] Browser/device

**Summary Stats**
- [ ] Total opens
- [ ] Unique opens (by IP)
- [ ] Clicks
- [ ] Bounce status

**Integration**
- [ ] GET /api/nonprofit/donor-messages/{message_id}/events

**Testing**
- [ ] Timeline renders in order
- [ ] Event icons correct
- [ ] Timestamps formatted
- [ ] Summary counts accurate
- [ ] Expand event shows full details

**Dashboard Integration**
- [ ] Opened from: DonorMessagesCard row click
- [ ] Show as modal overlay
- [ ] Close button / click outside to close

---

### NonprofitDashboardPage.tsx (Integration)
**Modifications**
- [ ] Add CreditPurchaseModal import
- [ ] Add DonorMessagesCard import
- [ ] Add ImpactForecast import
- [ ] Add ExportButton import
- [ ] Update grid layout (5 → 8 cards)
- [ ] Pass props to each component
- [ ] Add data refetch on component success
- [ ] Update page layout for 8 cards

**Layout**
- [ ] Grid: 1 col (mobile) | 2 cols (tablet) | 4 cols (desktop)
- [ ] Spacing: consistent gap between cards
- [ ] Responsive: no horizontal scroll
- [ ] Loading: show spinners while fetching

**Testing**
- [ ] All 8 cards render
- [ ] Cards responsive on 3 breakpoints
- [ ] Data refetch works when component updates
- [ ] No layout shift on load
- [ ] Accessibility: keyboard nav works

---

## INTEGRATION & TESTING

### End-to-End Testing
- [ ] **Workflow 1**: Purchase → Balance Updates
  - [ ] Click buy → select qty → pay → wait → balance ↑
  
- [ ] **Workflow 2**: Send Message → Email → Pixel Open
  - [ ] Send message → verify email sent → open email → pixel tracked
  
- [ ] **Workflow 3**: Export Volunteer Hours
  - [ ] Click export → select format → wait → download file
  
- [ ] **Workflow 4**: Dashboard Metrics
  - [ ] Dashboard loads → all cards visible → metrics accurate

### Performance Testing
- [ ] Load test pixel endpoint (1000+ req/min)
- [ ] Load test dashboard endpoint (<500ms)
- [ ] Database query plan (no N+1)
- [ ] Memory usage under load

### Regression Testing
- [ ] Existing nonprofit endpoints still work
- [ ] Database migrations don't break old data
- [ ] UI doesn't break existing flows
- [ ] Auth still required for all endpoints

---

## DEPLOYMENT

### Pre-Deployment
- [ ] All tests passing (37 backend + new frontend tests)
- [ ] Code review complete
- [ ] Security audit done (Stripe, pixel, auth)
- [ ] Database backup created
- [ ] Rollback plan documented

### Dev Deployment
- [ ] Pull code to dev machine
- [ ] Run migrations: `python3 daanaa_api.py` (check logs)
- [ ] Verify tables created: `sqlite3 data/merit_registry.db ".tables"`
- [ ] Run test suite: `pytest tests/test_nonprofit_endpoints_phase3.py`
- [ ] Test endpoints with curl/Postman
- [ ] Test frontend components locally

### Staging Deployment
- [ ] Deploy to staging server
- [ ] Run migrations on staging DB
- [ ] E2E testing (all workflows)
- [ ] Performance testing
- [ ] Security testing
- [ ] Verify Stripe sandbox integration

### Production Deployment
- [ ] Backup production database
- [ ] Deploy code (migrations auto-run)
- [ ] Verify tables created
- [ ] Feature flag: disable Phase 3 for non-testers
- [ ] Monitor for 24 hours
- [ ] Gradually enable for 10% → 50% → 100%

### Post-Deployment Monitoring
- [ ] Payment success rate (target: >95%)
- [ ] Message delivery rate (target: >98%)
- [ ] Pixel tracking accuracy (target: 30-40% open rate)
- [ ] API latency (target: <500ms)
- [ ] Database size growth
- [ ] Error rates (target: <0.1%)
- [ ] User feedback

---

## SUCCESS METRICS

- [x] Architecture documented (this checklist)
- [x] 11 endpoints implemented
- [x] 5 tables with proper schema
- [x] 37 tests written
- [x] Zod schemas defined
- [ ] 5 frontend components built
- [ ] All tests passing (backend + frontend)
- [ ] E2E workflows working
- [ ] Performance targets met
- [ ] 0 production errors (first 24h)
- [ ] Payment success >95%
- [ ] Email delivery >98%
- [ ] Pixel tracking 20-40% open rate

---

## TIMELINE

| Phase | Owner | Start | End | Days |
|-------|-------|-------|-----|------|
| Architecture | Backend | Jun 21 | Jun 21 | ✓ DONE |
| CreditPurchaseModal | Frontend | Jun 28 | Jul 5 | 7 |
| DonorMessagesCard | Frontend | Jul 6 | Jul 12 | 7 |
| ExportButton | Frontend | Jul 13 | Jul 19 | 7 |
| ImpactForecast + Timeline | Frontend | Jul 20 | Jul 26 | 7 |
| Integration | Both | Jul 27 | Aug 2 | 7 |
| Testing & QA | QA | Aug 3 | Aug 9 | 7 |
| Deployment | Ops | Aug 10 | Aug 11 | 2 |

**Total: 4 weeks (architecture complete, frontend pending)**

---

## Notes
- Use this checklist to track progress
- Check off items as completed
- Update as new tasks discovered
- Keep communication flowing between teams
- Document any blockers or issues
- Reference original docs for specs
