import { Link } from 'react-router-dom'
import { useState } from 'react'
import { usePageMeta } from '../hooks/usePageMeta'
import { useJsonLd, faqPageSchema } from '../hooks/useJsonLd'

export default function FAQ() {
  usePageMeta('FAQ — Daanaa', {
    description: 'Answers about Daanaa, nonprofit discovery, public records, Peer Financial Context, Lamp Tiers, and direct giving.',
    ogImage: 'https://daanaa.org/og-image-v2.png',
  })
  const [open, setOpen] = useState<number | null>(0)

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

  useJsonLd(faqPageSchema(faqs.map(faq => ({ question: faq.q, answer: faq.a }))))

  return (
    <div className="min-h-[100dvh]">
      <div className="bg-deep-navy pt-[72px]">
        <div className="max-w-[1120px] mx-auto px-6 md:px-12 pt-16 pb-12">
          <div className="flex items-center gap-2 mb-6">
            <Link to="/" className="font-body text-[12px] text-muted-cream">Home</Link>
            <span className="text-muted-cream">/</span>
            <span className="font-body text-[12px] text-muted-cream">FAQ</span>
          </div>
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-10 md:gap-16">
            <div className="max-w-[720px]">
              <h1 className="font-display italic text-warm-cream mt-3 text-[48px] md:text-[60px] leading-[1.05]">FAQ</h1>
              <p className="mt-6 font-body text-[17px] text-muted-cream">Common questions about Daanaa, public records, discovery, and giving.</p>
            </div>
            <div className="shrink-0 hidden md:flex justify-end">
              <img src="/logo.png" alt="Daanaa" className="w-44 h-44 lg:w-52 lg:h-52 object-contain drop-shadow-[0_12px_48px_rgba(201,169,110,0.22)]" />
            </div>
          </div>
        </div>
      </div>

      <div className="bg-warm-cream py-16 md:py-20">
        <div className="max-w-[800px] mx-auto px-6 md:px-12">
          <div className="space-y-4">
            {faqs.map((faq, i) => (
              <div key={i} className="border border-light-grey rounded-xl overflow-hidden bg-white">
                <button
                  onClick={() => setOpen(open === i ? null : i)}
                  className="w-full px-6 py-5 flex items-center justify-between hover:bg-warm-cream/50 transition-colors text-left"
                >
                  <p className="font-body text-[16px] font-semibold text-deep-navy">{faq.q}</p>
                  <svg className={`w-5 h-5 shrink-0 text-soft-gold transition-transform ${open === i ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <polyline points="6 9 12 15 18 9"></polyline>
                  </svg>
                </button>
                {open === i && (
                  <div className="px-6 py-4 border-t border-light-grey bg-warm-cream/30">
                    <p className="font-body text-[15px] text-cool-grey leading-[1.65]">{faq.a}</p>
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className="mt-16 pt-12 border-t border-light-grey">
            <p className="font-body text-[14px] text-cool-grey leading-[1.65]">
              Still have questions? <Link to="/feedback" className="text-soft-gold hover:text-bright-gold font-semibold">Contact us</Link> or check out our <Link to="/guides" className="text-soft-gold hover:text-bright-gold font-semibold">guides</Link>.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
