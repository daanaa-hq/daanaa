# The Daanaa Playbook: How to Build a Regional Discovery Platform

**Purpose:** Share our approach so others can build similar platforms in their region  
**Authority:** Daanaa Stewardship Commitment + Charter  
**License:** Share-alike (if you adapt this, share your adaptations)  
**Last Updated:** August 2026

---

## The Vision We're Sharing

**"Make giving easy and simple and natural and repeatable."**

Daanaa exists to help people discover nonprofits with confidence. We're not trying to be the only platform. We're trying to establish a standard that others can adopt, adapt, and improve.

This playbook is for anyone who wants to build a nonprofit discovery platform in their region, using our principles and approach.

---

## What Makes Daanaa Work (The Core Model)

### 1. **Public Data Only**
- Source: IRS Form 990 (public record, freely available)
- Why: Eliminates conflicts of interest; removes gatekeeping
- Result: Anyone can verify our data; no proprietary information
- Adaptation: Your region's equivalent of IRS data (different countries have different filing systems)

### 2. **Peer-Group Benchmarking, Not Ranking**
- We compare orgs to similar orgs (same cause, similar size)
- We don't rank small vs. large, old vs. new, popular vs. obscure
- Why: Prevents algorithmic bias; treats every org with equal dignity
- Result: Users see context, not verdicts

### 3. **Financial Context, Not Mission Judgment**
- We show financial health (reserves, revenue trend, margin)
- We do NOT rate mission impact ("good" vs. "bad" org)
- Why: IRS data tells us about sustainability, not impact
- Result: Users make informed choices without paternalism

