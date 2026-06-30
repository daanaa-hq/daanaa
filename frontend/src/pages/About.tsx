import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import RelatedPages from '../components/RelatedPages'

export default function About() {
  usePageMeta('About — Daanaa', 'Daanaa is an independent nonprofit discovery platform built to make giving discovery simpler, more contextual, and more respectful.')

  return (
    <div className="min-h-[100dvh]">
      <div className="bg-deep-navy pt-[72px]">
        <div className="max-w-[1120px] mx-auto px-6 md:px-12 pt-16 pb-12">
          <div className="flex items-center gap-2 mb-6">
            <Link to="/" className="font-body text-[12px] text-muted-cream">Home</Link>
            <span className="text-muted-cream">/</span>
            <span className="font-body text-[12px] text-muted-cream">About</span>
          </div>
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-10 md:gap-16">
            <h1 className="font-display italic text-warm-cream mt-3 text-[48px] md:text-[60px] leading-[1.05]">About Daanaa</h1>
            <div className="shrink-0 hidden md:flex justify-end">
              <img src="/logo.png" alt="Daanaa" className="w-44 h-44 lg:w-52 lg:h-52 object-contain drop-shadow-[0_12px_48px_rgba(201,169,110,0.22)]" />
            </div>
          </div>
        </div>
      </div>

      <div className="bg-warm-cream py-16 md:py-20">
        <div className="max-w-[1120px] mx-auto px-6 md:px-12">

          <div className="max-w-[720px] mb-16">
            <p className="font-body text-[18px] text-cool-grey leading-[1.65]">
              Daanaa was created to make nonprofit discovery simpler, more contextual, and more respectful.
            </p>
            <p className="mt-6 font-body text-[16px] text-cool-grey leading-[1.65]">
              The platform is built around a simple belief: <span className="font-semibold text-deep-navy">giving should be guided by wisdom, not pressure.</span>
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-12 my-16">
            <div>
              <h2 className="font-display text-deep-navy text-[24px] mb-6">What we are</h2>
              <ul className="space-y-3">
                {[
                  'An independent nonprofit discovery platform',
                  'A public information organizer',
                  'A discovery layer for causes and organizations'
                ].map(item => (
                  <li key={item} className="flex items-start gap-3 font-body text-[16px] text-cool-grey">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2.5" className="shrink-0 mt-0.5">
                      <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                    {item}
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h2 className="font-display text-deep-navy text-[24px] mb-6">What we are not</h2>
              <ul className="space-y-3">
                {[
                  'Not a rating agency',
                  'Not a donation processor',
                  'Not affiliated with the IRS',
                  'Not a nonprofit ranking platform'
                ].map(item => (
                  <li key={item} className="flex items-start gap-3 font-body text-[16px] text-cool-grey">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#D1D5DB" strokeWidth="2.5" className="shrink-0 mt-0.5">
                      <line x1="5" y1="12" x2="19" y2="12"></line>
                    </svg>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="bg-white border border-light-grey rounded-2xl p-8 md:p-12 my-16">
            <h2 className="font-display text-deep-navy text-[28px] mb-6">Our commitment</h2>
            <p className="font-body text-[16px] text-cool-grey leading-[1.65]">
              We believe people deserve clear information, honest context, and the freedom to choose for themselves. We believe small organizations deserve to be seen. We believe trust is earned through transparency, fairness, and humility.
            </p>
            <p className="mt-6 font-body text-[16px] text-cool-grey leading-[1.65]">
              If Daanaa succeeds, it will not be because of technology alone. It will be because it earns trust over time. That trust matters more than growth.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
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
              <div key={item.title} className="bg-white border border-light-grey rounded-xl p-6 text-center">
                <h3 className="font-display text-deep-navy text-[20px] mb-2">{item.title}</h3>
                <p className="font-body text-[14px] text-cool-grey">{item.description}</p>
              </div>
            ))}
          </div>

          <RelatedPages
            links={[
              { to: '/methodology', label: 'How we score' },
              { to: '/research', label: 'Research & data' },
              { to: '/principles', label: 'Our principles' },
              { to: '/directory', label: 'Browse the directory' },
            ]}
          />

          <div className="mt-12 pt-8 border-t border-light-grey text-center">
            <p className="font-body text-[14px] text-cool-grey mb-6">Questions? <Link to="/feedback" className="text-soft-gold hover:text-bright-gold font-semibold">Get in touch</Link>.</p>
          </div>

        </div>
      </div>
    </div>
  )
}
