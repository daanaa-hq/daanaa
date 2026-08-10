# Daanaa LinkedIn Carousel Format — Complete System

**Status:** ✅ Format locked and ready to populate with data.  
**Built:** July 14, 2026  
**Goal:** 20-carousel library publishing starting Week of July 21  

---

## What's Ready Right Now

### 1. **SIGNATURE VISUAL DESIGN** ✓
The carousel looks unmistakably Daanaa — professional, premium, impossible to confuse with generic SaaS.

**Key elements:**
- Navy + Gold + Cream color palette
- Cormorant Garamond (italic headlines) + DM Sans (body)
- 1080 × 1350px (4:5 LinkedIn portrait)
- Signature accent circles (content) and squares (CTAs)
- Stat boxes with visual hierarchy (108pt gold stats on navy background)
- Premium white space (breathing room, luxury feel)

**Design files:** `docs/CAROUSEL_DESIGN_SYSTEM.md`

### 2. **MODULAR CONTENT TEMPLATE** ✓
Anyone can write a carousel using this structure. No creativity required—just fill in the blanks.

**Template:**
```
Slide 1: COVER (hook question + context)
Slide 2: CONTENT (Part 1: The Data)
Slide 3: CONTENT (Part 2: Who's Vulnerable)
Slide 4: CONTENT (Part 3: The Solution/Multiplier)
Slide 5: CONTENT (Key Insight)
Slide 6: CTA (action + benefits)
```

**Content files:** `docs/CAROUSEL_CONTENT_TEMPLATE.md`

### 3. **INVESTIGATIVE NARRATIVE FRAMEWORK** ✓
Every carousel follows the Johnny Harris narrative arc:

```
Hook
↓
Investigation (data foundation)
↓
Gap (the broken system)
↓
Discovery (counterintuitive insight)
↓
Stakes (why this matters)
↓
Call (action)
```

**Narrative guide:** `docs/CAROUSEL_JOHNNY_HARRIS_GUIDE.md`

### 4. **RENDERING PIPELINE** ✓
**Input:** JSON file with carousel content  
**Output:** Professional PDF ready to post

```bash
python3 scripts/linkedin/render_carousel_from_json.py carousels/sample.json
# → output/daanaa_sector_insight_20260714_143132.pdf (358KB)
```

**No design skills needed.** JSON in → PDF out.

### 5. **COMPLETE DOCUMENTATION** ✓
Four guides covering design, content, narrative, and usage:

1. `docs/CAROUSEL_DESIGN_SYSTEM.md` — Look & feel
2. `docs/CAROUSEL_CONTENT_TEMPLATE.md` — How to write
3. `docs/CAROUSEL_JOHNNY_HARRIS_GUIDE.md` — Narrative voice
4. `scripts/linkedin/README_CAROUSELS.md` — How to use the system

---

## Sample Carousels (Rendered)

Three samples already built as reference:

1. **The Reserve Crisis** (6 slides, 429KB)
   - Hook: "Nearly Half Can't Survive a Funding Gap"
   - Shows 3-act structure perfectly

2. **The Invisible Nonprofits** (5 slides)
   - Hook: "40% of Nonprofits Are Invisible to Donors"
   - Demonstrates how-it-works carousel type

3. **The Funding Paradox** (5 slides)
   - Hook: "More Nonprofits, Less Funding Per Org"
   - Investigative narrative example

**Location:** `scripts/linkedin/output/*.pdf`

---

## The 20-Topic Backlog

Ready to fill with data (already identified with research approach):

### Research Phase (Data available)
1. **Reserve Crisis** ✓ (IRS 990 reserve % analysis)
2. **Invisible Nonprofits** ✓ (Donor visibility scoring)
3. **Funding Paradox** ✓ (1.7M org funding trend)
4. **Small Org Advantage** (Efficiency metrics by size)
5. **Leadership Turnover Crisis** (Executive job postings)
6. **Endowment Myths** (IRS 990 endowment data)
7. **Geographic Equity** (Regional funding analysis)
8. **Revenue Diversity** (Funding source concentration)
9. **Sector Health Index** (Aggregate financial health)
10. **Rural Nonprofit Crisis** (Location-based underfunding)
11. **Nonprofit Mergers** (Consolidation trends)
12. **Tech Adoption Gap** (Website/digital presence)
13. **Board Problem** (Governance + financial correlation)
14. **Volunteer Economy** (Pure volunteer org prevalence)
15. **Program Spend Reality** (Admin overhead myths)
16. **Overhead Myth** (Debunking the 80/20 rule)
17. **Partnership Opportunity** (Collaboration effectiveness)
18. **Data Desert** (Visibility gaps by cause)
19. **Funder Blind Spot** (What foundations miss)
20. **Next Generation** (Young nonprofit success)

---

## How to Build a Carousel

**From start to finish: ~1.5 hours per carousel**

### Step 1: Choose Topic (5 min)
Pick from the 20-topic backlog.

### Step 2: Gather Data (20 min)
Pull 5-7 key statistics from Daanaa database:
- 1 founding stat (the hook)
- 3-5 supporting stats
- 1 memorable insight
- Source each with year

### Step 3: Write Narrative (30 min)
Fill JSON template using CAROUSEL_CONTENT_TEMPLATE.md:
```json
{
  "carousel_type": "sector_insight",
  "title": "Your Topic",
  "slides": [
    { "slide_type": "cover", "headline": "...", ... },
    { "slide_type": "content", "label": "Part 1: The Data", ... },
    ...
  ]
}
```

### Step 4: Render (1 min)
```bash
python3 scripts/linkedin/render_carousel_from_json.py carousels/your_topic.json
```

