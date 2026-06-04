# LEGAL DISCLOSURES & TERMS

**Date:** 2026-06-04  
**Purpose:** Protect Daanaa and users from liability regarding financial scores and unverified data

---

## 1. Data Submission & Privacy Disclosure

**For Org Self-Reporting Form:**

```
By submitting financial information to Daanaa:
- You certify that the revenue and expense figures are accurate
- You authorize Daanaa to use this data for scoring and display
- Your submission may be publicly visible (EIN, revenue, expenses)
- Your email will not be shared or published
- We will process submissions within 5-7 business days
- Submissions are unverified and may be rejected if inconsistent
- See our Privacy Policy (link) for full terms
```

---

## 2. Financial Health Score Disclaimer

**Required on ALL score displays (badge, detail page, search results):**

```
⚠️ IMPORTANT: "Financial Health" is a peer-group ranking, not an absolute measure.
This score reflects how an organization's revenue and program efficiency compares 
to similar organizations of its size and sector.

It does NOT evaluate:
- Mission impact or effectiveness
- Staff compensation
- Program quality
- Community outcomes
- Governance or board quality

A "Strong" rating means efficient relative to peers—it's not a guarantee of 
organizational quality. Always verify additional information before donating.
```

---

## 3. Unscored Org Disclosure

**For orgs with no financial data (shown in search):**

```
🔍 "No Financial Data Available"

This organization does not have revenue/expense data in our database because:
1. They haven't filed recent Form 990 with the IRS
2. They may not be required to file (revenue under $50K threshold)
3. Their data hasn't been published yet

This does NOT mean the organization is unhealthy or unreliable.
To verify legitimacy:
- Check their 501(c)(3) status at IRS.gov
- Visit their website or contact them directly
- Ask for their latest Form 990

Help us score them: Organizations can submit their financial data here [link]
```

---

## 4. Self-Reported Data Disclaimer

**For Tier D orgs (data submitted by the org itself):**

```
⚠️ Self-Reported Data

This financial information was submitted by the organization directly.
Unlike IRS Form 990s (independently filed), we have not independently verified 
these figures.

We recommend:
- Requesting Form 990 directly from the organization
- Verifying via GuideStar or Charity Navigator
- Cross-checking with their annual report

Daanaa assumes no liability for accuracy of self-reported data.
```

---

## 5. Tier Classification Disclosures

### Tier A (Complete Data)
```
Based on Form 990 filing with:
✓ Revenue
✓ Expenses  
✓ Net Assets
✓ Program Expense Percentage

Data source: IRS Form 990 (verified public filing)
Status: Fully scored with peer-group methodology
```

### Tier B (Deductible, Partial Data)
```
Based on Form 990 filing with:
✓ Revenue
✓ Expenses
✗ Program Expense data (estimated from sector benchmark)
✓ Peer group comparison

Data source: IRS Form 990
Status: Peer-ranked with sector-level program estimates
Risk: Program efficiency may vary from sector average
```

### Tier C (Non-Deductible, Partial Data)
```
Based on Form 990 filing with:
✓ Revenue
✓ Expenses
✗ Program Expense data (estimated from sector benchmark)
✓ Peer group comparison

Data source: IRS Form 990
Status: Peer-ranked among non-donor-deductible nonprofits
Note: These organizations are legitimate nonprofits but don't qualify 
for charitable deductions (e.g., unions, professional associations, 
health maintenance organizations, mutual benefit societies)
```

### Tier D (Self-Reported Data) - IF IMPLEMENTED
```
Based on financial data submitted by the organization:
✓ Revenue (organization-provided)
✓ Expenses (organization-provided)
✗ Independently verified
✗ Program Expense breakdown (may not be available)

Data source: Organization self-report
Status: NOT INDEPENDENTLY VERIFIED
Risk: Data unconfirmed, organization may not have submitted accurate figures

Daanaa assumes NO LIABILITY for accuracy.
```

---

## 6. Methodology Disclaimer

**Required on Methodology page and in API responses:**

