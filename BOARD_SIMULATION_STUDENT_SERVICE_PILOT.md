# BOARD SIMULATION: Student Community-Service Initiative
**Simulated Board Meeting:** July 22, 2026  
**Participants:** Founder, Board Chair, Education/Youth Sector Expert, Nonprofit Operations Director, Privacy/Legal Advisor, Impact Investor

---

## OPENING REMARKS (Founder - 5 min)

**Founder presents:** We've built Daanaa as a discovery platform. We've successfully deployed nonprofit dashboards, volunteer-hours tracking, and staff management tools. What we haven't solved yet is how to convert discovery into sustained engagement.

This proposal takes what we've built and extends it to serve students, schools, and nonprofits through community service. It's not a pivot. It's applying our existing infrastructure to a different user segment.

I'm asking for authorization to run a 90-day pilot in Houston with 3-5 schools and 20 nonprofits. If it works, we have a new product line. If it doesn't, we've learned something valuable at minimal cost.

---

## BOARD MEMBER REACTIONS

### BOARD CHAIR (Cautious but Intrigued)
**Initial reaction:** "This is thoughtful and scoped tightly. I like that you're asking for authorization to explore, not to commit to national expansion."

**Questions:**
1. **Resource allocation:** "What's the opportunity cost? Are we pulling product/engineering from core Daanaa work?"
   - *Answer:* 3 FTE during development (6-8 weeks), 2.5 FTE during pilot. We can sustain this alongside core work if we defer lower-priority initiatives.

2. **Why Houston specifically?** "Why not pilot in a city where you already have nonprofit relationships?"
   - *Answer:* Houston has diverse nonprofit ecosystem, known to founder, established relationships with schools through previous work, represents mid-size market (not too small, not too large for pilot learning).

3. **Exit criteria:** "What does failure look like? When would you recommend we pause this?"
   - *Answer:* If fewer than 2 schools or 10 nonprofits participate; if pilot enrollment stays below 50 students; if verification overhead exceeds 30 minutes per hour submitted; if significant privacy/compliance issues emerge. Board would receive early warning at week 9.

---

### EDUCATION/YOUTH SECTOR EXPERT
**Initial reaction:** "This fills a real gap. There's huge demand for verified volunteer records in schools."

**Questions:**
1. **School adoption:** "Will schools actually use this? How do you get them to care?"
   - *Answer:* Start with schools where founder has existing relationships (path of least resistance). School benefit is clear: students get verified records without school doing work. We handle verification; school just reviews/approves.

2. **Age and COPPA:** "You're starting at 13+, which sidesteps COPPA questions. Smart. But what happens if you want to expand to 12-year-olds or younger?"
   - *Answer:* Pilot phase 1 is 13+ only—that gives us clearer COPPA exemption and minimizes risk. Our week-2 legal review will determine whether under-13 expansion with parental consent is feasible. But no enrollment under 13 will occur without explicit legal clearance. That's a hard boundary until we have independent counsel sign off. Board will see the legal findings in our week-9 update.

3. **Comparison to existing programs:** "How is this different from VolunteerHub, iServe, or other platforms?"
   - *Answer:* Those platforms are volunteer-management tools built for nonprofits. We're starting with discovery (students find orgs via Daanaa) and adding service tracking. We're unique in connecting students to 1.7M organizations and linking it to nonprofit operations.

4. **Nonprofit readiness:** "Will nonprofits want this? They're already stretched."
   - *Answer:* Pilot limited to nonprofits where founder has relationships—they're motivated. Tools are free. We handle student signup, hour logging, and initial verification. Nonprofit just approves or rejects. Benefit: access to student volunteers without recruiting overhead.

---

### NONPROFIT OPERATIONS DIRECTOR
**Initial reaction:** "I'm skeptical. This could become a support burden for nonprofits."

**Questions:**
1. **Nonprofit liability:** "If a nonprofit supervisor verifies false hours, are they liable? What's our liability?"
   - *Answer:* Nonprofit bears responsibility for their supervisor's verification (standard nonprofit model). Daanaa is record-keeper. We include liability language in agreements. Covered by nonprofit's insurance; we maintain audit trail. Legal review will confirm indemnification.

2. **Supervisor overhead:** "How long does it take a nonprofit supervisor to verify an hour submission?"
   - *Answer:* Our estimate: 2-3 minutes (click, confirm, submit). We'll measure this during pilot. If it's longer, design is broken.

