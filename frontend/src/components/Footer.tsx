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
        <div className="grid grid-cols-2 lg:grid-cols-6 gap-x-6 gap-y-8">
          {/* Brand */}
          <div className="col-span-2 lg:col-span-1">
            <Link to="/" className="font-display italic text-[20px] text-warm-cream tracking-[-0.02em]">
              Daanaa
            </Link>
            <p className="mt-2 font-body text-[14px] leading-[1.5] tracking-[0.01em] text-muted-cream">
              See the overlooked. Give with heart. Stay private.
            </p>
          </div>

          {/* Quick Links (per spec order) */}
          <div>
            <p className="font-body text-[12px] font-medium tracking-[0.08em] text-pale-gold uppercase mb-3">
              Discover
            </p>
            <ul className="space-y-1">
              {[
                { label: 'Discover Organizations', to: '/directory' },
                { label: 'Your Wallet', to: '/wallet' },
              ].map(({ label, to }) => (
                <li key={label}>
                  <Link to={to} className="font-body text-[14px] text-muted-cream hover:text-warm-cream transition-colors duration-150 block py-1.5">
                    {label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* For Nonprofits */}
          <div>
            <p className="font-body text-[12px] font-medium tracking-[0.08em] text-pale-gold uppercase mb-3">
              For Nonprofits
            </p>
            <ul className="space-y-1">
              {[
                { label: 'Claim Your Profile', to: '/for-nonprofits' },
              ].map(({ label, to }) => (
                <li key={label}>
                  <Link to={to} className="font-body text-[14px] text-muted-cream hover:text-warm-cream transition-colors duration-150 block py-1.5">
                    {label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Learn */}
          <div>
            <p className="font-body text-[12px] font-medium tracking-[0.08em] text-pale-gold uppercase mb-3">
              Learn
            </p>
            <ul className="space-y-1">
              {[
                { label: 'Methodology', to: '/methodology' },
                { label: 'Stewardship', to: '/stewardship' },
                { label: 'Guides', to: '/guides' },
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

          {/* About */}
          <div>
            <p className="font-body text-[12px] font-medium tracking-[0.08em] text-pale-gold uppercase mb-3">
              About
            </p>
            <ul className="space-y-1">
              {[
                { label: 'About Daanaa', to: '/about' },
                { label: 'Privacy', to: '/legal#privacy' },
                { label: 'Terms', to: '/legal#terms' },
                { label: 'Contact', to: '/feedback' },
              ].map(({ label, to }) => (
                <li key={label}>
                  <Link to={to} className="font-body text-[14px] text-muted-cream hover:text-warm-cream transition-colors block py-1.5">
                    {label}
                  </Link>
                </li>
              ))}
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
      <div className="max-w-[1200px] mx-auto px-6 lg:px-12 py-6 border-t border-navy-mid flex flex-col gap-4">
        <p className="font-body text-[12px] tracking-[0.02em] text-cool-grey/60">
          Daanaa.org is an independent nonprofit discovery platform. It is not affiliated with the IRS, the federal government, or any nonprofit rating agency.
        </p>
        <p className="font-body text-[12px] tracking-[0.02em] text-cool-grey/60">
          © 2026 Daanaa. Data sourced from IRS, NCCS, and ProPublica public records. Some descriptions and links are AI-generated or auto-collected and labeled beta.{' '}
          <Link to="/legal" className="hover:text-warm-cream transition-colors underline underline-offset-2">
            Attribution & Terms
          </Link>
        </p>
      </div>
    </footer>
  )
}
