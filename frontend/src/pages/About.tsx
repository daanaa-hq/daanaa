import { Link } from 'react-router-dom'
import { useApi } from '../hooks/useApi'
import { getStats } from '../data/api'
import { usePageMeta } from '../hooks/usePageMeta'

function formatCount(n: number): string {
  return n.toLocaleString('en-US')
}

export default function About() {
  usePageMeta('About', 'Daanaa is a civic nonprofit-discovery platform. We index tax-deductible 501(c)(3) organizations and make that information freely available to any donor who wants to give with confidence.')
  const { data: stats } = useApi(() => getStats(), [])

  return (
    <div className="min-h-[100dvh]">
      <div className="bg-deep-navy pt-[72px]">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12 pt-8 pb-10 md:pt-12 md:pb-16">
          <div className="flex items-center gap-2 mb-6">
            <Link to="/" className="font-body text-[12px] text-muted-cream hover:text-warm-cream transition-colors">Home</Link>
            <span className="text-muted-cream/50">/</span>
            <span className="font-body text-[12px] text-muted-cream">About</span>
          </div>
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-10 md:gap-16">
            {/* Copy — left */}
            <div className="max-w-[560px]">
              <span className="font-body text-[11px] font-medium tracking-[0.08em] text-soft-gold uppercase">About Daanaa</span>
              <h1 className="font-display italic text-warm-cream mt-3 leading-[1.05] tracking-[-0.01em]" style={{ fontSize: 'clamp(32px, 5vw, 60px)' }}>
                Civic infrastructure for informed giving
              </h1>
              <p className="mt-5 font-body text-[18px] leading-[1.65] text-muted-cream">
                Daanaa aims to index every active 501(c)(3) organization in the United States, more than 1.6 million whose donations are tax-deductible, all from public IRS data. We score each one against its true peers and make that picture free for any donor who wants to give with confidence.
              </p>
            </div>
            {/* Logo — right */}
            <div className="shrink-0 flex justify-center md:justify-end">
              <img
                src="/logo.png"
                alt="Daanaa"
                className="w-48 h-48 md:w-64 md:h-64 lg:w-80 lg:h-80 object-contain drop-shadow-[0_12px_48px_rgba(201,169,110,0.22)]"
              />
            </div>
          </div>
        </div>
      </div>

      <div className="bg-warm-cream py-10 md:py-16 lg:py-20">
        <div className="max-w-[800px] mx-auto px-6 lg:px-12 space-y-16">

          {/* Name */}
          <div className="border-l-2 border-soft-gold/30 pl-6 md:pl-8">
            <span className="font-body text-[11px] font-medium tracking-[0.08em] text-soft-gold uppercase">Our name</span>
            <h2 className="font-display italic text-deep-navy mt-3 leading-[1.05]" style={{ fontSize: 'clamp(24px, 3.5vw, 40px)' }}>
              Giving should be as wise as it is generous
            </h2>
            <div className="mt-5 space-y-4 font-body text-[16px] text-cool-grey leading-[1.7]">
              <p>
                Daanaa means "wise." We focus on helping you give intentionally.
              </p>
              <p>
                Instead of handling donations, we connect you directly to nonprofits and help you track your impact in a secure donor wallet.
              </p>
              <p>
                Because real wisdom isn't just in what we give. It's in how we share it.
              </p>
            </div>
          </div>

          {/* Mission */}
          <div className="border-l-2 border-soft-gold/30 pl-6 md:pl-8">
            <span className="font-body text-[11px] font-medium tracking-[0.08em] text-soft-gold uppercase">Why we built this</span>
            <h2 className="font-display italic text-deep-navy mt-3 leading-[1.05]" style={{ fontSize: 'clamp(24px, 3.5vw, 40px)' }}>
              Giving should not require a research degree
            </h2>
            <div className="mt-5 space-y-4 font-body text-[16px] text-cool-grey leading-[1.7]">
              <p>
                The IRS makes 990 filings public. ProPublica makes them searchable. But turning a 30 page tax return into a clear answer takes hours most donors don't have. Is the organization doing what it says? Is it financially healthy? Is it who it claims to be?
              </p>
              <p>
                Daanaa does that work. We read the filings, compare each organization to its peers, and show the result in a form you can read in seconds. The score doesn't replace your judgment. It informs it.
              </p>
              <p>
                We are not a charity, and we never ask for donations on behalf of organizations. We are infrastructure, built to make the charitable sector easier to see clearly.
              </p>
            </div>
          </div>

          {/* Data */}
          <div className="border-l-2 border-soft-gold/30 pl-6 md:pl-8">
            <span className="font-body text-[11px] font-medium tracking-[0.08em] text-soft-gold uppercase">The data</span>
            <h2 className="font-display italic text-deep-navy mt-3 leading-[1.05]" style={{ fontSize: 'clamp(24px, 3.5vw, 40px)' }}>
              Built on public records
            </h2>
            <div className="mt-5 space-y-4 font-body text-[16px] text-cool-grey leading-[1.7]">
              <p>
                Every organization on Daanaa comes from the IRS Business Master File, the official list of active 501(c)(3) tax exempt organizations in the United States. Financial data comes from IRS Statistics of Income extracts and ProPublica Nonprofit Explorer, both of which republish Form 990 filings.
              </p>
              <p>
                We do not create or change the source data. We gather it, clean it up, score it, and show it. The raw sources, IRS filings and registration records, are public, so anyone can check our work.
              </p>
            </div>
            <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: stats ? formatCount(stats.total_organizations) : '—', sub: 'organizations indexed' },
                { label: '26', sub: 'NTEE major categories' },
                { label: '2020 to 2024', sub: 'financial data range' },
                { label: 'Monthly', sub: 'IRS update cadence' },
              ].map(s => (
                <div key={s.sub} className="bg-white border border-light-grey rounded-xl p-5">
                  <p className="font-display text-[22px] text-deep-navy leading-tight">{s.label}</p>
                  <p className="font-body text-[13px] text-cool-grey mt-1.5">{s.sub}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Score */}
          <div className="border-l-2 border-soft-gold/30 pl-6 md:pl-8">
            <span className="font-body text-[11px] font-medium tracking-[0.08em] text-soft-gold uppercase">Peer financial context</span>
            <h2 className="font-display italic text-deep-navy mt-3 leading-[1.05]" style={{ fontSize: 'clamp(24px, 3.5vw, 40px)' }}>
              A peer percentile, not a grade
            </h2>
            <div className="mt-5 space-y-4 font-body text-[16px] text-cool-grey leading-[1.7]">
              <p>
                A peer financial context score of 87 means this organization has a larger financial footprint than 87% of nonprofits in its peer group. It is not an absolute judgment. A score of 60 in a highly competitive peer group may represent stronger practice than a 90 in a sparse one.
              </p>
              <p>
                Every score is explainable. Each organization also carries a visibility level (Beacon, Lantern, Flame, Glow, or Spark) reflecting how much public information is available. Click any lamp mark on any profile to see the exact criteria and what's needed to reach the next level. There are no black boxes.
              </p>
            </div>
          </div>

          {/* Contact */}
          <div className="border-t border-light-grey pt-12">
            <span className="font-body text-[11px] font-medium tracking-[0.08em] text-soft-gold uppercase">Contact</span>
            <h2 className="font-display italic text-deep-navy mt-3 leading-[1.05]" style={{ fontSize: 'clamp(22px, 3vw, 36px)' }}>
              Get in touch
            </h2>
            <div className="mt-5 space-y-3 font-body text-[16px] text-cool-grey leading-[1.7]">
              <p>For data corrections, organization disputes, feedback, or press inquiries:</p>
              <Link to="/feedback" className="inline-flex items-center gap-2 text-soft-gold hover:text-bright-gold transition-colors font-medium">
                Send us a message
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg>
              </Link>
              <p className="text-[14px]">
                Or email directly at{' '}
                <a href="mailto:hello@daanaa.org" className="text-soft-gold hover:text-bright-gold transition-colors">hello@daanaa.org</a>
              </p>
              <p className="text-[14px]">
                For organizations wanting to claim or update their profile:
                <Link to="/for-nonprofits" className="ml-1 text-soft-gold hover:text-bright-gold transition-colors">
                  For Nonprofits →
                </Link>
              </p>
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}
