import type { TierName } from './TrustBadge'
import { TIER_COLORS } from './TrustBadge'

const SIZES = { xs: 16, sm: 24, md: 40, lg: 72, xl: 120 } as const
type LampSize = keyof typeof SIZES

// 8-pointed lamp form using cubic bezier curves — flagged for designer review before public launch
const PATH = [
  'M 12,1.5',
  'C 12.4,1.6 13.8,7.2 13.9,7.4',
  'C 14.6,8.0 19.8,11.5 20,12',
  'C 19.8,12.5 14.6,16.0 13.9,16.6',
  'C 13.7,16.8 12.6,20.5 12,22.5',
  'C 11.4,20.5 10.3,16.8 10.1,16.6',
  'C 9.4,16.0 4.2,12.5 4,12',
  'C 4.2,11.5 9.4,8.0 10.1,7.4',
  'C 10.2,7.2 11.6,1.6 12,1.5',
  'Z',
].join(' ')

interface LampMarkProps {
  tier: TierName
  size?: LampSize
  onClick?: () => void
  className?: string
}

export default function LampMark({ tier, size = 'md', onClick, className = '' }: LampMarkProps) {
  const px          = SIZES[size]
  const fill        = TIER_COLORS[tier]
  const interactive = !!onClick

  return (
    <svg
      viewBox="0 0 24 24"
      width={px}
      height={px}
      fill={fill}
      onClick={onClick}
      role={interactive ? 'button' : 'img'}
      aria-label={interactive ? `${tier} tier, tap to see breakdown` : `${tier} tier`}
      tabIndex={interactive ? 0 : undefined}
      onKeyDown={interactive ? (e) => { if (e.key === 'Enter' || e.key === ' ') onClick() } : undefined}
      className={`shrink-0 block${interactive ? ' cursor-pointer' : ''}${className ? ` ${className}` : ''}`}
      style={{ display: 'block' }}
    >
      <path d={PATH} />
    </svg>
  )
}