3. **Duplicate/fraud detection:** "You mentioned duplicate-hour prevention. How?"
   - *Answer:* System flags if same student + same org + same date appears twice. Also flags outliers (student claims 16 hours in one shift). Nonprofit reviews flagged submissions. Random audits (5-10%) verify supervisor decisions.

4. **What if a nonprofit gets overwhelmed with student submissions?"
   - *Answer:* Pilot size limits this (max 5-10 students per nonprofit in first semester). We monitor. If org is getting 100+ requests/month, that's success—we help them scale or recruit more supervisors.

---

### PRIVACY/LEGAL ADVISOR
**Initial reaction:** "Good instincts on the legal and privacy side, but you need to move faster on compliance."

**Questions:**
1. **COPPA timeline:** "You can't enroll students until COPPA review is done. How confident are you that you're compliant?"
   - *Answer:* Confident because: (a) 13+ is above COPPA jurisdiction, (b) school-mediated enrollment means no direct targeting of minors, (c) parental consent for under-18s provides extra protection. But independent legal review will confirm. Scheduling it for week 2.

2. **FERPA and school data:** "Are you collecting student educational records? If yes, FERPA applies."
   - *Answer:* No educational records collected. We collect: name, age, school affiliation, service commitment. School never provides grades, test scores, disciplinary records. Service record is student-initiated, not school-created. Still need FERPA confirmation, but lower risk than I initially thought.

3. **Data minimization:** "You say you're collecting minimal data. Are you really? Walk me through what data persists."
   - *Answer:* Per student: name, age, school, date of birth (for age verification), service commitment, hours submitted, supervisor confirmation, certificate. That's it. No browsing history, no interests, no peer network. Deleted upon student request. And critically: no data sharing with vendors, partners, or any commercial entity, regardless of partnership depth. That's Charter Promise #3. Partnerships are operational only—nonprofit recruiting, school coordination—never data-access relationships.

4. **Student access and deletion rights:** "If a student wants to delete their record, how far back can they go?"
   - *Answer:* Student can delete unverified submissions anytime. Verified records can be deleted by student request within 90 days; after that, aggregate data persists (for impact reporting) but identified record is de-identified.

5. **Dispute resolution confidentiality:** "What if a nonprofit and student disagree about hours? How is that handled privately?"
   - *Answer:* Disputes handled through school liaison (school admin is intermediary). Daanaa staff review if needed, but student and nonprofit identities are protected. No public record of dispute.

---

### IMPACT INVESTOR
**Initial reaction:** "This is a mission-aligned feature. But let me understand the business case."

**Questions:**
1. **Revenue model:** "Are you charging schools or nonprofits for this?"
   - *Answer:* Pilot is free. Post-pilot, potential models: (a) freemium (schools pay for advanced reporting), (b) nonprofit subscription (Daanaa+ with student discovery), (c) school contracts. No decision yet. Pilot will inform which model users prefer.

2. **Scale potential:** "If this works in Houston, how fast can it grow nationally?"
   - *Answer:* Depends on network effects. If schools see value, they evangelize (peer network). If nonprofits see value, they attract more schools. If students see value, schools come to us. Probably 2-3 years to regional scale (Texas, Southwest), 5+ years to national. This pilot tests assumptions. All expansion respects Charter constraints and requires board approval.

3. **Charter compliance on future revenue:** "The memo mentions freemium and subscription models. How do we ensure Charter Promise #5 (never charge for platform) is maintained?"
   - *Answer:* Good question—that's exactly why we're asking for board authorization, not a blank check. Core student service (discovery, logging, verification, certification) will remain free under Charter. Only advanced features beyond core (custom analytics, premium reporting) may have paid options, and even those require board approval before launch. This pilot will test what users want; the board decides what we monetize.

3. **Cost structure:** "What's the cost per verified hour? How does that compare to existing platforms?"
   - *Answer:* During pilot, high cost (overhead + development amortized across small base). Estimate: $10-15 per verified hour. As scale grows: $1-3 per verified hour (mostly staff audits and dispute resolution). Existing platforms: $5-20/hour. We think we can be competitive.

4. **Competitive threat:** "Could someone else (EdPlus, NationServe, etc.) copy this?"
   - *Answer:* Absolutely. But they don't have nonprofit discovery. We do. We're unique in the intersection of (discovery + service tracking + nonprofit operations). That's defensible if executed well.

5. **Impact metrics:** "You list 10+ success metrics. Which ones actually matter for board decision-making?"
   - *Answer:* Three that matter most: (1) student enrollment (proof of demand), (2) nonprofit voluntary participation (proof of value), (3) hour completion rate and verification accuracy (proof of system reliability). Others are nice-to-have.

---

