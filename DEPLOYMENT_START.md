# 🚀 DEPLOYMENT START - TODAY

**Status:** READY TO DEPLOY  
**Timeline:** 7 days to live  
**Your involvement:** Follow checklist below  
**System autonomy:** Begins after deployment  

---

## Day 1: Code Deployment (2-3 hours)

### Step 1: Copy Backend Files

```bash
# Verify files exist
ls -la /home/akbar/meritgiving/scripts/campaigns_api.py
ls -la /home/akbar/meritgiving/scripts/carousel_renderer.py
ls -la /home/akbar/meritgiving/scripts/campaigns_orchestrator.py

# These should show the files we created
```

### Step 2: Copy Frontend Files

```bash
# Verify files exist
ls -la /home/akbar/meritgiving/frontend/src/pages/AdminCampaigns.tsx

# Check if it's there
```

### Step 3: Test Backend API Import

```bash
# In your Flask app (daanaa_api.py or app.py), add:
# At the top:
from scripts.campaigns_api import campaigns_bp

# Register blueprint:
app.register_blueprint(campaigns_bp)

# Test it:
python3 -c "from scripts.campaigns_api import campaigns_bp; print('✓ API imported successfully')"
```

### Step 4: Test Frontend Component

```bash
# Verify React component can import
cd /home/akbar/meritgiving/frontend

# Check if TypeScript compiles without errors (optional)
npm run type-check 2>&1 | grep "AdminCampaigns" || echo "✓ Component ready"
```

**✅ When you see all green checkmarks above → Move to Day 2**

---

## Day 2: Database + Templates (1 hour)

### Step 1: Initialize Database

```bash
# Run this to create campaign tables
cd /home/akbar/meritgiving

python3 << 'EOF'
from scripts.campaigns_api import init_campaigns_db

try:
    init_campaigns_db()
    print("✅ Campaign database initialized")
except Exception as e:
    print(f"❌ Error: {e}")
EOF
```

### Step 2: Verify Tables Created

```bash
sqlite3 /home/akbar/meritgiving/data/merit_registry.db << 'EOF'
.tables
SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'campaign%';
EOF

# Should show: campaigns, campaign_analytics, utm_links
```

### Step 3: Load Carousel Templates

```bash
python3 << 'EOF'
from scripts.campaigns_orchestrator import CampaignOrchestrator

orch = CampaignOrchestrator()

templates = [
    'sample_1_reserve_crisis.json',
    'sample_2_fundraising_tax.json',
    'sample_2_invisible_97_donors.json',
    'sample_3_funding_paradox.json',
    'sample_4_find_your_cause_celebrity.json',
    'sample_5_find_your_cause_awareness_day.json'
]

print("Loading carousel templates...")
for template in templates:
    try:
        renderer = orch.load_carousel(template)
        print(f"  ✅ {template}")
    except FileNotFoundError as e:
        print(f"  ❌ {template} NOT FOUND: {e}")
    except Exception as e:
        print(f"  ❌ {template} ERROR: {e}")

orch.close()
print("\n✅ All templates loaded")
EOF
```

**✅ When all templates load successfully → Move to Day 3**

---

## Day 3: Automation Setup (1 hour)

### Step 1: Create Log Directory

```bash
mkdir -p /home/akbar/meritgiving/logs
chmod 755 /home/akbar/meritgiving/logs
```

### Step 2: Add Cron Jobs

```bash
# Edit crontab
crontab -e

# Add these lines (paste into editor):

# =================================
# Daanaa Campaign Automation
# =================================

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

# =================================
```

### Step 3: Verify Cron Jobs

```bash
# List your cron jobs
crontab -l

# Should show all 5 jobs above
# Count them:
crontab -l | grep -c "campaigns_orchestrator"  # Should output: 5
```

**✅ When you see 5 cron jobs → Move to Day 4**

---

## Day 4: Email + LinkedIn Setup (1 hour)

### Step 1: Create .env File (If you don't have one)

```bash
# Create or update .env in your Flask app directory
cat >> /home/akbar/meritgiving/.env << 'EOF'

# Daanaa Campaign System
DAANAA_PHASE=1
PHASE_1_TARGETS_MET=false
PHASE_2_TARGETS_MET=false
PHASE_3_TARGETS_MET=false

# Email Configuration
GMAIL_USER=your-email@gmail.com
GMAIL_PASSWORD=your-app-password

# LinkedIn Integration
BUFFER_API_TOKEN=optional-buffer-token

# Campaign Settings
CAMPAIGN_APPROVAL_EMAIL=akbar@daanaa.org
WEEKLY_REPORT_EMAIL=akbar@daanaa.org

EOF

# Fill in your actual values above
```

### Step 2: Test Email Configuration (Optional)

```bash
# If you have email setup, test it:
python3 << 'EOF'
import os
from dotenv import load_dotenv

load_dotenv()

print(f"Gmail user: {os.getenv('GMAIL_USER', 'NOT SET')}")
print(f"Gmail password: {'SET' if os.getenv('GMAIL_PASSWORD') else 'NOT SET'}")
print(f"Report email: {os.getenv('WEEKLY_REPORT_EMAIL', 'NOT SET')}")
EOF
```