### 4. **Transparency as Default**
- Show sources (IRS, ProPublica, claimed data)
- Show confidence levels (70% confident vs. 95% confident)
- Show limitations (what data can't measure)
- Why: Builds trust; lets users form their own judgment
- Result: Users trust us because they understand what we know and don't know

### 5. **Small Org Fairness**
- No algorithmic disadvantage for nonprofits <$150K revenue
- Geographic diversity (don't hide rural orgs)
- Diversity equity (actively surface underserved communities)
- Why: Stewardship principle; structural fairness
- Result: Users discover hidden gems

### 6. **Privacy as Structural**
- No tracking of individual donors
- No profiles unless orgs claim them
- No data shared with third parties
- Why: Stewardship principle; protects supporter privacy
- Result: Users give without fear of tracking

### 7. **Giving Stays Outside the Platform**
- We link to orgs' own donate buttons
- We never touch money
- We never take a cut
- Why: Keeps us independent; prevents conflicts
- Result: Users trust us because we have no revenue incentive to game the system

---

## The Replication Playbook

### **Phase 1: Define Your Scope (2-4 weeks)**

**Questions to answer:**
1. **Geography:** What region are you covering? (State, metro area, county, country?)
2. **Data source:** What's your region's equivalent of IRS 990 data?
   - USA: IRS Form 990 (ProPublica API + IRS e-file)
   - Canada: CRA Form T1236
   - UK: Charity Commission database
   - EU: National charity registries (varies by country)
3. **Initial orgs:** How many nonprofits will you cover at launch?
   - Daanaa started with 1.7M (national scale)
   - You might start with 10K (state/metro) and grow
4. **Differentiation:** What's unique about your region?
   - Rural focus? Urban focus? Specific cause? Specific demographic?

**Deliverable:** 2-page scope document (who, what, where, why)

---

### **Phase 2: Build Your Core Infrastructure (6-8 weeks)**

**Step 1: Get the data**
- Download or API-connect to your region's nonprofit registry
- Clean and standardize it (orgs change names, EINs, addresses)
- Load into a database

**Step 2: Add financial context**
- Download financial data (990s, equivalent forms)
- Calculate: reserves ratio, operating margin, revenue trend
- Benchmark orgs against peers (same cause + similar size)

**Step 3: Build search**
- Full-text search on org names, missions, causes
- Filter by cause (use NTEE codes or equivalent)
- Filter by location (city, zip code, county)
- Filter by size (revenue band)

**Step 4: Create org detail pages**
- Display: name, mission, location, website, financial context, peer rank
- Show: reserves graph, revenue trend, peer percentile
- Link to: direct website, donation link (verified if possible)
- Meta tags: org name, mission, location (for search engines + social preview)

**Step 5: Deploy search interface**
- Minimal UI: search box, filters, result list, org detail
- Mobile-responsive
- Fast (<500ms query time)
- Accessible (WCAG AA minimum)

**Technology stack (what Daanaa uses):**
- Database: SQLite (for small regions) or PostgreSQL (for scale)
- Search: FTS5 (full-text search) or Elasticsearch
- API: Flask (Python) or equivalent
- Frontend: React/Vue or vanilla JS
- Hosting: Modest cloud instance ($20-100/mo)

**Cost estimate:** $2,000-5,000 to build MVP (if you code it yourself or have volunteer developers)

---

### **Phase 3: Add Trust Signals (4-6 weeks)**

**What Daanaa does:**
1. **Source attribution:** Show where data came from (IRS, ProPublica, claimed)
2. **Confidence indicators:** "70% confident in this mission (limited data)" vs. "95% confident (verified by org)"
3. **Peer ranking:** Visual (bar chart showing where org ranks vs. peers)
4. **Financial narrative:** Plain-language interpretation ("3.2 months reserves" → "Healthy reserves, though below peer average")

**How to implement:**
- Add data source field to every data point
- Calculate confidence based on data recency and completeness
- Show peer percentile visually (no judgment, just context)
- Write narrative templates based on org metrics

**Why this matters:**
- Users see transparency immediately
- Reduces misunderstanding (they know what we're sure of vs. guessing)
- Builds credibility (we're not hiding behind pretty charts)

---

### **Phase 4: Amplify via Research & Content (Ongoing)**

**What Daanaa does:**
1. **Monthly sector reports:** "State of Food Banking 2026"
2. **Regional analysis:** "Nonprofit deserts: Where [region] lacks services"
3. **Thought leadership:** "Why nonprofit reserves matter"

**How to implement:**
- Analyze your data monthly (or quarterly)
- Publish findings (blog post, PDF, newsletter)
- Link from articles to search results ("See all food banks in your area")
- SEO optimize (keywords, headers, meta tags)

**Cost:** 10-20 hours/month (can automate much of it)

**Impact:** Organic traffic, media coverage, credibility as expert

---

### **Phase 5: Enable Nonprofit Profiles (Optional but Valuable)**

**What Daanaa does:**
Nonprofits can claim their profile and:
- Add/update their mission statement
- Update contact info
- Add impact stories, programs, team
- Upload documents (annual report, strategic plan)

**How to implement:**
- Email-based verification (send signup link to org email)
- Simple form to edit info
- Store in separate database (don't overwrite IRS data)
- Display claimed data with a badge ("updated by org")

**Why it matters:**
- Orgs get control over their narrative
- Users see up-to-date info
- Creates feedback loop (org engagement = lower bounces = better SEO)

**Cost:** Additional 2-3 weeks development

---

### **Phase 6: Launch & Market (Ongoing)**

**What Daanaa does:**
1. **SEO:** Optimize for sector keywords, geographic keywords
2. **Direct outreach:** Email nonprofits about profile
3. **Content:** Publish articles that link to directory
4. **Partnerships:** Academic, nonprofit association collaborations
5. **Word of mouth:** Users tell other users

**How to implement:**
- Optimize your site for Google search (meta tags, sitemap, schema markup)
- Create content that links to your directory
- Email nonprofits: "You're listed here, claim your profile"
- Partner with local nonprofit association, funder, or news outlet
- Share data openly (license for researchers)

**Cost:** Mostly time; no paid marketing needed initially

**Success metrics:** 1K+ monthly organic visits in month 3, 10K+ by month 6

---

## Stewardship Commitments (Copy Ours or Adapt)

When you launch, make public commitments that protect the integrity of your work. Here's what Daanaa committed to:

### **The Daanaa Charter: 10 Things We Never Do**

1. **Never take a cut of donations** — Giving stays between supporter and nonprofit
2. **Never rank orgs by size** — Small nonprofits get equal visibility
3. **Never hide data** — All sources, methods, limitations are public
4. **Never sell nonprofit data** — Nonprofits aren't commodities
5. **Never let money shape rankings** — No paid placement, no sponsored results
6. **Never track individual donors** — Supporter privacy is sacred
7. **Never make unverified claims** — All signals are evidence-based
8. **Never assume impact** — Financial health ≠ mission quality
9. **Never lock nonprofits in** — Claiming your profile is optional; leaving is free
10. **Never stop explaining ourselves** — If we make mistakes, we correct and document them

**Why this matters:**
- Public commitments build trust
- They constrain future decisions (you can't "just monetize" later if you've promised not to)
- They give nonprofits confidence in your platform
- They're your competitive advantage (trustworthiness beats features)

**Adapt these to your context.** Your charter should reflect your region's needs and values.

---

## How to Adapt the Model to Your Region

### **If you're smaller (state/metro scale)**

**What to change:**
- Start with one sector (Food, Education, Health) and expand
- Load only nonprofits in your region (not national)
- Simpler search (maybe no semantic search, just keyword + filters)
- Simpler infrastructure (SQLite instead of PostgreSQL)

**Cost:** $500-2K to build

**Timeline:** 3-4 months to MVP

### **If you're in a different country**

**What to change:**
- Use your country's nonprofit registry (Charity Commission, tax authority, etc.)
- Adapt peer-grouping to local cause taxonomy
- Translate interface to local language(s)
- Publish content in local media context
- Partner with local funders/associations

**Cost:** $3K-10K (translation, local infrastructure, compliance)

**Timeline:** 4-6 months to MVP

### **If you're focusing on a specific cause**

**What to change:**
- Filter nationally (or by region) to just your cause
- Add cause-specific metrics (outcomes, program types, etc.)
- Research and publish cause-specific insights
- Partner with cause-specific organizations

**Cost:** $1K-3K (focused development)

**Timeline:** 2-3 months to MVP

---

## The Hidden Advantage: Network Effects

**If multiple regions adopt this model:**

1. **Data sharing:** States can learn from states, countries from countries
2. **Reusable research:** Articles, methodologies, tools transfer
3. **Collective credibility:** "Region Z launched a platform based on the Daanaa model" → Daanaa credibility increases
4. **Supporter movement:** Supporters who use Daanaa elsewhere trust your platform
5. **Network effects:** If you're consistent with Daanaa, everything is easier for users across regions

**Long-term vision:** A federation of regional platforms, all using the same principles, sharing research and learning.

---

## Open Questions & Feedback

**If you're building a regional platform, tell us:**
1. What's your region and data source?
2. What's unique about your nonprofit ecosystem?
3. What did you have to adapt from this playbook?
4. What worked? What didn't?
5. What should we add to the playbook?

**Contact:** playbook@daanaa.org

We'll feature your platform on our site and link your research to ours. Let's build a movement.

---

## The Why: Why We're Sharing This

**We could keep this proprietary.** Daanaa's competitive advantage is real, and there are ways to monetize the model.

**We're not, because:**

1. **The mission matters more than the company.** "Make giving easy" is bigger than Daanaa. If we're right that transparency + fairness + small-org dignity = more effective giving, then 10 great regional platforms are better than 1 national one.

2. **We trust the model.** If our principles are sound, they'll work elsewhere. Proving that is the best validation.

3. **Network effects compound.** 10 platforms sharing research and learning will outpace 1 platform alone.

4. **Giving is not zero-sum.** Your region's supporters learning to give better doesn't hurt ours. Rising tide.

5. **We want to be wrong.** If other teams try this and find flaws, we want to learn and fix them.

---

## Getting Started Checklist

- [ ] Read the Daanaa Charter (daanaa.org/charter)
- [ ] Read the Stewardship Commitment (daanaa.org/stewardship)
- [ ] Identify your region and data source
- [ ] Assess: Can you build this? (Code? Budget? Partners?)
- [ ] Sketch: What's unique about your ecosystem?
- [ ] Reach out: Tell us you're thinking about this
- [ ] Learn: Read Daanaa's code (open-source coming) or other regional platforms
- [ ] Build: Start with Phase 1 scope
- [ ] Launch: Share what you learn

---

## Resources

- **Daanaa codebase:** [Open source version coming 2026]
- **Data sources by country:** [Link to registry by country]
- **Community:** [Forum/Slack for others building platforms]
- **Templates:** [Article templates, form templates, schemas]
- **Articles on the model:** [Blog posts explaining our approach]

---

## License & Share-Alike

**This playbook is shared under a Creative Commons Share-Alike license.**

You can:
- ✅ Copy it and adapt it for your region
- ✅ Share it publicly
- ✅ Use it commercially (but not exclusively)
- ✅ Build a for-profit platform using this approach

You must:
- ✅ Credit Daanaa
- ✅ Share your adaptations (so we can all learn)
- ✅ Preserve the charter (commitment to fairness)

**In other words:** Copy us, improve on us, share what you learn. That's the point.

---

## Success Stories (As They Happen)

We'll track and feature regional platforms built on this model:

- **[Region Name]** — Launched [date], covers [X] nonprofits, published [Y] articles
- **[Region Name]** — Launched [date], focus on [cause], partner with [org]

[Your platform here?]

---

**Made with ❤️ by Daanaa**

*We believe giving should be easy, simple, natural, and repeatable. If you do too, let's build this together.*

*hello@daanaa.org*