```
🔬 Our Scoring Methodology

Financial Health scores are RELATIVE rankings, not absolute measures.

How we calculate:
1. Group organizations by operating model (8 categories)
2. Within each model, group by revenue band (7 tiers)
3. Rank by revenue percentile + program efficiency percentile
4. Map to terciles: Strong (top 33%) / Stable (middle) / Inspiring (bottom 33%)

IMPORTANT LIMITATIONS:
- Only based on financial data—doesn't measure impact
- Small organizations aren't penalized for being small
- Peer groups include only orgs with comparable data
- Program expense estimates (Tier B/C) use sector averages

This is NOT:
✗ A credit score
✗ A measure of organizational effectiveness
✗ A guarantee of legitimacy or solvency
✗ Investment advice
✗ A substitute for due diligence

See [methodology page] for full technical details.
```

---

## 7. Liability Limitations

**Add to Terms of Service:**

```
LIMITATION OF LIABILITY

Daanaa provides nonprofit financial information for educational purposes only.

We are NOT liable for:
- Inaccurate or missing IRS Form 990 data (source: IRS)
- Your investment or donation decisions based on our scores
- Organizational changes after last data publication
- Self-reported data accuracy
- Third-party actions or data breaches
- Business decisions made in reliance on our platform

Organizations are responsible for:
- Accuracy of their own self-reported data
- Maintaining current Form 990 filings with IRS
- Updating information when organizational status changes

Users are responsible for:
- Conducting independent due diligence
- Verifying information directly with organizations
- Not relying solely on Daanaa scores for major decisions
```

---

## 8. Form Disclosures (Frontend)

### Org Data Submission Form
```
□ I certify that the revenue and expense figures provided are accurate
□ I understand this data will be publicly visible on Daanaa
□ I authorize Daanaa to score and display my organization's financial health
□ I have read and agree to the Data Submission Terms [link]

[Submit]
```

### Search Results with Unscored Orgs
```
[Organization Name] [UNSCORED - No Financial Data]
Location | NTEE Code | Website

Why unscored:
- IRS Form 990 data not available
- Organization too new or recently revised 501(c)(3) status
- Org can submit data to get scored: [Submit Financial Data]

Help us complete our database
```

---

## 9. API Response Headers

Add to all API responses:

```
X-Data-Source: IRS Form 990 (Tier A/B/C) | Organization Self-Report (Tier D)
X-Verification-Status: IRS-Filed | Self-Reported-Unverified
X-Score-Reliability: Peer-relative ranking, not absolute measure
X-Liability-Disclaimer: See daanaa.org/terms for limitations
```

---

## 10. Email Communications

### Submission Confirmation Email
```
Subject: Daanaa - Financial Data Received

Hi [Organization Name],

Thank you for submitting your financial information to Daanaa!

We received:
- Revenue: $[amount]
- Expenses: $[amount]
- Submitted: [date]

Next steps:
1. We verify accuracy (5-7 business days)
2. Your org receives a peer-based Financial Health score
3. You can claim your profile to manage information

During verification, we may contact you at [email] to confirm data.

Until then, your organization is visible in search with "Unscored - Awaiting Verification"

Questions? Reply to this email.

---
Daanaa | Fair Nonprofit Discovery
daanaa.org
```

---

## 11. Attestation

**By deploying this system, Daanaa attests:**

✅ All disclosures are clear and visible to users  
✅ No misleading claims about score reliability  
✅ Self-reported data clearly marked as unverified  
✅ Users understand limitations before relying on data  
✅ Organization assumes no liability for user decisions  
✅ IRS data attribution is clear (we're a directory, not auditor)  

---

## Legal Checklist

- [ ] Disclosures added to all score displays
- [ ] Self-reported data marked as unverified
- [ ] Methodology page includes full limitations
- [ ] Terms of Service includes liability limitations
- [ ] Form includes data submission agreement
- [ ] Email confirmations include verification timeline
- [ ] API responses include source/verification headers
- [ ] Privacy Policy updated for data collection
- [ ] Unscored org explanation is visible in search
- [ ] Legal review completed by attorney

---

**Status:** Ready for implementation ✅

These disclosures protect Daanaa while being transparent to users about:
- What our scores mean (peer comparison, not absolute truth)
- What data we have (IRS 990 + self-reported)
- What we don't measure (impact, quality, legitimacy verification)
- User responsibility (do your own due diligence)
