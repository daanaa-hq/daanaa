import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import type { WalletOrg } from '../types/wallet'

interface WalletCardProps {
  org: WalletOrg
  onRemove?: (ein: string) => void
  onEdit?: (ein: string) => void
}

const healthMap: Record<string, { label: string; classes: string }> = {
  HEALTHY: { label: 'Financially healthy',        classes: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
  STABLE:  { label: 'Financially stable',         classes: 'bg-blue-50 text-blue-700 border-blue-200' },
  CAUTION: { label: 'Needs support',    classes: 'bg-amber-50 text-amber-700 border-amber-200' },
}

function getIntentDisplay(org: WalletOrg): string | null {
  const intent = org.givingIntent
  if (!intent) return null
  if (intent.status === 'withdrawn') return 'No longer interested'
  const { type, amount, hours, frequency } = intent
  switch (type) {
    case 'giving': {
      if (!amount) return 'Planning to give'
      const freq = frequency === 'month' ? '/mo' : frequency === 'one-time' ? ' one-time' : '/yr'
      return `Giving · $${amount.toLocaleString()}${freq}`
    }
    case 'volunteer':
      return hours ? `Volunteering · ${hours} hrs/wk` : 'Planning to volunteer'
    case 'board':
      return 'Interested in the board'
    default:
      return null
  }
}

function WalletCardComponent({ org, onRemove, onEdit }: WalletCardProps) {
  const [confirmRemove, setConfirmRemove] = useState(false)
  const displayedCauses = org.cause.slice(0, 3)
  const hiddenCauseCount = Math.max(0, org.cause.length - 3)
  const health = healthMap[org.merit_health_signal_v5] ?? healthMap.STABLE
  const intentText = getIntentDisplay(org)

  function handleRemoveClick() {
    if (confirmRemove) {
      onRemove?.(org.ein)
    } else {
      setConfirmRemove(true)
    }
  }

  return (
    <div className="bg-white rounded-2xl border border-light-grey p-6 hover:border-soft-gold/40 transition-colors">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <Link
          to={`/org/${org.ein}`}
          className="font-body text-[15px] font-semibold text-deep-navy hover:text-soft-gold transition-colors leading-snug flex-1"
        >
          {org.name}
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
                aria-label={`Remove ${org.name} from wallet`}
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
      {(org.location || displayedCauses.length > 0) && (
        <p className="font-body text-[12px] text-cool-grey mb-3 leading-relaxed">
          {org.location}
          {org.location && displayedCauses.length > 0 && ' · '}
          {displayedCauses.join(', ')}
          {hiddenCauseCount > 0 && <span> +{hiddenCauseCount} more</span>}
        </p>
      )}

      {/* Mission */}
      {org.mission && (
        <p className="font-body text-[13px] text-cool-grey mb-3 line-clamp-2 italic">
          &ldquo;{org.mission.replace(/^[""\s]+|[""\s]+$/g, '')}&rdquo;
        </p>
      )}

      {/* Health badge + peer rank */}
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold border font-body ${health.classes}`}>
          {health.label}
        </span>
        {org.is_hidden_gem && (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold border bg-violet-50 text-violet-700 border-violet-200 font-body">
            Hidden gem
          </span>
        )}
        {org.merit_score_v5 >= 50 && (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold border bg-deep-navy/5 text-deep-navy border-deep-navy/10 font-body">
            Top {Math.max(1, 100 - org.merit_score_v5)}% of peers
          </span>
        )}
      </div>

      {/* Giving intent */}
      {intentText && (
        <div className="border-t border-light-grey pt-3 mb-4">
          <p className={`font-body text-[12px] font-medium ${intentText === 'No longer interested' ? 'text-cool-grey line-through' : 'text-deep-navy'}`}>
            {intentText}
          </p>
          {org.givingIntent?.notes && intentText !== 'No longer interested' && (
            <p className="font-body text-[11px] text-cool-grey mt-1 italic">"{org.givingIntent.notes}"</p>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2 items-center">
        {org.website && (
          <a
            href={org.website}
            target="_blank"
            rel="noopener noreferrer"
            aria-label={`Visit ${org.name}'s website`}
            className="flex-1 px-3 py-2 rounded-xl bg-deep-navy text-warm-cream font-body text-[13px] font-semibold hover:bg-deep-navy/80 transition-colors text-center"
          >
            Visit website
          </a>
        )}
        {onEdit && (
          <button
            onClick={() => onEdit(org.ein)}
            aria-label={`Edit giving intent for ${org.name}`}
            className="flex-1 px-3 py-2 rounded-xl bg-soft-gold text-deep-navy font-body text-[13px] font-semibold hover:bg-bright-gold transition-colors"
          >
            {intentText && intentText !== 'No longer interested' ? 'Edit intent' : intentText === 'No longer interested' ? 'Update intent' : 'Set intent'}
          </button>
        )}
        <Link
          to={`/org/${org.ein}`}
          aria-label={`View ${org.name} detail page`}
          className="shrink-0 p-2 rounded-lg text-cool-grey hover:text-deep-navy hover:bg-light-grey/40 transition-colors"
          title="View detail page"
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M7 17 17 7M17 7H8M17 7v9"/>
          </svg>
        </Link>
      </div>
    </div>
  )
}

export const WalletCard = React.memo(WalletCardComponent)
export default WalletCard
