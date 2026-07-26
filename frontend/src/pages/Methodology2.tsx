import { Link } from 'react-router-dom'
import { useState } from 'react'
import TrustNav from '../components/TrustNav'
import LampMark from '../components/LampMark'
import { TIER_COLORS } from '../components/TrustBadge'
import type { TierName } from '../components/TrustBadge'
import { usePageMeta } from '../hooks/usePageMeta'
import { useJsonLd, faqPageSchema } from '../hooks/useJsonLd'

// Table of contents — drives the sticky sidebar and the anchor IDs below.
const TOC = [
  { id: 'overview', label: 'What Daanaa is' },
  { id: 'public-data-sources', label: 'Where the data comes from' },
  { id: 'peer-financial-context', label: 'Peer financial context' },
  { id: 'not-measured', label: 'What we don’t measure' },
  { id: 'data-limits', label: 'Data limits' },
  { id: 'lamp-tiers', label: 'Visibility levels' },
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
    q: 'What is Peer Financial Context?',
    a: 'Peer Financial Context shows public financial information within comparable peer groups. It is designed to add context, not to rate, rank, or recommend organizations.',
  },
  {
    q: 'What are Lamp Tiers?',
    a: 'Lamp Tiers are visibility indicators based on public information completeness and availability. They are not ratings. They reflect how much public context Daanaa can show.',
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
    <section id={id} className="py-10 md:py-14 border-b border-light-grey last:border-0 scroll-mt-[88px]">
      <div className="max-w-[760px]">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-6 h-px bg-soft-gold/50" />
          <span className="font-body text-[11px] font-medium tracking-[0.10em] text-soft-gold uppercase">{label}</span>
        </div>
        <h2 className="font-display italic text-deep-navy leading-[1.05] tracking-[-0.01em]" >
          {title}
        </h2>
        <div className="mt-6 space-y-4 font-body text-[16px] text-cool-grey leading-[1.7]">
          {children}
        </div>
      </div>
    </section>
  )
}

function Callout({ children }: { children: React.ReactNode }) {
  return (
    <div className="mt-6 p-5 rounded-xl bg-soft-gold/10 border border-soft-gold/20">
      <p className="font-body text-[15px] text-deep-navy leading-[1.6]">{children}</p>
    </div>
  )
}

