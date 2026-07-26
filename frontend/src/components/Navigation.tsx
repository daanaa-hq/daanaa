import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useWallet } from '../contexts/WalletContext'

interface NavigationProps {
  solid?: boolean
}

export default function Navigation({ solid = true }: NavigationProps) {
  const [mobileOpen, setMobileOpen] = useState(false)
  const [headerQuery, setHeaderQuery] = useState('')
  const location = useLocation()
  const navigate = useNavigate()
  const { entries } = useWallet()
  const savedCount = entries.length

  // Discover stays lit while browsing anything reached from the directory
  const discoverPrefixes = ['/directory', '/org/', '/category/', '/causes/', '/volunteer', '/events/']
  const isActive = (path: string) =>
    path === '/directory'
      ? discoverPrefixes.some(pre => location.pathname === pre || location.pathname.startsWith(pre))
      : location.pathname === path

  // Skip the header search on pages that already have a primary search of their
  // own (the hero on Home, the page-level bar on Directory) to avoid duplicates.
  const showHeaderSearch = !['/', '/directory'].includes(location.pathname)

  const submitHeaderSearch = (e: React.FormEvent) => {
    e.preventDefault()
    const q = headerQuery.trim()
    navigate(q ? `/directory?q=${encodeURIComponent(q)}` : '/directory')
    setHeaderQuery('')
    setMobileOpen(false)
  }

  return (
    <>
      <nav
        aria-label="Main navigation"
        className="fixed top-0 left-0 right-0 z-50 h-[72px] flex items-center transition-all duration-300 ease-out border-b"
        style={{
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(12px)',
          borderColor: 'rgba(229, 224, 219, 0.8)',
        }}
      >
        <div className="w-full max-w-[1200px] mx-auto px-6 lg:px-12 flex items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2.5 py-3">
            <img
              src="/logo.png"
              alt="Daanaa"
              className="h-7 w-7 object-contain"
              width={28}
              height={28}
            />
            {/* charcoal, not deep-navy: the nav bar is white in BOTH themes, and
                deep-navy inverts to near-white in light mode (invisible on white) */}
            <span className="font-cinzel text-title-sm text-charcoal tracking-[0.12em]">Daanaa</span>
          </Link>

          {/* Desktop Nav Links */}
          <div className="hidden md:flex items-center gap-8">
            {[
              { label: 'Discover', path: '/directory' },
              { label: 'Volunteer', path: '/volunteer' },
              { label: 'How it works', path: '/methodology' },
              { label: 'Claim your page', path: '/for-nonprofits' },
            ].map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className="relative font-body text-body tracking-[0.02em] transition-colors duration-150 py-3 flex items-center"
                style={{
                  color: isActive(item.path) ? '#0A1628' : '#374151',
                  fontWeight: isActive(item.path) ? '500' : '400',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.color = '#0A1628')}
                onMouseLeave={(e) => {
                  if (!isActive(item.path)) e.currentTarget.style.color = '#374151'
                }}
              >
                {item.label}
                {isActive(item.path) && (
                  <span className="absolute -bottom-1 left-0 right-0 h-[2px] bg-soft-gold rounded-full" />
                )}
              </Link>
            ))}
          </div>

          {/* Persistent header search — kept in the layout on every page so the
              nav never shifts; visually hidden where the page owns a primary search */}
          <form
            onSubmit={submitHeaderSearch}
            className={`hidden md:flex flex-1 max-w-[320px] mx-6 ${showHeaderSearch ? '' : 'invisible pointer-events-none'}`}
            aria-hidden={!showHeaderSearch}
          >
              <div className="relative w-full">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6B7280" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                     className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none">
                  <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
                <input
                  type="search"
                  value={headerQuery}
                  onChange={e => setHeaderQuery(e.target.value)}
                  placeholder="Search nonprofits…"
                  aria-label="Search nonprofits"
                  className="w-full pl-8 pr-3 py-1.5 rounded-full bg-white border border-light-grey font-body text-small text-charcoal placeholder:text-cool-grey outline-none focus:border-soft-gold focus:ring-1 focus:ring-soft-gold/30 transition-colors"
                />
              </div>
            </form>

          {/* Right Actions */}
          <div className="hidden md:flex items-center gap-3">
            <Link
              to="/wallet"
              className="relative inline-flex items-center gap-1.5 px-4 py-[11px] rounded-full font-body text-small transition-all duration-150"
              style={{
                color: isActive('/wallet') ? '#0A1628' : '#4B5563',
                background: isActive('/wallet') ? 'rgba(201,169,110,0.08)' : 'transparent',
                border: '1px solid',
                borderColor: isActive('/wallet') ? 'rgba(201,169,110,0.4)' : 'rgba(229,224,219,0.8)',
              }}
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill={savedCount > 0 ? '#C9A96E' : 'none'} stroke="#C9A96E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z" />
              </svg>
              Wallet
              {savedCount > 0 && (
                <span className="inline-flex items-center justify-center min-w-[17px] h-[17px] bg-soft-gold text-deep-navy text-micro font-bold rounded-full px-[4px]">
                  {savedCount > 99 ? '99+' : savedCount}
                </span>
              )}
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
          <div className="flex flex-col items-center gap-5 w-full max-w-[320px] px-6">
            <form onSubmit={submitHeaderSearch} className="w-full opacity-0 animate-[fadeIn_0.4s_ease-out_forwards]">
              <input
                type="search"
                value={headerQuery}
                onChange={e => setHeaderQuery(e.target.value)}
                placeholder="Search nonprofits…"
                aria-label="Search nonprofits"
                autoFocus
                className="w-full px-4 py-3 rounded-full bg-white/10 border border-white/15 font-body text-body-lg text-warm-cream placeholder:text-warm-cream/50 outline-none focus:border-soft-gold focus:bg-white/15 transition-colors"
              />
            </form>
            {[
              { label: 'Discover', path: '/directory' },
              { label: 'Volunteer', path: '/volunteer' },
              { label: 'Claim your page', path: '/for-nonprofits' },
            ].map((item, i) => (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setMobileOpen(false)}
                className="font-display italic text-headline-lg tracking-[-0.01em] text-warm-cream opacity-0 animate-[fadeIn_0.4s_ease-out_forwards] hover:text-soft-gold transition-colors"
                style={{ animationDelay: `${i * 0.07}s` }}
              >
                {item.label}
              </Link>
            ))}
            <div
              className="w-12 h-px bg-white/10 my-2 opacity-0 animate-[fadeIn_0.4s_ease-out_forwards]"
              style={{ animationDelay: '0.2s' }}
            />
            <div
              className="flex items-center gap-5 opacity-0 animate-[fadeIn_0.4s_ease-out_forwards]"
              style={{ animationDelay: '0.25s' }}
            >
              {[
                { label: 'How it works', path: '/methodology' },
                { label: 'About', path: '/about' },
              ].map(item => (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setMobileOpen(false)}
                  className="font-body text-body text-warm-cream/60 hover:text-soft-gold transition-colors"
                >
                  {item.label}
                </Link>
              ))}
            </div>
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
