import { Link } from 'react-router-dom'

const NAV_COLS = [
  {
    heading: 'Discover',
    links: [
      { label: 'Directory', to: '/directory' },
      { label: 'Research', to: '/research' },
      { label: 'Open data', to: '/open-data' },
      { label: 'Wallet', to: '/wallet' },
    ],
  },
  {
    heading: 'Get Involved',
    links: [
      { label: 'Claim your page', to: '/for-nonprofits' },
      { label: 'Volunteer', to: '/volunteer' },
      { label: 'Member benefits', to: '/member/benefits' },
      { label: 'Join the network', to: '/for-vendors' },
    ],
  },
  {
    heading: 'Learn',
    links: [
      { label: 'About Daanaa', to: '/about' },
      { label: 'How it works', to: '/methodology' },
      { label: 'Our Charter', to: '/charter' },
    ],
  },
  {
    heading: 'Legal',
    links: [
      { label: 'Privacy', to: '/privacy' },
      { label: 'Security', to: '/security' },
      { label: 'Terms', to: '/terms' },
      { label: 'Partners', to: '/partners' },
      { label: 'Contact', to: '/feedback' },
    ],
  },
]

export default function Footer() {
  return (
    <footer className="bg-deep-navy border-t border-navy-mid">
      {/* Main link grid */}
      <div className="max-w-[1200px] mx-auto px-6 lg:px-12 pt-12 pb-8">
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-x-6 gap-y-8">
          {/* Brand */}
          <div className="col-span-2 lg:col-span-1">
            <Link to="/" className="font-display italic text-[20px] text-warm-cream tracking-[-0.02em]">
              Daanaa
            </Link>
            <p className="mt-2 font-body text-[14px] leading-[1.5] tracking-[0.01em] text-muted-cream">
              See the overlooked.<br />Give with heart.
            </p>
          </div>

          {/* Nav columns */}
          {NAV_COLS.map(({ heading, links }) => (
            <div key={heading}>
              <p className="font-body text-[12px] font-medium tracking-[0.08em] text-pale-gold uppercase mb-3">
                {heading}
              </p>
              <ul className="space-y-1">
                {links.map(({ label, to }) => (
                  <li key={label}>
                    <Link
                      to={to}
                      className="font-body text-[14px] text-muted-cream hover:text-warm-cream transition-colors duration-150 block py-1.5"
                    >
                      {label}
                    </Link>
                  </li>
                ))}
                {heading === 'Discover' && (
                  <li>
                    <a
                      href="https://data.daanaa.org/nonprofits/state/index.html"
                      className="font-body text-[14px] text-muted-cream hover:text-warm-cream transition-colors duration-150 block py-1.5"
                    >
                      Explore by location
                    </a>
                  </li>
                )}
                {heading === 'Discover' && (
                  <li>
                    <a
                      href="/llms.txt"
                      className="font-body text-[14px] text-muted-cream hover:text-warm-cream transition-colors duration-150 block py-1.5"
                    >
                      AI access file
                    </a>
                  </li>
                )}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom bar */}
      <div className="max-w-[1200px] mx-auto px-6 lg:px-12 py-6 border-t border-navy-mid space-y-2">
        <p className="font-body text-[12px] tracking-[0.02em] text-muted-cream">
          Daanaa is an independent nonprofit discovery platform. Not affiliated with the IRS, the federal government, or any nonprofit rating agency.
        </p>
        <p className="font-body text-[12px] tracking-[0.02em] text-muted-cream">
          Daanaa does not process donations, hold donor funds, issue tax receipts, or represent any nonprofit.
        </p>
        <p className="font-body text-[12px] tracking-[0.02em] text-muted-cream">
          Public records may be delayed or incomplete. Independently verify an organization before donating or volunteering.
        </p>
        <p className="font-body text-[12px] tracking-[0.02em] text-muted-cream">
          © 2026 Daanaa. Data sourced from IRS, NCCS, and ProPublica public records. Some summaries, categories, and descriptions may be AI assisted and should be reviewed for accuracy.{' '}
          <Link to="/legal" className="hover:text-warm-cream transition-colors duration-150 underline underline-offset-2">
            Attribution &amp; Terms
          </Link>
        </p>
      </div>
    </footer>
  )
}
