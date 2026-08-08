import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import { getGuildBenefits, getGuildMemberCount, submitGuildWaitlist, type VendorBenefit } from '../data/api'
import { normalizeExternalUrl } from '../utils/externalLink'

// Member milestone targets — member-count based until vendor contracts define dollar thresholds
const MILESTONES = [
  { label: 'Tier 2', target: 500, description: 'First pricing improvements unlock' },
  { label: 'Tier 3', target: 2_000, description: 'Expanded partner categories' },
  { label: 'Tier 4', target: 10_000, description: 'Maximum guild rates' },
]

function CopyButton({ code }: { code: string }) {
  const [copied, setCopied] = useState(false)

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(code)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Clipboard blocked — select the text fallback is handled by the input's onClick
      setCopied(false)
    }
  }

  return (
    <button
      onClick={handleCopy}
      className={`shrink-0 px-3 py-2 rounded-lg font-body text-caption font-semibold transition-all ${
        copied
          ? 'bg-green-100 text-green-700'
          : 'bg-soft-gold/15 text-soft-gold hover:bg-soft-gold/25'
      }`}
    >
      {copied ? 'Copied!' : 'Copy'}
    </button>
  )
}

function VendorCard({ v }: { v: VendorBenefit }) {
  function handleCodeClick(e: React.MouseEvent<HTMLInputElement>) {
    (e.target as HTMLInputElement).select()
  }

  return (
    <div className="bg-white rounded-2xl border border-light-cream p-6 flex flex-col gap-4">
      <div>
        <span className="inline-block px-2 py-0.5 rounded-full bg-soft-gold/10 font-body text-micro font-semibold tracking-[0.08em] uppercase text-soft-gold mb-2">
          {v.category}
        </span>
        <h3 className="font-display italic text-deep-navy text-title leading-tight">{v.vendor_name}</h3>
        <p className="font-body text-small text-soft-gold font-semibold mt-0.5">{v.discount_label}</p>
        <p className="font-body text-body text-cool-grey leading-[1.6] mt-2">{v.description}</p>
      </div>

      <div>
        <p className="font-body text-label text-cool-grey uppercase tracking-[0.08em] mb-1.5">Your guild code</p>
        <div className="flex items-center gap-2">
          <input
            readOnly
            value={v.code}
            onClick={handleCodeClick}
            className="flex-1 min-w-0 px-3 py-2 rounded-lg bg-light-cream font-mono text-body text-deep-navy font-semibold border border-transparent focus:outline-none focus:border-soft-gold/40 cursor-text"
          />
          <CopyButton code={v.code} />
        </div>
        {v.how_to_use && (
          <p className="font-body text-caption text-muted-cream mt-1.5 leading-[1.5]">{v.how_to_use}</p>
        )}
      </div>

      {v.website_url && (
        <a
          href={normalizeExternalUrl(v.website_url) || undefined}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-auto inline-flex items-center gap-1.5 font-body text-small text-soft-gold font-semibold hover:text-bright-gold transition-colors"
        >
          Visit {v.vendor_name}
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M7 17 17 7M17 7H8M17 7v9"/>
          </svg>
        </a>
      )}
    </div>
  )
}

function MilestoneTracker({ memberCount }: { memberCount: number }) {
  const next = MILESTONES.find(m => memberCount < m.target) ?? MILESTONES[MILESTONES.length - 1]
  const prev = MILESTONES[MILESTONES.indexOf(next) - 1]
  const base = prev?.target ?? 0
  const pct = Math.min(100, Math.round(((memberCount - base) / (next.target - base)) * 100))

  return (
    <div className="bg-warm-cream border border-light-cream rounded-2xl p-5">
      <p className="font-body text-label font-semibold tracking-[0.1em] uppercase text-cool-grey mb-1">Guild milestone</p>
      <p className="font-display italic text-deep-navy text-title-sm leading-tight">
        {next.label}: {next.description}
      </p>
      <p className="font-body text-small text-cool-grey mt-1">
        {memberCount.toLocaleString()} of {next.target.toLocaleString()} members
      </p>
      <div className="mt-3 h-2 rounded-full bg-light-cream overflow-hidden">
        <div
          className="h-full rounded-full bg-soft-gold transition-all duration-700"
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className="font-body text-label text-muted-cream mt-2">
        Milestone pricing baked into every partner contract from day one. No renegotiation needed.
      </p>
    </div>
  )
}

function WaitlistForm({ memberCount }: { memberCount: number }) {
  const [email, setEmail] = useState('')
  const [state, setState] = useState<'idle' | 'submitting' | 'done' | 'error'>('idle')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!email.trim()) return
    setState('submitting')
    try {
      await submitGuildWaitlist(email.trim())
      setState('done')
    } catch {
      setState('error')
    }
  }

  if (state === 'done') {
    return (
      <div className="text-center py-4">
        <p className="font-body text-body-lg text-deep-navy font-semibold">You're on the list.</p>
        <p className="font-body text-small text-cool-grey mt-1">We'll email you when the first guild deals go live.</p>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-2">
      <input
        type="email"
        required
        placeholder="your@email.org"
        value={email}
        onChange={e => setEmail(e.target.value)}
        className="flex-1 px-4 py-2.5 rounded-xl border border-light-cream font-body text-body text-deep-navy placeholder:text-muted-cream focus:outline-none focus:border-soft-gold/60"
      />
      <button
        type="submit"
        disabled={state === 'submitting'}
        className="px-5 py-2.5 bg-soft-gold text-deep-navy rounded-xl font-body text-body font-semibold hover:bg-bright-gold transition-colors disabled:opacity-60"
      >
        {state === 'submitting' ? 'Saving…' : 'Notify me'}
      </button>
      {state === 'error' && (
        <p className="w-full font-body text-caption text-red-500 mt-1">Something went wrong. Try again.</p>
      )}
    </form>
  )
}

