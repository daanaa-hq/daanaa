import type { OrgBadge } from '../utils/badges'

interface BadgeChipProps {
  badge: OrgBadge
  size?: 'sm' | 'md'
  variant?: 'light' | 'dark'
  onClick?: () => void
  active?: boolean
}

const COLOR_STYLES = {
  light: {
    green: { bg: 'rgba(42,107,69,0.08)',   border: 'rgba(42,107,69,0.22)',   text: '#2A6B45' },
    blue:  { bg: 'rgba(96,165,250,0.10)',  border: 'rgba(96,165,250,0.30)',  text: '#3B82F6' },
    gold:  { bg: 'rgba(201,169,110,0.12)', border: 'rgba(201,169,110,0.35)', text: '#C9A96E' },
  },
  // 'dark' variant sits on theme-flipping surfaces — its text colors are CSS
  // vars (declared in index.css) so they darken when the light theme is active.
  dark: {
    green: { bg: 'rgba(42,107,69,0.15)',   border: 'rgba(42,107,69,0.35)',   text: 'var(--badge-green, #5CA878)' },
    blue:  { bg: 'rgba(96,165,250,0.12)',  border: 'rgba(96,165,250,0.30)',  text: 'var(--badge-blue, #93C5FD)' },
    gold:  { bg: 'rgba(201,169,110,0.15)', border: 'rgba(201,169,110,0.40)', text: 'var(--soft-gold)' },
  },
}

function BadgeIcon({ icon, size }: { icon: OrgBadge['icon']; size: number }) {
  const s = { width: size, height: size }
  const props = { ...s, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 2.5, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const }

  switch (icon) {
    case 'check-shield':
      return <svg {...props}><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/></svg>
    case 'file-text':
      return <svg {...props}><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
    case 'trending-up':
      return <svg {...props}><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>
    case 'star':
      return <svg {...props}><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
    case 'globe':
      return <svg {...props}><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg>
    default:
      return null
  }
}

export default function BadgeChip({ badge, size = 'sm', variant = 'light', onClick, active = false }: BadgeChipProps) {
  const styles = COLOR_STYLES[variant][badge.color]
  const iconSize = size === 'sm' ? 10 : 12
  const fontSize = size === 'sm' ? '11px' : '12px'
  const px = size === 'sm' ? '8px' : '10px'
  const py = size === 'sm' ? '4px' : '6px'

  return (
    <button
      onClick={onClick}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: size === 'sm' ? '5px' : '6px',
        paddingLeft: px,
        paddingRight: px,
        paddingTop: py,
        paddingBottom: py,
        borderRadius: '999px',
        fontSize,
        fontFamily: 'var(--font-body, Inter, sans-serif)',
        fontWeight: active ? '600' : '500',
        letterSpacing: '0.01em',
        backgroundColor: active ? styles.border : styles.bg,
        border: `1px solid ${active ? styles.text : styles.border}`,
        color: styles.text,
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 0.15s ease',
        whiteSpace: 'nowrap',
      }}
    >
      <BadgeIcon icon={badge.icon} size={iconSize} />
      {badge.label}
    </button>
  )
}
