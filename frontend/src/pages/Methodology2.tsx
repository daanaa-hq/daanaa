import { Link } from 'react-router-dom'
import { useState } from 'react'
import TrustNav from '../components/TrustNav'
import { usePageMeta } from '../hooks/usePageMeta'
import { useJsonLd, faqPageSchema } from '../hooks/useJsonLd'

// Table of contents — drives the sticky sidebar and the anchor IDs below.
const TOC = [
  { id: 'overview', label: 'What Daanaa is' },
  { id: 'public-data-sources', label: 'Where the data comes from' },
  { id: 'peer-financial-context', label: 'Peer financial context' },
  { id: 'not-measured', label: 'What we don’t measure' },
  { id: 'data-limits', label: 'Data limits' },
  { id: 'financial-context', label: 'Financial context' },
  { id: 'hidden-gems', label: 'Orgs you may not have heard of' },
  { id: 'two-layers', label: 'What the organization controls' },
  { id: 'updates', label: 'How data stays current' },
  { id: 'faq', label: 'Frequently asked questions' },
] as const

const FAQS = [
  {
    q: 'What is Daanaa?',
    a: 'Daanaa is an independent nonprofit discovery platform that helps people discover causes and organizations using public information presented with context, stewardship, and respect.',
  },
  {
    q: 'Is Daanaa a rating agency?',
    a: 'No. Daanaa does not rate, rank, endorse, or recommend nonprofits. We organize public information to add context to giving decisions, which is different from rating.',
  },
  {
    q: 'What happens when an organization\'s finances are missing?',
    a: 'v6 may show financial patterns reported by a reasonable peer group—organizations comparable by category, geography, scale, and funding pattern. That is reference context, not an estimate of the organization\'s own finances. If the peer evidence is too weak, we show limited context instead.',
  },
  {
    q: 'What were Lamp Tiers?',
    a: 'Lamp Tiers were a visibility indicator based on public information completeness, shown on every organization page through 8 August 2026. They were retired because peer financial context (above) covers more organizations and says something more useful. They were never a rating.',
  },
  {
    q: 'Does Daanaa process donations?',
    a: 'No. When available, Daanaa links to an organization\'s own official website. Donations never pass through our platform, and we never collect donor payment information.',
  },
  {
    q: 'Is Daanaa affiliated with the IRS?',
    a: 'No. Daanaa.org is independent and is not affiliated with the IRS, the federal government, or any nonprofit rating agency.',
  },
  {
    q: 'Can organizations request corrections?',
    a: 'Yes. Organizations and visitors can report data issues through our feedback form. We correct errors quickly and disclose corrections publicly.',
  },
]

function Section({ id, label, title, children }: { id: string; label: string; title: string; children: React.ReactNode }) {
  return (
    <section id={id} className="py-10 md:py-14 border-b border-light-grey last:border-0 scroll-mt-anchor">
      <div className="max-w-[760px]">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-6 h-px bg-soft-gold/50" />
          <span className="font-body text-label font-medium tracking-[0.10em] text-soft-gold uppercase">{label}</span>
        </div>
        <h2 className="font-display italic text-deep-navy leading-[1.05] tracking-[-0.01em]" >
          {title}
        </h2>
        <div className="mt-6 space-y-4 font-body text-lead text-cool-grey leading-[1.7]">
          {children}
        </div>
      </div>
    </section>
  )
}

function Callout({ children }: { children: React.ReactNode }) {
  return (
    <div className="mt-6 p-5 rounded-xl bg-soft-gold/10 border border-soft-gold/20">
      <p className="font-body text-body-lg text-deep-navy leading-[1.6]">{children}</p>
    </div>
  )
}


