#!/usr/bin/env python3
"""
Phase 3 Measurement Setup — Plausible Integration

Adds custom events to track Phase 3 impact on small org CTR.
Integrates with frontend analytics to measure week-over-week improvement.

Events to add:
1. atagla nce_visible — user sees At a Glance section
2. org_detail_bookmark — user bookmarks org (proxy for decision-making)
3. search_filter_leadership — user filters by leadership criteria

Measurement window: Aug 9-16 (baseline vs Phase 3 impact)
Decision gate: Aug 16 (CTR +30%+ = green light Phase 4)
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta

LOG_DIR = Path.home() / 'meritgiving' / 'logs'
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'phase3_measurement_setup.log'),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def generate_plausible_setup_guide():
    """Generate step-by-step Plausible custom event setup guide."""

    guide = """
╔════════════════════════════════════════════════════════════════════╗
║ PHASE 3 MEASUREMENT — Plausible Setup Guide                       ║
╚════════════════════════════════════════════════════════════════════╝

STEP 1: Add Custom Events to Frontend Analytics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Location: frontend/src/utils/analytics.ts

Add these event tracking functions:

```typescript
// Track when At a Glance section becomes visible
export function trackAtAGlanceVisible() {
  trackEvent('atagla nce_visible', {
    section: 'at_a_glance',
    org_size: document.dataset.orgSize || 'unknown',
  });
}

// Track when user bookmarks an org (existing, enhance with org_size)
export function trackOrgBookmark(ein: string, orgSize: string) {
  trackEvent('org_detail_bookmark', {
    ein,
    org_size: orgSize,
    revenue_band: document.dataset.revenueBand || 'unknown',
  });
}

// Track if user clicks leadership/stability filters in search
export function trackSearchFilter(filterType: string) {
  if (['leadership', 'stability', 'board_size'].includes(filterType)) {
    trackEvent('search_filter_context', {
      filter: filterType,
      context: 'at_a_glance_inspired',
    });
  }
}
```

STEP 2: Integrate into Components
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Component: frontend/src/components/AtAGlance.tsx
├─ On mount: call trackAtAGlanceVisible()
└─ Attach org_size metadata to window.plausible context

Component: frontend/src/components/WalletHeartButton.tsx
├─ On bookmark click: call trackOrgBookmark(ein, orgSize)
└─ Emit revenue_band to event payload

Component: frontend/src/pages/Directory.tsx
├─ On filter click (leadership, stability): call trackSearchFilter()
└─ Attach reason: 'at_a_glance_inspired'

STEP 3: Plausible Dashboard Setup
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Login: https://plausible.io/daanaa.org
2. Settings → Custom Properties → Add:
   - org_size (string: Micro, Professional, Established)
   - revenue_band (string: same as above)
   - section (string: at_a_glance, financial_context, etc.)

3. Create Custom Goal:
   - Name: "atagla nce_visible"
   - Trigger: plausible('atagla nce_visible')
   - Repeat for: org_detail_bookmark, search_filter_context

STEP 4: Query Templates (Copy-Paste into Plausible)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Query A: Small Org CTR Week-over-Week
─────────────────────────────────────
Goal: atagla nce_visible (or org_detail_bookmark)
Segment by: org_size = 'Micro'
Period: Week (Aug 2-8 baseline, Aug 9-16 Phase 3 impact)
Formula: (atagla nce_visible events / sessions) × 100

Query B: At a Glance Visibility Rate
─────────────────────────────────────
Goal: atagla nce_visible
Period: Daily (Aug 9+)
Target: >60% of org_detail visitors see At a Glance

Query C: Micro Org Bookmarks vs Large Org
──────────────────────────────────────────
Goal: org_detail_bookmark
Segment by: org_size = 'Micro' vs 'Professional' vs 'Established'
Period: Week
Formula: micro_bookmarks / large_bookmarks ratio

