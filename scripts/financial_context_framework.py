#!/usr/bin/env python3
"""
Financial Context Framework — Stewardship-Aligned Assessment

Replaces "red flag" labels with transparent, model-aware financial context.
Honors Stewardship Principles 3, 4, 5, 6, 9:
  P3: Evidence-based signals, honest about uncertainty
  P4: Small orgs fairness, peer-relative benchmarking
  P5: No shaming; respectful, careful communication
  P6: Mistakes corrected immediately (suppress invalid data)
  P9: Explainable decisions with full audit trail

Output: Financial context (VERIFIED_HEALTHY, DATA_INCOMPLETE, FINANCIAL_NOTE)
Not: Judgment labels (RED_FLAG, DISTRESSED, etc.)

Rules:
  1. If data invalid (negative assets/revenue): DATA_INCOMPLETE (don't judge)
  2. If data missing (null financials): DATA_INCOMPLETE (don't assume)
  3. If verified + peer-healthy: VERIFIED_HEALTHY
  4. If verified + peer-strained: FINANCIAL_NOTE (with peer comparison)
  5. Never display shame language; always show peer context
"""

import sqlite3
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

DB = Path.home() / "meritgiving" / "data" / "merit_registry.db"

# NTEE1 to Operating Model mapping (9 models)
NTEE1_TO_MODEL = {
    'A': 'Activity_Programming',  # Arts/culture
    'B': 'Cause_Advocacy_Research',  # Education/research
    'C': 'Cause_Advocacy_Research',  # Environment
    'D': 'Clinical_Reimbursement',  # Health/medicine
    'E': 'Clinical_Reimbursement',  # Mental health/addiction
    'F': 'Community_Human_Services',  # Crime/legal services
    'G': 'Community_Human_Services',  # Employment/training
    'H': 'Direct_Delivery',  # Food/agriculture/nutrition
    'I': 'Direct_Delivery',  # Housing/shelter
    'J': 'Emergency_Logistics',  # Public safety/relief
    'K': 'Activity_Programming',  # Recreation/sports
    'L': 'Activity_Programming',  # Youth development
    'M': 'Membership_Mutual_Benefit',  # Voluntary organizations
    'N': 'Intermediary_Public_Benefit',  # Philanthropy/grantmaking
    'O': 'Intermediary_Public_Benefit',  # Public/societal benefit
    'P': 'Faith_Community',  # Religion/faith
    'Q': 'Membership_Mutual_Benefit',  # Mutual benefit
    'T': 'Activity_Programming',  # Unknown
}

# Operating model reserve expectations (in months)
# Based on validated financial patterns from 130K+ scored orgs
MODEL_BASELINES = {
    'Clinical_Reimbursement': {'target': 3.0, 'min_healthy': 2.0, 'concern_threshold': 0.5},
    'Direct_Delivery': {'target': 1.5, 'min_healthy': 0.5, 'concern_threshold': -1.0},
    'Activity_Programming': {'target': 2.0, 'min_healthy': 0.5, 'concern_threshold': -1.0},
    'Community_Human_Services': {'target': 0.5, 'min_healthy': -0.5, 'concern_threshold': -2.0},
    'Emergency_Logistics': {'target': 6.0, 'min_healthy': 4.0, 'concern_threshold': 2.0},
    'Cause_Advocacy_Research': {'target': 1.0, 'min_healthy': -0.5, 'concern_threshold': -2.5},
    'Intermediary_Public_Benefit': {'target': 12.0, 'min_healthy': 9.0, 'concern_threshold': 3.0},
    'Faith_Community': {'target': 2.0, 'min_healthy': 1.0, 'concern_threshold': 0.0},
    'Membership_Mutual_Benefit': {'target': 15.0, 'min_healthy': 12.0, 'concern_threshold': 6.0},
}

def get_operating_model(ntee1: str) -> str:
    """Derive operating model from NTEE1 code."""
    if not ntee1:
        return 'Activity_Programming'  # safe default
    ntee_code = ntee1.upper().strip()[0] if ntee1 else 'T'
    return NTEE1_TO_MODEL.get(ntee_code, 'Activity_Programming')

@dataclass
class FinancialContext:
    """Assessment of org financial health per stewardship principles."""
    status: str  # VERIFIED_HEALTHY, DATA_INCOMPLETE, FINANCIAL_NOTE
    months_reserve: Optional[float]
    peer_model: str
    peer_baseline: float
    peer_healthy_range: tuple  # (min, target)
    gap_from_baseline: Optional[float]
    confidence: str  # HIGH, MEDIUM, LOW
    explanation: str  # User-facing, never shaming
    data_issues: list  # ["negative_assets", "missing_revenue", etc]

