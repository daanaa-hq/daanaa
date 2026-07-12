# Board Resolution Implementation Plan

**Authority:** Stewardship Board 2026-07-11  
**Status:** Phased execution  
**Classification:** Operational Practice  

---

## PHASE 1: INSTITUTIONAL MEMORY & PRESERVATION (CRITICAL PATH)
*Trigger: Today. Unblocks everything else.*

### P1.1: Git-track institutional library
- [ ] `git add institution/`
- [ ] `git commit -m "institution: track governance library in version control (board 2026-07-11)"`
- [ ] Update `.gitignore` if needed (library is public-tracking-ready)
- [ ] Verify: GitHub shows institution/ in remote

### P1.2: Update SUCCESSION.md with Memory Substrate section
- [ ] Document all five stores (git repo, institution/, AI session memory, gstack state, mempalace)
- [ ] For each: location, format, authority level, recovery procedure
- [ ] Add: "if this doc was not found, the institution has failed at succession"

### P1.3: Fix backup script silent-skip
- [ ] Update `scripts/ops/daanaa_backup.sh` to fail loudly if rclone missing
- [ ] Add: offsite push confirmation to stdout
- [ ] Test: backup cycle with rclone unavailable (should error, not silent-skip)

**Milestone:** Institutional memory is version-controlled, backed up, and recovery is documented and tested.

---

## PHASE 2: CONSTITUTIONAL HIERARCHY (GOVERNANCE)
*Unblocks: Library reconciliation, future amendments*

### P2.1: Create Constitution.md hierarchy document
- [ ] Document: Mission → Constitution → Stewardship Library → Policies → Engineering → Implementation
- [ ] Add to root: `/home/akbar/meritgiving/CONSTITUTION_HIERARCHY.md`
- [ ] Reference: Board resolution 2.1
- [ ] Headers in all three tier documents pointing to hierarchy

### P2.2: Tag existing documents with authority level
- [ ] Root `STEWARDSHIP.md`: **Supreme Law** (signed, revision-logged)
- [ ] `institution/CONSTITUTION.md`: **Governance Layer** (elaborates STEWARDSHIP.md; see article references)
- [ ] Library 003 (Stewardship): **Elaboration** (traces to STEWARDSHIP.md Articles)
- [ ] Each document: add header stating its tier and parent/child relationships

**Milestone:** Constitutional authority is transparent and unambiguous.

---

## PHASE 3: CONCIERGE DEPLOYMENT (ENGINEERING)
*Unblocks: Concierge feature shipping*

### P3.1: Update concierge endpoint disclosure wording
- [ ] File: `/home/akbar/meritgiving/daanaa_api.py`, endpoint `/api/admin/concierge/confirm`
- [ ] Add: Logging/documentation of the disclosure standard
- [ ] Add: Comment referencing Board resolution 1.1
- [ ] Operationalize: Disclosure is made by human operator (via phone), not the endpoint; endpoint receives confirmation

### P3.2: Update 004_ai_with_empathy.md per resolution
- [ ] Clarify: "invisible infrastructure, never undisclosed AI"
- [ ] Update: Transparent principle section with "disclosed at moment of interaction" language
- [ ] Update: Concierge section confirming disclosure
- [ ] Flag: Both Position A confirmed

### P3.3: Test + commit concierge work
- [ ] Run: `pytest tests/test_concierge_confirm.py -v`
- [ ] Commit: concierge endpoint + test suite
- [ ] Verify: All 13 tests pass
- [ ] Deploy to droplet: via standard safe_deploy pipeline

**Milestone:** Concierge shipping gate passes. Feature live on droplet.

---

## PHASE 4: LIBRARY CLASSIFICATION & RECONCILIATION (INSTITUTIONAL)
*Unblocks: Future amendments, measurement*

### P4.1: Classify all library documents (Board resolution 8)
- [ ] Library 001–010: each receives one Classification tag (Stewardship Principle, Institutional Principle, etc.)
- [ ] Framework documents (AI_GOVERNANCE, DEVELOPMENT_CONSTITUTION, RESEARCH_AGENDA, FUTURE_OF_GIVING): classify
- [ ] Add to header: `**Classification:** [tag]` (see 15-item taxonomy in board resolution)
- [ ] Example: "001_foundation.md — **Classification:** Institutional Principle"

