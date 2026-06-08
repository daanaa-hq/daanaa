import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'

export default function Guides() {
  usePageMeta('Guides — Daanaa', 'Simple guides for thoughtful discovery and giving.')

  const guides = [
    {
      category: 'For donors',
      items: [
        { title: 'What is Daanaa?', to: '/faq#what-is-daanaa' },
        { title: 'How to use Peer Financial Context', to: '/methodology#peer-financial-context' },
        { title: 'What Lamp Tiers mean', to: '/methodology#lamp-tiers' },
        { title: 'How direct giving works', to: '/faq#direct-giving' },
      ]
    },
    {
      category: 'For nonprofits',
      items: [
        { title: 'Understanding your Lamp Tier', to: '/methodology#lamp-tiers' },
        { title: 'How to request corrections', to: '/feedback' },
        { title: 'Daanaa data sources', to: '/methodology#public-data-sources' },
      ]
    },
    {
      category: 'For researchers',
      items: [
        { title: 'How Daanaa uses public records', to: '/methodology' },
        { title: 'Data sources and limitations', to: '/methodology#data-limits' },
        { title: 'Peer Financial Context explained', to: '/methodology#peer-financial-context' },
      ]
    },
  ]

  return (
    <div className="min-h-[100dvh]">
      <div className="bg-deep-navy pt-[72px]">
        <div className="max-w-[1120px] mx-auto px-6 md:px-12 pt-16 pb-12">
          <div className="flex items-center gap-2 mb-6">
            <Link to="/" className="font-body text-[12px] text-muted-cream">Home</Link>
            <span className="text-muted-cream/40">/</span>
            <span className="font-body text-[12px] text-muted-cream">Guides</span>
          </div>
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-10 md:gap-16">
            <div className="max-w-[720px]">
              <h1 className="font-display italic text-warm-cream mt-3 text-[48px] md:text-[60px] leading-[1.05]">Guides</h1>
              <p className="mt-6 font-body text-[17px] text-muted-cream">Simple guides for thoughtful discovery and giving.</p>
            </div>
            <div className="shrink-0 hidden md:flex justify-end">
              <img src="/logo.png" alt="Daanaa" className="w-44 h-44 lg:w-52 lg:h-52 object-contain drop-shadow-[0_12px_48px_rgba(201,169,110,0.22)]" />
            </div>
          </div>
        </div>
      </div>

      <div className="bg-warm-cream py-16 md:py-20">
        <div className="max-w-[1120px] mx-auto px-6 md:px-12">

          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            {guides.map(group => (
              <div key={group.category}>
                <h2 className="font-display text-deep-navy text-[24px] mb-6">{group.category}</h2>
                <ul className="space-y-4">
                  {group.items.map(item => (
                    <li key={item.title}>
                      <Link to={item.to} className="font-body text-[16px] text-soft-gold hover:text-bright-gold transition-colors">
                        {item.title}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          <div className="mt-16 pt-12 border-t border-light-grey">
            <h2 className="font-display text-deep-navy text-[28px] mb-6">Can't find what you're looking for?</h2>
            <p className="font-body text-[16px] text-cool-grey leading-[1.65] max-w-[720px] mb-6">
              Check the <Link to="/faq" className="text-soft-gold hover:text-bright-gold">FAQ</Link> or <Link to="/feedback" className="text-soft-gold hover:text-bright-gold">contact us</Link>.
            </p>
          </div>

        </div>
      </div>
    </div>
  )
}
