import { useState } from 'react'
import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'

interface FAQItem {
  q: string
  a: React.ReactNode
}

const FAQS: { section: string; items: FAQItem[] }[] = [
  {
    section: 'About Daanaa',
    items: [
      {
        q: 'Is Daanaa free?',
        a: 'Yes, completely. Daanaa is free to search, free to use, and free for nonprofits to claim their page. We do not charge for listings, scores, or access to any feature. We do not accept payments from organizations to influence their score or placement.',
      },
      {
        q: 'Who runs Daanaa?',
        a: 'Daanaa is an independent platform. We are not affiliated with the IRS, the federal government, or any nonprofit rating agency. We are not a nonprofit ourselves. We\'re a free research tool that makes it easier to understand and explore the nonprofit sector.',
      },
      {
        q: 'How do you make money?',
        a: 'We are currently in public beta and not yet monetized. When we do generate revenue, it will come from institutional tools, never from listing fees, score manipulation, or selling donor data. Organizations will never pay to improve their scores.',
      },
      {
        q: 'Is my data private?',
        a: (
          <>
            Your Giving Wallet and saved organizations are stored locally on your device. They never leave your browser. We do not collect personal information from visitors, do not use tracking cookies, and do not sell or share user data. See our{' '}
            <Link to="/legal" className="text-soft-gold hover:text-bright-gold transition-colors">privacy policy</Link> for the full picture.
          </>
        ),
      },
    ],
  },
  {
    section: 'Peer Financial Context',
    items: [
      {
        q: 'How is peer financial context calculated?',
        a: (
          <>
            <p>Two signals together give the full financial picture:</p>
            <ul className="mt-3 space-y-2">
              <li><strong className="text-deep-navy font-semibold">Peer rank (0–100)</strong> — financial scale relative to similar organizations. A score of 72 means the organization is financially larger than 72% of comparable groups. It says nothing about how well the organization manages its resources.</li>
              <li><strong className="text-deep-navy font-semibold">Financial Health tier (Strong / Stable / Inspiring)</strong> — based on a weighted composite of program spending, reserves, revenue sustainability, and asset intensity. Always relative to true peers. An Inspiring organization is doing real work within real constraints — not a failure.</li>
            </ul>
            <p className="mt-3">Neither measures mission, impact, or whether an organization deserves support. See the full <Link to="/methodology" className="text-soft-gold hover:text-bright-gold transition-colors">methodology</Link> for the complete formula.</p>
          </>
        ),
      },
      {
        q: 'What\'s the difference between the visibility tier and Financial Health?',
        a: (
          <>
            <p>They measure different things:</p>
            <ul className="mt-3 space-y-2">
              <li><strong className="text-deep-navy font-semibold">Visibility tier</strong> (Spark → Beacon) answers: how much public data backs this profile today? It reflects what public records exist — mission, financials, website — not quality of work.</li>
              <li><strong className="text-deep-navy font-semibold">Financial Health</strong> (Strong / Stable / Inspiring) answers: how does this organization manage its resources compared to true peers — same operating model, similar revenue size?</li>
            </ul>
            <p className="mt-3">An organization can be a high-visibility Beacon and Inspiring financially. Or a low-visibility Spark and Strong financially. Neither tells you whether the work is good. Read the{' '}<Link to="/tiers" className="text-soft-gold hover:text-bright-gold transition-colors">full visibility tier reference</Link> for details.</p>
          </>
        ),
      },
      {
        q: 'Why doesn\'t my organization have a score?',
        a: 'A score needs enough financial data to compare an organization with its peers. Very small nonprofits (under $50,000 in revenue) file only a short confirmation with the government, with no financial detail. We can confirm they exist but can\'t rank them. Once they grow and file a full report, a score appears automatically.',
      },
      {
        q: 'Can an organization pay to improve its score?',
        a: 'No. The score comes directly from government public records and cannot be influenced by any payment. Any platform that lets organizations pay for a better score is not using real data.',
      },
      {
        q: 'My organization has an Inspiring Financial Health tier. Why?',
        a: 'Financial Health reflects where your organization sits on a weighted composite of four metrics — program spending, reserves, revenue sustainability, and asset intensity — compared to true peers at the same operating model and revenue size. Inspiring means constrained resources relative to that peer group. It is not a verdict on your work, your mission, or your community impact. A neighborhood food pantry operating on $30,000 a year may do extraordinary work and still be Inspiring relative to other food pantries in its revenue band. Read the mission. Look at the programs. Make your own judgment.',
      },
    ],
  },
  {
    section: 'Data & Accuracy',
    items: [
      {
        q: 'Where does Daanaa\'s data come from?',
        a: (
          <>
            All data comes from public records: the IRS nonprofit registration list, IRS annual financial reports, and ProPublica's nonprofit database. We do not create, modify, or supplement source data. We organize and display it. See our{' '}<Link to="/legal" className="text-soft-gold hover:text-bright-gold transition-colors">full data attribution</Link>.
          </>
        ),
      },
      {
        q: 'How current is the financial data?',
        a: 'Financial reports are usually filed 6 to 18 months after the year ends, and the government processes them gradually. What you see on Daanaa is typically 1 to 3 years old depending on the organization. Every profile shows the year the data is from so you always know.',
      },
      {
        q: 'How often is Daanaa updated?',
        a: (
          <ul className="space-y-2">
            {[
              { freq: 'Monthly', what: 'New financial reports added as the IRS and ProPublica publish them' },
              { freq: 'Monthly', what: 'IRS tax-exempt status checked against the federal auto-revocation list' },
              { freq: 'Ongoing', what: 'Rankings updated whenever new data comes in' },
            ].map(({ freq, what }) => (
              <li key={freq} className="flex gap-3">
                <span className="shrink-0 font-semibold text-soft-gold w-16">{freq}</span>
                <span>{what}</span>
              </li>
            ))}
          </ul>
        ),
      },
      {
        q: 'The information about my organization is wrong. What can I do?',
        a: (
          <>
            If the data shown is incorrect, the most likely explanation is that the IRS filing contains the error, in which case the correction needs to happen there first, and Daanaa will pick it up on the next refresh. For claims or additions (mission statement, website, programs), you can claim your page when that feature launches. In the meantime, report a data issue at{' '}<a href="mailto:trust@daanaa.org" className="text-soft-gold hover:text-bright-gold transition-colors">trust@daanaa.org</a>.
          </>
        ),
      },
    ],
  },
  {
    section: 'For Nonprofits',
    items: [
      {
        q: 'How do I claim my organization\'s page?',
        a: (
          <>
            Claiming is open now and free. Go to your organization's profile, click "Claim this page," enter your EIN and email, and we mail a verification letter to your IRS-registered postal address. The letter contains a QR code and a 6-digit PIN — scan or enter it to unlock your profile editor. The whole process takes 3 to 5 business days for the letter to arrive. Visit the{' '}<Link to="/for-nonprofits" className="text-soft-gold hover:text-bright-gold transition-colors">For Nonprofits</Link> page for details.
          </>
        ),
      },
      {
        q: 'What can I add to my page once I claim it?',
        a: 'Claimed pages let organizations add a mission statement, program descriptions, leadership team, impact numbers, and documents. Everything you add is clearly labeled as written by you and kept visually separate from the government data, so donors always know which is which.',
      },
      {
        q: 'My organization isn\'t listed on Daanaa. Why?',
        a: 'Daanaa lists every tax-deductible 501(c)(3) organization the IRS recognizes. If your organization isn\'t appearing, the most likely reasons are that your IRS recognition is recent (the IRS list updates monthly, so newly recognized organizations may take 30 to 60 days to appear), or your organization\'s status has lapsed. Daanaa does not list 501(c)(4), 501(c)(6), or other nonprofit types where donations are not tax-deductible. Search on the IRS Tax Exempt Organization Search to verify your status.',
      },
    ],
  },
  {
    section: 'Giving & Donations',
    items: [
      {
        q: 'Does Daanaa process donations?',
        a: 'No. Daanaa is a research and tracking tool that helps you find and research organizations. All actual giving happens directly with the nonprofit through their own website, by check, or by any other method you choose. Daanaa logs your intent and keeps your record, but money never flows through us.',
      },
      {
        q: 'What is the Giving Wallet?',
        a: 'The Giving Wallet is a private donation tracker stored in your browser. You record gifts you\'ve made (through any channel), and the wallet keeps them for reference at tax time. It\'s not connected to any payment processor. Think of it as a private notebook for anyone who gives to multiple organizations and wants a single record.',
      },
      {
        q: 'What documentation do I need for a tax deduction?',
        a: (
          <>
            Under IRS rules: gifts under $250 require only a bank or card statement. Gifts of $250 or more require a written acknowledgment letter from the organization. Daanaa\'s Giving Wallet helps you track what you\'ve given and to whom, but the letter must come from the nonprofit directly. See our{' '}<Link to="/guides" className="text-soft-gold hover:text-bright-gold transition-colors">giving guide on documentation</Link> for the full breakdown.
          </>
        ),
      },
    ],
  },
]

