"""
V6 Financial Context API Handler.

Implements /api/organizations/{ein}/financial-context from the current v6
values materialized by the nightly scorer in registry_enriched.

ENABLE_V6_FINANCIAL_CONTEXT=false remains an emergency rollback switch.
"""

import os


ENABLE_V6 = os.environ.get('ENABLE_V6_FINANCIAL_CONTEXT', 'true').lower() == 'true'


def get_v6_financial_context(db, ein):
    """Fetch persisted v6 financial context for an organization."""

    if not ENABLE_V6:
        return None

    try:
        row = db.execute('''
            SELECT
                EIN AS ein,
                scoring_tier,
                tier_label,
                peer_group_size_v6,
                peer_group_description_v6,
                confidence_v6,
                confidence_margin_v6,
                merit_percentile_v6,
                merit_percentile_confidence_v6,
                merit_peer_count_v6_scoreable,
                is_inferred_v6,
                merit_archetype_v5,
                merit_archetype_v5_label,
                merit_band_v5_label,
                total_revenue,
                total_expenses,
                net_assets,
                months_of_reserve
            FROM registry_enriched
            WHERE EIN = ?
            LIMIT 1
        ''', (ein,)).fetchone()

        if not row:
            return {
                'organization_ein': ein,
                'methodology_version': 'v6',
                'data_status': 'insufficient_data',
                'selected_tier': None,
                'peer_group_description': None,
                'funding_archetype': None,
                'confidence': None,
                'confidence_margin': None,
                'sources': None,
                'limitations': ['No registry record was found for this EIN.'],
                'message': 'We do not have enough public information for a numeric comparison yet. This is a data limitation, not a judgment.',
            }

        assignment = dict(row)
        is_inferred = bool(assignment['is_inferred_v6'])
        selected_tier = assignment['scoring_tier']

        return {
            'organization_ein': assignment['ein'],
            'methodology_version': 'v6',
            'data_status': 'inferred' if is_inferred else 'direct',
            # These fields are retained for response compatibility, but v6's
            # current materialized schema does not provide values for them.
            'ntee_code': None,
            'ntee_level': None,
            'geography_scope': None,
            'geography_value': None,
            'funding_archetype': assignment['merit_archetype_v5'],
            'funding_archetype_label': assignment['merit_archetype_v5_label'],
            'archetype_source': None,
            'archetype_confidence': None,
            'revenue_band': assignment['merit_band_v5_label'],
            'revenue_band_source': None,
            'selected_tier': selected_tier,
            'tier_label': assignment['tier_label'],
            'peer_group_description': assignment['peer_group_description_v6'],
            'metric_name': 'months_of_reserve',
            'organization_metric': assignment['months_of_reserve'],
            'peer_median': None,
            'peer_p25': None,
            'peer_p75': None,
            'peer_count': assignment['peer_group_size_v6'],
            'scoreable_peer_count': assignment['merit_peer_count_v6_scoreable'],
            'confidence': assignment['confidence_v6'],
            'confidence_margin': assignment['confidence_margin_v6'],
            'merit_percentile': assignment['merit_percentile_v6'],
            'merit_percentile_confidence': assignment['merit_percentile_confidence_v6'],
            'source_year_min': None,
            'source_year_max': None,
            'sources': None,
            'limitations': _get_limitations(assignment),
            'reported_vs_inferred': {
                'peer_context': 'inferred' if is_inferred else 'direct',
            },
            # No replacement exists for the dropped conditional-band table.
            'conditional_band_context': None,
            'total_revenue': assignment['total_revenue'],
            'total_expenses': assignment['total_expenses'],
            'net_assets': assignment['net_assets'],
        }

    except Exception as exc:
        return {
            'error': f'Error fetching financial context: {str(exc)}',
            'organization_ein': ein,
            'methodology_version': 'v6',
        }


def _get_limitations(assignment):
    """Generate limitations from the persisted v6 tier and peer counts."""

    limitations = []
    tier = assignment.get('scoring_tier')
    scoreable = assignment.get('merit_peer_count_v6_scoreable')

    if scoreable is None:
        limitations.append('The scoreable peer count is unavailable.')
    elif scoreable < 10:
        limitations.append('Very limited peer data')
    elif scoreable < 30:
        limitations.append('Limited peer group size')

    if tier == '2_Regional_Context':
        limitations.append('Comparison uses a national peer group because a sufficiently large regional group was unavailable.')
    elif tier == '3_Broad_Category':
        limitations.append('Comparison uses a broader category without a revenue band because a more specific peer group was unavailable.')
    elif tier == '3b_Broad_Category':
        limitations.append('Comparison uses a broad category and revenue band because a more specific peer group was unavailable.')
    elif tier == '4_Archetype_Only':
        limitations.append('No numeric peer comparison is available.')
    elif tier is None:
        limitations.append('No v6 peer-context tier is available.')

    if assignment.get('total_revenue') in (None, 0):
        limitations.append('No revenue band is available because revenue is missing or zero.')
    if assignment.get('is_inferred_v6'):
        limitations.append('The peer context is marked as inferred.')

    return limitations or None