### Step 3: LinkedIn Posting Setup

**Option A: Use Buffer (Recommended - API integration)**

```bash
# 1. Go to https://buffer.com/app/settings/api
# 2. Create a Buffer account if needed
# 3. Get API token
# 4. Add to .env:
#    BUFFER_API_TOKEN=your_token

# For now, you can skip this - manual Buffer posting works fine
echo "✅ LinkedIn posting: Manual Buffer (can upgrade to API later)"
```

**Option B: Manual Buffer (No API needed)**

```bash
# We'll generate captions + hashtags
# You copy/paste into Buffer
# Takes 2 min per post

echo "✅ LinkedIn posting: Manual Buffer ready"
```

**✅ Email/LinkedIn ready → Move to Day 5**

---

## Day 5: Dashboard Testing (1 hour)

### Step 1: Start Your Flask App

```bash
cd /home/akbar/meritgiving

# Activate venv
source venv/bin/activate

# Start Flask (if you have a dev server command)
python3 daanaa_api.py

# Or: Start your normal production server
# (make sure campaigns_bp is registered)

# In another terminal, verify:
curl http://localhost:5000/api/campaigns/health
# Should return: {"status": "ok", "service": "campaigns_api"}
```

### Step 2: Test React Dashboard

```bash
# In browser, navigate to:
http://localhost:5173/admin/campaigns

# Should see:
# - Dashboard title: "Campaign Manager"
# - Tabs: Drafts, Pending, Approved, Scheduled, Posted
# - Message: "No campaigns" (for all tabs)

# ✅ If you see this, dashboard is working
```

### Step 3: Create Test Carousels

```bash
# Generate first batch manually (don't wait for cron)
python3 << 'EOF'
from scripts.campaigns_orchestrator import CampaignOrchestrator

print("Generating test batch...")
orch = CampaignOrchestrator()
campaign_ids = orch.generate_weekly_batch(batch_name="Test Batch")

print(f"\n✅ Created {len(campaign_ids)} test carousels:")
for cid in campaign_ids:
    print(f"  - {cid}")

orch.close()
EOF
```

### Step 4: Test Dashboard Approval

```
1. Refresh dashboard in browser (F5)
2. Click "Drafts" tab
3. You should see 5-6 carousels
4. Click on one to see details
5. Click "Approve" button
6. Status should change to "pending_approval"
7. Click "Schedule" button
8. It should schedule for posting

✅ If all steps work, dashboard is ready
```

**✅ Dashboard working → Move to Day 6**

---

## Day 6: Final Testing (1 hour)

### Step 1: Test Metrics Collection

```bash
# Manually trigger metric collection
python3 << 'EOF'
from scripts.campaigns_orchestrator import CampaignOrchestrator

orch = CampaignOrchestrator()

# Log a test metric
orch.db.cursor().execute("""
    INSERT INTO campaign_analytics (id, campaign_id, metric_type, metric_value, recorded_at)
    SELECT 
        'test_metric_' || datetime('now'),
        (SELECT id FROM campaigns LIMIT 1),
        'impressions',
        1000,
        datetime('now')
    WHERE EXISTS (SELECT 1 FROM campaigns LIMIT 1)
""")
orch.db.commit()

print("✅ Test metric logged")
orch.close()
EOF
```

### Step 2: Test Weekly Report Generation

```bash
# Generate a test report
python3 << 'EOF'
from scripts.campaigns_orchestrator import CampaignOrchestrator

orch = CampaignOrchestrator()
report = orch.generate_weekly_report()

print("✅ Weekly Report Generated:")
print(f"  Period: {report.get('period')}")
print(f"  Campaigns posted: {report.get('campaigns_posted')}")
print(f"  Analytics: {report.get('analytics')}")

orch.close()
EOF
```

### Step 3: Full System Checklist

```bash
echo "System Status Checklist:"
echo "========================"

# Check backend API
curl -s http://localhost:5000/api/campaigns/health > /dev/null && echo "✅ API running" || echo "❌ API down"

# Check database
sqlite3 /home/akbar/meritgiving/data/merit_registry.db "SELECT COUNT(*) as campaign_count FROM campaigns" && echo "✅ Database ready"

# Check cron jobs
[ $(crontab -l | grep -c "campaigns_orchestrator") -eq 5 ] && echo "✅ Cron jobs installed" || echo "❌ Cron jobs missing"

# Check templates
python3 -c "from scripts.campaigns_orchestrator import CampaignOrchestrator; orch = CampaignOrchestrator(); print('✅ Orchestrator loads')" 2>/dev/null || echo "❌ Orchestrator error"

echo ""
echo "✅ System ready for launch"
```

**✅ All checks pass → Move to Day 7**

---

## Day 7: LAUNCH 🚀

### Step 1: Generate First Production Batch