## DISCUSSION: PAIN POINTS & CONCERNS

### Safety & Liability
**Chair:** "Let's talk about the elephant in the room. If a student gets hurt at a nonprofit, who's liable?"

**Founder:** "Good question. This is why we limit to 13+, require school enrollment, and require nonprofit background checks. Nonprofit retains liability for the volunteer (standard model). We're not the employer. The student is a volunteer at the nonprofit, supervised by the nonprofit."

**Legal Advisor:** "We need volunteer-liability language in the nonprofit agreement. Standard nonprofit contracts already address this—we're just documenting it."

**Investor:** "What if a student mis-represents their age?"

**Founder:** "School verifies at enrollment (they know the student). Fraud flag if we detect age inconsistency. But yes, risk remains. This is why pilot is small and heavily monitored."

### Data Privacy & Retention
**Privacy Advisor:** "You say student records are private. But what if law enforcement requests records? What if a nonprofit disputes an hour and demands the student's contact info?"

**Founder:** "Law enforcement: we comply with valid court order. Nonprofit: they get to know the student's name (they're the supervisor). We mediate any additional contact through the school."

**Privacy Advisor:** "Documenting this clearly will be critical. We need to include student-rights language in the certificate and school agreements."

### School Buy-In
**Education Expert:** "Schools are busy. How do you convince them to participate?"

**Founder:** "Start with schools I already know. Offer to handle all the heavy lifting. They just review what we propose. If it works with 3-5 schools in Houston, we have proof points for other cities."

**Chair:** "Do you need school board approval to pilot this?"

**Founder:** "Possibly, depending on the district. That's why partnership work starts early (weeks 7-9). We'll know by week 10 if participation is achievable."

### Nonprofit Supervisor Training
**Operations Director:** "You plan to train nonprofit supervisors. How thorough does that need to be?"

**Founder:** "During pilot: intensive. Probably 30-minute onboarding per org, plus written guidelines. We review their first 5 submissions closely. Post-pilot: probably self-service with documentation."

**Operations Director:** "And if a supervisor rejects a student's hours unfairly?"

**Founder:** "Student can dispute. If pattern emerges, we flag it with the nonprofit leadership. This is why audits matter."

---

## RISK DISCUSSION

### Severity Matrix (Founder Presents)

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Privacy violation (student data exposed) | Critical | Minimal data collection, encryption, access controls, legal review |
| Student safety incident | Critical | Age 13+, school-mediated, nonprofit supervision, background checks |
| COPPA non-compliance | High | Legal review in week 2, delayed enrollment if issues found |
| Nonprofit supervisor fraud (false hour verification) | Medium | Audit trail, random audits, reputation damage discourages fraud |
| Low adoption (fewer than 50 students) | Medium | Board would be notified at week 9; option to pause |
| Nonprofit overwhelm (too many student submissions) | Low | Pilot size limits submissions per org |
| Legal dispute (student vs nonprofit; school vs Daanaa) | Medium | Clear agreements, dispute procedure, insurance, legal support |

**Chair:** "What's your tolerance for shutdown? If issues emerge, when do you pull the plug?"

**Founder:** "Before we enroll students: if COPPA review surfaces blocking issues. After enrollment: if significant fraud detected, if privacy incident occurs, or if enrollment falls below 30 students by week 15."

**Legal Advisor:** "I'd add one: if we can't get nonprofit liability language that we're comfortable with."

**Founder:** "Agreed."

---

## RESOURCE ALLOCATION DISCUSSION

**Chair:** "Let's talk about the 3 FTE during development. Where are you pulling that from?"

**Founder:** "Product manager: reallocating 0.5 from content roadmap. We're deprioritizing the insights dashboard (pushing to Q4). Engineer: full-time hire or allocation from current team. Designer: 0.3 from existing capacity (part-time)."

**Chair:** "Is this going to slip core Daanaa roadmap?"

**Founder:** "By maybe 4-6 weeks. We're deferring the nonprofit CRM integration (was planned for Q3; pushing to Q4). Worth it if student service shows promise."

**Investor:** "Hire or internal? If external, how long is ramp-up?"

**Founder:** "Internal if possible—they understand our codebase and stewardship model. If we need surge capacity, we'd hire a contractor for specific components (certificate generation, reporting dashboard)."

---

## BOARD DECISION FRAMEWORK

**Chair:** "Let me lay out what I'm hearing. The proposal has three components:

1. **Technical:** Build student service, verification, certificate capabilities. Board consensus: doable, fits with existing architecture.

