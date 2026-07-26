# UX Test Plan: Peer Inference v6 Badge & Messaging

**Objective:** Verify donors + nonprofits understand that T2 (inferred) context is peer-based, not org's actual data. Badge clarity + messaging comprehension.

**Scope:** 8 participants (5 donors, 3 nonprofit staff)  
**Duration:** 30 min per session  
**Timeline:** 2026-07-29 to 2026-07-31 (3 days)  
**Success Criteria:** 8/8 pass comprehension tests (detailed below)

---

## Participant Recruitment

### Donor Segment (5 people)
- **Criteria:** Give $100–$10K/year to nonprofits, use nonprofit discovery tools
- **Recruiting from:** Email list, social media, casual referrals
- **Incentive:** $25 Amazon gift card for 30-min session
- **Diversity target:** Mix of ages, giving experience (some new, some veteran)

### Nonprofit Segment (3 people)
- **Criteria:** Program director or executive at small-to-medium org, no recent 990 filed
- **Recruiting from:** Daanaa network, LinkedIn outreach
- **Incentive:** $25 gift card or nonprofit donation matching
- **Org type target:** Mix (food bank, youth program, community center)

### Recruiting Script
```
Subject: Help shape the future of nonprofit discovery (30 min, $25 gift card)

Hi [Name],

We're testing a new way to show donors financial context for nonprofits 
without recent tax filings. Your feedback will shape how 2M+ nonprofits 
are discovered.

Session: 30 min video call, zero prep needed
Date: [flexible options]
Incentive: $25 Amazon gift card

Interested? Reply with your availability: [Calendly link]
```

---

## Test Flow (30 min)

### Segment A: Donors (5 sessions)

**Setup (2 min):**
- Introduce self, explain test is about nonprofit discovery UI
- No wrong answers; we're testing the UI, not the donor
- Share screen: live site showing T2 org (inferred peer context)

**Discovery Phase (5 min):**
- "Browse this nonprofit's profile. Tell me what you see on the page."
- Observe: Do they notice the InferenceBadge? Do they read it?
- Probe: "What does this blue info box mean to you?"

**Comprehension Test 1 (5 min):**
- Show InferenceBadge in isolation
- Question 1: "What does this badge tell you?" (open-ended)
  - **Pass:** Mentions "similar orgs" OR "not their actual data" OR "inferred"
  - **Fail:** Thinks it's actual org data or misunderstands
- Question 2: "Is this showing the org's actual financial data, or something else?"
  - **Pass:** "Something else" + explains (peer data, typical orgs, etc.)
  - **Fail:** "Yes, actual data" or confused

**Comprehension Test 2 (5 min):**
- Show T2 reserves copy: "Although we don't have revenue data for this organization, nonprofits in this group typically carry 2.1 months of operating reserves."
- Question 3: "What does 'this group' mean?"
  - **Pass:** Refers to peer group, similar orgs, region/type-based
  - **Fail:** Thinks it's just averages or doesn't know
- Question 4: "Would you trust this number to make a donation decision?"
  - **Pass:** "As a starting point, yes" OR "I'd verify with them" (realistic trust)
  - **Fail:** "No, it's fake" OR "Yes, 100% trust" (either extreme is wrong)

**Comparison Test (5 min):**
- Show T1 org side-by-side with T2 org
- Question 5: "How are these two different? What's the difference in how data is presented?"
  - **Pass:** Clearly identifies T1 as "actual org data" vs T2 as "peer-based"
  - **Fail:** Treats them the same or confuses them
- Question 6: "Which one would you trust more?"
  - **Pass:** "T1, but T2 is still helpful" (realistic nuance)
  - **Fail:** Doesn't understand the distinction

**Closing (3 min):**
- "Anything confusing about how this data is presented?"
- "What would make this clearer?"
- Thank you + gift card details

---

### Segment B: Nonprofits (3 sessions)

**Setup (2 min):**
- Explain: We show donors peer financial context for orgs without recent 990s
- Show their org's profile (T2 inferred tier)

**Perspective Test (5 min):**
- "How do you feel seeing your org shown with peer context instead of actual data?"
- Probe: Is this fair? Does it help donors understand you?
- Probe: "Would you want to claim your profile and share actual data?"

**Accuracy Test (5 min):**
- Show peer group definition: "Donation-funded youth programs in [State]"
- Question: "Does this peer group make sense for your org?"
  - **Pass:** "Yes, that's accurate" or "Close, but [minor adjustment]"
  - **Fail:** "No, totally wrong peer group"
- Question: "Do the peer median reserves (2.1 months) seem realistic for orgs like yours?"
  - **Pass:** "Yes, that matches what I see" or "About right"
  - **Fail:** "Way off, unrealistic"

