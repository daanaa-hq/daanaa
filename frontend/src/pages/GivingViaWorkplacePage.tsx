import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import TrustNav from '../components/TrustNav'

export default function GivingViaWorkplacePage() {
  usePageMeta(
    'Give Through Your Workplace',
    'Give through payroll deduction or ask your employer about matching gifts.'
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
            Give straight from your paycheck.
          </p>

          <p className="mt-8 max-w-[680px] font-body text-body-lg text-muted-cream leading-[1.6]">
            Many employers let you give through payroll deduction. Some also match what you give. Both happen through your employer, not through Daanaa.
          </p>
        </div>
      </div>

      {/* Main content */}
      <div className="bg-warm-cream py-16 md:py-20">
        <div className="max-w-[1120px] mx-auto px-6 md:px-12">

          {/* How to give */}
          <section className="mb-16">
            <h2 className="font-display italic text-deep-navy text-headline md:text-headline-lg mb-10">How workplace giving works</h2>

            <div className="space-y-8">
              <div className="border-l-4 border-soft-gold pl-6">
                <div className="flex items-baseline gap-3 mb-3">
                  <span className="font-display text-deep-navy text-title-lg">1</span>
                  <h3 className="font-display text-deep-navy text-title">Ask your employer what they offer</h3>
                </div>
                <p className="font-body text-body-lg text-cool-grey leading-[1.65]">
                  Start with your HR team or benefits portal. Ask about:
                </p>
                <ul className="font-body text-body text-cool-grey leading-[1.65] mt-3 space-y-2 ml-4">
                  <li>• Payroll deduction (a set amount from each paycheck)</li>
                  <li>• Matching gifts (your employer gives alongside you)</li>
                  <li>• The giving platform they use, if any</li>
                </ul>
                <p className="font-body text-small text-muted-cream/70 mt-3">
                  Employer matching is voluntary. Every employer sets its own policy, and many offer nothing at all. There is no law requiring it.
                </p>
              </div>

              <div className="border-l-4 border-soft-gold pl-6">
                <div className="flex items-baseline gap-3 mb-3">
                  <span className="font-display text-deep-navy text-title-lg">2</span>
                  <h3 className="font-display text-deep-navy text-title">Find the nonprofit and its EIN</h3>
                </div>
                <p className="font-body text-body-lg text-cool-grey leading-[1.65]">
                  Workplace giving platforms look up nonprofits by EIN, the number the IRS assigns to every registered nonprofit. Every organization on Daanaa shows its EIN on its page.
                </p>
                <p className="font-body text-body text-cool-grey leading-[1.65] mt-3">
                  Copy the EIN, then search for it in your employer's giving portal.
                </p>
              </div>

              <div className="border-l-4 border-soft-gold pl-6">
                <div className="flex items-baseline gap-3 mb-3">
                  <span className="font-display text-deep-navy text-title-lg">3</span>
                  <h3 className="font-display text-deep-navy text-title">Set your amount</h3>
                </div>
                <p className="font-body text-body-lg text-cool-grey leading-[1.65]">
                  Choose how much comes out of each paycheck. Your employer handles the withholding and sends the money to the nonprofit.
                </p>
                <p className="font-body text-small text-muted-cream/70 mt-3">
                  <strong>Tax note:</strong> Payroll contributions are deductible in the tax year the withholding happens, not the year you sign up. Each paycheck counts as a separate contribution. Consult a tax professional.{' '}
                  <a href="https://www.irs.gov/publications/p526" target="_blank" rel="noopener noreferrer" className="text-link-gold hover:text-bright-gold">IRS Publication 526</a>
                </p>
              </div>

              <div className="border-l-4 border-soft-gold pl-6">
                <div className="flex items-baseline gap-3 mb-3">
                  <span className="font-display text-deep-navy text-title-lg">4</span>
                  <h3 className="font-display text-deep-navy text-title">Keep your pay stubs</h3>
                </div>
                <p className="font-body text-body-lg text-cool-grey leading-[1.65]">
                  Pay stubs showing the deduction are your record. For any single gift of 250 dollars or more, the nonprofit also needs to send you a written acknowledgment.
                </p>
                <p className="font-body text-small text-muted-cream/70 mt-3">
                  If your employer matches, that match is the employer's own contribution. It is recorded separately and is not part of your deduction.
                </p>
              </div>
            </div>
          </section>

          {/* Why workplace giving */}
          <section className="mb-16 pt-12 border-t border-light-grey">
            <h2 className="font-display italic text-deep-navy text-title md:text-title-lg mb-6">Why give through work?</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {[
                {
                  title: 'Automatic',
                  body: 'Set it once. It comes out of each paycheck without you thinking about it.'
                },
                {
                  title: 'Spread out',
                  body: 'Smaller amounts each pay period instead of one large gift.'
                },
                {
                  title: 'Employer may add to it',
                  body: 'Some employers match employee gifts. Ask yours whether they do, and what the limits are.'
                },
                {
                  title: 'Records handled',
                  body: 'Your pay stubs document every contribution for you.'
                },
              ].map((item, i) => (
                <div key={i} className="bg-white border border-light-grey rounded-xl p-6">
                  <h3 className="font-display text-deep-navy text-lead mb-3">{item.title}</h3>
                  <p className="font-body text-small text-cool-grey leading-[1.65]">{item.body}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Common platforms */}
          <section className="mb-16 pt-12 border-t border-light-grey">
            <h2 className="font-display italic text-deep-navy text-title md:text-title-lg mb-6">Platforms employers commonly use</h2>
            <p className="font-body text-body text-cool-grey leading-[1.65] mb-6">
              If your employer uses one of these, you will sign in through your company, not through Daanaa. We have no relationship with any of them and receive nothing from them.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {[
                { name: 'Benevity', body: 'Used by many large employers for payroll giving and matching.' },
                { name: 'CyberGrants', body: 'Corporate giving and matching gift administration.' },
                { name: 'YourCause', body: 'Employee giving and volunteering programs.' },
                { name: 'America\'s Charities', body: 'Workplace giving campaigns for employers of many sizes.' },
              ].map((item, i) => (
                <div key={i} className="bg-white border border-light-grey rounded-xl p-6">
                  <h3 className="font-display text-deep-navy text-lead mb-3">{item.name}</h3>
                  <p className="font-body text-small text-cool-grey leading-[1.65]">{item.body}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Important note */}
          <section className="mb-16 pt-12 border-t border-light-grey">
            <div className="bg-soft-gold/10 border border-soft-gold/20 rounded-lg p-6">
              <h3 className="font-display text-deep-navy text-title-sm mb-3">Important: how Daanaa works</h3>
              <p className="font-body text-body text-cool-grey leading-[1.65]">
                <strong>Daanaa does NOT process your workplace gift.</strong> We help you find the nonprofit and its EIN. Everything after that happens between you, your employer, and the nonprofit.
              </p>
              <p className="font-body text-small text-muted-cream/70 mt-3">
                We are not paid by any giving platform and we do not receive any share of what you give.
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
                to="/giving-via-recurring"
                className="flex items-center justify-between px-6 py-5 bg-white border border-light-grey rounded-xl hover:border-soft-gold transition-colors group"
              >
                <div>
                  <p className="font-body text-label tracking-[0.08em] text-link-gold uppercase mb-1">Another way</p>
                  <p className="font-display italic text-deep-navy text-title-sm">Recurring gifts</p>
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
