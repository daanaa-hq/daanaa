import { ApiOrganization } from '../data/api'
import { formatCurrency, formatNumber } from '../data/organizations'

/**
 * HowToHelp: Impact Story + Expense Allocation
 *
 * Shows donors where their money goes (program vs admin vs fundraising)
 * and the impact of giving. Stewardship P3 (evidence-based),
 * P5 (no shame framing), P8 (never handle funds).
 */
export default function HowToHelp({ org }: { org: ApiOrganization }) {
  const hasAllocation =
    org.program_expense_pct !== null ||
    org.management_expenses !== null ||
    org.fundraising_expenses !== null

  if (!hasAllocation) {
    return null
  }

  const programPct = org.program_expense_pct ?? 0
  const totalExpenses = org.total_functional_expenses ?? 0

  // Calculate admin and fundraising percentages if we have program pct
  const adminPct = totalExpenses && org.management_expenses
    ? Math.round((org.management_expenses / totalExpenses) * 100)
    : 0
  const fundraisingPct = totalExpenses && org.fundraising_expenses
    ? Math.round((org.fundraising_expenses / totalExpenses) * 100)
    : 0

  return (
    <section className="mb-16 py-12 md:py-16 border-b border-cool-grey/20">
      <h2 className="font-display italic text-deep-navy text-title-sm mb-8">How do I help?</h2>

      <div className="space-y-8">
        {/* Impact narrative */}
        <div>
          <p className="font-body text-base leading-relaxed text-deep-navy mb-6">
            Your donation directly supports {org.organization_name?.toLowerCase()}'s core mission.
            Every contribution helps expand their impact, reach more people in need, and continue their essential work.
          </p>

          {/* Mission-specific giving prompt */}
          {org.programs?.service_area && (
            <div className="p-4 bg-blue-50 border border-blue-100 rounded-lg mb-6">
              <p className="font-body text-small text-deep-navy">
                <strong>Service area:</strong> {org.programs.service_area}
                {org.programs.years_active && ` · ${org.programs.years_active} years of experience`}
              </p>
            </div>
          )}
        </div>

        {/* Expense allocation breakdown */}
        {hasAllocation && (
          <div>
            <h3 className="font-body text-small font-semibold text-deep-navy mb-4 uppercase tracking-wide">Where your money goes</h3>

            <div className="space-y-4 mb-6">
              {/* Program expenses bar */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="font-body text-base text-cool-grey">Direct mission work</span>
                  <span className="font-body text-base font-medium text-deep-navy">{Math.round(programPct)}%</span>
                </div>
                <div className="h-3 bg-cool-grey/10 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-soft-gold rounded-full transition-all duration-500"
                    style={{ width: `${Math.min(programPct, 100)}%` }}
                  ></div>
                </div>
                {org.program_expenses && (
                  <p className="font-body text-caption text-cool-grey mt-2">
                    {formatCurrency(org.program_expenses)} annually
                  </p>
                )}
              </div>

              {/* Admin expenses bar */}
              {(adminPct > 0 || org.management_expenses) && (
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-body text-base text-cool-grey">Management & operations</span>
                    <span className="font-body text-base font-medium text-deep-navy">{adminPct}%</span>
                  </div>
                  <div className="h-3 bg-cool-grey/10 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-cool-grey/30 rounded-full transition-all duration-500"
                      style={{ width: `${Math.min(adminPct, 100)}%` }}
                    ></div>
                  </div>
                  {org.management_expenses && (
                    <p className="font-body text-caption text-cool-grey mt-2">
                      {formatCurrency(org.management_expenses)} annually
                    </p>
                  )}
                </div>
              )}

              {/* Fundraising expenses bar */}
              {(fundraisingPct > 0 || org.fundraising_expenses) && (
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-body text-base text-cool-grey">Fundraising</span>
                    <span className="font-body text-base font-medium text-deep-navy">{fundraisingPct}%</span>
                  </div>
                  <div className="h-3 bg-cool-grey/10 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-cool-grey/20 rounded-full transition-all duration-500"
                      style={{ width: `${Math.min(fundraisingPct, 100)}%` }}
                    ></div>
                  </div>
                  {org.fundraising_expenses && (
                    <p className="font-body text-caption text-cool-grey mt-2">
                      {formatCurrency(org.fundraising_expenses)} annually
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* Context on allocation */}
            <p className="font-body text-small text-cool-grey leading-relaxed">
              {programPct >= 75
                ? 'This organization dedicates the vast majority of resources to direct mission work — an excellent sign of spending discipline.'
                : programPct >= 65
                ? 'This organization directs a strong portion of spending to their core mission while maintaining necessary operations and fundraising.'
                : 'This organization allocates funds across mission work, operations, and fundraising activities.'}
            </p>
          </div>
        )}
      </div>
    </section>
  )
}
