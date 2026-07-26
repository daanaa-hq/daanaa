import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { getOrganizations } from '../data/api'
import type { ApiOrganization } from '../data/api'
import LampMark from './LampMark'
import { getTierFromOrg } from './TrustBadge'

interface SearchBarProps {
  value: string
  onChange: (v: string) => void
  onSearch?: (q: string) => void  // if omitted, navigates to /directory?q=
  dark?: boolean                  // glass/blur variant (hero) vs light (default)
  placeholder?: string
  className?: string
  autoFocus?: boolean
}

export default function SearchBar({
  value,
  onChange,
  onSearch,
  dark = false,
  placeholder = 'Search by name, city, or cause…',
  className = '',
  autoFocus = false,
}: SearchBarProps) {
  const navigate = useNavigate()
  const [suggestions, setSuggestions] = useState<ApiOrganization[]>([])
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    if (value.length < 2) {
      setSuggestions([])
      setOpen(false)
      return
    }
    debounceRef.current = setTimeout(async () => {
      setLoading(true)
      try {
        const q = /^\d{2}-\d{7}$/.test(value.trim()) ? value.replace(/-/g, '') : value
        const result = await getOrganizations({ q, per_page: 6, sort: 'organization_name' })
        setSuggestions(result.organizations)
        setOpen(result.organizations.length > 0)
      } catch {
        setSuggestions([])
      } finally {
        setLoading(false)
      }
    }, 250)
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current) }
  }, [value])

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const submit = (q = value) => {
    setOpen(false)
    const trimmed = q.trim()
    if (onSearch) {
      onSearch(trimmed)
    } else {
      navigate(trimmed ? `/directory?q=${encodeURIComponent(trimmed)}` : '/directory')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') { e.preventDefault(); submit() }
    if (e.key === 'Escape') setOpen(false)
  }

  const inputCls = dark
    ? 'w-full h-[58px] bg-white/10 border border-white/20 backdrop-blur-sm text-warm-cream text-body-lg pl-12 pr-4 rounded-l-full outline-none focus:border-soft-gold focus:bg-white/15 transition-all placeholder:text-warm-cream/40'
    : 'w-full h-[58px] bg-white border border-light-grey text-deep-navy text-body-lg pl-12 pr-4 rounded-l-full outline-none focus:border-soft-gold focus:shadow-[0_0_0_3px_rgba(201,169,110,0.10)] transition-all placeholder:text-cool-grey'

  const iconColor = dark ? 'rgba(245,240,235,0.5)' : '#9CA3AF'

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <div className="flex items-center shadow-sm">
        <div className="flex-1 relative">
          <svg
            className="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none"
            width="18" height="18" viewBox="0 0 24 24" fill="none"
            stroke={iconColor} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
          >
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
          </svg>
          <input
            type="text"
            inputMode="search"
            autoComplete="off"
            autoCorrect="off"
            autoCapitalize="off"
            spellCheck={false}
            value={value}
            onChange={e => onChange(e.target.value)}
            onFocus={() => { if (suggestions.length > 0) setOpen(true) }}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            autoFocus={autoFocus}
            className={inputCls}
          />
          {loading && (
            <div className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 rounded-full border-2 border-soft-gold/30 border-t-soft-gold animate-spin pointer-events-none" />
          )}
        </div>
        <button
          type="button"
          onClick={() => submit()}
          className="h-[58px] px-7 bg-soft-gold text-deep-navy font-body text-body font-semibold rounded-r-full hover:bg-bright-gold transition-colors shrink-0"
        >
          Search
        </button>
      </div>

      {open && suggestions.length > 0 && (
        <div className="absolute top-[calc(100%+6px)] left-0 right-0 bg-white rounded-2xl shadow-xl border border-light-grey z-50 overflow-hidden">
          {suggestions.map(org => {
            const tier = getTierFromOrg(org)
            return (
              <button
                key={org.EIN}
                type="button"
                onMouseDown={e => { e.preventDefault(); setOpen(false); navigate(`/org/${org.EIN}`) }}
                className="w-full flex items-center gap-3 px-4 py-3 hover:bg-warm-cream transition-colors text-left group"
              >
                <LampMark tier={tier} size="xs" />
                <div className="flex-1 min-w-0">
                  <p className="font-body text-small font-medium text-deep-navy truncate group-hover:text-soft-gold transition-colors">
                    {org.organization_name}
                  </p>
                  <p className="font-body text-label text-cool-grey">
                    {[org.CITY, org.STATE].filter(Boolean).join(', ')}
                    {org.NTEE1 && <span className="ml-1 opacity-60">· {org.NTEE1}</span>}
                  </p>
                </div>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2" className="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                  <polyline points="9 18 15 12 9 6"/>
                </svg>
              </button>
            )
          })}
          <button
            type="button"
            onMouseDown={e => { e.preventDefault(); submit() }}
            className="w-full flex items-center justify-between px-4 py-3 border-t border-light-grey hover:bg-warm-cream transition-colors"
          >
            <span className="font-body text-caption text-link-gold">
              See all results for "{value}"
            </span>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="9 18 15 12 9 6"/>
            </svg>
          </button>
        </div>
      )}
    </div>
  )
}
