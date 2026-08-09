# Beta Disclosure Policy — Web Discovery & Donation Links

**Core Principle:** Full transparency about what we discovered vs. what the organization verified.

---

## Data Classification

### Tier 1: Org-Verified (Status = 'ok')
- **Source:** IRS records, Form 990, org claimed data
- **Verification:** Confirmed by organization or official government source
- **Display:** No disclosure needed
- **Example:** Website on 990 filing, donated website from org claim

### Tier 2: Heuristic-Discovered (Status = 'beta')
- **Source:** Automated pattern matching + HTTP verification
- **Verification:** Domain exists and responds, NOT confirmed by org
- **Display:** ALWAYS include disclosure
- **Example:** `example.org` matches org name pattern + domain responds to HTTP GET

---

## Disclosure Requirements

### For Beta Websites

**API Response:**
```json
{
  "website": "example.org",
  "website_status": "beta",
  "website_disclosure": "🔍 Website discovered via heuristic search and verified to exist, but NOT confirmed by the organization. Always verify on their official channels before using. Organizations can claim and update their information at daanaa.org/for-nonprofits"
}
```

**Frontend (Org Detail Page):**
```
Website: example.org
⚠️  This website was discovered automatically and has not been verified 
by the organization. Always confirm on their official channels.
[Claim and update your information →]
```

### For Beta Donation Links

**API Response:**
```json
{
  "donate_url": "https://example.org/donate",
  "donate_platform": "custom",
  "donate_url_status": "beta",
  "donate_confidence": 85,
  "donate_link_disclosure": "🔍 Donation link discovered automatically and NOT verified by the organization. Always confirm this link on their official website before giving. Help us verify: claim your profile at daanaa.org/for-nonprofits"
}
```

**Frontend (Org Detail - Give Section):**
```
[Give to Example Org →] https://example.org/donate
⚠️  This donation link was discovered automatically and has NOT been 
verified by the organization. Always confirm on their official website.
[Is this correct? Report →]
```

---

## Quality Metrics

### Website Discovery (Phase 1-2)
- **Source:** Pattern matching + HTTP HEAD/GET
- **Confidence:** 85%+ (domain responds to HTTP)
- **False positive rate:** ~5-10% (404s, redirects, domain squatters)
- **Remediation:** Org can claim profile and verify/correct

### Donation Link Extraction (Phase 3)
- **Source:** HTML parsing for donate/give/contribute links
- **Confidence:** 70-85% (heuristic pattern matching)
- **False positive rate:** ~10-20% (membership pages, sponsorship forms marked as donate)
- **Remediation:** Org can claim profile and verify/correct

### Semantic Verification (Phase 4, when available)
- **Source:** GPU embeddings + address matching
- **Confidence:** 85-95% (semantic similarity)
- **False positive rate:** <5% (only high-similarity matches)
- **Remediation:** Final verification step before moving to 'ok' status

---

## User Trust Protection

### What We Show
1. **Org name, location, EIN** - IRS verified ✓
2. **Lamp tier (visibility)** - Based on real data ✓
3. **Financial Health** - Peer comparison ✓
4. **Website (beta)** - Exists but not org-confirmed ⚠️
5. **Donation link (beta)** - Found on website but not org-confirmed ⚠️

### What We Don't Show
- ✗ Non-tax-deductible orgs (filtered out)
- ✗ Revoked orgs (hourly check removes them)
- ✗ Unverified data presented as confirmed
- ✗ AI-generated scores without data basis

### Remediation Paths
**For Inaccurate Data:**
1. Click "Report an issue" → fills feedback form with EIN pre-filled
2. "Claim your profile" → org directly corrects data
3. Manual review queue → staff verifies contested data

---

## Implementation in Frontend

### OrgCard (Search Results)
```
[Organization Name]
[Lamp Tier] [Location]
[Revenue] [Category]

[If website_status = 'beta']
  Website: example.org ⚠️ (heuristic-discovered)

[If donate_url_status = 'beta']  
  Donate: example.org/donate ⚠️ (auto-discovered, verify first)

[Give] [Compare] [Details →]
```

### OrganizationDetail (Full Profile)
```
Hero Section:
  [Lamp tier] [Verified facts]
  ✓ Registered US Nonprofit
  ✓ Annual report filed (FY 2024)
  [Claimed / Unclaimed]

Website Section:
  [If website_status = 'ok']
    Website: example.org ✓ (org-verified)
  [If website_status = 'beta']
    Website: example.org ⚠️
    Discovered via automated search.
    This is not confirmed by the organization.
    [Verify on their channels] [Report issue]

Giving Section:
  [If donate_url_status = 'ok']
    Give directly → example.org/donate ✓
    [Report issue]
  [If donate_url_status = 'beta']
    Give directly → example.org/donate ⚠️
    This link was found automatically and not verified.
    Always confirm on their official website.
    [Report issue]

[Claim and update your information →]
```

---

## Escalation to 'ok' Status

Beta → OK transition requires:
1. **Organization claims profile** + verifies data, OR
2. **Semantic verification** (Phase 4) confirms 85%+ confidence + manual spot-check, OR
3. **Staff review** marks as verified after manual check

**Goal:** 30-50% of beta websites move to 'ok' within 6 months as orgs claim profiles.

---

## Compliance & Audit

### What We Track
- `website_status`: 'ok' vs 'beta' (audit trail)
- `website_checked_at`: When verification happened
- `donate_url_status`: 'ok' vs 'beta' vs 'dead' (audit trail)
- `donate_checked_at`: When link was verified
- `donate_confidence`: Confidence score (0-100)

### What We Log
- Phase 1: 795 websites discovered (candidates → verified)
- Phase 2: 490 donation links extracted (confidence 85%)
- Phase 4 (when ready): Semantic verification confidence scores

### Audit Query Example
```sql
-- Find all beta websites for compliance review
SELECT EIN, organization_name, website, website_status, website_checked_at
FROM registry_enriched
WHERE website_status = 'beta'
ORDER BY website_checked_at DESC
```

---

## Disclosure Text (Shown to Users)

### In API Response
```
website_disclosure: "🔍 Website discovered via heuristic search and verified to exist, but NOT confirmed by the organization. Always verify on their official channels before using. Organizations can claim and update their information at daanaa.org/for-nonprofits"
```

### On Org Detail Page
```
⚠️ This website was discovered automatically and has NOT been 
verified by the organization. Always confirm on their official 
channels before donating.

[Report issue] [Claim profile to verify]
```

### In FAQ/Help
```
Q: What does the ⚠️ icon mean?
A: It means we discovered this information automatically (not from the 
organization). It's real data (the website exists, the link works), but 
the organization hasn't confirmed it yet. Always verify directly with 
them before donating.

Organizations can claim their profiles to confirm, update, or correct 
any information at daanaa.org/for-nonprofits.
```

---

## Success Criteria

✅ **Credibility maintained:**
- Clear distinction between org-verified and auto-discovered
- No misrepresentation of data
- Users trust the ⚠️ icon means "human-review needed"

✅ **Data quality improved:**
- +300K-500K websites accessible
- +100K-180K donation links available
- 85%+ accuracy on what we show

✅ **User empowerment:**
- Organizations can claim + verify
- Users get more discovery paths
- No dark patterns or hidden curation

---

**Policy ensures we expand discovery WITHOUT sacrificing trust.**
