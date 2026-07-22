# End-to-End User Experience Test Guide
## Volunteer Hours: Login → Event → Hours → Approval → Wallet

**Time Required:** ~15 minutes  
**Difficulty:** Beginner-friendly, visual test

---

## Part 0: Start the Servers

### Terminal 1: Start the API
```bash
cd /home/akbar/meritgiving
source ~/meritgiving/venv/bin/activate
python3 daanaa_api.py
```

You should see:
```
[Startup] ✓ SearchIntentClassifier imported successfully
[Startup] ✓ SearchSemanticReranker imported successfully
[embeddings] loaded 537,776 scored vectors
 * Running on http://127.0.0.1:5000
```

### Terminal 2: Start the Frontend Dev Server
```bash
cd /home/akbar/meritgiving/frontend
npm run dev
```

You should see:
```
VITE v5.x ready in xxx ms

➜  Local:   http://localhost:5173/
```

### Terminal 3: Keep available for manual API calls (optional)
Leave this terminal ready for curl commands if needed.

---

## Part 1: Donor/Volunteer Signup & Wallet Setup

### Step 1a: Open Volunteer Wallet (No Login Required)
1. Open browser → `http://localhost:5173`
2. You should see: Daanaa homepage with search
3. Look for "Giving Wallet" button in top nav
4. Click "Giving Wallet" → Should open private wallet (no login required yet)
5. You should see: "Your giving wallet is private and stays on your device"

**✅ What you should see:**
- Empty wallet with "Start tracking" prompt
- "Save organizations" section
- "Log volunteer hours" section

---

## Part 2: Nonprofit Login & Event Creation

### Step 2a: Nonprofit Portal Login
1. In the same browser, go to `http://localhost:5173/nonprofit/login`
2. You should see: "Nonprofit Portal" login page with options:
   - "Sign in with Google"
   - "Or enter a verification token"

