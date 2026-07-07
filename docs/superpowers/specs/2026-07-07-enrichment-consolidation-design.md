# Enrichment Consolidation Design

**Date:** July 7, 2026
**Supersedes:** 2026-06-22 "no websites or donate links" directive (see DECISIONS.md)
**Builds on:** 2026-07-06 Semantic Enrichment Pipeline (Tasks 1-10, commit chain a9a01ee2f4d..b27cb676c14)

---

## Problem

The previously-built Semantic Enrichment Pipeline generates cause tags and websites but:
1. Never promotes results to `registry_enriched` — nothing it produces is visible on daanaa.org
2. Overlaps with an existing live script (`enrich_cause_tags_llm.py`) doing simpler cause-tag enrichment
3. Doesn't touch donate links or mission quality, despite those being core to a credible org profile
4. Doesn't use website content to ground mission generation — currently guesses missions from NTEE code + similar orgs alone, when the org's own website (once found) is a far stronger source

Founder direction (2026-07-07): consolidate into one system where cause tags, mission,
website, and donate links share context to build one credible profile per org — this
directly serves the mission ("help users find nonprofits, especially smaller ones, lead
them to their website or donate links") and reverses the 2026-06-22 pause on website/
donate-link work (see DECISIONS.md 2026-07-07 entry for the legal/strategic reasoning).

---

## Architecture

```
For each org needing enrichment:

  1. SemanticLookup: find similar orgs (existing, unchanged)

  2. Website discovery: search for + validate candidate domain
       └─ IF found: fetch page content, cache via existing page_cache table
                    (donation_link_pipeline.py's schema, reused not rebuilt)
       └─ Same fetch pass: scan for a volunteer/get-involved page link
                    (near-zero marginal cost — content already fetched;
                    store URL as new registry_enriched.volunteer_url column,
                    for future use — not consumed by any UI yet)

  3. Mission generation:
       └─ IF website content available: ground mission in real page text
          (NEW: QwenInference gets a website-grounded generation method)
       └─ ELSE: fall back to NTEE + similar-org context (current approach)

  4. Cause tags: informed by mission + website content (if available) +
                 similar-org tags (existing generate_tags(), context extended)

  5. Donate URL: separate candidate search →
       score_confidence() + identity_match() gate
       (extracted from donation_link_pipeline.py into scripts/donate_confidence.py,
       imported as a library — proven logic, not rebuilt)

  6. Promotion (inline, per-org, wrapped in existing try/except):
       - Fields clearing their confidence threshold → UPDATE registry_enriched
       - Fields below threshold → left untouched (donate_url: flagged
         donate_human_review=1, existing pattern) — never overwrite good
         data with a worse guess
```

### Retiring `enrich_cause_tags_llm.py`

Paused (cron disabled), not deleted, for a validation week. If the new pipeline's
tag quality regresses per `quality_log`, re-enable the old cron. Delete once
parity or better is confirmed.

### Scheduling

- 9pm-9am nightly, **exclusive GPU access** during initial 1.7M-org backlog clear
  (pauses mission-gen/reembed_watchdog, which have month-scale existing backlogs
  and can absorb a few paused nights)
- Stops cleanly at 9am if not finished, checkpoints progress, resumes next night
- Once backlog is cleared, reverts to normal shared 9p-9a scheduling alongside
  mission-gen/reembed_watchdog

### Monitoring

`monitor_batch.py`'s `check_batch_health()` runs every 3 hours during the window,
logs throughput/ETA per enrichment type (cause_tags, mission, website, donate_url),
and alerts via the existing `alert_manager.py` on a detected stall. Resource
*reallocation* stays a human decision (visible in the morning digest), not an
automated algorithm — appropriate for a single-operator home-server context.

---

## Files touched

| File | Change |
|------|--------|
| `scripts/enrich_batch.py` | Add website-discovery + content-fetch step (also scans for volunteer/get-involved page), sequence mission/tags generation with grounding context, add inline promotion step |
| `scripts/db_enrich_migration.py` | Add `volunteer_url TEXT` column to `registry_enriched` |
| `scripts/qwen_inference.py` | New website-grounded mission generation method; extend `generate_tags()` to accept optional grounding context |
| `scripts/donate_confidence.py` (new) | Extracted `score_confidence()`/`identity_match()` from `donation_link_pipeline.py` — shared library, no behavior change |
| `scripts/donation_link_pipeline.py` | Import from the new shared module instead of defining locally |
| `scripts/monitor_batch.py` | Extend for 3-hourly per-field throughput/ETA logging + stall alerting |
| `scripts/cron_enrich_nightly.sh` | Update scheduling for exclusive-access backlog-clear mode |
| `scripts/gpu_night.sh` | Pause `enrich_cause_tags_llm.py` block during validation week; document the pause/retire plan |

---

## Non-negotiables carried forward

- Never handle funds; donate links route to the org's own processor, Daanaa is never merchant of record
- Below-threshold results never silently overwrite good existing data
- All promotion failures are visible (logged), never silent
- Pre-launch attorney consult (tracked separately, not yet completed) required before scaling donate-link generation broadly — this design authorizes building it now, not skipping that review before wide rollout

---

## Open follow-up (not blocking this design)

- Attorney review of the automated donate-link generation mechanism specifically
- Deleting `enrich_cause_tags_llm.py` after the validation week confirms parity
