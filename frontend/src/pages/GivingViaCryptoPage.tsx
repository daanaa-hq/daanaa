import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import TrustNav from '../components/TrustNav'

export default function GivingViaCryptoPage() {
  usePageMeta(
    'Give Cryptocurrency',
    'How donating digital assets to a nonprofit works, and what the IRS requires.'
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
            Give digital assets directly.
          </p>

          <p className="mt-8 max-w-[680px] font-body text-[15px] text-muted-cream leading-[1.6]">
            The IRS treats cryptocurrency as property, not currency. That means donating it follows the rules for noncash gifts, which are different from giving cash.
          </p>
        </div>
      </div>

      {/* Main content */}
      <div className="bg-warm-cream py-16 md:py-20">
        <div className="max-w-[1120px] mx-auto px-6 md:px-12">

          {/* Up front disclaimer */}
          <section className="mb-14">
            <div className="bg-white border border-light-grey rounded-lg p-6">
              <p className="font-body text-[14px] text-cool-grey leading-[1.7]">
                <strong>This is not tax advice.</strong> Crypto donations involve valuation, holding period, and appraisal rules that depend on your own situation. Everything below points to the IRS as the authority. Talk to a tax professional before you give.
              </p>
            </div>
          </section>

          {/* How to give */}
          <section className="mb-16">
            <h2 className="font-display italic text-deep-navy text-[26px] md:text-[32px] mb-10">How to give cryptocurrency</h2>

            <div className="space-y-8">
              <div className="border-l-4 border-soft-gold pl-6">
                <div className="flex items-baseline gap-3 mb-3">
                  <span className="font-display text-deep-navy text-[24px]">1</span>
                  <h3 className="font-display text-deep-navy text-[20px]">Check whether the nonprofit accepts it</h3>
                </div>
                <p className="font-body text-[15px] text-cool-grey leading-[1.65]">
                  Most nonprofits do not accept crypto directly. Those that do usually work through a platform or accept it into a donor-advised fund. Ask them before sending anything.
                </p>
                <p className="font-body text-[14px] text-cool-grey leading-[1.65] mt-3">
                  A transfer sent to the wrong address cannot be reversed by anyone, including the nonprofit.
                </p>
              </div>

              <div className="border-l-4 border-soft-gold pl-6">
                <div className="flex items-baseline gap-3 mb-3">
                  <span className="font-display text-deep-navy text-[24px]">2</span>
                  <h3 className="font-display text-deep-navy text-[20px]">Know your holding period</h3>
                </div>
                <p className="font-body text-[15px] text-cool-grey leading-[1.65]">
                  How long you held the asset changes the deduction the IRS allows:
                </p>
                <ul className="font-body text-[14px] text-cool-grey leading-[1.65] mt-3 space-y-2 ml-4">
                  <li>• Held more than one year: generally deductible at fair market value on the donation date</li>
                  <li>• Held one year or less: generally deductible at the lesser of your cost basis or fair market value</li>
                </ul>
                <p className="font-body text-[13px] text-muted-cream/70 mt-3">
                  This mirrors how the IRS treats appreciated securities.{' '}
                  <a href="https://www.irs.gov/individuals/international-taxpayers/frequently-asked-questions-on-digital-asset-transactions" target="_blank" rel="noopener noreferrer" className="text-link-gold hover:text-bright-gold">IRS digital asset FAQs</a>
                </p>
              </div>

              <div className="border-l-4 border-soft-gold pl-6">
                <div className="flex items-baseline gap-3 mb-3">
                  <span className="font-display text-deep-navy text-[24px]">3</span>
                  <h3 className="font-display text-deep-navy text-[20px]">Transfer it and record the date</h3>
                </div>
                <p className="font-body text-[15px] text-cool-grey leading-[1.65]">
                  Send from your wallet or exchange to the address the nonprofit gives you. Write down the date and the value on that date, because the donation date is what determines the valuation.
                </p>
              </div>

              <div className="border-l-4 border-soft-gold pl-6">
                <div className="flex items-baseline gap-3 mb-3">
                  <span className="font-display text-deep-navy text-[24px]">4</span>
                  <h3 className="font-display text-deep-navy text-[20px]">Handle the paperwork</h3>
                </div>
                <p className="font-body text-[15px] text-cool-grey leading-[1.65]">
                  Noncash gifts carry more reporting than cash gifts:
                </p>
                <ul className="font-body text-[14px] text-cool-grey leading-[1.65] mt-3 space-y-2 ml-4">
                  <li>• 250 dollars or more: written acknowledgment from the nonprofit</li>
                  <li>• More than 500 dollars in noncash gifts: Form 8283</li>
                  <li>• More than 5,000 dollars claimed: a qualified appraisal is generally required</li>
                </ul>
                <p className="font-body text-[13px] text-muted-cream/70 mt-3">
                  Unlike publicly traded stock, crypto does not get the appraisal exemption above 5,000 dollars. Consult a tax professional.{' '}
                  <a href="https://www.irs.gov/instructions/i8283" target="_blank" rel="noopener noreferrer" className="text-link-gold hover:text-bright-gold">Form 8283 instructions</a>
                  {' '}and{' '}
                  <a href="https://www.irs.gov/publications/p561" target="_blank" rel="noopener noreferrer" className="text-link-gold hover:text-bright-gold">IRS Publication 561</a>
                </p>
              </div>
            </div>
          </section>

          {/* Why crypto */}
          <section className="mb-16 pt-12 border-t border-light-grey">
            <h2 className="font-display italic text-deep-navy text-[20px] md:text-[24px] mb-6">Why give crypto instead of cash?</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {[
                {
                  title: 'You hold appreciated assets',
                  body: 'If the asset has gained value and you have held it over a year, giving it directly may be treated differently than selling first. A tax professional can tell you whether that applies to you.'
                },
                {
                  title: 'You already hold crypto',
                  body: 'If this is where your assets are, giving from there can be simpler than converting first.'
                },
                {
                  title: 'It reaches them the same way',
                  body: 'Once converted by the nonprofit or its platform, the support is the same as any other gift.'
                },
                {
                  title: 'Records are traceable',
                  body: 'The transaction itself is recorded on chain, which helps document the date and amount.'
                },
              ].map((item, i) => (
                <div key={i} className="bg-white border border-light-grey rounded-xl p-6">
                  <h3 className="font-display text-deep-navy text-[16px] mb-3">{item.title}</h3>
                  <p className="font-body text-[13px] text-cool-grey leading-[1.65]">{item.body}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Cautions */}
          <section className="mb-16 pt-12 border-t border-light-grey">
            <h2 className="font-display italic text-deep-navy text-[20px] md:text-[24px] mb-6">Things to be careful about</h2>
            <ul className="font-body text-[15px] text-cool-grey leading-[1.75] space-y-3 ml-4">
              <li>• Transfers cannot be undone. Confirm the address with the nonprofit directly.</li>
              <li>• Value can move sharply between when you decide and when the transfer settles.</li>
              <li>• Network fees come out of the transfer, so the nonprofit receives slightly less.</li>
              <li>• Not every nonprofit can accept or convert digital assets, and some have a policy against it.</li>
            </ul>
          </section>

          {/* Important note */}
          <section className="mb-16 pt-12 border-t border-light-grey">
            <div className="bg-soft-gold/10 border border-soft-gold/20 rounded-lg p-6">
              <h3 className="font-display text-deep-navy text-[18px] mb-3">Important: how Daanaa works</h3>
              <p className="font-body text-[14px] text-cool-grey leading-[1.65]">
                <strong>Daanaa does NOT process your crypto donation.</strong> We hold no wallet, no keys, and no custody of any asset. We do not accept crypto ourselves. Everything happens between you and the nonprofit or the platform they use.
              </p>
              <p className="font-body text-[13px] text-muted-cream/70 mt-3">
                We do not endorse any exchange, wallet, or crypto giving platform.
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
                to="/giving-via-stocks"
                className="flex items-center justify-between px-6 py-5 bg-white border border-light-grey rounded-xl hover:border-soft-gold transition-colors group"
              >
                <div>
                  <p className="font-body text-[11px] tracking-[0.08em] text-link-gold uppercase mb-1">Similar rules</p>
                  <p className="font-display italic text-deep-navy text-[18px]">Giving stock</p>
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
