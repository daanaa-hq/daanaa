import { useState } from 'react'

interface FAQItem {
  question: string
  answer: string
  icon?: string
}

const faqItems: FAQItem[] = [
  {
    question: 'How does volunteer approval work?',
    icon: '✓',
    answer: `Volunteers log hours at your events using the QR code. Their submission appears in your approval dashboard as "Pending." You review the submission and click "Approve" or "Reject." Approved hours count toward your organization's public volunteer impact. You have 30 days to edit or reject after approval.`
  },
  {
    question: 'What information do donors want to see?',
    icon: '💡',
    answer: `Donors want to understand: (1) What your mission is—what problem you solve, (2) What programs you run—what you actually do, (3) How they can help—donate link or volunteer, (4) Where you work—geographic area. Fill these four fields and your profile is 100% complete.`
  },
  {
    question: 'How long until my profile changes appear?',
    icon: '⏱️',
    answer: `Changes appear to donors within 5 minutes of you clicking "Save." No approval needed—you control when your information updates. This is your organization's data, so edits are published immediately.`
  },
  {
    question: 'What if I make a mistake after approving hours?',
    icon: '🔧',
    answer: `You can reject hours within 30 days of approval. Once 30 days have passed, approved hours are locked (this prevents retroactive changes). If you need to correct something after 30 days, reach out to Daanaa support.`
  },
  {
    question: 'How is my financial context score calculated?',
    icon: '📊',
    answer: `Your Financial Health score shows how financially stable you are compared to similar-sized organizations in your sector. It comes from your IRS Form 990 data (public record). We never manually adjust scores—they're calculated from the data. If your data changes, your score updates automatically.`
  },
  {
    question: 'Can I mark information as private or request removal?',
    icon: '🔒',
    answer: `All information shown on your profile is public record (from IRS 990 filings or data you provide). You can update nonprofit-supplied information anytime. If you believe information is inaccurate, use the "Report an Issue" button on your profile to request a correction.`
  },
  {
    question: 'How do I get more volunteer sign-ups?',
    icon: '👥',
    answer: `Create events in your events dashboard and share the QR code or volunteer link. Make sure your profile is complete—donors check your mission and programs before volunteering. The clearer your description, the more aligned volunteers you'll attract.`
  },
  {
    question: 'What does "nonprofit-supplied" vs "IRS" mean?',
    icon: '📋',
    answer: `"IRS" = official public records from your Form 990 filing. "Nonprofit-supplied" = information you added or corrected. "AI-generated" = Daanaa created (usually summaries). "Corrected" = Daanaa fixed an error. Donors see all sources so they understand where data comes from.`
  }
]

interface HelpModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function HelpModal({ isOpen, onClose }: HelpModalProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null)

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" role="presentation">
      <div className="bg-white rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto shadow-lg">
        {/* Header */}
        <div className="sticky top-0 bg-warm-cream border-b border-light-grey px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="font-display text-2xl text-deep-navy">Help & FAQ</h2>
            <p className="font-body text-caption text-cool-grey mt-1">Common questions about managing your nonprofit</p>
          </div>
          <button
            onClick={onClose}
            className="flex-shrink-0 text-cool-grey hover:text-deep-navy text-2xl leading-none transition hover:bg-light-grey/30 rounded-lg p-1"
            aria-label="Close help modal"
          >
            ×
          </button>
        </div>

        {/* FAQ Items */}
        <div className="px-6 py-6 space-y-3">
          {faqItems.map((item, idx) => (
            <div
              key={idx}
              className="border border-light-grey rounded-xl overflow-hidden hover:border-soft-gold/50 transition"
              role="region"
              aria-label={`FAQ item: ${item.question}`}
            >
              <button
                onClick={() => setExpandedIndex(expandedIndex === idx ? null : idx)}
                className="w-full p-4 flex items-start gap-3 hover:bg-warm-cream/50 transition text-left"
                aria-expanded={expandedIndex === idx}
                aria-controls={`faq-answer-${idx}`}
              >
                <span className="text-xl flex-shrink-0 mt-0.5" aria-hidden="true">
                  {item.icon || '❓'}
                </span>
                <div className="flex-1">
                  <h3 className="font-display text-body-lg text-deep-navy font-semibold">
                    {item.question}
                  </h3>
                  <span
                    className="font-body text-caption text-cool-grey inline-block mt-1"
                    aria-hidden={expandedIndex !== idx}
                  >
                    {expandedIndex === idx ? '−' : '+'}
                  </span>
                </div>
                <span
                  className="text-soft-gold text-lg flex-shrink-0 transition"
                  aria-hidden="true"
                >
                  {expandedIndex === idx ? '▲' : '▼'}
                </span>
              </button>

              {expandedIndex === idx && (
                <div
                  id={`faq-answer-${idx}`}
                  className="px-4 pb-4 border-t border-light-grey/50 bg-white"
                  role="region"
                >
                  <p className="font-body text-body text-deep-navy leading-relaxed">
                    {item.answer}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-warm-cream border-t border-light-grey px-6 py-4 flex gap-3 justify-end">
          <button
            onClick={onClose}
            className="px-6 py-2.5 rounded-lg bg-soft-gold text-deep-navy font-body text-body font-semibold hover:bg-bright-gold transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
