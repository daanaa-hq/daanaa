# Research & Content Strategy for Organic Traffic

**Authority:** Team E (Research) + Team D (Growth)  
**Goal:** Use sector insights + white papers to drive organic discovery traffic  
**Timeline:** Weekly sector reports + monthly deep dives + quarterly white papers

---

## The Model

**Content → SEO Traffic → Discovery → Nonprofit Engagement**

1. **Monthly Sector Health Report** (recurring, low-effort, high-impact)
   - "State of Food Banking Q3 2026" 
   - "Nonprofit Funding Trends: Mid-Year Update"
   - Auto-generated from Phase 10 sector_health_snapshots table
   - ~500 words, 3-5 key charts/stats, published to `/research/`
   - **Result:** Google ranks us for "food bank statistics 2026" → user discovers Daanaa → browses directory

2. **Quarterly White Paper** (deeper research, thought leadership)
   - "The 2026 State of Nonprofit Sustainability"
   - "Why Small Nonprofits Outperform: An Analysis of 100K Organizations"
   - 2,000-3,000 words, data-backed, downloadable as PDF
   - Published to `/research/whitepaper/YEAR-SEASON-TITLE`
   - **Result:** Academic citations, media coverage, link-worthy content

3. **Sector Focus Hubs** (curated results + insights)
   - `/research/sectors/food-assistance/` → sector stats + link to directory results
   - Topic hub = insights + "See all {topic} orgs" CTA
   - Generated from cause_tags + v5_context data
   - **Result:** "best food banks" search → lands here → links to live directory

4. **Data Partnerships** (research licensing)
   - License anonymized sector datasets to universities / research orgs
   - "Nonprofit Diversity in America: A 1.7M Org Dataset"
   - $5-25K per partnership, drives backlinks + credibility
   - **Result:** academic.edu citations → links → SEO

---

## What We Have Ready

### Data Already in Database

- `sector_health_snapshots` (Phase 10) — sector-wide metrics
- `funding_flows` (Phase 10) — where money goes by cause/size
- `coverage_gaps` (Phase 10) — which causes are underserved
- `org_claims` — nonprofit self-reported data (missions, impacts)
- Full financial context (`nonprofit_financial_health`) — 537K orgs benchmarked
- 1.7M org records with NTEE coding, geography, revenue band

### Templates Ready

- Chart templates (sector trends, funding distribution)
- Report template (monthly format: headline + 3 charts + takeaways + CTA)
- Hub template (topic, stats, org count, sample orgs, directory link)

### Content Calendar

| Content Type | Frequency | Trigger | Purpose |
|---|---|---|---|
| **Monthly pipeline report** | 1x/month | After overnight pipeline completes | What changed in data (new orgs, score updates, trends) |
| **Quarterly white papers** | 4x/year | Calendar | Thought leadership & methodology |
| **Sector deep-dives** | 1-2x/month | As needed | Deep analysis linked from monthly report |
| **Research articles** | As needed | Seasonal/topical | Explain findings + teach skills |

**Monthly reports are the heartbeat** — everything else hangs off them.

---

## Autonomous Work (What I Can Do)

### Phase 1: Monthly Reports (Weeks 1-2)
- [ ] Extract sector_health_snapshots → report narrative
- [ ] Generate 3 default charts (funding distribution, org count by band, reserve ratios)
- [ ] Create `/research/monthly/YEAR-MONTH-SECTOR.md` template
- [ ] Publish June 2026 report (retrospective, catch up)
- [ ] Set up cron to auto-publish on first Monday of each month

### Phase 2: Sector Hub Generation (Weeks 3-4)
- [ ] Build `/research/sectors/CAUSE/` hub for top 10 causes
- [ ] Hub = "State of CAUSE", stat summary, "See all X orgs" CTA to directory
- [ ] Wire cause_tags → hub auto-generation
- [ ] Publish 10 hubs and measure traffic impact

### Phase 3: Search Optimization (Weeks 5-6)
- [ ] Add "How many CAUSE nonprofits?" to site title + meta
- [ ] Create topic clusters ("food + hunger + feeding" all → food hub)
- [ ] Internal links: research → directory (with search query pre-filled)
- [ ] Verify Google Search Console picks up new content

### Needs Founder Input

1. **White Paper Topics:** What issues matter most to Daanaa's mission?
   - Example: "Why Nonprofit Reserves Matter" (defends our financial context visibility)
   - Example: "The Economics of Scale in Nonprofits" (explains small org fairness)
   
2. **Voice & Framing:** How academic vs. conversational?
   - Academic = citations, authority, link-worthy
   - Conversational = accessible, shareable, engaging
   
3. **Distribution:** Do we have media/academic partnerships to amplify?

---

## Expected Impact

### Traffic (3–6 months)
- Month 1: 50-100 organic visits to research section
- Month 2: 200-300 organic visits (first report published)
- Month 3: 500-1K organic visits (Google indexing + backlinks)
- Month 6: 2K-5K monthly organic from research content

### Engagement
- Research readers = 3x more likely to explore directory
- "See all CAUSE orgs" CTAs = conversion to directory usage
- Nonprofit discovery traffic increases = more orgs get traffic → more claim activity

### Authority
- Backlinks from academic citations (research partnerships)
- Media coverage ("New data shows nonprofits...")
- Positioning as the authority on nonprofit data

---

## Example: July 2026 Food Banking Report

**Title:** State of Food Banking 2026 — Q2 Update

**Intro paragraph:**
> 147,382 food-assistance nonprofits in the U.S. manage ~$8.2B in annual spending. New Daanaa analysis of IRS data reveals shifting funding patterns and reserve challenges affecting half the sector.

**Sections:**
1. **The Numbers** (3 stats with charts)
   - Total food-assistance orgs: 147K (↓2% from 2025)
   - Average annual revenue: $557K (↑3%)
   - Median reserve ratio: 3.2 months (↓0.8 months YoY)

2. **What It Means**
   - Sector is leaner than before (more at-risk orgs)
   - But total funding is growing (good sign)
   - Small orgs (< $150K) driving growth (16% YoY)

3. **Take Action**
   - [Browse all food-assistance nonprofits](/?ntee=I&cause=food)
   - [Compare peer organizations](/research/sectors/food-assistance/)
   - [Download full dataset](...)

**Outcome:** Published to `/research/monthly/2026-07-food-banking/`, auto-linkable, ranks for "food bank statistics 2026", drives 50-100 visitors in week 1.

---

## Implementation Checklist

- [ ] Phase 10 tables populated (sector_health_snapshots, funding_flows)
- [ ] Report template + automation (cron-able)
- [ ] First 3 monthly reports published
- [ ] Topic hubs created for top 5 causes
- [ ] Google Search Console integration (sitemaps for research content)
- [ ] Internal link strategy (research → directory with pre-filled queries)
- [ ] Analytics tracking (where do research visitors go in directory?)
- [ ] Founder input on white paper topics and voice

---

## Success Metrics

**By Month 3:**
- [ ] 500+ organic visits to research section
- [ ] 10+ research → directory link clicks per week
- [ ] Top sector report ranking on Google (1st page for "SECTOR statistics")
- [ ] 3 sector hubs published and live

**By Month 6:**
- [ ] 2,000+ monthly organic traffic from research
- [ ] 1+ media mention citing Daanaa data
- [ ] 1+ academic partnership (dataset license)
- [ ] Research content = 5% of total discovery traffic
