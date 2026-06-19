import React from 'react'
import { Link } from 'react-router-dom'
import type { WalletOrg } from '../types/wallet'

interface WalletCardProps {
  org: WalletOrg
  onRemove?: (ein: string) => void
  onEdit?: (ein: string) => void
}

/**
 * WalletCard: Individual nonprofit card in wallet
 * Shows org info, financial health, giving intent, and actions
 * Memoized to prevent unnecessary rerenders
 */
function WalletCardComponent({ org, onRemove, onEdit }: WalletCardProps) {
  const healthBgColor = {
    HEALTHY: 'bg-green-50 border-green-200',
    STABLE: 'bg-yellow-50 border-yellow-200',
    CAUTION: 'bg-orange-50 border-orange-200',
  }[org.merit_health_signal_v5]

  const healthBadgeColor = {
    HEALTHY: 'bg-green-100 text-green-800',
    STABLE: 'bg-yellow-100 text-yellow-800',
    CAUTION: 'bg-orange-100 text-orange-800',
  }[org.merit_health_signal_v5]

  // Show max 3 cause tags, with +N more indicator
  const displayedCauses = org.cause.slice(0, 3)
  const hiddenCauseCount = Math.max(0, org.cause.length - 3)

  // Format giving intent display
  const getIntentDisplay = () => {
    if (!org.givingIntent) {
      return 'No intent set'
    }

    const { type, amount, hours, frequency } = org.givingIntent

    switch (type) {
      case 'giving': {
        if (!amount) return 'Interested in Giving'
        const freqLabel = frequency === 'month' ? '/month' : frequency === 'one-time' ? '(one-time)' : '/year'
        return `Interested in Giving · $${amount}${freqLabel}`
      }
      case 'volunteer':
        return hours ? `Interested in Volunteering · ${hours} hours/week` : 'Interested in Volunteering'
      case 'board':
        return 'Interested in Board Opportunity'
      default:
        return 'No intent set'
    }
  }

  return (
    <div className={`border rounded-lg p-5 transition-all hover:shadow-md ${healthBgColor}`}>
      {/* Header: Org Name + Remove Button */}
      <div className="flex items-start justify-between mb-3">
        <Link
          to={`/org/${org.ein}`}
          className="text-lg font-semibold text-deep-navy hover:text-soft-gold transition-colors flex-1"
        >
          {org.name}
        </Link>
        {onRemove && (
          <button
            onClick={() => onRemove(org.ein)}
            aria-label={`Remove ${org.name} from wallet`}
            className="ml-2 p-1 hover:bg-white/50 rounded transition-colors flex-shrink-0"
            title="Remove from wallet"
          >
            <svg
              className="w-5 h-5 text-cool-grey hover:text-deep-navy"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* Location + Causes */}
      <div className="mb-3">
        <p className="text-sm text-cool-grey">
          {org.location}
          {displayedCauses.length > 0 && ' · '}
          {displayedCauses.join(', ')}
          {hiddenCauseCount > 0 && <span> +{hiddenCauseCount} more</span>}
        </p>
      </div>

      {/* Mission */}
      {org.mission && (
        <p className="text-sm text-slate-600 mb-3 line-clamp-2">"{org.mission}"</p>
      )}

      {/* Health Signal + Score */}
      <div className="mb-4 flex items-center gap-2 flex-wrap">
        <span className={`px-2 py-1 rounded text-xs font-semibold ${healthBadgeColor}`}>
          {org.merit_health_signal_v5}
        </span>
        <span className="text-xs text-cool-grey">
          Score: {org.merit_score_v5}/100
        </span>
        {org.is_hidden_gem && (
          <span className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded font-semibold">
            Hidden Gem
          </span>
        )}
      </div>

      {/* Giving Intent / Status */}
      <div className="border-t border-current border-opacity-20 pt-3 mb-4">
        <p className="text-sm font-medium text-deep-navy">
          {getIntentDisplay()}
        </p>
        {org.givingIntent?.notes && (
          <p className="text-xs text-slate-600 mt-1 italic">"{org.givingIntent.notes}"</p>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2">
        {onEdit && (
          <button
            onClick={() => onEdit(org.ein)}
            aria-label={`Edit giving intent for ${org.name}`}
            className="flex-1 px-3 py-2 bg-soft-gold text-white rounded-lg text-sm font-medium hover:bg-soft-gold/90 transition-colors"
          >
            Edit
          </button>
        )}
        <Link
          to={`/org/${org.ein}`}
          className="flex-1 px-3 py-2 bg-warm-cream text-deep-navy rounded-lg text-sm font-medium hover:bg-warm-cream/70 transition-colors text-center border border-light-grey"
        >
          View
        </Link>
      </div>
    </div>
  )
}

export const WalletCard = React.memo(WalletCardComponent)

export default WalletCard
