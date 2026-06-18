# Sprint 1 Testing Strategy

**Goal:** Launch Aug 15 with zero critical bugs + high confidence in core flows.

**Testing Levels:**
1. Unit tests (backend functions)
2. Integration tests (API endpoints)
3. End-to-end tests (full user flows)
4. Sandbox testing (50 real nonprofits)
5. Manual QA (edge cases, UX)

---

## Unit Tests (Backend)

**Framework:** pytest  
**Coverage target:** 80%+

**What to test:**
```python
# Agent validation logic
def test_onboarding_agent_fuzzy_match_ein():
    # EIN "001234567" should match "001234568" if name matches
    assert fuzzy_match_irs("001234567", "Save the World") > 0.8

def test_onboarding_agent_email_domain_check():
    # Email "ceo@nonprofit.org" should match website "nonprofit.org"
    assert verify_email_domain("ceo@nonprofit.org", "https://nonprofit.org") == True
    
    # Email "ceo@gmail.com" should be flagged for manual review
    assert verify_email_domain("ceo@gmail.com", "https://nonprofit.org") == False

def test_support_agent_classification():
    # Classify support emails correctly
    assert classify_email("How do I claim my profile?") == "nonprofit-claim-q"
    assert classify_email("I found a bug") == "bug"
    assert classify_email("Can I volunteer?") == "volunteer"

# Database models
def test_org_claim_creation():
    claim = OrgClaim(org_ein="001234567", status="approved")
    db.add(claim)
    assert claim.created_at is not None

def test_wallet_data_sync():
    wallet = WalletData(donor_email="jane@example.com")
    wallet.bookmarks = ["ein_1", "ein_2"]
    db.add(wallet)
    assert WalletData.query.filter_by(donor_email="jane@example.com").one().bookmarks == ["ein_1", "ein_2"]

# Search logic
def test_search_filters():
    # Search by cause + location + health
    results = search_orgs(cause="environment", location="texas", health="healthy")
    assert all(r.cause == "environment" for r in results)
    assert all(r.health_signal == "HEALTHY" for r in results)
```

**Run:** `pytest -v --cov=backend tests/`

---

## Integration Tests (API Endpoints)

**Framework:** pytest + FastAPI TestClient  
**Coverage target:** All 6 endpoints

```python
def test_search_api_returns_valid_response():
    response = client.get("/api/orgs?q=climate&cause=environment")
    assert response.status_code == 200
    assert "results" in response.json()
    assert "total" in response.json()

def test_nonprofit_detail_api():
    response = client.get("/api/orgs/001234567")
    assert response.status_code == 200
    data = response.json()
    assert data["ein"] == "001234567"
    assert "financial_context" in data

def test_claim_submission_auto_approves_valid():
    response = client.post("/api/claims/submit", json={
        "org_ein": "001234567",
        "org_name": "Save the World",
        "website": "https://savetheworld.org",
        "claimer_email": "ceo@savetheworld.org"
    })
    assert response.status_code == 200
    assert response.json()["status"] == "approved"

def test_claim_submission_flags_invalid_email():
    response = client.post("/api/claims/submit", json={
        "org_ein": "001234567",
        "org_name": "Save the World",
        "website": "https://savetheworld.org",
        "claimer_email": "random@gmail.com"  # Domain mismatch
    })
    assert response.status_code == 200
    assert response.json()["status"] == "flagged"

def test_wallet_add_bookmark():
    response = client.post("/api/wallet/add-bookmark", json={"ein": "001234567"})
    assert response.status_code == 200

def test_wallet_add_intent():
    response = client.post("/api/wallet/add-intent", json={
        "ein": "001234567",
        "intent_type": "giving"
    })
    assert response.status_code == 200
```

**Run:** `pytest tests/integration/ -v`

---

## End-to-End Tests (User Flows)

**Framework:** Playwright (browser automation)  
**Run:** `playwright test`

```javascript
// Donor flow: Search → Detail → Wallet
test('donor can search, view detail, and add to wallet', async ({ page }) => {
  // Go to search
  await page.goto('http://localhost:5173/search');
  
  // Search for "climate"
  await page.fill('[placeholder="Search"]', 'climate');
  await page.click('[type="submit"]');
  
  // Wait for results
  await page.waitForSelector('.nonprofit-card');
  
  // Click first result
  await page.click('.nonprofit-card:first-child');
  
  // Should be on detail page
  await page.waitForSelector('.detail-page');
  
  // Add to wallet
  await page.click('[aria-label="Add to wallet"]');
  
  // Should show success message
  await expect(page.locator('text=Added to wallet')).toBeVisible();
  
  // Go to wallet
  await page.goto('http://localhost:5173/wallet');
  
  // Should show the nonprofit
  await expect(page.locator('text=Climate org name')).toBeVisible();
});

// Nonprofit flow: Claim profile
test('nonprofit can claim profile and see it live', async ({ page }) => {
  // Go to claim form
  await page.goto('http://localhost:5173/claim');
  
  // Fill form
  await page.fill('[name="org_ein"]', '001234567');
  await page.fill('[name="org_name"]', 'Save the World');
  await page.fill('[name="website"]', 'https://savetheworld.org');
  await page.fill('[name="claimer_email"]', 'ceo@savetheworld.org');
  
  // Submit
  await page.click('[type="submit"]');
  
  // Should show success
  await expect(page.locator('text=Profile claimed')).toBeVisible();
  
  // Visit profile
  const profileUrl = await page.locator('a:has-text("View your profile")').getAttribute('href');
  await page.goto(profileUrl);
  
  // Should see profile details
  await expect(page.locator('text=Save the World')).toBeVisible();
});

// Error case: Invalid claim should flag
test('nonprofit with mismatched email gets flagged', async ({ page }) => {
  await page.goto('http://localhost:5173/claim');
  
  await page.fill('[name="org_ein"]', '001234567');
  await page.fill('[name="org_name"]', 'Save the World');
  await page.fill('[name="website"]', 'https://savetheworld.org');
  await page.fill('[name="claimer_email"]', 'random@gmail.com');  // Wrong domain
  
  await page.click('[type="submit"]');
  
  // Should show "flagged for review" message
  await expect(page.locator('text=We need to verify')).toBeVisible();
});
```

