import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import TrustNav from '../components/TrustNav'

const SECTIONS = [
  {
    tag: 'Who we cover',
    title: 'Every active 501(c)(3) in America',
    body: [
      'Daanaa indexes every 501(c)(3) organization the IRS recognizes as active and eligible for tax deductible giving. We check each organization against the IRS automatic revocation list every month — if an organization has lost its tax exempt status, it does not appear in browse or search.',
      'Most platforms stop at a curated subset. We cover all 1.7 million. The words "active" and "tax deductible" are not marketing language — they are the filter we enforce in the database and verify continuously against federal records.',
    ],
    link: { to: '/legal', label: 'How we source and verify the data' },
  },
  {
    tag: 'Who we surface',
    title: 'Including the 97% that go unseen',
    body: [
      'Most giving platforms highlight the same few hundred well known organizations. The other 97% — small community groups, local mutual aid networks, neighborhood health clinics, regional arts organizations — are registered, active, and doing real work. They just lack the staff and budget to build a public profile.',
      'Daanaa treats every organization with equal dignity. A $40,000 food pantry gets the same care as a $40 million hospital foundation. Our hidden gems feature actively surfaces small organizations with strong public context precisely because they are the ones that benefit most from being found.',
    ],
    link: { to: '/directory', label: 'Browse the directory' },
  },
  {
    tag: 'How we present data',
    title: 'v6 context, not ratings',
    body: [
      'Daanaa does not rate, rank, endorse, or recommend organizations. v6 shows what public records tell us directly and what comparable organizations typically report when direct information is missing. We label the difference clearly; this is context, not a judgment.',
      'No organization can pay to improve its score. No partner can influence how an organization appears. The methodology is public, versioned, and derived entirely from IRS Form 990 filings. We publish it so anyone can check our work.',
    ],
    link: { to: '/methodology', label: 'Read the full methodology' },
  },
  {
    tag: 'The giving experience',
    title: 'Easy to give, easy to remember',
    body: [
      'Finding an organization should be the beginning, not the end. The Giving Wallet lets you save organizations you care about, log the time and money you\'ve given, and return to your list whenever you\'re ready — all without creating an account.',
      'We never process donations, hold donor funds, or issue tax receipts. Every gift goes directly to the nonprofit through their own page. Our role is to make that hand off frictionless and to give you a personal record of the giving that matters to you.',
    ],
    link: { to: '/wallet', label: 'Learn about the Giving Wallet' },
  },
  {
    tag: 'How we operate',
    title: 'Independent and evidence based',
    body: [
      'No organization can pay for placement, change its public context, or suppress how it appears on Daanaa. No partner or sponsor can influence what users see. Independence is structural — there is no mechanism in the platform for money to change how an organization ranks or appears.',
      'Every trust signal comes from public IRS data, NCCS financial summaries, or ProPublica 990 records. When we use AI to generate a mission summary, we label it clearly. When data is incomplete or stale, we say so. We do not present assumptions as facts.',
    ],
    links: [
      { to: '/methodology', label: 'How scoring works' },
      { to: '/legal', label: 'Data sources and attribution' },
    ],
  },
  {
    tag: 'How we benchmark',
    title: 'Equal dignity for every organization',
    body: [
      'A $200,000 community health clinic is never compared against a $2 billion hospital system. Daanaa benchmarks every organization within its true peer group: organizations with the comparable category, geography, size, and funding pattern. This means a small organization can be understood in context without being compared with a much larger organization.',
      'We built Daanaa for the organizations most people have never heard of. The lamp tier system is not a verdict — it reflects how much public data is available today. Any organization can raise its visibility by adding its mission, website, and financial records, and that path is always free.',
    ],
    link: { to: '/methodology#peer-financial-context', label: 'How peer groups work' },
  },
]

