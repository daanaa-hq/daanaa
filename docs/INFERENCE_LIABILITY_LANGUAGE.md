# Legal Liability Language: Tier 2 Peer Inference

**Status:** Draft for Legal Review  
**Date:** 2026-07-26  
**Reviewed by:** [Legal team to sign off]

---

## TOS Update: Tier 2 Inferred Context

**Add to Terms of Service — Financial Context Section:**

---

### Tier 2 (Regional Context — Inferred)

**What Tier 2 shows:**

For organizations where we do not have direct revenue data, we display inferred financial context based on statistically similar organizations in the same region and nonprofit category.

**Example of Tier 2 display:**

> "Although we don't have revenue data for this organization, nonprofits in this group [category + state + funding model] typically carry 2.1 months of operating reserves."

**What this is NOT:**

- ❌ Actual financial data about this specific organization
- ❌ A prediction of this organization's financial health
- ❌ A professional financial assessment or audit
- ❌ A recommendation to donate or not donate
- ❌ Verified financial information from the organization itself

**What this IS:**

- ✅ Statistical inference based on peer group data
- ✅ A starting point for conversation with the organization
- ✅ Publicly available information from IRS Form 990 filings
- ✅ Explicitly labeled as "inferred" (with badge)
- ✅ Includes margin of error and confidence level

**Limitations you should know:**

1. **Data lag:** 990 filings are typically 1–2 years old
2. **Peer variation:** Individual organizations may differ significantly from peer group median
3. **Incomplete coverage:** Some nonprofit categories or regions have smaller sample sizes (lower confidence)
4. **Self-selection bias:** Organizations filing complete 990s may differ from non-filers

**Margin of error:**

Inference confidence ranges from "Good" (±10–15% margin) to "Moderate" (±20% margin). The specific margin for each organization's peer group is displayed in the methodology section.

**What to do with Tier 2 context:**

1. Use it as a conversation starter: "Most similar orgs maintain 2.1 months reserves. What's your practice?"
2. Cross-reference with other sources: their website, annual report, direct inquiry
3. Verify critical claims directly with the organization
4. Do not rely solely on inferred context for major funding decisions

---

## Privacy Policy Update

**Add to Privacy Policy — Data Sources Section:**

---

### How We Calculate Financial Context

**Tier 1 (Direct):** For organizations with filed Form 990 data, we display their actual reported financial metrics (revenue, reserves, expenses).

**Tier 2 (Inferred):** For organizations without filed 990 data available to us, we calculate inferred financial context by:

1. Identifying peer group (same nonprofit subcategory + state + funding model)
2. Analyzing median financial metrics of peers with available 990 data
3. Displaying peer statistics with explicit inference label

**No personal data is used in inference.** We analyze only:
- IRS Form 990 public data
- NCCS publicly available governance data
- NTEE nonprofit category codes (public)
- State location (public)
- Archetype classification based on public data

**Your data is never shared with peers.** Organizations do not see each other's names or identifying information — only aggregate median statistics.

---

## Liability Disclaimers

### In-Product Disclaimer (Tier 2 Display)

Display on every Tier 2 org detail page:

```
ⓘ This organization's financial context is inferred from similar 
organizations in the same region and category. It is not the 
organization's actual financial data. 

Inferred data should not be the sole basis for funding decisions. 
We recommend contacting the organization directly to verify.

Peer group: X organizations | Confidence: Good (±10% margin)
Data sources: IRS Form 990 (2019-2023), NCCS
Last updated: [date]

[Learn More about Tier 2 Inference →]
```

### Help Center / FAQ

**Q: Is Tier 2 data reliable?**

A: Tier 2 inference is statistically sound when based on peer groups with ≥5 organizations with revenue data. However, it represents **typical practices**, not this specific organization's actual data. Individual organizations may differ significantly from the peer median.

Use Tier 2 as a starting point for due diligence, not as final verification.

**Q: Why don't you have this org's actual financial data?**

A: Organizations may not have filed a Form 990 with the IRS yet, or their filing may not be indexed in public databases. Small organizations may file simplified 990-N filings that don't include financial detail.

**Q: Can I contact the org to get Tier 1 data?**

A: Yes. Any organization can claim their profile and provide verified financial data. [Claim Your Organization →]

**Q: What if the inferred data seems wrong?**

A: Report data quality concerns via our [Mistake Registry](https://daanaa.org/mistakes). Include your concern and we'll investigate.

---

## Liability Risk Assessment

### Risk 1: Donor acts on inferred data and org underperforms
**Severity:** Medium  
**Mitigation:** Clear "inferred" badge + disclaimer + confidence interval  
**Liability:** Low (user is explicitly told data is inferred, not actual)

### Risk 2: Organization claims misrepresentation
**Severity:** Low  
**Mitigation:** Explicit disclaimer + methodology documentation + peer group definition shown to org  
**Liability:** Very Low (we're showing peer group stats, not making claims about the org)

### Risk 3: Inference methodology has systematic bias
**Severity:** Medium  
**Mitigation:** Documented methodology + board review + donor testing + public transparency  
**Liability:** Low (methodology is explainable and reproducible)

### Risk 4: Legal challenge to inference validity
**Severity:** Low  
**Mitigation:** Peer inference is well-established statistical practice; methodology is sound  
**Liability:** Very Low (follows standard practices in nonprofit analytics)

---

## Recommended Legal Actions

1. **TOS Review:** Legal team reviews inference language above
2. **Privacy Policy Review:** Confirm data handling aligns with privacy commitments
3. **Disclaimer Sign-Off:** Approve in-product disclaimer language
4. **Data Classification:** Confirm Tier 2 data classified as "derived public data" per [PRIVACY-INVARIANTS.md](https://daanaa.org/docs/PRIVACY-INVARIANTS.md)
5. **Insurance Notification:** Notify errors & omissions insurance provider of inference feature (informational)

---

## Stewardship Alignment

**Principle 3 (Evidence-based):** ✅  
Inference is based on actual peer 990 data (evidence), not assumptions. Limitations are explicit.

**Principle 9 (Explainable):** ✅  
Methodology is fully documented. Donors see peer group definition, confidence level, data sources.

**Principle 6 (Mistakes corrected):** ✅  
Inference logic is algorithmic and reproducible. If errors found, they can be fixed in next scoring run.

---

## Sign-Off

- **Legal Review:** [Pending]
- **Compliance:** [Pending]
- **Board Approval:** ✅ Stewardship Board approved (2026-07-26)

---

**Next:** Legal team review and sign-off on disclaimers.

