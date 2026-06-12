# Week 3: Feedback Collection & Metrics

**Timeline**: June 12-13, 2026 (Thu-Fri)  
**Cohort**: 1% of users (~100-500 daily actives)  
**Decision**: Friday EOD

---

## Success Metrics

### Primary Metrics (Must Measure)

| Metric | Target | Method | Threshold |
|--------|--------|--------|-----------|
| **Archetype Clarity** | ≥80% | "Do you understand this financial category?" | Clear/Somewhat/Unclear votes |
| **Peer Comparison Preference** | ≥70% | "Is peer comparison helpful?" | Prefer peer / Equal / Prefer absolute |
| **NTEE Questionnaire Accuracy** | ≤20% misclass | For B,C,E,L,N,S,U: user input vs default | % disagreement |
| **Coverage on Viewed Orgs** | ≥98% | API response rate | Count non-null v5_context |

### Secondary Metrics (Nice to Have)

| Signal | What It Tells Us |
|--------|------------------|
| Time on page | Do users spend more time reading v5 vs v4? |
| Scroll depth | Do users read full donor explanation? |
| Feedback volume | What % of users volunteer comments? |
| Archetype distribution | Are all 5 archetypes equally understood? |
| Health signal accuracy | Do users agree with HEALTHY/STABLE/CAUTION? |

---

## In-App Feedback Form

