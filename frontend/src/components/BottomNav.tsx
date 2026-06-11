import { Link, useLocation } from 'react-router-dom'
import { useSavedOrgs } from '../hooks/useSavedOrgs'

export default function BottomNav() {
  const location = useLocation()
  const { count: savedCount } = useSavedOrgs()
  const p = location.pathname

  const items = [
    {
      path: '/',
      label: 'Home',
      exact: true,
      icon: (active: boolean) => (
        <svg width="22" height="22" viewBox="0 0 24 24" fill={active ? '#C9A96E' : 'none'} stroke={active ? '#C9A96E' : '#6B7280'} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
          <polyline points="9 22 9 12 15 12 15 22"/>
        </svg>
      ),
    },
    {
      path: '/directory',
      label: 'Search',
      exact: false,
      icon: (active: boolean) => (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={active ? '#C9A96E' : '#6B7280'} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="11" cy="11" r="8"/>
          <path d="m21 21-4.3-4.3"/>
        </svg>
      ),
    },
    {
      path: '/wallet',
      label: 'Wallet β',
      exact: false,
      badge: savedCount > 0 ? savedCount : 0,
      icon: (active: boolean) => (
        <svg width="22" height="22" viewBox="0 0 24 24" fill={active ? '#C9A96E' : 'none'} stroke={active ? '#C9A96E' : '#6B7280'} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z"/>
        </svg>
      ),
    },
  ]

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-40 md:hidden bg-white"
      style={{
        paddingBottom: 'env(safe-area-inset-bottom, 0px)',
        boxShadow: '0 -1px 0 rgba(229,224,219,0.9), 0 -8px 24px rgba(10,22,40,0.06)',
      }}
    >
      <div className="flex items-stretch">
        {items.map(item => {
          const isActive = item.exact ? p === item.path : p.startsWith(item.path)
          return (
            <Link
              key={item.path}
              to={item.path}
              className="relative flex-1 flex flex-col items-center justify-center gap-[4px] min-h-[56px] pt-2 pb-1 transition-colors duration-150"
              aria-label={item.label}
            >
              {/* Active indicator bar */}
              <div
                className="absolute top-0 left-1/2 -translate-x-1/2 rounded-b-full transition-all duration-200"
                style={{
                  width: isActive ? '24px' : '0px',
                  height: '2px',
                  backgroundColor: '#C9A96E',
                }}
              />
              <div className="relative">
                {item.icon(isActive)}
                {item.badge != null && item.badge > 0 && (
                  <span className="absolute -top-1 -right-1.5 min-w-[15px] h-[15px] flex items-center justify-center bg-soft-gold text-deep-navy text-[8px] font-bold rounded-full px-[3px]">
                    {item.badge > 9 ? '9+' : item.badge}
                  </span>
                )}
              </div>
              <span
                className="font-body text-[11px] tracking-[0.02em] leading-none"
                style={{ color: isActive ? '#C9A96E' : '#9CA3AF' }}
              >
                {item.label}
              </span>
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
