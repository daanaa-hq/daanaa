# Daanaa Carousel Data Format

Clean JSON schema for carousel creation. Define once, plug data in, render guaranteed.

---

## Structure

```json
{
  "carousel_type": "sector_insight|hidden_gems|how_it_works|myth_bust|feature_launch",
  "title": "Human-readable carousel title",
  "description": "What this carousel is about",
  "cta_text": "Call to action (e.g., 'Explore daanaa.org')",
  "slides": [
    {
      "slide_type": "cover|content|cta",
      // slide-specific fields...
    }
  ]
}
```

---

## Slide Types

### Cover Slide (Title Slide)
```json
{
  "slide_type": "cover",
  "headline": "Main title (short, impactful)",
  "subheadline": "Supporting tagline or context"
}
```

**Example:**
```json
{
  "slide_type": "cover",
  "headline": "Nonprofit Sector's Financial Health Insights",
  "subheadline": "Understanding the emergency reserves landscape across the nonprofit sector."
}
```

---

### Content Slide (Data + Story + Source)
```json
{
  "slide_type": "content",
  "label": "Section heading (UPPERCASE)",
  "headline": "Slide title",
  "accent_stat": "Number or percentage (e.g., '48%')",
  "accent_label": "Label below the stat",
  "story": "The narrative (2-3 sentences. What does this data mean for donors/leaders?)",
  "source": "Data source attribution (e.g., 'IRS 990 Filings, 2023')"
}
```

**Example:**
```json
{
  "slide_type": "content",
  "label": "Overview",
  "headline": "Reserve Funding Crisis in U.S. Nonprofits",
  "accent_stat": "48%",
  "accent_label": "Nonprofits Lacking Adequate Reserves",
  "body": "Nearly half of nonprofits lack adequate emergency reserves. Data from IRS 990 filings reveals this critical financial vulnerability across the sector."
}
```

**Rules:**
- `accent_stat`: Just the number/percentage (e.g., "48%", "33,900+", "$500K")
- `accent_label`: Short label (e.g., "Nonprofits Lacking Reserves")
- `body`: 2-3 sentences max. Professional tone. No jargon. Donor-friendly language.
- NO HTML TAGS anywhere

---

### CTA Slide (Call to Action - Final Slide)
```json
{
  "slide_type": "cta",
  "headline": "Closing headline",
  "body_lines": [
    "Action line 1",
    "Action line 2"
  ]
}
```

**Example:**
```json
{
  "slide_type": "cta",
  "headline": "Secure Nonprofit Financial Health",
  "body_lines": [
    "Support emergency savings.",
    "Prioritize long-term sustainability."
  ]
}
```

---

## Sample Complete Carousel (Reserve Crisis - Sector Insight)

```json
{
  "carousel_type": "sector_insight",
  "title": "Reserve Funding Crisis in U.S. Nonprofits",
  "description": "Financial stability matters. 48% of nonprofits lack adequate emergency reserves.",
  "cta_text": "daanaa.org",
  "slides": [
    {
      "slide_type": "cover",
      "headline": "Nonprofit Sector's Financial Health Insights",
      "subheadline": "Understanding the emergency reserves landscape across the nonprofit sector."
    },
    {
      "slide_type": "content",
      "label": "Overview",
      "headline": "Reserve Funding Crisis in U.S. Nonprofits",
      "accent_stat": "48%",
      "accent_label": "Nonprofits Lacking Adequate Reserves",
      "body": "Nearly half of nonprofits lack adequate emergency reserves. Data from IRS 990 filings reveals this critical financial vulnerability across the sector."
    },
    {
      "slide_type": "content",
      "label": "General Sector",
      "headline": "Emergency Funding Trends",
      "accent_stat": "40%",
      "accent_label": "Nonprofits with Less Than 3 Months of Operating Funds",
      "body": "Approximately 40% of nonprofits have fewer than 3 months of emergency funds. This underscores the financial fragility of the sector."
    },
    {
      "slide_type": "content",
      "label": "Small Organizations",
      "headline": "Small Nonprofits and Financial Reserves",
      "accent_stat": "$500K",
      "accent_label": "Annual Funding Threshold",
      "body": "Organizations with less than $500K in annual funding are more likely to have lean reserves, often reinvesting directly into programs."
    },
    {
      "slide_type": "content",
      "label": "Data Source",
      "headline": "Public IRS 990 Filings",
      "accent_stat": "",
      "accent_label": "",
      "body": "This data is derived from public IRS 990 filings, providing a comprehensive view of financial health across the sector."
    },
    {
      "slide_type": "content",
      "label": "Leadership Perspective",
      "headline": "Financial Stability for Nonprofit Leaders",
      "accent_stat": "",
      "accent_label": "",
      "body": "Nonprofit leaders must prioritize building and maintaining emergency reserves to ensure long-term sustainability and program delivery."
    },
    {
      "slide_type": "content",
      "label": "Funding Role",
      "headline": "Role of Funders in Financial Health",
      "accent_stat": "",
      "accent_label": "",
      "body": "Funders play a crucial role by supporting nonprofits in building their reserves, ensuring they can weather financial storms and continue their missions."
    },
    {
      "slide_type": "cta",
      "headline": "Secure Nonprofit Financial Health",
      "body_lines": [
        "Support emergency savings.",
        "Prioritize long-term sustainability."
      ]
    }
  ]
}
```

---

## How to Use This Format

1. **Create the JSON file** with carousel data (one file per carousel)
2. **Validate** the JSON structure
3. **Pass to renderer** (modified carousel_generator.py to read JSON instead of LLM output)
4. **Render to PDF** (guaranteed perfect formatting every time)
5. **Post to LinkedIn** (with post_carousel.py)

---

## Validation Checklist

Before rendering, verify:
- [ ] All slides have required fields for their type
- [ ] NO HTML tags anywhere (`<i>`, `<b>`, etc.)
- [ ] `accent_stat` is just the number (e.g., "48%", not "48% of nonprofits")
- [ ] `body` text is 2-3 sentences max
- [ ] Language is professional, donor-friendly (no jargon)
- [ ] Numbers are accurate and from verified sources
- [ ] CTA slide is last slide

---

## Next Steps

1. Create 3 JSON files (Sample 1, 2, 3) with verified data
2. Modify carousel_generator.py to read JSON files instead of LLM output
3. Render all 3 perfectly
4. Post to LinkedIn
5. Scale to 20 carousels (create 17 more JSON files, render in batch)
