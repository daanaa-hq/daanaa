import React, { useMemo } from 'react';

/**
 * V6 Financial Context Component
 *
 * Displays peer financial context using the v6 foundation methodology.
 * Feature-flagged: only renders when VITE_ENABLE_V6_FINANCIAL_CONTEXT=true
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
  const enabled = import.meta.env.VITE_ENABLE_V6_FINANCIAL_CONTEXT === 'true';

  if (!enabled) {
    return null; // Feature not enabled
  }

  if (loading) {
    return <div className="p-4 text-sm text-gray-600">Loading financial context...</div>;
  }

  if (error) {
    return <div className="p-4 text-sm text-red-600">Error loading financial context: {error}</div>;
  }

  if (!context || context.data_status === 'not_found') {
    return (
      <div className="p-4 border border-gray-200 rounded bg-gray-50">
        <p className="text-sm text-gray-700">
          Financial context not yet available for this organization.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h3 className="text-lg font-semibold mb-2">Financial Context</h3>
        <p className="text-sm text-gray-600">
          Peer comparison from {context.source_year_min}–{context.source_year_max} IRS filings
        </p>
      </div>

      {/* How this context was built */}
      <div className="border-l-4 border-blue-500 pl-4 py-2 bg-blue-50">
        <p className="text-sm font-medium text-blue-900">How this context was built</p>
        <p className="text-sm text-blue-800 mt-1">
          {context.peer_group_description}
        </p>
        <p className="text-xs text-blue-700 mt-2">
          {context.confidence_margin ? `Confidence: ${context.confidence_margin}` : 'Confidence: Limited'}
        </p>
      </div>

      {/* Direct vs Inferred */}
      {context.reported_vs_inferred && (
        <div className="bg-gray-50 p-3 rounded text-sm">
          <p className="font-medium text-gray-900 mb-2">Data source</p>
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
      {context.selected_tier && !context.selected_tier.startsWith('5_') && (
        <div className="border rounded p-4 bg-white">
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            {context.organization_metric !== null && context.organization_metric !== undefined ? (
              <div>
                <p className="text-xs font-medium text-gray-600 uppercase">This org</p>
                <p className="text-xl font-semibold text-gray-900">
                  {context.organization_metric.toFixed(1)} mo
                </p>
                <p className="text-xs text-gray-500 mt-1">Operating reserve</p>
              </div>
            ) : (
              <div>
                <p className="text-xs font-medium text-gray-600 uppercase">This org</p>
                <p className="text-sm text-gray-600 italic">Not reported</p>
              </div>
            )}

            {context.peer_median !== null && context.peer_median !== undefined && (
              <div>
                <p className="text-xs font-medium text-gray-600 uppercase">Peer median</p>
                <p className="text-xl font-semibold text-gray-900">
                  {context.peer_median.toFixed(1)} mo
                </p>
                <p className="text-xs text-gray-500 mt-1">Similar orgs</p>
              </div>
            )}

            {context.peer_p25 !== null && context.peer_p75 !== null && (
              <div>
                <p className="text-xs font-medium text-gray-600 uppercase">Typical range</p>
                <p className="text-xl font-semibold text-gray-900">
                  {context.peer_p25.toFixed(1)}–{context.peer_p75.toFixed(1)} mo
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
          <p className="text-sm font-medium text-yellow-900 mb-3">
            Peer context by revenue level
          </p>
          <p className="text-sm text-yellow-800 mb-4 italic">
            {context.conditional_band_context.explanation}
          </p>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-yellow-100">
                <tr>
                  <th className="px-3 py-2 text-left font-medium text-yellow-900">Revenue band</th>
                  <th className="px-3 py-2 text-right font-medium text-yellow-900">Median (mo)</th>
                  <th className="px-3 py-2 text-right font-medium text-yellow-900">Range (mo)</th>
                  <th className="px-3 py-2 text-right font-medium text-yellow-900">Peers</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-yellow-200">
                {context.conditional_band_context.bands.map((band) => (
                  <tr key={band.revenue_band} className="hover:bg-yellow-100">
                    <td className="px-3 py-2 text-yellow-900">{band.revenue_band}</td>
                    <td className="px-3 py-2 text-right text-yellow-900">
                      {band.peer_median?.toFixed(1) ?? '—'}
                    </td>
                    <td className="px-3 py-2 text-right text-yellow-900 text-xs">
                      {band.peer_p25 && band.peer_p75
                        ? `${band.peer_p25.toFixed(1)}–${band.peer_p75.toFixed(1)}`
                        : '—'}
                    </td>
                    <td className="px-3 py-2 text-right text-yellow-900">
                      {band.scoreable_peer_count}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tier 5 (Archetype only) */}
      {context.selected_tier?.startsWith('5_') && (
        <div className="bg-purple-50 border border-purple-200 rounded p-4">
          <p className="text-sm font-medium text-purple-900 mb-2">Limited context available</p>
          <p className="text-sm text-purple-800">
            This organization has limited publicly available financial data. However, organizations with a{' '}
            <em>{context.funding_archetype}</em> funding model typically operate with varying financial patterns.
          </p>
          <p className="text-xs text-purple-700 mt-3 italic">
            Numeric comparison not available for this organization.
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

      {/* Data sources */}
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
              className="text-blue-600 hover:underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              Learn more about our methodology →
            </a>
          </p>
        </div>
      )}
    </div>
  );
};

export default V6FinancialContext;
