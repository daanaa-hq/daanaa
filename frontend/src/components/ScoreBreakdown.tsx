import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import type { ApiOrganization } from '../data/api'
import { getOrgBadges } from '../utils/badges'
import BadgeChip from './BadgeChip'

interface ScoreBreakdownProps {
  org: ApiOrganization
  onClose: () => void
  mode: 'drawer' | 'inline'
}

export default function ScoreBreakdown({ org, onClose, mode }: ScoreBreakdownProps) {
  const badges = getOrgBadges(org)
  const panelRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (mode !== 'drawer') return
    const handler = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) onClose()
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [mode, onClose])

  const taxYear = org.latest_tax_year
  const sourceLabel = org.data_source === 'propublica' ? 'ProPublica Nonprofit Explorer'
    : org.data_source === 'irs_soi' ? 'IRS SOI Extract'
    : 'IRS Business Master File'

  const content = (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-start justify-between p-5 border-b border-light-grey shrink-0">
        <div>
          <p className="font-body text-[11px] font-semibold tracking-[0.08em] uppercase text-cool-grey mb-1">What we know</p>
          <p className="font-body text-[13px] text-deep-navy font-medium leading-[1.4] max-w-[280px]">
            {org.organization_name}
          </p>
        </div>
        <button onClick={onClose} className="p-1.5 rounded-full hover:bg-light-grey transition-colors shrink-0 ml-3">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#6B7280" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>

      {/* Badge rows */}
      <div className="flex-1 overflow-y-auto divide-y divide-light-grey/60">
        {badges.map(badge => (
          <div key={badge.id} className="px-5 py-4">
            <div className="flex items-start gap-3">
              <BadgeChip badge={badge} size="sm" variant="light" />
              <div className="flex-1 min-w-0 pt-0.5">
                <p className="font-body text-[12px] text-cool-grey leading-[1.6]">
                  {badge.detail}
                </p>
                <p className="font-body text-[10px] text-cool-grey/45 mt-1.5 tracking-[0.01em]">
                  {badge.source}{taxYear && badge.id.includes('filing') ? ` · FY ${taxYear}` : ''}
                </p>
              </div>
            </div>
          </div>
        ))}

        {/* Honest note about what we don't yet measure */}
        <div className="px-5 py-4 bg-warm-cream/60">
          <p className="font-body text-[11px] font-semibold text-deep-navy mb-2">Not yet measured</p>
          <ul className="space-y-1.5">
            {[
              'Board independence and governance practices',
              'Independent audit records',
              'Program outcome and impact data',
            ].map(item => (
              <li key={item} className="flex items-start gap-2 font-body text-[11px] text-cool-grey">
                <span className="mt-0.5 shrink-0 text-cool-grey/40">›</span>
                {item}
              </li>
            ))}
          </ul>
          <p className="mt-3 font-body text-[10px] text-cool-grey/50 leading-[1.5]">
            These gaps reflect data we haven't collected yet — not red flags. Governance and impact data will be added as MERIT expands.
          </p>
        </div>
      </div>

      {/* Footer */}
      <div className="px-5 py-3 border-t border-light-grey shrink-0 flex items-start justify-between gap-3">
        <p className="font-body text-[10px] text-cool-grey/50 leading-[1.5]">
          Data sourced from {sourceLabel} and the IRS Business Master File.
          MERIT does not process donations or independently audit organizations.
        </p>
        <Link
          to="/methodology"
          className="shrink-0 font-body text-[10px] text-soft-gold hover:text-bright-gold transition-colors whitespace-nowrap"
        >
          How scoring works →
        </Link>
      </div>
    </div>
  )

  if (mode === 'inline') {
    return (
      <div className="bg-white border border-light-grey rounded-xl overflow-hidden">
        {content}
      </div>
    )
  }

  return (
    <div className="fixed inset-0 z-50 flex justify-end pointer-events-none">
      <div
        ref={panelRef}
        className="pointer-events-auto w-[380px] h-full bg-white border-l border-light-grey shadow-card-hover flex flex-col"
        style={{ animation: 'slideInRight 0.2s ease-out' }}
      >
        {content}
      </div>
      <style>{`
        @keyframes slideInRight {
          from { transform: translateX(100%); opacity: 0; }
          to   { transform: translateX(0);   opacity: 1; }
        }
      `}</style>
    </div>
  )
}