function TierRow({ score, label, description }: { score: string; label: string; description: string }) {
  // Reserve strength is not a danger gradient. Stronger reserves get a gentle
  // green; everything else is calm slate. Lower reserves are not "worse".
  const color = label === '90th percentile or above' || label === '75th–89th percentile'
    ? '#5a9e6f'
    : '#8a8f98'
  return (
    <div className="flex flex-col sm:flex-row sm:items-start gap-1 sm:gap-4 py-3 border-b border-light-grey last:border-0">
      <span className="shrink-0 sm:w-20 font-body text-[13px] font-semibold" style={{ color }}>{score}</span>
      <span className="shrink-0 sm:w-48 font-body text-[14px] font-medium text-deep-navy">{label}</span>
      <span className="font-body text-[14px] text-cool-grey">{description}</span>
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
      <div className="bg-deep-navy pt-[72px]">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12 pt-8 pb-10 md:pt-12 md:pb-16">
          <div className="flex items-center gap-2 mb-6">
            <Link to="/" className="font-body text-[12px] tracking-[0.02em] text-muted-cream hover:text-warm-cream transition-colors">Home</Link>
            <span className="text-muted-cream">/</span>
            <span className="font-body text-[12px] text-muted-cream">Methodology</span>
          </div>
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-10 md:gap-16">
            <div className="max-w-[640px]">
              <h1 className="font-display italic text-warm-cream leading-[1.05] tracking-[-0.01em]" style={{ fontSize: 'clamp(32px, 5vw, 64px)' }}>
                How Daanaa Works
              </h1>
              <p className="mt-4 font-body text-[18px] leading-[1.6] text-muted-cream">
                We don't score nonprofits on our opinion. We surface publicly available data, place each organization alongside its true peers, and let you decide. This page explains exactly how.
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
              <p className="font-body text-[11px] font-semibold tracking-[0.08em] text-cool-grey uppercase mb-4">On this page</p>
              <nav aria-label="On this page" className="space-y-2.5">
                {TOC.map(item => (
                  <a
                    key={item.id}
                    href={`#${item.id}`}
                    className="block font-body text-[13px] text-cool-grey hover:text-soft-gold transition-colors leading-snug"
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
              <p className="font-body text-[16px] font-semibold text-deep-navy leading-[1.6]">
                Peer Financial Context is not a rating, endorsement, impact score, or recommendation. Daanaa does not rank human worth — we organize public information so people can give more thoughtfully.
              </p>
            </div>

            <Section id="overview" label="Our foundation" title="What Daanaa is, and what it isn't">
              <p>
                Daanaa is a public directory of every active 501(c)(3) in America — independent of paid influence, not affiliated with the IRS or any rating agency, and not a donation processor.{' '}
                <Link to="/about" className="text-soft-gold hover:text-bright-gold font-medium">How we approach this →</Link>
              </p>
              <Callout>
                Two signals work together on every page. The peer financial context score (0–100) measures months of operating reserves as a percentile within a peer group. The peer financial context signal (Healthy, Stable, or Needs Support) adds a plain-language summary of financial health. Neither measures impact, mission quality, or whether a group deserves support. Daanaa is not a charity rating agency.
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
                      <p className="font-body text-[14px] font-semibold text-deep-navy">{source}</p>
                      <p className="font-body text-[14px] text-cool-grey mt-1">{what}</p>
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
                This number sits quietly behind the lamp. It is not a grade and it is not a judgment. It says nothing about the quality of the work, the people, or the good they do. All it does is measure one organization's financial reserves compared to genuinely similar groups. The lamp is the journey. This is just one fact along the way.
              </p>
              <p>
                We use two dimensions to find organizations that are truly comparable:
              </p>
              <div className="mt-2 space-y-3">
                <div className="p-4 bg-white rounded-lg border border-light-grey">
                  <p className="font-body text-[14px] font-semibold text-deep-navy">Funding model</p>
                  <p className="font-body text-[14px] text-cool-grey mt-1">
                    Each nonprofit is placed into one of three funding archetypes: Donation-Funded Programs (organizations that rely on community fundraising), Fee-for-Service Operators (organizations that earn revenue by providing services), or Endowment-Funded Grantmakers (organizations funded by endowment returns). A food bank is compared to other donation-funded programs, not to consulting firms or family foundations.
                  </p>
                </div>
                <div className="p-4 bg-white rounded-lg border border-light-grey">
                  <p className="font-body text-[14px] font-semibold text-deep-navy">Revenue band</p>
                  <p className="font-body text-[14px] text-cool-grey mt-1">
                    A nonprofit raising $60,000 a year operates in a completely different reality from one raising $5 million. We use three universal revenue bands: Micro (under $150K), Professional ($150K–$700K), and Established (over $700K). A small food bank is compared to other donation-funded programs in the Micro band, not to large hospitals or international NGOs.
                  </p>
                </div>
              </div>
              <p className="mt-4">
                Within each peer group, organizations are ranked by one metric: months of operating reserves. This is how many months an organization could keep operating on its unrestricted net assets if income stopped completely. It comes directly from the most recent IRS Form 990 filing and is calculated the same way for every organization, regardless of funding model or size.
              </p>

              <div className="mt-6">
                <p className="font-body text-[14px] font-semibold text-deep-navy mb-1">What the score means</p>
                <p className="font-body text-[13px] text-cool-grey mb-3 max-w-[640px]">
                  The 0–100 score is a percentile: where this organization's reserves fall compared to similar organizations. A score of 75 means stronger reserves than 75% of its peers. This is not about size or budget; it is about financial resilience.
                </p>
                <div className="bg-white rounded-xl border border-light-grey p-4">
                  <TierRow score="90 to 100" label="90th percentile or above" description="Holds more reserves than nearly all similar organizations. A strong financial cushion." />
                  <TierRow score="75 to 89" label="75th–89th percentile" description="Holds more reserves than most similar organizations." />
                  <TierRow score="50 to 74" label="Above median reserves" description="Financial position is comparable to or slightly better than the peer median." />
                  <TierRow score="25 to 49" label="Below median reserves" description="Holds fewer reserves than the peer median. Often because resources go directly into programs." />
                  <TierRow score="0 to 24" label="Lowest reserves" description="Among the lowest reserves in its peer group. Often a sign of lean operations focused on mission delivery, not weakness." />
                </div>
              </div>

              <p className="mt-5 font-body text-[15px] text-cool-grey leading-[1.7]">
                When you visit an organization's page, you also see a <strong className="text-deep-navy font-medium">peer financial context signal</strong>: Healthy, Stable, or Needs Support. This is separate from the percentile number. The percentile shows where reserves fall among peers. The signal shows financial health: whether the organization is building reserves, holding steady, or operating with limited cushion. A small organization can have healthy reserves for its size; a large one can show Needs Support.
              </p>
              <p className="mt-3 font-body text-[15px] text-cool-grey leading-[1.7]">
                <strong className="text-deep-navy font-medium">Why "Needs Support"?</strong> A lower reserve position does not mean a lesser organization. It often means a group doing essential work within tight means, investing its resources directly into mission rather than building savings. That is exactly the kind of organization that benefits most from community support. It is an invitation, not a verdict.
              </p>
              <p className="mt-3 font-body text-[15px] text-cool-grey leading-[1.7]">
                <strong className="text-deep-navy font-medium">Economic context.</strong> On some organization pages, you'll also see a short note about the broader economy in that filing year, things like unemployment or interest rates. This is background, not part of the score. It doesn't change the percentile or the health signal. It's there so a lean reserve position in a hard year reads differently than the same position in a strong one.
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
                  <li key={item} className="flex items-start gap-3 font-body text-[15px] text-cool-grey">
                    <span className="text-soft-gold mt-1.5 w-1.5 h-1.5 rounded-full bg-soft-gold shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
              <p className="mt-4">
                These are important decisions you should make based on your own research, not assumptions from a score.
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
                  <li key={item} className="flex items-start gap-3 font-body text-[15px] text-cool-grey">
                    <span className="text-soft-gold mt-1.5 w-1.5 h-1.5 rounded-full bg-soft-gold shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
            </Section>

            <Section id="lamp-tiers" label="Visibility levels" title="Visibility levels: how much information is available">
              <p>
                Every page displays a lamp tier, and it is a journey, not a verdict. The lamp shows how much public data backs a page <em>today</em>, never our opinion of the organization's work. Most U.S. nonprofits are small, rooted in their communities, and nearly invisible in public data. They are exactly who we built Daanaa for. A fainter lamp isn't a judgment. It's an invitation. Any organization can add more context by sharing its mission, website, and available financial detail, and that path stays free and open, always.
              </p>
              <div className="mt-4 space-y-3">
                {([
                  { tier: 'Beacon' as TierName, what: 'Complete public data: financial reports, mission statement, website, and current Form 990.' },
                  { tier: 'Torch' as TierName, what: 'Strong public data: financial context available, recent filings, and organizational information.' },
                  { tier: 'Candle' as TierName, what: 'Moderate public data: some financial information and basic organizational records.' },
                  { tier: 'Spark' as TierName, what: 'Recognized nonprofit with minimal public information available. Many small organizations filing simplified forms fall here.' },
                ] as const).map(({ tier, what }) => (
                  <div key={tier} className="flex gap-4 p-4 bg-white rounded-lg border border-light-grey items-start">
                    <div className="shrink-0 flex flex-col items-center gap-1.5 pt-0.5">
                      <LampMark tier={tier} size="sm" />
                      <span className="font-body text-[10px] font-semibold tracking-[0.03em]" style={{ fontFamily: 'Cinzel, serif', color: TIER_COLORS[tier] }}>{tier}</span>
                    </div>
                    <p className="font-body text-[14px] text-cool-grey leading-[1.6]">{what}</p>
                  </div>
                ))}
              </div>
              <Callout>
                A lower tier is not a negative judgment. It reflects what public data is available, not the organization's character or importance. A small organization filing a simplified annual form while doing extraordinary community work will show as Spark. That can change as more data enters the public record.
              </Callout>
              <div className="mt-6">
                <Link
                  to="/tiers"
                  className="inline-flex items-center gap-1.5 font-body text-[13px] font-semibold text-soft-gold hover:text-bright-gold transition-colors"
                >
                  Full tier reference →
                </Link>
              </div>
            </Section>

            <Section id="hidden-gems" label="Orgs you may not have heard of" title="Organizations you may not have heard of">
              <p>
                These are small organizations with strong financial health for their size — solid reserve funds, reasonable expense ratios, and mission-driven operations. They often get overlooked in favor of larger, more visible nonprofits. Daanaa surfaces them specifically because they deserve to be found.
              </p>
              <p className="mt-4">
                Three criteria must all be true, based entirely on public IRS data:
              </p>
              <div className="mt-4 space-y-3">
                {[
                  {
                    label: '85th percentile or above within peer group',
                    detail: 'A peer financial context score of 85 or above — stronger reserves than at least 85% of organizations with the same funding model and revenue band.',
                  },
                  {
                    label: 'Annual revenue under $500,000',
                    detail: 'The organization is genuinely small. Revenue must be verified from IRS filings — organizations with no reported revenue don\'t qualify.',
                  },
                  {
                    label: 'Has a mission statement',
                    detail: 'There is a readable description of what the organization does, sourced from IRS filings or the organization\'s own public records.',
                  },
                ].map(({ label, detail }) => (
                  <div key={label} className="flex gap-4 p-4 bg-white rounded-lg border border-light-grey">
                    <div className="shrink-0 w-2 h-2 mt-2 rounded-full bg-soft-gold" />
                    <div>
                      <p className="font-body text-[14px] font-semibold text-deep-navy">{label}</p>
                      <p className="font-body text-[14px] text-cool-grey mt-1">{detail}</p>
                    </div>
                  </div>
                ))}
              </div>
              <Callout>
                Hidden gem status is determined algorithmically from public IRS data — not by editorial judgment, paid promotion, or any relationship with Daanaa. An organization either meets all three criteria or it doesn't. About 33,000 organizations currently qualify, including micro-organizations with as little as $7,000 in annual revenue that rank at the top of their peer group.
              </Callout>
            </Section>

            <Section id="two-layers" label="Two layer model" title="What the organization controls">
              <p>Every page has two distinct layers:</p>
              <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-5 bg-white rounded-xl border border-light-grey">
                  <p className="font-body text-[12px] tracking-[0.06em] text-soft-gold uppercase font-medium mb-2">Daanaa's data</p>
                  <p className="font-body text-[13px] text-cool-grey leading-[1.6]">
                    Sourced from IRS public records. Objective, fact checked, timestamped. Organizations cannot edit this layer.
                  </p>
                  <ul className="mt-3 space-y-1 font-body text-[13px] text-cool-grey">
                    {['Legal name', 'Nonprofit category', 'Revenue from IRS filings', 'Peer financial context score', 'Data source & year'].map(i => (
                      <li key={i} className="flex items-center gap-2">
                        <span className="w-1 h-1 rounded-full bg-cool-grey shrink-0" />{i}
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="p-5 bg-white rounded-xl border-2 border-dashed border-soft-gold/30">
                  <p className="font-body text-[12px] tracking-[0.06em] text-soft-gold uppercase font-medium mb-2">Organization's data</p>
                  <p className="font-body text-[13px] text-cool-grey leading-[1.6]">
                    Added directly by the organization. Clearly labeled as self reported. Claim your page to update this information.
                  </p>
                  <ul className="mt-3 space-y-1 font-body text-[13px] text-cool-grey">
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
                  { freq: 'Ongoing', what: 'Peer financial context scores recalculated after bulk revenue updates' },
                ].map(({ freq, what }, i) => (
                  <div key={`${freq}-${i}`} className="flex gap-4 items-start">
                    <span className="shrink-0 font-body text-[13px] font-semibold text-soft-gold w-20">{freq}</span>
                    <span className="font-body text-[14px] text-cool-grey">{what}</span>
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
                      <span className="font-body text-[15px] font-semibold text-deep-navy">{faq.q}</span>
                      <svg className={`w-5 h-5 shrink-0 text-soft-gold transition-transform ${openFaq === i ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <polyline points="6 9 12 15 18 9"></polyline>
                      </svg>
                    </button>
                    {openFaq === i && (
                      <div className="px-5 py-3 border-t border-light-grey bg-warm-cream/20">
                        <p className="font-body text-[14px] text-cool-grey leading-[1.6]">{faq.a}</p>
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
                <h3 className="font-display italic text-warm-cream text-[28px] leading-[1.1]">Questions or corrections?</h3>
                <p className="mt-3 font-body text-[16px] text-muted-cream max-w-[480px] mx-auto leading-[1.6]">
                  If you represent a listed organization and want to update or claim your page, or if you spot an error in our data, we want to hear from you. We correct errors quickly and disclose corrections publicly.
                </p>
                <Link
                  to="/feedback"
                  className="mt-6 inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-soft-gold text-deep-navy font-body text-[14px] font-semibold hover:bg-bright-gold transition-colors"
                >
                  Contact us
                </Link>
                <div className="mt-6 flex flex-wrap items-center justify-center gap-6">
                  <Link to="/about" className="font-body text-[13px] text-muted-cream hover:text-warm-cream transition-colors">
                    About Daanaa →
                  </Link>
                  <Link to="/research" className="font-body text-[13px] text-muted-cream hover:text-warm-cream transition-colors">
                    Research & data →
                  </Link>
                  <Link to="/directory" className="font-body text-[13px] text-muted-cream hover:text-warm-cream transition-colors">
                    Browse the directory →
                  </Link>
                  <Link to="/legal" className="font-body text-[13px] text-muted-cream hover:text-warm-cream transition-colors">
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
