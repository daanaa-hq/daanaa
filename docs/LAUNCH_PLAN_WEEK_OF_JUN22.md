# Launch Plan: Peer Context System — Week of June 22, 2026

## Timeline at a Glance

```
Mon 6/22   Board approval + deploy display layer
Tue 6/23   Test with 5 partner nonprofits + collect feedback
Wed 6/24   Iterate on copy/display based on feedback
Thu 6/25   Deploy database + correction form backend
Fri 6/26   Final testing + monitoring setup
Sat-Sun    Soft launch to early adopters
Mon 6/29+  Nonprofit beta testing + daily monitoring
```

---

## MON 6/22 — Board Approval + Display Deployment

### Morning: Board Presentation
**Deliverable:** Board memo (docs/BOARD_MEMO_COMPLETE_SYSTEM.md)

**Talking points (5 min):**
- V5 validation shows system is fair to all nonprofit sizes
- Reframed display (context vs. ranking) reduces nonprofit shame
- Transparency + correction path builds trust
- All stewardship principles aligned
- Ready to ship immediately

**Ask:** Approval to launch Option A this week

### Afternoon: Deploy Display Layer (Already Done!)
**What:** Frontend components + styling
**Status:** ✅ Already built and committed
**Action:**
- [ ] Rebuild frontend: `npm run build`
- [ ] Rsync to droplet: `dist/` folder
- [ ] Verify on live (daanaa.org/organizations/EIN)

**Verification (5 min):**
```bash
# Check display renders
curl https://daanaa.org/organizations/261234567 | grep -o "How Donors See You"
```

**Testing on localhost (before droplet):**
```bash
npm run dev
# Navigate to any org detail page
# Should see new "How Donors See You" section below financial context
```

---

## TUE 6/23 — Partner Nonprofit Testing

### Morning: Outreach to 5 Test Nonprofits
**Target:** Mix of profiles (small healthy, mid-stable, large struggling)

**Email template:**
```
Subject: Help us test a new feature (1 minute of your time)

Hi [ED Name],

We're testing a new way we show how your nonprofit compares financially 
to similar organizations. We'd love your gut reaction.

Can you spend 1 minute looking at your org on Daanaa and telling us: 
Does this feel fair? Accurate? Motivating?

Link: https://daanaa.org/organizations/[EIN]

Scroll down to "How Donors See You"

Just reply with a sentence or two. What's your gut reaction?

Thanks,
Akbar
```

**Partners to contact:**
- [ ] 1 small/lean org (that struggles)
- [ ] 1 small/healthy org (that thrives)
- [ ] 1 mid-sized stable org
- [ ] 1 large healthy org
- [ ] 1 large struggling org

### Afternoon: Collect Feedback
**What to ask (in follow-up call if needed):**
1. "Did this feel like you were being ranked or understood?"
2. "What's your reaction to seeing your peer group size?"
3. "Would you want to claim your profile and tell your story?"
4. "Any language that felt off or judgmental?"

**Feedback tracking:**
```
Org Name | Profile | Copy Reaction | Dignity Felt | Action Intent | Notes
---------|---------|---|---|---|---
ABC Org | Small, CAUTION | "Fair" | "Yes, understood" | "Would claim" | ...
```

---

## WED 6/24 — Copy Iteration

### Morning: Analyze Feedback
**Process:**
1. Aggregate reactions from 5 orgs
2. Note any language that felt off
3. Identify if reframe is working

### Afternoon: Adjust Copy (If Needed)
**Likely changes (based on anticipated feedback):**
- If "Building reserves" still feels like shame → try "Focusing on financial resilience"
- If "Lean" feels negative → try "Focused on mission impact"
- If peer group size overwhelms → add reassurance: "You're in good company"

**Deploy updated copy:**
- [ ] Edit PeerContextBreakdown.tsx
- [ ] Rebuild frontend
- [ ] Rsync to droplet
- [ ] Test on live

**Zero-downtime:** Changes go live within 5 minutes of rebuild

---

## THU 6/25 — Database + Backend Deployment

### Morning: Database Schema
**Action:**
```bash
cd ~/meritgiving
sqlite3 data/merit_registry.db < migrations/002_nonprofit_data_updates.sql
```

