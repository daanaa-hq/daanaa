import { useState } from 'react'
import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import { useApi } from '../hooks/useApi'
import { getStats, getGuildMemberCount, getGuildBenefits } from '../data/api'

const ALL_CATEGORIES = [
  'Insurance',
  'Printing and marketing',
  'Travel and fuel',
  'Food and catering',
  'Software and technology',
  'Office supplies and shipping',
  'Legal and compliance',
  'Accounting and bookkeeping',
  'Staffing and HR',
  'Design and creative',
  'Construction and facilities',
  'Health and wellness',
  'Training and education',
  'Other',
]

// ─── Community partner form ──────────────────────────────────────────────────

type ServiceReach = 'local' | 'regional' | 'multi_state' | 'online'

const REACH_OPTIONS: { value: ServiceReach; label: string; hint: string }[] = [
  { value: 'local',       label: 'My city or neighborhood',     hint: 'A few miles radius. I know my customers by name.' },
  { value: 'regional',    label: 'Metro area or multiple counties', hint: 'A region, a metro, a cluster of cities' },
  { value: 'multi_state', label: 'Multiple states',             hint: 'Physical presence or clients across several states' },
  { value: 'online',      label: 'Online, works with anyone',   hint: 'Software, consulting, remote services. No geography required.' },
]

function ServiceReachSelector({
  value, onChange,
}: {
  value: ServiceReach
  onChange: (v: ServiceReach) => void
}) {
  return (
    <div>
      <span className="block font-body text-small font-medium text-deep-navy mb-2">
        How do you serve nonprofits?
      </span>
      <div className="grid sm:grid-cols-2 gap-2">
        {REACH_OPTIONS.map(opt => (
          <label
            key={opt.value}
            className={`flex gap-3 p-3 rounded-xl border cursor-pointer transition-colors ${
              value === opt.value
                ? 'border-soft-gold bg-soft-gold/8'
                : 'border-light-grey bg-white hover:border-soft-gold/40'
            }`}
          >
            <input
              type="radio"
              name="service_reach"
              value={opt.value}
              checked={value === opt.value}
              onChange={() => onChange(opt.value)}
              className="mt-0.5 accent-[#C9A96E] shrink-0"
            />
            <div>
              <p className="font-body text-small font-semibold text-deep-navy leading-tight">{opt.label}</p>
              <p className="font-body text-caption text-cool-grey mt-0.5">{opt.hint}</p>
            </div>
          </label>
        ))}
      </div>
    </div>
  )
}

