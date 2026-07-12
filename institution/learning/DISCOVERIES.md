# Institutional Discoveries Register

**Purpose:** Continuously updated inventory of institutional learning, discoveries, and evidence.

**Authority:** Founder + Institutional Learning Steward  
**Last Updated:** 2026-07-12  
**Review Frequency:** Monthly minimum

---

## Registry Purpose

Document what the institution learns from every completed project, feature, experiment, deployment, research effort, failure, success, and milestone.

**Goal:** Become wiser, not merely larger. Enable other organizations to learn from our discoveries.

---

## ACTIVE DISCOVERIES

*None yet recorded. First Learning Records will populate this section after initial milestone reviews.*

---

## PROVISIONAL OBSERVATIONS

**These are preliminary patterns being monitored for discovery status:**

### O1: AI-Generated Content Adoption Barrier
**Observation:** Nonprofits show higher engagement with AI-assisted drafts when disclosure language is honest and invites review, lower when framing implies AI completeness.

**Evidence:** Concierge endpoint disclosure trials (in progress)

**Confidence:** Low (pilot stage)

**Status:** Under investigation

**Affected Principles:** STEWARDSHIP Principle #3 (trust signals must be evidence-based)

---

### O2: Website Discovery Scaling Challenge
**Observation:** Automatic website discovery scales in volume but accuracy degrades at higher concurrency without additional verification infrastructure.

**Evidence:** Web discovery Phase 1-2 metrics (Jun 2026), retry patterns in enrichment logs

**Confidence:** Medium

**Status:** Requires independent replication

**Affected Principles:** STEWARDSHIP Principle #4 (small orgs deserve fairness — data-dark small orgs need multiple verification rounds)

---

### O3: Backup Silent Failure Risk
**Observation:** Backup systems with implicit success criteria fail silently when components (rclone, SSH keys, remote connectivity) become unavailable—operators don't notice until restore is attempted.

**Evidence:** 2026-07-05 SPA fallback outage (11h), 2026-07-11 SSH key publish failure in overnight pipeline

**Confidence:** High

**Status:** Addressed via BACKUP_ROBUSTNESS directive (2026-07-11); awaiting replication of fix

**Affected Principles:** Operational resilience (not a Stewardship principle, but critical to mission continuity)

---

### O4: Enrichment Pipeline GPU Throughput
**Observation:** Running 4–7 parallel enrichment batches with 68+ concurrent workers on dual GPU servers (Qwen-3B @ parallel=12, mxbai embedding @ -np 4) sustains 90+ minutes of continuous processing without degradation.

**Evidence:** Overnight automation 2026-07-11 to 2026-07-12 (6+ hours sustained, 7 batches active at 06:40 AM)

**Confidence:** Medium-High

**Status:** Single run, requires week-long monitoring for replication

**Affected Principles:** Infrastructure efficiency, not directly principle-related

---

## REJECTED DISCOVERIES

*None yet.*

---

## PRINCIPLE CANDIDATES PENDING ADOPTION

*To be populated as discoveries reach confidence threshold for constitutional consideration.*

---

## LEARNING RECORDS ARCHIVE

*Individual milestone learning records stored in institution/learning/records/*

| Title | Date | Project | Confidence | Status |
|-------|------|---------|------------|--------|
| (First records to be added) | | | | |

---

## PUBLICATION QUEUE

*Discoveries suitable for external publication*

| Discovery | Target Audience | Venue | Timeline | Status |
|-----------|-----------------|-------|----------|--------|
| (To be populated) | | | | |

---

## NEXT STEPS

1. Establish process for generating Learning Records after each major milestone
2. Monthly discovery review meeting (Founder + Learning Steward)
3. Quarterly pattern synthesis (do multiple discoveries point to an emerging principle?)
4. Annual discovery synthesis document (for external publication consideration)
5. Track nonprofit applicability of each discovery (how could others benefit?)

---

## Governance Notes

**What belongs here:** Substantive learnings with evidence, patterns, unexpected discoveries, things we now understand better

**What doesn't:** Day-to-day operational notes, routine status updates, debugging logs

**Publication standard:** See LEARNING_DIRECTIVE_2026_07_12.md

**Constitutional impact:** Discoveries that challenge or strengthen Stewardship principles are flagged for Founder review

---

**The work continues.**

