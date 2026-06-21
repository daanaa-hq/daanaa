import React, { useMemo } from 'react'
import { useWallet } from '../contexts/WalletContext'

export default function ImpactSummary() {
  const { entries } = useWallet()

  const impact = useMemo(() => {
    if (!entries || entries.length === 0) {
      return {
        totalDonated: 0,
        uniqueOrgs: 0,
        totalHours: 0,
        averageDonation: 0,
      }
    }

    // Collect all donations from all entries
    const allDonations: any[] = []
    entries.forEach((entry: any) => {
      if (entry.donations && Array.isArray(entry.donations)) {
        allDonations.push(...entry.donations)
      }
    })

    const totalDonated = allDonations.reduce((sum: number, d: any) => sum + (d.amount || 0), 0)
    const uniqueOrgs = entries.length
    const totalHours = 0  // TODO: track volunteer hours when available
    const averageDonation = allDonations.length > 0 ? totalDonated / allDonations.length : 0

    return {
      totalDonated,
      uniqueOrgs,
      totalHours,
      averageDonation,
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
          Impact
        </p>
        <p className="font-display text-xl text-blue-600">
          {impact.uniqueOrgs > 0 || impact.totalHours > 0 ? '⚡ Active' : '○ Ready'}
        </p>
        <p className="text-xs text-cool-grey mt-1">
          {impact.uniqueOrgs > 0 && impact.totalHours > 0
            ? 'Giver + Volunteer'
            : impact.uniqueOrgs > 0
              ? 'Financial supporter'
              : impact.totalHours > 0
                ? 'Hands-on helper'
                : 'Your giving journey'}
        </p>
      </div>
    </div>
  )
}
