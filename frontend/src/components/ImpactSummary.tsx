import React, { useMemo } from 'react'
import { useWallet } from '../contexts/WalletContext'

export default function ImpactSummary() {
  const { entries } = useWallet()

  // Placeholder BAL (Benefit Amount in Labor) for volunteer hour valuation
  // In production, this should be fetched for the current year from Independent Sector or similar
  const VOLUNTEER_HOURLY_VALUE = 31.80  // 2026 placeholder

  const impact = useMemo(() => {
    if (!entries || entries.length === 0) {
      return {
        totalDonated: 0,
        uniqueOrgs: 0,
        totalHours: 0,
        averageDonation: 0,
        lifetimeImpact: 0,
        volunteeredCount: 0,
      }
    }

    // Collect all donations and volunteer hours from all entries
    const allDonations: any[] = []
    let allVolunteerHours: any[] = []

    entries.forEach((entry: any) => {
      if (entry.donations && Array.isArray(entry.donations)) {
        allDonations.push(...entry.donations)
      }
      if (entry.volunteerHours && Array.isArray(entry.volunteerHours)) {
        allVolunteerHours.push(...entry.volunteerHours)
      }
    })

    const totalDonated = allDonations.reduce((sum: number, d: any) => sum + (d.amount || 0), 0)
    const totalHours = allVolunteerHours.reduce((sum: number, v: any) => sum + (v.hours || 0), 0)
    const volunteeredCount = entries.filter(e => e.volunteerHours && e.volunteerHours.length > 0).length
    const uniqueOrgs = entries.length
    const averageDonation = allDonations.length > 0 ? totalDonated / allDonations.length : 0

    // Lifetime impact = total donated + (volunteer hours × hourly value)
    const lifetimeImpact = totalDonated + (totalHours * VOLUNTEER_HOURLY_VALUE)

    return {
      totalDonated,
      uniqueOrgs,
      totalHours,
      averageDonation,
      lifetimeImpact,
      volunteeredCount,
    }
  }, [entries])

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div className="bg-gradient-to-br from-soft-gold/20 to-bright-gold/10 rounded-lg p-4 border border-soft-gold/30">
        <p className="text-xs text-cool-grey uppercase tracking-wide font-semibold mb-1">
          Total Donated
        </p>
        <p className="font-display text-2xl text-soft-gold">
          ${impact.totalDonated.toLocaleString('en-US', { maximumFractionDigits: 0 })}
        </p>
        <p className="text-xs text-cool-grey mt-1">
          {impact.averageDonation > 0 ? `Avg: $${impact.averageDonation.toFixed(0)}` : 'Start giving'}
        </p>
      </div>

      <div className="bg-gradient-to-br from-deep-navy/10 to-cool-grey/10 rounded-lg p-4 border border-light-grey">
        <p className="text-xs text-cool-grey uppercase tracking-wide font-semibold mb-1">
          Organizations
        </p>
        <p className="font-display text-2xl text-deep-navy">
          {impact.uniqueOrgs}
        </p>
        <p className="text-xs text-cool-grey mt-1">
          {impact.uniqueOrgs === 1 ? 'organization' : 'organizations'}
        </p>
      </div>

      <div className="bg-gradient-to-br from-green-100/40 to-emerald-100/20 rounded-lg p-4 border border-green-200/40">
        <p className="text-xs text-cool-grey uppercase tracking-wide font-semibold mb-1">
          Volunteer Hours
        </p>
        <p className="font-display text-2xl text-green-600">
          {impact.totalHours.toFixed(1)}
        </p>
        <p className="text-xs text-cool-grey mt-1">
          {impact.totalHours === 0 ? 'Start volunteering' : 'hours'}
        </p>
      </div>

      <div className="bg-gradient-to-br from-blue-100/30 to-cyan-100/20 rounded-lg p-4 border border-blue-200/30">
        <p className="text-xs text-cool-grey uppercase tracking-wide font-semibold mb-1">
          Lifetime Value
        </p>
        <p className="font-display text-xl text-blue-600">
          ${impact.lifetimeImpact.toLocaleString('en-US', { maximumFractionDigits: 0 })}
        </p>
        <p className="text-xs text-cool-grey mt-1">
          {impact.totalDonated > 0 && impact.totalHours > 0
            ? `Funding + ${impact.totalHours.toFixed(1)}h volunteer`
            : impact.totalDonated > 0
              ? 'Financial support'
              : impact.totalHours > 0
                ? `${impact.totalHours.toFixed(1)} volunteer hours`
                : 'Ready to give'}
        </p>
      </div>
    </div>
  )
}
