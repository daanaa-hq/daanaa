# Daanaa Carousel Content Template

**Modular format for building 6-slide carousels.**  
Fill in the template below, save as JSON, render with `render_carousel_from_json.py`.

---

## Template Structure

```json
{
  "carousel_type": "sector_insight",
  "title": "[TOPIC NAME]",
  "slides": [
    {
      "slide_type": "cover",
      "headline": "[HOOK QUESTION OR BOLD CLAIM]",
      "subheadline": "[BRIEF CONTEXT - 1 SENTENCE]"
    },
    {
      "slide_type": "content",
      "label": "Part 1: The Data",
      "headline": "[CLEAR, SPECIFIC TITLE]",
      "accent_stat": "[KEY NUMBER - 2-4 CHARS MAX]",
      "accent_label": "[STAT DESCRIPTION - 1 LINE]",
      "story": "[CONTEXT + CONSEQUENCE - 2-3 SENTENCES]",
      "source": "[DATA ATTRIBUTION]"
    },
    {
      "slide_type": "content",
      "label": "Part 2: [THEME]",
      "headline": "[WHO IS AFFECTED]",
      "accent_stat": "[KEY NUMBER]",
      "accent_label": "[STAT MEANING]",
      "story": "[NARRATIVE + IMPACT - 2-3 SENTENCES]",
      "source": "[DATA ATTRIBUTION]"
    },
    {
      "slide_type": "content",
      "label": "Part 3: [RESOLUTION/OPPORTUNITY]",
      "headline": "[THE SOLUTION OR SILVER LINING]",
      "accent_stat": "[KEY NUMBER]",
      "accent_label": "[STAT MEANING]",
      "story": "[WHAT THIS ENABLES - 2-3 SENTENCES]",
      "source": "[DATA ATTRIBUTION]"
    },
    {
      "slide_type": "content",
      "label": "Key Insight",
      "headline": "[HEADLINE: WHAT THIS MEANS FOR THE SECTOR]",
      "accent_stat": "[MEMORABLE RATIO OR COMPARISON]",
      "accent_label": "[TAKEAWAY - SHORT, BOLD]",
      "story": "[EXPANDED INSIGHT - 2 SENTENCES]",
      "source": "[DATA ATTRIBUTION]"
    },
    {
      "slide_type": "cta",
      "headline": "[ACTION-ORIENTED INVITATION]",
      "body_lines": [
        "[BENEFIT 1 - 1 LINE]",
        "[BENEFIT 2 - 1 LINE]"
      ]
    }
  ]
}
```

---

## Field-by-Field Guidelines

### COVER SLIDE (Slide 1)

**headline** (Required)
- Length: 5-12 words
- Tone: Provocative, surprising, or question-form
- Purpose: Stop the scroll
- Examples:
  - ✓ "Nearly Half Can't Survive a Funding Gap"
  - ✓ "40% of Nonprofits Are Invisible to Donors"
  - ✓ "The Funding Paradox: More Nonprofits, Less Money"

**subheadline** (Required)
- Length: 1 sentence, 10-20 words
- Tone: Matter-of-fact, grounding
- Purpose: Set context without explanation
- Examples:
  - ✓ "The reserve crisis affecting 1.7M nonprofits"
  - ✓ "Why small organizations are overlooked"
  - ✓ "How the sector is fragmenting under growth"

---

### CONTENT SLIDES (Slides 2-5)

**label** (Required)
- Format: "Part X: [THEME]" or "Key Insight"
- Length: 3-5 words
- Purpose: Signal what section user is in
- Examples:
  - "Part 1: The Data"
  - "Part 2: Who's Vulnerable"
  - "Part 3: The Multiplier"
  - "Key Insight"

**headline** (Required)
- Length: 2-6 words (fit on 1-2 lines)
- Tone: Direct, clear, actionable
- Purpose: Main idea of this slide
- Examples:
  - ✓ "Small Orgs Have Zero Cushion"
  - ✓ "Reserve Stability = Impact Multiplier"
  - ✗ "The reasons why organizations struggle with lack of adequate organizational financial reserves"

