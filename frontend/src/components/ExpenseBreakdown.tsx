/**
 * ExpenseBreakdown Component
 * 
 * Shows how an organization spends money across three categories:
 * 1. Program Services (what donors care about most)
 * 2. Management & General (necessary overhead)
 * 3. Fundraising (cost to find donors)
 * 
 * Visibility Enhancement: CauseIQ's core feature.
 * Addresses donor question: "Does my $ actually fund the mission?"
 * 
 * Data source: IRS Form 990 Parts I & IX
 * Stewardship: P3 (evidence-based) + P5 (no shame language)
 */

import type { ApiOrganization } from '../data/api'

interface ExpenseBreakdownProps {
  org: ApiOrganization
}

export default function ExpenseBreakdown({ org }: ExpenseBreakdownProps) {
  // Calculate expenses
  const programExpenses = org.program_expenses || 0
  const managementExpenses = org.management_expenses || 0
  const fundraisingExpenses = org.fundraising_expenses || 0

  const partsSum = programExpenses + managementExpenses + fundraisingExpenses

  // If no expense data, don't render
  if (partsSum === 0) {
    return null
  }

  // Data-integrity guard (added 2026-08-16 after a partner org flagged this
  // breakdown as wrong). registry_enriched.program_expenses/management_expenses/
  // fundraising_expenses trace back to a legacy irs_soi ingestion pass and, for
  // ~94% of orgs with all three fields populated, do NOT reconcile with the
  // verified-correct total_expenses field -- commonly summing to ~2x the real
  // total (e.g. management_expenses holding what looks like the true program
  // figure). Rather than compute percentages against a self-derived total that
  // may itself be wrong, cross-check against the authoritative total_expenses
  // and refuse to render a breakdown we can't verify. See DECISIONS.md
  // 2026-08-16 for the full investigation; root-cause data correction is a
  // separate, larger follow-up (this guard just stops showing wrong numbers
  // in the meantime).
  const verifiedTotal = org.total_expenses
  if (!verifiedTotal || verifiedTotal <= 0) {
    return null
  }
  const reconciles = Math.abs(partsSum - verifiedTotal) <= 0.2 * verifiedTotal
  if (!reconciles) {
    return null
  }

  const totalExpenses = partsSum

  // Calculate percentages
  const programPct = Math.round((programExpenses / totalExpenses) * 100)
  const managementPct = Math.round((managementExpenses / totalExpenses) * 100)
  const fundraisingPct = Math.round((fundraisingExpenses / totalExpenses) * 100)

  // Format currency
  const formatAmount = (amount: number) => {
    if (amount >= 1_000_000) return `$${(amount / 1_000_000).toFixed(1)}M`
    if (amount >= 1_000) return `$${(amount / 1_000).toFixed(0)}K`
    return `$${amount}`
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h3 className="font-display italic text-deep-navy text-title-sm mb-2">How money is spent</h3>
        <p className="text-body text-cool-grey">
          Breakdown of total expenses from their latest 990 filing.
        </p>
      </div>

      {/* Visual Bar Chart */}
      <div className="flex h-12 rounded-lg overflow-hidden border border-cool-grey/20 shadow-sm">
        {/* Program Services — Green/mission color */}
        {programPct > 0 && (
          <div
            style={{ width: `${programPct}%`, backgroundColor: '#7CB342' }}
            className="flex items-center justify-center"
            title={`Program: ${programPct}%`}
          >
            {programPct > 10 && (
              <span className="text-white text-xs font-semibold">{programPct}%</span>
            )}
          </div>
        )}

        {/* Management — Neutral gray */}
        {managementPct > 0 && (
          <div
            style={{ width: `${managementPct}%`, backgroundColor: '#9CA3AF' }}
            className="flex items-center justify-center"
            title={`Management: ${managementPct}%`}
          >
            {managementPct > 10 && (
              <span className="text-white text-xs font-semibold">{managementPct}%</span>
            )}
          </div>
        )}

        {/* Fundraising — Orange/warm */}
        {fundraisingPct > 0 && (
          <div
            style={{ width: `${fundraisingPct}%`, backgroundColor: '#FB923C' }}
            className="flex items-center justify-center"
            title={`Fundraising: ${fundraisingPct}%`}
          >
            {fundraisingPct > 10 && (
              <span className="text-white text-xs font-semibold">{fundraisingPct}%</span>
            )}
          </div>
        )}
      </div>

      {/* Legend with Details */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Program Services */}
        <div className="space-y-2 p-4 rounded-lg bg-white border border-cool-grey/10">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#7CB342' }} />
            <h4 className="font-body font-semibold text-deep-navy text-small">Program Services</h4>
          </div>
          <div>
            <p className="font-display text-headline text-deep-navy font-semibold">{programPct}%</p>
            <p className="font-body text-label text-cool-grey">{formatAmount(programExpenses)}</p>
          </div>
          <p className="font-body text-label text-cool-grey/70 text-xs">
            Directly funds the mission and programs.
          </p>
        </div>

        {/* Management & General */}
        <div className="space-y-2 p-4 rounded-lg bg-white border border-cool-grey/10">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#9CA3AF' }} />
            <h4 className="font-body font-semibold text-deep-navy text-small">Management & General</h4>
          </div>
          <div>
            <p className="font-display text-headline text-deep-navy font-semibold">{managementPct}%</p>
            <p className="font-body text-label text-cool-grey">{formatAmount(managementExpenses)}</p>
          </div>
          <p className="font-body text-label text-cool-grey/70 text-xs">
            Administration, salaries, office operations.
          </p>
        </div>

        {/* Fundraising */}
        <div className="space-y-2 p-4 rounded-lg bg-white border border-cool-grey/10">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#FB923C' }} />
            <h4 className="font-body font-semibold text-deep-navy text-small">Fundraising</h4>
          </div>
          <div>
            <p className="font-display text-headline text-deep-navy font-semibold">{fundraisingPct}%</p>
            <p className="font-body text-label text-cool-grey">{formatAmount(fundraisingExpenses)}</p>
          </div>
          <p className="font-body text-label text-cool-grey/70 text-xs">
            Finding and cultivating donors.
          </p>
        </div>
      </div>

      {/* Interpretation Guide — Stewardship P5 (no shame language) */}
      <div className="bg-warm-cream/40 border border-warm-cream/60 rounded-lg p-4">
        <p className="font-body text-small text-cool-grey">
          <strong>What's healthy?</strong> {' '}
          {programPct >= 65
            ? `This org spends ${programPct}% on programs—above the typical 60% benchmark. Strong focus on mission.`
            : programPct >= 50
            ? `This org spends ${programPct}% on programs—within the typical 50–70% range. Balanced approach.`
            : `This org spends ${programPct}% on programs—below typical benchmarks, but overhead varies by sector. Check their website for context.`}
        </p>
      </div>

      {/* Data Source & Transparency */}
      <p className="text-xs text-cool-grey/70">
        Data from IRS Form 990 filing ({org.latest_tax_year}). 
        {org.latest_tax_year && new Date().getFullYear() - org.latest_tax_year > 1 && (
          <> This is {new Date().getFullYear() - org.latest_tax_year} year(s) old; check their website for recent updates.</>
        )}
      </p>
    </div>
  )
}