export default function Methodology() {
  usePageMeta(
    'Methodology — How Daanaa Works',
    'How Daanaa organizes public nonprofit information: data sources, Peer Financial Context, Lamp Tiers, what we don’t measure, data limits, and answers to common questions.'
  )
  useJsonLd(faqPageSchema(FAQS.map(f => ({ question: f.q, answer: f.a }))))

  const [openFaq, setOpenFaq] = useState<number | null>(0)

  return (
    <div className="min-h-[100dvh]">
      {/* Header */}
      <div className="bg-deep-navy pt-nav">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12 pt-8 pb-10 md:pt-12 md:pb-16">
          <div className="flex items-center gap-2 mb-6">
            <Link to="/" className="font-body text-caption tracking-[0.02em] text-muted-cream hover:text-warm-cream transition-colors">Home</Link>
            <span className="text-muted-cream">/</span>
            <span className="font-body text-caption text-muted-cream">Methodology</span>
          </div>
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-10 md:gap-16">
            <div className="max-w-[640px]">
              <h1 className="font-display italic text-warm-cream leading-[1.05] tracking-[-0.01em]" style={{ fontSize: 'clamp(32px, 5vw, 64px)' }}>
                How Daanaa Works
              </h1>
              <p className="mt-4 font-body text-title-sm leading-[1.6] text-muted-cream">
                We do not turn public records into a rating. We place each organization alongside relevant peers, explain what the evidence supports, and let you decide. This page explains how.
              </p>
            </div>
            <div className="shrink-0 hidden md:flex justify-end">
              <img src="/logo.png" alt="" aria-hidden="true" className="w-48 h-48 lg:w-56 lg:h-56 object-contain drop-shadow-[0_12px_48px_rgba(201,169,110,0.22)]" />
            </div>
          </div>
        </div>
      </div>

      {/* Content + sticky TOC */}
      <div className="bg-warm-cream">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12 flex gap-12">

          {/* Sticky table of contents (desktop) */}
          <aside className="hidden lg:block shrink-0 w-56 pt-14">
            <div className="sticky top-[88px]">
              <p className="font-body text-label font-semibold tracking-[0.08em] text-cool-grey uppercase mb-4">On this page</p>
              <nav aria-label="On this page" className="space-y-2.5">
                {TOC.map(item => (
                  <a
                    key={item.id}
                    href={`#${item.id}`}
                    className="block font-body text-small text-cool-grey hover:text-soft-gold transition-colors leading-snug"
                  >
                    {item.label}
                  </a>
                ))}
              </nav>
            </div>
          </aside>

          {/* Main column */}
          <div className="min-w-0 flex-1">

            {/* Critical disclaimer */}
            <div className="mt-12 mb-2 p-6 bg-white border-2 border-deep-navy/10 rounded-2xl max-w-[760px]">
              <p className="font-body text-lead font-semibold text-deep-navy leading-[1.6]">
                Peer Financial Context is not a rating, endorsement, impact score, or recommendation. Daanaa does not rank human worth — we organize public information so people can give more thoughtfully.
              </p>
            </div>

            <Section id="overview" label="Our foundation" title="What Daanaa is, and what it isn't">
              <p>
                Daanaa is a public directory of every active 501(c)(3) in America — independent of paid influence, not affiliated with the IRS or any rating agency, and not a donation processor.{' '}
                <Link to="/about" className="text-soft-gold hover:text-bright-gold font-medium">How we approach this →</Link>
              </p>
              <Callout>
                v6 is the public peer-context system on every organization page. It shows what public records tell us directly and, when direct data is missing, what similar organizations typically report. It is context for a giving decision—not a rating, endorsement, impact score, or recommendation.
              </Callout>
            </Section>

            <Section id="public-data-sources" label="Data sources" title="Where the data comes from">
              <p>Every organization page is built from multiple layers of public data:</p>
              <div className="mt-2 space-y-3">
                {[
                  { source: 'IRS nonprofit registration list (Business Master File)', what: 'Legal name, category, state, and nonprofit status. Updated by the IRS continuously.' },
                  { source: 'Annual financial reports (Form 990, 990-EZ, 990-N)', what: 'Reports nonprofits file with the IRS each year. Source of mission statements, program descriptions, leadership, and detailed financials.' },
                  { source: 'Government published financial summaries (IRS SOI / NCCS)', what: 'IRS Statistics of Income and National Center for Charitable Statistics data covering 2019–2024. Revenue and expense figures for about 530,000 organizations.' },
                  { source: 'ProPublica Nonprofit Explorer (a public interest newsroom)', what: 'Financial data for about 42,000 organizations with verified 2022–2024 figures.' },
                ].map(({ source, what }) => (
                  <div key={source} className="flex gap-4 p-4 bg-white rounded-lg border border-light-grey">
                    <div className="shrink-0 w-2 h-2 mt-2 rounded-full bg-soft-gold" />
                    <div>
                      <p className="font-body text-body font-semibold text-deep-navy">{source}</p>
                      <p className="font-body text-body text-cool-grey mt-1">{what}</p>
                    </div>
                  </div>
                ))}
              </div>
              <p className="mt-4">
                Every page shows when the data is from and where it came from, like "2023 · Source: IRS", so you always know how recent the information is.
              </p>
            </Section>

            <Section id="peer-financial-context" label="The financial picture" title="How peer financial context works">
              <p>
                v6 does not grade an organization or judge its work. It presents a small set of financial facts and peer patterns so donors can ask better questions. The result never claims to describe more than the public evidence supports.
              </p>
              <p>
                We use two dimensions to find organizations that are truly comparable:
              </p>
              <div className="mt-2 space-y-3">
                <div className="p-4 bg-white rounded-lg border border-light-grey">
                  <p className="font-body text-body font-semibold text-deep-navy">Funding model</p>
                  <p className="font-body text-body text-cool-grey mt-1">
                    We use the available category, geography, revenue information, and funding pattern to build a comparable peer group. A food bank should not be compared with a hospital system simply because both are nonprofits. When a field is inferred, we label it.
                  </p>
                </div>
                <div className="p-4 bg-white rounded-lg border border-light-grey">
                  <p className="font-body text-body font-semibold text-deep-navy">Revenue band</p>
                  <p className="font-body text-body text-cool-grey mt-1">
                    Revenue is used when it is available to avoid comparing organizations of very different scale. We do not invent revenue when it is missing. In that case, v6 shows a broader or descriptive context and says what is not known.
                  </p>
                </div>
              </div>
              <p className="mt-4">
                Where public filings support it, v6 shows a reserve-related metric and the range reported by the peer group. The page identifies the source years, peer group, and uncertainty. A peer pattern is not a prediction of what an organization has or will do.
              </p>

              <div className="mt-6">
                <p className="font-body text-body font-semibold text-deep-navy mb-1">What the context means</p>
                <p className="font-body text-small text-cool-grey mb-3 max-w-[640px]">
                  Direct context describes the organization's reported metric. Inferred context describes similar organizations, not this organization's actual finances. Limited context means we do not have enough public information for a numeric comparison. None of these is a judgment about mission or effectiveness.
                </p>
                <div className="grid gap-3 sm:grid-cols-3">
                  {[
                    { label: "Reported", detail: "The organization filing supports the figure shown." },
                    { label: "Peer reference", detail: "Comparable organizations provide a useful reference when its own figure is missing." },
                    { label: "Limited", detail: "The evidence is too thin for a responsible numeric comparison." },
                  ].map(({ label, detail }) => (
                    <div key={label} className="rounded-lg bg-warm-cream p-3">
                      <p className="font-body text-small font-semibold text-deep-navy">{label}</p>
                      <p className="mt-1 font-body text-caption text-cool-grey leading-[1.5]">{detail}</p>
                    </div>
                  ))}
                </div>
              </div>

              <p className="mt-5 font-body text-body-lg text-cool-grey leading-[1.7]">
                On an organization page, look for the data status: reported, inferred, or limited. Reported means the record supports a direct comparison. Inferred means the peer pattern is being used because the organization-specific field is missing. Limited means we stop short of a numeric comparison.
              </p>
              <p className="mt-3 font-body text-body-lg text-cool-grey leading-[1.7]">
                A lower reserve figure is not a verdict. Organizations may spend available resources on current work, operate seasonally, or have incomplete public records. Use this context alongside the organization's mission, community knowledge, and information from the organization itself.
              </p>
              <p className="mt-3 font-body text-body-lg text-cool-grey leading-[1.7]">
                Filing years can lag the current year. Read the source year shown on the page, and contact the organization when you need current information.
              </p>
            </Section>

            <Section id="not-measured" label="Honest limits" title="What Daanaa does not measure">
              <p>Daanaa deliberately does not measure or estimate:</p>
              <ul className="mt-2 space-y-2.5 max-w-[640px]">
                {[
                  'Impact or effectiveness of programs',
                  'Executive compensation or overhead ratios',
                  'Program delivery or service quality',
                  'Community need or local priority',
                  'Organizational leadership or governance',
                  'Staff expertise or program outcomes',
                ].map(item => (
                  <li key={item} className="flex items-start gap-3 font-body text-body-lg text-cool-grey">
                    <span className="text-soft-gold mt-1.5 w-1.5 h-1.5 rounded-full bg-soft-gold shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
              <p className="mt-4">
                These are important decisions you should make based on your own research, not assumptions from peer context.
              </p>
            </Section>

            <Section id="data-limits" label="Honest limits" title="Data limits">
              <p>Public nonprofit data has real limits, and we'd rather name them than hide them:</p>
              <ul className="mt-2 space-y-2.5 max-w-[640px]">
                {[
                  'Reporting delays: Form 990 filings are often 1–2 years behind current operations.',
                  'Coverage gaps: not all nonprofits file annually; small organizations may file simplified forms.',
                  'Classification challenges: NTEE categorization is imperfect and assigned by filing organizations.',
                  'Missing data: some organizations don\'t file or have incomplete financial records.',
                ].map(item => (
                  <li key={item} className="flex items-start gap-3 font-body text-body-lg text-cool-grey">
                    <span className="text-soft-gold mt-1.5 w-1.5 h-1.5 rounded-full bg-soft-gold shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
            </Section>

              <Section id="financial-context" label="Financial context" title="Financial context: how much peer comparison we can offer">
                <p>Where the public record supports it, a page shows financial context: how an organization compares with peers doing similar work at a similar scale in a similar place. It is context, never a rating, and never our opinion of the organization or its work.</p>
                <p className="mt-4">How closely we can match peers depends on what the public record contains, so we say which kind of comparison we were able to make:</p>
                <div className="mt-4 space-y-3">
                  {[
                    { label: "Full context", what: "Compared with organizations of similar type, size, and region." },
                    { label: "Regional context", what: "Compared within a broader regional peer group." },
                    { label: "Broad category", what: "Compared across a wider category when a closer peer group was too small to be meaningful." },
                    { label: "Category only", what: "We can describe the kind of work, but the public record does not yet support a peer comparison." },
                  ].map(({ label, what }) => (
                    <div key={label} className="flex gap-4 p-4 bg-white rounded-lg border border-light-grey items-start">
                      <div className="shrink-0 pt-0.5 min-w-[7.5rem]">
                        <span className="font-body text-small font-semibold text-deep-navy">{label}</span>
                      </div>
                      <p className="font-body text-body text-cool-grey leading-[1.6]">{what}</p>
                    </div>
                  ))}
                </div>
                <p className="mt-4 font-body text-small text-cool-grey">Each page also shows how confident we are in that comparison, and how many peers it is based on.</p>
                <Callout>A broader comparison reflects what the public record contains, not organizational character, importance, or mission quality. Smaller and newer organizations often have thinner records; that is a gap in the data, not a judgment about the work.</Callout>
                <p className="mt-6 font-body text-small text-cool-grey">Previously this section described a four-level &ldquo;lamp tier&rdquo; visibility mark shown on every page. Those marks were retired on 8 August 2026 because they rested on assumptions that did not hold, and because peer financial context covers more organizations and says something more useful. Research published before that date describes the retired system.</p>
              </Section>

            <Section id="hidden-gems" label="Orgs you may not have heard of" title="Organizations you may not have heard of">
              <p>Daanaa surfaces smaller and less visible organizations so donors can discover more local and community-rooted work.</p>
              <p className="mt-4">Hidden-gem discovery uses public information, not editorial judgment or paid promotion:</p>
              <div className="mt-4 space-y-3">
                {[
                  { label: "Small and easy to miss", detail: "A lower public profile or smaller revenue footprint helps surface organizations donors may not otherwise encounter." },
                  { label: "Public context available", detail: "The public record provides enough information to show useful, clearly labeled context." },
                  { label: "Mission information", detail: "There is a readable description of what the organization does, from public records or the organization itself." },
                ].map(({ label, detail }) => (
                  <div key={label} className="flex gap-4 p-4 bg-white rounded-lg border border-light-grey">
                    <div className="shrink-0 w-2 h-2 mt-2 rounded-full bg-soft-gold" />
                    <div><p className="font-body text-body font-semibold text-deep-navy">{label}</p><p className="font-body text-body text-cool-grey mt-1">{detail}</p></div>
                  </div>
                ))}
              </div>
              <Callout>Hidden-gem status is a discovery aid, not an endorsement. It never changes how an organization is ranked, described, or treated because of payment or partnership.</Callout>
            </Section>

            <Section id="two-layers" label="Two layer model" title="What the organization controls">
              <p>Every page has two distinct layers:</p>
              <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-5 bg-white rounded-xl border border-light-grey">
                  <p className="font-body text-caption tracking-[0.06em] text-soft-gold uppercase font-medium mb-2">Daanaa's data</p>
                  <p className="font-body text-small text-cool-grey leading-[1.6]">
                    Sourced from IRS public records. Objective, fact checked, timestamped. Organizations cannot edit this layer.
                  </p>
                  <ul className="mt-3 space-y-1 font-body text-small text-cool-grey">
                    {['Legal name', 'Nonprofit category', 'Revenue from IRS filings', 'Peer financial context', 'Data source & year'].map(i => (
                      <li key={i} className="flex items-center gap-2">
                        <span className="w-1 h-1 rounded-full bg-cool-grey shrink-0" />{i}
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="p-5 bg-white rounded-xl border-2 border-dashed border-soft-gold/30">
                  <p className="font-body text-caption tracking-[0.06em] text-soft-gold uppercase font-medium mb-2">Organization's data</p>
                  <p className="font-body text-small text-cool-grey leading-[1.6]">
                    Added directly by the organization. Clearly labeled as self reported. Claim your page to update this information.
                  </p>
                  <ul className="mt-3 space-y-1 font-body text-small text-cool-grey">
                    {['Mission statement', 'Program descriptions', 'Leadership team', 'Photos & annual reports', 'Impact metrics'].map(i => (
                      <li key={i} className="flex items-center gap-2">
                        <span className="w-1 h-1 rounded-full bg-soft-gold/50 shrink-0" />{i}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
              <p className="mt-6">
                This separation is fundamental to trust. You always know whether you're reading data from the IRS or an organization's own description of itself. Both are valuable, for different reasons.
              </p>
            </Section>

            <Section id="updates" label="Updates" title="How data stays current">
              <p>We run automated updates on a regular schedule:</p>
              <div className="mt-2 space-y-2">
                {[
                  { freq: 'Monthly', what: 'ProPublica data for organizations with new financial reports' },
                  { freq: 'Monthly', what: 'IRS financial data update for newly published years' },
                  { freq: 'Monthly', what: 'IRS tax-exempt status check against the federal auto-revocation list' },
                  { freq: 'Ongoing', what: 'v6 peer context recalculated after underlying data updates' },
                ].map(({ freq, what }, i) => (
                  <div key={`${freq}-${i}`} className="flex gap-4 items-start">
                    <span className="shrink-0 font-body text-small font-semibold text-soft-gold w-20">{freq}</span>
                    <span className="font-body text-body text-cool-grey">{what}</span>
                  </div>
                ))}
              </div>
              <p className="mt-4">
                Every organization's detail page shows when the data is from and where it came from, so you're never guessing how old the information is.
              </p>
            </Section>

            <Section id="faq" label="Questions" title="Frequently asked questions">
              <div className="space-y-3 max-w-[760px]">
                {FAQS.map((faq, i) => (
                  <div key={i} className="border border-light-grey rounded-lg overflow-hidden bg-white">
                    <button
                      onClick={() => setOpenFaq(openFaq === i ? null : i)}
                      className="w-full px-5 py-4 flex items-center justify-between hover:bg-warm-cream/40 transition-colors text-left"
                      aria-expanded={openFaq === i}
                    >
                      <span className="font-body text-body-lg font-semibold text-deep-navy">{faq.q}</span>
                      <svg className={`w-5 h-5 shrink-0 text-soft-gold transition-transform ${openFaq === i ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <polyline points="6 9 12 15 18 9"></polyline>
                      </svg>
                    </button>
                    {openFaq === i && (
                      <div className="px-5 py-3 border-t border-light-grey bg-warm-cream/20">
                        <p className="font-body text-body text-cool-grey leading-[1.6]">{faq.a}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </Section>

            <TrustNav />

            {/* CTA */}
            <div className="py-12">
              <div className="bg-deep-navy rounded-2xl p-8 md:p-12 text-center">
                <h3 className="font-display italic text-warm-cream text-headline leading-[1.1]">Questions or corrections?</h3>
                <p className="mt-3 font-body text-lead text-muted-cream max-w-[480px] mx-auto leading-[1.6]">
                  If you represent a listed organization and want to update or claim your page, or if you spot an error in our data, we want to hear from you. We correct errors quickly and disclose corrections publicly.
                </p>
                <Link
                  to="/feedback"
                  className="mt-6 inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-soft-gold text-deep-navy font-body text-body font-semibold hover:bg-bright-gold transition-colors"
                >
                  Contact us
                </Link>
                <div className="mt-6 flex flex-wrap items-center justify-center gap-6">
                  <Link to="/about" className="font-body text-small text-muted-cream hover:text-warm-cream transition-colors">
                    About Daanaa →
                  </Link>
                  <Link to="/research" className="font-body text-small text-muted-cream hover:text-warm-cream transition-colors">
                    Research & data →
                  </Link>
                  <Link to="/directory" className="font-body text-small text-muted-cream hover:text-warm-cream transition-colors">
                    Browse the directory →
                  </Link>
                  <Link to="/legal" className="font-body text-small text-muted-cream hover:text-warm-cream transition-colors">
                    Data attribution →
                  </Link>
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  )
}
