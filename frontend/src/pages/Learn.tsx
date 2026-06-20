import { Link, useSearchParams } from 'react-router-dom'
import { useState } from 'react'
import { usePageMeta } from '../hooks/usePageMeta'

export default function Learn() {
  usePageMeta('Learn — Daanaa', 'Guides and FAQs about Daanaa, nonprofit discovery, Peer Financial Context, and Lamp Tiers.')
  const [searchParams, setSearchParams] = useSearchParams()
  const [openFaq, setOpenFaq] = useState<number | null>(0)

  const tab = searchParams.get('tab') || 'guides'

  const faqs = [
    {
      q: 'What is Daanaa?',
      a: 'Daanaa is an independent nonprofit discovery platform that helps people discover causes and organizations using public information presented with context, stewardship, and respect.'
    },
    {
      q: 'Is Daanaa a rating agency?',
      a: 'No. Daanaa does not rate, rank, endorse, or recommend nonprofits. We organize public information to add context to giving decisions, which is different from rating.'
    },
    {
      q: 'What is Peer Financial Context?',
      a: 'Peer Financial Context shows public financial information within comparable peer groups. It is designed to add context, not to rate, rank, or recommend organizations.'
    },
    {
      q: 'What are Lamp Tiers?',
      a: 'Lamp Tiers are visibility indicators based on public information completeness and availability. They are not ratings. They reflect how much public context Daanaa can show.'
    },
    {
      q: 'Does Daanaa process donations?',
      a: 'No. When available, Daanaa links to an organization\'s own official website. Donations never pass through our platform, and we never collect donor payment information.'
    },
    {
      q: 'Is Daanaa affiliated with the IRS?',
      a: 'No. Daanaa.org is independent and is not affiliated with the IRS, the federal government, or any nonprofit rating agency.'
    },
    {
      q: 'Can organizations request corrections?',
      a: 'Yes. Organizations and visitors can report data issues through our feedback form. We correct errors quickly and disclose corrections publicly.'
    },
  ]

  const guides = [
    {
      category: 'For donors',
      items: [
        { title: 'What is Daanaa?', to: '/learn?tab=faq#what-is-daanaa' },
        { title: 'How to use Peer Financial Context', to: '/methodology#peer-financial-context' },
        { title: 'What Lamp Tiers mean', to: '/methodology#lamp-tiers' },
        { title: 'How direct giving works', to: '/learn?tab=faq#does-daanaa' },
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
        <div className="max-w-[1120px] mx-auto px-6 md:px-12 pt-12 pb-10">
          <div className="flex items-center gap-2 mb-4">
            <Link to="/" className="font-body text-[12px] text-muted-cream">Home</Link>
            <span className="text-muted-cream">/</span>
            <span className="font-body text-[12px] text-muted-cream">Learn</span>
          </div>
          <h1 className="font-display italic text-warm-cream text-[42px] md:text-[52px] leading-[1.05]">Learn</h1>
          <p className="mt-4 font-body text-[16px] text-muted-cream max-w-[600px]">
            Guides and answers about nonprofit discovery, Peer Financial Context, and Lamp Tiers.
          </p>
        </div>
      </div>

      <div className="bg-warm-cream py-12 md:py-16">
        <div className="max-w-[1120px] mx-auto px-6 md:px-12">
          {/* Tabs */}
          <div className="flex gap-8 border-b border-light-grey mb-12">
            <button
              onClick={() => setSearchParams({ tab: 'guides' })}
              className={`pb-3 font-body text-[15px] font-medium transition-colors ${
                tab === 'guides'
                  ? 'text-deep-navy border-b-2 border-deep-navy'
                  : 'text-cool-grey hover:text-deep-navy'
              }`}
            >
              Guides
            </button>
            <button
              onClick={() => setSearchParams({ tab: 'faq' })}
              className={`pb-3 font-body text-[15px] font-medium transition-colors ${
                tab === 'faq'
                  ? 'text-deep-navy border-b-2 border-deep-navy'
                  : 'text-cool-grey hover:text-deep-navy'
              }`}
            >
              Questions
            </button>
          </div>

          {/* Guides Tab */}
          {tab === 'guides' && (
            <div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {guides.map(group => (
                  <div key={group.category}>
                    <h2 className="font-display text-deep-navy text-[20px] mb-4">{group.category}</h2>
                    <ul className="space-y-2.5">
                      {group.items.map(item => (
                        <li key={item.title}>
                          <Link to={item.to} className="font-body text-[15px] text-soft-gold hover:text-bright-gold transition-colors">
                            {item.title}
                          </Link>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* FAQ Tab */}
          {tab === 'faq' && (
            <div>
              <div className="max-w-[800px] space-y-3">
                {faqs.map((faq, i) => (
                  <div key={i} className="border border-light-grey rounded-lg overflow-hidden bg-white">
                    <button
                      onClick={() => setOpenFaq(openFaq === i ? null : i)}
                      className="w-full px-5 py-4 flex items-center justify-between hover:bg-warm-cream/40 transition-colors text-left"
                    >
                      <p className="font-body text-[15px] font-semibold text-deep-navy">{faq.q}</p>
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
              <div className="mt-10 pt-8 border-t border-light-grey max-w-[800px]">
                <p className="font-body text-[14px] text-cool-grey leading-[1.6]">
                  Still have questions? <Link to="/feedback" className="text-soft-gold hover:text-bright-gold font-semibold">Contact us</Link>.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