**Verify:**
```sql
SELECT name FROM sqlite_master WHERE type='table' AND name='org_nonprofit_updates';
-- Should return: org_nonprofit_updates
```

### Afternoon: Backend API Endpoint
**Endpoint:** `POST /api/nonprofit/update-data`

**Acceptance:** 
- Accept JSON: `{ claim_token, ein, updates: { revenue, expenses, program_pct, reserves }, explanation }`
- Validate data (revenue > 0, etc.)
- Check sanity (revenue > expenses, % 0-100)
- Store in org_nonprofit_updates with status = "pending_review"
- Return: `{ status: "received", update_id: 123 }`

**Add to daanaa_api.py:**

```python
@app.route('/api/nonprofit/update-data', methods=['POST'])
@limiter.limit("5 per minute")
def nonprofit_update_data():
    """Accept nonprofit-submitted financial data updates"""
    try:
        data = request.get_json()
        claim_token = data.get('claim_token')
        ein = data.get('ein')
        updates = data.get('updates', {})
        explanation = data.get('explanation', '')

        if not claim_token or not ein:
            return jsonify({"error": "Missing claim_token or ein"}), 400

        # Validate update values
        if updates.get('total_revenue') is not None and updates['total_revenue'] < 0:
            return jsonify({"error": "Revenue cannot be negative"}), 400
        if updates.get('program_expense_pct') is not None:
            pct = updates['program_expense_pct']
            if pct < 0 or pct > 100:
                return jsonify({"error": "Program % must be 0-100"}), 400

        # Store in database
        db = get_db()
        update_id = db.execute("""
            INSERT INTO org_nonprofit_updates 
            (ein, claim_token, submitted_total_revenue, submitted_total_expenses, 
             submitted_program_expense_pct, submitted_months_of_reserve, submitted_explanation, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending_review')
        """, (
            ein, claim_token,
            updates.get('total_revenue'),
            updates.get('total_expenses'),
            updates.get('program_expense_pct'),
            updates.get('months_of_reserve'),
            explanation
        )).lastrowid

        db.commit()

        return jsonify({
            "status": "received",
            "update_id": update_id,
            "message": "Your update will be included in tomorrow's scoring run"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

### Evening: Test Endpoint
```bash
curl -X POST http://localhost:5000/api/nonprofit/update-data \
  -H "Content-Type: application/json" \
  -d '{
    "claim_token": "test-token-123",
    "ein": "261234567",
    "updates": {
      "total_revenue": 3100000,
      "months_of_reserve": 3.2
    },
    "explanation": "2024 was stronger year"
  }'

# Should return: { "status": "received", "update_id": 1, ... }
```

---

## FRI 6/26 — Final Testing + Monitoring Setup

### Morning: End-to-End Testing
**Scenario:** Nonprofit claims → sees data → updates → next day sees peer context change

**Manual test:**
1. Nonprofit dashboard shows research data
2. Nonprofit clicks "Update Your Information"
3. Form appears with current values
4. Nonprofit submits update
5. Backend confirms receipt
6. Admin sees update in org_nonprofit_updates table

### Afternoon: Monitoring Setup

**Slack alerts for:**
- [ ] Updates with flagged data (>50% change)
- [ ] Sanity check failures
- [ ] API errors

**Admin dashboard query (check daily):**
```sql
SELECT ein, submitted_total_revenue, submitted_explanation, status
FROM org_nonprofit_updates
WHERE status = 'pending_review'
ORDER BY submitted_at DESC;
```

### Evening: Pre-Launch Checklist
- [ ] Display layer live on daanaa.org ✅
- [ ] Copy tested with 5 nonprofits ✅
- [ ] Database schema deployed ✅
- [ ] API endpoint working ✅
- [ ] Monitoring alerts configured ✅
- [ ] Staff knows how to review submissions ✅

---

## SAT-SUN 6/27-28 — Soft Launch to Early Adopters

### Outreach: "Be a Testing Partner"
**Email to claimed nonprofits (those with Google accounts + profile dashboard access):**

```
Subject: New feature: Help us understand your financial data

Hi [Org Name],

