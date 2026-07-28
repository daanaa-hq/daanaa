import React from 'react';

/**
 * V6 Financial Context Component
 *
 * Displays peer financial context using the v6 foundation methodology.
 *
 * Shows:
 * - Organization's financial data (if available)
 * - Peer group description and statistics
 * - Confidence level and limitations
 * - Conditional revenue-band context (if revenue missing)
 * - Methodology link and source information
 */

interface ConditionalBand {
  revenue_band: string;
  peer_median: number | null;
  peer_p25: number | null;
  peer_p75: number | null;
  peer_count: number;
  scoreable_peer_count: number;
  confidence: string;
  note: string;
}

interface V6ContextData {
  organization_ein: string;
  methodology_version: string;
  data_status: 'direct' | 'inferred' | 'insufficient_data' | 'not_found';
  ntee_code?: string;
  ntee_level?: string;
  geography_scope?: string;
  geography_value?: string;
  funding_archetype?: string;
  archetype_source?: string;
  revenue_band?: string;
  selected_tier?: string;
  peer_group_description?: string;
  metric_name?: string;
  organization_metric?: number | null;
  peer_median?: number | null;
  peer_p25?: number | null;
  peer_p75?: number | null;
  peer_count?: number;
  scoreable_peer_count?: number;
  confidence?: string;
  confidence_margin?: string;
  source_year_min?: number;
  source_year_max?: number;
  sources?: string[];
  limitations?: string[];
  reported_vs_inferred?: {
    archetype?: string;
    revenue_band?: string;
    peer_context?: string;
  };
  conditional_band_context?: {
    explanation: string;
    bands: ConditionalBand[];
    message?: string | null;
  };
}

interface V6FinancialContextProps {
  ein: string;
  context?: V6ContextData | null;
  loading?: boolean;
  error?: string | null;
}

