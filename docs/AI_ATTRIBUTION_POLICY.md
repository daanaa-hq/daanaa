# AI Attribution Policy: Trust Through Transparency

**Principle:** Stewardship #3 (Trust signals = evidence-based, honestly stated) + Principle #10 (AI is a tool, not replacement for responsibility)

**Rule:** Every piece of content discloses what's AI-generated, what's human-verified, and what's sourced from public data.

---

## Where AI Gets Attribution

### **Research Articles**

```markdown
---
title: "The State of U.S. Nonprofits 2026"
ai_generated: "Analysis framework, narrative structure, chart interpretations"
human_verified: "Data sourcing, statistical claims, quoted insights, confidence levels"
sources: "IRS Form 990, ProPublica API, Daanaa database queries"
reviewed_by: "[Founder name or team member]"
---

[Article content...]

---

## About This Article

**Data sources:** IRS Form 990 (public record), ProPublica Nonprofit Explorer, Daanaa analysis

**How it was made:**
- Data: Queried from our 1.7M nonprofit database (human-curated, IRS-sourced)
- Analysis framework: AI-assisted (identified trends, structured findings)
- Narrative: AI-generated initial draft, human-reviewed and edited for accuracy
- Charts: AI-generated from data queries, verified for correctness
- Confidence levels: Human-assigned based on data completeness

**What you can trust:**
- ✅ All statistics verified against source data
- ✅ All claims grounded in public IRS records
- ✅ Confidence levels honestly assessed
- ✅ Limitations clearly stated
- ✅ All human-edited for clarity

**What's less certain:**
- ⚠️ Trend interpretations are analytical hypotheses, not facts
- ⚠️ Causal claims ("X caused Y") require further investigation
- ⚠️ Sector-specific context may miss local nuances

**Methodology:** [Link to detailed methodology document]

**Questions?** hello@daanaa.org
```

---

### **Monthly Pipeline Reports**

```markdown
---
title: "What Changed This Month: July 2026 Nonprofit Sector Update"
report_type: "AI-assisted data summary with human review"
ai_components: "New org detection, trend calculation, narrative generation"
human_components: "Data validation, CTA strategy, sector context"
data_sources: "IRS Form 990 ingestion, Daanaa overnight pipeline output"
reviewed_by: "[Human name], [Date]"
---

[Report content...]

---

## How This Report Was Made

**Data processing (automated):**
1. IRS 990 filings ingested and parsed
2. New org detection: EINs not in previous month's snapshot (automated)
3. Financial metrics calculated: reserves, margin, peer rank (automated)
4. Trends computed: month-over-month changes (automated)

**Report generation (AI-assisted, human-reviewed):**
- Initial narrative drafted from data (AI)
- Sector context verified (human)
- Confidence levels assigned (human)
- CTAs strategy validated (human)
- Final copy edited for clarity (human)

**What's reliable here:**
- ✅ New org count: verified from database queries
- ✅ Financial metrics: calculated directly from IRS data
- ✅ Trend direction: confirmed by peer group analysis
- ✅ Geographic distribution: aggregated from org records

**What's interpretation:**
- ⚠️ "What it means" sections are analysis, not fact
- ⚠️ Causal claims need deeper investigation
- ⚠️ Predictions are trend extrapolations, not forecasts

**Transparency:**
- Data sources: IRS (public), Daanaa database (our own)
- Methodology: Peer-group benchmarking (NTEE + revenue band, N≥20)
- Limitations: See data quality section above
- Last verified: [Date]

**Questions about this report?** hello@daanaa.org
```

---

### **Sector Deep-Dives & Analysis**

```markdown
---
title: "Food Banking in Crisis: What 47,000 Nonprofits Tell Us"
ai_role: "Pattern detection, data visualization, narrative framing"
human_role: "Research question, validation, interpretation, recommendation"
data_sources: "IRS 990s (N=47,382), Daanaa financial analysis, sector research"
human_author: "[Name/role]"
reviewed_by: "[Name/role]"
confidence: "80% (well-measured IRS data, limited outcome metrics)"
---

[Article content...]

---

## Research Methodology

**AI assistance in this analysis:**
- Identified financial health patterns across 47K food nonprofits
- Generated initial visualizations of reserve trends
- Drafted narrative interpretations of data clusters
- Suggested causal hypotheses (flagged for human verification)

**Human work in this analysis:**
- Defined research question ("Why are food bank reserves declining?")
- Validated AI-generated patterns against raw data
- Assigned confidence levels based on data completeness
- Verified causal claims against external research
- Edited narrative for accuracy and fairness

**What's data (high confidence):**
- Reserve ratios, revenue trends, org counts: ✅ Direct from IRS 990s
- Geographic distribution, sector size: ✅ Well-measured in IRS data

**What's analysis (medium-high confidence):**
- Trend direction (reserves down): ✅ Confirmed across peer groups
- Sector viability (food banking pressured): ✅ Supported by multiple metrics

**What's interpretation (medium confidence):**
- "Why" claims (e.g., "demand outpacing funding"): ⚠️ Plausible but needs external validation
- Causal statements: ⚠️ IRS data shows correlation, not causation

**What's NOT in this analysis:**
- Mission impact (can't measure from financial data)
- Individual org quality (only financial health)
- Outcome metrics (not reported in IRS 990)

**How you can verify:**
1. Download the raw 990 data from ProPublica
2. Filter to NTEE-I (Food, Agriculture, Nutrition)
3. Calculate reserve ratios yourself
4. Compare your findings to ours

---

## Sources & Transparency

[Full citations, methodological notes, confidence intervals]
```