function CommunityPartnerForm({ onGateToNetwork }: { onGateToNetwork: () => void }) {
  const [form, setForm] = useState({
    business_name: '', category: ALL_CATEGORIES[0], offer: '',
    location_city: '', location_state: '', location_country: '',
    service_area_type: 'local' as ServiceReach,
    contact_email: '', contact_phone: '', website_url: '',
    submitter_name: '', submitter_email: '', notes: '',
  })
  const [sending, setSending] = useState(false)
  const [sent, setSent] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function set(field: string) {
    return (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
      setForm(f => ({ ...f, [field]: e.target.value }))
  }

  const isRemote = form.service_area_type === 'online' || form.service_area_type === 'multi_state'

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setSending(true)
    try {
      const res = await fetch('/api/guild/community-partner', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })
      const body = await res.json()
      if (!res.ok) { setError(body.error || 'Something went wrong.'); setSending(false); return }
      setSent(true)
    } catch {
      setError('Could not reach the server. Email us at partners@daanaa.org.')
      setSending(false)
    }
  }

  if (sent) return (
    <div className="text-center py-8">
      <div className="w-12 h-12 rounded-full bg-soft-gold/15 mx-auto mb-4 flex items-center justify-center">
        <svg width="20" height="16" viewBox="0 0 20 16" fill="none">
          <path d="M1 8L7 14L19 1" stroke="#C9A96E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </div>
      <h3 className="font-display italic text-title-lg text-deep-navy mb-2">You're in the network</h3>
      <p className="font-body text-body text-cool-grey leading-[1.7] max-w-[400px] mx-auto">
        We review every application and reply from{' '}
        <a href="mailto:partners@daanaa.org" className="text-soft-gold hover:underline">partners@daanaa.org</a>.
        Once approved, your listing goes live in the Daanaa community directory.
      </p>
    </div>
  )

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="p-4 bg-destructive/5 border border-destructive/20 rounded-xl">
          <p className="font-body text-body text-destructive">{error}</p>
        </div>
      )}

      <ServiceReachSelector
        value={form.service_area_type}
        onChange={v => setForm(f => ({ ...f, service_area_type: v }))}
      />

      {/* Soft nudge for multi-state/online — no wall, just an option */}
      {isRemote && (
        <div className="flex items-start gap-3 bg-deep-navy/[0.04] border border-light-grey rounded-xl px-4 py-3">
          <span className="shrink-0 mt-0.5 text-soft-gold">◆</span>
          <p className="font-body text-small text-cool-grey leading-[1.6]">
            Community partner works great for online businesses and those serving across multiple states.
            If you want a formal contract, a shared code for all members, and milestone pricing,{' '}
            <button type="button" onClick={onGateToNetwork}
              className="text-soft-gold hover:underline font-medium">
              the network partner path
            </button>{' '}
            might be the right fit. Either way, you're welcome in this community.
          </p>
        </div>
      )}

      <div className="grid sm:grid-cols-2 gap-4">
        <label className="block">
          <span className="block font-body text-small font-medium text-deep-navy mb-1.5">Business name</span>
          <input type="text" value={form.business_name} onChange={set('business_name')} required
            className="w-full px-4 py-2.5 border border-light-grey rounded-xl font-body text-body text-deep-navy focus:outline-none focus:ring-2 focus:ring-soft-gold" />
        </label>
        <label className="block">
          <span className="block font-body text-small font-medium text-deep-navy mb-1.5">Category</span>
          <select value={form.category} onChange={set('category')}
            className="w-full px-4 py-2.5 border border-light-grey rounded-xl font-body text-body text-deep-navy bg-white focus:outline-none focus:ring-2 focus:ring-soft-gold">
            {ALL_CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </label>
      </div>
      <label className="block">
        <span className="block font-body text-small font-medium text-deep-navy mb-1.5">What you offer nonprofit members</span>
        <textarea value={form.offer} onChange={set('offer')} required rows={3} maxLength={500}
          placeholder="e.g. 15% off all orders for verified Daanaa members, or a free first consultation"
          className="w-full px-4 py-3 border border-light-grey rounded-xl font-body text-body text-deep-navy placeholder-muted-cream focus:outline-none focus:ring-2 focus:ring-soft-gold resize-y" />
        <p className="mt-1 font-body text-caption text-muted-cream">Keep it simple. Members need to understand it in one sentence.</p>
      </label>
      <div className="grid sm:grid-cols-2 gap-4">
        <label className="block">
          <span className="block font-body text-small font-medium text-deep-navy mb-1.5">
            {isRemote ? 'City or headquarters' : (form.service_area_type === 'local' ? 'Your city' : 'Primary city or region')}
            {isRemote && <span className="text-cool-grey font-normal ml-1">(optional)</span>}
          </span>
          <input type="text" value={form.location_city} onChange={set('location_city')}
            placeholder={isRemote ? 'Toronto, London, Chicago…' : 'Chicago'}
            className="w-full px-4 py-2.5 border border-light-grey rounded-xl font-body text-body text-deep-navy focus:outline-none focus:ring-2 focus:ring-soft-gold" />
        </label>
        {!isRemote ? (
          <label className="block">
            <span className="block font-body text-small font-medium text-deep-navy mb-1.5">State</span>
            <input type="text" value={form.location_state} onChange={set('location_state')} placeholder="IL"
              className="w-full px-4 py-2.5 border border-light-grey rounded-xl font-body text-body text-deep-navy focus:outline-none focus:ring-2 focus:ring-soft-gold" />
          </label>
        ) : (
          <label className="block">
            <span className="block font-body text-small font-medium text-deep-navy mb-1.5">
              Country <span className="text-cool-grey font-normal">(if outside the US)</span>
            </span>
            <input type="text" value={form.location_country} onChange={set('location_country')}
              placeholder="Canada, UK, Germany…"
              className="w-full px-4 py-2.5 border border-light-grey rounded-xl font-body text-body text-deep-navy focus:outline-none focus:ring-2 focus:ring-soft-gold" />
          </label>
        )}
      </div>
      <div className="grid sm:grid-cols-2 gap-4">
        <label className="block">
          <span className="block font-body text-small font-medium text-deep-navy mb-1.5">Website</span>
          <input type="url" value={form.website_url} onChange={set('website_url')} placeholder="https://"
            className="w-full px-4 py-2.5 border border-light-grey rounded-xl font-body text-body text-deep-navy focus:outline-none focus:ring-2 focus:ring-soft-gold" />
        </label>
        <label className="block">
          <span className="block font-body text-small font-medium text-deep-navy mb-1.5">Contact phone <span className="text-cool-grey font-normal">(optional)</span></span>
          <input type="tel" value={form.contact_phone} onChange={set('contact_phone')}
            className="w-full px-4 py-2.5 border border-light-grey rounded-xl font-body text-body text-deep-navy focus:outline-none focus:ring-2 focus:ring-soft-gold" />
        </label>
      </div>
      <div className="border-t border-light-grey pt-4">
        <p className="font-body text-caption text-cool-grey mb-3">About you</p>
        <div className="grid sm:grid-cols-2 gap-4">
          <label className="block">
            <span className="block font-body text-small font-medium text-deep-navy mb-1.5">Your name</span>
            <input type="text" value={form.submitter_name} onChange={set('submitter_name')} required
              className="w-full px-4 py-2.5 border border-light-grey rounded-xl font-body text-body text-deep-navy focus:outline-none focus:ring-2 focus:ring-soft-gold" />
          </label>
          <label className="block">
            <span className="block font-body text-small font-medium text-deep-navy mb-1.5">Your email</span>
            <input type="email" value={form.submitter_email} onChange={set('submitter_email')} required
              className="w-full px-4 py-2.5 border border-light-grey rounded-xl font-body text-body text-deep-navy focus:outline-none focus:ring-2 focus:ring-soft-gold" />
          </label>
        </div>
      </div>
      <label className="block">
        <span className="block font-body text-small font-medium text-deep-navy mb-1.5">Anything else? <span className="text-cool-grey font-normal">(optional)</span></span>
        <textarea value={form.notes} onChange={set('notes')} rows={2} maxLength={1000}
          placeholder="We've worked with nonprofits for 10 years / We're a small business ourselves / We'd love to expand with Daanaa…"
          className="w-full px-4 py-3 border border-light-grey rounded-xl font-body text-body text-deep-navy placeholder-muted-cream focus:outline-none focus:ring-2 focus:ring-soft-gold resize-y" />
      </label>
      <div className="space-y-3">
        <p className="font-body text-caption text-muted-cream">
          Your application will be reviewed by our team for completeness and good faith.
        </p>
        <label className="flex items-start gap-3 cursor-pointer">
          <input
            type="checkbox"
            required
            className="mt-0.5 accent-soft-gold shrink-0"
          />
          <span className="font-body text-small text-cool-grey leading-[1.6]">
            I have read and agree to the{' '}
            <a href="/vendor-policy" target="_blank" rel="noopener noreferrer" className="text-soft-gold hover:underline">
              Daanaa Impact Network Partner Policy
            </a>
            , including that participation never affects how any organization appears in Daanaa search results, and that the discount or benefit I describe must be real and honored as listed.
          </span>
        </label>
      </div>
      <button type="submit" disabled={sending}
        className="w-full sm:w-auto px-8 py-3 bg-soft-gold text-deep-navy font-body text-body-lg font-semibold rounded-xl hover:bg-bright-gold disabled:opacity-40 transition-colors">
        {sending ? 'Sending…' : 'Join the network'}
      </button>
      <p className="font-body text-caption text-muted-cream">
        No CAF, no reporting, no fees.{' '}
        <a href="mailto:partners@daanaa.org" className="text-soft-gold hover:underline">partners@daanaa.org</a>
      </p>
    </form>
  )
}

