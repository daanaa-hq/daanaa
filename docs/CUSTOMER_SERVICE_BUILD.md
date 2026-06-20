# Daanaa Customer Service Build Log

## Day 1: Chatwoot Setup ✅ COMPLETE (Partial)

### What's Running
- **Chatwoot v3.5.0** on droplet:3000 (rails + sidekiq + postgres + redis)
- **Nginx reverse proxy** → support.daanaa.org (ready for DNS)
- **Admin setup:** Accessible via web UI setup wizard

### Next Steps (Same Session)
1. Access http://162.243.97.179:3000 → complete Chatwoot web setup
2. Create admin account through UI
3. Add daanaa@daanaa.org as inbox email
4. Configure basic routing rules (nonprofit claims, donor support, partner tickets)

### Day 2: Jambonz Voice IVR
- Set up on home server (Ryzen + R9700 GPU)
- Configure SIP trunk (Voxbeam / Plivo)
- Build nonprofit claim voice script:
  - "Press 1 to claim nonprofit page"
  - Collect EIN (DTMF) + domain email (speech recognition)
  - Create Chatwoot ticket automatically

### Day 3: n8n Email Triage  
- Email ingestion from daanaa@daanaa.org
- Intent detection: "How do I give" → donate link, "I volunteered" → LogVolunteerHours link
- FAQ bot: semantic search on common questions
- Auto-response rules (70-80% should be auto-handled)
- Route remaining to Chatwoot

### Day 4: Testing + Go-Live
- Test all flows end-to-end
- Set up Metabase dashboards (backlog, response time, escalation alerts)
- Launch phone number to nonprofits
- Monitor first week of usage

### Budget
- **Total:** $240–600/year (SIP trunk only)
- **Staff:** $0 (fully automated)
- **Timeline:** 4 days build, ongoing tuning

### Key Principle
**Automation-first:** Akbar handles exceptions only. Target: <1 hr/day on support.
