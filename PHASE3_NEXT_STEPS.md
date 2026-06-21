# Phase 3 Next Steps — Frontend Implementation Guide

**Current Status**: Architecture + Backend Complete (11 endpoints, 5 tables, 37 tests)
**Next**: Build 5 React components + integrate with dashboard

---

## Week 1: CreditPurchaseModal Component

### Goal
Build Stripe checkout UI for purchasing letter credits.

### Files to Create/Modify
- **NEW**: `frontend/src/components/CreditPurchaseModal.tsx`
- **MODIFY**: `frontend/src/pages/nonprofit/NonprofitDashboardPage.tsx` (add modal trigger)

### Implementation Checklist

```typescript
// CreditPurchaseModal.tsx
interface Props {
  nonprofitEin: string
  authToken: string
  isOpen: boolean
  onClose: () => void
  onPurchaseComplete?: () => void
}

// Features
1. Modal wrapper (shadcn Dialog)
2. Quantity selector (1-10 packs, default 1)
3. Real-time cost calculation ($10/pack)
4. Stripe card element integration
5. Loading state during payment
6. Error handling + retry button
7. Success confirmation card
8. Automatic balance refresh on success

// Validation (Zod)
- Use LetterCreditPurchaseSchema for response
- Validate: 1 ≤ quantity ≤ 10
- Email validation for receipt

// Integration
POST /api/nonprofit/letter-credits/purchase
  Input: stripe_payment_method_id, idempotency_key, quantity
  Output: purchase_id, status (pending|succeeded)
  Polling: GET /api/nonprofit/letter-credits/balance every 2s until succeeded
  Timeout: 30 seconds
```

### Testing
```bash
# Manual test
1. Open dashboard
2. Click "Buy Letter Credits" button
3. Modal opens
4. Select quantity (2 packs)
5. Total shows $20.00
6. Enter test card (4242 4242 4242 4242)
7. Click purchase
8. Loading spinner appears
9. Success message appears
10. Balance updates to +200 letters
11. Close modal
12. Verify dashboard shows new balance
```

---

## Week 2: DonorMessagesCard Component

### Goal
Build message composition + list UI for donor thank-yous with engagement metrics.

### Files to Create/Modify
- **NEW**: `frontend/src/components/DonorMessagesCard.tsx`
- **MODIFY**: `frontend/src/pages/nonprofit/NonprofitDashboardPage.tsx`

### Implementation Checklist

```typescript
// DonorMessagesCard.tsx
interface Props {
  nonprofitEin: string
  authToken: string
}

// Layout: 2 tabs
Tab 1: Send New Message
  - Donor email input (text, required, validated)
  - Donor name input (text)
  - Message subject input (text, required)
  - Message body textarea (required, min 10 chars)
  - Template selector dropdown (defaults + custom)
  - Track opens toggle (default: on)
  - Send button
  - Success toast + clear form

Tab 2: Sent Messages
  - Table with columns:
    | Date Sent | Donor | Subject | Opens | Clicks | Status |
  - Sort by date descending
  - Pagination (10/page)
  - Status filter: All | Sent | Draft | Failed
  - Click row → expand to show timeline
  - Hover → copy pixel URL (for testing)

// Validation (Zod)
- Use DonorMessageSendSchema
- Email must have @
- Subject required, >1 char
- Body required, >10 chars
- Default: track_opens = true

// Endpoints
POST /api/nonprofit/donor-messages/send
  Input: donor_email, donor_name, message_subject, message_body, track_opens
  Output: message_id, tracking_pixel_url, status (queued)

GET /api/nonprofit/donor-messages
  Query: status=all, limit=10, offset=0
  Output: [{ id, donor_email, subject, status, sent_at, open_count, link_clicks }]
```

### Testing
```bash
# Test send workflow
1. Click DonorMessagesCard
2. Enter donor email: donor@example.com
3. Enter name: Jane Smith
4. Subject: Thank you for your generosity
5. Body: Your $500 gift makes a difference...
6. Track opens: ON
7. Click "Send Message"
8. Toast: "Message queued for delivery"
9. Form clears
10. Pixel URL copied to clipboard

# Test list workflow
1. Click "Sent Messages" tab
2. Wait for list to load (should show Jane Smith message)
3. Click status filter: "Sent"
4. Messages update
5. Click row to expand
6. Shows: "Queued for delivery" status
7. (After 2+ hours) Status changes to "Sent"
8. open_count increments when recipient opens email
```

---

## Week 3: ExportButton Component

### Goal
Multi-format export (CSV/PDF/Excel) with progress tracking.

### Files to Create/Modify
- **NEW**: `frontend/src/components/ExportButton.tsx`
- **MODIFY**: `frontend/src/pages/nonprofit/NonprofitDashboardPage.tsx`

### Implementation Checklist

