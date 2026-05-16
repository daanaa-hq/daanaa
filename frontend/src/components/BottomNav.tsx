import { Link, useLocation } from 'react-router-dom'
import { useGivingList } from '../hooks/useGivingList'
import { useSavedOrgs } from '../hooks/useSavedOrgs'

export default function BottomNav() {
  const location = useLocation()
  const { count } = useGivingList()
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
      path: '/giving-list',
      label: 'Give',
      exact: false,
      badge: count,
      icon: (active: boolean) => (
        <svg width="22" height="22" viewBox="0 0 24 24" fill={active ? '#C9A96E' : 'none'} stroke={active ? '#C9A96E' : '#6B7280'} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
        </svg>
      ),
    },
    {
      path: '/wallet',
      label: 'Wallet',
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
      className="fixed bottom-0 left-0 right-0 z-40 md:hidden bg-merit-cream"
      style={{
        paddingBottom: 'env(safe-area-inset-bottom, 0px)',
        boxShadow: '0 -4px 24px rgba(10,22,40,0.08)',
      }}
    >
      <div className="flex items-center py-1">
        {items.map(item => {
          const isActive = item.exact ? p === item.path : p.startsWith(item.path)
          return (
            <Link
              key={item.path}
              to={item.path}
              className="flex-1 flex items-center justify-center py-1"
            >
              <div
                className="flex flex-col items-center gap-[3px] px-5 py-2 rounded-2xl transition-all duration-200"
                style={{ backgroundColor: isActive ? 'rgba(201,169,110,0.12)' : 'transparent' }}
              >
                <div className="relative">
                  {item.icon(isActive)}
                  {item.badge != null && item.badge > 0 && (
                    <span className="absolute -top-1.5 -right-1.5 min-w-[16px] h-4 flex items-center justify-center bg-soft-gold text-deep-navy text-[9px] font-bold rounded-full px-1">
                      {item.badge > 9 ? '9+' : item.badge}
                    </span>
                  )}
                </div>
                <span
                  className="font-body text-[10px] tracking-[0.03em]"
                  style={{ color: isActive ? '#C9A96E' : '#A89F94' }}
                >
                  {item.label}
                </span>
              </div>
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