### Display Conditions
- Show on org detail pages for v5-enabled users
- Appears after V5Context component
- Sticky footer: "Help us improve this beta"
- Can be dismissed (don't force)

### Form Schema

```json
{
  "form_id": "v5_context_feedback",
  "question_1": {
    "text": "Does this financial comparison make sense to you?",
    "type": "radio",
    "options": [
      { "value": "clear", "label": "Yes, it's clear" },
      { "value": "somewhat", "label": "Somewhat clear, but I have questions" },
      { "value": "unclear", "label": "No, I don't understand this" }
    ]
  },
  "question_2": {
    "text": "What would help you understand better?",
    "type": "textarea",
    "optional": true,
    "placeholder": "e.g., I don't know what 'Donation-Funded' means..."
  },
  "question_3": {
    "text": "Is peer comparison more helpful than a single number score?",
    "type": "radio",
    "options": [
      { "value": "prefer_peer", "label": "Yes, comparing to peers is better" },
      { "value": "equal", "label": "Both are equally helpful" },
      { "value": "prefer_absolute", "label": "No, a single score is better" }
    ]
  },
  "question_4": {
    "text": "For this organization, what's the primary funding source?",
    "type": "radio",
    "conditional": "org.NTEE1 in [B, C, E, L, N, S, U]",
    "options": [
      { "value": "donations", "label": "Donations/Grants" },
      { "value": "earned", "label": "Earned revenue (fees, contracts)" },
      { "value": "endowment", "label": "Endowment/Investment income" },
      { "value": "membership", "label": "Membership dues" },
      { "value": "mixed", "label": "Mix of multiple sources" }
    ]
  },
  "question_5": {
    "text": "Any other feedback?",
    "type": "textarea",
    "optional": true
  }
}
```

---

## Data Collection Points

### Server-Side Tracking

Log to `feedback_v5.jsonl` (one JSON per line):

```json
{
  "timestamp": "2026-06-12T14:32:01Z",
  "user_id_hash": "abc123def456",
  "ein": "391214392",
  "in_cohort": true,
  "org_scored": true,
  "form_responses": {
    "clarity": "clear",
    "clarity_comment": "Clear explanation",
    "peer_vs_absolute": "prefer_peer",
    "ntee_funding_source": "donations",
    "other_feedback": ""
  },
  "page_metrics": {
    "time_on_page_sec": 45,
    "scroll_depth_pct": 95,
    "form_shown_at_sec": 30,
    "form_submitted": true,
    "submission_latency_sec": 15
  }
}
```

### Frontend Events

Track via localStorage (no external analytics):

```javascript
// Log when V5Context renders
logEvent('v5_context_rendered', {
  ein: org.EIN,
  archetype: org.v5_context.archetype.key,
  percentile: org.v5_context.score.percentile
})

// Log when user sees form
logEvent('feedback_form_shown', {
  ein: org.EIN,
  visible_at_sec: timeOnPage
})

// Log on form submit
logEvent('feedback_form_submitted', {
  ein: org.EIN,
  clarity_response: formData.clarity,
  preference_response: formData.preference
})
```

---

## Analysis Plan (Friday AM)

### Clarity Analysis

```python
# Count responses
clear_pct = (clear_count / total_responses) * 100

if clear_pct >= 80:
  verdict = "✓ PASS — Archetype labels are clear"
else:
  verdict = "✗ FAIL — Need terminology adjustment"
  
# Find most confusing archetypes
by_archetype = responses.groupby('archetype_key').agg({
  'clarity': lambda x: (x == 'clear').sum() / len(x)
})
```

### Preference Analysis

```python
prefer_peer_pct = (prefer_peer_count / total_responses) * 100

if prefer_peer_pct >= 70:
  verdict = "✓ PASS — Users prefer peer comparison"
else:
  verdict = "✗ FAIL — Peer comparison not resonating"
  
# Check if absolute-score users have lower clarity
absolute_pref = responses[responses.preference == 'prefer_absolute']
absolute_clarity = (absolute_pref.clarity == 'clear').sum() / len(absolute_pref)
```

### NTEE Accuracy Analysis

```python
# For ambiguous categories only
ambiguous_ntee = ['B', 'C', 'E', 'L', 'N', 'S', 'U']
ntee_feedback = responses[responses.org_ntee1.isin(ambiguous_ntee)]

# Compare user input to default archetype
disagreements = (ntee_feedback.user_funding_source != ntee_feedback.default_archetype)
disagreement_pct = (disagreements.sum() / len(ntee_feedback)) * 100

if disagreement_pct <= 20:
  verdict = "✓ PASS — NTEE defaults accurate"
else:
  verdict = "✗ FAIL — Need questionnaire refinement"
  
# Find most problematic categories
by_ntee = ntee_feedback.groupby('org_ntee1').apply(
  lambda x: (x.user_funding_source != x.default_archetype).sum() / len(x)
)
```

### Coverage Analysis

```python
# Track all page views
views_with_v5 = sum(1 for r in responses if r.v5_context_present)
total_org_views = api_logs.count_views()
coverage_pct = (views_with_v5 / total_org_views) * 100

if coverage_pct >= 98:
  verdict = "✓ PASS — v5_context available on viewed orgs"
else:
  verdict = "✗ FAIL — Some orgs missing v5_context"
```

---

## Decision Matrix (Friday EOD)

```
clarity_pass = clear_pct >= 80
preference_pass = prefer_peer_pct >= 70
accuracy_pass = disagreement_pct <= 20
coverage_pass = coverage_pct >= 98

decision = (
  "LAUNCH_WEEK4" if (clarity_pass AND preference_pass AND 
                     accuracy_pass AND coverage_pass)
  else "ITERATE_WEEK3" if (clarity_pass AND preference_pass)
  else "MAJOR_REVISION"
)

if decision == "LAUNCH_WEEK4":
  # Proceed with full launch
  # Remove v4 scores
  # Deploy to 100%
  
elif decision == "ITERATE_WEEK3":
  # Adjust based on feedback
  # Re-test on 5% cohort
  # Extend Week 3 another 2-3 days
  
else:  # MAJOR_REVISION
  # Significant issues found
  # Go back to design phase
  # Schedule next beta attempt
```

---

## Iteration Scenarios

### If Clarity < 80%

**Most likely issue**: Archetype labels unclear

**Solutions**:
- Rename "Donation-Funded Programs" → "Grant & Donation Based"?
- Add 1-line definition: "Organizations funded primarily by donations and grants"
- Link to terminology glossary
- Create archetype examples (real orgs in each type)

**Re-test**: Deploy adjusted labels to 5% of users, repeat feedback collection

### If Preference < 70%

**Most likely issue**: Users confused by percentile concept

**Solutions**:
- Add more context: "Percentile tells you where this org ranks among similar nonprofits"
- Show example: "25th percentile = better than 25%, similar to 75%"
- Simplify donor copy (less jargon)
- Add comparison chart (this org vs peer median)

**Re-test**: Deploy improved explanation to 5%, collect feedback again

### If NTEE Accuracy > 20%

**Most likely issue**: Default archetype incorrect for some categories

**Solutions**:
- Review failed mappings (which B/C/E orgs disagreed most?)
- Adjust default archetype for problem categories
- Improve questionnaire wording (be more specific about funding sources)
- Add examples ("Is your org more like X or Y?")

**Re-test**: Re-run on same 5% cohort with improved questionnaire

---

## Post-Launch Monitoring (Week 4+)

### Daily Metrics (Monitor continuously)

```
API Endpoint Health:
  ✓ /api/organizations/<ein>?v5=true response time
  ✓ v5_context null rate (should be ~78% unscored orgs)
  ✓ Error rates (target: <0.1%)
  
User Engagement:
  ✓ % of users viewing v5_context (should be ~1%)
  ✓ Avg time spent on org detail (should not decrease)
  ✓ Search → org detail conversion (should not regress)
  
Feedback Volume:
  ✓ Forms submitted per day
  ✓ Sentiment of comments (positive/neutral/negative)
  ✓ Most common feedback themes
```

### Weekly Metrics (Analyze trends)

```
Archetype Distribution:
  ✓ Do all 5 archetypes appear evenly in user views?
  ✓ Are some archetypes more confusing than others?
  
Health Signal Distribution:
  ✓ % HEALTHY, STABLE, CAUTION
  ✓ Do users agree with signals?
  
NTEE Mapping Quality:
  ✓ For ambiguous categories, how often do users override defaults?
  ✓ Are overrides consistent (same category always overridden)?
```

---

## Rollback Triggers

If any of these occur, disable v5_context:

```
- Error rate > 1% on /api/organizations endpoint
- v5_context null rate > 85% (suggests data corruption)
- API response time > 500ms (performance regression)
- >30% negative feedback on clarity
- >50% users prefer absolute score over peer comparison
```

**Rollback procedure**:
```bash
# Hide V5Context component (keep serving data)
export FEATURE_FLAG_V5_ENABLED=0

# Restart API
systemctl restart daanaa_api

# Check logs
tail -f /var/log/daanaa/error.log
```

---

## Communication Template (If Iterating)

**Email to early beta users** (if extending Week 3):

```
Subject: v5.0 Financial Context Feedback — Thank You!

Thanks for testing our new peer-based financial comparison system. 
We've received excellent feedback, and based on your input, we're making 
a few refinements this week:

- Clearer archetype names (easier to understand what each category means)
- Better examples (showing real nonprofits in each peer group)
- Improved explanations (less jargon, more context)

We'll launch the updated version early next week. Your feedback helped 
make it better. 🙏

Questions? Reply to this email or visit daanaa.org/feedback
```

---

## Success Example (All Metrics Pass)

```
Thursday 2pm: Feedback collection starts
Friday 9am: Analysis begins

Clarity: 82% (PASS ✓)
  - "Clear" responses: 82%
  - Most confusing: Fee-for-Service (75% clarity, needs one-liner)

Preference: 73% (PASS ✓)
  - Prefer peer: 73%
  - Prefer absolute: 18%
  - Equal: 9%

NTEE Accuracy: 18% misclassification (PASS ✓)
  - Healthcare (C): 12% disagreement
  - Employment (E): 8% disagreement
  - All others: <5%

Coverage: 99% (PASS ✓)
  - v5_context present on 99% of viewed orgs
  - 1% missing only due to data corruption (isolated)

DECISION: LAUNCH WEEK 4
- Deploy v5.0 to 100% of users
- Remove v4 scores from responses
- Publish methodology page
- Send launch announcement
```

---

**Prepared by**: Claude Code  
**Timeline**: June 12-13, 2026  
**Decision**: Friday EOD, 2026-06-13