```typescript
// ExportButton.tsx
interface Props {
  nonprofitEin: string
  authToken: string
  dataType: 'volunteer_hours' | 'letters' | 'donors'
  defaultFormat?: 'csv' | 'pdf' | 'excel'
}

// Features
1. Dropdown button with format options
2. On click:
   - POST /api/nonprofit/exports/[type]?format=csv|pdf|excel
   - Get job_id, status=pending
   - Show progress modal (indeterminate progress bar)
   - Poll GET /api/nonprofit/background-jobs/{job_id} every 1s
   - Show elapsed time
   - Cancel button → DELETE /api/nonprofit/background-jobs/{job_id}
3. On completion:
   - Download link appears
   - Auto-download file
   - Show file size + download time
   - Success toast
4. On error:
   - Show error message
   - Retry button
   - Copy error to clipboard

// Polling logic
while (status !== 'complete' && status !== 'failed') {
  await sleep(1000)
  const job = await getJobStatus(jobId)
  setStatus(job.status)
  if (job.completed_at) clearInterval(pollTimer)
}
```

### Testing
```bash
# Test CSV export
1. Click ExportButton
2. Select "CSV"
3. Modal shows "Generating..."
4. Poll bar shows progress
5. After 5-10s: "Download" link appears
6. Click download
7. volunteer_hours_EIN_jobid.csv downloaded
8. Verify CSV format (name, email, hours, date, activity, status)

# Test long-running export (PDF)
1. Click ExportButton
2. Select "PDF"
3. Modal shows "Generating..." for 2+ minutes
4. Can cancel mid-export
5. Error shown if cancelled
6. Retry works

# Test error handling
1. Export starts
2. Kill server process
3. Error message: "Export failed"
4. Retry button available
5. Click Retry → restarts from checkpoint
```

---

## Week 4: ImpactForecast Component

### Goal
4-card metric display + trend visualization + forecast.

### Files to Create/Modify
- **NEW**: `frontend/src/components/ImpactForecast.tsx`
- **MODIFY**: `frontend/src/pages/nonprofit/NonprofitDashboardPage.tsx`

### Implementation Checklist

```typescript
// ImpactForecast.tsx (4-card grid layout)
interface Props {
  nonprofitEin: string
  authToken: string
}

// Card 1: Credit Utilization
  Title: "Letter Credits"
  Metric: "350 / 500 letters used (70%)"
  Trend: "↑ up" (green) or "↓ down" (orange) or "→ flat" (gray)
  Secondary: "$50 spent this month"
  Sparkline: 7-day letter usage trend

// Card 2: Donor Engagement
  Title: "Donor Messages"
  Metric: "45 messages sent"
  Engagement: "32% open rate, 8% click rate"
  Trend: "↑ up"
  Sparkline: Message volume over 7 days

// Card 3: Volunteer Impact
  Title: "Volunteer Hours"
  Metric: "280 hours verified"
  Value: "$7,980 value @ $28.50/hour"
  Trend: "↑ up"
  Volunteers: "22 active volunteers, avg 12.7 hrs"

// Card 4: Revenue Equivalent
  Title: "Total Impact"
  Metric: "$11,480 value"
  Breakdown: "$3,500 letters + $7,980 volunteer"
  Trend: "↑ up"
  Text: "Equivalent to X months of operating budget"

// Forecast Section (below cards)
  Title: "Next 30 Days Projection"
  Projection 1: "650 letters expected (vs 500 actual last month)"
  Projection 2: "350 volunteer hours expected"
  Confidence: "75% confidence"
  Notes: "Based on last 60 days trend"

// Validation (Zod)
- Use ImpactMetricsSchema
- All numbers must be non-negative
- Percentages 0-1
- Trend must be 'up' | 'down' | 'flat'
```

### Testing
```bash
# Visual test
1. Load dashboard
2. See 5 metric cards
3. Hover over card → shows tooltip "Based on last 30 days"
4. Click trend icon → explanation appears
5. See sparkline charts on each card
6. Forecast section shows projected numbers
7. Confidence indicator (75%) displayed

# Data validation
1. Navigate to org with NO data yet
2. Cards show 0 / empty state
3. Forecast shows "Not enough data"
4. After 1 month of data: forecast activates
```

---

## Week 5: DonorMessageTimeline Component (Bonus)

### Goal
Detailed event timeline for individual messages.

### Files to Create/Modify
- **NEW**: `frontend/src/components/DonorMessageTimeline.tsx`
- **MODIFY**: `DonorMessagesCard.tsx` (add click handler to open timeline modal)

### Implementation Checklist

```typescript
// DonorMessageTimeline.tsx
interface Props {
  messageId: string
  nonprofitEin: string
  authToken: string
  isOpen: boolean
  onClose: () => void
}

// Timeline view
GET /api/nonprofit/donor-messages/{messageId}/events

// Display
1. Message header:
   | To: john@example.com | Jane Donor |
   | Subject: Thank you for your support |
   | Sent: Jun 21, 2026 10:05 AM |

2. Event list (chronological):
   Each event:
   | Time | Type (icon) | Description | IP | Browser |
   | 10:05 | 📤 sent | Delivered to john@example.com | - | - |
   | 10:30 | 👁️ opened | First open | 203.0.113.x | Chrome 91 |
   | 10:35 | 👁️ opened | Second open | 203.0.113.x | Chrome 91 |
   | 10:42 | 🔗 clicked | Clicked "View org page" | 203.0.113.x | Chrome 91 |

3. Summary stats:
   Total opens: 2
   Unique opens: 1 device
   Clicks: 1
   Bounce: No

// Styling
- Timeline vertical line (left side)
- Icons by event type
- Timestamps relative ("10 minutes ago")
- Expand event to see full details (IP full, user agent, referer)
```

