# Daanaa Campaign Management System

**Version:** 1.0  
**Built:** 2026-07-15  
**Status:** Ready for Launch  
**Philosophy:** World-class tools, stewardship-first design

---

## What This Is

A complete LinkedIn campaign management system built specifically for Daanaa. It lets you:

1. **Create carousels** (5 templates ready, infinite variations)
2. **Batch-approve campaigns** (you review 4-5 at once weekly)
3. **Schedule posts** (automated via API + UTM generation)
4. **Track engagement** (impressions, likes, clicks, traffic)
5. **Report performance** (weekly summary, trend analysis)

**Key difference from Buffer/Later/Hootsuite:** This system is built on Daanaa's Stewardship Commitment. Every carousel, every metric, every design choice is anchored to mission, not engagement maximization.

---

## System Components

### 1. Backend API (`campaigns_api.py`)

**What it does:** Manages campaigns (create, edit, approve, schedule) + analytics tracking

**Key routes:**
- `POST /api/campaigns/create` — Create draft campaign
- `POST /api/campaigns/{id}/submit-for-approval` — Submit for review
- `POST /api/campaigns/{id}/approve` — Approve for scheduling
- `POST /api/campaigns/{id}/schedule` — Schedule for posting
- `POST /api/campaigns/{id}/record-metric` — Log engagement metric
- `GET /api/campaigns/{id}/analytics` — Get campaign performance

**Security:**
- Admin-key gated (not exposed)
- Local SQLite (no cloud vendor)
- No third-party integrations
- Human approval required before posting

---

### 2. Dashboard (`AdminCampaigns.tsx`)

**What it does:** React UI for managing campaigns

**Features:**
- View drafts, pending approval, approved, scheduled, posted campaigns
- Click to see analytics (impressions, likes, clicks)
- One-click submit/approve/schedule
- Weekly summary view

**Access:** `/admin/campaigns` (founders + admins only)

---

### 3. Carousel Renderer (`carousel_renderer.py`)

**What it does:** Converts carousel JSON to LinkedIn-ready format

**Outputs:**
- LinkedIn caption (with hashtags + CTA)
- HTML render (for preview/archiving)
- JSON export (for programmatic use)

**Philosophy:** Mechanical, transparent, no AI inference.

---

### 4. Orchestrator (`campaigns_orchestrator.py`)

**What it does:** Coordinates full campaign lifecycle

**Key functions:**
- `batch_create_campaigns()` — Create multiple from carousel files
- `validate_carousel_stewardship()` — Audit against Charter principles
- `generate_weekly_batch()` — Auto-create batch for review
- `export_campaign_for_posting()` — Prepare for LinkedIn
- `generate_weekly_report()` — Performance summary

---

### 5. Carousel Library (`/linkedin/carousels/`)

**Files:**
- `sample_1_reserve_crisis.json` — Reserve adequacy crisis
- `sample_2_fundraising_tax.json` — Fundraising burden (nonprofit leaders)
- `sample_2_invisible_97_donors.json` — Finding invisible nonprofits (donors)
- `sample_3_funding_paradox.json` — Financial context (thoughtful givers)
- `sample_4_find_your_cause_celebrity.json` — Celebrity/news hook
- `sample_5_find_your_cause_awareness_day.json` — Awareness day template

All JSON files include:
- Slide content (headline, story, stats)
- Sources (with confidence levels)
- Hashtags + CTAs
- Charter compliance notes

---

## How to Use

### Weekly Workflow

**Monday (You):**
1. Open `/admin/campaigns`
2. See new batch of 4-5 carousels (auto-created)
3. Review each carousel + copy
4. Approve or request tweaks

**Wednesday (System):**
1. Schedule approved carousels
2. Generate UTM links
3. Post to LinkedIn (via Buffer or manual)

**Friday (System):**
1. Collect analytics
2. Generate weekly report
3. You review metrics

**Next Monday (You):**
1. Decide: "What worked? What next?"
2. Create new batch based on performance

### Creating a Custom Carousel