export default function About() {
  usePageMeta(
    'About Daanaa',
    'Daanaa is a public directory of every active 501(c)(3) in America — including the 97% that go unseen — organized with independent, evidence based financial context so giving is easy to understand, easy to record, and easy to return to.'
  )

  return (
    <div className="min-h-[100dvh]">
      {/* Hero */}
      <div className="bg-deep-navy pt-nav">
        <div className="max-w-[1120px] mx-auto px-6 md:px-12 pt-14 pb-14">
          <div className="flex items-center gap-2 mb-6">
            <Link to="/" className="font-body text-caption text-muted-cream hover:text-warm-cream transition-colors">Home</Link>
            <span className="text-muted-cream">/</span>
            <span className="font-body text-caption text-muted-cream">About</span>
          </div>

          <p className="font-body text-caption tracking-[0.1em] text-pale-gold uppercase mb-4">About Daanaa</p>

          {/* Canonical identity statement */}
          <p className="font-display italic text-warm-cream max-w-[820px] h2-display">
            Daanaa is a public directory of every active 501(c)(3) in America — including the 97% that go unseen — organized with financial context so giving is easy to understand, easy to record, and easy to return to.
          </p>

          {/* Positioning line */}
          <div className="mt-8 max-w-[680px] space-y-1.5">
            {[
              'Independent of paid influence.',
              'Evidence based on public IRS data.',
              'No ratings. Every organization benchmarked within its true peer group — never against a different type or size.',
              'Equal dignity for the small org doing extraordinary work as for the large one everyone has heard of.',
            ].map(line => (
              <p key={line} className="font-body text-body-lg text-muted-cream leading-[1.6]">{line}</p>
            ))}
          </div>

          <div className="mt-8 max-w-[760px] rounded-xl border border-soft-gold/20 bg-soft-gold/10 px-5 py-4">
            <p className="font-body text-body text-muted-cream leading-[1.7]">Daanaa is currently a self-funded public-interest initiative and a DBA of EcoMargins Consulting LLC, a for-profit entity. We are keeping overhead deliberately low while the concept is tested. Daanaa does not process donations or take a percentage of gifts. This structure does not represent Daanaa as a nonprofit or tax-exempt organization.</p>
          </div>
        </div>
      </div>

      {/* How we do it — six sections */}
      <div className="bg-warm-cream py-16 md:py-20">
        <div className="max-w-[1120px] mx-auto px-6 md:px-12">

          <h2 className="font-display italic text-deep-navy text-headline md:text-headline-lg mb-14">How we do it</h2>

          <div className="space-y-0">
            {SECTIONS.map((section, i) => (
              <div
                key={section.title}
                className={`grid grid-cols-1 md:grid-cols-[1fr_2fr] gap-8 md:gap-16 py-12 ${i < SECTIONS.length - 1 ? 'border-b border-light-grey' : ''}`}
              >
                {/* Left */}
                <div className="md:pt-1">
                  <p className="font-body text-label tracking-[0.1em] text-link-gold uppercase mb-2">{section.tag}</p>
                  <h3 className="font-display italic text-deep-navy text-title md:text-title-lg leading-[1.2]">{section.title}</h3>
                </div>

                {/* Right */}
                <div>
                  <div className="space-y-4">
                    {section.body.map((para, j) => (
                      <p key={j} className="font-body text-body-lg text-cool-grey leading-[1.7]">{para}</p>
                    ))}
                  </div>
                  <div className="mt-5 flex flex-wrap gap-5">
                    {'link' in section && section.link && (
                      <Link to={section.link.to} className="font-body text-small font-medium text-link-gold hover:text-bright-gold transition-colors">
                        {section.link.label} →
                      </Link>
                    )}
                    {'links' in section && section.links && section.links.map(l => (
                      <Link key={l.to} to={l.to} className="font-body text-small font-medium text-link-gold hover:text-bright-gold transition-colors">
                        {l.label} →
                      </Link>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* What we are / are not */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-16 pt-12 border-t border-light-grey">
            <div>
              <h3 className="font-display text-deep-navy text-title mb-5">What we are</h3>
              <ul className="space-y-3">
                {[
                  'A public directory of every active 501(c)(3)',
                  'An independent, evidence based financial context layer',
                  'A discovery platform for the 97% that go unseen',
                  'A giving record that stays on your device',
                ].map(item => (
                  <li key={item} className="flex items-start gap-3 font-body text-body-lg text-cool-grey">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2.5" className="shrink-0 mt-0.5">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                    {item}
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h3 className="font-display text-deep-navy text-title mb-5">What we are not</h3>
              <ul className="space-y-3">
                {[
                  'Not a rating agency',
                  'Not a donation processor',
                  'Not affiliated with the IRS or any government body',
                  'Not a nonprofit ranking platform',
                  'Not influenced by paid placement',
                ].map(item => (
                  <li key={item} className="flex items-start gap-3 font-body text-body-lg text-cool-grey">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#D1D5DB" strokeWidth="2.5" className="shrink-0 mt-0.5">
                      <line x1="5" y1="12" x2="19" y2="12" />
                    </svg>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Our commitments */}
          <div className="mt-16 pt-12 border-t border-light-grey">
            <h2 className="font-display italic text-deep-navy text-headline md:text-headline-lg mb-8">What we commit to</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {[
                {
                  title: 'No paid placement',
                  body: 'Organizations cannot pay to appear higher in search results or change how they appear. Visibility is based on publicly available information and transparent methodology, not advertising budgets.',
                },
                {
                  title: 'No control of donor funds',
                  body: 'Donations do not pass through Daanaa. We link to the organization\'s own official page. Anyone who gives deals with the nonprofit directly. We never hold, process, or transfer charitable funds.',
                },
                {
                  title: 'No sale of donor activity',
                  body: 'We do not build profiles based on giving behavior or encourage public displays of generosity. Giving is personal and should remain in the hands of the giver.',
                },
                {
                  title: 'Independence is structural',
                  body: 'No partner, sponsor, or outside relationship can influence verification outcomes, rankings, or trust indicators. There is no mechanism in the platform for money to change how an organization appears.',
                },
                {
                  title: 'Errors are corrected quickly',
                  body: 'Errors in our data, logic, or presentation are corrected openly and promptly. Accuracy is more important than protecting the appearance of the platform. Every org page has a visible corrections path.',
                },
                {
                  title: 'Privacy is structural',
                  body: 'Your giving history stays on your device by default. Signing in with Google is optional and enables backup across your devices. We use Plausible Analytics with no tracking cookies and no advertising profiles. No social sharing of giving activity is surfaced or encouraged.',
                },
              ].map(c => (
                <div key={c.title} className="bg-white border border-light-grey rounded-xl p-6">
                  <h3 className="font-display text-deep-navy text-title-sm mb-3">{c.title}</h3>
                  <p className="font-body text-body text-cool-grey leading-[1.65]">{c.body}</p>
                </div>
              ))}
            </div>
          </div>

          {/* How we use AI */}
          <div className="mt-14 pt-10 border-t border-light-grey grid grid-cols-1 md:grid-cols-[1fr_2fr] gap-8 md:gap-16">
            <div className="md:pt-1">
              <p className="font-body text-label tracking-[0.1em] text-link-gold uppercase mb-2">A note on AI</p>
              <h2 className="font-display italic text-deep-navy text-title md:text-title-lg leading-[1.2]">How we use AI responsibly</h2>
            </div>
            <div className="space-y-4">
              <p className="font-body text-body-lg text-cool-grey leading-[1.7]">
                When a nonprofit hasn't filed a mission statement with the IRS, we use AI to read the available filing data and write a starting-point description — the way a research volunteer would read an annual report and draft a summary paragraph. We label every AI-generated description clearly. Any organization can replace it at any time with their own words. You should verify anything important directly with the organization.
              </p>
              <p className="font-body text-body-lg text-cool-grey leading-[1.7]">
                AI never touches financial data, scores, or peer benchmarks. Those come directly from IRS records. AI fills gaps in the written record — it does not shape the numbers. We run our AI locally on our own servers, not through third party cloud services, which means organization data stays within the platform. AI outputs are reviewable, correctable, and clearly labeled wherever they appear.
              </p>
            </div>
          </div>

          {/* CTAs */}
          <div className="mt-14 pt-10 border-t border-light-grey grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Link
              to="/directory"
              className="flex items-center justify-between px-6 py-5 bg-deep-navy rounded-xl hover:bg-navy-mid transition-colors group"
            >
              <div>
                <p className="font-body text-label tracking-[0.08em] text-pale-gold uppercase mb-1">Start here</p>
                <p className="font-display italic text-warm-cream text-title-sm">Browse the directory</p>
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
                <p className="font-body text-label tracking-[0.08em] text-link-gold uppercase mb-1">Go deeper</p>
                <p className="font-display italic text-deep-navy text-title-sm">Sector data and research</p>
              </div>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2" className="shrink-0 group-hover:translate-x-1 transition-transform">
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </Link>
          </div>

          <div className="mt-10 text-center">
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