---

## Dashboard Integration (All Weeks)

### Modify NonprofitDashboardPage.tsx

```typescript
// Current: 5 cards in grid
// Target: 8 cards (5 existing + 3 new)

// Layout
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
  {/* Existing cards */}
  <DonationLettersCard />
  <VolunteerInsightsCard />
  <DonorCommunicationCard />
  <OnboardingChecklist />
  
  {/* Phase 3 cards */}
  <CreditPurchaseModal triggerFromCard={true} />
  <DonorMessagesCard />
  <ImpactForecast />
  
  {/* Optional */}
  <ExportButton dataType="volunteer_hours" defaultFormat="csv" />
</div>
```

### Data Flow
```
Dashboard loads
  ├─ Fetch nonprofit info (EIN, name)
  ├─ Fetch volunteer summary
  ├─ Fetch letter credit balance
  ├─ Fetch impact metrics (GET /api/nonprofit/dashboard/impact)
  └─ Display all cards

On CreditPurchaseModal success
  └─ Refetch balance → update card

On DonorMessagesCard send
  └─ Refetch impact metrics → update forecast card

On ExportButton complete
  └─ Show toast notification (no card update needed)
```

---

## Testing Sequence

### Unit Tests (Jest + React Testing Library)
```bash
npm test -- CreditPurchaseModal.test.tsx
npm test -- DonorMessagesCard.test.tsx
npm test -- ImpactForecast.test.tsx
npm test -- ExportButton.test.tsx
npm test -- DonorMessageTimeline.test.tsx
```

### Integration Tests (E2E - Playwright/Cypress)
```bash
# Workflow: Purchase credits → send message → check engagement
1. Login as nonprofit ED
2. Dashboard loads
3. Click "Buy Credits" → purchase 2 packs
4. Wait for success
5. Balance updates (+200 letters)
6. Click "Send Message"
7. Fill form → send to test@example.com
8. Message shows in "Sent" list
9. Status shows "queued"
10. (In another browser) Open tracking pixel URL
11. Pixel loads (GIF returned)
12. In original browser: message open_count increments
13. Click "View Timeline"
14. Timeline shows [sent → opened]
```

### Performance Testing
```bash
# Load testing: pixel endpoint (open tracking)
# Should handle 1000+ requests/minute without dropping pixels
ab -n 10000 -c 100 https://daanaa.org/api/nonprofit/pixel/px_abc123?token=xyz

# Dashboard performance
# Impact metrics endpoint should respond <500ms even with 10+ years of data
# Monitor: N+1 queries, missing indexes
```

---

## Deployment Checklist

### Before Frontend Launch
- [ ] All backend endpoints tested (curl / Postman)
- [ ] Database migrations run successfully
- [ ] Stripe sandbox account configured
- [ ] Email delivery working (test send 1 message)
- [ ] Pixel tracking verified (GIF returns, events logged)

### Frontend Rollout
- [ ] All 5 components built and tested locally
- [ ] Zod schemas match backend responses
- [ ] Responsive design on mobile (320px+)
- [ ] Accessibility: keyboard nav, ARIA labels
- [ ] Error boundaries around components
- [ ] Feature flag hides Phase 3 from non-testers

### Post-Launch Monitoring
- [ ] Payment success rate >95%
- [ ] Message delivery success >98%
- [ ] Pixel tracking (open rate 20-40%)
- [ ] Dashboard load time <1s
- [ ] Zero unhandled errors in Sentry

---

## Success Metrics

**Week 1 (CreditPurchaseModal)**
- Payment endpoint: 100+ test purchases
- Success rate: >95%
- Time to credit: <5 minutes

**Week 2 (DonorMessagesCard)**
- Message send: 100+ test messages
- Delivery success: >98%
- Engagement tracking: >30% open rate

**Week 3 (ExportButton)**
- CSV export: <10 seconds for 1000 rows
- PDF export: <30 seconds
- Cancel functionality: works mid-export

**Week 4 (ImpactForecast)**
- Dashboard load: <1 second
- Metrics accuracy: 100% vs database
- Forecast precision: within 10% of actual (month after launch)

---

## Notes

- All components use existing Tailwind theme (soft-cream, deep-navy, etc)
- Use shadcn Dialog/Button/Input components (already installed)
- Leverage existing usePageMeta hook for SEO
- Follow existing error handling pattern (toast messages, Sentry logging)
- Load testing baseline: 100 concurrent users on dashboard
