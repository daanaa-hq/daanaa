import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'

const SECTIONS = [
  {
    tag: 'Who we cover',
    title: 'Every active 501(c)(3) in America',
    body: [
      'Daanaa indexes every 501(c)(3) organization that the IRS recognizes as active and eligible for tax-deductible giving. That means we check each organization against the IRS automatic revocation list every month — if an organization has lost its tax-exempt status, it does not appear in browse or search.',
      'Most platforms stop at a curated subset. We cover all 1.7 million. The words "active" and "tax-deductible" are not marketing language — they are the filter we enforce in the database and verify continuously against federal records.',
    ],
    link: { to: '/legal#data-sources', label: 'How we source and verify the data' },
  },
  {
    tag: 'Who we surface',
    title: 'Including the 97% that go unseen',
    body: [
      'Most giving platforms highlight the same few hundred well-known organizations. The other 97% — small community groups, local mutual aid networks, neighborhood health clinics, regional arts organizations — are registered, active, and doing real work. They just lack the staff and budget to build a public profile.',
      'Daanaa treats every organization with equal dignity. A $40,000 food pantry gets the same care as a $40 million hospital foundation. Our hidden gems feature actively surfaces small organizations with strong financial health precisely because they are the ones that benefit most from being found.',
    ],
    link: { to: '/directory', label: 'Browse the directory' },
  },
  {
    tag: 'How we present data',
    title: 'Financial context, not ratings',
    body: [
      'Daanaa does not rate, rank, endorse, or recommend organizations. We show financial context: where an organization\'s reserves stand relative to genuinely similar organizations — same funding model, similar revenue size, same peer group. A score of 75 means stronger reserves than 75% of its peers. That is a fact derived from public IRS data, not a judgment.',
      'No organization can pay to improve its score. No partner can influence how an organization appears. The methodology is public, versioned, and derived entirely from IRS Form 990 filings. We publish it so anyone can check our work.',
    ],
    link: { to: '/methodology', label: 'Read the full methodology' },
  },
  {
    tag: 'The giving experience',
    title: 'Easy to give, easy to remember',
    body: [
      'Finding an organization should be the beginning, not the end. Daanaa\'s Giving Wallet lets you save organizations you care about, log the time and money you\'ve given, and return to your list whenever you\'re ready to give again — all without creating an account.',
      'We never process donations, hold donor funds, or issue tax receipts. Every gift goes directly to the nonprofit through their own page. Our role is to make that hand-off clear and to give you a personal record of the giving that matters to you.',
    ],
    link: { to: '/wallet', label: 'Learn about the Giving Wallet' },
  },
  {
    tag: 'How we operate',
    title: 'Independent and evidence-based',
    body: [
      'No organization can pay for placement, boost its score, or suppress how it appears on Daanaa. No partner or sponsor can influence what users see. Independence is structural — there is no mechanism in the platform for money to change how an organization ranks or appears.',
      'Every trust signal we show comes from public IRS data, NCCS financial summaries, or ProPublica 990 records. When we use AI to generate a mission summary, we label it clearly. When data is incomplete or stale, we say so. We do not present assumptions as facts.',
    ],
    links: [
      { to: '/principles', label: 'Our founding principles' },
      { to: '/legal', label: 'Data sources and attribution' },
    ],
  },
  {
    tag: 'How we benchmark',
    title: 'Equal dignity for every organization',
    body: [
      'A $200,000 community health clinic is never compared against a $2 billion hospital system. Daanaa benchmarks every organization within its true peer group: organizations with the same funding model and a similar revenue band. This means a small organization can show strong financial health for its size, and a large one can show a need for support.',
      'We built Daanaa for the organizations most people have never heard of. The lamp tier system is not a verdict — it reflects how much public data is available today. Any organization can raise its visibility by adding its mission, website, and financial records, and that path is always free.',
    ],
    link: { to: '/methodology#peer-financial-context', label: 'How peer groups work' },
  },
]

