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
  STABLE:  { label: 'Financially stable',         classes: 'bg-amber-50 text-amber-700 border-amber-200' },
  CAUTION: { label: 'Needs support',    classes: 'bg-orange-50 text-orange-700 border-orange-200' },
}

function getIntentDisplay(org: WalletOrg): string | null {
  const intent = org.givingIntent
  if (!intent) return null
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
            Top {100 - org.merit_score_v5}% of peers
          </span>
        )}
      </div>

      {/* Giving intent */}
      {intentText && (
        <div className="border-t border-light-grey pt-3 mb-4">
          <p className="font-body text-[12px] font-medium text-deep-navy">{intentText}</p>
          {org.givingIntent?.notes && (
            <p className="font-body text-[11px] text-cool-grey mt-1 italic">"{org.givingIntent.notes}"</p>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2">
        {onEdit && (
          <button
            onClick={() => onEdit(org.ein)}
            aria-label={`Edit giving intent for ${org.name}`}
            className="flex-1 px-3 py-2 rounded-xl bg-soft-gold text-deep-navy font-body text-[13px] font-semibold hover:bg-bright-gold transition-colors"
          >
            {intentText ? 'Edit intent' : 'Set intent'}
          </button>
        )}
        <Link
          to={`/org/${org.ein}`}
          className="flex-1 px-3 py-2 rounded-xl border border-light-grey text-cool-grey font-body text-[13px] font-medium hover:border-soft-gold/40 hover:text-deep-navy transition-colors text-center"
        >
          View
        </Link>
      </div>
    </div>
  )
}

export const WalletCard = React.memo(WalletCardComponent)
export default WalletCard