### Step 5: Review (10 min)
Open PDF, verify:
- Headlines are readable (fit on slide)
- Stats are visible (big bold numbers)
- Hierarchy is clear (headline → stat → description)
- Footer URL is present

### Step 6: Iterate (10 min)
If headlines are too long or tone is generic, adjust JSON and re-render.

### Step 7: Publish (5 min)
When final, run posting script:
```bash
python3 scripts/linkedin/post_carousel.py --use-existing
```

---

## Data Already Available

All statistics needed come from existing Daanaa analysis:

- **IRS 990 SOI Data** — 1.7M org baseline, 10-year trends
- **Financial Health Scoring** — Reserve %, health signals, peer ranking
- **Website Analysis** — Donation link discovery, tech adoption
- **Funding Trends** — Regional, by cause, by size, by archetype
- **ProPublica 990 Extracts** — Leadership data, compensation, revenue trends
- **Geographic Data** — Rural/urban distribution, regional funding gaps

**No external APIs needed.** All carousels use Daanaa's own data.

---

## Quality Standards

Every carousel must pass before publishing:

✓ **Hook Test** — Would a donor want to read more after slide 1?  
✓ **Arc Test** — Do all 6 slides tell one coherent story?  
✓ **Tone Test** — Is voice specific, human, surprising, sourced?  
✓ **Stats Test** — Are all claims dated and attributed?  
✓ **Design Test** — Is hierarchy clear and readable?  
✓ **CTA Test** — Is benefit specific (not "Learn more")?  

No carousel publishes without passing all 6 tests.

---

## Timeline

### This Week (Completed)
- ✓ Format design system locked
- ✓ Content template finalized
- ✓ Narrative framework documented
- ✓ 3 sample carousels rendered
- ✓ Rendering pipeline tested

### Next Week (July 21-27)
- Build 3-4 carousels (topics #4-7)
- Test LinkedIn posting workflow
- Measure early engagement signals
- Refine narrative based on feedback

### Following 2 Weeks (July 28-Aug 10)
- Complete 20-carousel library
- Launch weekly Monday 9am ET cadence
- Monitor metrics daily
- Identify top-performing topics

### Month 2
- Optimize based on engagement data
- Pitch carousel series to nonprofit media
- Build daily nonprofit spotlight series
- Scale to LinkedIn audience growth

---

## Ownership & Autonomy

**Format is locked.** No more design changes needed.

**Anyone can create carousels** using:
1. CAROUSEL_CONTENT_TEMPLATE.md (how to write)
2. CAROUSEL_JOHNNY_HARRIS_GUIDE.md (how to sound like Daanaa)
3. `render_carousel_from_json.py` (how to render)

**Process:**
1. Fill template → Save JSON
2. Render → Get PDF
3. Review against quality checklist
4. Post

**Estimated capacity:** 2-3 carousels/week with current system.

---

## Design Principles (Non-Negotiable)

✓ **Memorable** — Signature accents + navy + gold = instantly Daanaa  
✓ **Readable** — High contrast, premium spacing, no clutter  
✓ **Simple** — Only intentional design elements (no decoration)  
✓ **Modular** — Same structure works for all topics  
✓ **Professional** — Premium typography, pixel-perfect alignment  
✓ **On-Brand** — Aligned with Daanaa mission (trust, transparency, evidence)  

**Change nothing here.** This is what makes Daanaa carousels different.

---

## Files to Reference

**Design & Brand:**
- `docs/CAROUSEL_DESIGN_SYSTEM.md` — Visual rules
- `scripts/linkedin/carousel_generator.py` — Rendering code
- `scripts/linkedin/assets/` — Fonts, logo

**Content & Narrative:**
- `docs/CAROUSEL_CONTENT_TEMPLATE.md` — Writing template
- `docs/CAROUSEL_JOHNNY_HARRIS_GUIDE.md` — Narrative voice
- `scripts/linkedin/carousels/*.json` — Sample JSON

**Operations:**
- `scripts/linkedin/README_CAROUSELS.md` — End-to-end guide
- `scripts/linkedin/render_carousel_from_json.py` — Rendering script
- `scripts/linkedin/post_carousel.py` — LinkedIn posting

---

## What's Next

**For you:**
1. Review the 3 sample carousels (PDFs in `scripts/linkedin/output/`)
2. Read CAROUSEL_JOHNNY_HARRIS_GUIDE.md (the investigative framework)
3. Pick 2-3 topics from the 20-topic backlog
4. Provide any design feedback

**For the team:**
1. Start filling template for topics #4-7
2. Test LinkedIn posting workflow
3. Measure engagement on first carousels
4. Refine topics/tone based on data

---

## Success Metrics

**By End of Week 1:**
- 3 carousels published
- 50+ followers
- Engagement baseline established

**By End of Week 4:**
- 12 carousels in library
- 200+ followers
- Top-performing topics identified

**By End of Month 2:**
- 20 carousels completed
- 2K+ followers
- Weekly cadence locked in
- Media interest beginning

**By End of Month 3:**
- Foundation/funder conversations starting
- Nonprofit media mentions appearing
- Daily spotlight series launched
- Board recruitment interest

---

## Questions?

**About design?** → `docs/CAROUSEL_DESIGN_SYSTEM.md`  
**About writing?** → `docs/CAROUSEL_CONTENT_TEMPLATE.md`  
**About voice?** → `docs/CAROUSEL_JOHNNY_HARRIS_GUIDE.md`  
**About process?** → `scripts/linkedin/README_CAROUSELS.md`  

Everything is documented. Format is ready. Let's fill it with data.

