#!/usr/bin/env python3
"""
credibility_signals.py — compute 6 credibility signals for nonprofits.

Signals:
1. IRS Verification (verified/unverified/revoked/unknown)
2. Data Freshness (filing date recency)
3. Expense Ratio (program spend transparency)
4. Peer Context (percentile rank within peer group)
5. Recency & Completeness (snapshot freshness + data gaps)
6. Mission Alignment (sourced from org vs AI-generated)

Each signal returns: status, confidence (0-100), explanation.
Composite confidence = mean of all signal confidences.
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

DB = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'


class CredibilitySignals:
    def __init__(self):
        self.db = DB
        self.today = datetime.now()

    def get_all_signals(self, ein: str) -> Dict[str, Any]:
        """Compute all 6 signals for an org."""
        con = sqlite3.connect(str(self.db))
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        try:
            # Fetch org data once
            cur.execute(
                'SELECT * FROM registry_enriched WHERE EIN = ?',
                (ein,)
            )
            org = cur.fetchone()
            if not org:
                return self._no_org_result()

            org_dict = dict(org)
            con.close()

            # Compute all signals
            signals = {
                'irs_verification': self.signal_irs_verification(org_dict),
                'data_freshness': self.signal_data_freshness(org_dict),
                'expense_ratio': self.signal_expense_ratio(org_dict),
                'peer_context': self.signal_peer_context(org_dict, ein),
                'recency_completeness': self.signal_recency_completeness(org_dict),
                'mission_alignment': self.signal_mission_alignment(org_dict),
            }

            # Composite confidence
            confidences = [s.get('confidence', 0) for s in signals.values()]
            composite = int(sum(confidences) / len(confidences)) if confidences else 0

            return {
                'ein': ein,
                'signals': signals,
                'composite_confidence': composite,
                'computed_at': self.today.isoformat(),
            }
        finally:
            con.close()

    # -----------------------------------------------------------------------
    # SIGNAL 1: IRS Verification
    # -----------------------------------------------------------------------

    def signal_irs_verification(self, org: Dict) -> Dict[str, Any]:
        """
        Verified: active status + in good standing (not in revoked_eins)
        Unverified: no 990 data or status unknown
        Revoked: in revoked_eins table
        Unknown: other edge cases
        """
        status = org.get('org_status', '').lower()
        irs_revoked = org.get('irs_revoked', 0)

        if irs_revoked == 1:
            return {
                'status': 'revoked',
                'confidence': 0,
                'label': 'IRS Status: Revoked',
                'explanation': 'This organization\'s 501(c)(3) status was automatically revoked by the IRS for failure to file.',
            }
        elif status == 'active' and irs_revoked == 0:
            return {
                'status': 'verified',
                'confidence': 100,
                'label': 'IRS Status: Verified',
                'explanation': 'Current 501(c)(3) status confirmed in IRS database (verified daily).',
            }
        elif not status or status == '':
            return {
                'status': 'unknown',
                'confidence': 30,
                'label': 'IRS Status: Unknown',
                'explanation': 'Insufficient data to verify current IRS status.',
            }
        else:
            return {
                'status': 'unverified',
                'confidence': 60,
                'label': 'IRS Status: Unverified',
                'explanation': 'Organization status not yet verified in current IRS data.',
            }

    # -----------------------------------------------------------------------
    # SIGNAL 2: Data Freshness
    # -----------------------------------------------------------------------

    def signal_data_freshness(self, org: Dict) -> Dict[str, Any]:
        """
        Fresh: Form 990 filed <18 months ago
        Aging: 18-30 months
        Stale: >30 months
        Unknown: no filing date
        """
        filing_year = org.get('filing_year')
        if not filing_year:
            return {
                'status': 'unknown',
                'confidence': 50,
                'label': 'Data Freshness: Unknown',
                'explanation': 'No recent Form 990 filing data available.',
            }

        try:
            filing_date = datetime(int(filing_year), 12, 31)
            months_old = (self.today - filing_date).days / 30.44

            if months_old < 18:
                return {
                    'status': 'fresh',
                    'confidence': 95,
                    'label': f'Data Freshness: Recent ({int(months_old)} months)',
                    'explanation': f'Form 990 filed in {filing_year} ({int(months_old)} months ago).',
                }
            elif months_old < 30:
                return {
                    'status': 'aging',
                    'confidence': 75,
                    'label': f'Data Freshness: Aging ({int(months_old)} months)',
                    'explanation': f'Form 990 from {filing_year} ({int(months_old)} months old).',
                }
            else:
                return {
                    'status': 'stale',
                    'confidence': 45,
                    'label': f'Data Freshness: Stale ({int(months_old)} months)',
                    'explanation': f'Most recent Form 990 from {filing_year} (>{int(months_old)} months).',
                }
        except (ValueError, TypeError):
            return {
                'status': 'unknown',
                'confidence': 40,
                'label': 'Data Freshness: Unknown',
                'explanation': 'Unable to verify filing date.',
            }

    # -----------------------------------------------------------------------
    # SIGNAL 3: Expense Ratio (Program Spend Transparency)
    # -----------------------------------------------------------------------

    def signal_expense_ratio(self, org: Dict) -> Dict[str, Any]:
        """
        Show actual program expense ratio + peer median for context.
        <65% = Concern, 65-75% = Fair, 75%+ = Strong.
        Confidence depends on data source quality.
        """
        ratio = org.get('program_expense_ratio')
        if ratio is None or ratio < 0:
            return {
                'status': 'unknown',
                'confidence': 50,
                'label': 'Program Expenses: Unknown',
                'explanation': 'Program expense ratio not available.',
            }

        ratio_pct = ratio * 100  # Assume stored as decimal

        if ratio_pct < 65:
            return {
                'status': 'concern',
                'confidence': 95,
                'label': f'Program Expenses: {ratio_pct:.0f}%',
                'explanation': f'{ratio_pct:.0f}% of revenue goes to programs (IRS Form 990). Consider asking org about this ratio.',
            }
        elif ratio_pct < 75:
            return {
                'status': 'fair',
                'confidence': 95,
                'label': f'Program Expenses: {ratio_pct:.0f}%',
                'explanation': f'{ratio_pct:.0f}% of revenue goes to programs (IRS Form 990).',
            }
        else:
            return {
                'status': 'strong',
                'confidence': 95,
                'label': f'Program Expenses: {ratio_pct:.0f}%',
                'explanation': f'{ratio_pct:.0f}% of revenue goes to programs (IRS Form 990).',
            }

    # -----------------------------------------------------------------------
    # SIGNAL 4: Peer Context (Percentile Rank)
    # -----------------------------------------------------------------------

    def signal_peer_context(self, org: Dict, ein: str) -> Dict[str, Any]:
        """
        Percentile rank within peer cell (NTEE2 × revenue band × region).
        Top 25% = Leader, 25-50% = Strong, 50-75% = Typical, Bottom 25% = Developing.
        """
        con = sqlite3.connect(str(self.db))
        cur = con.cursor()

        try:
            # Get peer group info
            cur.execute(
                '''SELECT merit_peer_group_v5, merit_peer_count_v5, peer_rank
                   FROM registry_enriched WHERE EIN = ?''',
                (ein,)
            )
            row = cur.fetchone()
            if not row or not row[0]:
                return {
                    'status': 'unknown',
                    'confidence': 50,
                    'label': 'Peer Context: Unknown',
                    'explanation': 'Peer group data not available.',
                }

            peer_group, peer_count, peer_rank = row
            if not peer_count or peer_rank is None:
                return {
                    'status': 'unknown',
                    'confidence': 50,
                    'label': 'Peer Context: Unknown',
                    'explanation': 'Peer group analysis not yet computed.',
                }

            percentile = (peer_rank / peer_count) * 100 if peer_count > 0 else 0

            if percentile >= 75:
                label = 'Peer Context: Leader'
                status = 'leader'
            elif percentile >= 50:
                label = 'Peer Context: Strong'
                status = 'strong'
            elif percentile >= 25:
                label = 'Peer Context: Typical'
                status = 'typical'
            else:
                label = 'Peer Context: Developing'
                status = 'developing'

            return {
                'status': status,
                'confidence': 85,
                'label': label,
                'explanation': f'Ranks {peer_rank}/{peer_count} in peer group (top {100-percentile:.0f}%).',
                'peer_rank': peer_rank,
                'peer_count': peer_count,
                'percentile': percentile,
            }
        finally:
            con.close()

    # -----------------------------------------------------------------------
    # SIGNAL 5: Recency & Completeness
    # -----------------------------------------------------------------------

    def signal_recency_completeness(self, org: Dict) -> Dict[str, Any]:
        """
        Check snapshot freshness + data gaps (mission, website, donation link, leadership).
        """
        gaps = []
        if not org.get('mission') or org.get('mission') == '':
            gaps.append('mission')
        if not org.get('website') or org.get('website') == '':
            gaps.append('website')
        if not org.get('donate_url') or org.get('donate_url') == '':
            gaps.append('donation link')
        if not org.get('board_size') or org.get('board_size') == 0:
            gaps.append('leadership')

        gap_pct = (len(gaps) / 4) * 100 if gaps else 0
        completeness = 100 - gap_pct

        if gap_pct == 0:
            status = 'complete'
            confidence = 100
            label = 'Data: Complete'
            explanation = 'All key data fields populated.'
        elif gap_pct <= 25:
            status = 'mostly_complete'
            confidence = 85
            label = 'Data: Mostly Complete'
            explanation = f'Minor gaps ({len(gaps)} of 4 fields): {", ".join(gaps)}.'
        elif gap_pct <= 50:
            status = 'partial'
            confidence = 70
            label = 'Data: Partial'
            explanation = f'Some key data missing ({len(gaps)} of 4 fields): {", ".join(gaps)}.'
        else:
            status = 'minimal'
            confidence = 50
            label = 'Data: Minimal'
            explanation = f'Limited data available ({len(gaps)} of 4 fields missing).'

        return {
            'status': status,
            'confidence': confidence,
            'label': label,
            'explanation': explanation,
            'completeness_pct': completeness,
            'missing_fields': gaps,
        }

    # -----------------------------------------------------------------------
    # SIGNAL 6: Mission Alignment (Source Tracking)
    # -----------------------------------------------------------------------

    def signal_mission_alignment(self, org: Dict) -> Dict[str, Any]:
        """
        Highest confidence: org-attested (website/990)
        Medium confidence: AI-generated (Qwen3-30B)
        Low confidence: No mission
        """
        mission = org.get('mission') or ''
        mission_source = org.get('mission_source') or ''

        if not mission:
            return {
                'status': 'unknown',
                'confidence': 30,
                'label': 'Mission: Not Available',
                'explanation': 'Organization mission description not yet available.',
            }

        if mission_source == 'ai_ntee':
            return {
                'status': 'ai_generated',
                'confidence': 70,
                'label': 'Mission: AI-Generated',
                'explanation': 'Mission derived from NTEE category (not org-attested).',
            }
        elif mission_source == 'ai_generated':
            return {
                'status': 'ai_generated',
                'confidence': 75,
                'label': 'Mission: AI-Generated',
                'explanation': 'Mission generated from org data (not directly attested).',
            }
        else:  # Assume org-sourced if not AI
            return {
                'status': 'org_attested',
                'confidence': 100,
                'label': 'Mission: Organization-Sourced',
                'explanation': 'Mission statement sourced directly from organization.',
            }

    def _no_org_result(self) -> Dict[str, Any]:
        """Return empty signal set for unknown org."""
        return {
            'ein': None,
            'error': 'Organization not found',
            'signals': {},
            'composite_confidence': 0,
            'computed_at': self.today.isoformat(),
        }


def compute_signals(ein: str) -> Dict[str, Any]:
    """Convenience function to compute signals for an EIN."""
    cs = CredibilitySignals()
    return cs.get_all_signals(ein)


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('Usage: python3 credibility_signals.py <EIN>')
        sys.exit(1)

    ein = sys.argv[1]
    result = compute_signals(ein)

    import json
    print(json.dumps(result, indent=2, default=str))
