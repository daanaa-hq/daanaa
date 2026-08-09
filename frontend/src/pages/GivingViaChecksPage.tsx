import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import TrustNav from '../components/TrustNav'

export default function GivingViaChecksPage() {
  usePageMeta(
    'Give by Check',
    'Send a physical check directly to the nonprofit you want to support.'
  )

  return (
    <div className="min-h-[100dvh]">
      {/* Hero */}
      <div className="bg-deep-navy pt-nav">
        <div className="max-w-[1120px] mx-auto px-6 md:px-12 pt-14 pb-14">
          <div className="flex items-center gap-2 mb-6">
            <Link to="/" className="font-body text-caption text-muted-cream hover:text-warm-cream transition-colors">Home</Link>
            <span className="text-muted-cream">/</span>
            <span className="font-body text-caption text-muted-cream">Giving Guide</span>
          </div>

          <p className="font-body text-caption tracking-[0.1em] text-pale-gold uppercase mb-4">Giving Guide</p>

          <p className="font-display italic text-warm-cream max-w-[820px] h2-display">
            Send a check directly to the nonprofit.
          </p>

          <p className="mt-8 max-w-[680px] font-body text-body-lg text-muted-cream leading-[1.6]">
            A physical check is a simple, direct way to give. Your check goes straight to the nonprofit. You decide the amount. Done.
          </p>
        </div>
      </div>

      {/* Main content */}
      <div className="bg-warm-cream py-16 md:py-20">
        <div className="max-w-[1120px] mx-auto px-6 md:px-12">

          {/* How to give */}
          <section className="mb-16">
            <h2 className="font-display italic text-deep-navy text-headline md:text-headline-lg mb-10">How to give by check</h2>

            <div className="space-y-8">
              <div className="border-l-4 border-soft-gold pl-6">
                <div className="flex items-baseline gap-3 mb-3">
                  <span className="font-display text-deep-navy text-title-lg">1</span>
                  <h3 className="font-display text-deep-navy text-title">Find the nonprofit's address</h3>
                </div>
                <p className="font-body text-body-lg text-cool-grey leading-[1.65]">
                  Every nonprofit on Daanaa has a mailing address. On their page, look for the "How to give" section. You'll see:
                </p>
                <ul className="font-body text-body text-cool-grey leading-[1.65] mt-3 space-y-2 ml-4">
                  <li>• Mailing address</li>
                  <li>• Organization name (exactly as they want it on checks)</li>
                  <li>• Optional: phone number to call and confirm</li>
                </ul>
              </div>

              <div className="border-l-4 border-soft-gold pl-6">
                <div className="flex items-baseline gap-3 mb-3">
                  <span className="font-display text-deep-navy text-title-lg">2</span>
                  <h3 className="font-display text-deep-navy text-title">Write your check</h3>
                </div>
                <p className="font-body text-body-lg text-cool-grey leading-[1.65]">
                  Fill out a check:
                </p>
                <ul className="font-body text-body text-cool-grey leading-[1.65] mt-3 space-y-2 ml-4">
                  <li>• Payable to: [Organization name, exactly as listed]</li>
                  <li>• Amount: whatever you choose to give</li>
                  <li>• Include your address (so they can send a receipt)</li>
                  <li>• Optional: memo line = "Daanaa" or the specific program you want to support</li>
                </ul>
              </div>

              <div className="border-l-4 border-soft-gold pl-6">
                <div className="flex items-baseline gap-3 mb-3">
                  <span className="font-display text-deep-navy text-title-lg">3</span>
                  <h3 className="font-display text-deep-navy text-title">Mail it</h3>
                </div>
                <p className="font-body text-body-lg text-cool-grey leading-[1.65]">
                  Mail your check to the address on the nonprofit's Daanaa page.
                  No middlemen. No fees. Your money goes directly to them.
                </p>
              </div>

              <div className="border-l-4 border-soft-gold pl-6">
                <div className="flex items-baseline gap-3 mb-3">
                  <span className="font-display text-deep-navy text-title-lg">4</span>
                  <h3 className="font-display text-deep-navy text-title">Keep your records</h3>
                </div>
                <p className="font-body text-body-lg text-cool-grey leading-[1.65]">
                  The nonprofit will send you a receipt. Keep it for your records (for taxes, if you itemize deductions).
                </p>
                <p className="font-body text-small text-muted-cream/70 mt-3">
                  <strong>Tax note:</strong> Donations to 501(c)(3) nonprofits may be tax-deductible if you itemize. Consult a tax professional.
                </p>
              </div>
            </div>
          </section>

          {/* Why checks */}
          <section className="mb-16 pt-12 border-t border-light-grey">
            <h2 className="font-display italic text-deep-navy text-title md:text-title-lg mb-6">Why give by check?</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {[
                {
                  title: 'No fees',
                  body: 'No transaction costs. Your entire gift goes to the nonprofit.'
                },
                {
                  title: 'Direct',
                  body: 'Mail straight to them. No middlemen, no payment processor, no Daanaa in the middle.'
                },
                {
                  title: 'Simple',
                  body: 'No account needed. No credit card. Just your checkbook.'
                },
                {
                  title: 'Preferred by many',
                  body: 'Some nonprofits prefer checks because of lower fees than credit card processing.'
                },
              ].map((item, i) => (
                <div key={i} className="bg-white border border-light-grey rounded-xl p-6">
                  <h3 className="font-display text-deep-navy text-lead mb-3">{item.title}</h3>
                  <p className="font-body text-small text-cool-grey leading-[1.65]">{item.body}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Important note */}
          <section className="mb-16 pt-12 border-t border-light-grey">
            <div className="bg-soft-gold/10 border border-soft-gold/20 rounded-lg p-6">
              <h3 className="font-display text-deep-navy text-title-sm mb-3">Important: How Daanaa works</h3>
              <p className="font-body text-body text-cool-grey leading-[1.65]">
                <strong>Daanaa does NOT process your check.</strong> We show you the nonprofit's mailing address and help you find organizations.
                That's all. Your check goes directly to them, not through Daanaa, not through any payment processor.
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