### P4.2: Reconcile capacity frameworks
- [ ] Library 006's eleven Capacity Dimensions: canonical frame (Clarity, Financial, Leadership, Technology, Community, Governance, Sustainability, Data, Communication, Growth, Impact)
- [ ] Amendment 1's seven Capacity Transfer Measures: quantify improvement within these dimensions
- [ ] Create: `institution/capacity_framework_reconciliation.md` — mapping document
- [ ] Update: Amendment 1 proposal to reference 006 as dimensional frame

### P4.3: Update capacity-transfer proposal with measurements
- [ ] Map: seven measures to six dimensions (most dimensions measured multiple ways)
- [ ] Add: concrete measurement examples (e.g., "Financial: hours of bookkeeping work eliminated per year")
- [ ] Cross-reference: to Board resolution 6.1 (Capacity Stewardship principle)

**Milestone:** Library is consistently classified. Capacity framework is unified. Future services can be measured.

---

## PHASE 5: DIRECTORY PRESENTATION AUDIT (PRODUCT)
*Implements: Board resolution 9*

### P5.1: Audit current directory sort/filter behavior
- [ ] Query: current default sort on /directory — is it score-based?
- [ ] If yes: log as Constitutional Tension (Board resolution 9 says it is)
- [ ] Document: all sort/filter options available to users

### P5.2: Reframe Financial Context in UI
- [ ] Research page / detail page: add language "context, not verdict"
- [ ] Sort options: primary (mission, location, cause, community), secondary (Financial Health)
- [ ] All score/tier displays: add micro-label "one dimension, not a verdict"
- [ ] Test: verify no UI implies organizational worth from score alone

**Milestone:** Directory presents Financial Context as one dimension among many.

---

## PHASE 6: VENDOR REFERRAL AUDIT (POLICY)
*Implements: Board resolution 10*

### P6.1: Review any current vendor/referral language
- [ ] Capacity dimension 10 (banking guidance): currently names specific vendors?
- [ ] If yes: evaluate against Board resolution 10 (category vs. specific)
- [ ] Create: VENDOR_REFERRAL_POLICY.md if not present
- [ ] Ensure: all current referrals meet Board standards (transparent, replaceable, objective, free from preference)

**Milestone:** Vendor relationships are transparent and governance-aligned.

---

## PHASE 7: CONTINUOUS IMPROVEMENT (STANDING PRACTICE)
*Implements: Board resolutions 11–14*

### P7.1: Document amendment procedures
- [ ] Update: SUCCESSION.md amendment procedures
- [ ] Standard: proposals go to Stewardship Board with constitutional gap analysis
- [ ] Timeframe: decisions documented and committed within 7 days
- [ ] Preservation: all proposals + reasoning preserved in institution/

### P7.2: Schedule institutional self-review (Board 4.2)
- [ ] Every major milestone (feature ship, research paper, architecture decision): constitutional review
- [ ] Template: does it strengthen mission, nonprofit capacity, stewardship, resilience, trust?
- [ ] Schedule: self-review occurs before deployment, not after

**Milestone:** Continuous improvement is structural, not accidental.

---

## EXECUTION SEQUENCE

**Week 1 (P1 + P2 + P3):**
- Day 1: Institutional memory (P1.1–P1.3)
- Day 2: Constitutional hierarchy (P2.1–P2.2)
- Day 3–5: Concierge deployment (P3.1–P3.3)

**Week 2 (P4):**
- Classify all library documents
- Reconcile capacity frameworks
- Publish Board resolution as institutional record

**Week 3+ (P5–P7):**
- Directory audit
- Vendor policy
- Establish continuous-improvement rhythm

---

## DEFINITION OF DONE

**P1:** Memory is git-tracked, backed up, recoverable. Test: successor can recover all institutional knowledge following SUCCESSION.md.

**P2:** Constitution hierarchy is documented and transparent. All documents reference their tier.

**P3:** Concierge ships with correct disclosure wording. All 13 tests pass. Feature live on daanaa.org.

**P4:** All library documents have classification tags. Capacity frameworks are unified. Proposal is measurable.

**P5:** Directory never implies organizational worth from score alone. Financial Context is clearly secondary.

**P6:** Vendor relationships meet Board standards. Policy is written and auditable.

**P7:** Amendment procedures are documented. Next self-review is scheduled.

---

**Classification:** Operational Practice  
**Authority:** Stewardship Board 2026-07-11  
**Responsibility:** Institutional steward (AI) + engineering team + human decision-makers  
**The work continues.**