export default function Approach() {
  usePageMeta(
    'Our Approach — Daanaa',
    'How Daanaa covers every active 501(c)(3) in America — including the 97% that go unseen — with independent, evidence-based financial context so giving is easy to understand, easy to record, and easy to return to.'
  )

  return (
    <div className="min-h-[100dvh]">
      {/* Hero */}
      <div className="bg-deep-navy pt-[72px]">
        <div className="max-w-[1120px] mx-auto px-6 md:px-12 pt-14 pb-14">
          <div className="flex items-center gap-2 mb-6">
            <Link to="/" className="font-body text-[12px] text-muted-cream hover:text-warm-cream transition-colors">Home</Link>
            <span className="text-muted-cream">/</span>
            <span className="font-body text-[12px] text-muted-cream">Our approach</span>
          </div>

          <p className="font-body text-[12px] tracking-[0.1em] text-pale-gold uppercase mb-4">How Daanaa works</p>

          {/* Canonical identity statement */}
          <p className="font-display italic text-warm-cream leading-[1.1] tracking-[-0.01em] max-w-[820px]">
            Daanaa is a public directory of every active 501(c)(3) in America — including the 97% that go unseen — organized with financial context so giving is easy to understand, easy to record, and easy to return to.
          </p>

          {/* Positioning line */}
          <div className="mt-8 max-w-[680px] space-y-1">
            {[
              'Independent of paid influence.',
              'Evidence-based from public IRS data.',
              'No ratings. Every organization benchmarked within its true peer group — never against a different type or size.',
              'Equal dignity for the small org doing extraordinary work as for the large one everyone has heard of.',
            ].map(line => (
              <p key={line} className="font-body text-[15px] text-muted-cream leading-[1.6]">{line}</p>
            ))}
          </div>
        </div>
      </div>

      {/* Sections */}
      <div className="bg-warm-cream py-16 md:py-20">
        <div className="max-w-[1120px] mx-auto px-6 md:px-12">

          <div className="space-y-16">
            {SECTIONS.map((section, i) => (
              <div key={section.title} className={`grid grid-cols-1 md:grid-cols-[1fr_2fr] gap-8 md:gap-16 pb-16 ${i < SECTIONS.length - 1 ? 'border-b border-light-grey' : ''}`}>
                {/* Left: tag + title */}
                <div className="md:pt-1">
                  <p className="font-body text-[11px] tracking-[0.1em] text-soft-gold uppercase mb-2">{section.tag}</p>
                  <h2 className="font-display italic text-deep-navy text-[22px] md:text-[26px] leading-[1.15]">{section.title}</h2>
                </div>

                {/* Right: body + links */}
                <div>
                  <div className="space-y-4">
                    {section.body.map((para, j) => (
                      <p key={j} className="font-body text-[15px] text-cool-grey leading-[1.7]">{para}</p>
                    ))}
                  </div>

                  <div className="mt-5 flex flex-wrap gap-4">
                    {'link' in section && section.link && (
                      <Link
                        to={section.link.to}
                        className="font-body text-[13px] font-medium text-soft-gold hover:text-bright-gold transition-colors"
                      >
                        {section.link.label} →
                      </Link>
                    )}
                    {'links' in section && section.links && section.links.map(l => (
                      <Link
                        key={l.to}
                        to={l.to}
                        className="font-body text-[13px] font-medium text-soft-gold hover:text-bright-gold transition-colors"
                      >
                        {l.label} →
                      </Link>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* CTAs */}
          <div className="mt-16 pt-12 border-t border-light-grey grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Link
              to="/directory"
              className="flex items-center justify-between px-6 py-5 bg-deep-navy rounded-xl hover:bg-navy-mid transition-colors group"
            >
              <div>
                <p className="font-body text-[12px] tracking-[0.08em] text-pale-gold uppercase mb-1">Start here</p>
                <p className="font-display italic text-warm-cream text-[18px]">Browse the directory</p>
              </div>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2" className="shrink-0 group-hover:translate-x-1 transition-transform">
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </Link>

            <Link
              to="/principles"
              className="flex items-center justify-between px-6 py-5 bg-white border border-light-grey rounded-xl hover:border-soft-gold transition-colors group"
            >
              <div>
                <p className="font-body text-[12px] tracking-[0.08em] text-soft-gold uppercase mb-1">Go deeper</p>
                <p className="font-display italic text-deep-navy text-[18px]">Our founding principles</p>
              </div>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2" className="shrink-0 group-hover:translate-x-1 transition-transform">
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </Link>
          </div>

        </div>
      </div>
    </div>
  )
}
