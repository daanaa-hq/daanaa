import React from 'react'
import { Link } from 'react-router-dom'
import type { Organization } from '../data/organizations'
import { formatCurrency, NTEE1_NAMES } from '../data/organizations'
import { NTEE_SUBCATEGORIES } from '../data/categories'
import BadgeChip from './BadgeChip'
import { getTierFromOrg, getInlineVerifiedFact } from './TrustBadge'
import LampMark from './LampMark'
import type { ApiOrganization } from '../data/api'
import { getCardBadges } from '../utils/badges'
import { useCompare } from '../contexts/CompareContext'
import AddToWalletButton from './AddToWalletButton'

interface OrgCardProps {
  org: Organization
  compact?: boolean
  isSaved?: boolean
  onToggleSave?: (e: React.MouseEvent, ein: string, meta?: { name: string; city?: string; state?: string; ntee1?: string }) => void
  apiOrg?: ApiOrganization
  trustSummary?: string
  hideCompare?: boolean
}

function getNteeInfo(code: string): { major: string; sub: string | null } {
  if (!code) return { major: '', sub: null }
  const letter = code[0].toUpperCase()
  const major = NTEE1_NAMES[letter] ?? ''
  const entry = (NTEE_SUBCATEGORIES[letter] ?? []).find(s => s.code === code)
  return { major, sub: entry?.label ?? null }
}


function CompareButton({ inCompare, canAdd, onClick }: { inCompare: boolean; canAdd: boolean; onClick: (e: React.MouseEvent) => void }) {
  const color = inCompare ? '#C9A96E' : '#A89F94'
  return (
    <button
      onClick={onClick}
      title={inCompare ? 'Remove from comparison' : canAdd ? 'Add to comparison' : 'Comparison full (max 4)'}
      disabled={!inCompare && !canAdd}
      className="flex flex-col items-center gap-0.5 px-1.5 py-1 rounded-lg transition-all duration-150 hover:bg-soft-gold/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-soft-gold/70 focus-visible:ring-offset-1 disabled:opacity-30 disabled:cursor-not-allowed"
      aria-pressed={inCompare}
    >
      <svg
        width="15" height="15" viewBox="0 0 24 24"
        fill={inCompare ? '#C9A96E' : 'none'}
        stroke={color}
        strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
      >
        <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
        <rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>
      </svg>
      <span className="font-body text-[10px] leading-none" style={{ color }}>Compare</span>
    </button>
  )
}

function SaveButton({ isSaved, onClick }: { isSaved: boolean; onClick: (e: React.MouseEvent) => void }) {
  const color = isSaved ? '#C9A96E' : '#A89F94'
  return (
    <button
      onClick={onClick}
      title={isSaved ? 'Saved to Wallet' : 'Save to Wallet'}
      className="flex flex-col items-center gap-0.5 px-1.5 py-1 rounded-lg transition-all duration-150 hover:bg-soft-gold/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-soft-gold/70 focus-visible:ring-offset-1"
      aria-pressed={isSaved}
    >
      <svg
        width="15" height="15" viewBox="0 0 24 24"
        fill={isSaved ? '#C9A96E' : 'none'}
        stroke={color}
        strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
      >
        <path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z"/>
      </svg>
      <span className="font-body text-[10px] leading-none" style={{ color }}>Save</span>
    </button>
  )
}