```bash
# 1. Create new carousel JSON (copy from sample)
cp sample_1_reserve_crisis.json sample_custom_awareness_day.json
# 2. Edit slides, add your content
# 3. Via API or dashboard:
orchestrator.create_campaign_from_carousel('sample_custom_awareness_day.json')
# 4. Review + approve in dashboard
```

### Scheduling a Post

```python
# API call (automatic via dashboard):
POST /api/campaigns/{campaign_id}/schedule
{
  "scheduled_for": "2026-07-24T09:00:00Z"
}
# Returns UTM link + posting details
```

### Tracking Performance

```bash
# Weekly report
orchestrator.generate_weekly_report()
# Output:
# {
#   "period": "2026-07-08 to 2026-07-15",
#   "campaigns_posted": 5,
#   "analytics": {
#     "impressions": 12,000,
#     "likes": 340,
#     "clicks": 89,
#     ...
#   }
# }
```

---

## Design Philosophy: Why It's Different

### 1. Stewardship Over Growth

**Industry Standard:** Maximize engagement, virality, follower growth.  
**Our Approach:** Drive traffic to daanaa.org/directory. That's it.

- CTAs never manipulate ("tag a friend," "comment below")
- No urgency language ("don't miss out," "act now")
- No vanity metrics (followers ≠ impact)
- Goal: nonprofit discovery, not brand awareness

**Proof:** 
- No "like this if you agree" CTAs
- No polls designed for engagement (only research)
- No pressure language in any carousel
- All CTAs are hand-offs (to search, not to action)

---

### 2. Privacy First

**Industry Standard:** Track everything, build advertising profiles.  
**Our Approach:** Aggregate metrics only. No user tracking.

- UTM links track source (LinkedIn), not person
- Analytics stored locally (no third-party tools)
- No integration with Google Analytics (would expose user behavior)
- No wallet data mixed with campaign data
- All data stays on Daanaa server

**Technical Implementation:**
- Local SQLite (not cloud database)
- Campaign analytics table has no user_id
- No external API calls for tracking
- Metrics are campaign-level, not individual-level

---

### 3. Evidence-Based Claims

**Industry Standard:** Generative AI insights, unverified hype.  
**Our Approach:** All stats sourced. Estimates clearly labeled.

- Every claim in every carousel is backed by IRS, ProPublica, or Daanaa data
- External sources cited (nonprofit burnout research, donor surveys)
- Confidence levels marked (100% = Daanaa data, external = noted)
- No "AI recommends"—just data + human interpretation

**Example:**
- "84% of donors want local giving" — External research (marked)
- "1.6M nonprofits are invisible" — Daanaa data (100%)
- "768M hours/year on fundraising" — Calculated (transparent math)

---

### 4. No Ranking

**Industry Standard:** Rank orgs, show "top performers."  
**Our Approach:** All orgs presented with equal dignity.

- Carousels never say "small orgs are better"
- No "data proves X is most efficient"
- No comparison between large and small
- Different models are presented as choices, not hierarchies

**Rewrite Example:**
- OLD: "Small nonprofits have 68% program spend. Large ones waste 40% on overhead."
- NEW: "Different organizations operate different models. Financial context helps you understand."

---

### 5. Respect & Dignity

**Industry Standard:** Emotional manipulation ("failing nonprofits," "neglected communities").  
**Our Approach:** Honest framing, no shame, no pressure.

- No "broken system" language
- No "nonprofits are drowning" narratives
- No "save them" urgency
- All orgs treated as professionals with agency

**Copy Review Process:**
1. Every carousel read by human
2. Checked for shame language
3. Checked for pressure/nudging
4. Checked for ranking
5. You approve before posting

---

## Best Practices Adopted

✅ **From Buffer/Later:**
- Scheduled posting (with calendar view)
- Analytics dashboard (impressions, likes, clicks)
- Content calendar (monthly planning)
- Performance reporting (what worked)