function EmptyState({ memberCount }: { memberCount: number }) {
  const display = memberCount > 0
    ? `${memberCount.toLocaleString()} nonprofits already have guild access.`
    : 'Early access. First members are joining now.'

  return (
    <div className="max-w-[560px] mx-auto py-8">
      <div className="bg-white rounded-2xl border border-light-cream p-8 mb-6">
        <p className="font-body text-caption font-semibold tracking-[0.1em] uppercase text-soft-gold mb-3">
          Guild benefits coming soon
        </p>
        <h2 className="font-display italic text-deep-navy text-title-lg leading-tight mb-3">
          First partner offers are being finalized.
        </h2>
        <p className="font-body text-body-lg text-cool-grey leading-[1.7] mb-2">
          {display}
        </p>
        <p className="font-body text-body text-cool-grey leading-[1.7]">
          You'll have access to discounted rates on software, insurance, printing, travel, and more. Prices the sector has never had before.
        </p>
      </div>

      <MilestoneTracker memberCount={memberCount} />

      <div className="mt-6 bg-white rounded-2xl border border-light-cream p-6">
        <p className="font-display italic text-deep-navy text-title-sm mb-1">Get notified when deals go live</p>
        <p className="font-body text-small text-cool-grey mb-4">We'll send one email when your first guild benefits are ready.</p>
        <WaitlistForm memberCount={memberCount} />
      </div>
    </div>
  )
}

export default function MemberBenefits() {
  usePageMeta(
    'Guild Benefits — Daanaa',
    'Daanaa guild members get exclusive pricing on software, insurance, printing, and more. Same discount code for every member.',
  )

  const [benefits, setBenefits] = useState<VendorBenefit[]>([])
  const [memberCount, setMemberCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError(false)
    try {
      const [b, m] = await Promise.all([getGuildBenefits(), getGuildMemberCount()])
      setBenefits(b)
      setMemberCount(m.member_count)
    } catch {
      setError(true)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  // Group by category
  const byCategory = benefits.reduce<Record<string, VendorBenefit[]>>((acc, v) => {
    ;(acc[v.category] ??= []).push(v)
    return acc
  }, {})

  return (
    <div className="min-h-screen bg-warm-cream pt-nav">
      <div className="max-w-[900px] mx-auto px-6 py-10">
        {/* Header */}
        <div className="mb-8">
          <Link to="/for-nonprofits" className="inline-flex items-center gap-1 font-body text-caption text-cool-grey hover:text-deep-navy mb-4">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="15 18 9 12 15 6"/></svg>
            For nonprofits
          </Link>
          <h1 className="font-display italic text-deep-navy leading-tight">
            Guild benefits
          </h1>
          <p className="font-body text-lead text-cool-grey mt-2 leading-[1.7]">
            Every Daanaa guild member gets the same discount code. No tiers, no upsells. Same price whether you're a two-person org or a mid-size foundation.
          </p>
        </div>

        {loading && (
          <div className="flex justify-center py-20">
            <div className="w-6 h-6 rounded-full border-2 border-soft-gold border-t-transparent animate-spin" />
          </div>
        )}

        {!loading && error && (
          <div className="text-center py-16">
            <p className="font-body text-body-lg text-cool-grey mb-4">Deals temporarily unavailable. Check back soon.</p>
            <button onClick={load} className="font-body text-small text-soft-gold hover:underline">Try again</button>
          </div>
        )}

        {!loading && !error && benefits.length === 0 && (
          <EmptyState memberCount={memberCount} />
        )}

        {!loading && !error && benefits.length > 0 && (
          <>
            {/* Milestone tracker above the grid */}
            <div className="mb-8">
              <MilestoneTracker memberCount={memberCount} />
            </div>

            {/* Category sections */}
            {Object.entries(byCategory).map(([category, items]) => (
              <div key={category} className="mb-10">
                <h2 className="font-body text-caption font-semibold tracking-[0.1em] uppercase text-cool-grey mb-4">
                  {category}
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {items.map(v => <VendorCard key={v.id} v={v} />)}
                </div>
              </div>
            ))}

            <div className="mt-6 border-t border-light-cream pt-6">
              <p className="font-body text-small text-muted-cream leading-[1.6]">
                Guild pricing improves automatically as the network grows. Milestone thresholds are baked into every partner contract from day one.
                Questions? <a href="mailto:orgs@daanaa.org" className="text-soft-gold hover:underline">orgs@daanaa.org</a>
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
