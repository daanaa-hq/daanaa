import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useSavedOrgs } from '../hooks/useSavedOrgs'
import GivingListDrawer from './GivingListDrawer'

interface NavigationProps {
  solid?: boolean
}

export default function Navigation({ solid = true }: NavigationProps) {
  const [mobileOpen, setMobileOpen] = useState(false)
  const location = useLocation()
  const { count: savedCount } = useSavedOrgs()

  const isActive = (path: string) => location.pathname === path

  return (
    <>
      <nav
        className="fixed top-0 left-0 right-0 z-50 h-[72px] flex items-center transition-all duration-300 ease-out border-b"
        style={{
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(12px)',
          borderColor: 'rgba(229, 224, 219, 0.8)',
        }}
      >
        <div className="w-full max-w-[1200px] mx-auto px-6 lg:px-12 flex items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-0 group py-3">
            <span className="font-cinzel text-[18px] text-deep-navy tracking-[0.12em] relative">
              MER
              <span className="relative inline-block">
                <span
                  className="absolute -top-[10px] left-1/2 -translate-x-1/2 w-[2px] h-[6px] bg-soft-gold rounded-full transition-all duration-300 group-hover:h-[8px]"
                />
                I
              </span>
              T
            </span>
          </Link>

          {/* Desktop Nav Links */}
          <div className="hidden md:flex items-center gap-8">
            {[
              { label: 'Directory', path: '/directory' },
              { label: 'For Nonprofits', path: '/for-nonprofits' },
              { label: 'How It Works', path: '/how-it-works' },
            ].map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className="relative font-body text-[14px] tracking-[0.02em] transition-colors duration-150 py-3 flex items-center"
                style={{
                  color: isActive(item.path) ? '#0A1628' : '#A89F94',
                  fontWeight: isActive(item.path) ? '500' : '400',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.color = '#0A1628')}
                onMouseLeave={(e) => {
                  if (!isActive(item.path)) e.currentTarget.style.color = '#A89F94'
                }}
              >
                {item.label}
                {isActive(item.path) && (
                  <span className="absolute -bottom-1 left-0 right-0 h-[2px] bg-soft-gold rounded-full" />
                )}
              </Link>
            ))}
          </div>

          {/* Right Actions */}
          <div className="hidden md:flex items-center gap-3">
            <GivingListDrawer />
            <Link
              to="/wallet"
              className="relative inline-flex items-center gap-1.5 px-4 py-[11px] rounded-full font-body text-[13px] transition-all duration-150"
              style={{
                color: isActive('/wallet') ? '#C9A96E' : '#6B7280',
                background: isActive('/wallet') ? 'rgba(201,169,110,0.08)' : 'transparent',
                border: '1px solid',
                borderColor: isActive('/wallet') ? 'rgba(201,169,110,0.4)' : 'rgba(229,224,219,0.8)',
              }}
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill={savedCount > 0 ? '#C9A96E' : 'none'} stroke="#C9A96E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z" />
              </svg>
              Wallet
            </Link>
          </div>

          {/* Mobile Hamburger */}
          <button
            className="md:hidden flex flex-col gap-[5px] p-3"
            onClick={() => setMobileOpen(true)}
            aria-label="Open menu"
          >
            <span className="w-6 h-[2px] bg-deep-navy block rounded-full" />
            <span className="w-4 h-[2px] bg-deep-navy block rounded-full" />
            <span className="w-6 h-[2px] bg-deep-navy block rounded-full" />
          </button>
        </div>
      </nav>

      {/* Mobile Overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-[60] flex flex-col items-center justify-center"
          style={{ backgroundColor: 'rgba(10, 22, 40, 0.98)' }}
        >
          <button
            className="absolute top-6 right-6 p-2"
            onClick={() => setMobileOpen(false)}
            aria-label="Close menu"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#F5F0EB" strokeWidth="2">
              <line x1="4" y1="4" x2="20" y2="20" />
              <line x1="20" y1="4" x2="4" y2="20" />
            </svg>
          </button>
          <div className="flex flex-col items-center gap-5">
            {[
              { label: 'Directory', path: '/directory' },
              { label: 'For Nonprofits', path: '/for-nonprofits' },
              { label: 'How It Works', path: '/how-it-works' },
              { label: 'Wallet', path: '/wallet' },
            ].map((item, i) => (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setMobileOpen(false)}
                className="font-display italic text-[30px] tracking-[-0.01em] text-warm-cream opacity-0 animate-[fadeIn_0.4s_ease-out_forwards] hover:text-soft-gold transition-colors"
                style={{ animationDelay: `${i * 0.07}s` }}
              >
                {item.label}
              </Link>
            ))}
            <div
              className="w-12 h-px bg-white/10 my-2 opacity-0 animate-[fadeIn_0.4s_ease-out_forwards]"
              style={{ animationDelay: '0.3s' }}
            />
            <Link
              to="/directory"
              onClick={() => setMobileOpen(false)}
              className="font-body text-[15px] font-semibold bg-soft-gold text-deep-navy px-9 py-3.5 rounded-full opacity-0 animate-[fadeIn_0.4s_ease-out_forwards] hover:bg-bright-gold transition-colors"
              style={{ animationDelay: '0.35s' }}
            >
              Browse Directory
            </Link>
          </div>
        </div>
      )}

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(16px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </>
  )
}
