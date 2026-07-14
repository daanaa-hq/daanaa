# Daanaa LinkedIn Carousel System

**Status:** Format complete and ready to populate with data.  
**Goal:** Build a 20-carousel library of nonprofit investigations.

---

## What This System Is

A modular, reusable format for creating **investigative nonprofit carousels** in the style of Johnny Harris:
- **Memorable** — signature visual design (navy + gold, bold stats, clean layout)
- **Readable** — high-contrast typography, scannable hierarchy
- **Simple** — no clutter, only intentional design
- **Modular** — same 6-slide structure works for all topics

Once you write the narrative, rendering takes seconds. All carousels look professional and on-brand.

---

## The Three-Document System

### 1. CAROUSEL_DESIGN_SYSTEM.md
**Visual identity.** Read this to understand the look and feel.

- Color palette (navy + gold + cream)
- Typography (Cormorant Garamond + DM Sans)
- 6-slide structure with visual purpose
- Signature accents (circles on content, squares on CTA)
- Do's and don'ts

**Outcome:** Every carousel looks unmistakably Daanaa.

### 2. CAROUSEL_CONTENT_TEMPLATE.md
**Writing guide.** Read this to understand how to structure narratives.

- Field-by-field guidelines (headline, stat, label, story, source)
- Real example: "The Reserve Crisis"
- Testing checklist
- 20-topic backlog

**Outcome:** You can write a carousel narrative in 30 minutes.

### 3. CAROUSEL_JOHNNY_HARRIS_GUIDE.md
**Narrative framework.** Read this to understand investigative voice.

- Hook → Investigation → Gap → Discovery → Stakes → Call
- Tone rules (specific, human, surprising, sourced)
- Before/after rewrites showing generic → impactful
- Testing questions

**Outcome:** Your carousel lands emotionally and intellectually.

---

## How to Build a Carousel

### Step 1: Choose a Topic
Pick from the 20-topic backlog in CAROUSEL_CONTENT_TEMPLATE.md.

Example topics ready to go:
- Reserve Crisis ✓ (done)
- Invisible Nonprofits
- Funding Paradox ✓ (done)
- Small Org Advantage
- Leadership Turnover Crisis
- Endowment Myths
- Geographic Equity

### Step 2: Research & Structure
Gather data for your topic:
- 1 founding stat (the hook)
- 2-3 context stats (for content slides)
- 1 memorable insight (the stakes)

Structure as:
```
Hook stat + Question
↓
Data foundation (why this stat matters)
↓
Who's affected (the gap, the victims)
↓
The opportunity (discovery or solution)
↓
One memorable takeaway
↓
Action aligned with mission
```

See CAROUSEL_JOHNNY_HARRIS_GUIDE.md for examples.

### Step 3: Write the Narrative
Fill this JSON template (save as `carousels/sample_YOUR_TOPIC.json`):

```json
{
  "carousel_type": "sector_insight",
  "title": "Your Topic Name",
  "slides": [
    {
      "slide_type": "cover",
      "headline": "[HOOK QUESTION - 5-12 WORDS]",
      "subheadline": "[CONTEXT - 1 SENTENCE]"
    },
    {
      "slide_type": "content",
      "label": "Part 1: The Data",
      "headline": "[CLEAR TITLE - 2-6 WORDS]",
      "accent_stat": "[KEY NUMBER - 2-4 CHARS]",
      "accent_label": "[STAT MEANING - 1-2 LINES]",
      "story": "[CONTEXT + CONSEQUENCE - 2-3 SENTENCES]",
      "source": "[DATA ATTRIBUTION]"
    },
    {
      "slide_type": "content",
      "label": "Part 2: [THEME]",
      "headline": "[WHO'S AFFECTED - 2-6 WORDS]",
      "accent_stat": "[KEY NUMBER]",
      "accent_label": "[STAT MEANING]",
      "story": "[NARRATIVE + IMPACT - 2-3 SENTENCES]",
      "source": "[DATA ATTRIBUTION]"
    },
    {
      "slide_type": "content",
      "label": "Part 3: [RESOLUTION]",
      "headline": "[THE ANSWER - 2-6 WORDS]",
      "accent_stat": "[KEY NUMBER]",
      "accent_label": "[STAT MEANING]",
      "story": "[WHAT IT UNLOCKS - 2-3 SENTENCES]",
      "source": "[DATA ATTRIBUTION]"
    },
    {
      "slide_type": "content",
      "label": "Key Insight",
      "headline": "[WHAT THIS MEANS FOR SECTOR - 2-6 WORDS]",
      "accent_stat": "[MEMORABLE RATIO]",
      "accent_label": "[TAKEAWAY - SHORT, BOLD]",
      "story": "[EXPANDED INSIGHT - 2 SENTENCES]",
      "source": "[DATA ATTRIBUTION]"
    },
    {
      "slide_type": "cta",
      "headline": "[ACTION-ORIENTED - 3-8 WORDS]",
      "body_lines": [
        "[BENEFIT 1 - 1 LINE]",
        "[BENEFIT 2 - 1 LINE]"
      ]
    }
  ]
}
```