// ─── Network partner form ────────────────────────────────────────────────────

function NetworkPartnerForm() {
  const [form, setForm] = useState({
    org_name: '', name: '', email: '', partner_type: ALL_CATEGORIES[0], message: '',
  })
  const [sending, setSending] = useState(false)
  const [sent, setSent] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function set(field: string) {
    return (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
      setForm(f => ({ ...f, [field]: e.target.value }))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setSending(true)
    try {
      const res = await fetch('/api/partner/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          org_name: form.org_name.trim(), name: form.name.trim(),
          email: form.email.trim(), partner_type: form.partner_type,
          message: form.message.trim(), source: 'vendor_guild',
        }),
      })
      const body = await res.json()
      if (!res.ok) { setError(body.error || 'Something went wrong.'); setSending(false); return }
      setSent(true)
    } catch {
      setError('Could not reach the server. Email us at partners@daanaa.org.')
      setSending(false)
    }
  }

  if (sent) return (
    <div className="text-center py-8">
      <div className="w-12 h-12 rounded-full bg-soft-gold/15 mx-auto mb-4 flex items-center justify-center">
        <svg width="20" height="16" viewBox="0 0 20 16" fill="none">
          <path d="M1 8L7 14L19 1" stroke="#C9A96E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </div>
      <h3 className="font-display italic text-title-lg text-deep-navy mb-2">Thank you</h3>
      <p className="font-body text-body text-cool-grey leading-[1.7] max-w-[400px] mx-auto">
        We review every network partner inquiry and reply from{' '}
        <a href="mailto:partners@daanaa.org" className="text-soft-gold hover:underline">partners@daanaa.org</a>.
      </p>
    </div>
  )

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="p-4 bg-destructive/5 border border-destructive/20 rounded-xl">
          <p className="font-body text-body text-destructive">{error}</p>
        </div>
      )}
      <div className="grid sm:grid-cols-2 gap-4">
        <label className="block">
          <span className="block font-body text-small font-medium text-deep-navy mb-1.5">Your name</span>
          <input type="text" value={form.name} onChange={set('name')} required
            className="w-full px-4 py-2.5 border border-light-grey rounded-xl font-body text-body text-deep-navy focus:outline-none focus:ring-2 focus:ring-soft-gold" />
        </label>
        <label className="block">
          <span className="block font-body text-small font-medium text-deep-navy mb-1.5">Company name</span>
          <input type="text" value={form.org_name} onChange={set('org_name')} required
            className="w-full px-4 py-2.5 border border-light-grey rounded-xl font-body text-body text-deep-navy focus:outline-none focus:ring-2 focus:ring-soft-gold" />
        </label>
      </div>
      <div className="grid sm:grid-cols-2 gap-4">
        <label className="block">
          <span className="block font-body text-small font-medium text-deep-navy mb-1.5">Work email</span>
          <input type="email" value={form.email} onChange={set('email')} required
            className="w-full px-4 py-2.5 border border-light-grey rounded-xl font-body text-body text-deep-navy focus:outline-none focus:ring-2 focus:ring-soft-gold" />
        </label>
        <label className="block">
          <span className="block font-body text-small font-medium text-deep-navy mb-1.5">Category</span>
          <select value={form.partner_type} onChange={set('partner_type')}
            className="w-full px-4 py-2.5 border border-light-grey rounded-xl font-body text-body text-deep-navy bg-white focus:outline-none focus:ring-2 focus:ring-soft-gold">
            {ALL_CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </label>
      </div>
      <label className="block">
        <span className="block font-body text-small font-medium text-deep-navy mb-1.5">What you offer and your nonprofit reach</span>
        <textarea value={form.message} onChange={set('message')} required rows={4} maxLength={5000}
          placeholder="Tell us about your nonprofit programs, current pricing, and approximate number of nonprofit customers."
          className="w-full px-4 py-3 border border-light-grey rounded-xl font-body text-body text-deep-navy placeholder-muted-cream focus:outline-none focus:ring-2 focus:ring-soft-gold resize-y" />
      </label>
      <button type="submit" disabled={sending}
        className="w-full sm:w-auto px-8 py-3 bg-deep-navy text-warm-cream font-body text-body-lg font-semibold rounded-xl hover:opacity-90 disabled:opacity-40 transition-opacity">
        {sending ? 'Sending…' : 'Start the conversation'}
      </button>
      <p className="font-body text-caption text-muted-cream">
        <a href="mailto:partners@daanaa.org" className="text-soft-gold hover:underline">partners@daanaa.org</a>
      </p>
    </form>
  )
}

