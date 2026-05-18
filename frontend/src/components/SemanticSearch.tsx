import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { semanticSearch, semanticStatus, type SemanticResult } from '../data/api'
import { formatCurrency, getScoreLabel } from '../data/organizations'

const EXAMPLES = [
  "food banks helping low-income families",
  "veterans mental health support",
  "climate change research Pacific Northwest",
  "after-school programs inner city youth",
  "affordable housing rural communities",
]

function ScoreBadge({ score }: { score: number }) {
  const label = getScoreLabel(score)
  // Financial scale is not a danger gradient — larger scale gets a gentle green,
  // everything else is calm slate. Small ≠ bad, so never alarm colors here.
  const color = score >= 75 ? '#5a9e6f' : '#8a8f98'
  return (
    <span className="inline-flex items-center gap-1 font-body text-[11px] font-medium"
          style={{ color }}>
      {score > 0 ? `${score} · ${label}` : 'Unscored'}
    </span>
  )
}

export default function SemanticSearch() {
  const [query, setQuery]       = useState('')
  const [results, setResults]   = useState<SemanticResult[] | null>(null)
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState<string | null>(null)
  const [ready, setReady]       = useState(false)
  const [indexed, setIndexed]   = useState(0)
  const [total, setTotal]       = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    semanticStatus().then(s => {
      setReady(s.ready)
      setIndexed(s.indexed)
      setTotal(s.total)
    }).catch(() => {})
  }, [])

  const search = async (q = query) => {
    if (!q.trim() || !ready) return
    setLoading(true)
    setError(null)
    try {
      const data = await semanticSearch({ q: q.trim(), limit: 20 })
      setResults(data.results)
    } catch (e: any) {
      setError(e.message || 'Search failed')
    } finally {
      setLoading(false)
    }
  }

  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') search()
  }

  return (
    <div className="w-full">
      {/* Search bar */}
      <div className="relative">
        <div className="flex items-center gap-3 bg-white border border-light-grey rounded-xl px-4 py-3 shadow-sm focus-within:border-soft-gold/60 transition-colors">
          {/* Sparkle icon */}
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="1.8"
               strokeLinecap="round" strokeLinejoin="round" className="flex-shrink-0">
            <path d="M12 3l1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5z"/>
            <path d="M19 17l.75 2.25L22 20l-2.25.75L19 23l-.75-2.25L16 20l2.25-.75z" opacity=".5"/>
          </svg>
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={onKey}
            placeholder={ready ? "Describe what you're looking for in plain English…" : `Building search index… ${indexed.toLocaleString()} / ${total.toLocaleString()} orgs`}
            disabled={!ready}
            className="flex-1 font-body text-[15px] text-deep-navy placeholder:text-cool-grey/60 outline-none bg-transparent"
          />
          <button
            onClick={() => search()}
            disabled={!ready || !query.trim() || loading}
            className="flex-shrink-0 px-4 py-1.5 rounded-lg bg-soft-gold text-deep-navy font-body text-[13px] font-semibold hover:bg-bright-gold disabled:opacity-40 transition-colors"
          >
            {loading ? 'Searching…' : 'Search'}
          </button>
        </div>

        {/* Example queries */}
        {!results && !loading && ready && (
          <div className="mt-3 flex flex-wrap gap-2">
            {EXAMPLES.map(ex => (
              <button key={ex}
                onClick={() => { setQuery(ex); search(ex) }}
                className="px-3 py-1 rounded-full bg-navy-mid/8 border border-light-grey text-cool-grey font-body text-[12px] hover:border-soft-gold/40 hover:text-deep-navy transition-colors">
                {ex}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* AI badge */}
      <div className="mt-2 flex items-center gap-1.5">
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-soft-gold/10 text-soft-gold font-body text-[10px] font-semibold tracking-wide uppercase">
          AI Powered
        </span>
        <span className="font-body text-[11px] text-cool-grey/70">
          {ready
            ? `Searching across ${indexed.toLocaleString()} organizations by mission & purpose`
            : 'Semantic index building in background — try keyword search in the meantime'}
        </span>
      </div>

      {/* Error */}
      {error && (
        <p className="mt-4 font-body text-[14px] text-red-500">{error}</p>
      )}

      {/* Results */}
      {results && !loading && (
        <div className="mt-6">
          <p className="font-body text-[12px] text-cool-grey mb-4">
            {results.length} results for &ldquo;<span className="text-deep-navy font-medium">{query}</span>&rdquo;
          </p>
          {results.length === 0 ? (
            <p className="font-body text-[14px] text-cool-grey">No matching organizations found.</p>
          ) : (
            <div className="space-y-3">
              {results.map(org => (
                <Link key={org.EIN}
                  to={`/org/${org.EIN}`}
                  className="block bg-white border border-light-grey rounded-xl p-5 hover:border-soft-gold/40 hover:shadow-md transition-all group">
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0">
                      <p className="font-body text-[15px] font-semibold text-deep-navy group-hover:text-soft-gold transition-colors truncate">
                        {org.organization_name}
                      </p>
                      <p className="font-body text-[12px] text-cool-grey mt-0.5">
                        {[org.CITY, org.STATE].filter(Boolean).join(', ')}
                        {org.NTEE1 && <span className="ml-2 px-1.5 py-0.5 rounded bg-navy-mid/8 text-[11px]">{org.NTEE1}</span>}
                      </p>
                      {org.mission && (
                        <p className="mt-2 font-body text-[13px] text-cool-grey line-clamp-2 leading-[1.5]">
                          {org.mission}
                        </p>
                      )}
                    </div>
                    <div className="flex-shrink-0 text-right space-y-1">
                      <ScoreBadge score={Math.round(org.ntee1_percentile ?? 0)} />
                      {org.total_revenue && org.total_revenue > 0 && (
                        <p className="font-body text-[11px] text-cool-grey">
                          {formatCurrency(org.total_revenue)}
                        </p>
                      )}
                      <p className="font-body text-[10px] text-cool-grey/50">
                        {Math.round(org.similarity_score * 100)}% match
                      </p>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