**accent_stat** (Required)
- Format: Number + symbol (%, $, words) | Max 4 characters
- Examples:
  - "48%" — percentage
  - "6 months" — duration
  - "$2B" — money
  - "1 in 3" — ratio
  - "2.3x" — multiplier
- Rule: ALWAYS fit in 108pt (big number on slide)

**accent_label** (Required)
- Length: 1-2 lines, 5-15 words
- Purpose: Explain what the stat means
- Tone: Specific, human-focused
- Examples:
  - ✓ "Nonprofits Without Adequate Reserves"
  - ✓ "Enables Long-Term Planning, Growth, Stability"
  - ✗ "The percentage of nonprofits that have a number of reserves" (too vague, too long)

**story** (Required)
- Length: 2-3 sentences (~50-80 words)
- Structure: [STAT MEANING] + [REAL-WORLD IMPACT] + [SO WHAT?]
- Tone: Conversational, grounded in reality
- Example:
  ```
  When a major grant ends or a funder withdraws, nonprofits 
  without reserves cannot survive the gap. Programs shut down. 
  Staff are laid off. Communities suffer. This isn't speculation—
  it's the reality for nearly half the sector.
  ```

**source** (Required)
- Format: "[DATA SOURCE], [YEAR]" or "[ORGANIZATION], [YEAR]"
- Purpose: Trustworthiness (Principle #3: Evidence-based)
- Examples:
  - "IRS 990 Filings, 1.7M active U.S. nonprofits"
  - "Daanaa financial health analysis, 2024"
  - "FSG nonprofit management research, 2023"
- Rule: ALWAYS cite the data source (never unsourced claims)

---

### CTA SLIDE (Slide 6)

**headline** (Required)
- Length: 3-8 words
- Tone: Action-oriented, benefit-forward
- Purpose: What user should do
- Examples:
  - ✓ "See Which Nonprofits Need Reserves Most"
  - ✓ "Find the Hidden Gems in Your Sector"
  - ✗ "Click Here" (no benefit stated)

**body_lines** (Required)
- Count: Exactly 2 lines
- Length: Each 8-15 words (fit on 1 line)
- Purpose: State concrete benefit
- Examples:
  ```
  [
    "Explore financial health data for 1.7M nonprofits.",
    "Make informed funding decisions."
  ]
  ```

---

## Content Strategy: The Three-Act Structure

Every 3-slide content sequence follows:

### Part 1: The Data
**Goal:** Surface the number that stops the scroll.  
**Pattern:** [BIG STAT] + [What it means] + [General impact]
```
48%
Nonprofits Without Adequate Reserves

When a major grant ends or funder withdraws, nonprofits 
without reserves cannot survive the gap. Programs shut down. 
Staff are laid off.
```

### Part 2: Who's Affected
**Goal:** Make it human, not abstract.  
**Pattern:** [WHO/WHERE] + [STAT] + [Consequence for that group]
```
40%
Nonprofits with Less Than 3 Months of Funds

Organizations under $500K invest every dollar into programs—
admirable, but dangerous. One disruption shuts down services.
```

### Part 3: The Answer/Opportunity
**Goal:** Show a path forward (or explain why this matters).  
**Pattern:** [INSIGHT] + [STAT/RATIO] + [What it unlocks]
```
6 months
Enables Long-Term Planning, Growth, Stability

A nonprofit with 6 months of reserves can weather funding 
storms, plan long-term, and serve their community with 
confidence. Strategic reserve funding is infrastructure investment.
```

---

## Tone & Voice Guidelines

**For Daanaa carousels, adopt this voice:**

✓ **Direct & Specific**
- "40% of small nonprofits have less than 3 months of reserves"
- ✗ "Many nonprofits struggle with financial challenges"

✓ **Human-Centered**
- "Programs shut down. Staff are laid off. Communities suffer."
- ✗ "Financial instability negatively impacts service delivery capacity"

✓ **Data-Grounded**
- Every claim tied to IRS data or published research
- Every stat sourced and dated
- ✗ No speculation or unverified claims

✓ **Active Voice**
- "Donors who use financial data identify strong small nonprofits others miss"
- ✗ "Financial data is used by donors to identify strong nonprofits"

✓ **Conversational, Not Corporate**
- "Here's the catch: average funding per nonprofit declined 3%"
- ✗ "Notably, the average funding allocation per nonprofit has decreased 3% year-over-year"

---

## Real Example: "The Reserve Crisis"

```json
{
  "carousel_type": "sector_insight",
  "title": "The Reserve Crisis",
  "slides": [
    {
      "slide_type": "cover",
      "headline": "Nearly Half Can't Survive a Funding Gap",
      "subheadline": "The reserve crisis affecting 1.7M nonprofits"
    },
    {
      "slide_type": "content",
      "label": "Part 1: The Data",
      "headline": "48% Lack Adequate Emergency Reserves",
      "accent_stat": "48%",
      "accent_label": "Nonprofits Without Adequate Reserves",
      "story": "When a major grant ends or a funder withdraws, nonprofits without reserves cannot survive the gap. Programs shut down. Staff are laid off. Communities suffer. This isn't speculation—it's the reality for nearly half the sector.",
      "source": "IRS 990 Filings, 1.7M active U.S. nonprofits"
    },
    {
      "slide_type": "content",
      "label": "Part 2: Who's Vulnerable",
      "headline": "Small Orgs Have Zero Cushion",
      "accent_stat": "40%",
      "accent_label": "Nonprofits with Less Than 3 Months of Funds",
      "story": "Organizations under $500K in annual funding invest every dollar into programs—admirable, but dangerous. One disruption shuts down services. Small nonprofits are one crisis away from collapse.",
      "source": "Daanaa financial health analysis, 2024"
    },
    {
      "slide_type": "content",
      "label": "Part 3: The Multiplier",
      "headline": "6 Months of Reserves Enables Growth",
      "accent_stat": "6 months",
      "accent_label": "Enables Long-Term Planning, Growth, Stability",
      "story": "A nonprofit with 6 months of reserves can weather funding storms, plan long-term, and serve their community with confidence. Strategic reserve funding isn't charity—it's infrastructure investment.",
      "source": "FSG nonprofit management research, 2023"
    },
    {
      "slide_type": "content",
      "label": "Key Insight",
      "headline": "Reserve Stability = Impact Multiplier",
      "accent_stat": "1 in 3",
      "accent_label": "Nonprofits Could Stabilize with Strategic Funding",
      "story": "Funders who support reserve-building don't just save organizations. They multiply impact by enabling long-term strategy, not just survival.",
      "source": "Daanaa nonprofit analysis"
    },
    {
      "slide_type": "cta",
      "headline": "See Which Nonprofits Need Reserves Most",
      "body_lines": [
        "Explore financial health data for 1.7M nonprofits.",
        "Make informed funding decisions."
      ]
    }
  ]
}
```

---

## Testing Checklist

Before finalizing a carousel, verify:

- [ ] **Headline Test:** Can I understand the main idea by reading only the headlines?
- [ ] **Stat Test:** Are all statistics 2-4 characters (fit in 108pt type)?
- [ ] **Source Test:** Is every claim sourced with year?
- [ ] **Tone Test:** Does copy sound like Daanaa (direct, human, data-grounded)?
- [ ] **Flow Test:** Does it tell a 3-act story (Data → Meaning → Stakes)?
- [ ] **CTA Test:** Is the benefit specific, not generic ("Find hidden gems" not "Learn more")?

---

## Next: Data Library

Ready to populate with carousels? Fill this template for:

1. ✓ Reserve Crisis
2. ✓ Hidden Gems / Funding Paradox
3. Small Org Advantage
4. Executive Transition Crisis
5. Endowment Myths
6. Revenue Diversity
7. Geographic Equity
8. Sector Health Index
9. Rural Nonprofit Crisis
10. Nonprofit Mergers

...and 10 more.

Save each as JSON, render with `render_carousel_from_json.py`, review, and publish.