function FAQAccordion({ item }: { item: FAQItem }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="border-b border-light-grey last:border-0">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-start justify-between gap-6 py-5 text-left"
      >
        <span className="font-body text-[15px] font-medium text-deep-navy leading-[1.5]">{item.q}</span>
        <span
          className="shrink-0 w-5 h-5 flex items-center justify-center transition-transform duration-200"
          style={{ transform: open ? 'rotate(45deg)' : 'rotate(0deg)' }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
        </span>
      </button>
      {open && (
        <div className="pb-5 font-body text-[15px] text-cool-grey leading-[1.7] space-y-3 pr-8">
          {typeof item.a === 'string' ? <p>{item.a}</p> : item.a}
        </div>
      )}
    </div>
  )
}

export default function FAQPage() {
  usePageMeta('FAQ', 'Frequently asked questions about Daanaa. How scores work, where data comes from, how to claim your nonprofit page, and how donations are tracked.')

  return (
    <div className="min-h-[100dvh]">
      {/* Header */}
      <div className="bg-deep-navy pt-[72px]">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12 pt-8 pb-10 md:pt-12 md:pb-16">
          <div className="flex items-center gap-2 mb-6">
            <Link to="/" className="font-body text-[12px] text-muted-cream hover:text-warm-cream transition-colors">Home</Link>
            <span className="text-muted-cream/50">/</span>
            <span className="font-body text-[12px] text-muted-cream">FAQ</span>
          </div>
          <h1 className="font-display italic text-warm-cream leading-[1.05] tracking-[-0.01em]" style={{ fontSize: 'clamp(32px, 5vw, 64px)' }}>
            Frequently asked questions
          </h1>
          <p className="mt-4 font-body text-[18px] leading-[1.6] text-muted-cream max-w-[560px]">
            Answers to the most common questions about Daanaa, our data, and how giving works on this platform.
          </p>
        </div>
      </div>

      {/* Content */}
      <div className="bg-warm-cream">
        <div className="max-w-[860px] mx-auto px-6 lg:px-12 py-12">
          <div className="space-y-12">
            {FAQS.map(({ section, items }) => (
              <div key={section}>
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-6 h-px bg-soft-gold/50" />
                  <span className="font-body text-[11px] font-medium tracking-[0.10em] text-soft-gold uppercase">{section}</span>
                </div>
                <div className="bg-white rounded-2xl border border-light-grey px-6 divide-y divide-light-grey">
                  {items.map(item => (
                    <FAQAccordion key={item.q} item={item} />
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Still have questions */}
          <div className="mt-14 p-8 bg-deep-navy rounded-2xl text-center">
            <h3 className="font-display italic text-warm-cream text-[24px]">Still have a question?</h3>
            <p className="mt-3 font-body text-[15px] text-muted-cream leading-[1.6] max-w-[400px] mx-auto">
              We read every email. If something on Daanaa doesn't make sense, we want to know.
            </p>
            <a
              href="mailto:hello@daanaa.org"
              className="mt-6 inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-soft-gold text-deep-navy font-body text-[14px] font-semibold hover:bg-bright-gold transition-colors"
            >
              hello@daanaa.org
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}
