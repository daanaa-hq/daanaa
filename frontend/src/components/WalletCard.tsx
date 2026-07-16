import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import type { WalletEntry, GivingIntent } from '../types/wallet'
import type { ApiOrganization } from '../data/api'

interface WalletCardProps {
  entry: WalletEntry
  orgData: ApiOrganization | null
  onRemove?: (ein: string) => void
  onEdit?: (ein: string) => void
}

const healthMap: Record<string, { label: string; classes: string; title: string }> = {
  HEALTHY: { label: 'Financially healthy', classes: 'bg-emerald-50 text-emerald-700 border-emerald-200', title: 'More reserves than most similar organizations. From public IRS data.' },
  STABLE:  { label: 'Financially stable',  classes: 'bg-blue-50 text-blue-700 border-blue-200',         title: 'Typical reserve level for this type of organization. From public IRS data.' },
  CAUTION: { label: 'Needs support',       classes: 'bg-amber-50 text-amber-700 border-amber-200',      title: 'Fewer reserves than most similar organizations. An invitation to give, not a judgment of the work.' },
}

function getIntentDisplay(intent: GivingIntent | undefined): string | null {
  if (!intent) return null
  const { type, amount, hoursPerMonth, frequency } = intent
  switch (type) {
    case 'giving': {
      if (!amount) return 'Planning to give'
      const freq = frequency === 'month' ? '/mo' : frequency === 'one-time' ? ' one-time' : '/yr'
      return `Giving · $${amount.toLocaleString()}${freq}`
    }
    case 'volunteer':
      return hoursPerMonth ? `Volunteering · ${hoursPerMonth} hrs/mo` : 'Planning to volunteer'
    default:
      return null
  }
}

