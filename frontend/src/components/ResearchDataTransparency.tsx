import type { ApiOrganization } from '../data/api'
import { formatCurrency } from '../data/organizations'

interface ResearchDataProps {
  org: ApiOrganization
  onUpdateClick?: () => void
}

export default function ResearchDataTransparency({ org, onUpdateClick }: ResearchDataProps) {
  if (!org.latest_tax_year) return null

  const getDataFreshnessStatus = () => {
    if (!org.latest_tax_year) return { status: 'unknown', days: 0 }
    const taxYearDate = new Date(`${org.latest_tax_year}-12-31`)
    const now = new Date()
    const days = Math.floor((now.getTime() - taxYearDate.getTime()) / (1000 * 60 * 60 * 24))

    if (days < 365) return { status: 'current', days }
    if (days < 730) return { status: 'recent', days }
    return { status: 'stale', days }
  }

  const freshness = getDataFreshnessStatus()
  const isStale = freshness.status === 'stale'

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-6">
      <div className="mb-6">
        <h3 className="font-display text-[18px] font-semibold text-deep-navy mb-2">
          Research Data Behind Your Profile
        </h3>
        <p className="font-body text-[13px] text-cool-grey">
          Here's the financial data we use to understand your organization.
          {isStale && " It's outdated. You can update it below."}
        </p>
      </div>

      {/* Data Source & Freshness */}
      <div className="mb-6 p-4 rounded-lg bg-slate-50 border border-slate-100">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="font-body text-[11px] text-cool-grey uppercase tracking-wide mb-1">
              Latest Tax Year
            </p>
            <p className="font-display text-[20px] font-bold text-deep-navy">
              FY {org.latest_tax_year}
            </p>
            <p className="font-body text-[11px] text-cool-grey mt-1">
              {freshness.days > 365 ? `${Math.floor(freshness.days / 365)} years old` : `${freshness.days} days old`}
            </p>
          </div>
          <div>
            <p className="font-body text-[11px] text-cool-grey uppercase tracking-wide mb-1">
              Data Source
            </p>
            <p className="font-display text-[14px] font-semibold text-deep-navy">
              {org.data_source === 'irs_soi' ? 'IRS 990' :
               org.data_source === 'propublica' ? 'ProPublica' :
               org.data_source === 'nccs' ? 'NCCS' :
               'IRS BMF (verified)'}
            </p>
            <p className="font-body text-[11px] text-cool-grey mt-1">
              Public database
            </p>
          </div>
        </div>
      </div>

      {/* Key Metrics Used in Peer Context */}
      <div className="space-y-3 mb-6">
        <p className="font-body text-[12px] font-semibold text-deep-navy uppercase tracking-wide">
          Financial Metrics
        </p>

        <div className="grid grid-cols-2 gap-4">
          {/* Total Revenue */}
          <div className="p-3 rounded-lg bg-blue-50 border border-blue-100">
            <p className="font-body text-[11px] text-cool-grey mb-1">Total Revenue</p>
            <p className="font-display text-[16px] font-bold text-blue-900">
              {org.total_revenue ? formatCurrency(org.total_revenue) : 'N/A'}
            </p>
            <p className="font-body text-[10px] text-cool-grey mt-1">
              Used to determine your size band
            </p>
          </div>

          {/* Program Expense % */}
          <div className="p-3 rounded-lg bg-green-50 border border-green-100">
            <p className="font-body text-[11px] text-cool-grey mb-1">Program Expense %</p>
            <p className="font-display text-[16px] font-bold text-green-900">
              {org.program_expense_pct ? `${org.program_expense_pct.toFixed(0)}%` : 'N/A'}
            </p>
            <p className="font-body text-[10px] text-cool-grey mt-1">
              Shows mission efficiency
            </p>
          </div>

          {/* Months of Reserve */}
          <div className="p-3 rounded-lg bg-alert-amber/5 border border-amber-100">
            <p className="font-body text-[11px] text-cool-grey mb-1">Months of Reserve</p>
            <p className="font-display text-[16px] font-bold text-amber-900">
              {org.months_of_reserve ? `${org.months_of_reserve.toFixed(1)} mo` : 'N/A'}
            </p>
            <p className="font-body text-[10px] text-cool-grey mt-1">
              Financial cushion (typical: 3+ months)
            </p>
          </div>

          {/* Total Expenses */}
          <div className="p-3 rounded-lg bg-purple-50 border border-purple-100">
            <p className="font-body text-[11px] text-cool-grey mb-1">Total Expenses</p>
            <p className="font-display text-[16px] font-bold text-purple-900">
              {org.total_expenses ? formatCurrency(org.total_expenses) : 'N/A'}
            </p>
            <p className="font-body text-[10px] text-cool-grey mt-1">
              Operating costs
            </p>
          </div>
        </div>
      </div>

      {/* Stale Data Warning */}
      {isStale && (
        <div className="mb-6 p-4 rounded-lg bg-alert-amber/5 border border-amber-200">
          <p className="font-body text-[13px] text-amber-900 mb-2">
            <strong>Your data is from {org.latest_tax_year}.</strong> The 2025 990 may not be filed yet, but if your financials have changed, you can update them below.
          </p>
          <p className="font-body text-[12px] text-amber-800">
            Updating your information helps donors understand your current position.
          </p>
        </div>
      )}

      {/* Validation & Action */}
      <div className="pt-6 border-t border-slate-200">
        <div className="mb-4">
          <p className="font-body text-[13px] font-semibold text-deep-navy mb-2">
            Is this data correct?
          </p>
          <p className="font-body text-[12px] text-cool-grey mb-4">
            If you see errors or know your data has changed, you can update your information below.
            We'll include your updates in our next scoring run.
          </p>
        </div>

        <button
          onClick={onUpdateClick}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-soft-gold text-deep-navy font-body text-[13px] font-semibold hover:bg-bright-gold transition-colors"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
          </svg>
          Update Your Information
        </button>
      </div>

      <div className="mt-6 pt-6 border-t border-slate-200">
        <p className="font-body text-[11px] text-cool-grey italic">
          <strong>How we use this:</strong> Your financial data determines your peer group and health signal.
          Accurate data helps donors understand your context. It also helps us serve you better.
        </p>
      </div>
    </div>
  )
}
