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
      description: 'Donations do not pass through Daanaa. We link to an organization\'s own official website. Anyone who gives deals with the nonprofit directly—we never hold, process, or transfer charitable funds.'
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
      <div className="bg-deep-navy pt-[72px]">
        <div className="max-w-[1120px] mx-auto px-6 md:px-12 pt-12 pb-10">
          <div className="flex items-center gap-2 mb-4">
            <Link to="/" className="font-body text-[12px] text-muted-cream">Home</Link>
            <span className="text-muted-cream">/</span>
            <span className="font-body text-[12px] text-muted-cream">Principles</span>
          </div>
          <h1 className="font-display italic text-warm-cream text-[42px] md:text-[52px] leading-[1.05]">Principles</h1>
          <p className="mt-4 font-body text-[16px] text-muted-cream max-w-[720px]">
            How we make decisions, protect independence, and care for donors, organizations, and the public record.
          </p>
        </div>
      </div>

      <div className="bg-warm-cream py-12 md:py-16">
        <div className="max-w-[1120px] mx-auto px-6 md:px-12">

          {/* Purpose */}
          <section className="max-w-[720px] mb-12">
            <h2 className="font-display text-deep-navy text-[26px] md:text-[30px] leading-[1.15] mb-4">Our Purpose</h2>
            <div className="space-y-3 font-body text-[15px] text-cool-grey leading-[1.6]">
              <p>
                Daanaa exists to help people discover causes they care about and support them with confidence.
              </p>
              <p>
                Every decision we make is measured against that purpose. If a feature, partnership, or opportunity does not help people make informed giving decisions, it does not belong.
              </p>
            </div>
          </section>

          {/* Commitments Grid */}
          <section>
            <h2 className="font-display text-deep-navy text-[26px] md:text-[30px] leading-[1.15] mb-8">Our Commitments</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {commitments.map(commitment => (
                <div key={commitment.title} className="bg-white border border-light-grey rounded-lg p-6">
                  <h3 className="font-display text-deep-navy text-[18px] mb-3">{commitment.title}</h3>
                  <p className="font-body text-[14px] text-cool-grey leading-[1.6]">{commitment.description}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Learn more */}
          <div className="mt-12 pt-8 border-t border-light-grey">
            <p className="font-body text-[12px] font-semibold tracking-[0.08em] text-cool-grey uppercase mb-4">Learn more</p>
            <div className="flex flex-wrap gap-6">
              <Link to="/methodology" className="inline-flex items-center gap-2 font-body text-[14px] text-soft-gold hover:text-bright-gold">
                Methodology →
              </Link>
              <Link to="/legal" className="inline-flex items-center gap-2 font-body text-[14px] text-soft-gold hover:text-bright-gold">
                Privacy & Legal →
              </Link>
              <Link to="/feedback" className="inline-flex items-center gap-2 font-body text-[14px] text-soft-gold hover:text-bright-gold">
                Contact →
              </Link>
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}
