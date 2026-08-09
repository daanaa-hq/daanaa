# Master Deployment Guide: Daanaa Marketing Automation

**Status:** Ready to Deploy  
**Complexity:** Medium (straightforward setup)  
**Timeline:** 1 week to live  
**Your time:** 30 min/week after launch  
**Autonomy:** 99% (system runs itself)

---

## What You're Deploying

**A complete autonomous marketing system that:**
1. Generates carousels automatically
2. Posts them on schedule
3. Sends emails automatically
4. Publishes blog articles automatically
5. Collects metrics automatically
6. Reports weekly automatically
7. Escalates phases automatically
8. Pauses underperformers automatically
9. Scales winners automatically

**Your job:** Approve carousels (Monday) + read report (Friday)

---

## 7-Day Deployment Schedule

### Day 1: Code Deployment

**Backend Setup**

```bash
# Copy files to your Flask app
cp scripts/campaigns_api.py app/
cp scripts/campaigns_orchestrator.py scripts/
cp scripts/carousel_renderer.py scripts/

# Update Flask app.py
# In app.py:
from scripts.campaigns_api import campaigns_bp
app.register_blueprint(campaigns_bp)

# Create database tables
python3 -c "from scripts.campaigns_api import init_campaigns_db; init_campaigns_db()"
```

**Frontend Setup**

```bash
# Copy React component
cp frontend/src/pages/AdminCampaigns.tsx frontend/src/pages/

# Update React routing (in main router)
# Add route:
{
  path: "/admin/campaigns",
  element: <AdminCampaigns />,
  requiresAuth: true
}

# Run build
cd frontend && npm run build
```

**Verify:**
```bash
# Test backend API
curl http://localhost:5000/api/campaigns/health
# Expected: {"status": "ok", "service": "campaigns_api"}

# Test frontend
# Navigate to: http://localhost:5173/admin/campaigns
# Should see: Empty campaigns dashboard
```

---

### Day 2: Template Loading

**Load carousel templates into system**

```bash
# Copy carousel JSON files to system
cp scripts/linkedin/carousels/sample_*.json /home/akbar/meritgiving/scripts/linkedin/carousels/

# Initialize templates in database
python3 << 'EOF'
from scripts.campaigns_orchestrator import CampaignOrchestrator

orch = CampaignOrchestrator()

# Verify all 6 templates can load
templates = [
    'sample_1_reserve_crisis.json',
    'sample_2_fundraising_tax.json',
    'sample_2_invisible_97_donors.json',
    'sample_3_funding_paradox.json',
    'sample_4_find_your_cause_celebrity.json',
    'sample_5_find_your_cause_awareness_day.json'
]

for template in templates:
    try:
        renderer = orch.load_carousel(template)
        print(f"✓ {template}: {renderer.title}")
    except Exception as e:
        print(f"✗ {template}: {e}")

orch.close()
EOF
```

---

### Day 3: Cron Jobs + Automation Setup

**Set up automated processes**

```bash
# Edit crontab
crontab -e

# Add these lines:

# Sunday 12:00 AM UTC - Generate weekly carousels
0 0 * * 0 cd /home/akbar/meritgiving && python3 scripts/campaigns_orchestrator.py --action generate_weekly_batch >> logs/cron_carousel_generation.log 2>&1

# Daily 6:00 PM UTC - Collect metrics
0 18 * * * cd /home/akbar/meritgiving && python3 scripts/campaigns_orchestrator.py --action collect_daily_metrics >> logs/cron_metrics.log 2>&1

# Friday 8:00 PM UTC - Generate weekly report
0 20 * * 5 cd /home/akbar/meritgiving && python3 scripts/campaigns_orchestrator.py --action generate_weekly_report >> logs/cron_weekly_report.log 2>&1

# Monday 6:00 AM UTC (Week 8, 16, 32) - Check phase escalation
0 6 * * 1 cd /home/akbar/meritgiving && python3 scripts/campaigns_orchestrator.py --action check_phase_escalation >> logs/cron_phase_check.log 2>&1

# Every 5 minutes - Monitor posted campaigns
*/5 * * * * cd /home/akbar/meritgiving && python3 scripts/campaigns_orchestrator.py --action monitor_posted_campaigns >> logs/cron_monitor.log 2>&1

# Verify
crontab -l  # Should show 5 new entries
```