function WalletCardComponent({ entry, orgData, onRemove, onEdit }: WalletCardProps) {
  const [confirmRemove, setConfirmRemove] = useState(false)

  if (!orgData) {
    return (
      <div className="bg-white rounded-2xl border border-light-grey p-6 animate-pulse" aria-busy="true">
        <div className="h-4 bg-soft-cream rounded w-3/4 mb-3" />
        <div className="h-3 bg-soft-cream rounded w-full mb-2" />
        <div className="h-3 bg-soft-cream rounded w-2/3" />
      </div>
    )
  }

  const orgName = orgData.organization_name ?? ''
  const location = [orgData.CITY, orgData.STATE].filter(Boolean).join(', ')
  const cause = orgData.cause_tags ?? []
  const mission = orgData.mission ?? ''
  const healthSignal = orgData.v5_context?.score.health_signal ?? 'STABLE'
  const meritScore = orgData.v5_context?.score.percentile ?? 0
  const isHiddenGem = orgData.is_hidden_gem ?? false
  const website = (orgData.website_status === 'ok' && orgData.website) ? orgData.website : undefined

  const displayedCauses = cause.slice(0, 3)
  const hiddenCauseCount = Math.max(0, cause.length - 3)
  const health = healthMap[healthSignal] ?? healthMap.STABLE
  const intentText = getIntentDisplay(entry.givingIntent)

  function handleRemoveClick() {
    if (confirmRemove) {
      onRemove?.(entry.ein)
    } else {
      setConfirmRemove(true)
    }
  }

  return (
    <div className="bg-white rounded-2xl border border-light-grey p-6 hover:border-soft-gold/40 transition-colors">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <Link
          to={`/org/${entry.ein}`}
          className="font-body text-[15px] font-semibold text-deep-navy hover:text-soft-gold transition-colors leading-snug flex-1"
        >
          {orgName}
        </Link>
        {onRemove && (
          <div className="flex items-center gap-1 shrink-0">
            {confirmRemove ? (
              <>
                <button
                  onClick={handleRemoveClick}
                  className="px-2 py-1 rounded-lg text-[12px] font-semibold bg-red-50 text-red-700 border border-red-200 hover:bg-red-100 transition-colors"
                >
                  Remove
                </button>
                <button
                  onClick={() => setConfirmRemove(false)}
                  className="px-2 py-1 rounded-lg text-[12px] font-semibold bg-light-grey/40 text-cool-grey hover:bg-light-grey transition-colors"
                >
                  Cancel
                </button>
              </>
            ) : (
              <button
                onClick={handleRemoveClick}
                aria-label={`Remove ${orgName} from wallet`}
                className="p-1.5 rounded-lg text-cool-grey hover:text-deep-navy hover:bg-light-grey/40 transition-colors"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        )}
      </div>

      {/* Location + causes */}
      {(location || displayedCauses.length > 0) && (
        <p className="font-body text-[12px] text-cool-grey mb-3 leading-relaxed">
          {location}
          {location && displayedCauses.length > 0 && ' · '}
          {displayedCauses.join(', ')}
          {hiddenCauseCount > 0 && <span> +{hiddenCauseCount} more</span>}
        </p>
      )}

      {/* Mission */}
      {mission && (
        <p className="font-body text-[13px] text-cool-grey mb-3 line-clamp-2 italic">
          &ldquo;{mission.replace(/^[""\s]+|[""\s]+$/g, '')}&rdquo;
        </p>
      )}

      {/* Health badge + peer rank */}
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <span title={health.title} className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold border font-body ${health.classes}`}>
          {health.label}
        </span>
        {isHiddenGem && (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold border bg-violet-50 text-violet-700 border-violet-200 font-body">
            Hidden gem
          </span>
        )}
        {meritScore >= 50 && (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold border bg-deep-navy/5 text-deep-navy border-deep-navy/10 font-body">
            Top {Math.max(1, 100 - meritScore)}% of peers
          </span>
        )}
      </div>

      {/* Giving intent */}
      {intentText && (
        <div className="border-t border-light-grey pt-3 mb-4">
          <p className={`font-body text-[12px] font-medium ${intentText === 'No longer interested' ? 'text-cool-grey line-through' : 'text-deep-navy'}`}>
            {intentText}
          </p>
          {entry.givingIntent?.notes && intentText !== 'No longer interested' && (
            <p className="font-body text-[11px] text-cool-grey mt-1 italic">"{entry.givingIntent.notes}"</p>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2 items-center">
        {website && (
          <a
            href={website}
            target="_blank"
            rel="noopener noreferrer"
            aria-label={`Visit ${orgName}'s website`}
            title="Link from our public records. Websites can change. Search by name if this does not work."
            className="flex-1 px-3 py-2 rounded-xl bg-deep-navy text-warm-cream font-body text-[13px] font-semibold hover:bg-deep-navy/80 transition-colors text-center"
          >
            Visit website
          </a>
        )}
        {onEdit && (
          <button
            onClick={() => onEdit(entry.ein)}
            aria-label={`Edit giving intent for ${orgName}`}
            className="flex-1 px-3 py-2 rounded-xl bg-soft-gold text-deep-navy font-body text-[13px] font-semibold hover:bg-bright-gold transition-colors"
          >
            {intentText && intentText !== 'No longer interested' ? 'Edit intent' : intentText === 'No longer interested' ? 'Update intent' : 'Set intent'}
          </button>
        )}
        {website ? (
          <Link
            to={`/org/${entry.ein}`}
            aria-label={`View ${orgName} detail page`}
            className="shrink-0 p-2 rounded-lg text-cool-grey hover:text-deep-navy hover:bg-light-grey/40 transition-colors"
            title="View detail page"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M7 17 17 7M17 7H8M17 7v9"/>
            </svg>
          </Link>
        ) : (
          <Link
            to={`/org/${entry.ein}`}
            aria-label={`View ${orgName} detail page`}
            className="flex-1 px-3 py-2 rounded-xl border border-light-grey text-cool-grey font-body text-[13px] font-medium hover:border-soft-gold/40 hover:text-deep-navy transition-colors text-center"
          >
            View profile
          </Link>
        )}
      </div>
      {website && (
        <p className="font-body text-[10px] text-cool-grey/75 mt-2 leading-relaxed">
          Link from our records. Websites can change. If it is broken, search for them by name.
        </p>
      )}
      {entry.givingIntent?.type === 'giving' && (entry.givingIntent as GivingIntent & { status?: string }).status !== 'withdrawn' && !website && (
        <div className="mt-3 p-3 rounded-lg bg-soft-gold/[0.06] border border-soft-gold/20">
          <p className="font-body text-[11px] font-medium text-deep-navy mb-1">Give by EIN</p>
          <p className="font-body text-[13px] font-semibold text-deep-navy">{entry.ein}</p>
          <p className="font-body text-[11px] text-cool-grey mt-1">Use this for a donor-advised fund gift or when writing a check. The full mailing address is on their profile page.</p>
        </div>
      )}
    </div>
  )
}

export const WalletCard = React.memo(WalletCardComponent)
export default WalletCard
