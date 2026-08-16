"""
V6 Financial Context API Handler

Implements /api/organizations/{ein}/financial-context endpoint.
Returns comprehensive peer context using normalized v6 data foundation.

Uses v6 by default; ENABLE_V6_FINANCIAL_CONTEXT=false is an emergency rollback switch.
"""

import sqlite3
import json
import os
from datetime import datetime

ENABLE_V6 = os.environ.get('ENABLE_V6_FINANCIAL_CONTEXT', 'true').lower() == 'true'
V6_CANDIDATE_RUN_ID = os.environ.get(
    'V6_CANDIDATE_RUN_ID',
    'v6_foundation_candidate_20260727_revocation_refresh',
)

def get_v6_financial_context(db, ein):
    """
    Fetch v6 financial context for an organization.

    Returns:
    {
        organization_ein,
        methodology_version,
        data_status,
        ntee_code,
        ntee_level,
        geography_scope,
        geography_value,
        funding_archetype,
        archetype_source,
        archetype_confidence,
        revenue_band,
        revenue_band_source,
        selected_tier,
        peer_group_description,
        metric_name,
        organization_metric,
        peer_median,
        peer_p25,
        peer_p75,
        peer_count,
        scoreable_peer_count,
        confidence,
        confidence_margin,
        source_year_min,
        source_year_max,
        sources,
        limitations,
        conditional_band_context (if revenue missing)
    }
    """

    if not ENABLE_V6:
        return None  # Feature disabled

    try:
        # Get v6 assignment for this org from the active candidate run
        assignment_sql = '''
            SELECT
                v.run_id,
                v.EIN AS ein,
                v.selected_tier,
                v.ntee_level,
                v.ntee_code,
                v.geography_scope,
                v.geography_value,
                v.revenue_band,
                v.revenue_band_source,
                v.peer_group_key,
                v.peer_group_description,
                v.peer_count,
                v.scoreable_peer_count,
                v.metric_name,
                v.metric_value,
                v.peer_median,
                v.peer_p25,
                v.peer_p75,
                v.source_year_min,
                v.source_year_max,
                v.confidence,
                v.confidence_margin,
                v.is_inferred,
                org.merit_archetype_v5 AS archetype,
                r.scorer_version AS methodology_version
            FROM v6_peer_context_assignments v
            JOIN v6_scoring_runs r ON v.run_id = r.run_id
            LEFT JOIN registry_enriched org ON org.EIN = v.EIN
            WHERE v.ein = ? AND v.run_id = ? AND r.status IN ('candidate', 'active')
            LIMIT 1
        '''

        assignment = db.execute(assignment_sql, (ein, V6_CANDIDATE_RUN_ID)).fetchone()
        if not assignment:
            return {
                'organization_ein': ein,
                'methodology_version': 'v6.1-foundation-candidate',
                'data_status': 'insufficient_data',
                'selected_tier': '5_archetype_only',
                'peer_group_description': 'We do not have enough public records to make a numeric peer comparison yet.',
                'funding_archetype': None,
                'confidence': 'limited',
                'confidence_margin': 'Limited evidence',
                'sources': ['IRS public filings', 'Public nonprofit datasets'],
                'limitations': ['No sufficiently complete public financial record for a numeric comparison'],
                'message': 'We do not have enough public information for a numeric comparison yet. This is a data limitation, not a judgment.'
            }

        assignment_dict = dict(assignment)

        # Get organization's actual financial data
        org_sql = '''
            SELECT
                total_revenue,
                total_expenses,
                net_assets,
                months_of_reserve
            FROM registry_enriched
            WHERE EIN = ?
        '''
        org_data = db.execute(org_sql, (ein,)).fetchone()
        organization_metric = None
        if org_data and org_data['net_assets'] and org_data['total_expenses'] and org_data['total_expenses'] > 0:
            organization_metric = (org_data['net_assets'] / org_data['total_expenses']) * 12

        # Build response
        context = {
            'organization_ein': assignment_dict['ein'],
            'methodology_version': assignment_dict['methodology_version'],
            'data_status': 'direct' if not assignment_dict['is_inferred'] else 'inferred',
            'ntee_code': assignment_dict['ntee_code'],
            'ntee_level': assignment_dict['ntee_level'],
            'geography_scope': assignment_dict['geography_scope'],
            'geography_value': assignment_dict['geography_value'],
            'funding_archetype': assignment_dict['archetype'],
            'archetype_source': 'inferred_from_revenue' if assignment_dict['is_inferred'] else 'reported',
            'archetype_confidence': 'high' if not assignment_dict['is_inferred'] else 'medium',
            'revenue_band': assignment_dict['revenue_band'],
            'revenue_band_source': assignment_dict['revenue_band_source'],
            'selected_tier': assignment_dict['selected_tier'],
            'peer_group_description': assignment_dict['peer_group_description'],
            'metric_name': 'months_of_reserve',
            'organization_metric': organization_metric,
            'peer_median': assignment_dict['peer_median'],
            'peer_p25': assignment_dict['peer_p25'],
            'peer_p75': assignment_dict['peer_p75'],
            'peer_count': assignment_dict['peer_count'],
            'scoreable_peer_count': assignment_dict['scoreable_peer_count'],
            'confidence': assignment_dict['confidence'],
            'confidence_margin': assignment_dict['confidence_margin'],
            'source_year_min': assignment_dict['source_year_min'],
            'source_year_max': assignment_dict['source_year_max'],
            'sources': [
                'IRS Form 990 (public filings)',
                'ProPublica nonprofit database',
                'NCCS research data'
            ],
            'limitations': _get_limitations(assignment_dict),
            'reported_vs_inferred': {
                'archetype': 'inferred' if assignment_dict['is_inferred'] else 'reported',
                'revenue_band': assignment_dict['revenue_band_source'] or 'unknown',
                'peer_context': 'inferred' if assignment_dict['peer_median'] is not None else 'unavailable'
            }
        }

        # If organization is Tier 2 (Regional Conditional) with missing revenue,
        # include conditional band context
        if (
            assignment_dict['selected_tier'] in ('2_regional_conditional', '2_Regional_Conditional')
            and not assignment_dict['revenue_band']
        ):
            context['peer_median'] = None
            context['peer_p25'] = None
            context['peer_p75'] = None
            context['conditional_band_context'] = _get_conditional_bands(db, assignment_dict)

        return context

    except Exception as e:
        return {
            'error': f'Error fetching financial context: {str(e)}',
            'organization_ein': ein,
            'methodology_version': 'v6_foundation'
        }