def assess_financial_context(ein: str) -> FinancialContext:
    """
    Assess org financial health per stewardship framework.

    Returns context (VERIFIED_HEALTHY, DATA_INCOMPLETE, FINANCIAL_NOTE),
    never judgment labels.
    """
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    org = c.execute("""
        SELECT
            EIN, organization_name, NTEE1,
            total_revenue, total_assets, months_of_reserve
        FROM registry_enriched
        WHERE EIN = ?
    """, (ein,)).fetchone()

    conn.close()

    if not org:
        return FinancialContext(
            status='DATA_INCOMPLETE',
            months_reserve=None,
            peer_model='unknown',
            peer_baseline=0,
            peer_healthy_range=(0, 0),
            gap_from_baseline=None,
            confidence='LOW',
            explanation='Organization record not found. Data may still be loading.',
            data_issues=['org_not_found']
        )

    ein, name, ntee1, revenue, assets, months_reserve = org
    model = get_operating_model(ntee1)

    # Data quality checks (P6: detect errors immediately)
    data_issues = []
    if revenue is not None and revenue < 0:
        data_issues.append('negative_revenue')
    if assets is not None and assets < 0:
        data_issues.append('negative_assets')
    # If months_reserve is derived from invalid data (negative assets), treat it as invalid
    if months_reserve is not None and months_reserve < -10:  # Extreme deficit likely from data error
        data_issues.append('extreme_deficit')

    # Rule 1: Invalid data → DATA_INCOMPLETE (don't judge)
    if data_issues:
        return FinancialContext(
            status='DATA_INCOMPLETE',
            months_reserve=months_reserve,
            peer_model=model or 'unknown',
            peer_baseline=MODEL_BASELINES.get(model, {}).get('target', 0) if model else 0,
            peer_healthy_range=(0, 0),
            gap_from_baseline=None,
            confidence='LOW',
            explanation=f'Financial data needs verification (flagged issues: {", ".join(data_issues)}). We\'re updating with the latest IRS data.',
            data_issues=data_issues
        )

    # Rule 2: Missing data → DATA_INCOMPLETE (don't assume)
    if revenue is None or assets is None or months_reserve is None:
        return FinancialContext(
            status='DATA_INCOMPLETE',
            months_reserve=months_reserve,
            peer_model=model or 'unknown',
            peer_baseline=MODEL_BASELINES.get(model, {}).get('target', 0) if model else 0,
            peer_healthy_range=(0, 0),
            gap_from_baseline=None,
            confidence='MEDIUM',
            explanation='Financial data is incomplete. This organization may have limited recent filings, or we\'re still gathering their data.',
            data_issues=['missing_data']
        )

    # Get peer baseline for this model
    if not model or model not in MODEL_BASELINES:
        baseline = MODEL_BASELINES.get('Activity_Programming')  # default fallback
        model = 'Activity_Programming'
    else:
        baseline = MODEL_BASELINES[model]

    target = baseline['target']
    min_healthy = baseline['min_healthy']
    concern = baseline['concern_threshold']
    gap = months_reserve - target

    # Rule 3: Verified + healthy → VERIFIED_HEALTHY (P3: confident)
    if months_reserve >= min_healthy:
        return FinancialContext(
            status='VERIFIED_HEALTHY',
            months_reserve=months_reserve,
            peer_model=model,
            peer_baseline=target,
            peer_healthy_range=(min_healthy, target),
            gap_from_baseline=gap,
            confidence='HIGH',
            explanation=f"This organization's financial position is healthy relative to similar organizations in the {model} sector.",
            data_issues=[]
        )

    # Rule 4: Verified + strained → FINANCIAL_NOTE (P4/P5: context, not shame)
    if months_reserve >= concern:
        return FinancialContext(
            status='FINANCIAL_NOTE',
            months_reserve=months_reserve,
            peer_model=model,
            peer_baseline=target,
            peer_healthy_range=(min_healthy, target),
            gap_from_baseline=gap,
            confidence='HIGH',
            explanation=(
                f"This organization has tighter finances than its peer group (other {model} organizations). "
                f"Peer baseline: {target:.1f} months reserve. This org: {months_reserve:.1f} months. "
                f"\n\nPossible reasons: temporary deficit awaiting grants, board-approved mission expansion, "
                f"or genuine sustainability challenge. Consider reaching out directly to understand their strategy."
            ),
            data_issues=[]
        )

    # Rule 4b: Severe deficit → FINANCIAL_NOTE with stronger language (still respectful)
    return FinancialContext(
        status='FINANCIAL_NOTE',
        months_reserve=months_reserve,
        peer_model=model,
        peer_baseline=target,
        peer_healthy_range=(min_healthy, target),
        gap_from_baseline=gap,
        confidence='HIGH',
        explanation=(
            f"This organization shows significant financial strain. "
            f"Peer baseline: {target:.1f} months reserve. This org: {months_reserve:.1f} months. "
            f"\n\nIf you're interested in supporting their mission, we recommend contacting them directly "
            f"to discuss their financial strategy and whether board support, fundraising help, or "
            f"grant navigation would be valuable. Small organizations sometimes operate with tight margins "
            f"while doing important work."
        ),
        data_issues=[]
    )

def main():
    """Test framework on known org."""
    import sys
    ein = sys.argv[1] if len(sys.argv) > 1 else '471694019'
    org = assess_financial_context(ein)
    print(f"Status: {org.status}")
    print(f"Confidence: {org.confidence}")
    print(f"Model: {org.peer_model}")
    print(f"Months reserve: {org.months_reserve}")
    print(f"Peer baseline: {org.peer_baseline}")
    print(f"Gap: {org.gap_from_baseline}")
    print(f"\nExplanation:\n{org.explanation}")
    if org.data_issues:
        print(f"\nData issues: {org.data_issues}")

if __name__ == '__main__':
    main()
