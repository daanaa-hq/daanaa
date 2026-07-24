# Guided Discovery Implementation Plan (2026-07-24)

**Status:** Ready to start  
**Complexity:** Medium (5-day sprint for full MVP + testing)  
**Risk Level:** Low (uses existing APIs, no schema changes, user-controlled UX)  
**Dependencies:** None blocking (can start immediately after shuffle QA)

---

## Executive Summary

Implement `/discover` as a guided, 5-step questionnaire that produces 20–25 transparent results using existing directory APIs. No opaque AI, no profiling, no payment influence. Complementary to `/directory` shuffle feature.

**Key Principle:** Transparent + reversible + respectful of user agency.

---

## Implementation Phases

### Phase 1: Core Flow (2 days)
Build the 5-step questionnaire with local state management and URL preservation.

**Deliverables:**
- ✅ GuidedDiscovery page component
- ✅ Progress indicator (Step N of 5)
- ✅ 5 Question screens (purpose, cause, place, connection, review)
- ✅ Navigation (back, skip optional, start over, continue)
- ✅ URL state encoding/decoding (shareable without PII)

**Files to Create:**
```
frontend/src/pages/GuidedDiscovery.tsx
frontend/src/components/discovery/
  ├─ DiscoveryProgress.tsx
  ├─ DiscoveryQuestion.tsx
  ├─ DiscoveryChoice.tsx
  ├─ DiscoveryResults.tsx
  ├─ DiscoveryWhyHere.tsx
frontend/src/lib/discovery.ts (choice→filter mapping)
```

**Testing:** Manual browser testing, accessibility keyboard/screen reader.

### Phase 2: Result Generation (1.5 days)
Implement deterministic shortlist builder using existing `/api/organizations` filters.

**Algorithm:**
1. Apply cause filters (NTEE tags)
2. Apply location filters (zip, state, proximity)
3. Apply connection filters (has_website, open_to_volunteers, smaller_org)
4. Sort by criteria match count (descending)
5. Add discovery mix for "broad mix" preference
6. Cap at 25 results, handle <20 gracefully

**Edge Cases:**
- Zero results → show friendly message, offer "Broaden search"
- Fewer than 20 → explain, offer to show more
- "Smaller org" requested → filter by revenue band, never describe as "better"
- "Broad mix" → 70% criteria-matched + 30% random from same cause/location

**Testing:** Unit tests for algorithm, API contract tests, edge case coverage.

### Phase 3: Results Display (1.5 days)
Render organization cards with "Why it is here" explanations.

**Card Contents:**
- Organization name + location
- Cause tag (plain language)
- Badges: website available, volunteer ops, recent filing
- "Why it is here" explanation
- "View organization" link
- Optional: "Save to wallet" (only if user intentionally selected it)

**Display Groups:**
- Close to what you selected (all criteria match)
- A few nearby possibilities (most criteria match)
- Something you may not have considered (discovery mix)

**Testing:** Visual regression, mobile responsiveness (375px minimum), dark mode.

### Phase 4: Home Page Integration (0.5 days)
Add link below search bar on home page.

**Placement:**
```
[Search the directory input box]

Not sure where to begin?
Answer a few simple questions to find a short list of organizations to explore.

[Start guided discovery]

Your answers help narrow the directory. Daanaa does not rank organizations 
or tell you where to give. Each result is a starting point for your own review.
```

**Testing:** Link works, visual parity with search bar.

### Phase 5: Analytics & Monitoring (1 day)
Implement privacy-respecting analytics tracking.

**Events to Track:**
- discovery_started
- question_completed (question name only)
- result_list_shown (count, criteria)
- result_opened
- criteria_changed
- another_list_requested
- discovery_completed
- discovery_abandoned (step)

**What NOT to Track:**
- Free-form answers, emails, IPs, wallet contents, donation amounts

**Testing:** Verify analytics payloads, no PII leakage.

---

## Technical Architecture

### State Management
Use URL + React state (no localStorage persistence by default):

```typescript
interface DiscoveryState {
  step: 1 | 2 | 3 | 4 | 5
  intent: string[]        // ['give-money', 'volunteer', ...]
  causes: string[]        // NTEE1 codes: ['E', 'P', ...]
  place: string          // 'near-me' | 'zip:97401' | 'state:CA' | 'nationwide'
  connection: string[]   // ['website', 'volunteer', 'smaller', ...]
  mix: 'focused' | 'broad'
  results?: OrganizationShortlist[]
}

// URL encoding: /discover?intent=volunteer,give&causes=E,P&place=zip:97401&connection=website,volunteer&mix=broad
```

### API Usage
Reuse existing `/api/organizations` endpoint with mapped filters:

| Question | Maps To | Example |
|----------|---------|---------|
| Cause (E, P, Y) | `ntee` param | `?ntee=E,P` |
| State | `state` param | `?state=CA` |
| Zip + radius | `near` param | `?near=97401&radius_mi=25` |
| Website | `has_website` param | `?has_website=1` |
| Volunteer | `open_to_volunteers` param | `?open_to_volunteers=1` |
| Smaller | `revenue` filter | Filter to band 0-1 (< $700K) |

**Result Builder Logic:**
```python
# Backend or frontend can do this
def build_shortlist(filters: Dict) -> List[Org]:
    results = get_organizations(filters)
    # Sort by criteria match count
    scored = [(org, count_criteria_match(org, filters)) for org in results]
    scored.sort(key=lambda x: -x[1])
    
    # Handle mix preference
    if filters['mix'] == 'broad':
        # Take top 70%, add 30% random
        focused = scored[:int(len(scored) * 0.7)]
        random_slice = shuffle(scored[int(len(scored) * 0.7):])[:int(len(scored) * 0.3)]
        return focused + random_slice
    else:
        return scored[:25]
```

