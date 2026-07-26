import { Link } from 'react-router-dom'
import type { ApiOrganization } from '../data/api'
import type { TierName } from './TrustBadge'
import { TIER_COLORS, TIER_MICROCOPY, buildCriteria, getNextTierPath } from './TrustBadge'
import LampMark from './LampMark'
import MistakeRegistry from './MistakeRegistry'

const STATUS_ICON: Record<string, string> = {
  met:         '✓',
  partial:     '⚠',
  unavailable: '—',
}

const STATUS_COLOR: Record<string, string> = {
  met:         '#4ADE80',
  partial:     '#F59E0B',
  unavailable: '#9CA3AF',
}

const STATUS_LABEL: Record<string, string> = {
  met:         'Met',
  partial:     'Partial',
  unavailable: 'Not yet available',
}

interface TierBreakdownProps {
  org: ApiOrganization
  tier: TierName
  onClose?: () => void
}

export default function TierBreakdown({ org, tier, onClose }: TierBreakdownProps) {
  const criteria  = buildCriteria(org)
  const nextPath  = getNextTierPath(tier)
  const color     = TIER_COLORS[tier]
  const microcopy = TIER_MICROCOPY[tier]

  return (
    <div className="bg-white border border-light-grey rounded-2xl p-6 max-w-[560px]">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-5">
        <div className="flex items-center gap-3">
          <LampMark tier={tier} size="lg" />
          <div>
            <h3
              className="text-title-lg leading-none tracking-[0.04em]"
              style={{ fontFamily: 'Cinzel, serif', color }}
            >
              {tier}
            </h3>
            <p className="font-body text-small text-cool-grey mt-1.5 leading-[1.45] max-w-[260px]">
              {microcopy}
            </p>
          </div>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="shrink-0 p-1.5 rounded-full hover:bg-light-grey/60 transition-colors"
            aria-label="Close breakdown"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6B7280" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        )}
      </div>

      {/* Criteria list */}
      <div className="divide-y divide-light-grey/50 mb-5">
        {criteria.map(c => (
          <div key={c.id} className="flex items-start gap-3 py-2.5">
            <span
              className="shrink-0 w-4 font-body text-small font-semibold mt-px"
              style={{ color: STATUS_COLOR[c.status] }}
            >
              {STATUS_ICON[c.status]}
            </span>
            <div className="flex-1 min-w-0">
              <div className="flex items-baseline gap-2 flex-wrap">
                <span className="font-body text-small font-medium text-deep-navy">{c.label}</span>
                <span className="font-body text-label text-cool-grey">{STATUS_LABEL[c.status]}</span>
              </div>
              <p className="font-body text-caption text-cool-grey mt-0.5 leading-[1.4]">{c.description}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Next tier path */}
      {nextPath && (
        <div className="rounded-xl px-4 py-3 mb-5" style={{ background: 'rgba(201,169,110,0.08)', border: '1px solid rgba(201,169,110,0.22)' }}>
          <p className="font-body text-micro font-semibold tracking-[0.07em] text-link-gold uppercase mb-1">Path to next tier</p>
          <p className="font-body text-small text-deep-navy/80 leading-[1.5]">{nextPath}</p>
        </div>
      )}

      {(!org.has_mission || !org.has_website || tier === 'Candle' || tier === 'Spark') && (
        <div className="rounded-xl px-4 py-3.5 mb-5" style={{ background: 'rgba(201,169,110,0.08)', border: '1px solid rgba(201,169,110,0.22)' }}>
          <p className="font-body text-small text-deep-navy/85 leading-[1.55]">
            <span className="font-semibold">This profile is still lighting up.</span>{' '}
            {org.organization_name} is a 501(c)(3) the IRS recognizes. A lower tier reflects the public data we have, not the quality of its work. Adding a mission and website brightens its flame.
          </p>
          <Link
            to="/for-nonprofits"
            className="inline-flex items-center gap-1.5 mt-2.5 font-body text-caption font-semibold text-soft-gold hover:text-bright-gold transition-colors"
          >
            Is this your nonprofit? Claim it free and add your own context →
          </Link>
        </div>
      )}

      <MistakeRegistry />

      <div className="mt-4 pt-4 border-t border-light-grey/60">
        <Link
          to="/tiers"
          className="font-body text-caption text-soft-gold hover:text-bright-gold transition-colors"
        >
          Full tier reference →
        </Link>
      </div>
    </div>
  )
}