def _get_limitations(assignment):
    """Generate limitations text based on tier and data availability."""

    limitations = []

    tier = assignment.get('selected_tier', '')
    scoreable = assignment.get('scoreable_peer_count', 0)

    if scoreable < 30:
        limitations.append('Limited peer group size')
    if scoreable < 10:
        limitations.append('Very limited peer data')
    if tier in ('3_broader_regional', '3_Broader_Regional'):
        limitations.append('Broader peer group (fewer exact matches)')
    if tier in ('4_national', '4_National'):
        limitations.append('National peer group (geographic variation)')
    if tier in ('5_archetype_only', '5_Archetype_Only'):
        limitations.append('No numeric comparison available')
    if assignment.get('is_inferred'):
        limitations.append('Archetype inferred from revenue composition')

    return limitations if limitations else None


def _get_conditional_bands(db, assignment):
    """Fetch conditional revenue-band context for orgs without direct revenue data."""

    try:
        sql = '''
            SELECT
                revenue_band,
                median_reserves AS peer_median,
                p25_reserves AS peer_p25,
                p75_reserves AS peer_p75,
                peer_count,
                scoreable_peer_count,
                confidence
            FROM v6_conditional_band_context
            WHERE run_id = ?
              AND peer_group_key = ?
              AND scoreable_peer_count >= 5
            ORDER BY revenue_band
        '''

        rows = db.execute(
            sql,
            (assignment['run_id'], assignment['peer_group_key']),
        ).fetchall()
        bands = []
        for row in rows:
            bands.append({
                'revenue_band': row['revenue_band'],
                'peer_median': row['peer_median'],
                'peer_p25': row['peer_p25'],
                'peer_p75': row['peer_p75'],
                'peer_count': row['peer_count'],
                'scoreable_peer_count': row['scoreable_peer_count'],
                'confidence': row['confidence'],
                'note': f'Based on {row["scoreable_peer_count"]} peer organizations in this revenue band'
            })

        return {
            'explanation': 'Revenue information was not available for this organization. The table below shows financial context for organizations in the same peer group across different revenue bands. This is not an assessment of this organization.',
            'bands': bands,
            'message': (
                'No revenue band currently has enough scoreable peers for a '
                'numeric comparison.'
                if not bands else None
            ),
        }
    except Exception:
        return None
