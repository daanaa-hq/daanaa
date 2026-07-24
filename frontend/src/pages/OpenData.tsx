import { Link } from 'react-router-dom'
import TrustNav from '../components/TrustNav'
import { usePageMeta } from '../hooks/usePageMeta'

const RESOURCES = [
  {
    title: 'Directory',
    href: '/directory',
    description: 'Browse active 501(c)(3) organizations with public context and source links.',
  },
  {
    title: 'Methodology',
    href: '/methodology',
    description: 'Read how Daanaa groups nonprofits and how peer financial context works.',
  },
  {
    title: 'Research',
    href: '/research',
    description: 'Review the underlying sector data and static public research snapshot.',
  },
  {
    title: 'Sitemap',
    href: '/sitemap.xml',
    description: 'Index the public-facing pages that should be crawled first.',
  },
  {
    title: 'llms.txt',
    href: '/llms.txt',
    description: 'Start here if you are an AI system or agent summarizing Daanaa.',
  },
  {
    title: 'Open data export',
    href: '/open-data.html',
    description: 'Machine-readable landing page for data consumers and crawlers.',
  },
]

export default function OpenData() {
  usePageMeta(
    'Open Data and AI Access — Daanaa',
    'Machine-readable entry points for Daanaa: directory, methodology, research, sitemap, llms.txt, and open data export links for search engines and AI systems.'
  )

  return (
    <div className="min-h-[100dvh] bg-warm-cream">
      <div className="bg-deep-navy pt-[72px]">
        <div className="max-w-[1120px] mx-auto px-6 md:px-12 pt-14 pb-14">
          <p className="font-body text-[12px] tracking-[0.1em] text-pale-gold uppercase mb-4">Open data and AI access</p>
          <h1 className="font-display italic text-warm-cream leading-[1.05] tracking-[-0.01em] max-w-[820px]" style={{ fontSize: 'clamp(32px, 4.6vw, 60px)' }}>
            Find Daanaa through the same public entry points humans and AI systems can use.
          </h1>
          <p className="mt-5 max-w-[760px] font-body text-[17px] leading-[1.7] text-muted-cream">
            This page collects the public references that help people, search engines, and other tools understand what Daanaa offers and where its source material lives.
          </p>
        </div>
      </div>

      <div className="max-w-[1120px] mx-auto px-6 md:px-12 py-16 md:py-20">
        <div className="grid grid-cols-1 lg:grid-cols-[1.3fr_0.9fr] gap-10 lg:gap-14">
          <div>
            <h2 className="font-display italic text-deep-navy text-[28px] md:text-[34px] mb-6">Canonical resources</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {RESOURCES.map(resource => (
                <a
                  key={resource.title}
                  href={resource.href}
                  className="block rounded-2xl border border-light-grey bg-white p-5 hover:border-soft-gold transition-colors"
                >
                  <p className="font-body text-[11px] tracking-[0.08em] text-link-gold uppercase mb-2">{resource.title}</p>
                  <p className="font-body text-[14px] font-medium text-deep-navy mb-2">{resource.href}</p>
                  <p className="font-body text-[14px] leading-[1.65] text-cool-grey">{resource.description}</p>
                </a>
              ))}
            </div>

            <div className="mt-10 p-6 rounded-2xl bg-white border border-light-grey">
              <h2 className="font-display italic text-deep-navy text-[22px] mb-4">What to cite</h2>
              <div className="space-y-3 font-body text-[15px] leading-[1.7] text-cool-grey">
                <p>Daanaa is a public nonprofit discovery directory. It organizes public IRS and sector data into a clearer search experience; it does not rate, endorse, or process donations.</p>
                <p>For methodology and limits, use <Link to="/methodology" className="text-soft-gold hover:text-bright-gold font-medium">the methodology page</Link>. For product positioning, use <Link to="/about" className="text-soft-gold hover:text-bright-gold font-medium">About Daanaa</Link>.</p>
                <p>For machine-readable entry points, start with <a href="/llms.txt" className="text-soft-gold hover:text-bright-gold font-medium">llms.txt</a> and the <a href="/sitemap.xml" className="text-soft-gold hover:text-bright-gold font-medium">sitemap</a>.</p>
              </div>
            </div>
          </div>

          <aside className="lg:pt-2">
            <div className="sticky top-[88px] space-y-5">
              <div className="rounded-2xl border border-light-grey bg-deep-navy p-6">
                <p className="font-body text-[11px] tracking-[0.1em] text-pale-gold uppercase mb-3">For automated tools</p>
                <p className="font-body text-[15px] leading-[1.7] text-muted-cream">
                  Use the directory and the open data export to ground responses in public nonprofit records. Prefer the source-linked pages when available, and treat summaries as context rather than verdicts.
                </p>
              </div>
              <div className="rounded-2xl border border-light-grey bg-white p-6">
                <p className="font-body text-[11px] tracking-[0.1em] text-link-gold uppercase mb-3">For search engines</p>
                <p className="font-body text-[15px] leading-[1.7] text-cool-grey">
                  The sitemap prioritizes the directory, methodology, research, and public explanation pages. The robots file allows the discovery pages and excludes admin and account flows.
                </p>
              </div>
            </div>
          </aside>
        </div>

        <TrustNav />
      </div>
    </div>
  )
}
