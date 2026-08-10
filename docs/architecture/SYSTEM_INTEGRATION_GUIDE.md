# System Integration Guide — All 6 Systems

**Status:** ALL BUILT  
**Timeline:** Week 1-6 deployment  
**Complexity:** All systems interconnected; deploy in sequence

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        CONTINUOUS IMPROVEMENT ENGINE            │
│         (Learns from all data, suggests optimizations)          │
│                                                                 │
│  Inputs: Campaign metrics + social engagement + claims + email  │
│  Outputs: Carousel topics + email optimizations + partners      │
└────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
    CAMPAIGNS        SOCIAL MEDIA      RELATIONSHIP
     SYSTEM          MANAGER            CRM
     (Posts)       (Comments)        (Tracking)
        │                │                │
        ├────────────────┼────────────────┤
        │                │                │
        └────────────────┼────────────────┘
                         │
                         ▼
                   EMAIL AUTOMATION
                    (Nurture sequences)
```

---

## Data Flow Between Systems

### Campaign → Social Media Manager
```
campaigns table
    ↓ (campaign_id)
    ↓
comments table
    ↓ (logs user comments on posts)
    ↓
traction_scores table
    ↓ (quality scoring: 0-100)
    ↓
Social Media Manager → Daily Digest to human
```

**What it does:** Campaign posts → people comment → we score quality → recommend responses

### Campaign → Relationship CRM
```
campaigns table
    ↓ (carousel click)
    ↓
nonprofits_engaged (if clicked by nonprofit)
donors_engaged (if clicked by donor)
    ↓ (interaction tracked)
    ↓
interaction table
    ↓ (all touchpoints in one place)
    ↓
Relationship Manager → Weekly summary
```

**What it does:** Carousel reach → people engage → relationships tracked → nurturing triggered

### Social Media Manager → Relationship CRM
```
traction_scores (comment quality)
    ↓ (high quality = nonprofit leader/investor)
    ↓
partners_potential table
    ↓ (auto-create record)
    ↓
Email Automation enrolls them
    ↓ (first partnership email)
```

**What it does:** High-quality comment → auto-create partner → start nurture sequence

### Relationship CRM → Email Automation
```
nonprofits_engaged
    ↓ (first_seen_date = trigger)
    ↓
email_sequences table
    ↓ (enroll nonprofit in 5-email sequence)
    ↓
Weekly: advance_sequence() moves them step by step
    ↓
Email Automation tracks opens/clicks
    ↓ (logged back to email_sequences)
```

**What it does:** New nonprofit discovered → auto-enroll in email sequence → track engagement

### Email Automation → Relationship CRM (Feedback Loop)
```
email_sequences (opened_at, clicked_at)
    ↓ (tracked per email)
    ↓
relationship CRM updated with engagement status
    ↓
nonprofits_engaged.engagement_status updated
    ↓ (INTERESTED → CLAIM_STARTED → CLAIMED)
```

**What it does:** Email engagement moves nonprofits through claim funnel

### All Systems → Continuous Improvement Engine
```
Campaign metrics + Social themes + Claims funnel + Email performance + Partner signals
    ↓ (weekly analysis)
    ↓
Weekly learning log + suggestions generated
    ↓
Optimization suggestions table populated
    ↓
Recommendations surface to Akbar for approval
```

**What it does:** All data analyzed → insights generated → carousel topics suggested

---

## Database Schema Dependencies

All systems share `merit_registry.db`:

```
CAMPAIGNS SYSTEM:
├─ campaigns
├─ campaign_analytics
└─ utm_links

SOCIAL MEDIA MANAGER:
├─ comments
├─ traction_scores
└─ engagement_themes

RELATIONSHIP CRM:
├─ nonprofits_engaged
├─ donors_engaged
├─ partners_potential
└─ interactions

EMAIL AUTOMATION:
├─ email_sequences
└─ email_templates

CONTINUOUS IMPROVEMENT:
├─ learning_logs
└─ optimization_suggestions
```

**Total new tables: 14**
**Shared with existing: merit_registry.db (no schema conflicts)**

---

## API Integration Points

### 1. Campaign System → Social Media Manager

**When:** Daily at 6pm (metrics collection cron)

```python
# campaigns_orchestrator.py calls:
from scripts.social_media_manager import SocialMediaManager

smm = SocialMediaManager()

# Scrape LinkedIn comments on campaigns posted in last 24 hours
# For each comment:
comment_id = smm.log_comment(campaign_id, author_name, ..., comment_text)
score = smm.score_comment(comment_id)
digest = smm.get_daily_digest()

# Digest now available for human review
```

**Endpoint:** `/api/campaigns/social-digest`  
**Response:** List of comments needing response, by priority score

---

### 2. Campaign System → Relationship CRM

**When:** Real-time on carousel click

```python
# Django/Flask middleware (droplet_api.py) hooks carousel click:
from scripts.relationship_manager import RelationshipManager

