import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import TrustNav from '../components/TrustNav'

export default function GivingViaRecurringPage() {
  usePageMeta(
    'Give on a Schedule',
    'Set up a recurring gift directly with the nonprofit you want to support.'
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
            Give a little, on a schedule you choose.
          </p>

          <p className="mt-8 max-w-[680px] font-body text-body-lg text-muted-cream leading-[1.6]">
            A small amount each month is easier to sustain than one large gift, and it gives the nonprofit something they can plan around. You set it up with them directly.
          </p>
        </div>
      </div>

      {/* Main content */}
      <div className="bg-warm-cream py-16 md:py-20">
        <div className="max-w-[1120px] mx-auto px-6 md:px-12">

          {/* How to give */}
          <section className="mb-16">
            <h2 className="font-display italic text-deep-navy text-headline md:text-headline-lg mb-10">How to set up a recurring gift</h2>

            <div className="space-y-8">
              <div className="border-l-4 border-soft-gold pl-6">
                <div className="flex items-baseline gap-3 mb-3">
                  <span className="font-display text-deep-navy text-title-lg">1</span>
                  <h3 className="font-display text-deep-navy text-title">Pick the nonprofit</h3>
                </div>
                <p className="font-body text-body-lg text-cool-grey leading-[1.65]">
                  Find the organization on Daanaa and open its page. If they have a verified donate link, it takes you to their own giving page.
                </p>
              </div>

              <div className="border-l-4 border-soft-gold pl-6">
                <div className="flex items-baseline gap-3 mb-3">
                  <span className="font-display text-deep-navy text-title-lg">2</span>
                  <h3 className="font-display text-deep-navy text-title">Choose monthly on their form</h3>
                </div>
                <p className="font-body text-body-lg text-cool-grey leading-[1.65]">
                  Most nonprofit donation forms have a monthly or recurring option. Pick the amount and the frequency that works for you.
                </p>
                <p className="font-body text-body text-cool-grey leading-[1.65] mt-3">
                  If they do not offer recurring giving online, you can often set up an automatic payment through your own bank instead, using the nonprofit's name and mailing address.
                </p>
              </div>

              <div className="border-l-4 border-soft-gold pl-6">
                <div className="flex items-baseline gap-3 mb-3">
                  <span className="font-display text-deep-navy text-title-lg">3</span>
                  <h3 className="font-display text-deep-navy text-title">Start small</h3>
                </div>
                <p className="font-body text-body-lg text-cool-grey leading-[1.65]">
                  A recurring gift you can sustain matters more than a large one you cancel in three months. Many nonprofits see meaningful support at modest monthly amounts.
                </p>
              </div>

              <div className="border-l-4 border-soft-gold pl-6">
                <div className="flex items-baseline gap-3 mb-3">
                  <span className="font-display text-deep-navy text-title-lg">4</span>
                  <h3 className="font-display text-deep-navy text-title">Keep records for each payment</h3>
                </div>
                <p className="font-body text-body-lg text-cool-grey leading-[1.65]">
                  Each payment is treated as its own contribution, not one gift spread over the year.
                </p>
                <p className="font-body text-small text-muted-cream/70 mt-3">
                  <strong>Tax note:</strong> A payment counts toward the tax year in which it actually clears, not the year you set up the schedule. Any single payment of 250 dollars or more needs a written acknowledgment from the nonprofit. This is not tax advice. Consult a tax professional.{' '}
                  <a href="https://www.irs.gov/publications/p526" target="_blank" rel="noopener noreferrer" className="text-link-gold hover:text-bright-gold">IRS Publication 526</a>
                  {' '}and{' '}
                  <a href="https://www.irs.gov/charities-non-profits/substantiating-charitable-contributions" target="_blank" rel="noopener noreferrer" className="text-link-gold hover:text-bright-gold">IRS guidance on substantiating contributions</a>
                </p>
              </div>
            </div>
          </section>

          {/* Why recurring */}
          <section className="mb-16 pt-12 border-t border-light-grey">
            <h2 className="font-display italic text-deep-navy text-title md:text-title-lg mb-6">Why give on a schedule?</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {[
                {
                  title: 'Easier to sustain',
                  body: 'A modest monthly amount fits a budget in a way a single large gift often does not.'
                },
                {
                  title: 'Predictable for them',
                  body: 'Steady support lets a nonprofit plan its work instead of guessing at next quarter.'
                },
                {
                  title: 'One decision',
                  body: 'You choose once. You are not deciding again every month.'
                },
                {
                  title: 'You stay in control',
                  body: 'You can change or cancel any time, directly with the nonprofit or your bank.'
                },
              ].map((item, i) => (
                <div key={i} className="bg-white border border-light-grey rounded-xl p-6">
                  <h3 className="font-display text-deep-navy text-lead mb-3">{item.title}</h3>
                  <p className="font-body text-small text-cool-grey leading-[1.65]">{item.body}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Before you commit */}
          <section className="mb-16 pt-12 border-t border-light-grey">
            <h2 className="font-display italic text-deep-navy text-title md:text-title-lg mb-6">Worth checking first</h2>
            <ul className="font-body text-body-lg text-cool-grey leading-[1.75] space-y-3 ml-4">
              <li>• How to cancel or change the amount later, and who to contact</li>
              <li>• Whether the nonprofit gives you a single annual summary or a receipt per payment</li>
              <li>• Whether their form charges a processing fee, and whether you can cover it</li>
              <li>• That the organization is the one you meant, since names can be similar</li>
            </ul>
          </section>

          {/* Important note */}
          <section className="mb-16 pt-12 border-t border-light-grey">
            <div className="bg-soft-gold/10 border border-soft-gold/20 rounded-lg p-6">
              <h3 className="font-display text-deep-navy text-title-sm mb-3">Important: how Daanaa works</h3>
              <p className="font-body text-body text-cool-grey leading-[1.65]">
                <strong>Daanaa does NOT process your recurring gift.</strong> The schedule lives with the nonprofit or your bank. We never see it, never hold your money, and never charge your card.
              </p>
              <p className="font-body text-small text-muted-cream/70 mt-3">
                Your giving activity stays private. We do not publish it and we do not use it to contact you.
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
                to="/giving-via-workplace"
                className="flex items-center justify-between px-6 py-5 bg-white border border-light-grey rounded-xl hover:border-soft-gold transition-colors group"
              >
                <div>
                  <p className="font-body text-label tracking-[0.08em] text-link-gold uppercase mb-1">Another way</p>
                  <p className="font-display italic text-deep-navy text-title-sm">Workplace giving</p>
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
