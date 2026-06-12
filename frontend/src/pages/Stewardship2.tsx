import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'

export default function Stewardship() {
  usePageMeta('Stewardship — Daanaa', 'See the principles that guide how Daanaa presents public information, handles uncertainty, and supports thoughtful discovery.')

  return (
    <div className="min-h-[100dvh]">
      <div className="bg-deep-navy pt-[72px]">
        <div className="max-w-[1120px] mx-auto px-6 md:px-12 pt-16 pb-12">
          <div className="flex items-center gap-2 mb-6">
            <Link to="/" className="font-body text-[12px] text-muted-cream hover:text-warm-cream transition-colors">Home</Link>
            <span className="text-muted-cream">/</span>
            <span className="font-body text-[12px] text-muted-cream">Stewardship</span>
          </div>
          <h1 className="font-display italic text-warm-cream mt-3 leading-[1.05] tracking-[-0.01em]" style={{ fontSize: 'clamp(40px, 5vw, 60px)' }}>
            Stewardship
          </h1>
          <p className="mt-6 font-body text-[17px] leading-[1.65] text-muted-cream max-w-[720px]">
            Stewardship means caring for donors, organizations, and the public record at the same time.
          </p>
        </div>
      </div>

      <div className="bg-warm-cream py-16 md:py-20">
        <div className="max-w-[1120px] mx-auto px-6 md:px-12">

          <div className="max-w-[720px] mb-16">
            <p className="font-body text-[16px] text-cool-grey leading-[1.65]">
              Daanaa is built to support discovery without turning giving into judgment. These principles guide how information is presented, how uncertainty is handled, and how corrections are welcomed.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {[
              {
                title: 'We do not rank nonprofits',
                practice: 'We avoid language that implies one organization is "better" or "stronger" than another. Context matters more than ranking.'
              },
              {
                title: 'We do not process donations',
                practice: 'Donations never pass through Daanaa. When available, we link to the organization\'s own official website.'
              },
              {
                title: 'We do not sell donor data',
                practice: 'We do not build profiles based on giving behavior, and we do not encourage public displays of generosity.'
              },
              {
                title: 'We remain independent',
                practice: 'Daanaa accepts no paid placement, partner influence, or revenue sharing that would compromise information integrity.'
              },
              {
                title: 'We welcome corrections',
                practice: 'Errors are corrected quickly and disclosed publicly. We treat the public record as a living resource that improves over time.'
              },
              {
                title: 'We protect privacy',
                practice: 'User data is never tracked, shared, or sold. Your giving history stays on your device only.'
              },
            ].map(principle => (
              <div key={principle.title} className="bg-white border border-light-grey rounded-2xl p-8">
                <h3 className="font-display text-deep-navy text-[20px]">{principle.title}</h3>
                <p className="mt-4 font-body text-[15px] text-cool-grey leading-[1.65]">{principle.practice}</p>
              </div>
            ))}
          </div>

          <div className="mt-16 pt-12 border-t border-light-grey">
            <p className="font-body text-[11px] font-semibold tracking-[0.08em] text-cool-grey uppercase mb-4">Related</p>
            <div className="flex flex-wrap gap-4">
              <Link to="/methodology" className="inline-flex items-center gap-2 font-body text-[14px] text-soft-gold hover:text-bright-gold">Methodology →</Link>
              <Link to="/privacy" className="inline-flex items-center gap-2 font-body text-[14px] text-soft-gold hover:text-bright-gold">Privacy →</Link>
              <Link to="/feedback" className="inline-flex items-center gap-2 font-body text-[14px] text-soft-gold hover:text-bright-gold">Contact →</Link>
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}