rm = RelationshipManager()

# User clicks carousel → track engagement
nonprofit_id = rm.track_nonprofit_from_carousel(
    nonprofit_id,
    carousel_id,
    carousel_title
)

# Later: nonprofit starts claim
rm.track_nonprofit_claim_start(nonprofit_id)

# Later: nonprofit completes claim
rm.track_nonprofit_claim_complete(nonprofit_id, completeness=85, contact_email="...")
```

**Endpoint:** `/api/crm/relationships/<nonprofit_id>`  
**Response:** Current engagement status + interaction history

---

### 3. Social Media Manager → Email Automation

**When:** Weekly Sunday after theme extraction

```python
# campaigns_orchestrator.py weekly job:
from scripts.social_media_manager import SocialMediaManager
from scripts.email_automation import EmailAutomation

smm = SocialMediaManager()
ea = EmailAutomation()

# Find high-quality nonprofit comments
digest = smm.get_daily_digest()

for comment in digest["comments_to_respond"]:
    if comment["intent"] == "INTRODUCTION" and comment["quality_score"] >= 70:
        nonprofit_id = extract_nonprofit_from_comment(comment)
        
        # Enroll in email sequence if not already
        ea.enroll_nonprofit(nonprofit_id, nonprofit_name, mission, email, contact_person)
```

**Endpoint:** `/api/email/enroll-nonprofit`  
**Params:** nonprofit_id, nonprofit_name, mission_statement, email, contact_person  
**Response:** sequence_id, first_email_scheduled

---

### 4. Relationship CRM → Email Automation (Periodic)

**When:** Weekly Monday after CRM summary

```python
# campaigns_orchestrator.py:
from scripts.relationship_manager import RelationshipManager
from scripts.email_automation import EmailAutomation

rm = RelationshipManager()
ea = EmailAutomation()

# Get weekly CRM summary
summary = rm.weekly_relationship_summary()

# Enroll new nonprofits in sequences
for nonprofit_id in summary["new_nonprofit_engagements"]:
    status = rm.get_relationship_status("nonprofit", nonprofit_id)
    if not status.get("email_sequence_enrolled"):
        ea.enroll_nonprofit(nonprofit_id, ...)
```

**Endpoint:** `/api/email/enroll-batch`  
**Params:** entity_type, entity_ids (nonprofit/donor/partner)  
**Response:** enrollment_count, sequences_created

---

### 5. Email Automation → Email Service

**When:** Daily at 9am (send scheduled emails)

```python
# campaigns_orchestrator.py:
from scripts.email_automation import EmailAutomation

ea = EmailAutomation()

# Get all sequences with sent_at = NULL (ready to send)
cursor = ea.db.cursor()
cursor.execute("""
    SELECT es.id, es.target_id, es.target_type, et.body
    FROM email_sequences es
    JOIN email_templates et ON es.email_template_id = et.id
    WHERE es.sent_at IS NULL
    AND es.sequence_step IS NOT NULL
""")

# For each, send email + log
for sequence in cursor:
    # Render email with personalization
    email_body = render_email(sequence["body"], sequence["target_id"])
    
    # Send via Gmail SMTP
    send_email(target_email, email_body)
    
    # Log sent
    ea.log_email_sent(sequence["id"], target_email)
```

**Endpoint:** `/api/email/send-batch`  
**Response:** sent_count, failed_count, logs

---

### 6. Continuous Improvement Engine (Read-Only)

**When:** Weekly Friday at 5pm

```python
# campaigns_orchestrator.py generates weekly report:
from scripts.continuous_improvement import ContinuousImprovementEngine

cie = ContinuousImprovementEngine()

# Run all analyses
weekly = cie.weekly_analysis()
# Returns: insights + suggestions

# Store + surface to Akbar
# /admin/dashboard shows suggestions
# Akbar approves + implements next week
```

**Endpoint:** `/api/insights/weekly`  
**Response:** themes, carousel_suggestions, email_optimizations, partners, metrics

---

## Cron Job Integration

Update `campaigns_orchestrator.py` to call all systems:

```python
# EXISTING (don't change):
# 0 0 * * 0   → generate_weekly_batch()
# 0 18 * * *  → collect_daily_metrics()
# 0 20 * * 5  → generate_weekly_report()

# NEW (add these):
# Sunday 12:30am → continuous_improvement.weekly_analysis()
# Monday 6:00am  → relationship_manager.weekly_summary()
# Daily 9:00am   → email_automation.send_batch()
# Weekly Friday  → all_systems_to_dashboard()
```

---

## Testing Integration

### Test Data Setup

```python
# Run once to populate test data
python3 << 'EOF'
from scripts.campaigns_orchestrator import CampaignOrchestrator
from scripts.social_media_manager import SocialMediaManager
from scripts.relationship_manager import RelationshipManager
from scripts.email_automation import EmailAutomation