### Accessibility
- ARIA labels on all choices
- Keyboard navigation (Tab/Enter)
- Focus management (move to next question after Continue)
- Screen reader announcements for progress
- No color-only indicators
- Reduced motion: suppress transitions
- Mobile: 375px minimum width, touch targets 44px+

---

## Component Map

### GuidedDiscovery.tsx (Main Page)
- Route: `/discover`
- State: DiscoveryState
- Flow: Step 1 → Step 5 → Results
- Navigation: Back/Skip/Start Over buttons
- Analytics tracking

### DiscoveryProgress.tsx
- Shows "Step N of 5"
- Progress bar (optional, if fits design)
- ARIA live region for announcements

### DiscoveryQuestion.tsx
- Renders a question (heading + subheading)
- Renders choice children
- Continues/backs to adjacent steps
- Focus management

### DiscoveryChoice.tsx
- Multi-select or single-select toggle
- Label + icon (optional)
- Selected state styling
- Keyboard accessible

### DiscoveryResults.tsx
- Grid of 20–25 organization cards
- Display groups (Close / Nearby / Discovery)
- Handles <20 and zero-result states
- Action buttons: Change answers / Show another list / Start over / Browse full directory

### DiscoveryWhyHere.tsx
- Explanation tied to user choices
- Example: "Included because you selected Houston, education, and volunteering."
- Plain language only

### discovery.ts (Utilities)
- `encodeState()` / `decodeState()` for URL
- `mapToDirectoryFilters()` — convert discovery choices to API params
- `buildShortlist()` — deterministic algorithm
- `explainInclusion()` — generate "Why it is here" text

---

## Testing Strategy

### Unit Tests
```typescript
// discovery.ts
- encodeState preserves round-trip
- decodeState rejects malformed URLs
- mapToDirectoryFilters produces correct API params
- buildShortlist sorts by criteria match
- buildShortlist "broad mix" has ~30% random
- explainInclusion matches user's selections
```

### Integration Tests
```typescript
// Components
- GuidedDiscovery flow from start to results
- Back button returns to previous step
- Start over clears all state
- Continue button disabled until required fields selected
- Results load and display correctly
- "Change answers" preserves results list but returns to questions
- "Show another list" changes order without changing criteria
```

### Accessibility Tests
```
- Keyboard navigation: Tab through all questions
- Screen reader: Progress announced, labels clear
- Mobile: 375px viewport, no horizontal scroll
- Reduced motion: transitions disabled when OS preference set
- Color: selected state visible without color alone
```

### QA Acceptance (from spec)
All 14 criteria from GUIDED_DISCOVERY_EXPERIENCE_HANDOFF_2026-07-24.md

---

## Timeline

| Phase | Task | Duration | Owner |
|-------|------|----------|-------|
| 1 | Core flow (questions, state, navigation) | 2 days | Frontend |
| 2 | Result algorithm (filtering, sorting, discovery mix) | 1.5 days | Frontend + Backend |
| 3 | Results display (cards, explanations, edge states) | 1.5 days | Frontend |
| 4 | Home page link | 0.5 days | Frontend |
| 5 | Analytics tracking | 1 day | Frontend |
| — | Testing + polish | 1 day | QA + Frontend |
| **Total** | | **~7 days** | |

**Can start:** Immediately (no blocking dependencies)  
**Expected ready:** 2026-07-31 (end of week)  
**Blockers:** None identified

---

## Risk & Mitigation

| Risk | Mitigation |
|------|-----------|
| "Smaller org" filter creates hidden ranking | Algorithm explicitly filters by revenue, not score; no "better" language |
| AI inference expected in v1 | Spec is clear: existing filters only; AI deferred to v2 |
| URL state leaks PII | Validation: no emails, IPs, wallet data, raw IDs in URL |
| Users confused about transparency | Copy is explicit: "did not rank", "starting point", "narrowed the directory" |
| Accessibility regressions | Keyboard + screen reader testing before QA |
| Results feel like "recommendations" | Display groups use neutral language (Close / Nearby / Discovery) |

---

## Success Metrics

✅ **Completion rate:** >70% of users who start complete the flow  
✅ **Time to first result:** <2 minutes  
✅ **Result quality:** Users open 2+ organizations per session (behavioral signal)  
✅ **Transparency:** Users understand "why it is here" explanations  
✅ **No silent broadening:** Zero-result and <20-result states handled gracefully  
✅ **Return visits:** 15%+ of users visit `/discover` again in next 2 weeks  

---

## Dependencies & Integration

**Frontend dependencies:**
- React Router (already available)
- Existing `getOrganizations()` API call
- Existing cause taxonomy (SORT_OPTIONS, NTEE_CATEGORIES)
- Existing location/proximity logic

**Backend dependencies:**
- Existing `/api/organizations` endpoint
- No new schema or API changes needed

**Existing features to preserve:**
- `/directory` (unchanged)
- Organization detail pages
- Wallet flow
- Volunteer event pages

---

## Deployment

**Safe merge:**
- No schema changes
- No API breaking changes
- Route-only addition (/discover is new)
- Can A/B test: show link to 50% of users on home page

**Smoke test after deploy:**
1. `/discover` loads
2. Complete flow → results show
3. Home page link works
4. `/directory` unchanged
5. Analytics payloads don't leak PII

---

## Next Steps

1. **Approve this plan** (proceed immediately or adjust scope)
2. **Create discovery.ts** with state management + algorithm
3. **Build question components** (5-step flow)
4. **Implement result builder + display**
5. **Integrate home page link**
6. **Add analytics tracking**
7. **QA validation** against 14 acceptance criteria
8. **Deploy with A/B test** (50% users see link initially)

Ready to start Phase 1? 🚀
