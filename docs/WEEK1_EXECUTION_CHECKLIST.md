# Week 1 Execution Checklist: Student Service Pilot Launch
**Status:** Board Approved 7-0  
**Week:** July 22-26, 2026 (Tue-Fri + next Mon)  
**Owner:** Founder (Akbar) + Team leads  

---

## TODAY (Tuesday, July 22 — 4 PM UTC)

### Immediate Actions (Next 2 hours)

- [ ] **Board resolution signed** — Get signatures on BOARD_RESOLUTION_APPROVED_2026_07_22.md
- [ ] **Email team announcement** — "Board approved. We're building this. Week 2 begins Monday."
- [ ] **Create project tracking** — Setup Jira/Linear with sprints
  - Sprint 1: Weeks 2-3 (Database + Foundation)
  - Sprint 2: Weeks 4-6 (Core Features)
- [ ] **Calendar blocks** — Schedule daily standups (10 AM CT, 15 min)
- [ ] **Slack channel** — #student-service-dev for team coordination

### Legal Engagement (Critical Path)

- [ ] **Send legal counsel engagement letter** — Include:
  - COPPA compliance requirements (13+ age verification, parental consent for under-13)
  - FERPA compliance (school data protection)
  - State privacy laws (Texas baseline, but apply broadly)
  - Student consent templates (needed before enrollment)
  - Parental consent forms (if applicable)
  - Timeline: Legal clearance needed by end of Week 3
  - Budget: $15-25K (estimate in engagement letter)

**Legal engagement template email:**

```
Subject: Legal Review Engagement: Daanaa Student Community-Service Pilot

Dear [Legal Counsel Name],

Daanaa board has approved a student community-service pilot program. 
We need legal review of the following before student enrollment (target: 
end of Week 3):

1. COPPA compliance (13+ age verification, parental consent for <13)
2. FERPA compliance (school data sharing, student records protection)
3. State student privacy laws (Texas, but consider national framework)
4. Student consent procedures
5. Parental consent forms
6. Nonprofit supervisor liability agreements
7. Data retention/deletion policies

Full context: DEVELOPMENT_PLAN_STUDENT_SERVICE_WITH_QA_FIXES.md

Timeline: Review complete by Week 3 (Aug 5). No student enrollment before 
legal clearance.

Please confirm availability and proposed timeline.

Best,
[Your Name]
```

### Engineering Leadership Brief

- [ ] **Schedule with backend lead** — 30 min sync
  - Share: STUDENT_SERVICE_IMPLEMENTATION_GUIDE.md
  - Share: STUDENT_SERVICE_API_SPEC.md
  - Confirm: Database migration plan for Week 2 Monday
  - Confirm: Backend Sprint 1 assignment (1 FTE)
  - Confirm: Week 2 sprint goals (database + auth foundation)

- [ ] **Schedule with frontend lead** — 30 min sync
  - Share: frontend/src/pages/StudentService/STRUCTURE.md
  - Confirm: Frontend Sprint 1 assignment (1 FTE + 0.3 designer)
  - Confirm: Week 2 sprint goals (setup + DiscoverPage)

- [ ] **Verify existing codebase access** — Both teams have:
  - Access to daanaa_api.py (backend reference)
  - Access to frontend/ (React/Tailwind patterns)
  - Access to database/ (migration templates)

### Operations/Partnerships Brief

- [ ] **Schedule with operations lead** — 30 min sync
  - Share: Partner recruitment targets (3-5 schools, 20 nonprofits)
  - Share: Houston focus (known relationships for founder)
  - Confirm: Week 1 partnership outreach begins (Thursday)
  - Confirm: Timeline for partner agreements (due Week 7)

---

## WEDNESDAY (July 23)

### Engineering Sprint Planning