✅ **From LinkedIn Best Practices:**
- Carousel format (higher engagement than images)
- Hashtag strategy (consistent #FindYourCause)
- Posting cadence (3-4x/week, not spammy)
- Hook-driven copy (question or stat opening)
- Clear CTAs (direct, not clickbait)
- Local optimization (cause-specific variants)

❌ **What We Rejected:**
- Cloud vendor lock-in (we use local SQLite)
- Multi-platform bloat (just LinkedIn + email)
- Engagement hacking (tag a friend, polls, etc.)
- Influencer detection (who cares?)
- Social scoring (BS metric)
- Algorithm gaming ("best time to post" tricks)

---

## Metrics We Track (And Why)

### Track

✅ **Impressions** — Reach (how many saw it?)  
✅ **Likes/reactions** — Sentiment (did they engage?)  
✅ **Shares** — Amplification (did they forward it?)  
✅ **Comments** — Dialogue (did they think about it?)  
✅ **Clicks to daanaa.org** — Traffic (did it drive action?)  
✅ **UTM conversion** — Discovery (did they search?)  

### Don't Track

❌ **Follower growth** — Vanity  
❌ **Individual user behavior** — Privacy violation  
❌ **Share of voice** — Ego  
❌ **Competitor mentions** — Not relevant  
❌ **Influencer reach** — Not our model  

---

## Weekly Review Checklist

**Every Monday, you assess:**

- [ ] Reviewed draft carousels (approved/requested tweaks)
- [ ] Confirmed no Charter violations (ranking, shame language, pressure)
- [ ] Checked sources (all stats verified)
- [ ] Approved final copy
- [ ] Scheduled posting dates
- [ ] Confirmed UTM links generated

**Every Friday, system reports:**

- [ ] Campaigns posted this week: __
- [ ] Total impressions: __
- [ ] Engagement rate: __% (likes/impressions)
- [ ] Clicks to daanaa.org: __
- [ ] Nonprofit profile claims from traffic: __
- [ ] Top-performing carousel: ___
- [ ] Recommendation for next week: ___

---

## Roadmap

### Phase 1 (Current): Core System ✅

- [x] Dashboard backend (API)
- [x] Dashboard frontend (React)
- [x] Carousel renderer
- [x] 5 carousel templates
- [x] Stewardship audit
- [x] Weekly approval workflow

### Phase 2 (2-4 weeks): Scaling

- [ ] Expand carousel library to 20 templates
- [ ] Add awareness day calendar (auto-generate variants)
- [ ] Email digest format (send carousels to list)
- [ ] Analytics export (CSV for spreadsheets)
- [ ] Performance trend analysis (what improves over time?)

### Phase 3 (Months): Ecosystem

- [ ] Nonprofit blog articles (mission-driven content)
- [ ] Donor education series (stewardship messaging)
- [ ] Community guidelines (how nonprofits can share)
- [ ] Impact measurement (nonprofits claiming they found donors)

---

## Support & Maintenance

**Questions?** Email akbar@daanaa.org  
**Bug report?** Open issue in GitHub (if applicable)  
**Feature request?** Document in DECISIONS.md

**Who maintains this:**
- API & backend: You (Akbar)
- Dashboard: React (you can update)
- Carousels: Batch creation (you review)
- Metrics: Weekly reports (system generates)

**Review cadence:**
- Weekly: Carousel approvals (you)
- Weekly: Performance report (you)
- Monthly: Stewardship audit (thorough check)
- Quarterly: Impact review (is this working?)

---

## Final Note

This system is built to last, not to optimize for vanity. It's designed so that 5 years from now, you can look back and say: "We grew Daanaa's platform engagement in a way we're proud of. We didn't manipulate, didn't track people, didn't rank nonprofits. We just made discovery easier and told honest stories."

That's the whole point.

---

**Built with:** Flask (backend), React (frontend), SQLite (data), Python (orchestration)  
**Designed for:** Founder-driven approval, stewardship-first, privacy-respecting  
**Status:** ✅ Ready to launch

Launch when ready. We've got this.
