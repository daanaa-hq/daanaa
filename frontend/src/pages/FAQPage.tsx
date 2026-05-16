import { useState } from 'react'
import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'

interface FAQItem {
  q: string
  a: React.ReactNode
}

const FAQS: { section: string; items: FAQItem[] }[] = [
  {
    section: 'About MERIT',
    items: [
      {
        q: 'Is MERIT free?',
        a: 'Yes — completely. MERIT is free to search, free to use, and free for nonprofits to claim their page. We do not charge for listings, scores, or access to any feature. We do not accept payments from organizations to influence their score or placement.',
      },
      {
        q: 'Who runs MERIT?',
        a: 'MERIT is an independent civic platform. We are not affiliated with the IRS, the federal government, or any existing nonprofit rating agency. We are not a nonprofit ourselves — we are infrastructure, built to make the charitable sector more legible.',
      },
      {
        q: 'How do you make money?',
        a: 'We are currently in public beta and not yet monetized. When we do generate revenue, it will come from institutional tools — not from listing fees, score manipulation, or selling donor data. Organizations will never pay to improve their scores.',
      },
      {
        q: 'Is my data private?',
        a: (
          <>
            Your Giving Wallet and saved organizations are stored locally on your device — they never leave your browser. We do not collect personal information from visitors, do not use tracking cookies, and do not sell or share user data. See our{' '}
            <Link to="/legal" className="text-soft-gold hover:text-bright-gold transition-colors">privacy policy</Link> for the full picture.
          </>
        ),
      },
    ],
  },
  {
    section: 'The MERIT Score',
    items: [
      {
        q: 'How is the MERIT score calculated?',
        a: 'The MERIT score is a peer percentile — not an absolute grade. We take each organization\'s financial data (primarily total revenue from IRS 990 filings), group it with true peers by NTEE subcategory and revenue band, and compute its rank within that group. A score of 72 means the organization outperforms 72% of its peers financially. The score does not measure mission, impact, or goodness of purpose.',
      },
      {
        q: 'What\'s the difference between the score and the trust tier?',
        a: (
          <>
            <p>They measure different things:</p>
            <ul className="mt-3 space-y-2">
              <li><strong className="text-deep-navy font-semibold">The MERIT score</strong> (0–100) answers: how does this organization compare financially to similar nonprofits?</li>
              <li><strong className="text-deep-navy font-semibold">The trust tier</strong> (Beacon → Spark) answers: how much public data backs this profile today?</li>
            </ul>
            <p className="mt-3">An organization can have a high score and a low tier (strong finances, but no public mission statement or website on record) — or vice versa. Read the{' '}<Link to="/tiers" className="text-soft-gold hover:text-bright-gold transition-colors">full tier reference</Link> for details.</p>
          </>
        ),
      },
      {
        q: 'Why doesn\'t my organization have a score?',
        a: 'A peer score requires enough financial data to rank within a peer group. If your organization files a 990-N (revenue under $50,000), no financial detail is submitted to the IRS — only a confirmation that you still exist. We can confirm your status but cannot compute a peer score. As your organization grows and files a full 990, a score will appear automatically on the next data refresh.',
      },
      {
        q: 'Can an organization pay to improve its score?',
        a: 'No. The MERIT score is computed directly from IRS public filings. It is auditable, reproducible, and cannot be influenced by any payment. Any platform that allows organizations to pay for better scores is not using verifiable public data.',
      },
      {
        q: 'My organization has a low score but we do great work. Why?',
        a: 'The score measures financial health relative to peers — not mission quality, impact, or importance. A neighborhood food pantry operating on $30,000 a year may do extraordinary work in its community and still score in the 40th percentile financially. The score is one signal. Read the mission, look at the programs, make your own judgment.',
      },
    ],
  },
  {
    section: 'Data & Accuracy',
    items: [
      {
        q: 'Where does MERIT\'s data come from?',
        a: (
          <>
            All data is sourced from public records: the IRS Business Master File (organization registration), IRS Form 990 XML filings (financial data and mission statements), and ProPublica Nonprofit Explorer (enriched 990 data). We do not create, modify, or supplement source data — we aggregate, normalize, and display it. See our{' '}<Link to="/legal" className="text-soft-gold hover:text-bright-gold transition-colors">full data attribution</Link>.
          </>
        ),
      },
      {
        q: 'How current is the financial data?',
        a: 'Form 990 filings are typically submitted 6–18 months after the fiscal year ends, and the IRS processes them on a rolling basis. The financial data on MERIT usually reflects the most recent 990 filed — which may be 1–3 years old depending on the organization. Every profile shows a "FY XXXX · Source" badge so you always know the vintage of the data you\'re looking at.',
      },
      {
        q: 'How often is MERIT updated?',
        a: (
          <ul className="space-y-2">
            {[
              { freq: 'Weekly', what: 'ProPublica enrichment for organizations with new 990 filings' },
              { freq: 'Monthly', what: 'IRS Statistics of Income extract download and ingestion' },
              { freq: 'Ongoing', what: 'Peer percentile recomputation after any bulk revenue update' },
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
            If the data shown is incorrect, the most likely explanation is that the IRS filing contains the error — in which case the correction needs to happen there first, and MERIT will pick it up on the next refresh. For claims or additions (mission statement, website, programs), you can claim your page when that feature launches. In the meantime, contact us at{' '}<a href="mailto:hello@meritgiving.org" className="text-soft-gold hover:text-bright-gold transition-colors">hello@meritgiving.org</a>.
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
            Claiming is in phased rollout. Join the waitlist on the{' '}<Link to="/for-nonprofits" className="text-soft-gold hover:text-bright-gold transition-colors">For Nonprofits</Link> page and we\'ll notify you when claiming opens for your organization. The process will be free and verification will use your organization\'s EIN and email domain.
          </>
        ),
      },
      {
        q: 'What can I add to my page once I claim it?',
        a: 'Claimed pages let organizations add: mission statement, program descriptions, leadership team, impact metrics, annual reports, and eventually events and volunteer opportunities. All self-reported content is clearly labeled as such and kept visually separate from IRS-sourced data — donors can always tell which is which.',
      },
      {
        q: 'My organization isn\'t listed on MERIT. Why?',
        a: 'MERIT indexes every IRS-recognized 501(c)(3) organization. If your organization isn\'t appearing, the most likely reasons are: your IRS recognition is recent (the BMF updates monthly — newly recognized orgs may take 30–60 days to appear), or your organization\'s status has lapsed. Search by EIN on the IRS Tax Exempt Organization Search to verify your status.',
      },
    ],
  },
  {
    section: 'Giving & Donations',
    items: [
      {
        q: 'Does MERIT process donations?',
        a: 'No. MERIT is a research and tracking tool — we help you find and research organizations. All actual giving happens directly with the nonprofit through their own website, by check, or by any other method you choose. MERIT logs your intent and keeps your record, but money never flows through us.',
      },
      {
        q: 'What is the Giving Wallet?',
        a: 'The Giving Wallet is a private, device-local donation log. You record gifts you\'ve made (through any channel), and the wallet stores them for reference at tax time. It\'s not connected to any payment processor. Think of it as a private spreadsheet that lives in your browser — useful for anyone who gives to multiple organizations and wants a single record.',
      },
      {
        q: 'What documentation do I need for a tax deduction?',
        a: (
          <>
            Under IRS rules: gifts under $250 require only a bank or card statement. Gifts of $250 or more require a written acknowledgment letter from the organization. MERIT\'s Giving Wallet helps you track what you\'ve given and to whom — but the letter must come from the nonprofit directly. See our{' '}<Link to="/guides" className="text-soft-gold hover:text-bright-gold transition-colors">giving guide on documentation</Link> for the full breakdown.
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
  usePageMeta('FAQ', 'Frequently asked questions about MERIT — how scores work, where data comes from, how to claim your nonprofit page, and how donations are tracked.')

  return (
    <div className="min-h-[100dvh]">
      {/* Header */}
      <div className="bg-deep-navy pt-[72px]">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12 pt-12 pb-16">
          <div className="flex items-center gap-2 mb-6">
            <Link to="/" className="font-body text-[12px] text-muted-cream hover:text-warm-cream transition-colors">Home</Link>
            <span className="text-muted-cream/50">/</span>
            <span className="font-body text-[12px] text-muted-cream">FAQ</span>
          </div>
          <h1 className="font-display italic text-warm-cream leading-[1.05] tracking-[-0.01em]" style={{ fontSize: 'clamp(32px, 5vw, 64px)' }}>
            Frequently asked questions
          </h1>
          <p className="mt-4 font-body text-[18px] leading-[1.6] text-muted-cream max-w-[560px]">
            Answers to the most common questions about MERIT, our data, and how giving works on this platform.
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
              We read every email. If something on MERIT doesn't make sense, we want to know.
            </p>
            <a
              href="mailto:hello@meritgiving.org"
              className="mt-6 inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-soft-gold text-deep-navy font-body text-[14px] font-semibold hover:bg-bright-gold transition-colors"
            >
              hello@meritgiving.org
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}