---

### Day 4: Email Configuration

**Set up weekly report emails**

```python
# Update campaigns_api.py to include email sending

# Add to imports:
from flask_mail import Mail, Message
import os

# Configure mail
mail = Mail(app)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('GMAIL_USER')
app.config['MAIL_PASSWORD'] = os.getenv('GMAIL_PASSWORD')

# Test email
def send_weekly_report(email_address, report_data):
    msg = Message(
        subject='Weekly Marketing Report',
        recipients=[email_address],
        body=format_report_email(report_data)
    )
    mail.send(msg)

# In orchestrator:
orchestrator.email_recipient = 'akbar@daanaa.org'
```

**Environment variables to set:**
```bash
# In your .env file:
GMAIL_USER=your-gmail@gmail.com
GMAIL_PASSWORD=your-app-password  # Use Gmail app password, not regular password
DAANAA_PHASE=1
PHASE_1_TARGETS_MET=false
```

---

### Day 5: LinkedIn Integration

**Set up LinkedIn posting automation**

**Option A: Buffer API (Recommended)**

```bash
# Get Buffer API token from https://buffer.com/app/settings/api
# Add to .env:
BUFFER_API_TOKEN=your_token_here

# Update campaigns_api.py to integrate Buffer:
import requests

def post_to_linkedin_buffer(caption, hashtags, scheduled_time):
    url = "https://api.bufferapp.com/1/updates/create.json"
    data = {
        'profile_id': 'linkedin_profile_id',
        'text': f"{caption}\n\n{' '.join(hashtags)}",
        'scheduled_at': int(scheduled_time.timestamp()),
        'token': os.getenv('BUFFER_API_TOKEN')
    }
    response = requests.post(url, data=data)
    return response.json()
```

**Option B: Manual Buffer (No API)**

```bash
# System generates carousels + captions
# You copy/paste into Buffer manually (2 min per post)
# Pros: Simple, no API needed
# Cons: Manual step each week

# System provides:
# - Caption (copy-ready)
# - Hashtags (copy-ready)
# - Scheduled times (recommended)
# You: Paste into Buffer, schedule, done
```

**Test:**
```bash
python3 << 'EOF'
from scripts.campaigns_orchestrator import CampaignOrchestrator

orch = CampaignOrchestrator()
campaign = orch.load_carousel('sample_1_reserve_crisis.json')
caption = campaign.render_linkedin_caption()
print("LinkedIn Caption:")
print(caption)
print("\nUTM Link:")
utm = orch.generate_utm_link('https://daanaa.org/directory', 'test_campaign', 'Sample 1')
print(utm)
EOF
```

---

### Day 6: Dashboard Testing

**Test the approval workflow**

```bash
# 1. Navigate to http://localhost:5173/admin/campaigns
# 2. You should see: "No campaigns yet"
# 3. Manually create test carousel:

python3 << 'EOF'
from scripts.campaigns_orchestrator import CampaignOrchestrator

orch = CampaignOrchestrator()
campaign_ids = orch.generate_weekly_batch()
print(f"Created {len(campaign_ids)} test carousels")
orch.close()
EOF

# 4. Refresh dashboard
# 5. You should see 6 draft carousels
# 6. Click "Approve" on one
# 7. Verify status changes to "pending_approval"
# 8. Verify scheduled time appears
# 9. Verify UTM link generated
```

---

### Day 7: Go Live

**Final checklist before launch**

- [ ] Backend API deployed and responding
- [ ] Frontend dashboard accessible
- [ ] Database tables created
- [ ] 6 carousel templates loaded
- [ ] Cron jobs scheduled (verify with `crontab -l`)
- [ ] Email configuration working (test send)
- [ ] LinkedIn integration working (Buffer API or manual ready)
- [ ] Dashboard approval workflow tested
- [ ] Metrics collection tested
- [ ] Weekly report email tested
- [ ] Stewardship validation working

**Launch:**

```bash
# Create first batch
python3 << 'EOF'
from scripts.campaigns_orchestrator import CampaignOrchestrator

orch = CampaignOrchestrator()
campaign_ids = orch.generate_weekly_batch(batch_name="Week 1 Launch")
print(f"✓ Created {len(campaign_ids)} carousels for launch")
print("→ Open /admin/campaigns to review and approve")
orch.close()
EOF
```

