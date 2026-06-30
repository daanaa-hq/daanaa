import React, { useMemo } from 'react'
import { useWallet } from '../contexts/WalletContext'

export default function ImpactSummary() {
  const { entries } = useWallet()

  // Placeholder BAL (Benefit Amount in Labor) for volunteer hour valuation
  // In production, this should be fetched for the current year from Independent Sector or similar
  const VOLUNTEER_HOURLY_VALUE = 31.80  // 2026 placeholder

  const impact = useMemo(() => {
    const currentYear = new Date().getFullYear()

    const allDonations: any[] = []
    const allVolunteerHours: any[] = []
    const supportedEins = new Set<string>()

    ;(entries || []).forEach((entry: any) => {
      const donations = Array.isArray(entry.donations) ? entry.donations : []
      const hours = Array.isArray(entry.volunteerHours) ? entry.volunteerHours : []
      if (donations.length > 0) allDonations.push(...donations)
      if (hours.length > 0) allVolunteerHours.push(...hours)
      // "Supported" = took an action (gave money or time), not just bookmarked
      if (donations.length > 0 || hours.length > 0) supportedEins.add(entry.ein)
    })

    const yearOf = (d: any) => {
      const dt = d?.date ? new Date(d.date) : null
      return dt && !isNaN(dt.getTime()) ? dt.getFullYear() : null
    }

    const ytdFunded = allDonations
      .filter(d => yearOf(d) === currentYear)
      .reduce((sum: number, d: any) => sum + (d.amount || 0), 0)
    const lifetimeFunds = allDonations.reduce((sum: number, d: any) => sum + (d.amount || 0), 0)
    const totalHours = allVolunteerHours.reduce((sum: number, v: any) => sum + (v.hours || 0), 0)
    const nonprofitsSupported = supportedEins.size
    // Total impact = lifetime funds + (volunteer hours × hourly value)
    const totalImpact = lifetimeFunds + (totalHours * VOLUNTEER_HOURLY_VALUE)

    return { ytdFunded, lifetimeFunds, totalHours, nonprofitsSupported, totalImpact, currentYear }
  }, [entries])

  const usd = (n: number) =>
    `$${n.toLocaleString('en-US', { maximumFractionDigits: 0 })}`

  return (
    <div className="space-y-3">
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
      <div className="bg-gradient-to-br from-soft-gold/20 to-bright-gold/10 rounded-lg p-4 border border-soft-gold/30">
        <p className="text-xs text-cool-grey uppercase tracking-wide font-semibold mb-1">
          {impact.currentYear} Funded
        </p>
        <p className="font-display text-2xl text-soft-gold">{usd(impact.ytdFunded)}</p>
        <p className="text-xs text-cool-grey mt-1">
          {impact.ytdFunded > 0 ? 'this year' : 'Start giving'}
        </p>
      </div>

      <div className="bg-gradient-to-br from-amber-100/40 to-soft-gold/10 rounded-lg p-4 border border-soft-gold/25">
        <p className="text-xs text-cool-grey uppercase tracking-wide font-semibold mb-1">
          Lifetime Funds
        </p>
        <p className="font-display text-2xl text-deep-navy">{usd(impact.lifetimeFunds)}</p>
        <p className="text-xs text-cool-grey mt-1">
          {impact.lifetimeFunds > 0 ? 'all-time giving' : 'Ready to give'}
        </p>
      </div>

      <div className="bg-gradient-to-br from-deep-navy/10 to-cool-grey/10 rounded-lg p-4 border border-light-grey">
        <p className="text-xs text-cool-grey uppercase tracking-wide font-semibold mb-1">
          Nonprofits Supported
        </p>
        <p className="font-display text-2xl text-deep-navy">{impact.nonprofitsSupported}</p>
        <p className="text-xs text-cool-grey mt-1">
          {impact.nonprofitsSupported === 1 ? 'organization' : 'organizations'}
        </p>
      </div>

      <div className="bg-gradient-to-br from-green-100/40 to-emerald-100/20 rounded-lg p-4 border border-green-200/40">
        <p className="text-xs text-cool-grey uppercase tracking-wide font-semibold mb-1">
          Hours Volunteered
        </p>
        <p className="font-display text-2xl text-green-600">{impact.totalHours.toFixed(1)}</p>
        <p className="text-xs text-cool-grey mt-1">
          {impact.totalHours === 0 ? 'Start volunteering' : 'hours'}
        </p>
      </div>

      <div className="bg-gradient-to-br from-blue-100/30 to-cyan-100/20 rounded-lg p-4 border border-blue-200/30">
        <p className="text-xs text-cool-grey uppercase tracking-wide font-semibold mb-1">
          $ Impact
        </p>
        <p className="font-display text-2xl text-blue-600">{usd(impact.totalImpact)}</p>
        <p className="text-xs text-cool-grey mt-1">
          {impact.lifetimeFunds > 0 && impact.totalHours > 0
            ? `Funds + ${impact.totalHours.toFixed(1)}h time`
            : impact.lifetimeFunds > 0
              ? 'Financial support'
              : impact.totalHours > 0
                ? `${impact.totalHours.toFixed(1)}h volunteer value`
                : 'Funds + time'}
        </p>
      </div>
    </div>
    <p className="font-body text-[11px] text-cool-grey leading-[1.5]">
      These figures are for your personal reference only. Dollar values for volunteer time use the Independent Sector national estimate and are not verified by Daanaa. This is not tax advice, not a tax receipt, and should not be used to support any deduction. Consult a tax advisor for guidance on charitable deductions.
    </p>
    </div>
  )
}
