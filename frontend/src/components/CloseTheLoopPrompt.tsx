import React, { useState } from 'react'
import DonationLogger from './DonationLogger'
import type { WalletEntry } from '../types/wallet'
import type { ApiOrganization } from '../data/api'

interface CloseTheLoopPromptProps {
  walletEntries: WalletEntry[]
  orgDataMap: Map<string, ApiOrganization>
  onDismiss: () => void
}

export default function CloseTheLoopPrompt({
  walletEntries,
  orgDataMap,
  onDismiss,
}: CloseTheLoopPromptProps) {
  const [showForm, setShowForm] = useState(false)
  const [selectedEin, setSelectedEin] = useState<string | null>(null)

  const fundingEntries = walletEntries.filter(
    e => e.inFunding === true || (e.inFunding === undefined && !e.inVolunteering)
  )

  if (fundingEntries.length === 0) return null

  if (selectedEin) {
    const org = orgDataMap.get(selectedEin)
    return (
      <div className="bg-white border border-soft-gold/30 rounded-2xl p-6 mb-8">
        <div className="flex items-start justify-between mb-4">
          <h2 className="font-display text-[18px] text-deep-navy">Log your recent donation</h2>
          <button
            onClick={() => {
              setSelectedEin(null)
              setShowForm(false)
            }}
            className="text-cool-grey hover:text-deep-navy transition-colors"
            aria-label="Close form"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
        <DonationLogger ein={selectedEin} orgName={org?.organization_name ?? selectedEin} />
      </div>
    )
  }

  if (!showForm) {
    return (
      <div className="bg-soft-gold/10 border border-soft-gold/30 rounded-2xl p-5 mb-8">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="font-body text-[14px] font-semibold text-deep-navy">Did you donate recently?</p>
            <p className="font-body text-[13px] text-cool-grey mt-1">Log your gift to help track your impact.</p>
          </div>
          <div className="flex items-center gap-2 ml-4">
            <button
              onClick={() => setShowForm(true)}
              className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-soft-gold text-deep-navy font-body text-[13px] font-semibold hover:bg-bright-gold transition-colors whitespace-nowrap"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 5v14M5 12h14"/>
              </svg>
              Log donation
            </button>
            <button
              onClick={onDismiss}
              className="text-cool-grey hover:text-cool-grey/60 transition-colors p-2"
              aria-label="Dismiss prompt"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white border border-light-grey rounded-2xl p-6 mb-8">
      <div className="flex items-start justify-between mb-5">
        <h2 className="font-display text-[18px] text-deep-navy">Log your recent donation</h2>
        <button
          onClick={() => setShowForm(false)}
          className="text-cool-grey hover:text-deep-navy transition-colors"
          aria-label="Close form"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>

      <label className="font-body text-[12px] font-semibold text-cool-grey uppercase tracking-wide block mb-2">
        Which organization did you give to?
      </label>
      <select
        value={selectedEin || ''}
        onChange={e => setSelectedEin(e.target.value || null)}
        className="w-full px-4 py-2.5 border border-light-grey rounded-xl font-body text-[13px] text-deep-navy focus:outline-none focus:ring-2 focus:ring-soft-gold/40 bg-white mb-6"
      >
        <option value="">Select an organization...</option>
        {fundingEntries.map(entry => {
          const org = orgDataMap.get(entry.ein)
          return (
            <option key={entry.ein} value={entry.ein}>
              {org?.organization_name ?? entry.ein}
            </option>
          )
        })}
      </select>

      {selectedEin && (
        <div>
          <p className="font-body text-[12px] text-cool-grey mb-4">
            Enter the details of your donation below. Your wallet is stored on this device and can be synced if you sign in.
          </p>
        </div>
      )}
    </div>
  )
}