// ─── Main page ───────────────────────────────────────────────────────────────

export default function ForVendors() {
  usePageMeta(
    'Join the Daanaa Impact Network',
    'Any business can join: local, small, national. Tell us what you offer nonprofits and we list you. No fees for community partners.',
  )

  const [path, setPath] = useState<'community' | 'network'>('community')
  const { data: stats } = useApi(() => getStats(), [])
  const { data: memberData } = useApi(() => getGuildMemberCount(), [])
  const { data: vendorData } = useApi(() => getGuildBenefits(), [])
  const orgCountLabel = stats?.total_organizations
    ? `${(Math.round(stats.total_organizations / 100000) / 10).toFixed(1)}M`
    : '1.7M+'
  const memberCountLabel = memberData?.member_count
    ? memberData.member_count.toLocaleString()
    : '—'
  const vendorCountLabel = vendorData?.length != null
    ? String(vendorData.length)
    : '—'

  return (
    <div className="min-h-[100dvh] bg-warm-cream">

      {/* Hero */}
      <div className="bg-deep-navy pt-[108px] pb-20 px-6">
        <div className="max-w-[800px] mx-auto">
          <p className="font-body text-caption font-medium tracking-[0.12em] text-soft-gold uppercase mb-5">
            Daanaa Impact Network
          </p>
          <h1 className="font-display italic text-warm-cream leading-[1.1] mb-6">
            We are building something<br />together. Join us.
          </h1>
          <p className="font-body text-title-sm text-warm-cream/80 leading-[1.7] max-w-[640px] mb-4">
            Daanaa connects {orgCountLabel} nonprofits with the donors who support them and the
            businesses that help them operate. The impact network is open to any business
            that wants to be part of it: a neighborhood print shop, a regional insurance
            broker, or a national payment processor.
          </p>
          <p className="font-body text-title-sm text-warm-cream/80 leading-[1.7] max-w-[640px] mb-8">
            No walls. No minimums. One community growing together.
          </p>
          <div className="flex flex-wrap gap-3">
            <a href="#join"
              className="inline-block px-8 py-3.5 bg-soft-gold text-deep-navy font-body text-body-lg font-semibold rounded-xl hover:bg-bright-gold transition-colors">
              Join the network
            </a>
            <a href="#how-it-works"
              className="inline-block px-8 py-3.5 border border-warm-cream/30 text-warm-cream font-body text-body-lg rounded-xl hover:bg-white/5 transition-colors">
              How it works
            </a>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="bg-navy-mid border-b border-deep-navy/30">
        <div className="max-w-[800px] mx-auto px-6 py-6 grid grid-cols-3 gap-6 text-center">
          {[
            { value: orgCountLabel, label: 'nonprofits in the directory' },
            { value: memberCountLabel, label: 'guild members so far' },
            { value: vendorCountLabel, label: 'active partner offers' },
          ].map(({ value, label }) => (
            <div key={label}>
              <p className="font-display italic text-headline text-soft-gold leading-none mb-1">{value}</p>
              <p className="font-body text-caption text-muted-cream leading-[1.4]">{label}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="max-w-[800px] mx-auto px-6">

        {/* Two paths */}
        <section id="how-it-works" className="py-16 scroll-mt-24">
          <h2 className="font-display italic text-headline-lg text-deep-navy mb-2">Two ways in. One network.</h2>
          <p className="font-body text-body-lg text-cool-grey mb-10 leading-[1.7]">
            The difference isn't size or geography. It's whether you want a formal contract.
            A local shop and an online SaaS serving clients in 40 states can both be community partners.
            Choose what fits your business now.
          </p>
          <div className="grid sm:grid-cols-2 gap-4">

            {/* Community */}
            <div className="bg-white rounded-2xl border border-light-grey p-7">
              <div className="w-10 h-10 rounded-full bg-soft-gold/15 flex items-center justify-center mb-4">
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                  <circle cx="9" cy="9" r="7.5" stroke="#C9A96E" strokeWidth="1.5"/>
                  <path d="M5.5 9l2.5 2.5 4.5-4.5" stroke="#C9A96E" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <h3 className="font-body text-title-sm font-semibold text-deep-navy mb-2">Community partner</h3>
              <p className="font-body text-body text-cool-grey leading-[1.65] mb-4">
                Any business. Any size. Any geography, including online services and
                businesses that work across multiple states. Tell us what you offer and we list you.
                No contract required.
              </p>
              <ul className="space-y-2 mb-6">
                {[
                  'Local shop, multi-state firm, or fully online. All welcome.',
                  'Any offer: discount, free session, priority service',
                  'No contract, no CAF, no monthly reporting',
                  'Reviewed and listed within a week',
                  'Shareable referral link included with your listing',
                ].map(item => (
                  <li key={item} className="flex gap-2.5">
                    <span className="shrink-0 mt-0.5 w-4 h-4 rounded-full bg-soft-gold/15 flex items-center justify-center">
                      <svg width="8" height="6" viewBox="0 0 8 6" fill="none">
                        <path d="M1 3L3 5L7 1" stroke="#C9A96E" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    </span>
                    <span className="font-body text-small text-cool-grey">{item}</span>
                  </li>
                ))}
              </ul>
              <button onClick={() => { setPath('community'); document.getElementById('join')?.scrollIntoView({ behavior: 'smooth' }) }}
                className="w-full py-2.5 bg-soft-gold text-deep-navy font-body text-body font-semibold rounded-xl hover:bg-bright-gold transition-colors">
                Join as a community partner
              </button>
            </div>

            {/* Network */}
            <div className="bg-deep-navy rounded-2xl p-7">
              <div className="w-10 h-10 rounded-full bg-soft-gold/20 flex items-center justify-center mb-4">
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                  <path d="M9 2L11.5 7H16.5L12.5 10.5L14 15.5L9 12.5L4 15.5L5.5 10.5L1.5 7H6.5L9 2Z" stroke="#C9A96E" strokeWidth="1.5" strokeLinejoin="round"/>
                </svg>
              </div>
              <h3 className="font-body text-title-sm font-semibold text-warm-cream mb-2">Network partner</h3>
              <p className="font-body text-body text-warm-cream/70 leading-[1.65] mb-4">
                For partners ready to formalize: a signed contract with milestone pricing built
                in from day one, a shared discount code for all members, and a dedicated
                referral page. Best for large scale or high volume nonprofit programs.
              </p>
              <ul className="space-y-2 mb-6">
                {[
                  'Formal contract with milestone pricing from day one',
                  'Shared code for all 1.7M+ members',
                  'Monthly aggregate reporting + CAF invoice',
                  'Dedicated page at daanaa.org/guild/your-name',
                  'Rates improve automatically as guild spend grows',
                ].map(item => (
                  <li key={item} className="flex gap-2.5">
                    <span className="shrink-0 mt-0.5 w-4 h-4 rounded-full bg-soft-gold/20 flex items-center justify-center">
                      <svg width="8" height="6" viewBox="0 0 8 6" fill="none">
                        <path d="M1 3L3 5L7 1" stroke="#C9A96E" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    </span>
                    <span className="font-body text-small text-warm-cream/70">{item}</span>
                  </li>
                ))}
              </ul>
              <button onClick={() => { setPath('network'); document.getElementById('join')?.scrollIntoView({ behavior: 'smooth' }) }}
                className="w-full py-2.5 bg-soft-gold text-deep-navy font-body text-body font-semibold rounded-xl hover:bg-bright-gold transition-colors">
                Start the conversation
              </button>
            </div>
          </div>
        </section>

        {/* Why join */}
        <section className="pb-16">
          <h2 className="font-display italic text-headline text-deep-navy mb-2">Why join the impact network?</h2>
          <p className="font-body text-body-lg text-cool-grey mb-8 leading-[1.7]">
            You are not just offering a discount. You are part of what makes the sector stronger.
          </p>
          <div className="grid gap-3">
            {[
              { title: 'Your customers are already here', body: "Most of your existing nonprofit clients are somewhere in our 1.7M+ index. Joining puts you in front of them and in front of the ones who haven't found you yet." },
              { title: 'No individual account management', body: 'Community partners get a listing and members reach you directly. Network partners use one shared code. Daanaa handles distribution, you handle the relationship.' },
              { title: 'You earn trust by showing up', body: 'No paid placement. Members choose partners on price, quality, and reputation. The network rewards partners who genuinely show up for nonprofits.' },
              { title: 'Your referral link grows your own book', body: 'Every listed partner gets a shareable page they can put in their email signature or on their website. Any nonprofit who clicks and claims their Daanaa page can access your offer.' },
              { title: 'Rates improve as the network grows', body: 'For network partners: milestone pricing is in every contract from day one. The more members use the network, the better the rates get, for everyone, automatically.' },
            ].map(({ title, body }) => (
              <div key={title} className="flex gap-4 bg-white rounded-xl border border-light-grey p-5">
                <span className="shrink-0 mt-1 w-5 h-5 rounded-full bg-soft-gold/15 flex items-center justify-center">
                  <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
                    <path d="M1 4L3.5 6.5L9 1" stroke="#C9A96E" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </span>
                <div>
                  <p className="font-body text-body font-semibold text-deep-navy mb-0.5">{title}</p>
                  <p className="font-body text-small text-cool-grey leading-[1.6]">{body}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Commitments */}
        <section className="pb-16">
          <div className="bg-soft-gold/8 border border-soft-gold/25 rounded-2xl p-7">
            <h2 className="font-display italic text-title-lg text-deep-navy mb-4">What we commit to you</h2>
            <div className="grid sm:grid-cols-2 gap-5">
              {[
                { title: 'Standard rates per category', body: 'Same CAF % for every network partner in the same category. No individual placement deals.' },
                { title: 'Your relationships stay yours', body: 'Once a member contacts you, the relationship is yours. We see aggregate numbers for invoicing only.' },
                { title: 'Milestone pricing in writing', body: 'Thresholds are in the contract before we sign. Rate improvements are automatic. No renegotiation.' },
                { title: 'Independence is absolute', body: 'No partner relationship ever affects how nonprofits are scored, ranked, or shown on the platform.' },
              ].map(({ title, body }) => (
                <div key={title}>
                  <p className="font-body text-body font-semibold text-deep-navy mb-0.5">{title}</p>
                  <p className="font-body text-small text-cool-grey leading-[1.6]">{body}</p>
                </div>
              ))}
            </div>
            <p className="mt-5 font-body text-small text-cool-grey">
              Full stewardship commitment at{' '}
              <Link to="/principles" className="text-soft-gold hover:underline">daanaa.org/principles</Link>
            </p>
          </div>
        </section>

        {/* Dual apply form */}
        <section id="join" className="pb-20 scroll-mt-24">
          <div className="flex gap-1 p-1 bg-light-grey rounded-xl mb-8 w-fit">
            <button onClick={() => setPath('community')}
              className={`px-5 py-2 rounded-lg font-body text-body font-medium transition-all ${path === 'community' ? 'bg-white text-deep-navy shadow-sm' : 'text-cool-grey hover:text-deep-navy'}`}>
              Community partner
            </button>
            <button onClick={() => setPath('network')}
              className={`px-5 py-2 rounded-lg font-body text-body font-medium transition-all ${path === 'network' ? 'bg-white text-deep-navy shadow-sm' : 'text-cool-grey hover:text-deep-navy'}`}>
              Network partner
            </button>
          </div>

          <div className="bg-white rounded-2xl shadow-sm border border-light-grey p-8">
            {path === 'network' ? (
              <>
                <h3 className="font-display italic text-title-lg text-deep-navy mb-1">Start the network partner conversation</h3>
                <p className="font-body text-body text-cool-grey mb-6 leading-[1.65]">
                  Tell us about your nonprofit reach and what you offer. We'll be in touch to discuss contract terms and milestone pricing.
                </p>
                <NetworkPartnerForm />
              </>
            ) : (
              <>
                <h3 className="font-display italic text-title-lg text-deep-navy mb-1">Join as a community partner</h3>
                <p className="font-body text-body text-cool-grey mb-6 leading-[1.65]">
                  Any business is welcome. Tell us what you offer nonprofits and where you operate.
                  We review and list you. No fees, no CAF.
                </p>
                <CommunityPartnerForm onGateToNetwork={() => setPath('network')} />
              </>
            )}
          </div>

          <div className="mt-6 text-center space-y-2">
            <p className="font-body text-small text-cool-grey">
              Are you a nonprofit?{' '}
              <Link to="/for-nonprofits" className="text-soft-gold hover:underline">Claim your free page</Link>
            </p>
            <p className="font-body text-small text-cool-grey">
              Know a business that supports nonprofits?{' '}
              <Link to="/for-vendors" className="text-soft-gold hover:underline">Nominate them on this page</Link>
            </p>
          </div>
        </section>

      </div>
    </div>
  )
}