### Step 2b: Test with Verification Token (Simpler for testing)
1. Choose "Use a verification token" option
2. Enter a test organization:
   - **EIN:** `10-1234567` (or any valid 9-digit number)
   - **Token:** (we'll create this next)

First, let's create a valid verification token via the API:

```bash
# Terminal 3:
curl -X POST http://localhost:5000/api/claim/initiate \
  -H "Content-Type: application/json" \
  -d '{
    "nonprofit_ein": "10-1234567",
    "nonprofit_name": "Test Nonprofit",
    "contact_email": "nonprofit@example.com"
  }'
```

This returns:
```json
{
  "verification_token": "abc123xyz...",
  "nonprofit_ein": "10-1234567"
}
```

Copy the `verification_token` value.

3. Return to browser, enter:
   - EIN: `10-1234567`
   - Token: `[paste the token from step above]`
4. Click "Continue"

**✅ What you should see:**
- Redirects to organization dashboard
- Shows: "My Organizations" or "Test Nonprofit" overview
- Menu items: Volunteer Hours, Events, Impact, Profile

### Step 2c: Navigate to Volunteer Events
1. Click "Volunteer Events" or "Create Event" in the menu
2. Click "+ Create New Event"
3. Fill in the form:
   - **Title:** "Community Cleanup Day"
   - **Date:** (pick today's date)
   - **City:** "Austin"
   - **State:** "Texas"
   - **Task Types:** Check "General volunteer" and "Setup"
4. Click "Create Event"

**✅ What you should see:**
- Event created successfully
- Shows event details
- Displays a QR code (for volunteers to scan)
- Copy the event's **shortId** from the URL or display

---

## Part 3: Volunteer Signs Up & Logs Hours

### Step 3a: Volunteer Accesses the Event
1. **Open a new browser tab** (to simulate a different person)
2. Go to `http://localhost:5173/volunteer/events/[shortId]` (use the shortId from step 2c)
   - OR: If there's a QR code, use your phone's camera to scan it
   - OR: Look for the event on the main discovery page

3. You should see: "Log Volunteer Hours" page with:
   - Event title
   - Date
   - Location
   - Form to fill in

### Step 3b: Fill in Volunteer Information
1. **Your name:** "Jane Volunteer"
2. **Your email:** "jane@example.com"
3. **Organization:** "Test Nonprofit" (should be auto-selected)
4. **Hours:** 4.5
5. **Role:** "General volunteer" (from dropdown)
6. **Notes (optional):** "Helped with trash collection and sorting"
7. Click **"Submit hours"**

**✅ What you should see:**
- Success screen: "Thanks, Jane!"
- Message: "Your hours were submitted. The organization will review and approve them."
- Shows the organization name and hours
- Status badge: "Pending review"
- Button: "Track in Wallet"

### Step 3c: Track Hours in Wallet
1. Click **"Track in Wallet"** button
2. You should see: "Added ✓" (button changes state)
3. Message: "Your Giving Wallet keeps a private record of every hour you volunteer. Tracked hours show as 'Submitted' until the organization reviews them."

**✅ What you should see:**
- Confirmation that hours were added to wallet
- No data sent to any server (stays on device)

---

## Part 4: Volunteer Checks Wallet Status

### Step 4a: Open Wallet (Same Browser, Same Device)
1. Click the "Giving Wallet" button in the header
2. You should see: Your wallet with the logged hours

**✅ What you should see:**
```
Community Cleanup Day
4.5 hours · 2026-07-22
[Pending review] ← Status badge
```

**Status Badge:** Should say "Pending review" (gray/amber color)

### Step 4b: Keep Wallet Open
Leave this wallet tab open — we'll see it update when the nonprofit approves.

---

## Part 5: Nonprofit Reviews & Approves Hours

### Step 5a: Return to Nonprofit Portal (Tab 1)
1. Go back to the first browser tab (nonprofit portal)
2. You should still be logged in
3. Navigate to: "Volunteer Hours" or "Approvals" section
4. You should see a list of pending submissions:
   - Volunteer name: "Jane Volunteer"
   - Email: "jane@example.com"
   - Hours: 4.5
   - Status: "Pending"

### Step 5b: Review the Submission
1. Click on the submission or "View Details"
2. You should see:
   - All submitted information
   - Service date: (the event date)
   - Task type: "General volunteer"
   - Notes: "Helped with trash collection and sorting"

### Step 5c: Approve the Hours
1. Click **"Approve"** button
2. Enter your email: "nonprofit@example.com" (optional prompt)
3. Click **"Confirm Approval"**

**✅ What you should see:**
- Success message: "Hours approved"
- Status changes to "Approved" ✓
- Record shows approval timestamp

---

## Part 6: Wallet Auto-Updates

### Step 6a: Check Wallet in Tab 2
1. Switch to the browser tab with the wallet open (from Step 4)
2. **The page should automatically refresh OR you can manually refresh (F5)**

**✅ Critical: Status Badge Should Update**
```
Community Cleanup Day
4.5 hours · 2026-07-22
[Approved ✓] ← Status changed from "Pending review" to "Approved ✓"
```

The status badge color should change from amber/gray to green.

**This verifies:**
- ✅ Wallet linked to nonprofit approval
- ✅ Status refreshed automatically
- ✅ Data stayed private (never left device until submitted)
- ✅ Nonprofit approval reflected in wallet

---

## Part 7: Verify Public Aggregate (Optional)

### Step 7a: Check Public Nonprofit Profile
1. Go to `http://localhost:5173` (back to homepage)
2. Search for the nonprofit: "Test Nonprofit"
3. Click on its profile
4. Scroll to "Volunteer Impact" section

**✅ What you should see:**
- Volunteer impact data IF nonprofit has opted into public visibility
- Shows: "4.5 hours by approved volunteers"
- **Never shows individual volunteer names** (privacy preserved)

### Step 7b: Verify Data Integrity via API
```bash
# Terminal 3:
# Check that exactly ONE impact record was created
curl http://localhost:5000/api/public/nonprofit/10-1234567/volunteer-impact?year=2026

# Should return:
# {
#   "total_hours_approved": 4.5,
#   "volunteer_count": 1,
#   "labor_value_estimate": 150.71,
#   ...
# }
```

---

## Part 8: Verify Privacy & Security

### Step 8a: Confirm No IP Address Stored
```bash
# Terminal 3:
sqlite3 data/merit_registry.db "SELECT * FROM volunteer_hours WHERE volunteer_email='jane@example.com';"
```

**✅ You should see:**
- volunteer_name, volunteer_email, hours, service_date, status
- **NO** `submitted_ip` or `ip_address` column
- All data is there BUT no IP

### Step 8b: Confirm Volunteer Name Not in Public API
```bash
# Terminal 3:
curl http://localhost:5000/api/public/nonprofit/10-1234567/volunteer-impact

# Response should contain ONLY:
# - total_hours_approved (aggregate)
# - volunteer_count (aggregate, no names)
# - labor_value_estimate
# **NEVER** volunteer_name or volunteer_email
```

---

## Test Checklist: What Should Work

| Step | What Should Happen | ✅/❌ |
|------|-------------------|--------|
| 1a | Wallet opens without login | |
| 2b | Nonprofit can login with token | |
| 2c | Nonprofit creates event with QR | |
| 3a | Volunteer can access event link | |
| 3b | Volunteer submits hours successfully | |
| 3c | "Track in Wallet" button works | |
| 4a | Wallet shows pending hours | |
| 4b | Wallet shows "Pending review" status | |
| 5a | Nonprofit sees pending submissions | |
| 5c | Nonprofit can approve hours | |
| 6a | **Wallet auto-updates status to "Approved ✓"** | ← KEY TEST |
| 7a | Public profile shows aggregate (if opted in) | |
| 7b | No duplicate records created | |
| 8a | No IP address persisted | |
| 8b | Public API never returns volunteer names | |

---

## Common Issues & Troubleshooting

### Issue: "Event not found"
- Check that you copied the shortId correctly
- Verify the event was created in the nonprofit portal
- Check URL format: `/volunteer/events/[shortId]`

### Issue: "Organization will review and approve them" but nonprofit doesn't see submission
- Ensure nonprofit is logged in
- Make sure you used the correct EIN (10-1234567)
- Check that the submission was for the right organization

### Issue: Wallet status doesn't update to "Approved"
- **This is critical** — means the refresh endpoint isn't working
- Check browser console (F12) for errors
- Manually refresh the wallet page (F5)
- If still doesn't update, check API logs in Terminal 1

### Issue: "Invalid token" during nonprofit login
- Make sure you created a fresh token via `/api/claim/initiate`
- Token may have expired (try creating a new one)
- Verify EIN is exactly 9 digits with leading zeros removed

---

## Success Criteria

The system is working correctly when:

1. ✅ Volunteer submits hours via QR/link (no account needed)
2. ✅ Hours appear in wallet as "Pending review"
3. ✅ Nonprofit sees submission in approval dashboard
4. ✅ Nonprofit clicks "Approve"
5. ✅ **Wallet automatically updates to show "Approved ✓"**
6. ✅ No duplicate records in database
7. ✅ No volunteer names in public API
8. ✅ No IP addresses persisted

---

## Next Steps After Test

**If all checkboxes pass:**
- System is ready for deployment
- Run automated tests: `pytest tests/test_volunteer_hours_flow.py -v`
- Then proceed with backend deploy

**If anything fails:**
- Check API logs in Terminal 1 for errors
- Check browser console (F12) for client-side errors
- Run individual tests: `pytest tests/test_volunteer_hours_flow.py::TestEndToEnd -v`

---

**Questions?** Check `VOLUNTEER_HOURS_AUDIT_SUMMARY.md` for technical details.
