import { Link } from 'react-router-dom'
import { useApi } from '../hooks/useApi'
import { getStats } from '../data/api'
import { usePageMeta } from '../hooks/usePageMeta'

function formatCount(n: number): string {
  return n.toLocaleString('en-US')
}

export default function About() {
  usePageMeta('About', 'Daanaa is a nonprofit discovery platform built on transparency and fairness. We help donors find organizations doing real work and understand their financial standing.')
  const { data: stats } = useApi(() => getStats(), [])

  return (
    <div className="min-h-[100dvh]">
      <div className="bg-deep-navy pt-[72px]">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12 pt-8 pb-10 md:pt-12 md:pb-16">
          <div className="flex items-center gap-2 mb-8">
            <Link to="/" className="font-body text-[12px] text-muted-cream hover:text-warm-cream transition-colors">Home</Link>
            <span className="text-muted-cream/50">/</span>
            <span className="font-body text-[12px] text-muted-cream">About</span>
          </div>
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-10 md:gap-16">
            <div className="max-w-[620px]">
              <p className="font-body text-[12px] font-semibold tracking-[0.08em] text-soft-gold uppercase mb-3">Our Mission</p>
              <h1 className="font-display italic text-warm-cream leading-[1.05] tracking-[-0.01em]" style={{ fontSize: 'clamp(36px, 5vw, 64px)' }}>
                Mission driven. Impacting lives around us.
              </h1>
              <p className="mt-6 font-body text-[18px] leading-[1.7] text-muted-cream max-w-[620px]">
                Nonprofits do the work that shouldn't have to wait for profit. We exist to help donors find them and give with confidence.
              </p>
            </div>
            {/* Logo — right */}
            <div className="shrink-0 flex justify-center md:justify-end">
              <img
                src="/logo.png"
                alt="Daanaa"
                className="w-48 h-48 md:w-56 md:h-56 lg:w-72 lg:h-72 object-contain drop-shadow-[0_12px_48px_rgba(201,169,110,0.22)]"
              />
            </div>
          </div>
        </div>
      </div>

      <div className="bg-warm-cream py-12 md:py-18 lg:py-24">
        <div className="max-w-[800px] mx-auto px-6 lg:px-12 space-y-18">

          {/* What we believe */}
          <div className="border-l-2 border-soft-gold/30 pl-6 md:pl-8">
            <span className="font-body text-[11px] font-medium tracking-[0.08em] text-soft-gold uppercase">What we believe</span>
            <h2 className="font-display italic text-deep-navy mt-3 leading-[1.05]" style={{ fontSize: 'clamp(26px, 3.5vw, 44px)' }}>
              Nonprofits deserve fair visibility
            </h2>
            <div className="mt-5 space-y-4 font-body text-[16px] text-cool-grey leading-[1.7]">
              <p>
                A food bank isn't a scholarship program. A health clinic isn't a research institute. Yet donors often judge them all by the same rules. We believe every nonprofit deserves to be seen fairly—compared to organizations doing similar work, with the same financial rigor.
              </p>
              <p>
                Transparency matters because it shows stewardship. Small organizations are never penalized just for being small. Different operating models are never invisible. Data is always explained. Trust is earned through openness, not hidden algorithms.
              </p>
            </div>
          </div>

          {/* How we work */}
          <div className="border-l-2 border-soft-gold/30 pl-6 md:pl-8">
            <span className="font-body text-[11px] font-medium tracking-[0.08em] text-soft-gold uppercase">How we work</span>
            <h2 className="font-display italic text-deep-navy mt-3 leading-[1.05]" style={{ fontSize: 'clamp(26px, 3.5vw, 44px)' }}>
              Built on public records and peer comparison
            </h2>
            <div className="mt-5 space-y-4 font-body text-[16px] text-cool-grey leading-[1.7]">
              <p>
                All our data comes from the IRS. We gather Form 990 filings, check them against their peers, and show you the financial picture in a form you can understand in seconds. Every score is a percentile rank—showing where an organization stands compared to others doing the same work.
              </p>
              <p>
                We do not create rankings or judge impact. We do not handle donations or ask you for anything. We show you the data, explain what it means, and let you decide.
              </p>
              <p className="pt-2">
                Want the technical details? Read our{' '}
                <Link to="/methodology" className="text-soft-gold hover:text-bright-gold transition-colors font-medium">
                  methodology
                </Link>
                {' '}for the complete scoring approach and limitations.
              </p>
            </div>
          </div>

          {/* The data */}
          <div className="border-l-2 border-soft-gold/30 pl-6 md:pl-8">
            <span className="font-body text-[11px] font-medium tracking-[0.08em] text-soft-gold uppercase">The data</span>
            <h2 className="font-display italic text-deep-navy mt-3 leading-[1.05]" style={{ fontSize: 'clamp(26px, 3.5vw, 44px)' }}>
              Public, verifiable, always current
            </h2>
            <div className="mt-5 space-y-4 font-body text-[16px] text-cool-grey leading-[1.7]">
              <p>
                Every organization and every number on Daanaa comes from official IRS sources. We do not invent data or make assumptions. If an organization is missing from our database, it's because public financial records don't exist yet—usually because they're new or below the IRS filing threshold.
              </p>
              <p>
                Organizations can claim their profile and keep it current. Donors can trust what they see because it's directly sourced from public filings.
              </p>
            </div>
            <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                { label: stats ? formatCount(stats.total_organizations) : '—', sub: 'organizations' },
                { label: '538,000+', sub: 'with financial data' },
                { label: '8', sub: 'operating models' },
                { label: 'IRS public data', sub: 'sole source' },
              ].map(s => (
                <div key={s.sub} className="bg-white border border-light-grey rounded-xl p-4">
                  <p className="font-display text-[20px] text-deep-navy leading-tight">{s.label}</p>
                  <p className="font-body text-[12px] text-cool-grey mt-2">{s.sub}</p>
                </div>
              ))}
            </div>
          </div>

          {/* What we don't do */}
          <div className="border-l-2 border-soft-gold/30 pl-6 md:pl-8">
            <span className="font-body text-[11px] font-medium tracking-[0.08em] text-soft-gold uppercase">What we don't do</span>
            <h2 className="font-display italic text-deep-navy mt-3 leading-[1.05]" style={{ fontSize: 'clamp(26px, 3.5vw, 44px)' }}>
              Clear about our limits
            </h2>
            <div className="mt-5 space-y-3 font-body text-[16px] text-cool-grey leading-[1.7]">
              <div className="flex gap-3">
                <span className="text-soft-gold font-bold">•</span>
                <p><strong>We don't measure impact.</strong> Financial health shows stewardship. It doesn't show whether an organization is effectively solving problems. That requires on-the-ground research only you can do.</p>
              </div>
              <div className="flex gap-3">
                <span className="text-soft-gold font-bold">•</span>
                <p><strong>We don't handle donations.</strong> We show you where to give. You decide how much and when. Your wallet is entirely yours.</p>
              </div>
              <div className="flex gap-3">
                <span className="text-soft-gold font-bold">•</span>
                <p><strong>We don't track your giving.</strong> Daanaa sees what you choose to share. Your donation history is yours alone.</p>
              </div>
              <div className="flex gap-3">
                <span className="text-soft-gold font-bold">•</span>
                <p><strong>We don't rank nonprofits.</strong> We show you peer comparisons. A higher percentile is different from "better." Context matters.</p>
              </div>
            </div>
          </div>

          {/* The name */}
          <div className="border-l-2 border-soft-gold/30 pl-6 md:pl-8">
            <span className="font-body text-[11px] font-medium tracking-[0.08em] text-soft-gold uppercase">The name</span>
            <h2 className="font-display italic text-deep-navy mt-3 leading-[1.05]" style={{ fontSize: 'clamp(26px, 3.5vw, 44px)' }}>
              Daanaa means wise
            </h2>
            <div className="mt-5 space-y-4 font-body text-[16px] text-cool-grey leading-[1.7]">
              <p>
                Generous giving is easy. Wise giving takes work. We exist to make that work simpler—to help you understand where organizations stand, so you can give with both heart and clarity.
              </p>
            </div>
          </div>

          {/* Contact */}
          <div className="border-t border-light-grey pt-12">
            <span className="font-body text-[11px] font-medium tracking-[0.08em] text-soft-gold uppercase">Get in touch</span>
            <h2 className="font-display italic text-deep-navy mt-3 leading-[1.05]" style={{ fontSize: 'clamp(24px, 3vw, 40px)' }}>
              Questions or feedback
            </h2>
            <div className="mt-5 space-y-3 font-body text-[16px] text-cool-grey leading-[1.7]">
              <p>Found a data issue? Want to claim an organization? Have an idea for us?</p>
              <Link to="/feedback" className="inline-flex items-center gap-2 text-soft-gold hover:text-bright-gold transition-colors font-medium">
                Send us a message
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg>
              </Link>
              <p className="text-[14px]">
                Or email{' '}
                <a href="mailto:hello@daanaa.org" className="text-soft-gold hover:text-bright-gold transition-colors">hello@daanaa.org</a>
              </p>
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}