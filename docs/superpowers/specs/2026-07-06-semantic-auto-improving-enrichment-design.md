# Semantic-Informed Auto-Improving Enrichment Pipeline

**Date:** July 6, 2026  
**Scope:** Cause tag enrichment + website validation for 1.7M nonprofits with autonomous quality improvement  
**Philosophy:** Minimal code, maximum intelligence, extensible for future enrichment types  

---

## Problem Statement

**Current state:**
- 1.7M nonprofits indexed in Daanaa
- ~900K lack cause tags (discovery blocker)
- ~700K lack validated websites (data gap)
- Search quality limited by incomplete enrichment
- Manual quality improvement is non-scalable

**Goal:** Automatically enrich all orgs with high-quality cause tags + websites, with self-improving cycle that gets smarter over time without manual intervention.

---

## Design Overview

### Architecture: Four-Layer Pipeline

**Layer 1: Nightly Enrichment Batch** (8 PM – ~6 AM)
- Process 1.7M orgs needing cause tags or website validation
- Semantic lookup: embed org mission → find 5 similar orgs with good existing tags
- Qwen-32B generation: generate tags/websites informed by similar orgs
- Validation: HEAD request + DNS lookup for websites
- Write incrementally to DB with confidence scores and context metadata

**Layer 2: Quality Measurement** (6 AM – 7 AM)
- Measure accuracy: % of generated tags preserved after user corrections
- Measure validity: % of generated websites that resolve successfully
- Measure by cohort: identify weak patterns (specific NTEE categories, org sizes, etc.)
- Store all metrics in `quality_log` table for trending

**Layer 3: Autonomous Prompt Improvement** (7 AM)
- Analyze yesterday's quality metrics
- If cause_tag_accuracy < 0.75: adjust prompt to emphasize similar-org patterns
- If website_validity < 0.80: refine domain generation strategy
- Create new prompt version (v1.0 → v1.1) in prompt version control
- Log rationale for improvement (for future review)

**Layer 4: Continuous Cycle**
- Day N: Run batch with prompt vN
- Day N+1 morning: Measure quality, identify weaknesses
- Day N+1 7 AM: Auto-generate improved prompt vN+1
- Day N+1 night: Run batch with vN+1 (improved)
- Weekly: Deep review, consolidate improvements into major version bump

### Data Structures

**Enrichment Result (written to DB):**
```sql
enrichment_run (
  run_id INTEGER,
  run_date DATE,
  org_ein TEXT,
  enrichment_type TEXT,  -- 'cause_tags' | 'website'
  generated_value TEXT,
  confidence_score FLOAT,  -- 0.0-1.0
  context_used TEXT,  -- JSON: similar_orgs, model_version, prompt_version
  prompt_version TEXT,  -- v1.0, v1.1, v2.0, etc.
  created_at TIMESTAMP
)
```

**Quality Metrics (for learning):**
```sql
quality_log (
  date DATE,
  metric_type TEXT,  -- 'cause_tag_accuracy', 'website_validity', etc.
  value FLOAT,  -- 0.0-1.0
  cohort TEXT,  -- 'All' | 'NTEE_A' | 'size_micro' | etc.
  prompt_version TEXT,
  notes TEXT
)
```

**Prompt Version Control (simple JSON file):**
```json
{
  "v1.0": {
    "created": "2026-07-07",
    "cause_tags": "Similar high-performing orgs are tagged: {similar_tags}. This org has mission: {mission}. NTEE category: {ntee}. Suggest 3-5 cause tags.",
    "website": "Similar orgs in {city}, {state} use domains like: {similar_domains}. Org name: {org_name}. Suggest likely domain."
  },
  "v1.1": {
    "created": "2026-07-08",
    "cause_tags": "v1.0 + For Arts/Culture orgs, emphasize: accessibility, audience type, art form. For Education: grade level, subject, modality.",
    "website": "v1.0 + Check: nonprofit.org, .org TLD, abbreviated names common in {state}."
  }
}
```

---

## Implementation Plan (High-level)

### Script: `enrich_batch.py` (~400 lines, Ponytail style)

**Phase 1: Data Prep** (~30 lines)
- Query orgs needing enrichment
- Split into batches (280K per worker if parallel, else sequential)

**Phase 2: Semantic Lookup + Qwen Inference** (~150 lines)
- For each org: embed mission using local embeddings server (port 11436)
- Find 5 similar orgs via vector similarity (pre-computed embeddings already in DB)
- Call Qwen-32B (port 11437) with context: `{similar_orgs_tags} + {org_mission} → generate tags`
- Validate websites: HEAD request + registrar check (parallel with tag inference)

**Phase 3: Quality Measurement** (~80 lines)
- After enrichment: compare generated tags against user corrections from past week
- Calculate per-cohort accuracy (overall, by NTEE, by size)
- Log metrics to quality_log table