- [ ] **Backend lead: Sprint 1 planning**
  - Review STUDENT_SERVICE_IMPLEMENTATION_GUIDE.md Week 2 section
  - List all tasks for Week 2 (database, Firebase, /api/student/* setup)
  - Assign story points, create Jira tickets
  - Identify blockers, dependencies, risks
  - Plan standup: 10 AM Thursday (team sync)

- [ ] **Frontend lead: Sprint 1 planning**
  - Review STUDENT_SERVICE_IMPLEMENTATION_GUIDE.md Week 2 section
  - List all tasks for Week 2 (setup, DiscoverPage, OpportunityCard)
  - Assign story points, create Jira tickets
  - Setup TypeScript types, create component stubs
  - Plan standup: 10 AM Thursday (team sync)

### Legal Review Kickoff

- [ ] **Confirm legal counsel engagement** — Received acceptance/timeline?
- [ ] **Send legal counsel context materials:**
  - BOARD_MEMO_STUDENT_SERVICE_INITIATIVE.md
  - database/migrations/024_student_service_tables.sql (schema overview)
  - STEWARDSHIP.md + DAANAA-CHARTER.md (principles to respect)
  - DEVELOPMENT_PLAN_STUDENT_SERVICE_WITH_QA_FIXES.md (timeline context)

- [ ] **Schedule legal review kickoff call** — Friday 3 PM with legal counsel
  - Clarify COPPA requirements (age verification, consent)
  - Clarify FERPA scope (what data can school share)
  - Discuss consent templates (who creates, who signs)
  - Confirm timeline for legal clearance (target: end Week 3)

### Partner Outreach Prep

- [ ] **Finalize Houston school list** — 3-5 targets
  - Confirm founder relationships
  - Prepare outreach email (brief, clear value prop)
  - Prepare preliminary partnership agreement (template)

- [ ] **Finalize nonprofit partner list** — 20 targets
  - Mix of sizes, causes, locations (Houston area)
  - Prepare outreach email
  - Prepare preliminary partnership agreement

---

## THURSDAY (July 24)

### Standup #1: Team Sync

**Attendees:** Backend lead, Frontend lead, Operations lead  
**Duration:** 15 minutes  
**Agenda:**
- [ ] Sprint 1 planning status (backend + frontend)
- [ ] Legal review kickoff status
- [ ] Partner recruitment prep status
- [ ] Questions/blockers
- [ ] Confirm Week 1 wrap-up plan (Friday)

### Engineering Milestones

- [ ] **Backend:** Sprint 1 Jira board created, all tasks assigned
- [ ] **Frontend:** Sprint 1 Jira board created, all tasks assigned
- [ ] **Database:** Migration checklist ready for Week 2 Monday deploy

### Partner Outreach Begins

- [ ] **Send school outreach emails** — 3-5 target schools
  - Subject: "Student Volunteer Service Program Pilot"
  - Mention: Free, verified records, helps students
  - Ask: 15-min call next week to discuss
  - Include: Preliminary partnership agreement (for review)

- [ ] **Begin nonprofit outreach prep** — Emails ready to send Friday/Monday
  - Prepare email list
  - Personalize first 5 outreach emails
  - Track responses in spreadsheet

---

## FRIDAY (July 25)

### Week 1 Wrap-Up

- [ ] **Daily standup (10 AM)** — Quick 10-min status
  - Backend: Sprint ready for Monday
  - Frontend: Sprint ready for Monday
  - Legal: Kickoff call scheduled
  - Operations: Partner emails sent, responses coming in

- [ ] **Legal review status** — Kickoff call feedback
  - [ ] Confirmed COPPA requirements
  - [ ] Confirmed FERPA compliance scope
  - [ ] Confirmed timeline for legal clearance
  - [ ] Next steps documented

### Week 1 Summary Document

- [ ] **Create WEEK1_SUMMARY.md** — Document:
  - Board resolution approved (7-0)
  - Engineering sprints ready (backend + frontend)
  - Legal review engaged and kicked off
  - Partner recruitment launched (emails sent)
  - Team synchronized and aligned
  - Week 2 ready to begin Monday

### Team Alignment Check

- [ ] **Verify all team members have:**
  - [ ] Access to all required files (architecture, API spec, guides)
  - [ ] Understand Week 1-6 timeline
  - [ ] Know their role (backend, frontend, operations, legal)
  - [ ] Know Week 2 sprint goals
  - [ ] Have Jira access and sprint board visibility
  - [ ] Know daily standup time (10 AM CT)

---

## MONDAY (July 29) — WEEK 2 BEGINS

### Development Sprint 1 Launch

- [ ] **Backend Sprint 1 Kickoff (9 AM)**
  - Database migration: Run 024_student_service_tables.sql
  - Verify: All 10 new tables created, 2 extended
  - Firebase auth: Setup student login endpoint
  - Verify: /api/student/* routes responding (even if 404 for unimplemented endpoints)

- [ ] **Frontend Sprint 1 Kickoff (9 AM)**
  - Setup StudentService directory structure
  - Create TypeScript types (student.ts, opportunity.ts, service-log.ts)
  - Create API client wrapper (studentApi.ts)
  - Create component stubs (OpportunityCard, OpportunitySearch)
  - Verify: React app builds without errors

- [ ] **Daily standup (10 AM)** — First of the week
  - Backend: Database migrated? Auth working?
  - Frontend: Types created? Components building?
  - Legal: Any blockers from initial review?
  - Operations: Partner call scheduled?

---

## Success Criteria for Week 1

✅ **Board resolution signed and filed**  
✅ **Legal counsel engaged with kickoff call scheduled**  
✅ **Engineering team briefed and sprints planned**  
✅ **Sprint 1 tasks created in Jira**  
✅ **Partner outreach launched (emails sent)**  
✅ **Team aligned on timeline and roles**  
✅ **No blockers preventing Week 2 start**  

---

## Blockers to Watch

| Risk | If This Happens | Then Do This |
|------|---|---|
| Legal counsel delays response | No response by Thu EOD | Call directly; escalate to board chair |
| School doesn't reply to outreach | No response by Fri | Try founder's existing contacts |
| Backend engineer unavailable | Can't start database migration | Founder provides support or hire temp |
| Frontend setup blocked | Can't build React app | Check Node/npm versions; verify dependencies |
| Jira not working | Can't track progress | Use Google Sheets as backup |

---

## Communication Plan

### Daily
- 10 AM CT standup (15 min) — Slack thread or Zoom
- Standup format: What I did / What I'm doing / Blockers
- Report to: Slack #student-service-dev

### Weekly
- Friday end-of-week wrap (15 min) — Review progress
- Review: Sprint board, legal updates, partner status
- Document: WEEK_SUMMARY.md (kept for record)

### Critical Updates
- If blocker emerges: Ping Slack immediately
- If partner responds: Update partner spreadsheet
- If legal clarifies: Update compliance checklist

### Board Checkpoint
- Week 9 checkpoint meeting (Aug 19)
- Prepare: Adoption metrics, go/no-go recommendation
- Report to: Board + full team

---

## Handoff to Week 2

**At end of Friday (July 25):**

- Backend lead has:
  - [ ] Sprint 1 tasks in Jira
  - [ ] Database migration script reviewed
  - [ ] Firebase auth plan documented
  - [ ] Week 2 Monday plan ready

- Frontend lead has:
  - [ ] Sprint 1 tasks in Jira
  - [ ] Component structure approved
  - [ ] TypeScript types planned
  - [ ] Week 2 Monday setup plan ready

- Operations lead has:
  - [ ] Partner list finalized
  - [ ] Outreach emails sent
  - [ ] Response tracking spreadsheet
  - [ ] Follow-up call plan for Week 2

- Legal counsel has:
  - [ ] All context materials
  - [ ] Kickoff meeting scheduled
  - [ ] Timeline committed (end Week 3 clearance)
  - [ ] First deliverables defined

---

## Who Owns What

| Area | Owner | Backup |
|------|-------|--------|
| Backend | Backend Lead | Founder (if engineer unavailable) |
| Frontend | Frontend Lead | Designer (for component feedback) |
| Legal/Compliance | External Counsel | Founder (oversight) |
| Partners/Operations | Operations Lead | Founder (decision-making) |
| Project Coordination | Founder | Operations Lead |

---

## Files to Share

**Send to engineering team (TODAY):**
- [ ] STUDENT_SERVICE_WEEK1_ARCHITECTURE_COMPLETE.md
- [ ] STUDENT_SERVICE_IMPLEMENTATION_GUIDE.md
- [ ] STUDENT_SERVICE_API_SPEC.md
- [ ] frontend/src/pages/StudentService/STRUCTURE.md
- [ ] database/migrations/024_student_service_tables.sql

**Send to legal counsel (TODAY):**
- [ ] BOARD_MEMO_STUDENT_SERVICE_INITIATIVE.md
- [ ] DEVELOPMENT_PLAN_STUDENT_SERVICE_WITH_QA_FIXES.md
- [ ] STEWARDSHIP.md + DAANAA-CHARTER.md
- [ ] database/migrations/024_student_service_tables.sql (schema preview)

**Send to operations lead (TODAY):**
- [ ] DEVELOPMENT_PLAN_STUDENT_SERVICE_WITH_QA_FIXES.md (weeks 7-9 section)
- [ ] Partner recruitment targets spreadsheet
- [ ] Partnership agreement templates

---

## Week 1 Complete When

✅ Board resolution signed  
✅ Legal counsel engaged + kickoff meeting scheduled  
✅ Engineering sprints planned + Jira ready  
✅ Partner outreach launched  
✅ All teams aligned on Week 2 plan  
✅ No blockers to Monday Week 2 launch  

**Then Monday: Engineering begins building.**

---

## Questions Before You Start?

**For engineering:** See STUDENT_SERVICE_IMPLEMENTATION_GUIDE.md  
**For legal:** See DEVELOPMENT_PLAN_STUDENT_SERVICE_WITH_QA_FIXES.md  
**For operations:** See partner recruitment section of plan  
**For anything else:** Ask. This is critical path.

---

**Week 1 Begins: NOW**  
**Week 2 Begins: Monday, July 29, 9 AM CT**  
**Pilot Launch: Week 10, Aug 26**  
**Pilot End: Week 22, October 28**  
**Board Decision: Week 23, October 29**  

**Go make it happen.** 🚀