---

### **Nonprofit Mission Statements**

**When AI-generated:**

```markdown
**About [Nonprofit Name]**

Mission: [AI-generated mission statement from 990 filing analysis]

**How we got this:**
- IRS Form 990 review (human-read)
- AI-assisted synthesis of stated activities into mission statement
- Not verified by the organization

**Better:** [Link to "Claim your profile" so org can provide their own mission]

---

*Is this mission wrong? [Report it] | Want to update it? [Claim your profile]*
```

**When organization-provided:**

```markdown
**About [Nonprofit Name]**

Mission: [Organization's stated mission from claimed profile]

**How we got this:**
- Provided by the organization themselves (verified email)
- Human-curated for clarity

[Report corrections | Update your profile]
```

---

## Clear Labeling Guidelines

### **In Article Headers**

```markdown
# [Title]

**Data source:** IRS Form 990  
**Analysis:** AI-assisted with human review  
**Confidence:** 85% (well-measured data)  
**Last verified:** [Date]  
**Author:** [Human] with AI assistance
```

### **In Charts/Visualizations**

```
[Chart title]
Generated from IRS Form 990 data (N=47,382 organizations)
Trend analysis: AI-detected, human-verified
Interpretation: See article for analysis and caveats
```

### **In Text**

**When citing AI-generated analysis:**
> "Our AI-assisted analysis of 47K food nonprofits found [X]. This pattern is statistically significant, though the cause is not clear from financial data alone."

**When presenting human-verified findings:**
> "IRS data clearly shows food bank reserves declining 5% month-over-month. This is a measurable fact, not interpretation."

**When uncertain:**
> "Food banks may be struggling due to increased demand outpacing funding (plausible hypothesis supported by reserves decline, but not proven by financial data alone)."

---

## Why This Matters (Stewardship #3 & #10)

**Stewardship #3:** "Trust signals must be evidence-based and honestly stated"
- By disclosing AI use, we're honest about our methods
- By showing what's verified vs. analysis, we let users judge credibility
- By linking to sources, we let users verify claims themselves

**Stewardship #10:** "AI is a tool, not a replacement for responsibility"
- We're responsible for AI-generated analysis; clear attribution shows that
- Humans verify important claims; we disclose when we haven't
- Transparency builds trust more than hiding the process

---

## Implementation Checklist

For every article/report:
- [ ] Disclose AI role (what did AI do?)
- [ ] Disclose human role (what did humans verify?)
- [ ] Link to data sources (let readers verify)
- [ ] Assign confidence level (how sure are we?)
- [ ] Note limitations (what can't we measure?)
- [ ] Provide feedback mechanism (help us improve)

For AI-generated mission statements:
- [ ] Mark as "AI-generated from 990 review"
- [ ] Link to "Claim your profile" CTA
- [ ] Show discrepancy if org has provided their own

For visualizations:
- [ ] Source data clearly labeled
- [ ] Method of generation noted
- [ ] Interpretation guidance provided

---

## Example: Full Article Footer

```
---

## About This Article

**Data sources:** IRS Form 990 (1.7M orgs), ProPublica API, Daanaa database

**How we made it:**
- Data queries: Automated database queries on verified IRS data ✅
- Statistical analysis: AI-detected patterns, human-verified ✅
- Narrative: AI-drafted, human-reviewed for accuracy ✅
- Visualizations: AI-generated charts, verified for correctness ✅
- Recommendations: Human judgment based on data ✅

**Confidence levels:**
- Financial metrics (reserves, margin): 95% confident (direct from 990)
- Trend direction (declining/growing): 85% confident (multi-year pattern)
- Sector interpretation ("Why"): 70% confident (limited to financial data)

**Limitations:**
- IRS data is 2 months old (lag in filing)
- Can't measure mission impact from financials alone
- Small orgs file simplified returns (less detail)
- No outcome data available in public records

**Verify yourself:**
1. IRS Form 990 data: [ProPublica link]
2. Our methodology: [Link to detailed methodology]
3. Raw data download: [CSV/JSON]

**Questions?** [Email] | **Found an error?** [Report it] | **Have data to share?** [Contact us]

---

*Daanaa is built on transparent use of public data and honest disclosure of methods. We use AI to analyze data faster, not to hide how we work.*
```

---

## The Why

Daanaa's competitive advantage is **trust**. We earn that trust by:
1. Using only public data (no hidden sources)
2. Showing our work (disclosing AI use, not hiding it)
3. Admitting limits (what we don't know)
4. Letting users verify claims (sources + methodology)

Hiding AI use would destroy that trust. Disclosing it honestly deepens it.
