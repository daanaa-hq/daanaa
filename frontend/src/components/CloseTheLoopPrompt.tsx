import React, { useState } from 'react'
import DonationLogger from './DonationLogger'
import type { WalletEntry } from '../types/wallet'
import type { ApiOrganization } from '../data/api'
import { CardPattern } from './ui/CardPattern'

interface CloseTheLoopPromptProps {
  walletEntries: WalletEntry[]
  orgDataMap: Map<string, ApiOrganization>
}

export default function CloseTheLoopPrompt({
  walletEntries,
  orgDataMap,
}: CloseTheLoopPromptProps) {
  const [selectedEin, setSelectedEin] = useState<string | null>(null)

  const fundingEntries = walletEntries.filter(
    e => e.inFunding === true || (e.inFunding === undefined && !e.inVolunteering)
  )

  if (fundingEntries.length === 0) return null

  const selectedOrg = selectedEin ? orgDataMap.get(selectedEin) : null

  return (
    <CardPattern variant="elevated" className="mb-8">
      {!selectedEin ? (
        // Prompt state: ask user if they gave recently
        <div>
          <p className="font-body text-body font-semibold text-deep-navy mb-1">Did you give recently?</p>
          <p className="font-body text-small text-cool-grey mb-4">
            Log your donation so you can track your impact.
          </p>

          <label className="font-body text-caption font-semibold text-cool-grey uppercase tracking-wide block mb-2">
            Organization
          </label>
          <select
            value={selectedEin || ''}
            onChange={e => setSelectedEin(e.target.value || null)}
            className="w-full px-4 py-2.5 border border-light-grey rounded-xl font-body text-small text-deep-navy focus:outline-none focus:ring-2 focus:ring-soft-gold/40 bg-white"
          >
            <option value="">Select where you gave...</option>
            {fundingEntries.map(entry => {
              const org = orgDataMap.get(entry.ein)
              return (
                <option key={entry.ein} value={entry.ein}>
                  {org?.organization_name ?? entry.ein}
                </option>
              )
            })}
          </select>
        </div>
      ) : (
        // Logging state: show the form
        <div>
          <div className="flex items-start justify-between mb-5">
            <div>
              <p className="font-body text-caption text-cool-grey uppercase tracking-wide font-semibold mb-1">Logging to</p>
              <p className="font-body text-body font-semibold text-deep-navy">{selectedOrg?.organization_name ?? selectedEin}</p>
            </div>
            <button
              onClick={() => setSelectedEin(null)}
              className="text-cool-grey hover:text-deep-navy transition-colors p-1.5"
              aria-label="Change organization"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>

          <div className="border-t border-light-grey pt-6">
            <DonationLogger
              ein={selectedEin}
              orgName={selectedOrg?.organization_name ?? selectedEin}
              irsSnapshot={selectedOrg ? {
                irsEligibilityStatus: (selectedOrg.tax_deductible === false ? ('unknown' as const) : ('verified' as const)),
                irsEligibilityCheckedAt: selectedOrg.tax_deductible_checked_at,
                irsEligibilitySources: ['IRS Business Master File', 'IRS Auto-Revocation List'],
              } : undefined}
            />
          </div>
        </div>
      )}
    </CardPattern>
  )
}
