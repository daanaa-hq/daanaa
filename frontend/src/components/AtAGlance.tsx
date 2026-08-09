import { useEffect } from 'react'
import { ApiOrganization } from '../data/api'
import { trackAtAGlanceVisible } from '../utils/analytics'

/**
 * AtAGlance: Small Org Clarity Display
 *
 * Surfaces existing data to help donors understand small orgs better:
 * - Leadership: board size, independence, staff, governance policies
 * - Service Scope: cause area, geography, revenue band
 * - Stability: composite health signal (At-risk to Excellent)
 * - Mission Attribution: source transparency (claimed vs. extracted)
 *
 * All data sourced from Form 990 + website extraction; no new collection.
 * Stewardship P3 (evidence-based), P4 (small org fairness), P5/P6 (honest transparency).
 *
 * Phase 3 measurement: Tracks visibility to measure if better display of context
 * helps small orgs reach parity with large orgs (Gate A.1 reliability).
 */
export default function AtAGlance({ org }: { org: ApiOrganization }) {
  const { leadership_info, service_scope, org_stability_signal, mission_attribution } = org

  // Track when this section becomes visible for Phase 3 measurement (Gate A.1)
  useEffect(() => {
    trackAtAGlanceVisible(service_scope?.revenue_band)
  }, [service_scope?.revenue_band])

  // Don't render if we have no new data
  if (!leadership_info && !service_scope && !org_stability_signal && !mission_attribution) {
    return null
  }

  const stabilityColors: Record<string, { bgClass: string; borderClass: string; textColor: string; label: string }> = {
    'Excellent': { bgClass: 'bg-green-50', borderClass: 'border-green-200', textColor: '#15803d', label: 'Excellent' },
    'Strong': { bgClass: 'bg-blue-50', borderClass: 'border-blue-200', textColor: '#1e40af', label: 'Strong' },
    'Solid': { bgClass: 'bg-blue-50', borderClass: 'border-blue-200', textColor: '#1e40af', label: 'Solid' },
    'Emerging': { bgClass: 'bg-amber-50', borderClass: 'border-amber-200', textColor: '#b45309', label: 'Emerging' },
    'At-risk': { bgClass: 'bg-red-50', borderClass: 'border-red-200', textColor: '#dc2626', label: 'At-risk' },
  }

  const missionSourceLabels: Record<string, { label: string; explanation: string }> = {
    'claimed': { label: 'Organization provided', explanation: 'This mission statement was provided by the nonprofit directly.' },
    'ai_web': { label: 'Website extracted', explanation: 'This mission was extracted from the nonprofit\'s website.' },
    'ai_ntee': { label: 'Category template', explanation: 'This is a template mission for this type of nonprofit.' },
    'extracted': { label: 'Website extracted', explanation: 'This mission was extracted from the nonprofit\'s website.' },
  }

  const signal = org_stability_signal?.signal as string | null
  const signalColor = signal ? stabilityColors[signal] : null

  return (
    <div className="mb-12">
      {/* Section title */}
      <h2 className="font-display italic text-deep-navy text-title-sm mb-6">At a glance</h2>

      {/* 4-column grid: Leadership | Service Scope | Stability | Mission Attribution */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">

        {/* Leadership Info */}
        {leadership_info && (leadership_info.board_size || leadership_info.employee_count ||
                            leadership_info.has_coi_policy || leadership_info.has_whistleblower_policy) && (
          <div className="rounded-xl p-5 bg-white border border-light-grey">
            <h3 className="font-body text-small font-semibold text-deep-navy mb-3">Leadership</h3>
            <div className="space-y-2 font-body text-small text-cool-grey">
              {leadership_info.board_size !== null && leadership_info.board_size !== undefined && (
                <div className="flex items-center justify-between">
                  <span>Board size</span>
                  <span className="font-medium text-deep-navy">{leadership_info.board_size}</span>
                </div>
              )}
              {leadership_info.board_independence_pct !== null && leadership_info.board_independence_pct !== undefined && (
                <div className="flex items-center justify-between">
                  <span>Independent directors</span>
                  <span className="font-medium text-deep-navy">{leadership_info.board_independence_pct}%</span>
                </div>
              )}
              {leadership_info.employee_count !== null && leadership_info.employee_count !== undefined && (
                <div className="flex items-center justify-between">
                  <span>Employees</span>
                  <span className="font-medium text-deep-navy">{leadership_info.employee_count}</span>
                </div>
              )}
              <div className="pt-2 border-t border-light-grey/50 space-y-1">
                {leadership_info.has_coi_policy && (
                  <div className="flex items-center gap-1.5">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                    <span className="text-xs">Conflict of Interest Policy</span>
                  </div>
                )}
                {leadership_info.has_whistleblower_policy && (
                  <div className="flex items-center gap-1.5">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                    <span className="text-xs">Whistleblower Policy</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Service Scope */}
        {service_scope && (service_scope.primary_cause_area || service_scope.service_states || service_scope.revenue_band) && (
          <div className="rounded-xl p-5 bg-white border border-light-grey">
            <h3 className="font-body text-small font-semibold text-deep-navy mb-3">Service Scope</h3>
            <div className="space-y-2 font-body text-small text-cool-grey">
              {service_scope.primary_cause_area && (
                <div>
                  <div className="text-xs uppercase tracking-wider text-cool-grey/60 mb-0.5">Focus area</div>
                  <div className="font-medium text-deep-navy">{service_scope.primary_cause_area}</div>
                </div>
              )}
              {service_scope.service_states && service_scope.service_states.length > 0 && (
                <div>
                  <div className="text-xs uppercase tracking-wider text-cool-grey/60 mb-0.5">Serves</div>
                  <div className="font-medium text-deep-navy">{service_scope.service_states.join(', ')}</div>
                </div>
              )}
              {service_scope.revenue_band && (
                <div>
                  <div className="text-xs uppercase tracking-wider text-cool-grey/60 mb-0.5">Size</div>
                  <div className="font-medium text-deep-navy">{service_scope.revenue_band}</div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Org Stability Signal */}
        {org_stability_signal && signal && signalColor && (
          <div className={`rounded-xl p-5 border-2 ${signalColor.bgClass} ${signalColor.borderClass}`} role="status">
            <h3 className="font-body text-small font-semibold mb-3 text-deep-navy">Stability</h3>
            <div className="inline-block px-3 py-1.5 rounded-full font-body text-small font-semibold mb-3 text-white" style={{ backgroundColor: signalColor.textColor }}>
              {signal}
            </div>
            {org_stability_signal.reasons && org_stability_signal.reasons.length > 0 && (
              <div className="space-y-1">
                {org_stability_signal.reasons.slice(0, 3).map((reason, idx) => (
                  <div key={idx} className="font-body text-small flex items-start gap-1.5" style={{ color: signalColor.textColor }}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" className="mt-0.5 shrink-0">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                    <span>{reason}</span>
                  </div>
                ))}
              </div>
            )}
            <div className="mt-3 font-body text-xs text-cool-grey/60">
              {org_stability_signal.confidence === 'high' ? 'High confidence' : 'Moderate confidence'}
            </div>
          </div>
        )}

        {/* Mission Attribution */}
        {mission_attribution && mission_attribution.source && (
          <div className="rounded-xl p-5 bg-white border border-light-grey">
            <h3 className="font-body text-small font-semibold text-deep-navy mb-3">Mission Source</h3>
            <div className="space-y-2">
              {mission_attribution.source && (
                <div>
                  <span className="inline-flex items-center px-2.5 py-1 rounded-full bg-soft-gold/20 text-deep-gold font-body text-xs font-medium mb-2">
                    {missionSourceLabels[mission_attribution.source]?.label || 'Unknown source'}
                  </span>
                  <p className="font-body text-xs text-cool-grey leading-relaxed">
                    {missionSourceLabels[mission_attribution.source]?.explanation}
                  </p>
                </div>
              )}
              {mission_attribution.verified_date && (
                <div className="pt-2 border-t border-light-grey/50">
                  <p className="font-body text-xs text-cool-grey/60">
                    Last verified {new Date(mission_attribution.verified_date).toLocaleDateString('en-US', { year: 'numeric', month: 'short' })}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

      </div>
    </div>
  )
}