**Notify yourself:**
```
Subject: Daanaa Marketing Automation is LIVE

First task: Open /admin/campaigns Monday 9am
You'll see 6 carousels ready for review + approval

Timeline:
- Monday 9am: You review + approve (10 min)
- Tuesday 2am: System schedules to LinkedIn
- Mon/Wed/Fri: Carousels post automatically
- Friday 6pm: Weekly report email arrives

Your job: 30 min/week (Monday + Friday)
System job: Everything else (99% automated)

Dashboard: http://localhost:5173/admin/campaigns
```

---

## Post-Launch Operations

### Week 1-4: Monitor & Learn

**Your weekly schedule:**

**Monday 9:00 AM ET (10 min)**
```
1. Open /admin/campaigns
2. See 5-6 draft carousels
3. Read each one (skim copy, verify stats)
4. Click "Approve" ✅ for each one
5. Done
```

**Friday 6:00 PM ET (20 min)**
```
1. Check email: Weekly Report
2. Read metrics:
   - Impressions this week
   - Engagement rate
   - Clicks to daanaa.org
   - Nonprofit profile claims
   - Top performing carousel
3. Note: What worked this week?
4. Optional: Reply with thoughts for next week
```

**System does:**
- Sunday: Generates carousels
- Tuesday: Schedules to LinkedIn
- Mon/Wed/Fri: Posts automatically
- Daily: Collects metrics
- Friday: Generates report + sends to you

---

### Week 8: Phase 1 → Phase 2 Decision

**System automatically checks:**
```
Targets:
- Impressions: 50,000+? ✅ YES
- Clicks: 200+? ✅ YES
- Claims: 50+? ✅ YES

RESULT: PHASE 1 PASSED
Next: Enable email distribution?

[APPROVE PHASE 2] [STAY ON PHASE 1]
```

**You decide:** Click one button

**If approved:**
- Email digest generation begins
- Wednesday: Weekly email starts going out
- Same approval workflow + metrics

---

### Week 16: Phase 2 → Phase 3 Decision

**System automatically checks:**
```
Targets:
- Email open rate: 25%+? ✅ YES
- Email CTR: 5%+? ✅ YES
- Claims from email: 100+? ✅ YES

RESULT: PHASE 2 PASSED
Next: Start blog article publishing?

[APPROVE PHASE 3] [STAY ON PHASE 2]
```

**If approved:**
- Blog article publishing begins
- Thursday: First article goes live
- SEO optimization automatic
- Same metrics tracking

---

### Week 32: Phase 3 → Phase 4 Decision

**System automatically checks:**
```
Targets:
- Blog visitors: 10,000+? ✅ YES
- Blog clicks to directory: 500+? ✅ YES
- Claims from blog: 200+? ✅ YES

RESULT: PHASE 3 PASSED
Next: Paid ads + partnerships?

⚠️  Phase 4 requires budget: $200-400/week for ads

[APPROVE PHASE 4] [STAY ON PHASE 3] [WAIT FOR BUDGET]
```

---

## Troubleshooting

### No carousels generated (Sunday passes, nothing appears)

**Check:**
```bash
# 1. Check cron job ran
grep "carousel_generation" /var/log/syslog  # or check logs

# 2. Check database
sqlite3 /home/akbar/meritgiving/data/merit_registry.db
SELECT COUNT(*) FROM campaigns WHERE status='draft';  # Should be 5-6

# 3. Check error log
tail -50 logs/cron_carousel_generation.log

# 4. Manual test
python3 scripts/campaigns_orchestrator.py --action generate_weekly_batch --verbose
```

---

### Dashboard shows no drafts

**Check:**
```bash
# 1. Frontend connected to API?
# In browser console:
fetch('http://localhost:5000/api/campaigns/batch/list')
  .then(r => r.json())
  .then(d => console.log(d))  # Should show campaigns

# 2. Is the API running?
curl http://localhost:5000/api/campaigns/health

# 3. Did carousel generation run?
sqlite3 /home/akbar/meritgiving/data/merit_registry.db
SELECT * FROM campaigns LIMIT 1;
```

---

### Metrics not showing