**Phase 4: Autonomous Prompt Improvement** (~50 lines)
- Read quality_log for yesterday
- If any metric < threshold: generate improved prompt reasoning + new version
- Write to prompt version control file + DB

**Phase 5: Monitoring & Rollback** (~50 lines)
- Watch GPU temp, memory, timeout errors
- If thermal throttle: pause, cool 5min, resume
- If Qwen unresponsive: skip org, log for manual review
- Log all errors for Phase 2 deep review

### Execution Frequency

| Cycle | Frequency | Window | Runtime |
|-------|-----------|--------|---------|
| Enrichment batch (full 1.7M) | Nightly | 8 PM – 6 AM | 10h |
| Quality measurement | Daily | 6 AM – 7 AM | 30m |
| Prompt auto-improvement | Daily | 7 AM | 5m |
| Incremental new orgs | Real-time on-demand | As orgs arrive | <5s/org |
| Deep review + prompt tuning | Weekly (manual) | Mondays 9 AM | 2h |

---

## Quality Gates & Safety

**Confidence Score Calculation:**
```
cause_tags_confidence = 
  0.9 * semantic_similarity_score +
  0.05 * tag_overlap_with_similar_orgs +
  0.05 * prompt_version_quality_trend
```

**Minimum thresholds to write to DB:**
- Cause tags: confidence ≥ 0.65 (ensures reasonable quality)
- Website: must pass validation (404 check, registrar lookup)

**Rollback mechanism:**
- If daily quality metric drops >10% vs. previous day → revert to previous prompt version, alert user
- All runs versioned + logged → can replay any day's run with any prompt version

---

## Long-term Evolution

**Phase 1 (Week 1):** Fill all gaps, establish baseline quality metrics
**Phase 2 (Weeks 2-4):** Auto-improve prompts, measure quality lift, identify weak cohorts
**Phase 3 (Month 2):** Consolidate improvements, add new enrichment types (leadership, financials) without architectural change
**Phase 4 (Q2+):** Expand to real-time enrichment on new orgs, integrate user feedback faster

---

## Success Criteria

| Metric | Target | Timeline |
|--------|--------|----------|
| Org enrichment coverage (cause tags) | 95%+ | Week 1 |
| Org enrichment coverage (websites) | 90%+ | Week 1 |
| Cause tag accuracy (user correction rate) | >75% | Week 2 |
| Website validity (successful HEAD requests) | >80% | Week 2 |
| Prompt improvement measurable | +5% quality per version | Week 4 |
| Search result relevance improvement | User-reported | Month 2 |

---

## Extensibility: Adding New Enrichment Types

Future enrichment types (leadership, board composition, financials) will be added as handlers:

```python
# Add new enrichment type in ~20 lines
@enrichment_handler('leadership')
def enrich_leadership(org):
    similar_orgs = find_similar(org)
    prompt = templates['v1.0']['leadership']
    result = qwen_infer(prompt.format(
        org_name=org['name'],
        similar_leadership=similar_orgs['leadership'],
        nonprofit_type=org['ntee']
    ))
    return result

# Then in Phase 4: just register it and run
enrich_batch.py --types cause_tags,website,leadership
```

No architectural changes needed.

---

## Assumptions & Constraints

- **Hardware:** Ryzen 7 9700X + R9700 GPU (24GB), local Qwen-32B + embeddings running
- **Data:** User corrections are captured (already done via Daanaa claims/corrections flow)
- **Timeline:** 10-14 hour batch windows acceptable (trade-off for quality improvement)
- **Staffing:** Autonomous improvement runs nightly; manual deep review ~2h/week

---

## Open Questions for User Review

1. **Website generation strategy:** Should we only fill missing websites, or re-validate all existing ones nightly?
2. **Correction feedback:** Where do user corrections come from (claims system, manual curator edits, API corrections)?
3. **Threshold sensitivity:** Are confidence thresholds (0.65 for tags, validation for websites) appropriate, or adjust?
4. **New org handling:** Once batch is running, should new orgs arriving during day 2+ be enriched in real-time (<5s) or queued for next batch?

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Qwen generates low-quality tags in v1.0 | Quality gate (conf ≥0.65), semantic validation, daily improvement cycle |
| Prompt auto-improvement breaks things | Versioning + rollback; improvement only if metric improves, else hold |
| GPU memory pressure during batch | Monitor temps, pause/resume if throttling |
| Missing corrections data | Deep review identifies gaps, manual tuning needed |

---

## Success Definition

✅ **Done when:**
- Script runs autonomously nightly, completes 1.7M enrichment in 10-14h
- Quality metrics captured daily, show measurable improvement week-over-week
- Prompts auto-improve without degrading accuracy
- Search result relevance improves (measured via user feedback)
- Architecture proven extensible (can add 1 new enrichment type without redesign)
