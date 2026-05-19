import { useState, useRef } from 'react'
import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import LampMark from '../components/LampMark'
import type { TierName } from '../components/TrustBadge'

const API_BASE = import.meta.env.VITE_API_URL || ''

interface AdvisorOrg {
  EIN: string
  organization_name: string
  NTEE1: string | null
  CITY: string | null
  STATE: string | null
  total_revenue: number | null
  peer_percentile: number | null
  ntee1_percentile: number | null
  merit_tier: string | null
  merit_score: number | null
  merit_band: string | null
  donate_url: string | null
  donate_platform: string | null
  cause_tags: string[] | null
}

interface AdvisorResult {
  orgs: AdvisorOrg[]
  parsed: {
    ntee: string | null
    state: string | null
    city: string | null
    prefer_small: boolean
  }
  context: string
  total: number
}

const SUGGESTIONS = [
  'Food bank in Chicago',
  'Mental health support in Texas',
  'Environmental conservation in California',
  'Youth mentorship in New York',
]

const VALID_TIERS = new Set<string>(['Beacon', 'Lantern', 'Flame', 'Ember', 'Spark'])

function OrgCard({
  org,
  onDonate,
}: {
  org: AdvisorOrg
  onDonate: (org: AdvisorOrg) => void
}) {
  const tier = org.merit_tier && VALID_TIERS.has(org.merit_tier)
    ? (org.merit_tier as TierName)
    : null
  const pct = org.peer_percentile ?? org.ntee1_percentile

  return (
    <div className="bg-white border border-light-grey rounded-2xl p-5 flex flex-col gap-4 hover:border-soft-gold/50 transition-colors">
      <div className="flex items-start gap-3">
        {tier && (
          <div className="shrink-0 mt-0.5">
            <LampMark tier={tier} size="sm" />
          </div>
        )}
        <div className="min-w-0 flex-1">
          <Link
            to={`/org/${org.EIN}`}
            className="font-body text-[15px] font-semibold text-deep-navy hover:text-soft-gold transition-colors leading-snug block"
          >
            {org.organization_name}
          </Link>
          {(org.CITY || org.STATE) && (
            <p className="font-body text-[13px] text-cool-grey mt-0.5">
              {[org.CITY, org.STATE].filter(Boolean).join(', ')}
            </p>
          )}
        </div>
      </div>

      {pct != null && (
        <div className="flex items-center gap-2">
          <div className="flex-1 h-1 bg-light-grey rounded-full overflow-hidden">
            <div
              className="h-full rounded-full"
              style={{ width: `${Math.min(100, Math.round(pct))}%`, background: '#C9A84C' }}
            />
          </div>
          <span className="font-body text-[11px] text-cool-grey shrink-0">
            Top {Math.max(1, Math.round(100 - pct))}% of peers
          </span>
        </div>
      )}

      {org.cause_tags && org.cause_tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {org.cause_tags.slice(0, 3).map(tag => (
            <span
              key={tag}
              className="font-body text-[10px] px-2 py-0.5 rounded-full bg-warm-cream text-cool-grey border border-light-grey"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      <div className="flex items-center gap-2 mt-auto pt-2 border-t border-light-grey/60">
        {org.donate_url ? (
          <a
            href={org.donate_url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={() => onDonate(org)}
            className="flex-1 text-center py-2.5 rounded-xl bg-soft-gold text-deep-navy font-body text-[13px] font-bold hover:bg-bright-gold transition-colors"
          >
            Give to this org
          </a>
        ) : (
          <Link
            to={`/org/${org.EIN}`}
            className="flex-1 text-center py-2.5 rounded-xl border border-soft-gold/40 text-soft-gold font-body text-[13px] font-medium hover:bg-soft-gold/5 transition-colors"
          >
            View profile
          </Link>
        )}
      </div>
    </div>
  )
}

export default function Advisor() {
  usePageMeta(
    'MERIT Advisor',
    "Tell us what you care about and we'll find the right nonprofits for you. Powered by MERIT's verified database of 430,000+ organizations.",
  )

  const [query, setQuery] = useState('')
  const [result, setResult] = useState<AdvisorResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastQuery, setLastQuery] = useState('')

  const inputRef = useRef<HTMLInputElement>(null)

  const search = async (q: string) => {
    const trimmed = q.trim()
    if (!trimmed) return
    setLoading(true)
    setError(null)
    setLastQuery(trimmed)
    try {
      const resp = await fetch(`${API_BASE}/api/advisor/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: trimmed }),
      })
      if (!resp.ok) throw new Error('Search failed')
      const data: AdvisorResult = await resp.json()
      setResult(data)
    } catch {
      setError('Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleDonate = async (org: AdvisorOrg) => {
    try {
      await fetch(`${API_BASE}/api/advisor/click`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ein: org.EIN, query: lastQuery }),
      })
    } catch { /* best-effort */ }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    search(query)
  }

  const handleSuggestion = (s: string) => {
    setQuery(s)
    search(s)
    inputRef.current?.focus()
  }

  const directoryHref = () => {
    if (!result) return '/directory'
    const p = result.parsed
    const parts: string[] = []
    if (p.ntee) parts.push(`ntee=${p.ntee}`)
    if (p.state) parts.push(`state=${p.state}`)
    return parts.length ? `/directory?${parts.join('&')}` : '/directory'
  }

  return (
    <div className="min-h-screen bg-warm-cream">
      {/* Header */}
      <div className="bg-deep-navy pt-[72px]">
        <div className="max-w-[720px] mx-auto px-6 pt-12 pb-10 text-center">
          <p className="font-body text-[11px] font-semibold tracking-[0.1em] text-soft-gold uppercase mb-4">
            MERIT Advisor
          </p>
          <h1
            className="font-display italic text-warm-cream leading-[1.05] tracking-[-0.02em]"
            style={{ fontSize: 'clamp(32px, 5vw, 54px)' }}
          >
            Tell us what you care about
          </h1>
          <p
            className="mt-4 font-body text-[16px] leading-[1.7]"
            style={{ color: 'rgba(245,240,235,0.60)' }}
          >
            We'll find verified nonprofits that match. You give directly to them,
            not through us.
          </p>

          {/* Search input */}
          <form onSubmit={handleSubmit} className="mt-8 relative">
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="e.g. food bank in Austin, Texas"
              maxLength={200}
              className="w-full h-14 pl-5 pr-36 rounded-2xl font-body text-[15px] text-deep-navy bg-white border border-white/10 focus:outline-none focus:ring-2 focus:ring-soft-gold/50 placeholder:text-cool-grey/50"
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="absolute right-2 top-2 h-10 px-5 rounded-xl bg-soft-gold text-deep-navy font-body text-[13px] font-bold hover:bg-bright-gold transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {loading ? 'Finding…' : 'Find orgs'}
            </button>
          </form>

          {/* Suggestion chips */}
          {!result && (
            <div className="mt-5 flex flex-wrap justify-center gap-2">
              {SUGGESTIONS.map(s => (
                <button
                  key={s}
                  onClick={() => handleSuggestion(s)}
                  className="font-body text-[12px] px-3 py-1.5 rounded-full border border-white/15 text-warm-cream/60 hover:border-soft-gold/40 hover:text-soft-gold transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Results */}
      <div className="max-w-[1000px] mx-auto px-6 lg:px-12 py-10">
        {error && (
          <p className="text-center font-body text-[14px] text-cool-grey py-8">
            {error}
          </p>
        )}

        {result && (
          <>
            {/* Context pill + count */}
            <div className="flex items-center flex-wrap gap-2 mb-6">
              <span className="font-body text-[12px] text-cool-grey">Showing:</span>
              <span className="font-body text-[12px] font-medium text-deep-navy px-3 py-1 rounded-full bg-white border border-light-grey">
                {result.context}
              </span>
              <span className="font-body text-[12px] text-cool-grey">
                {result.total} {result.total === 1 ? 'org' : 'orgs'}
              </span>
            </div>

            {result.orgs.length === 0 ? (
              <div className="text-center py-16">
                <p className="font-body text-[15px] text-cool-grey">
                  No matches found for that combination.
                </p>
                <p className="mt-2 font-body text-[13px] text-cool-grey/60">
                  Try a broader search — remove the city, or use a different cause.
                </p>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {result.orgs.map(org => (
                    <OrgCard
                      key={org.EIN}
                      org={org}
                      onDonate={handleDonate}
                    />
                  ))}
                </div>

                <div className="mt-8 text-center">
                  <Link
                    to={directoryHref()}
                    className="font-body text-[13px] text-soft-gold hover:text-bright-gold transition-colors"
                  >
                    See all matching organizations in the directory →
                  </Link>
                </div>

                <p className="mt-8 text-center font-body text-[12px] text-cool-grey/50 max-w-[560px] mx-auto leading-[1.6]">
                  You give directly to the nonprofit. MERIT never receives, holds, or
                  processes your money. All organizations are IRS-verified 501(c)(3)s.
                </p>
              </>
            )}
          </>
        )}

        {!result && !loading && (
          <div className="py-16 text-center">
            <p className="font-body text-[14px] text-cool-grey/50">
              Describe the cause you care about and we'll surface the best-matched
              nonprofits from our database of 430,000+ organizations.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
