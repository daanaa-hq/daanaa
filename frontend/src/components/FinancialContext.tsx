import type { ApiOrganization } from '../data/api'

interface FinancialContextProps {
  org: ApiOrganization
}

export default function FinancialContext({ org }: FinancialContextProps) {
  if (!org.financial_context) return null

  const fc = org.financial_context
  const isIncomplete = fc.status === 'DATA_INCOMPLETE'
  const isHealthy = fc.status === 'VERIFIED_HEALTHY'
  const isNote = fc.status === 'FINANCIAL_NOTE'

  // Color schemes per status type
  const getStyle = () => {
    if (isIncomplete) {
      return {
        bg: 'bg-slate-50',
        border: 'border-slate-200',
        label: 'text-slate-600',
        badge: 'bg-slate-100 text-slate-700',
      }
    }
    if (isHealthy) {
      return {
        bg: 'bg-green-50',
        border: 'border-green-200',
        label: 'text-green-700',
        badge: 'bg-green-100 text-green-700',
      }
    }
    // FINANCIAL_NOTE
    return {
      bg: 'bg-amber-50',
      border: 'border-amber-200',
      label: 'text-amber-700',
      badge: 'bg-amber-100 text-amber-700',
    }
  }

  const style = getStyle()

  return (
    <div className={`rounded-lg border p-6 ${style.bg} ${style.border}`}>
      <div className="space-y-5">
        {/* Header with status badge */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <h3 className={`font-body text-xs tracking-widest uppercase font-semibold ${style.label}`}>
              Financial Health Assessment
            </h3>
            <p className={`font-body text-lg font-semibold mt-2 ${style.label}`}>
              {isIncomplete && 'Data Under Verification'}
              {isHealthy && 'Healthy Financial Position'}
              {isNote && 'Financially Strained'}
            </p>
          </div>
          <span className={`inline-block px-3 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap ${style.badge}`}>
            {fc.confidence} confidence
          </span>
        </div>

        {/* Peer comparison (if available) */}
        {!isIncomplete && fc.peer_model && (
          <div className="space-y-3">
            <div className="text-xs text-cool-grey">
              Peer group: <span className="font-semibold">{fc.peer_model.replace(/_/g, ' ')}</span>
            </div>
            <div className="grid grid-cols-2 gap-6">
              <div className="text-center">
                <span className="block text-xs text-cool-grey mb-1.5">Peer Baseline</span>
                <span className={`block font-body text-3xl font-bold ${style.label}`}>
                  {fc.peer_baseline.toFixed(0)}
                </span>
                <span className="text-xs text-cool-grey">months reserve</span>
              </div>
              {fc.months_reserve !== null && (
                <div className="text-center">
                  <span className="block text-xs text-cool-grey mb-1.5">This Organization</span>
                  <span className={`block font-body text-3xl font-bold ${style.label}`}>
                    {fc.months_reserve.toFixed(0)}
                  </span>
                  <span className="text-xs text-cool-grey">months reserve</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Explanation — neutral dark for readability, not tinted */}
        <p className="font-body text-[15px] leading-relaxed text-slate">
          {fc.explanation}
        </p>

        {/* Data issues (if present) */}
        {fc.data_issues && fc.data_issues.length > 0 && (
          <div className="space-y-2 pt-2">
            <p className="text-xs text-cool-grey">Data quality flags:</p>
            <div className="flex flex-wrap gap-2">
              {fc.data_issues.map(issue => (
                <span key={issue} className={`inline-block px-2.5 py-1 rounded text-xs font-medium ${style.badge}`}>
                  {issue.replace(/_/g, ' ')}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Confidence disclaimer */}
        {fc.confidence === 'LOW' && (
          <p className="text-xs text-cool-grey italic pt-2">
            Some of this organization's financial filings are still being processed, so this context is partial. We're working to bring in their latest information.
          </p>
        )}
      </div>
    </div>
  )
}