2. **Legal & Compliance:** COPPA, FERPA, school agreements, nonprofit liability. Board consensus: manageable with proper review; must complete before enrollment.

3. **Operational:** Recruit schools and nonprofits, manage pilot, collect data. Board consensus: risky but contained (Houston-only, one semester).

The key question is: does the board feel confident that this is *exploratory* (we're learning), not a *commitment* (we're going national)?"

**All board members nod.**

**Chair continues:** "Then I'm inclined to authorize it with conditions. Specifically: (1) No student enrollment until legal/compliance review is complete. (2) Board update at week 9 with adoption metrics. (3) Early termination clause if enrollment stays below 30 or fraud emerges. (4) Post-pilot board decision required before any expansion. Does that reflect everyone's position?"

**Unanimous agreement.**

---

## SUMMARY OF BOARD SIMULATION

### Areas of Strong Agreement
✅ Technical feasibility is high (applies existing infrastructure)  
✅ Mission alignment is strong (serves students, nonprofits, communities)  
✅ Scope is appropriately contained (Houston, one semester, 3-5 schools, 20 nonprofits)  
✅ Privacy/safety concerns are addressable with proper diligence  
✅ Board maintains control (no expansion without approval)  

### Areas Requiring Close Attention
⚠️ COPPA/FERPA compliance review must complete before enrollment (weeks 2-3)  
⚠️ School partnership recruitment risk if key relationships don't participate  
⚠️ Nonprofit supervisor training and support (initial intensity needed)  
⚠️ Legal liability and insurance language (nonprofit agreements)  
⚠️ Adoption metrics must be hit (board will watch week 9 update closely)  

### Recommended Board Decision
✅ **AUTHORIZE** with conditions:  
1. Legal/compliance review before enrollment
2. Week-9 check-in with adoption metrics
3. Early termination clause if adoption is low or fraud emerges
4. Post-pilot board decision required before expansion

---

## PREPARATION FOR ACTUAL BOARD MEETING

### Materials to Prepare
- [ ] Final board memo (complete)
- [ ] Executive summary (1 page)
- [ ] Risk matrix (detailed version)
- [ ] Sample school partnership agreement (template)
- [ ] COPPA/FERPA compliance checklist (pre-review)
- [ ] Budget breakdown (3 FTE, costs, timeline)
- [ ] Success metrics dashboard (mockup)
- [ ] Legal review timeline (week-by-week)

### Key Talking Points
1. **This is exploratory, not a commitment.** Pilot is bounded (Houston, 1 semester). Board maintains full control over expansion.
2. **We're applying existing infrastructure.** No major new development. We're extending volunteer-hours system to serve students.
3. **Legal/compliance is a hard gate.** No student enrollment until COPPA/FERPA review is complete. This is non-negotiable.
4. **Nonprofits and schools must actually participate.** We're not assuming adoption. Week 9 check-in will confirm if this is viable.
5. **Impact is significant if it works.** Students get verified records. Nonprofits get student volunteers. Schools get free verification. Daanaa gets sustained engagement.

### Anticipated Questions (Prepare Answers)
- "What if Houston schools don't want to participate?" → Backup cities identified (Austin, San Antonio, Dallas). But Houston our first choice.
- "What's the long-term financial model?" → TBD. Pilot will inform. Options: freemium, nonprofit subscription, school contracts. No decision until post-pilot.
- "Could this dilute our mission (nonprofit discovery)?" → No. This deepens discovery by converting it into engagement. Students who volunteer discover nonprofits they might not have otherwise known.
- "What happens if this fails?" → We've learned something valuable about student engagement. We either iterate or shut it down. Cost of failure is low (6 months, 3 FTE).

---

## BOARD RESOLUTION (FINAL VERSION)

**Resolved:** The board authorizes management to allocate appropriate resources to design and conduct a controlled Houston pilot of Daanaa's student community-service capability, subject to:

1. Completion of legal review confirming COPPA and FERPA compliance before student enrollment
2. Board update at week 9 with adoption metrics and go/no-go recommendation
3. Early termination clause if enrollment falls below 30 students or significant fraud is detected
4. Explicit board authorization required before any expansion beyond Houston pilot
5. Post-pilot evaluation and board decision before any material expansion or major certification expenditures

**Motion:** Founder  
**Second:** [Board Member]  
**Vote:** [Unanimous / 7-0 / etc.]  
**Outcome:** APPROVED

---

**Next Steps:**
- Week 1: Begin legal review process
- Week 2: Partner recruitment outreach begins
- Week 3: First sprint planning (product/engineering)
- Week 9: Board update with adoption metrics