We just launched something new to build trust with donors: 
showing you exactly what data we use to understand your organization, 
and letting you correct it if it's outdated.

We're looking for 20 testing partners to try this and tell us what you think.

Visit your dashboard: [link to nonprofit dashboard]
Scroll down to "Research Data Behind Your Profile"

It takes 2 minutes. Your feedback helps us get it right.

Reply here or click [feedback link]

Thanks,
Akbar
```

**Target:** 20 early adopters (mix of sizes + health signals)

**Collect feedback:**
- Does the data display make sense?
- Is the update form easy to use?
- Did you find any errors?

---

## MON 6/29+ — Beta Testing + Daily Monitoring

### Daily (Every Morning)
**Check:**
```sql
-- See all updates from yesterday
SELECT ein, submitted_total_revenue, status FROM org_nonprofit_updates 
WHERE submitted_at >= datetime('now', '-1 day');

-- Look for flagged submissions
SELECT ein, submitted_explanation FROM org_nonprofit_updates 
WHERE sanity_check_failed = 1 AND status = 'pending_review';
```

**Action:**
- Review flagged submissions (do they make sense?)
- Email if we need clarification: "We see you submitted X. Just confirming that's correct?"
- Mark as "Validated" if ok, "Flagged" if needs review

### Weekly (Fridays)
**Retrospective:**
- How many nonprofits updated data?
- Did peer context improve for any?
- Any patterns in submissions?
- Any errors we caught?

**Iteration:** Adjust validation rules if needed

### Next Nightly Scoring (Monday 6/30)
**Updated overnight_pipeline.py to include:**
```python
# Check for validated nonprofit updates
validated_updates = db.execute("""
    SELECT ein, submitted_total_revenue, submitted_total_expenses, 
           submitted_program_expense_pct, submitted_months_of_reserve
    FROM org_nonprofit_updates
    WHERE status = 'validated' AND included_in_run_at IS NULL
""").fetchall()

# For each update, use nonprofit values instead of IRS when scoring
for update in validated_updates:
    # Pass to scorer with flag: use_nonprofit_data = True
    ...

# After scoring completes, mark updates as included:
db.execute("UPDATE org_nonprofit_updates SET included_in_run_at = ?, status = 'included_in_run' WHERE status = 'validated'")
```

**Email to nonprofits (after scoring):**
```
Subject: Your updated peer context is live!

Hi [Org Name],

Your updated financial data from June 25 is now live on Daanaa.

Before: Financially Stable
Now: Financially Healthy ✓

Your reserves improved, and donors will see that.

Visit your dashboard: [link]

Thanks for keeping your data current!
```

---

## Success Criteria (By End of Week 1)

✅ Display live and no complaints about shame/ranking language  
✅ 5+ test nonprofits confirm system feels fair + dignifying  
✅ Database + API working end-to-end  
✅ 20+ early adopters in beta testing  
✅ Zero critical bugs  
✅ At least 1 nonprofit submits data update (proof of engagement)  

---

## Risks & Mitigation

| Risk | Mitigation |
|------|-----------|
| **Copy still feels like ranking** | Run 5 nonprofits through test. Adjust before full rollout. |
| **API bugs** | Test endpoint thoroughly before marking as done. |
| **Nonprofit submits junk data** | Sanity checks + manual review before including in scoring. |
| **Scoring pipeline breaks** | Test with single nonprofit update first, then expand. |

---

## Deliverables by End of Week

- [ ] Display layer live & tested ✅
- [ ] Nonprofit feedback collected & analyzed
- [ ] Copy adjusted if needed
- [ ] Database schema deployed
- [ ] API endpoint live & tested
- [ ] Monitoring configured
- [ ] 20 early adopters in soft launch
- [ ] Staff trained on review process
- [ ] First scoring run includes nonprofit updates

---

## People/Roles

| Role | Responsibility |
|------|---|
| **You (Founder)** | Board approval, strategy, partner outreach |
| **Claude (AI)** | Code implementation, testing, monitoring setup |
| **[If staff available]** | Manual review of flagged submissions, nonprofit follow-up |

---

**Ready? I'll start with deployment right after you approve.**
