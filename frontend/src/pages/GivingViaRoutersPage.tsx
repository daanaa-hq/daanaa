import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import TrustNav from '../components/TrustNav'

export default function GivingViaRoutersPage() {
  usePageMeta(
    'Give via Platforms & Aggregators',
    'Use PayPal Giving Fund, Facebook Giving, or other giving platforms to donate to your nonprofit.'
  )

  return (
    <div className="min-h-[100dvh]">
      {/* Hero */}
      <div className="bg-deep-navy pt-[72px]">
        <div className="max-w-[1120px] mx-auto px-6 md:px-12 pt-14 pb-14">
          <div className="flex items-center gap-2 mb-6">
            <Link to="/" className="font-body text-[12px] text-muted-cream hover:text-warm-cream transition-colors">Home</Link>
            <span className="text-muted-cream">/</span>
            <span className="font-body text-[12px] text-muted-cream">Giving Guide</span>
          </div>

          <p className="font-body text-[12px] tracking-[0.1em] text-pale-gold uppercase mb-4">Giving Guide</p>

          <p className="font-display italic text-warm-cream max-w-[820px] h2-display">
            Give through platforms you already use.
          </p>

          <p className="mt-8 max-w-[680px] font-body text-[15px] text-muted-cream leading-[1.6]">
            Many nonprofits are registered with giving platforms like PayPal Giving Fund and Facebook Giving.
            You can search for the nonprofit by name or EIN and donate directly through these platforms.
          </p>
        </div>
      </div>

      {/* Main content */}
      <div className="bg-warm-cream py-16 md:py-20">
        <div className="max-w-[1120px] mx-auto px-6 md:px-12">

          {/* How it works */}
          <section className="mb-16">
            <h2 className="font-display italic text-deep-navy text-[26px] md:text-[32px] mb-10">How to give via platforms</h2>

            <div className="space-y-8">
              <div className="border-l-4 border-soft-gold pl-6">
                <div className="flex items-baseline gap-3 mb-3">
                  <span className="font-display text-deep-navy text-[24px]">1</span>
                  <h3 className="font-display text-deep-navy text-[20px]">Pick a platform</h3>
                </div>
                <p className="font-body text-[15px] text-cool-grey leading-[1.65]">
                  Choose one of the giving platforms below that you're comfortable using.
                  Each platform has its own process, but they all work similarly: search for the nonprofit and donate.
                </p>
              </div>

              <div className="border-l-4 border-soft-gold pl-6">
                <div className="flex items-baseline gap-3 mb-3">
                  <span className="font-display text-deep-navy text-[24px]">2</span>
                  <h3 className="font-display text-deep-navy text-[20px]">Search for the nonprofit</h3>
                </div>
                <p className="font-body text-[15px] text-cool-grey leading-[1.65]">
                  On the platform's website, use their search to find the nonprofit you want to support.
                  You can search by name or EIN (employer identification number — available on every nonprofit's Daanaa page).
                </p>
              </div>

              <div className="border-l-4 border-soft-gold pl-6">
                <div className="flex items-baseline gap-3 mb-3">
                  <span className="font-display text-deep-navy text-[24px]">3</span>
                  <h3 className="font-display text-deep-navy text-[20px]">Donate</h3>
                </div>
                <p className="font-body text-[15px] text-cool-grey leading-[1.65]">
                  Follow the platform's steps to complete your donation.
                  The platform handles payment processing and sends your gift to the nonprofit.
                </p>
              </div>

              <div className="border-l-4 border-soft-gold pl-6">
                <div className="flex items-baseline gap-3 mb-3">
                  <span className="font-display text-deep-navy text-[24px]">4</span>
                  <h3 className="font-display text-deep-navy text-[20px]">Get a receipt</h3>
                </div>
                <p className="font-body text-[15px] text-cool-grey leading-[1.65]">
                  The platform (or the nonprofit) will send you a receipt for tax purposes.
                  Keep it for your records.
                </p>
              </div>
            </div>
          </section>

          {/* Platforms */}
          <section className="mb-16 pt-12 border-t border-light-grey">
            <h2 className="font-display italic text-deep-navy text-[26px] md:text-[32px] mb-10">Popular giving platforms</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[
                {
                  name: 'PayPal Giving Fund',
                  description: 'Search by name or EIN. Zero fees; 100% of your donation goes to the nonprofit.',
                  url: 'https://www.paypalgivingfund.org/',
                  cta: 'Browse PayPal Giving Fund'
                },
                {
                  name: 'Facebook Giving',
                  description: 'Find nonprofits in Facebook\'s directory. Fast setup through your Facebook account.',
                  url: 'https://www.facebook.com/fundraisers/donate',
                  cta: 'Visit Facebook Giving'
                },
                {
                  name: 'Benevity',
                  description: 'Used by many corporate giving programs. Search by nonprofit name or EIN.',
                  url: 'https://www.benevity.com/',
                  cta: 'Browse Benevity'
                },
                {
                  name: 'GiveDirectly',
                  description: 'Specialized platform for direct giving. Search for vetted nonprofits.',
                  url: 'https://www.givedirectly.org/',
                  cta: 'Visit GiveDirectly'
                },
              ].map((platform, i) => (
                <a
                  key={i}
                  href={platform.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="bg-white border border-light-grey rounded-xl p-6 hover:border-soft-gold transition-colors group"
                >
                  <h3 className="font-display text-deep-navy text-[20px] mb-3 group-hover:text-link-gold transition-colors">
                    {platform.name}
                  </h3>
                  <p className="font-body text-[14px] text-cool-grey leading-[1.65] mb-4">
                    {platform.description}
                  </p>
                  <p className="font-body text-[13px] text-link-gold group-hover:text-bright-gold transition-colors">
                    {platform.cta} →
                  </p>
                </a>
              ))}
            </div>

            <p className="font-body text-[13px] text-muted-cream/70 mt-8 italic">
              Platform coverage varies by nonprofit. Not every nonprofit is registered with every platform.
              If your nonprofit isn't on a particular platform, try another or use a different giving method.
            </p>
          </section>

          {/* EIN-based search */}
          <section className="mb-16 pt-12 border-t border-light-grey">
            <h2 className="font-display italic text-deep-navy text-[20px] md:text-[24px] mb-6">What's an EIN?</h2>
            <div className="bg-soft-gold/10 border border-soft-gold/20 rounded-lg p-6">
              <p className="font-body text-[14px] text-cool-grey leading-[1.65] mb-4">
                An EIN (Employer Identification Number) is a unique ID that the IRS assigns to every nonprofit.
                It's nine digits, formatted like XX-XXXXXXX.
              </p>
              <p className="font-body text-[14px] text-cool-grey leading-[1.65]">
                Every nonprofit on Daanaa has an EIN. Look for it on the nonprofit's page.
                If a platform's search doesn't find the nonprofit by name, try searching by EIN — it always works.
              </p>
            </div>
          </section>

          {/* Privacy & fees */}
          <section className="mb-16 pt-12 border-t border-light-grey">
            <h2 className="font-display italic text-deep-navy text-[20px] md:text-[24px] mb-6">Fees & privacy</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {[
                {
                  title: 'Fees vary by platform',
                  body: 'Some platforms (like PayPal Giving Fund) are free. Others take a small fee. Check the platform's details before donating.'
                },
                {
                  title: 'Privacy depends on the platform',
                  body: 'Each platform has its own privacy policy. Review how they handle your personal information before giving.'
                },
                {
                  title: 'Direct to nonprofit',
                  body: 'The platform sends your donation directly to the nonprofit. Daanaa is not involved in the transaction.'
                },
                {
                  title: 'Tax-deductible',
                  body: 'Donations to 501(c)(3) nonprofits via these platforms are tax-deductible. Keep your receipt.'
                },
              ].map((item, i) => (
                <div key={i} className="bg-white border border-light-grey rounded-xl p-6">
                  <h3 className="font-display text-deep-navy text-[16px] mb-3">{item.title}</h3>
                  <p className="font-body text-[13px] text-cool-grey leading-[1.65]">{item.body}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Important note */}
          <section className="mb-16 pt-12 border-t border-light-grey">
            <div className="bg-soft-gold/10 border border-soft-gold/20 rounded-lg p-6">
              <h3 className="font-display text-deep-navy text-[18px] mb-3">💡 How Daanaa works</h3>
              <p className="font-body text-[14px] text-cool-grey leading-[1.65]">
                <strong>Daanaa does NOT process your donation.</strong> We show you information about nonprofits
                and link to platforms where you can give. You donate directly through the platform of your choice.
                Your donation goes directly to the nonprofit — not through Daanaa.
              </p>
              <p className="font-body text-[13px] text-muted-cream/70 mt-3">
                This keeps us independent and keeps your gift direct.
              </p>
            </div>
          </section>

          {/* Next steps */}
          <section className="mb-16 pt-12 border-t border-light-grey">
            <h2 className="font-display italic text-deep-navy text-[20px] md:text-[24px] mb-6">Ready to give?</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Link
                to="/directory"
                className="flex items-center justify-between px-6 py-5 bg-deep-navy rounded-xl hover:bg-navy-mid transition-colors group"
              >
                <div>
                  <p className="font-body text-[11px] tracking-[0.08em] text-pale-gold uppercase mb-1">Browse causes</p>
                  <p className="font-display italic text-warm-cream text-[18px]">Find a nonprofit</p>
                </div>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2" className="shrink-0 group-hover:translate-x-1 transition-transform">
                  <polyline points="9 18 15 12 9 6" />
                </svg>
              </Link>

              <Link
                to="/research"
                className="flex items-center justify-between px-6 py-5 bg-white border border-light-grey rounded-xl hover:border-soft-gold transition-colors group"
              >
                <div>
                  <p className="font-body text-[11px] tracking-[0.08em] text-link-gold uppercase mb-1">Learn more</p>
                  <p className="font-display italic text-deep-navy text-[18px]">Sector data</p>
                </div>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2" className="shrink-0 group-hover:translate-x-1 transition-transform">
                  <polyline points="9 18 15 12 9 6" />
                </svg>
              </Link>
            </div>
          </section>

          {/* Questions */}
          <div className="text-center mb-10">
            <p className="font-body text-[14px] text-cool-grey">
              Questions? <Link to="/feedback" className="text-link-gold hover:text-bright-gold font-semibold">Get in touch</Link>.
            </p>
          </div>

          <TrustNav />
        </div>
      </div>
    </div>
  )
}