---

## Sandbox Testing (50 Nonprofits)

**Phase:** Aug 10–15  
**Participants:** 50 real nonprofits (recruited by Akbar)  
**Deliverables:** Feedback + bug reports

**What we're testing:**
1. **Claim form UX:** Can nonprofits claim without confusion?
2. **Profile visibility:** Once claimed, can donors find them?
3. **Wallet functionality:** Do donors understand how to add/use wallet?
4. **Search quality:** Are results relevant?
5. **Agent behavior:** Does onboarding agent work for 80%+ of claims?

**Feedback collection:**
- Post-claim survey: "Was the form easy? (1-5)"
- Email follow-up: "Are donors finding you?"
- Bug reports: "I tried to [action] but [error]"

**Success criteria:**
- 80%+ of claims auto-approved (agent works)
- 0 critical UX issues (all claims complete form)
- 0 frontend crashes

**Bug triage:**
- P0 (blocks feature): Fix immediately
- P1 (degrades UX): Fix before public launch
- P2 (nice-to-have): Defer to Sprint 2

---

## Manual QA Checklist (Aug 13–15)

**Search Page**
- [ ] Search with 1 keyword
- [ ] Search with multiple keywords
- [ ] Filter by cause (all causes)
- [ ] Filter by location (major states)
- [ ] Filter by health (all 3 levels)
- [ ] Filter by hidden gem (on/off)
- [ ] Combine filters (cause + location + health)
- [ ] Search with 0 results → shows helpful message
- [ ] Pagination (20 per page)
- [ ] Mobile: responsive, touch-friendly

**Nonprofit Detail Page**
- [ ] Load detail for random nonprofit
- [ ] Financial context displays correctly
- [ ] Hidden gem explanation (if applicable)
- [ ] Donation link works (if verified)
- [ ] Similar nonprofits list (6 shown)
- [ ] Add to wallet button works
- [ ] Mobile: responsive

**Wallet Page**
- [ ] Add bookmark → shows in wallet
- [ ] Add giving intent → shows in wallet
- [ ] Remove from wallet → gone
- [ ] Wallet persists after refresh (localStorage)
- [ ] Wallet syncs if logged in (Google account)

**Claim Form**
- [ ] Fill form (valid data) → auto-approve
- [ ] Fill form (email domain mismatch) → flag for review
- [ ] Submit with missing fields → validation error
- [ ] Mobile: form responsive

**Agent Testing**
- [ ] Support email arrives → agent classifies
- [ ] Classification correct 100% (test 10 emails)
- [ ] Draft response plausible
- [ ] Approval flow works (Akbar approves → email sent)

**Performance**
- [ ] Search returns <500ms
- [ ] Detail page loads <200ms
- [ ] No 500 errors in logs
- [ ] No memory leaks (check for 10 min)

**Security**
- [ ] HTTPS only (no HTTP)
- [ ] Google OAuth flow works
- [ ] No API keys in logs
- [ ] Rate limiting works (test 101 requests/min)

---

## Regression Test Suite (Ongoing)

**Run before every push:**
```bash
pytest tests/ --cov=backend --cov-fail-under=80
playwright test
```

**Automated (CI/CD, if available):**
- Unit tests
- Integration tests
- Coverage check

---

## Success Criteria (Aug 15 Launch)

- [ ] ✅ All unit tests pass (80%+ coverage)
- [ ] ✅ All integration tests pass
- [ ] ✅ All E2E tests pass
- [ ] ✅ Sandbox testing complete (50 nonprofits, 0 blockers)
- [ ] ✅ Manual QA checklist 100% complete
- [ ] ✅ Zero critical bugs open
- [ ] ✅ Performance meets targets (<500ms search)
- [ ] ✅ Security baseline met (HTTPS, rate limiting)

---

## Post-Launch Monitoring (Aug 15+)

**First week:**
- [ ] API uptime 99%+
- [ ] Error rate <0.1%
- [ ] Support emails reviewed daily
- [ ] Bug reports triaged within 24 hours

**Ongoing:**
- Weekly regression tests
- Monthly E2E test refresh
- Quarterly security audit

---

**Owner:** QA Lead  
**Status:** Checklists ready  
**Next:** Engineer implements tests as code in Sprint 1

---

*Created: Jun 18, 2026*  
*Last updated: Jun 18, 2026*
