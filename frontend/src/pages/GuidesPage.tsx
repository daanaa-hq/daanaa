import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'

function GuideCard({ number, title, description, children }: {
  number: string
  title: string
  description: string
  children: React.ReactNode
}) {
  return (
    <div className="py-12 md:py-16 border-b border-light-grey last:border-0">
      <div className="flex items-start gap-6 max-w-[760px]">
        <span className="shrink-0 font-cinzel text-[13px] font-semibold text-soft-gold/50 tracking-[0.12em] pt-1">{number}</span>
        <div className="flex-1">
          <h2 className="font-display italic text-deep-navy leading-[1.05] tracking-[-0.01em]" style={{ fontSize: 'clamp(22px, 3vw, 36px)' }}>
            {title}
          </h2>
          <p className="mt-3 font-body text-[16px] text-cool-grey leading-[1.7]">{description}</p>
          <div className="mt-6 space-y-4 font-body text-[15px] text-cool-grey leading-[1.7]">
            {children}
          </div>
        </div>
      </div>
    </div>
  )
}

function Tip({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex gap-3 p-4 bg-soft-gold/8 border border-soft-gold/20 rounded-xl">
      <span className="shrink-0 w-1.5 h-1.5 rounded-full bg-soft-gold mt-2" />
      <p className="font-body text-[14px] text-deep-navy leading-[1.6]">{children}</p>
    </div>
  )
}

