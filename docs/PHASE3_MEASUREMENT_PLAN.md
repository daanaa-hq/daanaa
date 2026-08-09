# Phase 3 Measurement Plan — Week 1 Analytics (Aug 9-16)

**Status**: Deployed (live but unverified due to Cloudflare cache)
**Measurement Window**: Aug 9-16 (Week 1 baseline)
**Decision Gate**: Aug 16 (Phase 3 verdict → Phase 4 go/no-go)

---

## Metrics Definition

### Primary Metric: Small Org CTR (Click-Through Rate)

**Definition:**
- Clicks to org detail page for orgs with `revenue_band = 'Micro'` (< $150K annual revenue)
- Measured via Plausible Analytics event tracking
- Segmented by: desktop/mobile, new/returning visitor, traffic source

**Baseline (Pre-Aug-9):**
- Current small org CTR: ~40% of large org CTR
- Goal: 80% parity by Aug 23 (Phase 3 success = +100% relative improvement)

**How to measure (Plausible):**
```
Goal: Segment "Directory" page by org size
1. Directory page → Clicks to "org/EIN" link
2. Lookup org by EIN → get revenue_band from registry
3. Classify as "Micro" if revenue < $150K
4. CTR = Micro org clicks / Micro orgs shown
5. Compare week-over-week
```

**Stewardship alignment**: P4 (small org fairness) — we're measuring if better display actually helps small orgs.

---

### Secondary Metrics

**Org Detail Page Engagement:**
- Time on page (does At a Glance help donors understand faster?)
  - Success: +15% time on page for Micro orgs
  - Hypothesis: Better leadership/stability context → longer reading
- Scroll depth (do donors reach financial data?)
  - Track: % who scroll to "At a Glance" section
  - Success: >60% of visitors see the new section
- Wallet bookmarks (proxy for decision-making)
  - Micro org bookmarks should increase proportionally

**Search Behavior:**
- Small org search click rate (do they show up in search results more?)
- "Leadership" or "Stability" as search refinement (signal that users are finding it useful)

---

## Query Templates (Plausible Analytics)

### Query 1: Small Org CTR Week-over-Week

```
SELECT
  DATE_TRUNC('week', timestamp) as week,
  COUNT(DISTINCT session_id) as sessions,
  COUNT(CASE WHEN event = 'click_org_detail' THEN 1 END) as clicks_micro_org,
  COUNT(CASE WHEN event = 'click_org_detail' THEN 1 END) * 100.0 / 
    COUNT(DISTINCT session_id) as ctr_percent
FROM events
WHERE page = '/directory'
  AND org_size = 'Micro'
  AND timestamp >= '2026-08-02'  -- Start before Aug 9 for baseline
GROUP BY week
ORDER BY week;
```

### Query 2: Org Detail Page Scroll Depth (At a Glance Section)

```
SELECT
  DATE_TRUNC('day', timestamp) as date,
  COUNT(DISTINCT session_id) as sessions_to_org_detail,
  COUNT(CASE WHEN event = 'scroll_to_atagla nce' THEN 1 END) as saw_atagla nce,
  COUNT(CASE WHEN event = 'scroll_to_atagla nce' THEN 1 END) * 100.0 /
    COUNT(DISTINCT session_id) as pct_saw_atagla nce
FROM events
WHERE page LIKE '/org/%'
  AND timestamp >= '2026-08-09'
GROUP BY date
ORDER BY date DESC;
```

### Query 3: Micro Org Bookmark Rate

```
SELECT
  DATE_TRUNC('week', timestamp) as week,
  COUNT(CASE WHEN org_size = 'Micro' AND event = 'wallet_bookmark' THEN 1 END) as micro_bookmarks,
  COUNT(CASE WHEN org_size = 'Large' AND event = 'wallet_bookmark' THEN 1 END) as large_bookmarks,
  COUNT(CASE WHEN org_size = 'Micro' AND event = 'wallet_bookmark' THEN 1 END) * 100.0 /
    (COUNT(CASE WHEN org_size = 'Large' AND event = 'wallet_bookmark' THEN 1 END) + 1) as micro_to_large_ratio
FROM events
WHERE event = 'wallet_bookmark'
GROUP BY week
ORDER BY week;
```

---

## Measurement Setup Checklist

- [ ] **Plausible Custom Events** (add to analytics.ts):
  - `scroll_to_atagla nce` — fired when At a Glance section enters viewport
  - `click_org_detail` — fired when clicking org link from directory
  - `wallet_bookmark` — already exists (verify)
  - Attach metadata: `org_size`, `revenue_band`, `revenue_amount`

- [ ] **Event Enrichment** (backend):
  - When firing events, include `revenue_band` lookup (from registry_enriched)
  - Add to context: `org_age_years`, `merit_health_signal_v5` (for correlation)

- [ ] **Baseline Report** (Aug 9, 9am):
  - Query Week 1 (Aug 2-8) CTR for Micro orgs
  - Query search volume for Micro orgs
  - Query directory impressions by org size
  - Save as CSV for comparison on Aug 16

- [ ] **Weekly Report** (Aug 16, Friday):
  - Week 2 (Aug 9-15) CTR for Micro orgs vs. baseline
  - Org detail engagement (scroll, time, bookmarks)
  - Search behavior changes
  - Decision: Phase 3 helps? (CTR +30%+) → green light Phase 4

---

## Success Criteria & Actions

| Metric | Target | Outcome | Action |
|--------|--------|---------|--------|
| Small org CTR | +30% vs baseline | ✅ YES | Ship Phase 4 (Mission Capital) Aug 20 |
| Small org CTR | -5% to +30% | 🤔 NEUTRAL | Investigate: discovery vs. understanding? → A/B test At a Glance placement |
| Small org CTR | <-5% | ❌ NO | Rollback Phase 3, debug layout/UX |
| At a Glance scroll | >60% of visitors | ✅ YES | Component is discoverable |
| At a Glance scroll | <40% | 🤔 NEUTRAL | Try: move above fold, larger heading, highlight badge |
| Micro bookmarks | +20% vs large org ratio | ✅ YES | Donors are engaging better |

---

## Stewardship Notes

**P3 (Evidence-Based)**: We're measuring actual impact, not assuming. If display doesn't help, we'll know by Aug 16.

**P4 (Small Org Fairness)**: This metric directly tests our hypothesis that better display helps small orgs. No hidden assumptions.

**P6 (Mistakes Correction)**: If Phase 3 hurts CTR, we'll catch it in Week 1 and correct quickly.

---

## Timeline

**Aug 9 (Today):**
- Add custom events to Plausible
- Capture baseline metrics (week of Aug 2-8)

**Aug 10-15:**
- Collect live data for Week 1 (Phase 3 behavior)
- Daily pulse checks (sanity: CTR not crashing)

**Aug 16 (Decision Friday):**
- Generate Week 1 report
- Compare to baseline
- Decide: Phase 4 green light or pivot?

**Aug 20 (Phase 4 Ship, if green):**
- Deploy Mission Capital integration
- Continue measurement (Week 2)
- Measure Phase 4 impact

