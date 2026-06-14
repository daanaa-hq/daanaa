import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'

export default function About() {
  usePageMeta('About — Daanaa', 'The story behind Daanaa: an independent nonprofit discovery platform built on stewardship, transparency, and respect.')

  return (
    <div className="min-h-[100dvh]">
      <div className="bg-deep-navy pt-[72px]">
        <div className="max-w-[1120px] mx-auto px-6 md:px-12 pt-12 pb-10">
          <div className="flex items-center gap-2 mb-4">
            <Link to="/" className="font-body text-[12px] text-muted-cream">Home</Link>
            <span className="text-muted-cream">/</span>
            <span className="font-body text-[12px] text-muted-cream">About</span>
          </div>
          <h1 className="font-display italic text-warm-cream text-[42px] md:text-[52px] leading-[1.05]">About Daanaa</h1>
        </div>
      </div>

      <div className="bg-warm-cream py-12 md:py-16">
        <div className="max-w-[1120px] mx-auto px-6 md:px-12">

          {/* Why section */}
          <div className="max-w-[720px] mb-12">
            <h2 className="font-display text-deep-navy text-[28px] md:text-[32px] leading-[1.15] mb-4">Why Daanaa Exists</h2>
            <div className="space-y-4 font-body text-[16px] leading-[1.65] text-cool-grey">
              <p>
                Daanaa began with a simple observation: people want to help, but the information they need is scattered across reports, filings, and databases never designed to be easily understood.
              </p>
              <p>
                Thousands of organizations are doing meaningful work without visibility or resources enjoyed by larger institutions. We created Daanaa to help bridge that gap.
              </p>
            </div>
          </div>

          {/* Mission */}
          <div className="bg-white border border-light-grey rounded-xl p-6 md:p-8 mb-12">
            <h2 className="font-display text-deep-navy text-[22px] mb-4">Our Goal</h2>
            <p className="font-body text-[15px] text-cool-grey leading-[1.6]">
              We are not here to tell people where to give. We help people discover organizations, understand public information about them, and make their own informed decisions with clarity, honesty, and freedom.
            </p>
          </div>

          {/* What we are / are not */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
            <div>
              <h3 className="font-display text-deep-navy text-[20px] mb-4">What We Are</h3>
              <ul className="space-y-2.5">
                {[
                  'An independent nonprofit discovery platform',
                  'A public information organizer',
                  'A discovery layer for causes and organizations'
                ].map(item => (
                  <li key={item} className="flex items-start gap-3 font-body text-[15px] text-cool-grey">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2.5" className="shrink-0 mt-0.5">
                      <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                    {item}
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h3 className="font-display text-deep-navy text-[20px] mb-4">What We Are Not</h3>
              <ul className="space-y-2.5">
                {[
                  'Not a rating agency',
                  'Not a donation processor',
                  'Not affiliated with the IRS',
                  'Not a nonprofit ranking platform'
                ].map(item => (
                  <li key={item} className="flex items-start gap-3 font-body text-[15px] text-cool-grey">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#D1D5DB" strokeWidth="2.5" className="shrink-0 mt-0.5">
                      <line x1="5" y1="12" x2="19" y2="12"></line>
                    </svg>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Core values */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            {[
              {
                title: 'Independent',
                description: 'We accept no paid placement or partner influence'
              },
              {
                title: 'Public-record based',
                description: 'We use only IRS, NCCS, and ProPublica data'
              },
              {
                title: 'Community-driven',
                description: 'We welcome feedback and corrections from anyone'
              }
            ].map(item => (
              <div key={item.title} className="bg-white border border-light-grey rounded-lg p-5 text-center">
                <h3 className="font-display text-deep-navy text-[18px] mb-2">{item.title}</h3>
                <p className="font-body text-[13px] text-cool-grey">{item.description}</p>
              </div>
            ))}
          </div>

          {/* Commitment */}
          <div className="bg-white border border-light-grey rounded-xl p-6 md:p-8 mb-12">
            <h2 className="font-display text-deep-navy text-[22px] mb-4">Our Commitment</h2>
            <div className="space-y-4 font-body text-[15px] text-cool-grey leading-[1.6]">
              <p>
                We believe people deserve clear information, honest context, and the freedom to choose for themselves. We believe small organizations deserve to be seen. We believe trust is earned through transparency, fairness, and humility.
              </p>
              <p>
                If Daanaa succeeds, it will not be because of technology alone. <span className="font-semibold text-deep-navy">It will be because it earns trust over time. That trust matters more than growth.</span>
              </p>
            </div>
          </div>

          {/* Learn more links */}
          <div className="pt-8 border-t border-light-grey">
            <p className="font-body text-[12px] font-semibold tracking-[0.08em] text-cool-grey uppercase mb-6">Learn more</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Link
                to="/how-it-works"
                className="group p-5 border border-light-grey rounded-lg hover:border-soft-gold/50 hover:bg-white/60 transition-all"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-display text-deep-navy text-[16px] group-hover:text-soft-gold transition-colors">How we score</h3>
                    <p className="mt-1 font-body text-[13px] text-cool-grey">Our methodology for financial health and peer analysis</p>
                  </div>
                  <svg className="w-4 h-4 text-soft-gold shrink-0 group-hover:translate-x-0.5 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <polyline points="9 18 15 12 9 6"></polyline>
                  </svg>
                </div>
              </Link>

              <Link
                to="/methodology"
                className="group p-5 border border-light-grey rounded-lg hover:border-soft-gold/50 hover:bg-white/60 transition-all"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-display text-deep-navy text-[16px] group-hover:text-soft-gold transition-colors">Visibility levels</h3>
                    <p className="mt-1 font-body text-[13px] text-cool-grey">What each tier means and how data completeness varies</p>
                  </div>
                  <svg className="w-4 h-4 text-soft-gold shrink-0 group-hover:translate-x-0.5 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <polyline points="9 18 15 12 9 6"></polyline>
                  </svg>
                </div>
              </Link>
            </div>
          </div>

          <div className="mt-10 pt-8 border-t border-light-grey">
            <h2 className="font-display text-deep-navy text-[20px] font-semibold mb-3">How Daanaa stays free</h2>
            <p className="font-body text-[15px] text-cool-grey leading-[1.7] max-w-xl">
              Daanaa is free for donors and nonprofits. The Daanaa vendor network — businesses that offer nonprofits better pricing on the tools they already need — supports the infrastructure that keeps it that way. No ads, no donor data, no paid placement. Vendors earn access to nonprofit buyers by offering genuine value, and the arrangement is transparent by design.
            </p>
          </div>

          {import.meta.env.VITE_SUPPORT_URL && (
            <div className="mt-10 pt-8 border-t border-light-grey">
              <h2 className="font-display text-deep-navy text-[20px] font-semibold mb-3">Support the work</h2>
              <p className="font-body text-[15px] text-cool-grey mb-4 max-w-xl">
                Daanaa is free for everyone. If you find it useful, you can support the team behind it. Contributions go to EcoMargins LLC, which operates Daanaa.
              </p>
              <a
                href={import.meta.env.VITE_SUPPORT_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block font-body text-[14px] font-semibold bg-soft-gold text-deep-navy px-6 py-2.5 rounded-lg hover:bg-bright-gold transition-colors"
              >
                Support Daanaa
              </a>
              <p className="mt-3 font-body text-[12px] text-cool-grey">
                Not tax-deductible. This supports EcoMargins LLC, not a nonprofit.
              </p>
            </div>
          )}

          <div className="mt-10 pt-8 border-t border-light-grey text-center">
            <p className="font-body text-[14px] text-cool-grey">
              Questions? <Link to="/feedback" className="text-soft-gold hover:text-bright-gold font-semibold">Get in touch</Link>.
            </p>
          </div>

        </div>
      </div>
    </div>
  )
}
