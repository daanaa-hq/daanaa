import { Link, useLocation } from 'react-router-dom'

const PAGES = [
  { to: '/about',       label: 'About Daanaa',  sub: 'Identity & approach' },
  { to: '/methodology', label: 'Methodology',   sub: 'How we score' },
  { to: '/research',    label: 'Research',      sub: 'Sector data & findings' },
]

export default function TrustNav() {
  const { pathname } = useLocation()

  return (
    <div className="border-t border-light-grey pt-10 mt-16">
      <p className="font-body text-[11px] tracking-[0.1em] text-link-gold uppercase mb-5">Also in this series</p>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {PAGES.map(({ to, label, sub }) => {
          const active = pathname === to || pathname.startsWith(to + '#')
          return active ? null : (
            <Link
              key={to}
              to={to}
              className="flex items-center justify-between px-5 py-4 bg-white border border-light-grey rounded-xl hover:border-soft-gold transition-colors group"
            >
              <div>
                <p className="font-body text-[11px] tracking-[0.06em] text-cool-grey uppercase mb-0.5">{sub}</p>
                <p className="font-display italic text-deep-navy text-[16px] leading-snug">{label}</p>
              </div>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2" className="shrink-0 ml-3 group-hover:translate-x-0.5 transition-transform">
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </Link>
          )
        })}
      </div>
    </div>
  )
}
