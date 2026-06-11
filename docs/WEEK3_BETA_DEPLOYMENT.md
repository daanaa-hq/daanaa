# Week 3: Beta Testing & Iteration

**Status**: Ready for 1% Beta Deployment  
**Timeline**: 1 week  
**Success Criteria**: ≥80% user feedback positive on archetype clarity

## Deployment Plan

### Phase 1: Shadow Scoring (Day 1–3)
Deploy v5.0 alongside v4.0 on 1% of users. Show both scores:
- v4.0 score (current, familiar)
- v5.0 score + peer context (new system being tested)

**Changes needed:**
1. Update `/api/directory/org/{EIN}` to include v5.0 data
   - Add `v5_context` field with archetype, band, benchmarks, donor_copy
   - Keep v4.0 data for comparison
2. Frontend: Show both scores on org detail page
   - Display "New Financial Context" alongside current score
   - Note: "This is a test. Help us improve."

### Phase 2: Feedback Collection (Day 3–7)
Measure:
1. **Comprehension**: "Does 'Donation-Funded Programs' make sense?"
   - Yes → proceed
   - No → adjust terminology
2. **Helpfulness**: "Is peer comparison better than absolute score?"
3. **Archetype mapping**: "Is your org in the right financial category?"
   - For high-risk NTEE codes (B, C, E, L, N, S, U), test the clarifying question

### Success Metrics
- **Clarity**: ≥80% users understand archetype label
- **Satisfaction**: ≥70% prefer peer-based comparison to absolute score
- **Accuracy**: ≤20% misclassification on NTEE questionnaire
- **Coverage**: ≥98% of viewed orgs show v5.0 data

### NTEE Questionnaire Testing
For orgs in ambiguous categories (B, C, E, L, N, S, U):
- Show question: "How does your organization primarily fund itself?"
- Options: Donations, Earned Revenue, Endowment, Membership
- Validate: Does user's answer match our default archetype?
- If >20% disagree, refine the question or default mapping

## Implementation Steps

### 1. API Integration (2 hours)
```python
# In daanaa_api.py, add v5 context to org response:
from enrich_api_responses import get_v5_context

@app.route('/api/directory/org/<ein>')
def get_org(ein):
    org = fetch_from_registry(ein)
    v5_context = get_v5_context(ein)
    return {
        ...org,
        'v5': v5_context,  # New field
    }
```

### 2. Frontend Display (4 hours)
Add to `OrganizationDetail.tsx`:
```tsx
{org.v5 && (
  <div className="financial-context-v5">
    <h3>Financial Context (Beta)</h3>
    <p>Archetype: {org.v5.archetype.label}</p>
    <p>Band: {org.v5.band.label}</p>
    <p>Peer comparison: {org.v5.score.percentile}th percentile</p>
    <p>{org.v5.donor_explanation}</p>
    <button>Feedback</button>
  </div>
)}
```

### 3. Rollout (2 hours)
```bash
# Build and deploy to 1% of users
npm run build
./safe_deploy_droplet.sh --beta --feature v5_scoring
```

### 4. Monitoring (Ongoing)
Track:
- View count: % of users seeing v5 data
- Click-through: % clicking "provide feedback"
- Feedback sentiment: Are explanations clear?
- Archetype accuracy: Do users agree with assignments?

## Feedback Form (Simple)
```
Does this financial comparison make sense to you?
☐ Yes, it's clear
☐ Somewhat clear, but I have questions
☐ No, I don't understand this

What would help you understand better?
[Text field]

For this organization, what's the primary funding source?
☐ Donations/Grants
☐ Earned revenue (fees, contracts, tuition)
☐ Endowment/Investment income
☐ Membership dues
☐ Mix (explain below)

[Optional text]
```

## Rollback Plan
If satisfaction <70% on clarity:
1. Hide v5 score UI, keep serving data
2. Adjust terminology based on feedback
3. Re-test on 5% of users
4. Iterate until ≥80% comprehension

## Success = Week 4 Launch

If metrics are met:
- Deploy to 100% of users
- Remove v4.0 comparison (full cutover)
- Publish research methodology page
- Send user communication email

---

**Prepared for**: Week 3 Beta Testing  
**Next review**: After 3 days of feedback collection