**Check:**
```bash
# 1. Manual metric logging
python3 << 'EOF'
from scripts.campaigns_api import get_db
from datetime import datetime

conn = get_db()
cursor = conn.cursor()

# Get first campaign
cursor.execute("SELECT id FROM campaigns WHERE status='posted' LIMIT 1")
campaign_id = cursor.fetchone()[0]

# Log a test metric
cursor.execute("""
    INSERT INTO campaign_analytics (id, campaign_id, metric_type, metric_value)
    VALUES (?, ?, 'impressions', 1000)
""", (f"{campaign_id}_test", campaign_id))

conn.commit()
conn.close()

print(f"✓ Logged test metric for {campaign_id}")
EOF

# 2. Check if weekly report generates
python3 scripts/campaigns_orchestrator.py --action generate_weekly_report --verbose
```

---

### Email not sending

**Check:**
```bash
# 1. Is Gmail configured?
echo $GMAIL_USER  # Should show email
echo $GMAIL_PASSWORD  # Should be masked

# 2. Test email sending
python3 << 'EOF'
from flask_mail import Message
from app import app, mail

with app.app_context():
    msg = Message(
        subject='Test Email',
        recipients=['akbar@daanaa.org'],
        body='Test body'
    )
    try:
        mail.send(msg)
        print("✓ Email sent")
    except Exception as e:
        print(f"✗ Error: {e}")
EOF

# 3. Check logs
tail -50 logs/cron_*.log
```

---

## Quick Commands (Daily Use)

**Check system status:**
```bash
# Are cron jobs running?
crontab -l

# Any errors in logs?
tail -20 logs/cron_*.log

# Database health
sqlite3 /home/akbar/meritgiving/data/merit_registry.db ".tables"

# Latest carousels created
sqlite3 /home/akbar/meritgiving/data/merit_registry.db "SELECT title, status, created_at FROM campaigns ORDER BY created_at DESC LIMIT 5;"
```

**Generate batch manually (if cron fails):**
```bash
python3 scripts/campaigns_orchestrator.py --action generate_weekly_batch --verbose
```

**Send weekly report manually:**
```bash
python3 scripts/campaigns_orchestrator.py --action generate_weekly_report --verbose --email akbar@daanaa.org
```

**Check phase escalation:**
```bash
python3 scripts/campaigns_orchestrator.py --action check_phase_escalation --verbose
```

---

## Success Metrics (Phase 1)

**If you're on track:**
- Week 2: 10-15K impressions
- Week 4: 25-30K impressions
- Week 6: 40-50K impressions
- Week 8: 50K+ impressions
- By week 8: 50+ nonprofit profile claims

**If you're behind:**
- Week 4: < 10K impressions → Adjust copy
- Week 6: < 25K impressions → Try different carousel
- Week 8 decision: Miss targets → Extend Phase 1 + refine

---

## Final Deployment Checklist

**Pre-Launch**
- [ ] Backend API deployed
- [ ] Frontend dashboard working
- [ ] Database initialized
- [ ] 6 carousel templates loaded
- [ ] Cron jobs scheduled
- [ ] Email configured
- [ ] LinkedIn integration ready
- [ ] All systems tested

**Launch Day**
- [ ] Generate first batch
- [ ] You review + approve Monday morning
- [ ] First posts go live
- [ ] Collect first metrics

**First Week**
- [ ] 3 carousels posted (Mon/Wed/Fri)
- [ ] Metrics visible in dashboard
- [ ] Weekly report email arrives Friday
- [ ] You check system health

**Ongoing**
- [ ] 30 min/week (Monday + Friday)
- [ ] System runs itself
- [ ] Escalate phases automatically

---

## Support & Questions

**If something breaks:**
1. Check troubleshooting section above
2. Check logs: `tail -100 logs/cron_*.log`
3. Manual test the failing action
4. Verify database integrity

**If you need changes:**
- Modify carousel copy: Edit JSON files in `scripts/linkedin/carousels/`
- Change posting schedule: Edit crontab
- Adjust metrics targets: Edit phase thresholds in orchestrator.py
- New content type: Add to content_pipeline (email, blog, etc.)

---

**You're ready to deploy. System will handle the rest.**

When you're ready: Deploy, launch, and let the machine work.

Your job: Approve (Monday) + review (Friday).

System's job: Everything else.

**Go live when ready. I'll help with any issues.**