# Generate test campaign
orch = CampaignOrchestrator()
campaign_ids = orch.generate_weekly_batch()

# Log test comments
smm = SocialMediaManager()
comment_id = smm.log_comment(
    campaign_id=campaign_ids[0],
    author_name="Jane Nonprofit",
    author_handle="janelead",
    author_followers=5000,
    comment_text="This is exactly what we need. How do we claim our profile?",
    comment_url="https://linkedin.com/..."
)

# Score the comment
score = smm.score_comment(comment_id)
print(f"Comment quality: {score.quality_score}/100")

# Track nonprofit
rm = RelationshipManager()
nonprofit_id = "nonprofit_test_12345"
rm.track_nonprofit_from_carousel(nonprofit_id, campaign_ids[0], "Test Campaign")
rm.track_nonprofit_claim_start(nonprofit_id)

# Enroll in email
ea = EmailAutomation()
ea.enroll_nonprofit(nonprofit_id, "Test Nonprofit", "Testing Daanaa", "test@nonprofit.org")

print("✓ Integration test complete")
EOF
```

---

## Deployment Sequence

### Week 1: Campaign System + Social Media Manager

**Day 1-2:** Deploy campaign system (DEPLOYMENT_START.md)  
**Day 3-7:** Build + integrate social media manager  
**Day 7:** Manual comment monitoring workflow (you respond to high-quality comments)

### Week 2: Dashboard + CRM

**Day 1-7:** Build + integrate master dashboard  
**Day 1-7:** Build + integrate relationship CRM  
**End of week:** Dashboard shows all engagements + relationships

### Week 3: Email Automation

**Day 1-5:** Build + integrate email automation  
**Day 5:** First nonprofit + donor sequences start automatically

### Week 4: Continuous Improvement

**Day 1-7:** Integrate continuous improvement engine  
**Day 7:** System generates weekly optimization suggestions

### Week 4+: Full Automation

All systems running + learning together:
- Carousel posts every Mon/Wed/Fri
- Social media manager scores comments daily
- Relationship CRM tracks all engagement
- Email sequences nurture automatically
- Continuous improvement learns + suggests
- Akbar approves once per week

---

## Monitoring + Health Checks

### Weekly Health Checklist

```bash
# Campaign system
curl http://localhost:5000/api/campaigns/health

# Database integrity
sqlite3 /home/akbar/meritgiving/data/merit_registry.db ".tables" | grep -E "comments|traction|nonprofit|donors|partner|email|learning"

# Recent logs
tail -20 logs/cron_*.log

# Comment backlog (social media manager)
curl http://localhost:5000/api/social/digest

# Relationship pipeline (CRM)
curl http://localhost:5000/api/crm/weekly-summary

# Email performance
curl http://localhost:5000/api/email/weekly-metrics

# Weekly insights
curl http://localhost:5000/api/insights/weekly
```

---

## Troubleshooting

### Comments not being logged
```bash
# Check social media manager is running
python3 -c "from scripts.social_media_manager import SocialMediaManager; print('✓ Module loads')"

# Check database tables exist
sqlite3 /home/akbar/meritgiving/data/merit_registry.db "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'comment%';"
```

### Relationships not tracking
```bash
# Verify CRM module
python3 -c "from scripts.relationship_manager import RelationshipManager; print('✓ Module loads')"

# Check interactions table has records
sqlite3 /home/akbar/meritgiving/data/merit_registry.db "SELECT COUNT(*) FROM interactions;"
```

### Emails not sending
```bash
# Verify email automation module
python3 -c "from scripts.email_automation import EmailAutomation; print('✓ Module loads')"

# Check email_sequences table
sqlite3 /home/akbar/meritgiving/data/merit_registry.db "SELECT COUNT(*) FROM email_sequences WHERE sent_at IS NOT NULL;"
```

### Insights not generating
```bash
# Verify continuous improvement module
python3 -c "from scripts.continuous_improvement import ContinuousImprovementEngine; print('✓ Module loads')"

# Check learning logs
sqlite3 /home/akbar/meritgiving/data/merit_registry.db "SELECT COUNT(*) FROM learning_logs;"
```

---

## Success Metrics (Week 1-4)

| Week | Campaign | Social | CRM | Email | Insights |
|------|----------|--------|-----|-------|----------|
| 1 | Posts live | Manual reviews | — | — | — |
| 2 | 50K impressions | Auto-scoring | Tracking relationships | — | — |
| 3 | 100K impressions | Themes extracted | CRM dashboard | Sequences live | — |
| 4 | 150K impressions | Daily digest | Full pipeline | 500+ enrolled | Weekly suggestions |

**You know it's working when:**
- Dashboard shows all engagements in one place
- Email sequences auto-advance relationships
- Weekly insights suggest carousel topics
- Continuous improvement loop closes (carousel → social → email → improvement → better carousel)