export default function GuidesPage() {
  usePageMeta('Giving Guides', 'Practical guides for informed charitable giving — how to read a MERIT score, document your donations, and research a nonprofit before you give.')

  return (
    <div className="min-h-[100dvh]">
      {/* Header */}
      <div className="bg-deep-navy pt-[72px]">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12 pt-12 pb-16">
          <div className="flex items-center gap-2 mb-6">
            <Link to="/" className="font-body text-[12px] text-muted-cream hover:text-warm-cream transition-colors">Home</Link>
            <span className="text-muted-cream/50">/</span>
            <span className="font-body text-[12px] text-muted-cream">Giving Guides</span>
          </div>
          <h1 className="font-display italic text-warm-cream leading-[1.05] tracking-[-0.01em]" style={{ fontSize: 'clamp(32px, 5vw, 64px)' }}>
            Giving Guides
          </h1>
          <p className="mt-4 font-body text-[18px] leading-[1.6] text-muted-cream max-w-[580px]">
            Practical guidance for donors who want to give with intention — not anxiety.
          </p>
        </div>
      </div>

      {/* Content */}
      <div className="bg-warm-cream">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12">

          <GuideCard
            number="01"
            title="How to read a MERIT profile"
            description="A MERIT profile has two independent signals: the score and the tier. Understanding both takes about 60 seconds."
          >
            <p>
              The <strong className="text-deep-navy font-semibold">MERIT score</strong> is a peer percentile — a number from 0 to 100 that shows how this organization compares financially to similar nonprofits doing similar work at similar scale. A score of 80 means it outperforms 80% of its peers. This is not a grade on a curve — it is a ranking within a carefully constructed peer group defined by NTEE subcategory and revenue band.
            </p>
            <p>
              The <strong className="text-deep-navy font-semibold">trust tier</strong> (Beacon → Spark) reflects how much public data backs the profile today. A Beacon has a current 990 on file, a mission statement, an active website, and a top-quartile peer score. A Spark is an IRS-registered nonprofit with little financial detail yet in public records. The tier is a transparency signal, not a quality verdict.
            </p>
            <Tip>
              A high MERIT score in a Spark tier means: financially strong relative to peers, but limited public data. That combination often describes a well-run small organization that hasn't filed a full 990 (revenue under $50,000 — they file a 990-N postcard instead).
            </Tip>
            <p>
              Each profile also shows a <strong className="text-deep-navy font-semibold">data vintage</strong> — the fiscal year and source of the financial figures. A "FY 2022 · IRS" badge means the revenue figure is from the organization's 2022 tax return. Always check the vintage before making a large gift.
            </p>
          </GuideCard>

          <GuideCard
            number="02"
            title="Documenting your donations for tax purposes"
            description="The IRS has clear rules about charitable contribution documentation. Here's what you actually need — and when you need it."
          >
            <p>
              For any cash gift under <strong className="text-deep-navy font-semibold">$250</strong>, a bank statement, credit card statement, or cancelled check is the only documentation the IRS requires. You do not need a letter from the organization.
            </p>
            <p>
              For gifts of <strong className="text-deep-navy font-semibold">$250 or more</strong>, you must have a written acknowledgment from the organization by the time you file your taxes. The letter must state: the amount given, the date, whether you received any goods or services in return, and if so, the fair market value of those goods. No letter = no deduction, regardless of your bank statement.
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-[13px] font-body mt-2">
                <thead>
                  <tr className="border-b border-light-grey">
                    <th className="text-left py-2.5 pr-6 text-cool-grey font-medium">Gift amount</th>
                    <th className="text-left py-2.5 pr-6 text-cool-grey font-medium">Documentation required</th>
                    <th className="text-left py-2.5 text-cool-grey font-medium">Who provides it</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-light-grey">
                  {[
                    { amount: 'Under $250', doc: 'Bank or card statement', who: 'Your bank' },
                    { amount: '$250 – $499', doc: 'Written acknowledgment letter', who: 'The nonprofit' },
                    { amount: '$500 – $4,999', doc: 'Acknowledgment + IRS Form 8283', who: 'Nonprofit + you' },
                    { amount: '$5,000+', doc: 'Qualified appraisal required (non-cash gifts)', who: 'Qualified appraiser' },
                  ].map(({ amount, doc, who }) => (
                    <tr key={amount}>
                      <td className="py-2.5 pr-6 text-deep-navy font-medium">{amount}</td>
                      <td className="py-2.5 pr-6 text-cool-grey">{doc}</td>
                      <td className="py-2.5 text-cool-grey">{who}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Tip>
              MERIT's Giving Wallet logs each donation with date, org, EIN, and amount — the same fields an accountant or tax preparer needs. Export to CSV at year-end and hand it directly to whoever prepares your taxes.
            </Tip>
            <p>
              MERIT does not process payments or issue acknowledgment letters. Those come directly from the organization you give to. If you give online through the organization's own site, they will typically email a receipt that qualifies as the written acknowledgment.
            </p>
          </GuideCard>

          <GuideCard
            number="03"
            title="Researching a nonprofit before you give"
            description="Five things worth checking before making a meaningful gift — all findable from a MERIT profile."
          >
            <p><strong className="text-deep-navy font-semibold">1. Verify tax-exempt status.</strong> Every organization on MERIT is a current IRS-recognized 501(c)(3). If an organization is soliciting donations and isn't on MERIT, search the <a href="https://apps.irs.gov/app/eos/" target="_blank" rel="noopener noreferrer" className="text-soft-gold hover:text-bright-gold transition-colors">IRS Tax Exempt Organization Search</a> to confirm status before giving.</p>
            <p><strong className="text-deep-navy font-semibold">2. Check the fiscal year of the revenue figure.</strong> A 990 filed in 2024 typically covers fiscal year 2022 or 2023. Revenue figures that are 2–3 years old can be misleading if an organization has grown or shrunk significantly since then.</p>
            <p><strong className="text-deep-navy font-semibold">3. Look at the peer score in context.</strong> A score of 55 in the "Special Education" subcategory for a $200K/year organization tells you more than a score of 55 with no peer context. MERIT always shows the peer group — check it.</p>
            <p><strong className="text-deep-navy font-semibold">4. Read the mission statement.</strong> MERIT shows mission text from IRS 990 filings when available. This is what the organization told the federal government its purpose is — not its marketing copy.</p>
            <p><strong className="text-deep-navy font-semibold">5. Look for a current website.</strong> A Lantern or Beacon tier confirms an active website is in public records. If you can't find one, call the organization directly before writing a large check.</p>
            <Tip>
              For gifts over $1,000, spend 10 minutes on the organization's actual 990 filing — available on ProPublica Nonprofit Explorer. Look at Part IX (Statement of Functional Expenses) to see how much goes to program services vs. management vs. fundraising.
            </Tip>
          </GuideCard>

          <GuideCard
            number="04"
            title="Year-end giving checklist"
            description="The last days of December are the busiest for nonprofits and the most rushed for donors. A short checklist prevents mistakes."
          >
            <div className="space-y-3">
              {[
                { check: 'Confirm the organization is still IRS-recognized', detail: 'Status can change. Search MERIT or the IRS EOS tool before finalizing a gift.' },
                { check: 'Verify your gift will be completed by December 31', detail: 'Online gifts by card are deductible in the year charged. Checks are deductible when mailed, not when cashed — mail with tracking.' },
                { check: 'Save your confirmation email or bank record', detail: 'For gifts under $250, this is your documentation. File it with your tax documents before you need it.' },
                { check: 'Request an acknowledgment letter for gifts of $250+', detail: 'Some organizations send automatically; others require a request. Ask before year-end, not in April.' },
                { check: 'Log gifts to your MERIT Giving Wallet', detail: 'One place, all gifts, all years. Export to CSV when tax time comes.' },
                { check: 'Check if your employer matches charitable gifts', detail: 'Many employers match at 1:1 or 2:1. Submit matching requests before the employer\'s cutoff, which is often earlier than December 31.' },
              ].map(({ check, detail }) => (
                <div key={check} className="flex gap-4 p-4 bg-white rounded-xl border border-light-grey">
                  <div className="shrink-0 w-5 h-5 rounded-full border-2 border-soft-gold/50 mt-0.5" />
                  <div>
                    <p className="font-body text-[14px] font-semibold text-deep-navy">{check}</p>
                    <p className="font-body text-[13px] text-cool-grey mt-1 leading-[1.6]">{detail}</p>
                  </div>
                </div>
              ))}
            </div>
          </GuideCard>

          {/* CTA */}
          <div className="py-12">
            <div className="bg-deep-navy rounded-2xl p-8 md:p-12 flex flex-col md:flex-row items-start md:items-center gap-8 justify-between">
              <div>
                <h3 className="font-display italic text-warm-cream text-[26px] leading-[1.1]">Track every gift you make</h3>
                <p className="mt-2 font-body text-[15px] text-muted-cream max-w-[420px] leading-[1.6]">
                  Your Giving Wallet logs donations privately on your device — no account, no tracking, exportable at tax time.
                </p>
              </div>
              <div className="flex flex-col sm:flex-row gap-3 shrink-0">
                <Link to="/wallet" className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-soft-gold text-deep-navy font-body text-[14px] font-semibold hover:bg-bright-gold transition-colors whitespace-nowrap">
                  Open Giving Wallet
                </Link>
                <Link to="/faq" className="inline-flex items-center gap-2 px-6 py-3 rounded-xl border border-white/20 text-muted-cream font-body text-[14px] hover:border-white/40 transition-colors whitespace-nowrap">
                  Read the FAQ
                </Link>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}