export const V6FinancialContext: React.FC<V6FinancialContextProps> = ({
  ein,
  context,
  loading = false,
  error = null,
}) => {
  const yearRange = context?.source_year_min && context?.source_year_max
    ? `${context.source_year_min}–${context.source_year_max}`
    : 'available';
  const hasOrganizationMetric = context?.organization_metric !== null && context?.organization_metric !== undefined;
  const isPeerReference = context?.data_status === 'inferred' || !hasOrganizationMetric;
  const contextLabel = context?.data_status === 'insufficient_data' ? 'Limited context' : isPeerReference ? 'Peer reference' : 'Reported context';

  if (loading) {
    return <div className="p-4 text-sm text-gray-600" role="status">Loading financial context...</div>;
  }

  if (error) {
    return <div className="p-4 text-sm text-red-600" role="alert">We couldn’t load this financial context. Please try again later.</div>;
  }

  if (!context || context.data_status === 'not_found') {
    return (
      <div className="p-4 border border-gray-200 rounded bg-gray-50">
        <p className="text-sm text-gray-700">
          We do not have enough public information for a numeric comparison yet. This is a data limitation, not a judgment.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex flex-wrap items-center gap-3 mb-2">
          <h3 className="text-lg font-semibold">Peer financial context</h3>
          <span className="inline-flex rounded-full border border-soft-gold/40 bg-soft-gold/10 px-2.5 py-1 text-xs font-medium text-deep-navy">{contextLabel}</span>
        </div>
        <p className="text-sm text-gray-600">Peer context from {yearRange} public filings</p>
        <p className="text-sm text-gray-600 mt-2">{isPeerReference ? "The peer figures below are a reference for similar organizations, not this organization’s actual finances." : "The reported figure is shown alongside a comparable peer group. This is context, not a rating or assessment of mission effectiveness."}</p>
      </div>

      {/* How this context was built — context, not a rating */}
      <div className="rounded-xl border border-light-grey p-4 bg-soft-cream">
        <p className="text-sm font-medium text-deep-navy">How this context was built</p>
        <p className="text-sm text-cool-grey mt-1">
          {context.peer_group_description}
        </p>
        <p className="text-xs text-cool-grey mt-2">
          {context.confidence_margin ? `Uncertainty: ${context.confidence_margin}` : 'Uncertainty: Limited'}
        </p>
      </div>

      {/* Reported data and peer reference */}
      {context.reported_vs_inferred && (
        <div className="bg-gray-50 p-3 rounded text-sm">
          <p className="font-medium text-gray-900 mb-2">What this comparison uses</p>
          <ul className="space-y-1 text-gray-700">
            {context.reported_vs_inferred.archetype && (
              <li>Funding model: {context.reported_vs_inferred.archetype}</li>
            )}
            {context.reported_vs_inferred.revenue_band && (
              <li>Revenue band: {context.reported_vs_inferred.revenue_band}</li>
            )}
            {context.reported_vs_inferred.peer_context && (
              <li>Peer comparison: {context.reported_vs_inferred.peer_context}</li>
            )}
          </ul>
        </div>
      )}

      {/* Main peer comparison (Tier 1-4) */}
      {context.selected_tier && context.data_status !== 'insufficient_data' && !context.selected_tier.toLowerCase().includes('archetype') && (
        <div className="border rounded p-4 bg-white">
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            {context.organization_metric !== null && context.organization_metric !== undefined ? (
              <div>
                <p className="text-xs font-medium text-gray-600 uppercase">This organization</p>
                <p className="text-xl font-semibold text-gray-900">
                  {context.organization_metric.toFixed(1)} mo
                </p>
                <p className="text-xs text-gray-500 mt-1">Reported reserve metric</p>
              </div>
            ) : (
              <div>
                <p className="text-xs font-medium text-gray-600 uppercase">This organization</p>
                <p className="text-sm text-gray-600 italic">Not reported</p>
              </div>
            )}

            {isPeerReference && (
              <p className="col-span-2 md:col-span-4 text-xs text-cool-grey">No organization-level figure is being inferred from the peer group.</p>
            )}

            {context.peer_median !== null && context.peer_median !== undefined && (
              <div>
                <p className="text-xs font-medium text-gray-600 uppercase">Peer median</p>
                <p className="text-xl font-semibold text-gray-900">
                  {context.peer_median.toFixed(1)} mo
                </p>
                <p className="text-xs text-gray-500 mt-1">Peer reference group</p>
              </div>
            )}

            {context.peer_p25 !== null && context.peer_p75 !== null && (
              <div>
                <p className="text-xs font-medium text-gray-600 uppercase">Typical peer range</p>
                <p className="text-xl font-semibold text-gray-900">
                  {context.peer_p25!.toFixed(1)}–{context.peer_p75!.toFixed(1)} mo
                </p>
                <p className="text-xs text-gray-500 mt-1">25th–75th percentile</p>
              </div>
            )}

            <div>
              <p className="text-xs font-medium text-gray-600 uppercase">Peer group size</p>
              <p className="text-xl font-semibold text-gray-900">
                {context.scoreable_peer_count ?? context.peer_count}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {context.scoreable_peer_count === context.peer_count
                  ? 'with data'
                  : `with data of ${context.peer_count}`}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Conditional bands (Tier 2 without revenue) */}
      {context.conditional_band_context && (
        <div className="border rounded p-4 bg-yellow-50 border-yellow-200">
          <p className="text-sm font-medium text-deep-navy mb-3">
            Peer reference by revenue level
          </p>
          <p className="text-sm text-cool-grey mb-4 italic">
            {context.conditional_band_context.explanation}
          </p>

          {context.conditional_band_context.bands.length === 0 ? (
            <p className="text-sm text-cool-grey">
              {context.conditional_band_context.message ||
                'No conditional numeric comparison is available yet.'}
            </p>
          ) : <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-yellow-100">
                <tr>
                   <th scope="col" className="px-3 py-2 text-left font-medium text-deep-navy">Revenue band</th>
                   <th scope="col" className="px-3 py-2 text-right font-medium text-deep-navy">Median (mo)</th>
                   <th scope="col" className="px-3 py-2 text-right font-medium text-deep-navy">Range (mo)</th>
                   <th scope="col" className="px-3 py-2 text-right font-medium text-deep-navy">Peers</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-yellow-200">
                {context.conditional_band_context.bands.map((band) => (
                  <tr key={band.revenue_band} className="hover:bg-yellow-100">
                    <td className="px-3 py-2 text-deep-navy">{band.revenue_band}</td>
                    <td className="px-3 py-2 text-right text-deep-navy">
                      {band.peer_median?.toFixed(1) ?? '—'}
                    </td>
                    <td className="px-3 py-2 text-right text-deep-navy text-xs">
                      {band.peer_p25 && band.peer_p75
                        ? `${band.peer_p25.toFixed(1)}–${band.peer_p75.toFixed(1)}`
                        : '—'}
                    </td>
                    <td className="px-3 py-2 text-right text-deep-navy">
                      {band.scoreable_peer_count}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>}
        </div>
      )}

      {/* Archetype-only context */}
      {(context.data_status === 'insufficient_data' || context.selected_tier?.toLowerCase().includes('archetype')) && (
        <div className="bg-purple-50 border border-purple-200 rounded p-4">
          <p className="text-sm font-medium text-purple-900 mb-2">Descriptive context only</p>
          <p className="text-sm text-purple-800">
            We do not have enough public information for a numeric comparison yet. This is a data limitation, not a judgment.
            {context.funding_archetype && <> The available public records suggest a {context.funding_archetype} funding pattern, but that does not describe the organization's actual finances.</>}
          </p>
          <p className="text-xs text-purple-700 mt-3 italic">
            No numeric comparison is shown because the available evidence is limited.
          </p>
        </div>
      )}

      {/* Limitations */}
      {context.limitations && context.limitations.length > 0 && (
        <div className="text-sm bg-gray-50 p-3 rounded">
          <p className="font-medium text-gray-900 mb-2">Limitations</p>
          <ul className="list-disc pl-5 space-y-1 text-gray-700">
            {context.limitations.map((limitation, idx) => (
              <li key={idx}>{limitation}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Details and sources */}
      {context.sources && context.sources.length > 0 && (
        <div className="text-xs text-gray-600 border-t pt-4">
          <p className="font-medium text-gray-700 mb-2">Data sources</p>
          <ul className="space-y-1">
            {context.sources.map((source, idx) => (
              <li key={idx}>• {source}</li>
            ))}
          </ul>
          <p className="mt-2">
            <a
              href="/methodology"
              className="text-blue-600 hover:underline">
              Learn more about our methodology →
            </a>
          </p>
        </div>
      )}
    </div>
  );
};

export default V6FinancialContext;