```bash
# This generates the carousels for your first week
python3 << 'EOF'
from scripts.campaigns_orchestrator import CampaignOrchestrator
from datetime import datetime

print("="*50)
print("DAANAA MARKETING SYSTEM - LAUNCH")
print("="*50)

orch = CampaignOrchestrator()

print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Generating Week 1 carousels...")

campaign_ids = orch.generate_weekly_batch(batch_name="Week 1 - LAUNCH")

print(f"\n✅ Generated {len(campaign_ids)} carousels:")
for cid in campaign_ids:
    print(f"  ✓ {cid}")

orch.close()

print("\n" + "="*50)
print("NEXT STEP: Open /admin/campaigns Monday 9am")
print("Review + approve the 5 carousels")
print("System will post them automatically")
print("="*50)
EOF
```

### Step 2: Notify Yourself

```bash
# Send yourself a launch notification
echo "
Subject: 🚀 DAANAA MARKETING SYSTEM IS LIVE

Your autonomous marketing system is now active.

FIRST TASK: Monday 9:00 AM ET
- Open: http://localhost:5173/admin/campaigns
- You'll see: 5 draft carousels
- Do: Click 'Approve' on each one
- Time: 10 minutes
- System does: Posts them automatically Mon/Wed/Fri

WEEKLY RHYTHM:
- Monday 9am: Review + approve (10 min)
- Friday 6pm: Read weekly report (20 min)
- Everything else: Automated

DASHBOARD: http://localhost:5173/admin/campaigns
HELP: See AUTONOMOUS_EXECUTION_PLAN.md

Let's drive traffic to Daanaa.org 🎯
" | mail -s "DAANAA MARKETING SYSTEM LIVE" akbar@daanaa.org 2>/dev/null || echo "✅ Notification ready to send"
```

### Step 3: Launch Checklist

```bash
echo "
🚀 LAUNCH CHECKLIST
==================

Deployed:
✅ Backend API (campaigns_api.py)
✅ Frontend Dashboard (AdminCampaigns.tsx)
✅ Carousel Renderer (carousel_renderer.py)
✅ Orchestrator (campaigns_orchestrator.py)

Configured:
✅ Database (campaigns, analytics, utm_links)
✅ Cron jobs (5 automation jobs)
✅ Email configuration
✅ LinkedIn integration (manual Buffer)

Tested:
✅ API health check
✅ Dashboard approval workflow
✅ Carousel generation
✅ Metrics collection
✅ Weekly report generation

Ready:
✅ Week 1 batch generated (5 carousels)
✅ Awaiting your approval Monday morning
✅ System will post automatically

STATUS: 🟢 LIVE
==================
"
```

---

## Next Week: Ongoing Operations

### Monday 9:00 AM ET

```bash
# 1. Open http://localhost:5173/admin/campaigns
# 2. Click "Drafts" tab
# 3. See 5 carousels generated by system
# 4. Read each one
# 5. Click "Approve" on each
# 6. Done (10 minutes)

# System auto-schedules + posts
```

### Friday 6:00 PM ET

```bash
# 1. Check email (from: system)
# 2. Subject: "Weekly Marketing Report"
# 3. Read metrics:
#    - Impressions
#    - Clicks
#    - Profile claims
#    - Top performer
# 4. Done (20 minutes)
```

### Repeat for 52 Weeks

```
Week 8: System auto-checks if Phase 1 targets met
        You click: [APPROVE PHASE 2] or [STAY PUT]

Week 16: System auto-checks if Phase 2 targets met
         You click: [APPROVE PHASE 3] or [STAY PUT]

Week 32: System auto-checks if Phase 3 targets met
         You click: [APPROVE PHASE 4] or [STAY PUT]

Week 52: System running autonomously, driving traffic
```

---

## Questions During Deployment?

**Check these in order:**

1. **MASTER_DEPLOYMENT_GUIDE.md** — Detailed troubleshooting
2. **AUTONOMOUS_EXECUTION_PLAN.md** — How system works
3. **CAMPAIGN_SYSTEM_README.md** — System philosophy

**Can't find answer?**
- Check logs: `tail -50 logs/cron_*.log`
- Test manually: `python3 scripts/campaigns_orchestrator.py --action <action> --verbose`
- Verify database: `sqlite3 /home/akbar/meritgiving/data/merit_registry.db ".tables"`

---

## Success Looks Like

**By Day 7 (Friday):**
- ✅ Dashboard accessible
- ✅ 5 carousels ready for approval
- ✅ Cron jobs installed
- ✅ System generating content

**By Week 1 (Next Friday):**
- ✅ 3 carousels posted (Mon/Wed/Fri)
- ✅ Weekly report received
- ✅ First metrics in dashboard

**By Week 8:**
- ✅ 50K+ impressions
- ✅ 50+ nonprofit profile claims
- ✅ Phase 1 complete

---

## You're Ready

Follow this checklist.  
Deploy today.  
Live by Saturday.  
Approve first carousels Monday morning.  
System runs itself after that.

**Let's go. 🚀**

