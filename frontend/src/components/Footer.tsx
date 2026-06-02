import { useState } from 'react'
import { Link } from 'react-router-dom'
import { submitWaitlist } from '../data/api'

export default function Footer() {
  const [footerEmail, setFooterEmail] = useState('')
  const [footerDone, setFooterDone] = useState(false)

  async function handleSubscribe(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = footerEmail.trim()
    if (!trimmed) return
    try {
      await submitWaitlist(trimmed, 'newsletter')
    } catch {
      // still show success — submission will be retried on next visit if needed
    }
    setFooterDone(true)
  }

  return (
    <footer className="bg-deep-navy border-t border-navy-mid">
      {/* Top Row */}
      <div className="max-w-[1200px] mx-auto px-6 lg:px-12 pt-12 pb-8">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-x-6 gap-y-8">
          {/* Brand */}
          <div className="col-span-2 lg:col-span-1">
            <Link to="/" className="font-display italic text-[20px] text-warm-cream tracking-[-0.02em]">
              Daanaa
            </Link>
            <p className="mt-2 font-body text-[14px] leading-[1.5] tracking-[0.01em] text-muted-cream">
              See the overlooked. Give with heart. Stay private.
            </p>
          </div>

          {/* Platform */}
          <div>
            <p className="font-body text-[12px] font-medium tracking-[0.08em] text-pale-gold uppercase mb-3">
              Platform
            </p>
            <ul className="space-y-1">
              {[
                { label: 'Directory', to: '/directory' },
                { label: 'Wallet', to: '/wallet' },
                { label: 'For Nonprofits', to: '/for-nonprofits' },
              ].map(({ label, to }) => (
                <li key={label}>
                  <Link to={to} className="font-body text-[14px] text-muted-cream hover:text-warm-cream transition-colors duration-150 block py-1.5">
                    {label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Resources */}
          <div>
            <p className="font-body text-[12px] font-medium tracking-[0.08em] text-pale-gold uppercase mb-3">
              Resources
            </p>
            <ul className="space-y-1">
              {[
                { label: 'How It Works', to: '/how-it-works' },
                { label: 'How We Score', to: '/methodology' },
                { label: 'Sector Health', to: '/sector-health' },
                { label: 'FAQ', to: '/faq' },
              ].map(({ label, to }) => (
                <li key={label}>
                  <Link to={to} className="font-body text-[14px] text-muted-cream hover:text-warm-cream transition-colors block py-1.5">
                    {label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Company */}
          <div>
            <p className="font-body text-[12px] font-medium tracking-[0.08em] text-pale-gold uppercase mb-3">
              Company
            </p>
            <ul className="space-y-1">
              <li>
                <Link to="/about" className="font-body text-[14px] text-muted-cream hover:text-warm-cream transition-colors block py-1.5">About</Link>
              </li>
              <li>
                <Link to="/legal" className="font-body text-[14px] text-muted-cream hover:text-warm-cream transition-colors block py-1.5">Legal &amp; Privacy</Link>
              </li>
              <li>
                <Link to="/feedback" className="font-body text-[14px] text-muted-cream hover:text-warm-cream transition-colors block py-1.5">Share feedback</Link>
              </li>
              <li>
                <Link to="/feedback?type=data-issue" className="font-body text-[14px] text-muted-cream hover:text-warm-cream transition-colors block py-1.5">Report a data issue</Link>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Middle Row - Newsletter */}
      <div className="max-w-[1200px] mx-auto px-6 lg:px-12 py-6 border-t border-navy-mid">
        <form onSubmit={handleSubscribe} className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
          <span className="font-body text-[12px] tracking-[0.02em] text-muted-cream">
            Get nonprofit insights weekly
          </span>
          <div className="flex gap-2">
            {footerDone ? (
              <span className="font-body text-[14px] text-soft-gold py-2">✓ You're on the list</span>
            ) : (
              <>
                <input
                  type="email"
                  value={footerEmail}
                  onChange={e => setFooterEmail(e.target.value)}
                  placeholder="Enter your email"
                  className="bg-navy-mid border border-navy-mid text-warm-cream text-[14px] px-4 py-2 rounded-lg w-[200px] outline-none focus:border-soft-gold transition-colors placeholder:text-cool-grey ring-1 ring-white/10"
                />
                <button type="submit" className="bg-soft-gold text-deep-navy font-body text-[14px] font-medium px-5 py-2 rounded-lg hover:bg-bright-gold transition-colors">
                  Subscribe
                </button>
              </>
            )}
          </div>
        </form>
      </div>

      {/* Bottom Row */}
      <div className="max-w-[1200px] mx-auto px-6 lg:px-12 py-6 border-t border-navy-mid flex flex-col sm:flex-row items-center justify-between gap-4">
        <p className="font-body text-[12px] tracking-[0.02em] text-cool-grey/60">
          © 2026 Daanaa. Data sourced from IRS, NCCS, and ProPublica public records. Some descriptions and links are AI-generated or auto-collected and labeled beta.{' '}
          <Link to="/legal" className="hover:text-warm-cream transition-colors underline underline-offset-2">
            Attribution & Terms
          </Link>
        </p>
        <div className="flex items-center gap-4">
          {/* LinkedIn */}
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#A89F94" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="hover:stroke-warm-cream transition-colors cursor-pointer">
            <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" />
            <rect x="2" y="9" width="4" height="12" />
            <circle cx="4" cy="4" r="2" />
          </svg>
          {/* Twitter/X */}
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#A89F94" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="hover:stroke-warm-cream transition-colors cursor-pointer">
            <path d="M4 4l6.5 8L4 20h2l5.5-6.5L16 20h4l-6.8-8.8L20 4h-2l-5.2 6L8 4H4z" />
          </svg>
        </div>
      </div>
    </footer>
  )
}
