import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import TrustNav from '../components/TrustNav'

export default function GivingViaDafPage() {
  usePageMeta(
    'Give via Donor-Advised Fund',
    'Step-by-step guide to giving to nonprofits through your DAF account using Daanaa.'
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
            Give to causes you care about using your Donor-Advised Fund.
          </p>

          <p className="mt-8 max-w-[680px] font-body text-[15px] text-muted-cream leading-[1.6]">
            A Donor-Advised Fund (DAF) lets you claim your tax deduction upfront, then recommend grants to charities over time. Here's how to use your DAF to give to nonprofits on Daanaa.
          </p>
        </div>
      </div>

      {/* Main content */}
      <div className="bg-warm-cream py-16 md:py-20">
        <div className="max-w-[1120px] mx-auto px-6 md:px-12">

          {/* Prerequisites */}
          <section className="mb-16">
            <h2 className="font-display italic text-deep-navy text-[26px] md:text-[32px] mb-6">Do you already have a DAF?</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white border border-light-grey rounded-xl p-6">
                <h3 className="font-display text-deep-navy text-[18px] mb-3">Yes, I have a DAF account</h3>
                <p className="font-body text-[14px] text-cool-grey leading-[1.65] mb-4">
                  Skip ahead to "Step 1" below to find and grant funds to your chosen nonprofit.
                </p>
                <p className="font-body text-[12px] text-cool-grey/70">
                  You already have an account with a DAF sponsor like Fidelity Charitable, DAFgiving360 (Schwab), Vanguard Charitable, or a community foundation.
                </p>
              </div>
              <div className="bg-white border border-light-grey rounded-xl p-6">
                <h3 className="font-display text-deep-navy text-[18px] mb-3">No, I need to open one first</h3>
                <p className="font-body text-[14px] text-cool-grey leading-[1.65] mb-4">
                  Visit a major DAF sponsor to open and fund your account.
                </p>
                <div className="space-y-2 font-body text-[12px] text-cool-grey/70">
                  <p>• <a href="https://www.fidelitycharitable.org/" target="_blank" rel="noopener noreferrer" className="text-link-gold hover:text-bright-gold">Fidelity Charitable</a></p>
                  <p>• <a href="https://www.dafgiving360.org/" target="_blank" rel="noopener noreferrer" className="text-link-gold hover:text-bright-gold">DAFgiving360 (Schwab)</a></p>
                  <p>• <a href="https://www.vanguardcharitable.org/" target="_blank" rel="noopener noreferrer" className="text-link-gold hover:text-bright-gold">Vanguard Charitable</a></p>
                </div>
              </div>
            </div>
          </section>

          {/* Steps */}
          <section className="mb-16">
            <h2 className="font-display italic text-deep-navy text-[26px] md:text-[32px] mb-10">How to grant funds to a nonprofit</h2>

            <div className="space-y-8">
              {/* Step 1 */}
              <div className="border-l-4 border-soft-gold pl-6">
                <div className="flex items-baseline gap-3 mb-3">
                  <span className="font-display text-deep-navy text-[24px]">1</span>
                  <h3 className="font-display text-deep-navy text-[20px]">Search for the nonprofit</h3>
                </div>
                <p className="font-body text-[15px] text-cool-grey leading-[1.65] mb-4">
                  Log into your DAF account dashboard. Use your provider's charity search tool or enter the nonprofit's name or EIN (Federal Employer Identification Number).
                </p>
                <div className="bg-soft-gold/10 border border-soft-gold/20 rounded-lg p-4 mb-4">
                  <p className="font-body text-[13px] text-deep-navy font-medium mb-2">💡 Tip: Use the EIN for accuracy</p>
                  <p className="font-body text-[13px] text-cool-grey">
                    Each nonprofit on Daanaa has an EIN listed under "How to give" on their detail page. Using the EIN ensures your grant reaches the exact organization you intend, especially if the nonprofit name is common.
                  </p>
                </div>
                <p className="font-body text-[13px] text-muted-cream/70">
                  Most major DAF providers (Fidelity, DAFgiving360, Vanguard) index all active 501(c)(3) nonprofits, so you should find organizations on Daanaa in their databases.
                </p>
              </div>

              {/* Step 2 */}
              <div className="border-l-4 border-soft-gold pl-6">
                <div className="flex items-baseline gap-3 mb-3">
                  <span className="font-display text-deep-navy text-[24px]">2</span>
                  <h3 className="font-display text-deep-navy text-[20px]">Verify the charity details</h3>
                </div>
                <p className="font-body text-[15px] text-cool-grey leading-[1.65] mb-4">
                  Confirm you have the correct organization:
                </p>
                <ul className="space-y-2 font-body text-[14px] text-cool-grey leading-[1.65] mb-4">
                  <li>• Legal organization name (as filed with the IRS)</li>
                  <li>• EIN (9-digit Federal Employer Identification Number)</li>
                  <li>• City and state of operation</li>
                  <li>• 501(c)(3) status is current</li>
                </ul>
                <p className="font-body text-[13px] text-muted-cream/70">
                  The nonprofit's Daanaa page shows this information under "How to give" and in the organization header.
                </p>
              </div>

              {/* Step 3 */}
              <div className="border-l-4 border-soft-gold pl-6">
                <div className="flex items-baseline gap-3 mb-3">
                  <span className="font-display text-deep-navy text-[24px]">3</span>
                  <h3 className="font-display text-deep-navy text-[20px]">Specify grant amount and purpose</h3>
                </div>
                <p className="font-body text-[15px] text-cool-grey leading-[1.65] mb-4">
                  Enter the grant amount (usually a minimum of $50). If you want to direct your gift toward a specific program, project, or location, most DAF providers let you add a memo or note about how you'd like the grant used.
                </p>
                <div className="bg-soft-gold/10 border border-soft-gold/20 rounded-lg p-4">
                  <p className="font-body text-[13px] text-deep-navy font-medium mb-2">📋 Pro tip: Add a purpose note</p>
                  <p className="font-body text-[13px] text-cool-grey">
                    If the nonprofit has multiple programs, mention which one your grant is for. This helps the organization direct your gift where you care most about the impact.
                  </p>
                </div>
              </div>

              {/* Step 4 */}
              <div className="border-l-4 border-soft-gold pl-6">
                <div className="flex items-baseline gap-3 mb-3">
                  <span className="font-display text-deep-navy text-[24px]">4</span>
                  <h3 className="font-display text-deep-navy text-[20px]">Choose visibility (optional)</h3>
                </div>
                <p className="font-body text-[15px] text-cool-grey leading-[1.65] mb-4">
                  Most DAF providers let you decide whether your name appears on the grant letter. You can give anonymously to protect your privacy and avoid future solicitations.
                </p>
                <p className="font-body text-[13px] text-muted-cream/70">
                  Daanaa does not sell or share donor giving data, and we never use giving history for outreach or profiling.
                </p>
              </div>

              {/* Step 5 */}
              <div className="border-l-4 border-soft-gold pl-6">
                <div className="flex items-baseline gap-3 mb-3">
                  <span className="font-display text-deep-navy text-[24px]">5</span>
                  <h3 className="font-display text-deep-navy text-[20px]">Submit and confirm</h3>
                </div>
                <p className="font-body text-[15px] text-cool-grey leading-[1.65]">
                  Click submit. Your DAF provider will verify the nonprofit's 501(c)(3) status, then distribute the grant by check or electronic transfer. You'll receive a grant letter for your records.
                </p>
              </div>
            </div>
          </section>

          {/* Key facts */}
          <section className="mb-16">
            <h2 className="font-display italic text-deep-navy text-[20px] md:text-[24px] mb-6">Important: How DAF grants work</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {[
                {
                  title: 'One-time tax deduction',
                  body: 'You claim your tax deduction when you fund your DAF account, not when you make grants. Once you donate to your DAF, the tax benefit is locked in.'
                },
                {
                  title: 'Charities only',
                  body: 'DAF grants can only go to verified 501(c)(3) public charities. They cannot support political campaigns, private individuals, or non-charitable organizations.'
                },
                {
                  title: 'No personal benefits',
                  body: 'You cannot use a DAF to purchase tickets, auction items, or goods/services in exchange. Grants must be purely charitable.'
                },
                {
                  title: 'No pledge satisfaction',
                  body: 'In most cases, DAF grants cannot be used to satisfy a legally binding personal pledge you made previously.'
                },
              ].map((item, i) => (
                <div key={i} className="bg-white border border-light-grey rounded-xl p-6">
                  <h3 className="font-display text-deep-navy text-[16px] mb-3">{item.title}</h3>
                  <p className="font-body text-[13px] text-cool-grey leading-[1.65]">{item.body}</p>
                </div>
              ))}
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
              Have questions? <Link to="/feedback" className="text-link-gold hover:text-bright-gold font-semibold">Get in touch</Link>.
            </p>
          </div>

          <TrustNav />
        </div>
      </div>
    </div>
  )
}
