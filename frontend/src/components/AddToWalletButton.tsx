import { Link } from 'react-router-dom'
import { useWallet } from '../contexts/WalletContext'

interface AddToWalletButtonProps {
  ein: string
  orgName: string
  onAdded?: (ein: string) => void
}

const HEART_PATH = "M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"

/**
 * Two-heart save control — green = donation list, red = volunteer list.
 * Matches the org-page and directory-card pattern so "save this org" looks
 * the same everywhere on the site. Shows a giving-plan follow-up once an
 * org is in the donation list.
 */
export default function AddToWalletButton({
  ein,
  orgName,
  onAdded,
}: AddToWalletButtonProps) {
  const {
    isInFunding, isInVolunteering,
    addToFunding, addToVolunteering,
    removeFromFunding, removeFromVolunteering,
    getIntent,
  } = useWallet()

  const inFunding = isInFunding(ein)
  const inVolunteering = isInVolunteering(ein)
  const existingIntent = getIntent(ein)

  const toggleFunding = () => {
    if (inFunding) {
      removeFromFunding(ein)
    } else {
      addToFunding(ein)
      if (onAdded) onAdded(ein)
    }
  }

  const toggleVolunteering = () => {
    if (inVolunteering) {
      removeFromVolunteering(ein)
    } else {
      addToVolunteering(ein)
      if (onAdded) onAdded(ein)
    }
  }

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={toggleFunding}
          title={inFunding ? 'In donation list' : 'Add to donation list'}
          aria-pressed={inFunding}
          aria-label={inFunding ? `Remove ${orgName} from donation list` : `Add ${orgName} to donation list`}
          className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full font-body text-small font-medium transition-all duration-150"
          style={{
            background: inFunding ? '#22c55e20' : 'rgba(0,0,0,0.04)',
            border: `1px solid ${inFunding ? '#22c55e' : 'rgba(0,0,0,0.12)'}`,
            color: inFunding ? '#16a34a' : '#52525b',
          }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill={inFunding ? '#22c55e' : 'none'} stroke="#22c55e" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d={HEART_PATH}/></svg>
          {inFunding ? 'In donation list' : 'Add to donation list'}
        </button>
        <button
          type="button"
          onClick={toggleVolunteering}
          title={inVolunteering ? 'In volunteer list' : 'Add to volunteer list'}
          aria-pressed={inVolunteering}
          aria-label={inVolunteering ? `Remove ${orgName} from volunteer list` : `Add ${orgName} to volunteer list`}
          className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full font-body text-small font-medium transition-all duration-150"
          style={{
            background: inVolunteering ? '#ef444420' : 'rgba(0,0,0,0.04)',
            border: `1px solid ${inVolunteering ? '#ef4444' : 'rgba(0,0,0,0.12)'}`,
            color: inVolunteering ? '#dc2626' : '#52525b',
          }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill={inVolunteering ? '#ef4444' : 'none'} stroke="#ef4444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d={HEART_PATH}/></svg>
          {inVolunteering ? 'In volunteer list' : 'Add to volunteer list'}
        </button>
      </div>
      {inFunding && (
        <Link
          to={`/wallet?intent=${ein}`}
          className="font-body text-caption text-soft-gold hover:text-bright-gold transition-colors leading-snug"
          aria-label={existingIntent ? 'Edit your giving plan' : 'Set a giving plan'}
        >
          {existingIntent ? 'Edit your giving plan →' : 'How would you like to support them? →'}
        </Link>
      )}
    </div>
  )
}
