import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'

export default function Methodology() {
  usePageMeta('Methodology — Daanaa', 'Learn how Daanaa organizes public nonprofit information, Peer Financial Context, Lamp Tiers, data limits, and stewardship guardrails.')

  return (
    <div className="min-h-[100dvh]">
      {/* Hero */}
      <div className="bg-deep-navy pt-[72px]">
        <div className="max-w-[1120px] mx-auto px-6 md:px-12 pt-16 pb-12">
          <div className="flex items-center gap-2 mb-6">
            <Link to="/" className="font-body text-[12px] text-muted-cream hover:text-warm-cream transition-colors">Home</Link>
            <span className="text-muted-cream">/</span>
            <span className="font-body text-[12px] text-muted-cream">Methodology</span>
          </div>
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-10 md:gap-16">
            <div className="max-w-[720px]">
              <h1 className="font-display italic text-warm-cream mt-3 leading-[1.05] tracking-[-0.01em]" style={{ fontSize: 'clamp(40px, 5vw, 60px)' }}>
                Methodology
              </h1>
              <p className="mt-6 font-body text-[17px] leading-[1.65] text-muted-cream">
                Daanaa does not rank human worth. We organize public information so people can make more thoughtful giving decisions.
              </p>
            </div>
            <div className="shrink-0 hidden md:flex justify-end">
              <img src="/logo.png" alt="Daanaa" className="w-44 h-44 lg:w-52 lg:h-52 object-contain drop-shadow-[0_12px_48px_rgba(201,169,110,0.22)]" />
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="bg-warm-cream py-16 md:py-20">
        <div className="max-w-[1120px] mx-auto px-6 md:px-12">

          {/* Critical disclaimer */}
          <div className="mb-16 p-8 bg-white border-2 border-deep-navy/10 rounded-2xl">
            <p className="font-body text-[16px] font-semibold text-deep-navy leading-[1.65]">
              Peer Financial Context is not a rating, endorsement, impact score, or recommendation.
            </p>
          </div>

          {/* What this page explains */}
          <section className="mb-16">
            <h2 className="font-display italic text-deep-navy text-[32px] md:text-[40px] leading-[1.15] tracking-[-0.01em]">
              What this page explains
            </h2>
            <p className="mt-6 font-body text-[16px] text-cool-grey leading-[1.65] max-w-[720px]">
              This page explains how Daanaa organizes public nonprofit information, what Peer Financial Context shows, what Lamp Tiers mean, what data limitations exist, and how frequently Daanaa updates.
            </p>
          </section>

          <hr className="border-light-grey my-12" />

          {/* Public data sources */}
          <section className="mb-16">
            <h2 className="font-display italic text-deep-navy text-[32px] md:text-[40px] leading-[1.15] tracking-[-0.01em]">
              Public data sources
            </h2>
            <p className="mt-6 font-body text-[16px] text-cool-grey leading-[1.65] max-w-[720px]">
              Daanaa uses only public data from the IRS, NCCS (National Center for Charitable Statistics), and ProPublica.
            </p>
            <ul className="mt-6 space-y-3 max-w-[720px]">
              {[
                'IRS Form 990, 990-EZ, and 990-N filings',
                'IRS Business Master File (nonprofit registry)',
                'NCCS Core Files and research data',
                'ProPublica Nonprofit Explorer data',
              ].map(item => (
                <li key={item} className="flex items-start gap-3 font-body text-[16px] text-cool-grey">
                  <span className="text-soft-gold mt-1">•</span>
                  {item}
                </li>
              ))}
            </ul>
          </section>

          <hr className="border-light-grey my-12" />

          {/* Peer Financial Context */}
          <section className="mb-16">
            <h2 className="font-display italic text-deep-navy text-[32px] md:text-[40px] leading-[1.15] tracking-[-0.01em]">
              Peer Financial Context
            </h2>
            <div className="mt-6 space-y-4 max-w-[720px]">
              <p className="font-body text-[16px] text-cool-grey leading-[1.65]">
                <span className="font-semibold text-deep-navy">Peer Financial Context shows public financial information within comparable peer groups.</span> It is designed to add context, not to rate, rank, or recommend organizations.
              </p>
              <p className="font-body text-[16px] text-cool-grey leading-[1.65]">
                Peer groups are formed by nonprofit type (using NTEE classification), size (revenue), and location. An organization's financial position is compared only within its peer group.
              </p>
              <p className="font-body text-[16px] text-cool-grey leading-[1.65]">
                A small community food bank and a large national nonprofit both support feeding people. Their financial profiles are different, not better or worse. Daanaa shows the context so you can understand what the numbers mean.
              </p>
            </div>
          </section>

          <hr className="border-light-grey my-12" />

          {/* Lamp Tiers */}
          <section className="mb-16">
            <h2 className="font-display italic text-deep-navy text-[32px] md:text-[40px] leading-[1.15] tracking-[-0.01em]">
              Lamp Tiers
            </h2>
            <p className="mt-6 font-body text-[16px] text-cool-grey leading-[1.65] max-w-[720px]">
              <span className="font-semibold text-deep-navy">Lamp Tiers are visibility indicators based on public information completeness and availability.</span> They help explain how much public context Daanaa can show.
            </p>
            <p className="mt-4 font-body text-[16px] text-cool-grey leading-[1.65] max-w-[720px]">
              Tiers reflect what information exists in public records, not the quality, impact, or worth of the organization.
            </p>
            <div className="mt-8 space-y-4">
              {[
                { name: 'Beacon', description: 'Complete public data: financial reports, mission statement, website, current Form 990' },
                { name: 'Torch', description: 'Strong public data: financial context available, recent filings, organizational information' },
                { name: 'Candle', description: 'Moderate public data: some financial information, basic organizational records' },
                { name: 'Spark', description: 'Recognized nonprofit with minimal public information available' },
              ].map(tier => (
                <div key={tier.name} className="p-4 bg-white border border-light-grey rounded-lg">
                  <p className="font-display text-deep-navy text-[18px] font-semibold">{tier.name}</p>
                  <p className="mt-2 font-body text-[14px] text-cool-grey">{tier.description}</p>
                </div>
              ))}
            </div>
          </section>

          <hr className="border-light-grey my-12" />

          {/* What Daanaa does not measure */}
          <section className="mb-16">
            <h2 className="font-display italic text-deep-navy text-[32px] md:text-[40px] leading-[1.15] tracking-[-0.01em]">
              What Daanaa does not measure
            </h2>
            <p className="mt-6 font-body text-[16px] text-cool-grey leading-[1.65] max-w-[720px]">
              Daanaa deliberately does not measure or estimate:
            </p>
            <ul className="mt-6 space-y-3 max-w-[720px]">
              {[
                'Impact or effectiveness of programs',
                'Executive compensation or overhead ratios',
                'Program delivery or service quality',
                'Community need or local priority',
                'Organizational leadership or governance',
                'Staff expertise or program outcomes',
              ].map(item => (
                <li key={item} className="flex items-start gap-3 font-body text-[16px] text-cool-grey">
                  <span className="text-soft-gold mt-1">•</span>
                  {item}
                </li>
              ))}
            </ul>
            <p className="mt-6 font-body text-[16px] text-cool-grey leading-[1.65] max-w-[720px]">
              These are important decisions you should make based on your own research, not assumptions from a score.
            </p>
          </section>

          <hr className="border-light-grey my-12" />

          {/* Data limits */}
          <section className="mb-16">
            <h2 className="font-display italic text-deep-navy text-[32px] md:text-[40px] leading-[1.15] tracking-[-0.01em]">
              Data limits
            </h2>
            <p className="mt-6 font-body text-[16px] text-cool-grey leading-[1.65] max-w-[720px]">
              Public nonprofit data has real limits:
            </p>
            <ul className="mt-6 space-y-3 max-w-[720px]">
              {[
                'Reporting delays: Form 990 filings are often 1-2 years behind current operations',
                'Coverage gaps: not all nonprofits file annually; small organizations may file simplified forms',
                'Classification challenges: NTEE categorization is imperfect and assigned by filing organizations',
                'Missing data: some organizations don\'t file or have incomplete financial records',
              ].map(item => (
                <li key={item} className="flex items-start gap-3 font-body text-[16px] text-cool-grey">
                  <span className="text-soft-gold mt-1">•</span>
                  {item}
                </li>
              ))}
            </ul>
          </section>

          <hr className="border-light-grey my-12" />

          {/* Update cadence */}
          <section className="mb-16">
            <h2 className="font-display italic text-deep-navy text-[32px] md:text-[40px] leading-[1.15] tracking-[-0.01em]">
              Update cadence
            </h2>
            <p className="mt-6 font-body text-[16px] text-cool-grey leading-[1.65] max-w-[720px]">
              Daanaa updates public nonprofit information monthly as new IRS data becomes available.
            </p>
          </section>

          <hr className="border-light-grey my-12" />

          {/* Corrections and feedback */}
          <section className="mb-16">
            <h2 className="font-display italic text-deep-navy text-[32px] md:text-[40px] leading-[1.15] tracking-[-0.01em]">
              Corrections and feedback
            </h2>
            <p className="mt-6 font-body text-[16px] text-cool-grey leading-[1.65] max-w-[720px]">
              If you find an error or have feedback, please contact us. Organizations and community members can report data issues, and we welcome corrections to public record information.
            </p>
            <Link
              to="/feedback"
              className="mt-6 inline-flex items-center gap-2 font-body text-[14px] font-semibold text-soft-gold hover:text-bright-gold transition-colors"
            >
              Report a data issue →
            </Link>
          </section>

          {/* Related links */}
          <div className="mt-20 pt-12 border-t border-light-grey">
            <p className="font-body text-[11px] font-semibold tracking-[0.08em] text-cool-grey uppercase mb-4">Related</p>
            <div className="flex flex-wrap gap-4">
              <Link to="/stewardship" className="inline-flex items-center gap-2 font-body text-[14px] text-soft-gold hover:text-bright-gold transition-colors">
                Stewardship →
              </Link>
              <Link to="/faq" className="inline-flex items-center gap-2 font-body text-[14px] text-soft-gold hover:text-bright-gold transition-colors">
                FAQ →
              </Link>
              <Link to="/directory" className="inline-flex items-center gap-2 font-body text-[14px] text-soft-gold hover:text-bright-gold transition-colors">
                Discover →
              </Link>
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}
