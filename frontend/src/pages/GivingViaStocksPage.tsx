import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import TrustNav from '../components/TrustNav'

export default function GivingViaStocksPage() {
  usePageMeta(
    'Give Appreciated Stock',
    'Donate stock directly to a nonprofit and potentially avoid capital gains tax.'
  )

  return (
    <div className="min-h-[100dvh]">
      {/* Hero */}
      <div className="bg-deep-navy pt-[72px]">
        <div className="max-w-[1120px] mx-auto px-6 md:px-12 pt-14 pb-14">
          <div className="flex items-center gap-2 mb-6">
            <Link to="/" className="font-body text-caption text-muted-cream hover:text-warm-cream transition-colors">Home</Link>
            <span className="text-muted-cream">/</span>
            <span className="font-body text-caption text-muted-cream">Giving Guide</span>
          </div>

          <p className="font-body text-caption tracking-[0.1em] text-pale-gold uppercase mb-4">Giving Guide</p>

          <p className="font-display italic text-warm-cream max-w-[820px] h2-display">
            Donate stock you've held for more than a year.
          </p>

          <p className="mt-8 max-w-[680px] font-body text-body-lg text-muted-cream leading-[1.6]">
            If you have stock that's gained value, you can donate it directly to a nonprofit. You get a tax deduction for the full value, and you may avoid paying capital gains tax on the profit.
          </p>
        </div>
      </div>

      {/* Main content */}
      <div className="bg-warm-cream py-16 md:py-20">
        <div className="max-w-[1120px] mx-auto px-6 md:px-12">

          {/* Key benefit */}
          <section className="mb-16">
            <div className="bg-soft-gold/10 border border-soft-gold/20 rounded-lg p-6 mb-8">
              <h3 className="font-display text-deep-navy text-title-sm mb-3">🎯 Why donate stock?</h3>
              <p className="font-body text-body text-cool-grey leading-[1.65]">
                <strong>Tax advantage:</strong> If you've held the stock for more than one year and it's worth more than you paid for it, donating it to a nonprofit lets you:
              </p>
              <ul className="font-body text-body text-cool-grey leading-[1.65] mt-3 space-y-2 ml-4">
                <li>• Deduct the full current value (not what you paid)</li>
                <li>• Avoid paying capital gains tax on the profit</li>
              </ul>
              <p className="font-body text-caption text-muted-cream/70 mt-3 italic">
                This is not tax advice. Tax benefits depend on your situation. Consult a tax professional.
              </p>
            </div>

            <h2 className="font-display italic text-deep-navy text-headline md:text-headline-lg mb-10">How to donate stock</h2>

            <div className="space-y-8">
              <div className="border-l-4 border-soft-gold pl-6">
                <div className="flex items-baseline gap-3 mb-3">
                  <span className="font-display text-deep-navy text-title-lg">1</span>
                  <h3 className="font-display text-deep-navy text-title">Contact the nonprofit</h3>
                </div>
                <p className="font-body text-body-lg text-cool-grey leading-[1.65]">
                  Call or email the nonprofit's development office (fundraising team). Tell them you want to donate stock.
                </p>
                <p className="font-body text-small text-muted-cream/70 mt-3">
                  Not sure how to reach them? Look for their website link on their Daanaa page or call their main phone number.
                </p>
              </div>

              <div className="border-l-4 border-soft-gold pl-6">
                <div className="flex items-baseline gap-3 mb-3">
                  <span className="font-display text-deep-navy text-title-lg">2</span>
                  <h3 className="font-display text-deep-navy text-title">They'll give you brokerage details</h3>
                </div>
                <p className="font-body text-body-lg text-cool-grey leading-[1.65]">
                  The nonprofit will provide:
                </p>
                <ul className="font-body text-body text-cool-grey leading-[1.65] mt-3 space-y-2 ml-4">
                  <li>• Their brokerage account number</li>
                  <li>• The brokerage firm they use (e.g., Fidelity, Schwab)</li>
                  <li>• Any special instructions</li>
                </ul>
              </div>

              <div className="border-l-4 border-soft-gold pl-6">
                <div className="flex items-baseline gap-3 mb-3">
                  <span className="font-display text-deep-navy text-title-lg">3</span>
                  <h3 className="font-display text-deep-navy text-title">Transfer stock through your broker</h3>
                </div>
                <p className="font-body text-body-lg text-cool-grey leading-[1.65]">
                  You initiate the transfer from your own brokerage account (where you hold the stock).
                  Tell your broker you want to transfer shares to the nonprofit's brokerage account.
                </p>
                <p className="font-body text-small text-muted-cream/70 mt-3">
                  Your broker will handle the paperwork. The shares go directly from your account to theirs.
                </p>
              </div>

              <div className="border-l-4 border-soft-gold pl-6">
                <div className="flex items-baseline gap-3 mb-3">
                  <span className="font-display text-deep-navy text-title-lg">4</span>
                  <h3 className="font-display text-deep-navy text-title">Get a receipt and consult a tax pro</h3>
                </div>
                <p className="font-body text-body-lg text-cool-grey leading-[1.65]">
                  The nonprofit will send you a receipt for the donation.
                  Give this to your tax professional or tax software when you file.
                </p>
              </div>
            </div>
          </section>

          {/* Important notes */}
          <section className="mb-16 pt-12 border-t border-light-grey">
            <h2 className="font-display italic text-deep-navy text-title md:text-title-lg mb-6">Important to know</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {[
                {
                  title: 'Timing matters',
                  body: 'The stock must have been held for more than 1 year to get the tax benefit. Check with a tax pro if you are unsure.'
                },
                {
                  title: 'Not all stocks qualify',
                  body: 'Highly appreciated stock works best. Talk to your nonprofit about what they can accept.'
                },
                {
                  title: 'Tax deduction rules',
                  body: 'You can deduct up to 30% of your adjusted gross income. Over that, you can carry forward to next year.'
                },
                {
                  title: 'Get professional advice',
                  body: 'Tax treatment depends on your situation. Talk to a tax professional or CPA before transferring.'
                },
              ].map((item, i) => (
                <div key={i} className="bg-white border border-light-grey rounded-xl p-6">
                  <h3 className="font-display text-deep-navy text-lead mb-3">{item.title}</h3>
                  <p className="font-body text-small text-cool-grey leading-[1.65]">{item.body}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Tax information */}
          <section className="mb-16 pt-12 border-t border-light-grey">
            <h2 className="font-display italic text-deep-navy text-title md:text-title-lg mb-6">Tax guidance</h2>
            <div className="bg-soft-gold/10 border border-soft-gold/20 rounded-lg p-6">
              <p className="font-body text-body text-cool-grey leading-[1.65] mb-4">
                For details on tax treatment of appreciated asset donations, see:
              </p>
              <ul className="font-body text-body text-cool-grey leading-[1.65] space-y-2">
                <li>
                  <a href="https://www.irs.gov/publications/p526" target="_blank" rel="noopener noreferrer" className="text-link-gold hover:text-bright-gold">
                    IRS Publication 526 — Charitable Contributions
                  </a>
                </li>
                <li>
                  <a href="https://www.irs.gov/individuals/international-taxpayers/frequently-asked-questions-on-digital-asset-transactions" target="_blank" rel="noopener noreferrer" className="text-link-gold hover:text-bright-gold">
                    IRS guidance on appreciated assets
                  </a>
                </li>
              </ul>
              <p className="font-body text-caption text-muted-cream/70 mt-4 italic">
                This is educational information only, not tax advice. Consult a tax professional for your specific situation.
              </p>
            </div>
          </section>

          {/* Daanaa's role */}
          <section className="mb-16 pt-12 border-t border-light-grey">
            <div className="bg-soft-gold/10 border border-soft-gold/20 rounded-lg p-6">
              <h3 className="font-display text-deep-navy text-title-sm mb-3">How Daanaa works</h3>
              <p className="font-body text-body text-cool-grey leading-[1.65]">
                <strong>Daanaa does NOT process your stock transfer.</strong> We show you the nonprofit's contact information and help you find organizations.
                You work directly with the nonprofit and your broker. Your stock goes directly to them — not through Daanaa.
              </p>
              <p className="font-body text-small text-muted-cream/70 mt-3">
                This keeps us independent and keeps your gift direct.
              </p>
            </div>
          </section>

          {/* Next steps */}
          <section className="mb-16 pt-12 border-t border-light-grey">
            <h2 className="font-display italic text-deep-navy text-title md:text-title-lg mb-6">Ready to give?</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Link
                to="/directory"
                className="flex items-center justify-between px-6 py-5 bg-deep-navy rounded-xl hover:bg-navy-mid transition-colors group"
              >
                <div>
                  <p className="font-body text-label tracking-[0.08em] text-pale-gold uppercase mb-1">Browse causes</p>
                  <p className="font-display italic text-warm-cream text-title-sm">Find a nonprofit</p>
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
                  <p className="font-body text-label tracking-[0.08em] text-link-gold uppercase mb-1">Learn more</p>
                  <p className="font-display italic text-deep-navy text-title-sm">Sector data</p>
                </div>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2" className="shrink-0 group-hover:translate-x-1 transition-transform">
                  <polyline points="9 18 15 12 9 6" />
                </svg>
              </Link>
            </div>
          </section>

          {/* Questions */}
          <div className="text-center mb-10">
            <p className="font-body text-body text-cool-grey">
              Questions? <Link to="/feedback" className="text-link-gold hover:text-bright-gold font-semibold">Get in touch</Link>.
            </p>
          </div>

          <TrustNav />
        </div>
      </div>
    </div>
  )
}