**Messaging Test (5 min):**
- Show donor-facing copy: "Although we don't have revenue data..."
- Question: "How do you feel about this way of explaining it to donors?"
  - **Pass:** "Fair and honest" or "I appreciate the transparency"
  - **Fail:** "Feels like hiding our data" or unclear
- Question: "What would you want donors to know about your actual finances?"
  - **Pass:** "Here's what we actually are..." (uses session to clarify)
  - **Fail:** Defensive or dismissive

**Claim Flow (5 min):**
- "We let orgs claim profiles and share actual data. Interested?"
- Explain process: File 990 → Daanaa picks it up (4–6 weeks)
- Question: "What would make it easier for you to claim your profile?"
  - **Pass:** Specific obstacles or clear interest
  - **Fail:** Apathy or confusion about the process

**Closing (3 min):**
- Thank you + offer to send results
- Gift card details

---

## Success Metrics & Thresholds

| Metric | Target | Pass Criteria |
|--------|--------|---------------|
| **Donor Comprehension** | 8/8 pass | All 5 donors answer Q1–Q6 correctly |
| **Nonprofit Accuracy** | 3/3 pass | All 3 nonprofits confirm peer group makes sense |
| **Trust Calibration** | 8/8 realistic | All understand T2 ≠ T1, but realistic about trust level |
| **InferenceBadge Clarity** | 8/8 notice | All participants spontaneously notice + understand badge |
| **Messaging Tone** | 8/8 fair | No one finds copy deceptive or dismissive |

**If ANY metric falls below target:**
- Flag which specific test question failed
- Iterate: redesign badge/copy, re-test with 2–3 new participants
- Document changes in `DECISIONS.md`

---

## Data Collection

**Session Recording:**
- Record Zoom video + transcript (with participant consent)
- Save to: `logs/ux_testing/v6_inference/[date]_[participant_id].mp4`

**Response Sheet (per session):**
```
Participant ID: [donor_5] / [nonprofit_1]
Date: 2026-07-29
Duration: 28 min

Q1: What does badge mean? ___
  Pass: ☐ Fail: ☐ Notes: ___

Q2: Actual data or not? ___
  Pass: ☐ Fail: ☐ Notes: ___

[etc. for all 6 donor Qs or 4 nonprofit Qs]

Overall Impression (1–10 scale):
- Badge clarity: [7/10]
- Messaging fairness: [8/10]
- Trust in T2 context: [7/10]

Feedback for improvement:
___

Recommendation:
☐ Launch as-is
☐ Iterate (retest after changes)
```

---

## Analysis Plan

**Post-session:**
1. Compile response sheets into spreadsheet
2. Watch video clips (1–2 min per key question) to verify transcripts
3. Tally pass/fail per question
4. Identify patterns:
   - Which questions had lowest pass rate? (prioritize fix)
   - Did any demographic group struggle more? (age, giving exp, org type)
   - Common misunderstandings? (note for copy iteration)

**Report (24 hours post-testing):**
- 1-page summary: success metrics, top failure point, 1–2 recommended fixes
- Appendix: full response sheets + key video clips
- Decision: Launch now, or iterate + retest?

---

## Scheduling Template

**Email to recruits:**
```
Hi [Name],

You're invited to test Daanaa's new nonprofit discovery feature.

📅 Pick your time:
- Tue 7/29, 9am PT / 12pm ET ☐
- Tue 7/29, 2pm PT / 5pm ET ☐
- Wed 7/30, 10am PT / 1pm ET ☐
- Wed 7/30, 3pm PT / 6pm ET ☐
- Thu 7/31, 9am PT / 12pm ET ☐
- Thu 7/31, 2pm PT / 5pm ET ☐

RSVP: [Calendly link]
Zoom: [Link sent 1 day before]
Gift card: Sent within 48 hours
```

---

## Go/No-Go Decision

**Launch v6 publicly if:**
- 8/8 pass comprehension tests (Q1–Q6 for donors, accuracy + claim for nonprofits)
- No systematic misunderstanding of T2 inference
- Nonprofits confirm peer groups are accurate
- Legal sign-off received

**Iterate if:**
- 6–7/8 pass (identify weak question, redesign, retest)
- <6/8 pass (major redesign needed)
- Legal requests changes to copy/disclaimer

**Timeline:**
- Testing: 2026-07-29 to 2026-07-31 (3 days)
- Analysis: 2026-08-01 (1 day)
- Retest (if needed): 2026-08-02 to 2026-08-03 (2 days)
- Public launch: 2026-08-05 (pending legal sign-off)