export function OrgCardRow({ org, isSaved = false, onToggleSave, apiOrg, trustSummary, hideCompare }: OrgCardProps) {
  const { isInCompare, addItem: addCompare, removeItem: removeCompare, canAdd } = useCompare()
  const inCompare = isInCompare(org.ein)
  const lampTier  = apiOrg ? getTierFromOrg(apiOrg) : undefined
  const inlineFact = apiOrg ? getInlineVerifiedFact(apiOrg) : ''

  const handleBookmark = (e: React.MouseEvent) => {
    e.preventDefault(); e.stopPropagation()
    onToggleSave?.(e, org.ein, { name: org.name, city: org.city || undefined, state: org.state || undefined, ntee1: org.category || undefined })
  }

  const handleCompare = (e: React.MouseEvent) => {
    e.preventDefault(); e.stopPropagation()
    if (inCompare) removeCompare(org.ein)
    else addCompare({ ein: org.ein, name: org.name, ntee1: org.category, city: org.city || null, state: org.state || null })
  }

  return (
    <Link
      to={`/org/${org.id}`}
      className="flex items-center gap-4 bg-white border border-light-grey rounded-xl px-5 py-4 transition-all duration-200 hover:border-soft-gold/50 hover:shadow-card"
    >
      {/* LampMark sm */}
      {lampTier && <LampMark tier={lampTier} size="sm" className="self-start mt-0.5" />}

      {/* Name + fact + location */}
      <div className="flex-1 min-w-0">
        <h3 className="font-display text-[16px] text-deep-navy hover:text-soft-gold transition-colors line-clamp-2 mb-0.5">
          {org.name}
        </h3>
        {apiOrg?.match_sources && apiOrg.match_sources.length > 0 && (
          <p className="font-body text-[10px] text-cool-grey mb-0.5 leading-none">
            {apiOrg.match_sources.includes('keyword') && apiOrg.match_sources.includes('semantic')
              ? 'Matched by name and meaning'
              : apiOrg.match_sources.includes('semantic')
              ? 'Matched by meaning'
              : 'Matched by name'}
          </p>
        )}
        <div className="flex items-center gap-2 flex-wrap">
          {inlineFact && (
            <span className="font-body text-[11px] text-soft-gold">{inlineFact}</span>
          )}
          {inlineFact && (org.city || org.subcategory) && (
            <span className="text-cool-grey/30">·</span>
          )}
          <span className="font-body text-[12px] text-cool-grey">
            {[org.city, org.state].filter(Boolean).join(', ')}
          </span>
          {org.subcategory && (() => {
            const { major, sub } = getNteeInfo(org.subcategory)
            const label = sub ?? major
            if (!label) return null
            return (
              <>
                <span className="text-cool-grey/30">·</span>
                <span className="font-body text-[11px] text-cool-grey truncate max-w-[200px]">
                  {major && sub ? `${major} · ${sub}` : label}
                </span>
              </>
            )
          })()}
        </div>
      </div>

      {/* Badges */}
      {apiOrg && (
        <div className="hidden md:flex flex-wrap gap-1.5 shrink-0 max-w-[260px] justify-end">
          {getCardBadges(apiOrg).map(badge => (
            <BadgeChip key={badge.id} badge={badge} size="sm" variant="light" />
          ))}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-1.5 shrink-0">
        {/* Compare hidden on mobile — too small to be useful */}
        {!hideCompare && <span className="hidden md:contents"><CompareButton inCompare={inCompare} canAdd={canAdd} onClick={handleCompare} /></span>}
        {onToggleSave
          ? <SaveButton isSaved={isSaved} onClick={handleBookmark} />
          : <div onClick={e => { e.preventDefault(); e.stopPropagation() }}>
              <AddToWalletButton ein={org.ein} orgName={org.name} />
            </div>
        }
      </div>
    </Link>
  )
}

export default function OrgCard({ org, compact = false, isSaved = false, onToggleSave, apiOrg, trustSummary, hideCompare }: OrgCardProps) {
  const scored     = org.hasScore !== false && org.meritScore > 0
  const { isInCompare, addItem: addCompare, removeItem: removeCompare, canAdd } = useCompare()
  const inCompare  = isInCompare(org.ein)
  const lampTier   = apiOrg ? getTierFromOrg(apiOrg) : undefined
  const inlineFact = apiOrg ? getInlineVerifiedFact(apiOrg) : ''

  const handleBookmark = (e: React.MouseEvent) => {
    e.preventDefault(); e.stopPropagation()
    onToggleSave?.(e, org.ein, { name: org.name, city: org.city || undefined, state: org.state || undefined, ntee1: org.category || undefined })
  }

  const handleCompare = (e: React.MouseEvent) => {
    e.preventDefault(); e.stopPropagation()
    if (inCompare) removeCompare(org.ein)
    else addCompare({ ein: org.ein, name: org.name, ntee1: org.category, city: org.city || null, state: org.state || null })
  }

  return (
    <Link
      to={`/org/${org.id}`}
      className="block bg-white border border-light-grey rounded-xl p-5 transition-all duration-200 hover:border-soft-gold/50 hover:-translate-y-[3px] hover:shadow-card"
    >
      {/* Top row: lamp + name (full width, no button crowding it) */}
      <div className="flex items-start gap-3 mb-1.5">
        {lampTier && <LampMark tier={lampTier} size="md" className="mt-0.5 shrink-0" />}
        <div className="flex-1 min-w-0">
          <h3 className="font-display text-[17px] text-deep-navy leading-tight hover:text-soft-gold transition-colors line-clamp-2">
            {org.name}
          </h3>
          {inlineFact && (
            <p className="font-body text-[11px] text-soft-gold mt-0.5 leading-none">{inlineFact}</p>
          )}
          {apiOrg?.match_sources && apiOrg.match_sources.length > 0 && (
            <p className="font-body text-[10px] text-cool-grey mt-0.5 leading-none">
              {apiOrg.match_sources.includes('keyword') && apiOrg.match_sources.includes('semantic')
                ? 'Matched by name and meaning'
                : apiOrg.match_sources.includes('semantic')
                ? 'Matched by meaning'
                : 'Matched by name'}
            </p>
          )}
        </div>
      </div>

      {/* Location */}
      <div className="flex items-center gap-1.5 mb-2">
        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#A89F94" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>
        </svg>
        <span className="font-body text-[12px] text-cool-grey">
          {[org.city, org.state].filter(Boolean).join(', ') || 'IRS registered'}
        </span>
      </div>

      {/* Category — human-readable, two-level */}
      {org.subcategory && (() => {
        const { major, sub } = getNteeInfo(org.subcategory)
        const label = sub ?? major
        if (!label) return null
        return (
          <div className="mb-3">
            <span
              title={org.subcategory}
              className="inline-flex flex-col px-2.5 py-1 rounded-lg bg-soft-gold/8 cursor-default"
            >
              {major && sub && (
                <span className="font-body text-[9px] text-cool-grey leading-tight tracking-[0.05em] uppercase">
                  {major}
                </span>
              )}
              <span className="font-body text-[11px] text-deep-navy/70 font-medium leading-tight">
                {label}
              </span>
            </span>
          </div>
        )
      })()}

      {/* Mission snippet */}
      {!compact && org.mission && (
        <p className="font-body text-[12px] text-cool-grey/80 leading-[1.55] line-clamp-2 mb-2.5 -mt-1">
          {org.mission}
        </p>
      )}

      {/* Revenue (secondary) */}
      {!compact && !org.mission && scored && (
        <p className="font-body text-[12px] text-cool-grey mb-2.5">
          {org.latestTaxYear && <span className="text-soft-gold font-medium mr-1.5">FY {org.latestTaxYear}</span>}
          Revenue: {formatCurrency(org.revenue)}
        </p>
      )}
      {!compact && !org.mission && !scored && org.revenue > 0 && (
        <p className="font-body text-[12px] text-cool-grey mb-2.5">Revenue: {formatCurrency(org.revenue)}</p>
      )}

      {/* Footer: badges stacked above action buttons so Add never gets clipped */}
      <div className="mt-3 pt-2.5 border-t border-light-grey/60">
        {apiOrg && (
          <div className="flex flex-wrap gap-1.5 mb-2">
            {getCardBadges(apiOrg).map(badge => (
              <BadgeChip key={badge.id} badge={badge} size="sm" variant="light" />
            ))}
          </div>
        )}
        <div className="flex items-center justify-end gap-1">
          {!hideCompare && <CompareButton inCompare={inCompare} canAdd={canAdd} onClick={handleCompare} />}
          {onToggleSave && <SaveButton isSaved={isSaved} onClick={handleBookmark} />}
        </div>
        {/* Show AddToWalletButton only when parent doesn't provide its own toggle handler */}
        {!onToggleSave && (
          <div
            className="mt-2"
            onClick={e => { e.preventDefault(); e.stopPropagation() }}
          >
            <AddToWalletButton ein={org.ein} orgName={org.name} />
          </div>
        )}
      </div>
    </Link>
  )
}
