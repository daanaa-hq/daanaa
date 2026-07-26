import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'

export default function Principles() {
  usePageMeta('Principles — Daanaa', 'How Daanaa makes decisions, protects independence, and remains accountable through stewardship and governance.')

  const commitments = [
    {
      title: 'We do not accept paid placement',
      description: 'Organizations cannot pay to appear higher in search results. Visibility is based on publicly available information and transparent methodologies, not advertising budgets.'
    },
    {
      title: 'We do not control donor funds',
      description: 'Donations do not pass through Daanaa. We link to an organization\'s own official website. Anyone who gives deals with the nonprofit directly. We never hold, process, or transfer charitable funds.'
    },
    {
      title: 'We do not sell donor activity',
      description: 'We do not build profiles based on giving behavior or encourage public displays of generosity. Giving is personal and should remain in the hands of the giver.'
    },
    {
      title: 'We remain independent',
      description: 'Daanaa accepts no paid placement, partner influence, or revenue sharing that would compromise information integrity.'
    },
    {
      title: 'We welcome corrections',
      description: 'Errors are corrected quickly and disclosed publicly. We treat the public record as a living resource that improves over time.'
    },
    {
      title: 'We protect privacy',
      description: 'User data is never tracked, shared, or sold. Your giving history stays on your device only.'
    },
  ]

  return (
    <div className="min-h-[100dvh]">
      <div className="bg-deep-navy pt-nav">
        <div className="max-w-[1120px] mx-auto px-6 md:px-12 pt-12 pb-10">
          <div className="flex items-center gap-2 mb-4">
            <Link to="/" className="font-body text-caption text-muted-cream">Home</Link>
            <span className="text-muted-cream">/</span>
            <span className="font-body text-caption text-muted-cream">Principles</span>
          </div>
          <h1 className="font-display italic text-warm-cream text-display md:text-display leading-[1.05]">Principles</h1>
          <p className="mt-4 font-body text-lead text-muted-cream max-w-[720px]">
            How we make decisions, protect independence, and care for donors, organizations, and the public record.
          </p>
        </div>
      </div>

      <div className="bg-warm-cream py-12 md:py-16">
        <div className="max-w-[1120px] mx-auto px-6 md:px-12">

          {/* Purpose */}
          <section className="max-w-[720px] mb-12">
            <h2 className="font-display text-deep-navy text-headline md:text-headline-lg leading-[1.15] mb-4">Our Purpose</h2>
            <div className="space-y-3 font-body text-body-lg text-cool-grey leading-[1.6]">
              <p className="font-medium text-deep-navy text-lead">
                Daanaa is a public directory of every active 501(c)(3) in America — including the 97% that go unseen — organized with financial context so giving is easy to understand, easy to record, and easy to return to.
              </p>
              <p>
                Independent of paid influence. Evidence-based from public IRS data. No ratings. Every organization benchmarked within its true peer group — with equal dignity for the small org doing extraordinary work as for the large one everyone has heard of.
              </p>
              <p>
                These principles are not policies written after the fact. They are the structure the platform is built on. Every decision we make is measured against them. If a feature, partnership, or opportunity does not serve that purpose, it does not belong.{' '}
                <Link to="/about" className="text-soft-gold hover:text-bright-gold font-medium">How we do it →</Link>
              </p>
            </div>
          </section>

          {/* Commitments Grid */}
          <section>
            <h2 className="font-display text-deep-navy text-headline md:text-headline-lg leading-[1.15] mb-8">Our Commitments</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {commitments.map(commitment => (
                <div key={commitment.title} className="bg-white border border-light-grey rounded-lg p-6">
                  <h3 className="font-display text-deep-navy text-title-sm mb-3">{commitment.title}</h3>
                  <p className="font-body text-body text-cool-grey leading-[1.6]">{commitment.description}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Learn more */}
          <div className="mt-12 pt-8 border-t border-light-grey">
            <p className="font-body text-caption font-semibold tracking-[0.08em] text-cool-grey uppercase mb-4">Learn more</p>
            <div className="flex flex-wrap gap-6">
              <Link to="/about" className="inline-flex items-center gap-2 font-body text-body text-soft-gold hover:text-bright-gold">
                About Daanaa →
              </Link>
              <Link to="/methodology" className="inline-flex items-center gap-2 font-body text-body text-soft-gold hover:text-bright-gold">
                Methodology →
              </Link>
              <Link to="/research" className="inline-flex items-center gap-2 font-body text-body text-soft-gold hover:text-bright-gold">
                Research & data →
              </Link>
              <Link to="/legal" className="inline-flex items-center gap-2 font-body text-body text-soft-gold hover:text-bright-gold">
                Privacy & Legal →
              </Link>
              <Link to="/feedback" className="inline-flex items-center gap-2 font-body text-body text-soft-gold hover:text-bright-gold">
                Contact →
              </Link>
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}