STEP 5: Baseline Collection (Aug 9)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Before Phase 3 goes "live" (cache clears), capture:
1. CTR for Micro orgs (Aug 2-8): __________%
2. CTR for Large orgs (Aug 2-8): __________%
3. Ratio (Micro/Large): __________
4. Directory impressions by size
5. Search volume by org size

Save as: docs/PHASE3_BASELINE_AUG9.csv

STEP 6: Live Monitoring (Aug 10-16)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Daily pulse check (5 min):
┌─────────────────────────────────────┐
│ Aug 10: Micro CTR = ___%  (baseline)│
│ Aug 11: Micro CTR = ___%  (Δ: __%)  │
│ Aug 12: Micro CTR = ___%  (Δ: __%)  │
│ Aug 13: Micro CTR = ___%  (Δ: __%)  │
│ Aug 14: Micro CTR = ___%  (Δ: __%)  │
│ Aug 15: Micro CTR = ___%  (Δ: __%)  │
│ Aug 16: Micro CTR = ___%  (Δ: __%)  │
└─────────────────────────────────────┘

Red flag: CTR drops >10% — investigate layout/perf issue

STEP 7: Decision Report (Aug 16)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Generate report:
- Week 1 CTR (Aug 9-16) vs baseline (Aug 2-8)
- Improvement: ________%
- At a Glance visibility: ________%
- Micro/Large bookmark ratio: ________
- Conclusion: [ ] Phase 3 Wins [ ] Neutral [ ] Needs Debug

If CTR +30%+: Green light Phase 4 (Aug 20)
If Neutral: A/B test component placement
If Down: Rollback Phase 3 and investigate

════════════════════════════════════════════════════════════════════
"""

    return guide


def main():
    logger.info("=" * 70)
    logger.info("PHASE 3 MEASUREMENT — Plausible Setup")
    logger.info("=" * 70)

    guide = generate_plausible_setup_guide()
    print(guide)

    # Save guide
    guide_path = Path.home() / 'meritgiving' / 'docs' / 'PLAUSIBLE_SETUP_GUIDE.txt'
    guide_path.write_text(guide)
    logger.info(f"\n✅ Setup guide saved: {guide_path}")

    # Create measurement tracking file
    tracking = {
        'setup_date': datetime.now().isoformat(),
        'measurement_window_start': (datetime.now()).date().isoformat(),
        'measurement_window_end': (datetime.now() + timedelta(days=7)).date().isoformat(),
        'decision_gate': (datetime.now() + timedelta(days=7)).date().isoformat(),
        'events_to_track': [
            'atagla nce_visible',
            'org_detail_bookmark',
            'search_filter_context',
        ],
        'metrics': [
            'small_org_ctr_baseline',
            'small_org_ctr_week1',
            'atagla nce_visibility_pct',
            'micro_large_bookmark_ratio',
        ],
        'success_criteria': {
            'phase3_wins': 'Small org CTR +30%+ vs baseline',
            'phase3_neutral': 'Small org CTR -5% to +30%',
            'phase3_needs_debug': 'Small org CTR -5%+',
        },
    }

    tracking_path = Path.home() / 'meritgiving' / 'docs' / '.phase3_measurement_tracking.json'
    tracking_path.write_text(json.dumps(tracking, indent=2))
    logger.info(f"✅ Tracking config: {tracking_path}")

    logger.info("\n" + "=" * 70)
    logger.info("NEXT STEPS:")
    logger.info("=" * 70)
    logger.info("1. Read: docs/PLAUSIBLE_SETUP_GUIDE.txt")
    logger.info("2. Update: frontend/src/utils/analytics.ts (add event functions)")
    logger.info("3. Integrate: AtAGlance.tsx, WalletHeartButton.tsx, Directory.tsx")
    logger.info("4. Configure: Plausible dashboard (custom properties + goals)")
    logger.info("5. Baseline: Aug 9 (capture pre-Phase 3 metrics)")
    logger.info("6. Monitor: Aug 10-16 (daily pulse checks)")
    logger.info("7. Decide: Aug 16 (Phase 4 green light?)")


if __name__ == '__main__':
    main()