**Writing tips:**
- Keep headlines SHORT (2-6 words, fit on 1-2 lines)
- Every stat is SOURCED and DATED
- Tone is SPECIFIC, HUMAN, SURPRISING (see Johnny Harris guide)
- Stories are 2-3 sentences max (~50-80 words)

### Step 4: Render
```bash
cd /home/akbar/meritgiving
source venv/bin/activate

# Single carousel
python3 scripts/linkedin/render_carousel_from_json.py carousels/sample_YOUR_TOPIC.json

# Batch: all carousels in folder
python3 scripts/linkedin/render_carousel_from_json.py carousels/*.json
```

Output: `output/daanaa_{type}_{timestamp}.pdf`

### Step 5: Review
- Open the PDF
- Check readability (contrast, hierarchy, white space)
- Verify headlines fit (no overflow)
- Check stats are visible (big numbers, clear label)
- Verify footer URL and slide counter

### Step 6: Publish (Later)
When carousels are final:
```bash
# Post to LinkedIn
python3 scripts/linkedin/post_carousel.py --type sector_insight --use-existing
```

---

## Current Status

### ✓ Complete (Format)
- Signature design system
- Content template with examples
- Johnny Harris investigative narrative guide
- Rendering pipeline (JSON → PDF)

### Sample Carousels Rendered (as reference)
1. `daanaa_sector_insight_[ts].pdf` — Reserve Crisis
2. `daanaa_hidden_gems_[ts].pdf` — Invisible Nonprofits
3. `daanaa_sector_insight_[ts].pdf` — Funding Paradox

### Ready to Build (Topics with Data)
1. Small Org Advantage (efficiency benchmarking exists)
2. Executive Transition Crisis (Guidestar turnover data)
3. Endowment Myths (IRS 990 endowment field)
4. Geographic Equity (regional funding analysis)
5. Revenue Diversity (funding source concentration)
6. Sector Health Index (aggregate financial health)
7. Rural Nonprofit Crisis (location-based analysis)
8. Nonprofit Mergers (consolidation trends)
9. Tech Adoption Gap (web/digital footprint)
10. Board Problem (governance + financial health correlation)

---

## Quality Checklist

Before publishing, every carousel should pass:

- [ ] **Hook Test:** Slide 1 makes you want to swipe
- [ ] **Arc Test:** All 6 slides feel like one story
- [ ] **Tone Test:** Voice is specific, human, surprising
- [ ] **Source Test:** Every claim is sourced with year
- [ ] **Readability Test:** All type is readable (no overflow)
- [ ] **Visual Test:** Stat boxes are prominent, hierarchy is clear
- [ ] **Engagement Test:** CTA is specific, benefit-forward

---

## Timeline

**This Week:**
- ✓ Format locked (design + narrative + template)
- ✓ 3 sample carousels rendered
- → Review and refine design based on feedback

**Next Week:**
- Build 3-5 more carousels using template
- Test LinkedIn posting pipeline
- Measure engagement (saves, shares, clicks)
- Refine narrative based on what resonates

**Month 1:**
- Complete 20-carousel library
- Launch weekly carousel cadence (Mondays 9am ET)
- Monitor metrics, iterate on topics/tone
- Prepare for media outreach

---

## Data Sources (Already Available)

### Financial Health Data
- IRS 990 SOI (1.7M org baseline)
- Daanaa peer-ranking analysis
- Reserve % calculations (month of runway)

### Funding Data
- ProPublica 990 extracts (revenue trends)
- Regional funding disparity (state-level analysis)
- Cause-area funding concentration

### Demographic Data
- Rural vs urban org distribution
- Organization size distribution (revenue bands)
- Sector composition (NTEE groups)

### Operational Data
- Website adoption % (by size, region, cause)
- Donation link discovery rates
- Leadership turnover indicators (job postings)

All of this is already in the Daanaa database. No external APIs needed.

---

## Next: Run the Workflow

**To build your first carousel:**

1. Read CAROUSEL_JOHNNY_HARRIS_GUIDE.md (15 min)
2. Pick a topic from the 20-topic backlog
3. Gather 5-7 data points from Daanaa analysis
4. Write the 6-slide narrative (JSON format)
5. Run `render_carousel_from_json.py`
6. Review PDF
7. Iterate on wording/tone
8. Mark as final when it passes quality checklist

**Question?** See the docs. Every scenario is covered.

